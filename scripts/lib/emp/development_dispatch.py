"""Provider-neutral automatic dispatch for Development Stage 1 lifecycles.

This adapter only resolves the existing execution-agent registry. It never
authorizes a provider, fabricates a launch acknowledgement, or advances a
transaction without a qualified registry record.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def select_provider(repository: Path | str, *, registry_path: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    path = Path(registry_path) if registry_path else root / "engineering/dispatch/execution-agent-registry.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"result": "BLOCKED", "blocker": "EXECUTION_AGENT_REGISTRY_UNAVAILABLE", "detail": str(error), "candidates": []}
    candidates = []
    for item in value.get("agents", []) if isinstance(value, Mapping) else []:
        if not isinstance(item, Mapping):
            continue
        if item.get("active") is not True or item.get("qualification_status") != "QUALIFIED":
            continue
        scope = item.get("repository_access_scope", [])
        if scope and str(root) not in {str(Path(entry).resolve()) for entry in scope}:
            continue
        candidates.append(dict(item))
    candidates.sort(key=lambda item: str(item.get("agent_id", "")))
    if not candidates:
        return {"result": "BLOCKED", "blocker": "EXECUTION_AGENT_UNAVAILABLE", "detail": "no active qualified Development execution agent", "candidates": []}
    if len(candidates) > 1:
        # Deterministic selection is permitted only when policy ordering is
        # explicit; registry order is not an authority signal.
        selected = candidates[0]
    else:
        selected = candidates[0]
    return {"result": "PASS", "selected": selected, "candidates": [item.get("agent_id") for item in candidates]}


def automatic_executor(repository: Path | str, *, registry_path: Path | str | None = None):
    """Return the Stage 1 executor callback used by the CLI."""
    def execute(record: Mapping[str, Any]) -> dict[str, Any]:
        decision = select_provider(repository, registry_path=registry_path)
        if decision["result"] != "PASS":
            return {"blocker": decision["blocker"], "detail": decision["detail"], "candidates": decision["candidates"]}
        agent = decision["selected"]
        assignment = {
            "wop_id": record["wop_id"],
            "instance_id": record["instance_id"],
            "agent_id": agent["agent_id"],
            "repository": str(Path(repository).resolve()),
            "selection_policy": "qualified-agent-id-ascending",
        }
        assignment_id = "ZEUS-DISPATCH-" + _digest(assignment)[:24]
        dispatch = {
            "schema_version": 1,
            "receipt_type": "dispatch",
            "assignment_id": assignment_id,
            "assignment_digest": _digest(assignment),
            "agent_id": agent["agent_id"],
            "wop_id": record["wop_id"],
            "repository": str(Path(repository).resolve()),
            "selection": "qualified-agent-id-ascending",
        }
        dispatch["receipt_id"] = "ZEUS-RECEIPT-DISPATCH-" + _digest(dispatch)[:24]
        dispatch["receipt_digest"] = _digest(dispatch)
        return {"dispatch_receipt": dispatch, "provider_selection": {"agent_id": agent["agent_id"], "candidates": decision["candidates"]}}
    return execute
