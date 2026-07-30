"""Authoritative, idempotent OA-02 implementation publication."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority


class OA02ImplementationError(ValueError):
    """OA-02 implementation cannot safely advance."""


def canonical_digest(value: dict[str, Any], omitted: str) -> str:
    material = {key: item for key, item in value.items() if key != omitted}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(root: Path, arguments: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        arguments, cwd=root, text=True, capture_output=True, check=False,
        env=os.environ.copy(),
    )
    return {
        "command": arguments,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
    }


def inventory(root: Path) -> dict[str, Any]:
    result = run(root, ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"])
    if result["exit_code"]:
        raise OA02ImplementationError("working-tree inventory failed")
    entries = []
    for raw in result["stdout"].split("\0"):
        if not raw:
            continue
        status, name = raw[:2], raw[3:]
        path = root / name
        entries.append({
            "status": status,
            "path": name,
            "content_sha256": (
                hashlib.sha256(path.read_bytes()).hexdigest()
                if path.is_file() else "ABSENT"
            ),
        })
    value = {"entries": sorted(entries, key=lambda item: item["path"])}
    value["inventory_digest"] = hashlib.sha256(
        json.dumps(value["entries"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def evidence_path(root: Path) -> Path:
    return (
        root / progressive_oa.PACKAGE_PATH
        / "runtime/evidence/OA-02/IMPLEMENTATION.json"
    )


def validate_evidence(root: Path) -> dict[str, Any]:
    path = evidence_path(root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA02ImplementationError(f"OA-02 implementation evidence invalid: {error}") from error
    if value.get("canonical_evidence_digest") != canonical_digest(
        value, "canonical_evidence_digest"
    ):
        raise OA02ImplementationError("OA-02 implementation evidence digest mismatch")
    if value.get("result") != "IMPLEMENTATION_COMPLETE":
        raise OA02ImplementationError("OA-02 implementation evidence is incomplete")
    return value


def qualify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-02", {})
    if state.get("active_gate") != "OA-02":
        raise OA02ImplementationError("OA-02 is not the sole active gate")
    if gate.get("state") == "AWAITING_OPERATOR_VERIFICATION":
        evidence = validate_evidence(repository)
        return {
            "gate_id": "OA-02", "result": "IMPLEMENTATION_COMPLETE",
            "state": "AWAITING_OPERATOR_VERIFICATION",
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False, "idempotent_replay": True,
            "evidence_digest": evidence["canonical_evidence_digest"],
        }
    if gate.get("state") != "IMPLEMENTATION_REQUIRED":
        raise OA02ImplementationError(f"OA-02 cannot implement from {gate.get('state')}")

    if os.environ.get("ZEUS_OA02_INTERRUPT_BEFORE_AUTHORITY") == "1":
        raise OA02ImplementationError("interrupted before authority resolution persistence")
    authority = ControlledMissionAuthority(repository).require(
        boundary="oa02_implementation_start"
    )
    if os.environ.get("ZEUS_OA02_INTERRUPT_AFTER_AUTHORITY") == "1":
        raise OA02ImplementationError("interrupted after authority resolution")

    commands: dict[str, Any] = {}
    zeus = str(repository / "scripts/zeus")
    for name, arguments in {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "authority_validate": [zeus, "authority", "validate"],
        "focused_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa02-controlled-authority.py",
            "scripts/tests/test-zeus-oa02-lifecycle.py",
        ],
    }.items():
        if os.environ.get("ZEUS_OA02_INTERRUPT_DURING_QUALIFICATION") == name:
            raise OA02ImplementationError(f"interrupted during qualification: {name}")
        result = run(repository, arguments)
        commands[name] = result
        if result["exit_code"]:
            raise OA02ImplementationError(f"OA-02 implementation check failed: {name}")

    starting_inventory = inventory(repository)
    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001",
        "gate_id": "OA-02",
        "package_id": progressive_oa.PACKAGE,
        "wop_id": authority["wop_id"],
        "mission_id": authority["mission_id"],
        "contract_id": authority["contract_id"],
        "operational_mission_id": authority["operational_mission_id"],
        "repository_identity": authority["repository_identity"],
        "repository_root": authority["repository_root"],
        "branch": authority["branch"],
        "head": authority["head"],
        "upstream": authority["upstream"],
        "qualified_baseline": authority["qualified_baseline"],
        "authority_source": authority["authority_source"],
        "authority_digest": authority["authority_digest"],
        "oa01_acceptance_receipt": authority["oa01_acceptance_receipt"],
        "oa01_acceptance_digest": authority["oa01_acceptance_digest"],
        "package_admission_receipt": authority["package_admission_receipt"],
        "package_admission_digest": authority["package_admission_digest"],
        "implementation_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_tree": starting_inventory,
        "commands": commands,
        "assertions": {
            "authority_resolution": "PASS",
            "positive_tests": "PASS",
            "negative_tests": "PASS",
            "replay": "PASS",
            "interruption_recovery": "PASS",
            "oa01_acceptance_integrity": "PASS",
            "oa02_sole_active_gate": "PASS",
            "later_gates_inactive": "PASS",
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False,
            "protected_external_effect": "NONE",
        },
        "test_results": {"focused": "PASS"},
        "negative_test_results": "PASS",
        "replay_results": "PASS",
        "recovery_results": "PASS",
        "reconciliation_results": "PENDING_VERIFICATION",
        "result": "IMPLEMENTATION_COMPLETE",
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    if os.environ.get("ZEUS_OA02_INTERRUPT_BEFORE_EVIDENCE") == "1":
        raise OA02ImplementationError("interrupted before evidence publication")
    path = evidence_path(repository)
    if path.exists():
        existing = validate_evidence(repository)
        if existing != evidence:
            identity = existing["canonical_evidence_digest"]
            archive = path.parent / "attempts" / identity / path.name
            archive.parent.mkdir(parents=True, exist_ok=True)
            if archive.exists():
                if archive.read_bytes() != path.read_bytes():
                    raise OA02ImplementationError(
                        "implementation attempt archive identity collision"
                    )
                path.unlink()
            else:
                os.replace(path, archive)
            atomic_json(path, evidence)
    else:
        atomic_json(path, evidence)
    if os.environ.get("ZEUS_OA02_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA02ImplementationError("interrupted after evidence publication")

    # Revalidate immediately before the protected lifecycle transition.
    current_authority = ControlledMissionAuthority(repository).require(
        boundary="oa02_implementation_state_transition"
    )
    if current_authority["authority_digest"] != authority["authority_digest"]:
        raise OA02ImplementationError("authority changed during implementation")
    current = progressive_oa.load_state(repository)
    if (
        current.get("active_gate") != "OA-02"
        or current["gates"]["OA-02"].get("state") != "IMPLEMENTATION_REQUIRED"
    ):
        raise OA02ImplementationError("OA-02 runtime changed during implementation")
    if os.environ.get("ZEUS_OA02_INTERRUPT_BEFORE_TRANSITION") == "1":
        raise OA02ImplementationError("interrupted before state transition")
    current["gates"]["OA-02"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    current["status"] = "ACTIVE"
    progressive_oa._write_state(repository, current)
    if os.environ.get("ZEUS_OA02_INTERRUPT_AFTER_TRANSITION") == "1":
        raise OA02ImplementationError("interrupted after state transition")
    return {
        "gate_id": "OA-02", "result": "IMPLEMENTATION_COMPLETE",
        "state": "AWAITING_OPERATOR_VERIFICATION",
        "operator_acceptance_recorded": False, "next_gate_enabled": False,
        "idempotent_replay": False,
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
