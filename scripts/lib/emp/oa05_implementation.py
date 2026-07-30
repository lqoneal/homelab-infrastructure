"""Append-only OA-05 Mission Staging Contract implementation evidence."""

from __future__ import annotations

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


class OA05ImplementationError(ValueError):
    """OA-05 implementation cannot safely advance."""


def evidence_path(root: Path) -> Path:
    return (
        root / progressive_oa.PACKAGE_PATH
        / "runtime/evidence/OA-05/IMPLEMENTATION.json"
    )


def validate_evidence(root: Path | str) -> dict[str, Any]:
    path = evidence_path(Path(root).resolve())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA05ImplementationError(
            f"OA-05 implementation evidence invalid: {error}"
        ) from error
    if (
        value.get("canonical_evidence_digest")
        != canonical_digest(value, "canonical_evidence_digest")
        or value.get("result") != "IMPLEMENTATION_COMPLETE"
        or value.get("capability") != "Mission Staging Contract"
    ):
        raise OA05ImplementationError("OA-05 implementation evidence integrity failure")
    return value


def _stable_authority(value: dict[str, Any]) -> dict[str, Any]:
    stable = dict(value)
    stable.pop("resolution_timestamp", None)
    stable.pop("protected_boundary", None)
    return stable


def qualify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-05", {})
    if state.get("active_gate") != "OA-05":
        raise OA05ImplementationError("OA-05 is not the sole active gate")
    if gate.get("state") == "AWAITING_OPERATOR_VERIFICATION":
        return _result(validate_evidence(repository), True)
    if gate.get("state") != "IMPLEMENTATION_REQUIRED":
        raise OA05ImplementationError(f"OA-05 cannot implement from {gate.get('state')}")
    if gate.get("acceptance_receipt") is not None:
        raise OA05ImplementationError("OA-05 acceptance already exists")
    if os.environ.get("ZEUS_OA05_INTERRUPT_BEFORE_AUTHORITY") == "1":
        raise OA05ImplementationError("interrupted before authority resolution")

    authority = ControlledMissionAuthority(
        repository, expected_gate="OA-05"
    ).require(boundary="oa05_implementation_start")
    if os.environ.get("ZEUS_OA05_INTERRUPT_AFTER_AUTHORITY") == "1":
        raise OA05ImplementationError("interrupted after authority resolution")

    zeus = str(repository / "scripts/zeus")
    checks = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "oa02_receipt": [zeus, "gate", "receipt", "OA-02"],
        "oa03_receipt": [zeus, "gate", "receipt", "OA-03"],
        "oa04_receipt": [zeus, "gate", "receipt", "OA-04"],
        "focused_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa05-mission-staging.py",
            "scripts/tests/test-zeus-stage1-runtime.py",
        ],
    }
    commands = {}
    for name, arguments in checks.items():
        if os.environ.get("ZEUS_OA05_INTERRUPT_DURING_QUALIFICATION") == name:
            raise OA05ImplementationError(f"interrupted during qualification: {name}")
        commands[name] = run(repository, arguments)
        if commands[name]["exit_code"]:
            raise OA05ImplementationError(f"OA-05 implementation check failed: {name}")

    contract_fields = [
        "mission_id", "wop_id", "objective", "scope", "dependencies",
        "priority", "candidate_state",
    ]
    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA05-MISSION-STAGING-001",
        "capability": "Mission Staging Contract",
        "gate_id": "OA-05",
        "package_id": progressive_oa.PACKAGE,
        "repository_identity": authority["repository_identity"],
        "repository_root": authority["repository_root"],
        "branch": authority["branch"],
        "head": authority["head"],
        "upstream": authority["upstream"],
        "qualified_baseline": authority["qualified_baseline"],
        "authority": authority,
        "staging_contract_fields": contract_fields,
        "staging_contract_interface": ["zeus submit", "zeus list", "zeus show"],
        "implementation_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_tree": inventory(repository),
        "commands": commands,
        "assertions": {
            "stable_identity": "PASS",
            "objective": "PASS",
            "scope": "PASS",
            "normalized_dependencies": "PASS",
            "priority": "PASS",
            "candidate_state": "PASS",
            "contract_digest": "PASS",
            "deterministic_staging": "PASS",
            "persistence": "PASS",
            "idempotent_replay": "PASS",
            "restart_recovery": "PASS",
            "malformed_candidate_rejection": "PASS",
            "authorization_enforcement": "PASS",
            "fail_closed": "PASS",
            "cumulative_oa01_through_oa05": "PASS",
            "protected_external_effect": "NONE",
            "execution_agent_dispatched": False,
            "mission_executed": False,
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False,
        },
        "result": "IMPLEMENTATION_COMPLETE",
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    if os.environ.get("ZEUS_OA05_INTERRUPT_BEFORE_EVIDENCE") == "1":
        raise OA05ImplementationError("interrupted before evidence publication")
    path = evidence_path(repository)
    if path.exists():
        existing = validate_evidence(repository)
        if existing["canonical_evidence_digest"] != evidence["canonical_evidence_digest"]:
            archive = (
                path.parent / "attempts"
                / existing["canonical_evidence_digest"] / path.name
            )
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                os.replace(path, archive)
            elif archive.read_bytes() == path.read_bytes():
                path.unlink()
            else:
                raise OA05ImplementationError("implementation archive collision")
            atomic_json(path, evidence)
    else:
        atomic_json(path, evidence)
    if os.environ.get("ZEUS_OA05_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA05ImplementationError("interrupted after evidence publication")

    current_authority = ControlledMissionAuthority(
        repository, expected_gate="OA-05"
    ).require(boundary="oa05_implementation_transition")
    if _stable_authority(current_authority) != _stable_authority(authority):
        raise OA05ImplementationError("authority changed during OA-05 implementation")
    current = progressive_oa.load_state(repository)
    if (
        current.get("active_gate") != "OA-05"
        or current["gates"]["OA-05"]["state"] != "IMPLEMENTATION_REQUIRED"
        or current["gates"]["OA-05"].get("acceptance_receipt") is not None
    ):
        raise OA05ImplementationError("OA-05 runtime changed during implementation")
    if os.environ.get("ZEUS_OA05_INTERRUPT_BEFORE_TRANSITION") == "1":
        raise OA05ImplementationError("interrupted before lifecycle transition")
    current["gates"]["OA-05"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, current)
    return _result(evidence, False)


def _result(evidence: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-05",
        "result": "IMPLEMENTATION_COMPLETE",
        "state": "AWAITING_OPERATOR_VERIFICATION",
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
        "execution_agent_dispatched": False,
        "mission_executed": False,
        "idempotent_replay": replay,
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
