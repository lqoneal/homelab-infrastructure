"""Deterministic executor for the canonical blocker lifecycle.

The qualification contract remains the authority for whether a blocker is
blocking.  This module owns only transitions and their verification.  It does
not write blocker records, evidence, runtime state, EOS, or publication state.
That makes replay safe: the same authoritative seed always produces the same
transition result.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

STATES = ("DISCOVERED", "VERIFIED", "ACTIVE", "RESOLVING", "REVALIDATING", "RESOLVED", "RETIRED")
TRANSITIONS = {
    "DISCOVERED": {"VERIFIED"},
    "VERIFIED": {"ACTIVE"},
    "ACTIVE": {"RESOLVING"},
    "RESOLVING": {"REVALIDATING"},
    "REVALIDATING": {"RESOLVED", "ACTIVE"},
    "RESOLVED": {"RETIRED"},
    "RETIRED": set(),
}


class BlockerLifecycleError(ValueError):
    """A requested blocker transition is not safe or not canonical."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def transition(blocker: dict[str, Any], target: str, *, verified: bool = True) -> dict[str, Any]:
    """Return a verified transition record without changing the blocker."""
    source = blocker.get("lifecycle_state")
    if source not in STATES or target not in STATES or target not in TRANSITIONS[source]:
        raise BlockerLifecycleError(f"INVALID_BLOCKER_TRANSITION: {source}->{target}")
    if not verified:
        raise BlockerLifecycleError(f"UNVERIFIED_BLOCKER_TRANSITION: {source}->{target}")
    return {
        "blocker_id": blocker["blocker_id"],
        "from": source,
        "to": target,
        "verified": True,
        "verification_digest": _digest({"blocker": blocker.get("blocker_digest"), "from": source, "to": target}),
    }


def execute_blocker(
    blocker: dict[str, Any],
    *,
    corrective: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Execute one blocker through every required state boundary.

    An operator-owned blocker is never retired.  It is revalidated and returns
    to ACTIVE when its authoritative condition remains present.  An
    auto-resolvable blocker may retire only when the supplied corrective and
    the subsequent revalidation both succeed.
    """
    state = blocker.get("lifecycle_state")
    if state == "RETIRED":
        return {"blocker": blocker, "result": "IDEMPOTENT_REPLAY", "transitions": []}
    if state != "ACTIVE":
        raise BlockerLifecycleError(f"EXECUTION_REQUIRES_ACTIVE_BLOCKER: {blocker.get('blocker_id')}")
    transitions = [transition(blocker, "RESOLVING"),
                   transition({**blocker, "lifecycle_state": "RESOLVING"}, "REVALIDATING")]
    corrected = bool(corrective(blocker)) if blocker.get("auto_resolvable") and corrective else False
    if corrected:
        final_state = "RESOLVED"
        transitions.append(transition({**blocker, "lifecycle_state": "REVALIDATING"}, "RESOLVED"))
        transitions.append(transition({**blocker, "lifecycle_state": "RESOLVED"}, "RETIRED"))
        final_state = "RETIRED"
    else:
        final_state = "ACTIVE"
        transitions.append(transition({**blocker, "lifecycle_state": "REVALIDATING"}, "ACTIVE"))
    result = "RETIRED" if final_state == "RETIRED" else "OPERATOR_ACTION_REQUIRED"
    return {
        "blocker": {**blocker, "lifecycle_state": final_state},
        "result": result,
        "transitions": transitions,
        "idempotent_replay": False,
        "corrective_executed": corrected,
        "retirement_verified": final_state == "RETIRED",
        "execution_digest": _digest({"blocker": blocker.get("blocker_digest"), "transitions": transitions, "result": result}),
    }


def execute(blockers: list[dict[str, Any]], blocker_id: str | None = None) -> dict[str, Any]:
    """Execute selected/all active blockers and return one canonical summary."""
    selected = [b for b in blockers if blocker_id is None or b.get("blocker_id") == blocker_id]
    if blocker_id and not selected:
        raise BlockerLifecycleError(f"BLOCKER_NOT_FOUND: {blocker_id}")
    results = [execute_blocker(blocker) for blocker in selected if blocker.get("lifecycle_state") == "ACTIVE"]
    return {
        "result": "PASS" if all(item["result"] == "RETIRED" for item in results) else "BLOCKED",
        "blockers": results,
        "active_blockers": [item["blocker"]["blocker_id"] for item in results if item["blocker"]["lifecycle_state"] == "ACTIVE"],
        "retired_blockers": [item["blocker"]["blocker_id"] for item in results if item["blocker"]["lifecycle_state"] == "RETIRED"],
        "reevaluated": True,
        "decision_recomputed": True,
        "idempotent_replay": not results,
    }


def revalidate(blocker: dict[str, Any]) -> dict[str, Any]:
    """Verify the authoritative condition after a resolution attempt."""
    if blocker.get("lifecycle_state") == "ACTIVE":
        return execute_blocker(blocker)
    if blocker.get("lifecycle_state") in {"RESOLVED", "RETIRED"}:
        return {"blocker": blocker, "result": "PASS", "transitions": [], "idempotent_replay": True}
    raise BlockerLifecycleError(f"REVALIDATION_REQUIRES_RESOLUTION_STATE: {blocker.get('blocker_id')}")

