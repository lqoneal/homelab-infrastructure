"""Durable, bounded pause state for OA-23."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SafeInterruptionError(ValueError):
    """A pause request cannot be safely accepted or replayed."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SafeInterruptionError("invalid timestamp") from error
    if parsed.tzinfo is None:
        raise SafeInterruptionError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def authorize_pause(*, request_id: str, mission_id: str, target: str, repository: str,
                    baseline: str, authority: str, operator: str, authorized: bool,
                    requested_at: str, expires_at: str, at: str) -> dict[str, Any]:
    """Build a deterministic pause record after explicit authorization."""
    required = (request_id, mission_id, target, repository, baseline, authority, operator)
    if not all(isinstance(item, str) and item.strip() for item in required):
        raise SafeInterruptionError("complete pause identity is required")
    if mission_id != "OA-23":
        raise SafeInterruptionError("pause request is bound to OA-23")
    if not authorized:
        raise SafeInterruptionError("pause request is not explicitly authorized")
    requested, expires, observed = _time(requested_at), _time(expires_at), _time(at)
    if expires <= requested or observed >= expires:
        raise SafeInterruptionError("pause authorization is stale or expired")
    unsigned = {
        "schema_version": 1, "record_type": "ZEUS_SAFE_INTERRUPTION",
        "request_id": request_id, "mission_id": mission_id, "target": target,
        "repository": repository, "baseline": baseline, "authority": authority,
        "operator": operator, "requested_at": requested_at, "expires_at": expires_at,
        "observed_at": at, "state": "PAUSED", "completion_inferred": False,
        "effects_applied": False, "duplicate_effects": False, "telemetry_only": True,
    }
    return {**unsigned, "record_digest": _digest(unsigned)}


class PauseStore:
    """Atomic durable store with idempotent identical replay."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self, request_id: str) -> dict[str, Any]:
        try:
            value = json.loads((self.path / f"{request_id}.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SafeInterruptionError("pause record is unavailable") from error
        supplied = value.pop("record_digest", None)
        if supplied != _digest(value):
            raise SafeInterruptionError("pause record digest mismatch")
        value["record_digest"] = supplied
        return value

    def save(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        candidate = deepcopy(record)
        request_id = candidate.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise SafeInterruptionError("pause request identity is required")
        target = self.path / f"{request_id}.json"
        self.path.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            existing = self.load(request_id)
            if existing != candidate:
                raise SafeInterruptionError("pause replay diverged")
            return existing, False
        temporary = target.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return candidate, True


def observe(record: dict[str, Any], *, at: str) -> dict[str, Any]:
    """Return bounded presentation telemetry without changing authoritative state."""
    if record.get("state") != "PAUSED" or record.get("completion_inferred"):
        raise SafeInterruptionError("pause record is not safely observable")
    _time(at)
    return {"request_id": record["request_id"], "mission_id": record["mission_id"],
            "state": "PAUSED", "observation_at": at, "telemetry_only": True,
            "completion_inferred": False, "effects_applied": False}
