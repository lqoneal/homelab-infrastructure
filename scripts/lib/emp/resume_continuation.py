"""Durable reconstruction and idempotent continuation for OA-24."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


class ContinuationError(ValueError):
    """A continuation cannot be proven safe."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unsigned(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "record_digest"}


def create_state(*, execution_id: str, mission_id: str, repository: str,
                 baseline: str, authority: str, operator: str,
                 operations: list[dict[str, Any]]) -> dict[str, Any]:
    required = (execution_id, mission_id, repository, baseline, authority, operator)
    if not all(isinstance(item, str) and item.strip() for item in required):
        raise ContinuationError("complete execution identity is required")
    if mission_id != "OA-24":
        raise ContinuationError("execution is bound to OA-24")
    if not isinstance(operations, list) or not operations:
        raise ContinuationError("durable operation list is required")
    ids = [item.get("operation_id") for item in operations]
    sequences = [item.get("sequence") for item in operations]
    if len(ids) != len(set(ids)) or sequences != list(range(1, len(operations) + 1)):
        raise ContinuationError("operation sequence is not deterministic")
    if not all(item.get("state") in {"COMPLETED", "INCOMPLETE", "PENDING"} for item in operations):
        raise ContinuationError("operation state is invalid")
    unsigned = {"schema_version": 1, "record_type": "ZEUS_DURABLE_EXECUTION_STATE",
                "execution_id": execution_id, "mission_id": mission_id,
                "repository": repository, "baseline": baseline, "authority": authority,
                "operator": operator, "operations": deepcopy(operations)}
    return {**unsigned, "record_digest": _digest(unsigned)}


class ContinuationStore:
    """Atomic state and continuation records with identical replay protection."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def save_state(self, state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        candidate = deepcopy(state)
        if candidate.get("record_digest") != _digest(_unsigned(candidate)):
            raise ContinuationError("execution state digest mismatch")
        self.path.mkdir(parents=True, exist_ok=True)
        target = self.path / f"{candidate['execution_id']}.json"
        if target.is_file():
            existing = self.load_state(candidate["execution_id"])
            if existing != candidate:
                raise ContinuationError("execution state replay diverged")
            return existing, False
        temporary = target.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return candidate, True

    def load_state(self, execution_id: str) -> dict[str, Any]:
        try:
            value = json.loads((self.path / f"{execution_id}.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContinuationError("durable execution state is unavailable") from error
        if value.get("record_digest") != _digest(_unsigned(value)):
            raise ContinuationError("execution state digest mismatch")
        return value

    def resume(self, execution_id: str, *, mission_id: str, baseline: str,
               at: str) -> tuple[dict[str, Any], bool]:
        state = self.load_state(execution_id)
        if state.get("mission_id") != mission_id or state.get("baseline") != baseline:
            raise ContinuationError("continuation binding mismatch")
        incomplete = next((item for item in state["operations"] if item["state"] != "COMPLETED"), None)
        if incomplete is None:
            raise ContinuationError("no incomplete operation exists")
        record = {"schema_version": 1, "record_type": "ZEUS_IDEMPOTENT_CONTINUATION",
                  "execution_id": execution_id, "mission_id": mission_id,
                  "baseline": baseline, "resumed_at": at,
                  "first_incomplete_operation": incomplete["operation_id"],
                  "first_incomplete_sequence": incomplete["sequence"],
                  "state_reconstructed": True, "effects_applied": False,
                  "duplicate_effects": False, "continuation_status": "READY"}
        record["record_digest"] = _digest(record)
        target = self.path / f"{execution_id}.continuation.json"
        if target.is_file():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ContinuationError("continuation record is unavailable") from error
            if existing != record:
                raise ContinuationError("continuation replay diverged")
            return existing, False
        temporary = target.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return record, True
