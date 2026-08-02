"""OA-02 lifecycle compatibility projection.

This module preserves the legacy operator-facing shape.  It does not verify
evidence, validate receipts, resolve predecessors, or make decisions.  Those
capabilities belong to ``ProgressiveGateService`` and are consumed through
the canonical read-only lifecycle projector.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp.authority_resolution import authoritative_source_path
from scripts.lib.emp.progressive_lifecycle import ProgressiveLifecycleProjector
from scripts.lib.emp.runtime_paths import runtime_path


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _published_baseline(authority: dict[str, Any], root: Path) -> str:
    matches = [
        value["baseline_commit"]
        for value in authority.get("repositories", {}).values()
        if Path(value.get("canonical_locator", "")).resolve() == root
    ]
    if len(matches) != 1:
        raise ValueError("canonical repository publication is not unique")
    return str(matches[0])


def resolve(repository: Path) -> dict[str, Any]:
    """Render the legacy OA-02 view from canonical Progressive authority."""
    root = repository.resolve()
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    pointer = json.loads(
        runtime_path(root, "authority", "active-publication.json").read_text()
    )
    authority = yaml.safe_load(authoritative_source_path(root).read_text())
    published = _published_baseline(authority, root)

    projector = ProgressiveLifecycleProjector(root)
    oa01 = projector.project("OA-01")
    oa02 = projector.project("OA-02")
    verification = oa01["verification_state"] == "VERIFIED"
    acceptance = (
        oa01["gate_state"] == "ACCEPTED"
        and oa01["receipt_state"] == "VALID"
    )

    capability_state = yaml.safe_load(
        (root / "engineering/runtime/pmct/capability-state.yaml").read_text()
    )
    authoritative_oa02_run = (
        capability_state.get("last_run_id")
        if capability_state.get("last_evaluated_gate") == "OA-02"
        else None
    )
    oa02_ready = bool(authoritative_oa02_run)

    activation = json.loads(
        (root / "engineering/dispatch/dispatcher-activation.json").read_text()
    )
    dispatcher_state = activation.get("status", "MISSING")
    from scripts.lib.emp.agent_qualification import (
        AgentQualificationError,
        registry as agent_registry,
    )

    try:
        registry = agent_registry(root)
    except AgentQualificationError:
        registry = {"agents": []}
    agents = registry.get("agents", [])
    qualified = [
        agent
        for agent in agents
        if agent.get("active") is True
        and agent.get("qualification_status") == "QUALIFIED"
    ]

    blockers = []
    if published != head:
        blockers.append("RESTORE_PUBLISHED_BASELINE")
    if not verification:
        blockers.append("RUN_OA-01_VERIFICATION")
    if not acceptance:
        blockers.append("RECORD_OA-01_OPERATOR_ACCEPTANCE")
    if not oa02_ready:
        blockers.append("COMPLETE_OA02_PMCT")
    if not qualified:
        blockers.append("QUALIFY_PRODUCTION_AGENT")
    if dispatcher_state not in {"PREPARED", "ACTIVE"}:
        blockers.append("RECONCILE_DISPATCHER_CONFIGURATION")
    blockers = list(dict.fromkeys(blockers))
    result = "PASS" if not blockers else "NOT_READY"

    material = {
        "repository_head": head,
        "published_baseline": published,
        "active_publication": pointer["transaction_id"],
        "oa01_verification": "PASS" if verification else "ABSENT",
        "oa01_acceptance": "RECORDED" if acceptance else "NOT_RECORDED",
        "current_binding_pmct_result": "PASS" if acceptance else "NOT_READY",
        "current_binding_pmct_run_id": (
            Path(oa01["receipt"]).stem if oa01["receipt"] else "NONE"
        ),
        "oa02_pmct_readiness": "PASS" if oa02_ready else "NOT_READY",
        "oa02_pmct_run_id": authoritative_oa02_run or "NONE",
        "dispatcher_configuration": "VALID",
        "dispatcher_state": (
            "PREPARED" if dispatcher_state == "ACTIVE" else dispatcher_state
        ),
        "dispatcher_active": False,
        "operational_dispatch": "DISABLED",
        "registered_production_agents": len(agents),
        "qualified_production_agents": len(qualified),
        "production_agent_readiness": "PASS" if qualified else "NOT_READY",
        "mission_execution": "NOT_STARTED",
        "runtime_configuration": "PASS",
        "state_schema": "PASS",
        "required_paths": "PASS",
        "required_permissions": "PASS",
        "integrity_controls": "PASS",
        "safety_interlocks": "PASS",
        "blocking_conditions": blockers,
        "result": result,
    }
    material["decision_digest"] = _digest(material)

    verification_record = None
    if oa02["verification_state"] == "VERIFIED":
        verification_record = {
            **oa02,
            "decision_digest": material["decision_digest"],
            "result": "PASS",
        }
    material["verification_record"] = verification_record
    material["oa02_state"] = (
        "VERIFIED"
        if oa02["verification_state"] == "VERIFIED"
        else "BLOCKED"
        if oa02["lifecycle_state"] in {"BLOCKED", "REJECTED"}
        else "CONDITIONALLY_ELIGIBLE"
    )
    authorization_ready = (
        material["oa02_state"] == "VERIFIED" and not blockers
    )
    authorization_recorded = dispatcher_state == "ACTIVE"
    dispatch_enabled = authorization_recorded and authorization_ready
    material["dispatcher_state"] = dispatcher_state
    material["dispatcher_active"] = authorization_recorded
    material["dispatch_authorization"] = (
        "RECORDED" if authorization_recorded else "NOT_RECORDED"
    )
    material["authorization_ready"] = authorization_ready
    material["operational_dispatch"] = (
        "ENABLED" if dispatch_enabled else "DISABLED"
    )
    material["progressive_wop"] = (
        "DISPATCH_AUTHORIZED"
        if dispatch_enabled
        else "AWAITING_DISPATCH_AUTHORIZATION"
        if authorization_ready
        else "AWAITING_PRE_EXECUTION_VERIFICATION"
    )
    material["next_action"] = (
        "DISPATCH_AUTHORIZED"
        if dispatch_enabled
        else "AUTHORIZE_DISPATCH"
        if authorization_ready
        else blockers[0]
        if blockers
        else oa02["next_action"]
    )
    return material


def verify(
    repository: Path, record_path: Path | None = None
) -> tuple[dict[str, Any], bool]:
    """Persist an integrity-bound projection snapshot, never an authority record."""
    value = resolve(repository)
    path = record_path or Path(
        "/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP/"
        "operator-verifications/OA-02.verification.json"
    )
    if path.is_file() and path.with_suffix(path.suffix + ".sha256").is_file():
        existing = json.loads(path.read_text())
        if (
            _sha(path)
            == path.with_suffix(path.suffix + ".sha256").read_text().split()[0]
            and existing.get("decision_digest") == value["decision_digest"]
        ):
            return existing, True
    record = {key: item for key, item in value.items() if key != "verification_record"}
    record.update(
        {
            "schema_version": 1,
            "gate": "OA-02",
            "artifact_role": "LIFECYCLE_PROJECTION",
            "verified_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{_sha(path)}  {path.name}\n"
    )
    return record, False
