"""Mission-bound append-only evidence capture backed by EENS."""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

EENS_SOURCE = Path(__file__).resolve().parents[3] / "services" / "eens" / "src"
if str(EENS_SOURCE) not in sys.path:
    sys.path.insert(0, str(EENS_SOURCE))

from eens.events import EngineeringEvent  # noqa: E402
from eens.store import AppendResult, EventStore  # noqa: E402


class EvidenceCaptureError(ValueError):
    """Evidence input is incomplete or cannot be captured safely."""


def _checksum(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class EvidenceCapture:
    """Capture complete, replay-safe evidence records without updates or deletes."""

    def __init__(self, database_path: str | Path):
        self.store = EventStore(database_path)

    def capture(
        self,
        *,
        record_id: str,
        mission_id: str,
        wop_id: str,
        repository_identity: str,
        baseline_commit: str,
        agent_identity: str,
        command: str,
        stdout: str,
        stderr: str,
        state: str,
        completion_marker: str,
        timestamp: str,
    ) -> AppendResult:
        values = {
            "record_id": record_id,
            "mission_id": mission_id,
            "wop_id": wop_id,
            "repository_identity": repository_identity,
            "baseline_commit": baseline_commit,
            "agent_identity": agent_identity,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "state": state,
            "completion_marker": completion_marker,
            "timestamp": timestamp,
        }
        required_nonempty = ("record_id", "mission_id", "wop_id", "repository_identity", "baseline_commit", "agent_identity", "command", "state", "completion_marker", "timestamp")
        if any(not isinstance(values[key], str) or not values[key] for key in required_nonempty) or any(not isinstance(values[key], str) for key in ("stdout", "stderr")):
            raise EvidenceCaptureError("evidence record fields must be non-empty strings")
        values["checksum"] = _checksum(values)
        event = EngineeringEvent(
            event_type="zeus.evidence.capture",
            source="zeus.oa19",
            subject=mission_id,
            idempotency_key=f"{mission_id}:{wop_id}:{record_id}",
            occurred_at=timestamp,
            event_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{mission_id}:{wop_id}:{record_id}")),
            payload=values,
        )
        return self.store.append(event)

    def replay(self):
        return self.store.replay()
