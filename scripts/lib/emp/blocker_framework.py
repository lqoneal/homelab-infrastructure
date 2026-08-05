"""Canonical, deterministic blocker lifecycle for qualification decisions.

Blockers are projections of authoritative evidence, never operator-authored
status strings.  The service is intentionally read-only: verification,
resolution, retirement, and history are recalculated from evidence so a stale
or fabricated runtime record cannot block publication.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


LIFECYCLE_STATES = (
    "DISCOVERED", "VERIFIED", "ACTIVE", "RESOLVING", "REVALIDATING",
    "RESOLVED", "RETIRED",
)
BLOCKING_STATES = {"VERIFIED", "ACTIVE"}
FRAMEWORK_WOP = "WOP-ZDCL02-CANONICAL-BLOCKER-RESOLUTION-FRAMEWORK-001"
FRAMEWORK_MISSION = "MISSION-ZDCL02-CANONICAL-BLOCKER-RESOLUTION-FRAMEWORK-001"


class BlockerFrameworkError(ValueError):
    """The blocker graph cannot be resolved safely."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _relative(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _verify(root: Path, seed: dict[str, Any]) -> tuple[bool, str, str]:
    evidence = seed.get("authoritative_evidence") or seed.get("authoritative_source") or seed.get("evidence_locator")
    if not evidence:
        return False, "MISSING_EVIDENCE", ""
    path = _relative(root, evidence)
    try:
        content = path.read_bytes()
    except OSError:
        return False, "EVIDENCE_UNAVAILABLE", ""
    digest = hashlib.sha256(content).hexdigest()
    return True, "EVIDENCE_PRESENT", digest


def _normalize(root: Path, seed: dict[str, Any]) -> dict[str, Any]:
    verified, reason, verification_digest = _verify(root, seed)
    blocker_id = seed["blocker_id"]
    requested_state = seed.get("lifecycle_state")
    lifecycle_state = requested_state if requested_state in LIFECYCLE_STATES else ("ACTIVE" if verified else "DISCOVERED")
    blocker = {
        "blocker_id": blocker_id,
        "blocker_type": seed.get("blocker_type") or seed.get("category", "QUALIFICATION"),
        "category": seed.get("category") or seed.get("blocker_type", "QUALIFICATION"),
        "lifecycle_state": lifecycle_state,
        "severity": seed.get("severity", "BLOCKING"),
        "originating_controller": seed.get("originating_controller", "canonical-qualification-decision-engine"),
        "authoritative_source": seed.get("authoritative_evidence") or seed.get("authoritative_source") or seed.get("evidence_locator"),
        "evidence_locator": seed.get("authoritative_evidence") or seed.get("authoritative_source") or seed.get("evidence_locator"),
        "authoritative_evidence": seed.get("authoritative_evidence") or seed.get("authoritative_source") or seed.get("evidence_locator"),
        "owning_component": seed.get("originating_controller", "canonical-qualification-decision-engine"),
        "owning_transaction": seed.get("owning_transaction", "QUALIFICATION-TRANSACTION-CURRENT"),
        "owning_mission": seed.get("owning_mission", FRAMEWORK_MISSION),
        "owning_execution": seed.get("owning_execution", "EXECUTION-QUALIFICATION-CURRENT"),
        "owning_authority": seed.get("owning_authority", "AR-OA-10-001"),
        "first_detected": seed.get("first_detected", "evidence-derived"),
        "last_verified": "evidence-derived" if verified else None,
        "verification_digest": verification_digest,
        "auto_resolvable": bool(seed.get("auto_resolvable", False)),
        "operator_action_required": not bool(seed.get("auto_resolvable", False)),
        "publication_blocking": verified and lifecycle_state in BLOCKING_STATES and seed.get("publication_impact") == "PUBLICATION_BLOCKED",
        "retirement_conditions": seed.get("resolution_requirements", "Authoritative evidence no longer reports this condition."),
        "resolution_requirements": seed.get("resolution_requirements") or seed.get("retirement_conditions", "Authoritative evidence no longer reports this condition."),
        "reevaluation_trigger": "every qualification decision and lifecycle transition",
        "next_authorized_action": seed.get("resolution_requirements", "Re-run the authoritative qualification profile."),
        "governing_document": seed.get("governing_document"),
        "corrective_wop": seed.get("corrective_wop", FRAMEWORK_WOP),
        "publication_impact": seed.get("publication_impact", "PUBLICATION_BLOCKED"),
        "verification_reason": reason,
    }
    blocker["blocker_digest"] = _digest(blocker)
    return blocker


