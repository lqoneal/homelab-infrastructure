"""Integrity-bound production verification for Progressive OA-03."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.mission_contract_discovery import require
from scripts.lib.emp.oa02_implementation import atomic_json, canonical_digest, inventory, run
from scripts.lib.emp.oa03_implementation import validate_evidence


class OA03GateVerificationError(ValueError):
    """OA-03 verification cannot safely be represented as current."""


def _directory(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-03"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA03GateVerificationError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise OA03GateVerificationError(f"{path}: object required")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current(root: Path, boundary: str) -> dict[str, Any]:
    state = progressive_oa.load_state(root)
    gate = state.get("gates", {}).get("OA-03", {})
    if state.get("active_gate") != "OA-03" or gate.get("state") != "AWAITING_OPERATOR_VERIFICATION":
        raise OA03GateVerificationError("OA-03 is not awaiting operator verification")
    if gate.get("acceptance_receipt") is not None:
        raise OA03GateVerificationError("OA-03 acceptance already exists")
    for gate_id, item in state["gates"].items():
        if gate_id > "OA-03" and (
            item.get("state") != "PENDING" or item.get("acceptance_receipt") is not None
        ):
            raise OA03GateVerificationError(f"unexpected later-gate activity: {gate_id}")
    authority = ControlledMissionAuthority(
        root, expected_gate="OA-03"
    ).require(boundary=boundary)
    discovery = require(root)
    if discovery["contract_id"] != authority["contract_id"]:
        raise OA03GateVerificationError("discovery and authority disagree")
    implementation = validate_evidence(root)
    return {
        "authority": authority,
        "discovery": discovery,
        "implementation_evidence": str(
            (
                root / progressive_oa.PACKAGE_PATH
                / "runtime/evidence/OA-03/IMPLEMENTATION.json"
            ).relative_to(root)
        ),
        "implementation_digest": implementation["canonical_evidence_digest"],
        "working_tree": inventory(root),
    }


def _stable(value: dict[str, Any]) -> dict[str, Any]:
    stable = {key: item for key, item in value.items() if key != "working_tree"}
    authority = dict(stable["authority"])
    authority.pop("resolution_timestamp", None)
    authority.pop("protected_boundary", None)
    stable["authority"] = authority
    return stable


def _outside_evidence(value: dict[str, Any]) -> list[dict[str, str]]:
    prefix = str(progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-03/")
    return [item for item in value["entries"] if not item["path"].startswith(prefix)]


def _marker(evidence: dict[str, Any]) -> dict[str, Any]:
    inputs = evidence["authoritative_inputs"]
    value = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-03",
        "repository_identity": inputs["authority"]["repository_identity"],
        "branch": inputs["authority"]["branch"],
        "head": inputs["authority"]["head"],
        "authority_digest": inputs["authority"]["authority_digest"],
        "discovery_digest": inputs["discovery"]["discovery_digest"],
        "contract_id": inputs["discovery"]["contract_id"],
        "evidence_digest": evidence["canonical_evidence_digest"],
        "verification_timestamp": evidence["verification_timestamp"],
        "verification_result": "PASS",
    }
    value["marker_digest"] = canonical_digest(value, "marker_digest")
    return value


def validate_marker(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    evidence = _load(_directory(repository) / "VERIFICATION.json")
    marker = _load(_directory(repository) / "VERIFIED")
    if evidence.get("canonical_evidence_digest") != canonical_digest(
        evidence, "canonical_evidence_digest"
    ):
        raise OA03GateVerificationError("OA-03 verification digest mismatch")
    if marker != _marker(evidence):
        raise OA03GateVerificationError("OA-03 marker binding mismatch")
    current = _current(repository, "oa03_marker_validation")
    expected = evidence.get("authoritative_inputs", {})
    if (
        _stable(current) != _stable(expected)
        or _outside_evidence(current["working_tree"])
        != _outside_evidence(expected["working_tree"])
    ):
        raise OA03GateVerificationError("OA-03 verification is stale")
    return marker


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    directory = _directory(repository)
    evidence_path = directory / "VERIFICATION.json"
    marker_path = directory / "VERIFIED"
    if marker_path.is_file():
        try:
            return _result(repository, validate_marker(repository), True)
        except OA03GateVerificationError:
            stale = _load(marker_path)
            identity = str(stale.get("marker_digest", _sha256(marker_path)))
            archive = directory / "attempts" / identity
            archive.mkdir(parents=True, exist_ok=True)
            for source in (evidence_path, marker_path):
                if not source.exists():
                    continue
                destination = archive / source.name
                if destination.exists():
                    if destination.read_bytes() != source.read_bytes():
                        raise OA03GateVerificationError(
                            "verification attempt archive collision"
                        )
                    source.unlink()
                else:
                    os.replace(source, destination)

    authoritative_inputs = _current(repository, "oa03_verification_start")
    checks = {}
    zeus = str(repository / "scripts/zeus")
    commands = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "oa02_receipt": [zeus, "gate", "receipt", "OA-02"],
        "oa03_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa03-mission-contract-discovery.py",
            "scripts/tests/test-zeus-oa02-controlled-authority.py",
            "scripts/tests/test-zeus-oa02-lifecycle.py",
            "scripts/tests/test-zeus-oa01-implementation.py",
        ],
    }
    for name, arguments in commands.items():
        if os.environ.get("ZEUS_OA03_VERIFY_INTERRUPT") == name:
            raise OA03GateVerificationError(f"interrupted during verification: {name}")
        checks[name] = run(repository, arguments)
        if checks[name]["exit_code"]:
            raise OA03GateVerificationError(f"OA-03 verification failed: {name}")

    # Revalidate at the evidence and marker protected boundaries.
    before_evidence = _current(repository, "oa03_verification_evidence")
    if _stable(before_evidence) != _stable(authoritative_inputs):
        raise OA03GateVerificationError("OA-03 inputs changed during verification")
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-03",
        "package_id": progressive_oa.PACKAGE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": before_evidence,
        "commands": checks,
        "assertions": {
            "positive": "PASS", "negative": "PASS", "replay": "PASS",
            "interruption": "PASS", "recovery": "PASS",
            "cumulative_oa01_through_oa03": "PASS",
            "protected_external_effect": "NONE",
            "operator_acceptance_recorded": False,
            "oa04_enabled": False,
        },
        "result": "PASS",
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    atomic_json(evidence_path, evidence)
    if os.environ.get("ZEUS_OA03_VERIFY_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA03GateVerificationError("interrupted after verification evidence")
    current = _current(repository, "oa03_verification_marker")
    if _stable(current) != _stable(before_evidence):
        raise OA03GateVerificationError("OA-03 inputs changed before marker")
    marker = _marker(evidence)
    atomic_json(marker_path, marker)
    return _result(repository, marker, False)


def _result(root: Path, marker: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-03",
        "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "marker": str((_directory(root) / "VERIFIED").relative_to(root)),
        "evidence_digest": marker["evidence_digest"],
        "idempotent_replay": replay,
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
    }
