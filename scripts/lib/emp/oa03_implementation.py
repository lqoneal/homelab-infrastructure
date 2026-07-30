"""Append-only OA-03 Mission Contract discovery implementation evidence."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.mission_contract_discovery import require
from scripts.lib.emp.oa02_implementation import atomic_json, canonical_digest, inventory, run


class OA03ImplementationError(ValueError):
    """OA-03 implementation cannot safely advance."""


def evidence_path(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-03/IMPLEMENTATION.json"


def validate_evidence(root: Path | str) -> dict[str, Any]:
    path = evidence_path(Path(root).resolve())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA03ImplementationError(f"OA-03 implementation evidence invalid: {error}") from error
    if value.get("canonical_evidence_digest") != canonical_digest(
        value, "canonical_evidence_digest"
    ):
        raise OA03ImplementationError("OA-03 implementation evidence digest mismatch")
    if value.get("result") != "IMPLEMENTATION_COMPLETE":
        raise OA03ImplementationError("OA-03 implementation evidence incomplete")
    return value


def qualify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-03", {})
    if state.get("active_gate") != "OA-03":
        raise OA03ImplementationError("OA-03 is not the sole active gate")
    if gate.get("state") == "AWAITING_OPERATOR_VERIFICATION":
        evidence = validate_evidence(repository)
        return _result(evidence, True)
    if gate.get("state") != "IMPLEMENTATION_REQUIRED":
        raise OA03ImplementationError(f"OA-03 cannot implement from {gate.get('state')}")

    if os.environ.get("ZEUS_OA03_INTERRUPT_BEFORE_DISCOVERY") == "1":
        raise OA03ImplementationError("interrupted before discovery")
    authority = ControlledMissionAuthority(
        repository, expected_gate="OA-03"
    ).require(boundary="oa03_implementation_start")
    discovery = require(repository)
    if discovery["contract_id"] != authority["contract_id"]:
        raise OA03ImplementationError("discovery and controlled authority disagree")
    if os.environ.get("ZEUS_OA03_INTERRUPT_AFTER_DISCOVERY") == "1":
        raise OA03ImplementationError("interrupted after discovery")

    zeus = str(repository / "scripts/zeus")
    checks = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "oa02_receipt": [zeus, "gate", "receipt", "OA-02"],
        "focused_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa03-mission-contract-discovery.py",
            "scripts/tests/test-zeus-oa02-controlled-authority.py",
            "scripts/tests/test-zeus-oa02-lifecycle.py",
            "scripts/tests/test-zeus-oa01-implementation.py",
        ],
    }
    commands = {}
    for name, arguments in checks.items():
        if os.environ.get("ZEUS_OA03_INTERRUPT_DURING_QUALIFICATION") == name:
            raise OA03ImplementationError(f"interrupted during qualification: {name}")
        commands[name] = run(repository, arguments)
        if commands[name]["exit_code"]:
            raise OA03ImplementationError(f"OA-03 implementation check failed: {name}")

    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA03-MISSION-CONTRACT-DISCOVERY-001",
        "gate_id": "OA-03",
        "package_id": progressive_oa.PACKAGE,
        "wop_id": authority["wop_id"],
        "mission_id": authority["mission_id"],
        "contract_id": authority["contract_id"],
        "repository_identity": authority["repository_identity"],
        "repository_root": authority["repository_root"],
        "branch": authority["branch"],
        "head": authority["head"],
        "upstream": authority["upstream"],
        "qualified_baseline": authority["qualified_baseline"],
        "authority": authority,
        "discovery": discovery,
        "oa01_acceptance_receipt": authority["oa01_acceptance_receipt"],
        "oa01_acceptance_digest": authority["oa01_acceptance_digest"],
        "oa02_acceptance_receipt": authority["oa02_acceptance_receipt"],
        "oa02_acceptance_digest": authority["oa02_acceptance_digest"],
        "implementation_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_tree": inventory(repository),
        "commands": commands,
        "assertions": {
            "exactly_one_applicable_contract": "PASS",
            "negative_fail_closed": "PASS",
            "replay": "PASS",
            "interruption_recovery": "PASS",
            "oa01_through_oa03_regression": "PASS",
            "oa03_sole_active_gate": "PASS",
            "later_gates_inactive": "PASS",
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False,
            "protected_external_effect": "NONE",
        },
        "result": "IMPLEMENTATION_COMPLETE",
    }
    evidence["canonical_evidence_digest"] = canonical_digest(
        evidence, "canonical_evidence_digest"
    )
    if os.environ.get("ZEUS_OA03_INTERRUPT_BEFORE_EVIDENCE") == "1":
        raise OA03ImplementationError("interrupted before evidence publication")
    path = evidence_path(repository)
    if path.exists():
        existing = validate_evidence(repository)
        if existing["canonical_evidence_digest"] != evidence["canonical_evidence_digest"]:
            archive = path.parent / "attempts" / existing["canonical_evidence_digest"] / path.name
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                os.replace(path, archive)
            elif archive.read_bytes() == path.read_bytes():
                path.unlink()
            else:
                raise OA03ImplementationError("implementation archive collision")
            atomic_json(path, evidence)
    else:
        atomic_json(path, evidence)
    if os.environ.get("ZEUS_OA03_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA03ImplementationError("interrupted after evidence publication")

    current_authority = ControlledMissionAuthority(
        repository, expected_gate="OA-03"
    ).require(boundary="oa03_implementation_state_transition")
    current_discovery = require(repository)
    if (
        current_authority["authority_digest"] != authority["authority_digest"]
        or current_discovery["discovery_digest"] != discovery["discovery_digest"]
    ):
        raise OA03ImplementationError("authority or discovery changed during implementation")
    current = progressive_oa.load_state(repository)
    if current.get("active_gate") != "OA-03" or current["gates"]["OA-03"]["state"] != "IMPLEMENTATION_REQUIRED":
        raise OA03ImplementationError("OA-03 runtime changed during implementation")
    if os.environ.get("ZEUS_OA03_INTERRUPT_BEFORE_TRANSITION") == "1":
        raise OA03ImplementationError("interrupted before state transition")
    current["gates"]["OA-03"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, current)
    return _result(evidence, False)


def _result(evidence: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-03",
        "result": "IMPLEMENTATION_COMPLETE",
        "state": "AWAITING_OPERATOR_VERIFICATION",
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
        "idempotent_replay": replay,
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
