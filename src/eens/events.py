"""Engineering event model and validation."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


class EventValidationError(ValueError):
    """Raised when an engineering event is invalid."""


def utc_now() -> str:
    """Return the current UTC time in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def canonical_json(value: Mapping[str, Any]) -> str:
    """Serialize a mapping deterministically for hashing and persistence."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@dataclass(frozen=True, slots=True)
class EngineeringEvent:
    """Immutable engineering lifecycle event."""

    event_type: str
    source: str
    subject: str
    idempotency_key: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        string_fields = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "subject": self.subject,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at,
        }

        for field_name, value in string_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise EventValidationError(
                    f"{field_name} must be a non-empty string"
                )

        if not isinstance(self.payload, Mapping):
            raise EventValidationError("payload must be a mapping")

        try:
            uuid.UUID(self.event_id)
        except ValueError as exc:
            raise EventValidationError(
                "event_id must be a valid UUID"
            ) from exc

        try:
            parsed_time = datetime.fromisoformat(
                self.occurred_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise EventValidationError(
                "occurred_at must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed_time.tzinfo is None:
            raise EventValidationError(
                "occurred_at must include a timezone"
            )

        try:
            canonical_json(self.to_dict())
        except (TypeError, ValueError) as exc:
            raise EventValidationError(
                "event contains values that cannot be serialized as JSON"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        """Return a normal dictionary representation."""

        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "subject": self.subject,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }

    def canonical_json(self) -> str:
        """Return the canonical serialized event."""

        return canonical_json(self.to_dict())

    def fingerprint(self) -> str:
        """Return the SHA-256 fingerprint of the canonical event."""

        return hashlib.sha256(
            self.canonical_json().encode("utf-8")
        ).hexdigest()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EngineeringEvent":
        """Construct and validate an event from a mapping."""

        if not isinstance(value, Mapping):
            raise EventValidationError("event must be a mapping")

        required = {
            "event_type",
            "source",
            "subject",
            "idempotency_key",
        }

        missing = sorted(
            key for key in required
            if key not in value
        )

        if missing:
            raise EventValidationError(
                f"missing required fields: {', '.join(missing)}"
            )

        return cls(
            schema_version=value.get("schema_version", "1.0"),
            event_id=value.get("event_id", str(uuid.uuid4())),
            event_type=value["event_type"],
            source=value["source"],
            subject=value["subject"],
            idempotency_key=value["idempotency_key"],
            occurred_at=value.get("occurred_at", utc_now()),
            payload=value.get("payload", {}),
        )
