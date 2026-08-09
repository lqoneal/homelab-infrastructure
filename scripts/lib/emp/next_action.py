#!/usr/bin/env python3
"""Read-only authoritative next-action resolution for Zeus BETA."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.authority_resolution import authoritative_source_path
from scripts.lib.emp.gate_approval import GateApprovalError, GateApprovalService
from scripts.lib.emp.oa02_lifecycle import resolve as resolve_oa02
from scripts.lib.emp.repository_projection import project as project_repository


class NextActionError(ValueError):
    """Authoritative state cannot be inspected safely."""


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _mapping(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.suffix == ".json"
            else yaml.safe_load(path.read_text(encoding="utf-8"))
        )
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise NextActionError(f"{label} is unreadable: {error}") from error
    if not isinstance(value, Mapping):
        raise NextActionError(f"{label} must be an object")
    return value


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise NextActionError(result.stderr.strip() or "repository inspection failed")
    return result.stdout.strip()


def _published_baseline(authority: Mapping[str, Any], root: Path) -> str | None:
    for record in authority.get("repositories", {}).values():
        if (
            isinstance(record, Mapping)
            and Path(str(record.get("canonical_locator", ""))).resolve() == root
        ):
            return str(record.get("baseline_commit", "")) or None
    return None


def _active_work(registry: Mapping[str, Any]) -> list[str]:
    items = registry.get("entities", {}).get("work_items", [])
    return sorted(
        str(item.get("authority_reference"))
        for item in items
        if isinstance(item, Mapping)
        and item.get("management_state") == "active"
        and str(item.get("authority_reference", "")).startswith("ZEUS-")
    )


def _oa01_lifecycle(root: Path) -> dict[str, bool]:
    """Resolve only integrity-valid, current-binding OA-01 lifecycle evidence."""
    service = GateApprovalService.configured(root)
    try:
        binding = service.binding("OA-01", require_clean=False)
    except GateApprovalError:
        return {
            "verification_passed": False,
            "acceptance_recorded": False,
            "revalidation_required": False,
        }
    milestone = service.gate_milestone(binding)
    carry = milestone.get("carry_forward") or {}
    return {
        "verification_passed": milestone["verification"] == "PASS",
        "acceptance_recorded": milestone["acceptance"] == "RECORDED",
        "revalidation_required": bool(carry.get("oa01_revalidation_required")),
    }


def resolve_next_action(repository_root: Path | str) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    # Active Operational Alpha state is owned by the EMM-bound Mission
    # Knowledge Model.  The older authority/PMCT resolver remains below for
    # explicit historical compatibility consumers only.
    from scripts.lib.eos import mission_knowledge
    try:
        projection = mission_knowledge.next_action(root)
    except mission_knowledge.MissionKnowledgeError:
        # Fixture and historical callers may intentionally exercise the
        # pre-MKM resolver.  Active Zeus mission controllers never take this
        # compatibility branch; they call mission_knowledge directly.
        projection = None
    if projection is not None:
        return {
        "schema_version": 1,
        "resolver": projection["resolver"],
        "mission": "Zeus Operational Alpha",
        "current_mission": projection["current_mission"],
        "current_gate": projection["current_mission"],
        "current_lifecycle": projection["current_lifecycle"],
        "current_classification": projection["current_classification"],
        "blocking_conditions": [
            {"code": item, "detail": item}
            for item in projection["blocking_conditions"]
        ],
        "missing_capabilities": projection["missing_capabilities"],
        "next_authorized_action": projection["next_authorized_action"],
        "historical_progressive_runtime": "EXCLUDED_EVIDENCE_ONLY",
        "result": "READY",
            "decision_digest": digest(projection),
        }
    repository_projection = project_repository(root)
    if repository_projection.get("result") != "PASS":
        raise NextActionError(
            "; ".join(repository_projection.get("errors", []))
            or "canonical repository projection failed"
        )
    discovered = Path(repository_projection["repository_root"]).resolve()
    head = repository_projection["head"]
    branch = repository_projection.get("branch") or ""
    authority = _mapping(
        authoritative_source_path(root),
        "operational authority state",
    )
    activation = _mapping(
        root / "engineering/dispatch/dispatcher-activation.json",
        "dispatcher activation",
    )
    # Qualification records are the authoritative registry.  The dispatcher
    # projection is intentionally derived lazily and must not be required for
    # a pre-dispatch lifecycle decision.
    from scripts.lib.emp.agent_qualification import (
        AgentQualificationError,
        registry as agent_registry,
    )
    try:
        agents = agent_registry(root)
    except (AgentQualificationError, GateApprovalError, OSError, ValueError):
        # Before OA-01 is bindable there can be no valid qualified agent.  A
        # legacy projection is diagnostic-only in that early lifecycle phase.
        agents = _mapping(
            root / "engineering/dispatch/execution-agent-registry.json",
            "execution-agent registry",
        )
    pmct = _mapping(
        root / "engineering/runtime/pmct/capability-state.yaml", "PMCT state"
    )
    registry = _mapping(
        root / "engineering/registry/work-registry.yaml", "work registry"
    )

    published = repository_projection["origin_main"]
    oa01 = _oa01_lifecycle(root)
    gate = pmct.get("last_evaluated_gate") or "OA-01"
    qualified = [
        item for item in agents.get("agents", [])
        if isinstance(item, Mapping)
        and item.get("active") is True
        and item.get("qualification_status") == "QUALIFIED"
    ]
    blockers: list[dict[str, str]] = []
    if discovered != root:
        blockers.append({"code": "REPOSITORY_IDENTITY_MISMATCH", "detail": str(discovered)})
    if authority.get("operationally_configured") is not True:
        blockers.append({"code": "AUTHORITY_NOT_CONFIGURED", "detail": "operational authority is not configured"})
    if published != head:
        blockers.append({
            "code": "REPOSITORY_BASELINE_MISMATCH",
            "detail": f"published={published} implementation={head}",
        })
    if not oa01["verification_passed"]:
        blockers.append({
            "code": "OA-01_OPERATOR_VERIFICATION_REQUIRED",
            "detail": "no integrity-valid verification matches the current binding",
        })
    elif not oa01["acceptance_recorded"]:
        blockers.append({
            "code": "OA-01_OPERATOR_ACCEPTANCE_REQUIRED",
            "detail": "no integrity-valid acceptance matches the current binding",
        })
    oa02 = None
    if published == head and oa01["verification_passed"] and oa01["acceptance_recorded"]:
        try:
            oa02 = resolve_oa02(root)
        except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError):
            oa02 = None
        if oa02 is not None:
            blockers.extend(
                {"code": code, "detail": "OA-02 lifecycle prerequisite"}
                for code in oa02["blocking_conditions"]
            )

    if discovered != root:
        next_action = "Restore authoritative repository identity"
        action_code = "RESTORE_REPOSITORY_IDENTITY"
    elif authority.get("operationally_configured") is not True:
        next_action = "Restore controlled operational authority"
        action_code = "RESTORE_OPERATIONAL_AUTHORITY"
    elif published != head:
        next_action = "Publish signed repository baseline for current implementation HEAD"
        action_code = "PUBLISH_SIGNED_REPOSITORY_BASELINE"
    elif not oa01["verification_passed"]:
        next_action = "Run independent OA-01 operator verification"
        action_code = "RUN_OA-01_VERIFICATION"
    elif not oa01["acceptance_recorded"]:
        next_action = "Record explicit OA-01 operator acceptance"
        action_code = "RECORD_OA-01_OPERATOR_ACCEPTANCE"
    elif oa02 is not None:
        action_code = oa02["next_action"]
        next_action = action_code.replace("_", " ").title()
    else:
        next_action = "Run OA-02 pre-execution verification"
        action_code = "RUN_OA-02_PRE_EXECUTION_VERIFICATION"

    # OA-02 owns the shared lifecycle projection.  Readiness to authorize and
    # actual dispatch enablement are deliberately separate states.
    authorization_ready = bool(oa02 and oa02["authorization_ready"] and not blockers)
    operational_dispatch = (
        "ENABLED"
        if oa02 is not None
        and oa02["operational_dispatch"] == "ENABLED"
        and not blockers
        else "DISABLED"
    )
    mode = "BETA"
    result = "READY" if authorization_ready else "NOT_READY"
    value = {
        "schema_version": 1,
        "zeus_mode": mode,
        "mission": "Zeus Operational Alpha",
        "current_gate": gate,
        "repository": {
            "identity": str(discovered),
            "identity_valid": discovered == root,
            "branch": branch,
            "implementation_baseline": head,
            "published_baseline": published,
            "baseline_matches": published == head,
        },
        "authority": {
            "status": (
                "VALID" if authority.get("operationally_configured") is True
                else "RESTORATION_REQUIRED"
            ),
            "operationally_configured": bool(
                authority.get("operationally_configured")
            ),
            "active_work_authority": _active_work(registry),
        },
        "dispatcher": {
            "status": (
                oa02["dispatcher_state"]
                if oa02 is not None
                else str(activation.get("status", "MISSING"))
            ),
            "active": bool(oa02 and oa02["dispatcher_active"]),
        },
        "production_agent_registry": {
            "status": "EMPTY" if not agents.get("agents") else "POPULATED",
            "registered_count": len(agents.get("agents", [])),
            "qualified_active_count": len(qualified),
        },
        "pmct": {
            "status": (
                oa02["current_binding_pmct_result"]
                if oa02 is not None
                else str(pmct.get("overall_result", "UNKNOWN"))
            ),
            "last_evaluated_gate": pmct.get("last_evaluated_gate"),
            "oa02_readiness": (
                oa02["oa02_pmct_readiness"] if oa02 is not None else "NOT_READY"
            ),
        },
        "oa01_lifecycle": {
            "operator_verification": (
                "PASS" if oa01["verification_passed"] else "ABSENT"
            ),
            "operator_acceptance": (
                "RECORDED" if oa01["acceptance_recorded"] else "NOT_RECORDED"
            ),
            "revalidation_required": (
                "YES" if oa01.get("revalidation_required", False) else "NO"
            ),
        },
        "operational_dispatch": operational_dispatch,
        "blocking_conditions": blockers,
        "next_authorized_action": {
            "code": action_code,
            "description": next_action,
            "requires_separate_transition_authority": action_code not in {
                "EXECUTE_PMCT_GATE"
            },
        },
        "result": result,
    }
    value["decision_digest"] = digest(value)
    return value


def human_text(value: Mapping[str, Any]) -> str:
    repo = value["repository"]
    authority = value["authority"]
    dispatcher = value["dispatcher"]
    agents = value["production_agent_registry"]
    pmct = value["pmct"]
    action = value["next_authorized_action"]
    blockers = "\n".join(
        f"- {item['code']}: {item['detail']}"
        for item in value["blocking_conditions"]
    ) or "- None"
    work = ", ".join(authority["active_work_authority"]) or "NONE"
    recommendation = ""
    if action.get("wop"):
        recommendation = f"""
Recommendation:
{action['description']}

Objective:
{action.get('objective') or 'Authoritative objective unavailable'}

Expected Outcome:
{action.get('expected_outcome') or 'No successor outcome is authorized'}
"""
    return f"""ZEUS MODE: {value['zeus_mode']}

Mission:
{value['mission']}

Current Gate:
{value['current_gate']}

Implementation Baseline:
{repo['implementation_baseline']}

Published Baseline:
{repo['published_baseline']}

Authority:
{authority['status']}

Current Work Authority:
{work}

Dispatcher:
{dispatcher['status']}

Production Agent Registry:
{agents['status']}

PMCT:
{pmct['status']}

Operational Dispatch:
{value['operational_dispatch']}

Blocking Conditions:
{blockers}

Next Authorized Action:
{action['description']}
{recommendation}

Result:
{value['result']}

ZEUS_MODE={value['zeus_mode']}
ZEUS_NEXT_ACTION={action['code']}
ZEUS_NEXT_ACTION_RESULT={value['result']}
ZEUS_DECISION_DIGEST={value['decision_digest']}
"""
