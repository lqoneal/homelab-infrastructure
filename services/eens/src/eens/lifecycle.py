"""Standardized engineering handoff lifecycle event production."""

from __future__ import annotations

from dataclasses import dataclass

from .events import EngineeringEvent
from .store import AppendResult, EventStore, IdempotencyConflictError


VALID_STATES = frozenset({"started", "completed", "failed"})


@dataclass(frozen=True)
class HandoffEmissionResult:
    """Result of emitting one handoff lifecycle event."""

    inserted: bool
    sequence: int
    event: EngineeringEvent


class HandoffLifecycleProducer:
    """Produce mission-scoped handoff lifecycle events."""

    def __init__(
        self,
        store: EventStore,
        *,
        source: str = "engineering-handoff-lifecycle",
    ) -> None:
        if not source or not source.strip():
            raise ValueError("source must not be empty")
        self._store = store
        self._source = source.strip()

    def emit(
        self,
        *,
        state: str,
        mission: str,
        handoff: int,
        detail: str | None = None,
    ) -> HandoffEmissionResult:
        """Emit a standardized started, completed, or failed event."""

        normalized_state = state.strip().lower()
        normalized_mission = mission.strip()

        if normalized_state not in VALID_STATES:
            raise ValueError(
                "state must be started, completed, or failed"
            )
        if not normalized_mission:
            raise ValueError("mission must not be empty")
        if handoff < 1:
            raise ValueError("handoff must be greater than zero")

        payload: dict[str, object] = {
            "mission": normalized_mission,
            "handoff": handoff,
            "status": normalized_state,
        }
        if detail is not None:
            normalized_detail = detail.strip()
            if not normalized_detail:
                raise ValueError("detail must not be empty")
            payload["detail"] = normalized_detail

        event = EngineeringEvent(
            event_type=f"engineering.handoff.{normalized_state}",
            source=self._source,
            subject=(
                f"{normalized_mission} Handoff {handoff} "
                f"{normalized_state.capitalize()}"
            ),
            idempotency_key=(
                f"handoff:{normalized_mission}:{handoff}:{normalized_state}"
            ),
            payload=payload,
        )

        try:
            append_result = self._store.append(event)
        except IdempotencyConflictError:
            existing = self._find_existing(event.idempotency_key)
            if existing is None:
                raise

            existing_event = existing.event
            if (
                existing_event.event_type != event.event_type
                or existing_event.source != event.source
                or existing_event.subject != event.subject
                or existing_event.payload != event.payload
            ):
                raise

            return HandoffEmissionResult(
                inserted=False,
                sequence=existing.sequence,
                event=existing_event,
            )

        if append_result.inserted:
            return HandoffEmissionResult(
                inserted=True,
                sequence=append_result.sequence,
                event=event,
            )

        existing = self._find_existing(event.idempotency_key)
        if existing is None:
            raise RuntimeError(
                "duplicate append result did not resolve stored event"
            )

        return HandoffEmissionResult(
            inserted=False,
            sequence=existing.sequence,
            event=existing.event,
        )

    def _find_existing(self, idempotency_key: str):
        for stored_event in self._store.replay():
            if stored_event.event.idempotency_key == idempotency_key:
                return stored_event
        return None
