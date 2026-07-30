"""Production verification and integrity marker for Progressive OA-02."""

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
    atomic_json, canonical_digest, inventory, run, validate_evidence,
)


class OA02GateVerificationError(ValueError):
    """OA-02 verification cannot qualify or be represented as current."""


EVIDENCE_NAME = "VERIFICATION.json"
MARKER_NAME = "VERIFIED"


def _directory(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-02"


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA02GateVerificationError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise OA02GateVerificationError(f"{path}: object required")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory_without_oa02(value: dict[str, Any]) -> list[dict[str, str]]:
    prefix = str(progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-02/")
    return [
        item for item in value["entries"]
        if not item["path"].startswith(prefix)
    ]


def _stable_inputs(value: dict[str, Any]) -> dict[str, Any]:
    stable = {key: item for key, item in value.items() if key != "working_tree"}
    authority = dict(stable.get("authority", {}))
    authority.pop("resolution_timestamp", None)
    authority.pop("protected_boundary", None)
    stable["authority"] = authority
    return stable


def _current(root: Path) -> dict[str, Any]:
    state = progressive_oa.load_state(root)
    if (
        state.get("active_gate") != "OA-02"
        or state.get("gates", {}).get("OA-02", {}).get("state")
        != "AWAITING_OPERATOR_VERIFICATION"
    ):
        raise OA02GateVerificationError("OA-02 is not awaiting operator verification")
    if state["gates"]["OA-02"].get("acceptance_receipt") is not None:
        raise OA02GateVerificationError("OA-02 acceptance already exists")
    for gate_id, item in state["gates"].items():
        if gate_id > "OA-02" and (
            item.get("state") != "PENDING" or item.get("acceptance_receipt") is not None
        ):
            raise OA02GateVerificationError(f"unexpected later-gate activity: {gate_id}")
    authority = ControlledMissionAuthority(root).require(
        boundary="oa02_verification"
    )
    implementation = validate_evidence(root)
    return {
        "authority": authority,
        "implementation_evidence": str(
            (
                root / progressive_oa.PACKAGE_PATH
                / "runtime/evidence/OA-02/IMPLEMENTATION.json"
            ).relative_to(root)
        ),
        "implementation_digest": implementation["canonical_evidence_digest"],
        "working_tree": inventory(root),
    }


def _marker(root: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    authority = evidence["authoritative_inputs"]["authority"]
    value = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-02",
        "repository_identity": authority["repository_identity"],
        "repository_root": authority["repository_root"],
        "branch": authority["branch"],
        "head": authority["head"],
        "authority_source": authority["authority_source"],
        "authority_digest": authority["authority_digest"],
        "evidence_digest": evidence["canonical_evidence_digest"],
        "verification_timestamp": evidence["verification_timestamp"],
        "verification_result": "PASS",
    }
    value["marker_digest"] = canonical_digest(value, "marker_digest")
    return value


def validate_marker(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    directory = _directory(repository)
    evidence = _json(directory / EVIDENCE_NAME)
    marker = _json(directory / MARKER_NAME)
    if evidence.get("canonical_evidence_digest") != canonical_digest(
        evidence, "canonical_evidence_digest"
    ):
        raise OA02GateVerificationError("OA-02 verification evidence digest mismatch")
    if marker.get("marker_digest") != canonical_digest(marker, "marker_digest"):
        raise OA02GateVerificationError("OA-02 marker digest mismatch")
    if marker != _marker(repository, evidence):
        raise OA02GateVerificationError("OA-02 marker binding mismatch")
    current = _current(repository)
    expected = evidence.get("authoritative_inputs")
    if not isinstance(expected, dict):
        raise OA02GateVerificationError("OA-02 authoritative inputs missing")
    if (
        _stable_inputs(current) != _stable_inputs(expected)
        or _inventory_without_oa02(current["working_tree"])
        != _inventory_without_oa02(expected["working_tree"])
    ):
        raise OA02GateVerificationError("OA-02 verification is stale")
    return marker


def _result(root: Path, marker: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-02",
        "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "marker": str((_directory(root) / MARKER_NAME).relative_to(root)),
        "evidence_digest": marker["evidence_digest"],
        "idempotent_replay": replay,
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
    }


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    directory = _directory(repository)
    evidence_path = directory / EVIDENCE_NAME
    marker_path = directory / MARKER_NAME
    if marker_path.is_file():
        try:
            return _result(repository, validate_marker(repository), True)
        except OA02GateVerificationError:
            stale = _json(marker_path)
            identity = str(stale.get("marker_digest", _sha256(marker_path)))
            archive = directory / "attempts" / identity
            archive.mkdir(parents=True, exist_ok=True)
            for source in (evidence_path, marker_path):
                if not source.exists():
                    continue
                destination = archive / source.name
                if destination.exists():
                    if destination.read_bytes() != source.read_bytes():
                        raise OA02GateVerificationError(
                            "verification attempt archive identity collision"
                        )
                    source.unlink()
                else:
                    os.replace(source, destination)

    # Durable recovery: evidence is already a completed idempotent operation.
    if evidence_path.is_file():
        evidence = _json(evidence_path)
        if evidence.get("canonical_evidence_digest") != canonical_digest(
            evidence, "canonical_evidence_digest"
        ):
            raise OA02GateVerificationError("partial verification evidence is invalid")
        current = _current(repository)
        expected = evidence.get("authoritative_inputs", {})
        if (
            _stable_inputs(current) != _stable_inputs(expected)
            or _inventory_without_oa02(current["working_tree"])
            != _inventory_without_oa02(expected["working_tree"])
        ):
            identity = str(
                evidence.get("canonical_evidence_digest", _sha256(evidence_path))
            )
            archive = directory / "attempts" / identity / EVIDENCE_NAME
            archive.parent.mkdir(parents=True, exist_ok=True)
            if archive.exists():
                if archive.read_bytes() != evidence_path.read_bytes():
                    raise OA02GateVerificationError(
                        "verification evidence archive identity collision"
                    )
                evidence_path.unlink()
            else:
                os.replace(evidence_path, archive)
        else:
            marker = _marker(repository, evidence)
            atomic_json(marker_path, marker)
            return _result(repository, validate_marker(repository), True)

    starting = _current(repository)
    if os.environ.get("ZEUS_OA02_VERIFY_INTERRUPT_AFTER_AUTHORITY") == "1":
        raise OA02GateVerificationError("interrupted after verification authority resolution")
    zeus = str(repository / "scripts/zeus")
    commands: dict[str, Any] = {}
    command_map = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "positive_negative_replay_recovery": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa02-controlled-authority.py",
            "scripts/tests/test-zeus-oa02-lifecycle.py",
        ],
        "scripts_regression": [
            "python3", "-m", "unittest", "discover",
            "-s", "scripts/tests", "-p", "test*.py",
        ],
        "oa_regression": [
            "python3", "-m", "unittest", "discover",
            "-s", "engineering/tests/zeus-operational-alpha/tests",
            "-p", "test*.py",
        ],
        "repository_health": ["scripts/engctl", "repository", "health"],
        "eos_sync": ["scripts/engctl", "eos", "sync-validate"],
        "registry": ["scripts/engctl", "registry", "validate"],
        "aggregate": ["scripts/engctl", "validate"],
    }
    for name, arguments in command_map.items():
        if os.environ.get("ZEUS_OA02_VERIFY_INTERRUPT_DURING") == name:
            raise OA02GateVerificationError(f"interrupted during verification: {name}")
        result = run(repository, arguments)
        commands[name] = result
        if result["exit_code"]:
            raise OA02GateVerificationError(f"OA-02 verification check failed: {name}")

    # Revalidate after every potentially long-running qualification boundary.
    ending = _current(repository)
    if (
        starting["authority"]["authority_digest"]
        != ending["authority"]["authority_digest"]
    ):
        raise OA02GateVerificationError("authority changed during verification")
    if _inventory_without_oa02(starting["working_tree"]) != (
        _inventory_without_oa02(ending["working_tree"])
    ):
        raise OA02GateVerificationError("unexplained working-tree mutation")
    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001",
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-02",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": ending,
        "commands": commands,
        "assertions": {
            "positive_tests": "PASS",
            "negative_fail_closed": "PASS",
            "replay": "PASS",
            "interruption_recovery": "PASS",
            "cumulative_regression_through": "OA-02",
            "repository_health": "PASS",
            "eos_synchronization": "PASS",
            "registry_validation": "PASS",
            "aggregate_validation": "PASS",
            "controlled_record_reconciliation": "PASS",
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False,
            "protected_external_effect": "NONE",
        },
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    if os.environ.get("ZEUS_OA02_VERIFY_INTERRUPT_BEFORE_EVIDENCE") == "1":
        raise OA02GateVerificationError("interrupted before verification evidence")
    atomic_json(evidence_path, evidence)
    if os.environ.get("ZEUS_OA02_VERIFY_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA02GateVerificationError("interrupted after verification evidence")
    marker = _marker(repository, evidence)
    atomic_json(marker_path, marker)
    if os.environ.get("ZEUS_OA02_VERIFY_INTERRUPT_AFTER_MARKER") == "1":
        raise OA02GateVerificationError("interrupted after verification marker")
    return _result(repository, validate_marker(repository), False)
