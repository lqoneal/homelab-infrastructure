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
        snapshot = dict(record.get("authority_snapshot") or {})
        snapshot_digest = snapshot.get("authority_snapshot_digest")
        if not snapshot_digest:
            return {"blocker": "AUTHORITY_CHAIN_INTEGRITY_FAILURE",
                    "detail": "resolved authority snapshot is unavailable",
                    "candidates": decision["candidates"]}
        registry_file = Path(registry_path) if registry_path else Path(repository).resolve() / "engineering/dispatch/execution-agent-registry.json"
        registry_digest = json.loads(registry_file.read_text(encoding="utf-8")).get("registry_digest")
        qualification = agent.get("qualification_evidence") or []
        qualification_id = qualification[0] if qualification else ""
        assignment = {
            "wop_id": record["wop_id"],
            "instance_id": record["instance_id"],
            "agent_id": agent["agent_id"],
            "repository": str(Path(repository).resolve()),
            "selection_policy": "qualified-agent-id-ascending",
            "authority_snapshot_digest": snapshot_digest,
            "registry_digest": registry_digest,
        }
        assignment_id = "ZEUS-DISPATCH-" + _digest(assignment)[:24]
        dispatch = {
            "schema_version": 1,
            "receipt_type": "dispatch",
            "assignment_id": assignment_id,
            "assignment_digest": _digest(assignment),
            "agent_id": agent["agent_id"],
            "provider_id": agent.get("provider_id", agent["agent_id"]),
            "qualification_id": qualification_id,
            "registry_digest": registry_digest,
            "wop_id": record["wop_id"],
            "instance_id": record["instance_id"],
            "package_digest": record.get("package_digest"),
            "repository": str(Path(repository).resolve()),
            "selection": "qualified-agent-id-ascending",
            "dispatch_plan_digest": _digest(assignment),
            "authority_snapshot_digest": snapshot_digest,
            "predecessor_receipt": (record.get("receipts") or {}).get("admission", {}).get("receipt_id"),
        }
        dispatch["receipt_id"] = "ZEUS-RECEIPT-DISPATCH-" + _digest(dispatch)[:24]
        dispatch["receipt_digest"] = _digest(dispatch)
        selection = {
            "schema_version": 1,
            "receipt_type": "provider-selection",
            "transaction_id": record["instance_id"],
            "wop_id": record["wop_id"],
            "agent_id": agent["agent_id"],
            "provider_id": agent.get("provider_id", agent["agent_id"]),
            "candidates": decision["candidates"],
            "selection_policy": "qualified-agent-id-ascending",
            "registry_digest": registry_digest,
            "authority_snapshot_digest": snapshot_digest,
        }
        selection["receipt_id"] = "ZEUS-RECEIPT-PROVIDER-SELECTION-" + _digest(selection)[:24]
        selection["receipt_digest"] = _digest(selection)
        return {"dispatch_receipt": dispatch,
                "receipts": {"provider_selection": selection},
                "provider_selection": {"agent_id": agent["agent_id"], "candidates": decision["candidates"]}}
    return execute
