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
        return {"verification_passed": False, "acceptance_recorded": False}
    return {
        "verification_passed": service.verification_record(binding) is not None,
        "acceptance_recorded": service._matching_receipt(binding) is not None,
    }


def resolve_next_action(repository_root: Path | str) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    discovered = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    authority = _mapping(
        authoritative_source_path(root),
        "operational authority state",
    )
    activation = _mapping(
        root / "engineering/dispatch/dispatcher-activation.json",
        "dispatcher activation",
    )
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

    published = _published_baseline(authority, root)
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
    if activation.get("status") != "ACTIVE":
        blockers.append({
            "code": "DISPATCHER_INACTIVE",
            "detail": f"status={activation.get('status', 'MISSING')}",
        })
    if not qualified:
        blockers.append({
            "code": "NO_QUALIFIED_PRODUCTION_AGENT",
            "detail": f"registered={len(agents.get('agents', []))}",
        })
    if pmct.get("overall_result") != "PASS":
        blockers.append({
            "code": "PMCT_INCOMPLETE",
            "detail": f"overall={pmct.get('overall_result', 'UNKNOWN')}",
        })

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
    elif activation.get("status") != "ACTIVE":
        next_action = "Run OA-02 pre-execution verification"
        action_code = "RUN_OA-02_PRE_EXECUTION_VERIFICATION"
    elif not qualified:
        next_action = "Qualify first production execution agent"
        action_code = "QUALIFY_PRODUCTION_AGENT"
    elif pmct.get("overall_result") != "PASS":
        next_action = f"Execute and reconcile PMCT gate {gate}"
        action_code = "EXECUTE_PMCT_GATE"
    else:
        next_action = "Request Operational Alpha production-promotion decision"
        action_code = "REQUEST_PRODUCTION_PROMOTION"

    production_ready = (
        not blockers
        and all(
            item.get("status") == "PASS"
            for item in pmct.get("gates", {}).values()
        )
    )
    mode = "PRODUCTION" if production_ready else "BETA"
    result = "READY" if production_ready else "NOT_READY"
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
            "status": str(activation.get("status", "MISSING")),
            "active": activation.get("status") == "ACTIVE",
        },
        "production_agent_registry": {
            "status": "EMPTY" if not agents.get("agents") else "POPULATED",
            "registered_count": len(agents.get("agents", [])),
            "qualified_active_count": len(qualified),
        },
        "pmct": {
            "status": str(pmct.get("overall_result", "UNKNOWN")),
            "last_evaluated_gate": pmct.get("last_evaluated_gate"),
        },
        "oa01_lifecycle": {
            "operator_verification": (
                "PASS" if oa01["verification_passed"] else "ABSENT"
            ),
            "operator_acceptance": (
                "RECORDED" if oa01["acceptance_recorded"] else "NOT_RECORDED"
            ),
        },
        "operational_dispatch": "ENABLED" if production_ready else "DISABLED",
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

Result:
{value['result']}

ZEUS_MODE={value['zeus_mode']}
ZEUS_NEXT_ACTION={action['code']}
ZEUS_NEXT_ACTION_RESULT={value['result']}
ZEUS_DECISION_DIGEST={value['decision_digest']}
"""
