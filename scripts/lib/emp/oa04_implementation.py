"""Append-only OA-04 Project and Operational Context implementation evidence."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.project_operational_context import require
from scripts.lib.emp.oa02_implementation import atomic_json, canonical_digest, inventory, run


class OA04ImplementationError(ValueError):
    """OA-04 implementation cannot safely advance."""


def evidence_path(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-04/IMPLEMENTATION.json"


def validate_evidence(root: Path | str) -> dict[str, Any]:
    path = evidence_path(Path(root).resolve())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA04ImplementationError(f"OA-04 implementation evidence invalid: {error}") from error
    if value.get("canonical_evidence_digest") != canonical_digest(
        value, "canonical_evidence_digest"
    ) or value.get("result") != "IMPLEMENTATION_COMPLETE" or value.get(
        "capability"
    ) != "Project and Operational Context Reconstruction":
        raise OA04ImplementationError("OA-04 implementation evidence integrity failure")
    return value


def qualify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-04", {})
    if state.get("active_gate") != "OA-04":
        raise OA04ImplementationError("OA-04 is not the sole active gate")
    awaiting = gate.get("state") == "AWAITING_OPERATOR_VERIFICATION"
    if awaiting:
        try:
            existing = validate_evidence(repository)
            current = require(repository)
            if existing["project_operational_context"]["context_digest"] == current["context_digest"]:
                return _result(existing, True)
        except OA04ImplementationError:
            pass
    elif gate.get("state") != "IMPLEMENTATION_REQUIRED":
        raise OA04ImplementationError(f"OA-04 cannot implement from {gate.get('state')}")
    if os.environ.get("ZEUS_OA04_INTERRUPT_BEFORE_RESOLUTION") == "1":
        raise OA04ImplementationError("interrupted before context reconstruction")

    authority = ControlledMissionAuthority(
        repository, expected_gate="OA-04"
    ).require(boundary="oa04_implementation_start")
    context = require(repository)
    if context["governing_authority"]["digest"] != authority["authority_digest"]:
        raise OA04ImplementationError("context authority mismatch")
    if os.environ.get("ZEUS_OA04_INTERRUPT_AFTER_RESOLUTION") == "1":
        raise OA04ImplementationError("interrupted after context reconstruction")

    zeus = str(repository / "scripts/zeus")
    commands = {}
    checks = {
        "package_integrity": [
            str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")
        ],
        "oa01_receipt": [zeus, "gate", "receipt", "OA-01"],
        "oa02_receipt": [zeus, "gate", "receipt", "OA-02"],
        "oa03_receipt": [zeus, "gate", "receipt", "OA-03"],
        "focused_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa04-context-reconstruction.py",
            "scripts/tests/test-zeus-oa04-mission-resolution.py",
            "scripts/tests/test-zeus-oa03-mission-contract-discovery.py",
            "scripts/tests/test-zeus-oa02-controlled-authority.py",
            "scripts/tests/test-zeus-oa02-lifecycle.py",
            "scripts/tests/test-zeus-oa01-implementation.py",
        ],
    }
    for name, arguments in checks.items():
        if os.environ.get("ZEUS_OA04_INTERRUPT_DURING_QUALIFICATION") == name:
            raise OA04ImplementationError(f"interrupted during qualification: {name}")
        commands[name] = run(repository, arguments)
        if commands[name]["exit_code"]:
            raise OA04ImplementationError(f"OA-04 implementation check failed: {name}")

    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA04-CONTRACT-CONFORMANCE-REVIEW-001",
        "capability": "Project and Operational Context Reconstruction",
        "gate_id": "OA-04",
        "package_id": progressive_oa.PACKAGE,
        "repository_identity": authority["repository_identity"],
        "repository_root": authority["repository_root"],
        "branch": authority["branch"],
        "head": authority["head"],
        "upstream": authority["upstream"],
        "qualified_baseline": authority["qualified_baseline"],
        "authority": authority,
        "project_operational_context": context,
        "implementation_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_tree": inventory(repository),
        "commands": commands,
        "assertions": {
            "exactly_one_contract": "PASS",
            "exactly_one_mission": "PASS",
            "exactly_one_wop": "PASS",
            "exactly_one_execution_definition": "PASS",
            "exactly_one_authority_chain": "PASS",
            "complete_project_operational_context": "PASS",
            "repository_only": "PASS",
            "deterministic_replay": "PASS",
            "negative_fail_closed": "PASS",
            "interruption_recovery": "PASS",
            "cumulative_oa01_through_oa04": "PASS",
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
    if os.environ.get("ZEUS_OA04_INTERRUPT_BEFORE_EVIDENCE") == "1":
        raise OA04ImplementationError("interrupted before evidence publication")
    path = evidence_path(repository)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing["canonical_evidence_digest"] != evidence["canonical_evidence_digest"]:
            archive = path.parent / "attempts" / existing["canonical_evidence_digest"] / path.name
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                os.replace(path, archive)
            elif archive.read_bytes() == path.read_bytes():
                path.unlink()
            else:
                raise OA04ImplementationError("implementation archive collision")
            atomic_json(path, evidence)
    else:
        atomic_json(path, evidence)
    if os.environ.get("ZEUS_OA04_INTERRUPT_AFTER_EVIDENCE") == "1":
        raise OA04ImplementationError("interrupted after evidence publication")

    current_authority = ControlledMissionAuthority(
        repository, expected_gate="OA-04"
    ).require(boundary="oa04_implementation_transition")
    current_context = require(repository)
    if (
        current_authority["authority_digest"] != authority["authority_digest"]
        or current_context["context_digest"] != context["context_digest"]
    ):
        raise OA04ImplementationError("context reconstruction changed during implementation")
    current = progressive_oa.load_state(repository)
    if current.get("active_gate") != "OA-04" or current["gates"]["OA-04"]["state"] not in (
        "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"
    ):
        raise OA04ImplementationError("OA-04 runtime changed during implementation")
    if os.environ.get("ZEUS_OA04_INTERRUPT_BEFORE_TRANSITION") == "1":
        raise OA04ImplementationError("interrupted before lifecycle transition")
    if current["gates"]["OA-04"]["state"] == "IMPLEMENTATION_REQUIRED":
        current["gates"]["OA-04"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
        progressive_oa._write_state(repository, current)
    return _result(evidence, False)


def _result(evidence: dict[str, Any], replay: bool) -> dict[str, Any]:
    return {
        "gate_id": "OA-04",
        "result": "IMPLEMENTATION_COMPLETE",
        "state": "AWAITING_OPERATOR_VERIFICATION",
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
        "execution_agent_dispatched": False,
        "mission_executed": False,
        "idempotent_replay": replay,
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