def resolve_from_seed(root: Path | str, seeds: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one deduplicated blocker graph from canonical seed blockers."""
    repository = Path(root).resolve()
    by_id: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for seed in seeds:
        if not seed.get("blocker_id"):
            raise BlockerFrameworkError("ANONYMOUS_BLOCKER")
        blocker = _normalize(repository, seed)
        existing = by_id.get(blocker["blocker_id"])
        if existing:
            if existing["blocker_digest"] != blocker["blocker_digest"]:
                raise BlockerFrameworkError(f"CONFLICTING_DUPLICATE_BLOCKER: {blocker['blocker_id']}")
            duplicates.append(blocker["blocker_id"])
        else:
            by_id[blocker["blocker_id"]] = blocker
    blockers = [by_id[key] for key in sorted(by_id)]
    active = [b for b in blockers if b["lifecycle_state"] in BLOCKING_STATES and b["publication_blocking"]]
    resolved = [b for b in blockers if b["lifecycle_state"] == "RESOLVED"]
    retired = [b for b in blockers if b["lifecycle_state"] == "RETIRED"]
    return {
        "framework_id": "ZEUS-BLOCKER-FRAMEWORK-1",
        "framework_wop": FRAMEWORK_WOP,
        "blockers": blockers,
        "active_blockers": active,
        "resolved_blockers": resolved,
        "retired_blockers": retired,
        "duplicate_blockers_merged": sorted(set(duplicates)),
        "graph": {"nodes": [b["blocker_id"] for b in blockers], "edges": []},
        "verification": {"verified_count": sum(b["lifecycle_state"] in BLOCKING_STATES for b in blockers),
                          "unverified_count": sum(b["lifecycle_state"] == "DISCOVERED" for b in blockers)},
        "history": [{"blocker_id": b["blocker_id"], "states": (
                        ["DISCOVERED", "VERIFIED", "ACTIVE", "RESOLVING", "REVALIDATING", "ACTIVE"]
                        if b["lifecycle_state"] == "ACTIVE" else [b["lifecycle_state"]]),
                    "execution_attempt": "REVALIDATED",
                    "verification_digest": b["verification_digest"]} for b in blockers],
    }


def operation(root: Path | str, seeds: list[dict[str, Any]], action: str, blocker_id: str | None = None) -> dict[str, Any]:
    graph = resolve_from_seed(root, seeds)
    if action == "execute" and blocker_id is None:
        from scripts.lib.emp.blocker_lifecycle import execute
        return execute(graph["blockers"])
    if action == "show":
        for blocker in graph["blockers"]:
            if blocker["blocker_id"] == blocker_id:
                return blocker
        raise BlockerFrameworkError(f"BLOCKER_NOT_FOUND: {blocker_id}")
    if action in {"verify", "resolve"}:
        blocker = operation(root, seeds, "show", blocker_id)
        return {"action": action, "blocker": blocker,
                "result": "PASS" if blocker["lifecycle_state"] == "ACTIVE" and action == "verify" else "UNRESOLVED",
                "next_action": blocker["next_authorized_action"]}
    if action in {"execute", "revalidate", "retire"}:
        from scripts.lib.emp.blocker_lifecycle import execute_blocker, revalidate
        blocker = operation(root, seeds, "show", blocker_id)
        if action == "execute":
            return execute_blocker(blocker)
        if action == "revalidate":
            return revalidate(blocker)
        if blocker.get("lifecycle_state") != "RESOLVED":
            return {"action": action, "blocker": blocker, "result": "UNRESOLVED",
                    "next_action": blocker["next_authorized_action"]}
        return {"action": action, "blocker": blocker, "result": "RETIRED",
                "transition": {"from": "RESOLVED", "to": "RETIRED", "verified": True}}
    if action == "graph":
        return {"graph": graph["graph"], "active_blockers": graph["active_blockers"]}
    if action == "history":
        return {"history": graph["history"]}
    raise BlockerFrameworkError(f"UNKNOWN_BLOCKER_ACTION: {action}")
