"""Integrity-bound production verification for Progressive OA-05."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.oa02_implementation import (
    atomic_json,
    canonical_digest,
    inventory,
    run,
)
from scripts.lib.emp.oa05_implementation import validate_evidence


class OA05GateVerificationError(ValueError):
    """OA-05 verification cannot safely be represented as current."""


def _directory(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-05"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA05GateVerificationError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise OA05GateVerificationError(f"{path}: object required")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable(value: dict[str, Any]) -> dict[str, Any]:
    stable = {key: item for key, item in value.items() if key != "working_tree"}
    authority = dict(stable["authority"])
    authority.pop("resolution_timestamp", None)
    authority.pop("protected_boundary", None)
    stable["authority"] = authority
    return stable


def _outside_evidence(value: dict[str, Any]) -> list[dict[str, str]]:
    prefix = str(progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-05/")
    return [
        item for item in value["entries"]
        if not item["path"].startswith(prefix)
    ]


def _current(root: Path, boundary: str) -> dict[str, Any]:
    state = progressive_oa.load_state(root)
    gate = state.get("gates", {}).get("OA-05", {})
    if (
        state.get("active_gate") != "OA-05"
        or gate.get("state") != "AWAITING_OPERATOR_VERIFICATION"
    ):
        raise OA05GateVerificationError(
            "OA-05 is not awaiting operator verification"
        )
    if gate.get("acceptance_receipt") is not None:
        raise OA05GateVerificationError("OA-05 acceptance already exists")
    for gate_id, item in state["gates"].items():
        if gate_id > "OA-05" and (
            item.get("state") != "PENDING"
            or item.get("acceptance_receipt") is not None
        ):
            raise OA05GateVerificationError(
                f"unexpected later-gate activity: {gate_id}"
            )
    authority = ControlledMissionAuthority(
        root, expected_gate="OA-05"
    ).require(boundary=boundary)
    implementation = validate_evidence(root)
    return {
        "authority": authority,
        "implementation_evidence": str(
            (
                root / progressive_oa.PACKAGE_PATH
                / "runtime/evidence/OA-05/IMPLEMENTATION.json"
            ).relative_to(root)
        ),
        "implementation_digest": implementation["canonical_evidence_digest"],
        "staging_contract_fields": implementation["staging_contract_fields"],
        "staging_contract_interface": implementation["staging_contract_interface"],
        "working_tree": inventory(root),
    }


def _marker(evidence: dict[str, Any]) -> dict[str, Any]:
    inputs = evidence["authoritative_inputs"]
    authority = inputs["authority"]
    value = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-05",
        "repository_identity": authority["repository_identity"],
        "branch": authority["branch"],
        "head": authority["head"],
        "contract_id": authority["contract_id"],
        "mission_id": authority["operational_mission_id"],
        "wop_id": authority["wop_id"],
        "authority_digest": authority["authority_digest"],
        "implementation_digest": inputs["implementation_digest"],
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
    if (
        evidence.get("canonical_evidence_digest")
        != canonical_digest(evidence, "canonical_evidence_digest")
        or marker != _marker(evidence)
    ):
        raise OA05GateVerificationError("OA-05 marker integrity or binding mismatch")
    current = _current(repository, "oa05_marker_validation")
    expected = evidence.get("authoritative_inputs", {})
    if (
        _stable(current) != _stable(expected)
        or _outside_evidence(current["working_tree"])
        != _outside_evidence(expected["working_tree"])
    ):
        raise OA05GateVerificationError("OA-05 verification is stale")
    return marker


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    directory = _directory(repository)
    evidence_path = directory / "VERIFICATION.json"
    marker_path = directory / "VERIFIED"
    if marker_path.is_file():
        try:
            return _result(repository, validate_marker(repository), True)
        except OA05GateVerificationError:
            stale = _load(marker_path)
            archive = directory / "attempts" / str(
                stale.get("marker_digest", _sha256(marker_path))
            )
            archive.mkdir(parents=True, exist_ok=True)
            for source in (evidence_path, marker_path):
                if not source.exists():
                    continue
                destination = archive / source.name
                if destination.exists():
                    if destination.read_bytes() != source.read_bytes():
                        raise OA05GateVerificationError(
                            "verification archive collision"
                        )
                    source.unlink()
                else:
                    os.replace(source, destination)

    authoritative_inputs = _current(repository, "oa05_verification_start")
    zeus = str(repository / "scripts/zeus")
    commands = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "oa02_receipt": [zeus, "gate", "receipt", "OA-02"],
        "oa03_receipt": [zeus, "gate", "receipt", "OA-03"],
        "oa04_receipt": [zeus, "gate", "receipt", "OA-04"],
        "oa05_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa05-mission-staging.py",
            "scripts/tests/test-zeus-stage1-runtime.py",
        ],
    }
    checks = {}
    for name, arguments in commands.items():
        if os.environ.get("ZEUS_OA05_VERIFY_INTERRUPT") == name:
            raise OA05GateVerificationError(f"interrupted during verification: {name}")
        checks[name] = run(repository, arguments)
        if checks[name]["exit_code"]:
            raise OA05GateVerificationError(f"OA-05 verification failed: {name}")

    before_evidence = _current(repository, "oa05_verification_evidence")
    if _stable(before_evidence) != _stable(authoritative_inputs):
        raise OA05GateVerificationError("OA-05 inputs changed during verification")
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-05",
        "package_id": progressive_oa.PACKAGE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": before_evidence,
        "commands": checks,
        "assertions": {
            "positive": "PASS",
            "negative": "PASS",
            "deterministic_staging": "PASS",
            "persistence": "PASS",
            "replay": "PASS",
            "interruption": "PASS",
            "restart_recovery": "PASS",
            "malformed_candidate_rejection": "PASS",
            "authorization_enforcement": "PASS",
            "fail_closed": "PASS",
            "cumulative_oa01_through_oa05": "PASS",
            "protected_external_effect": "NONE",
            "execution_agent_dispatched": False,
            "mission_executed": False,
            "operator_acceptance_recorded": False,
            "oa06_enabled": False,
        },
        "result": "PASS",
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    atomic_json(evidence_path, evidence)
    if os.environ.get("ZEUS_OA05_VERIFY_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA05GateVerificationError("interrupted after verification evidence")
    current = _current(repository, "oa05_verification_marker")
    if _stable(current) != _stable(before_evidence):
        raise OA05GateVerificationError("OA-05 inputs changed before marker")
    marker = _marker(evidence)
    atomic_json(marker_path, marker)
    return _result(repository, marker, False)


def _result(root: Path, marker: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-05",
        "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "marker": str((_directory(root) / "VERIFIED").relative_to(root)),
        "evidence_digest": marker["evidence_digest"],
        "idempotent_replay": replay,
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
        "execution_agent_dispatched": False,
        "mission_executed": False,
    }
