"""Qualification tests for the EENS durable event store."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.events import EngineeringEvent, EventValidationError
from eens.store import EventStore, IdempotencyConflictError


class EventStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "eens.sqlite3"
        self.store = EventStore(self.database_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    @staticmethod
    def make_event(
        *,
        idempotency_key: str = "mission-0-handoff-1-started",
        subject: str = "Mission 0 Handoff 1",
        status: str = "started",
    ) -> EngineeringEvent:
        return EngineeringEvent(
            event_type="engineering.handoff.started",
            source="eens-test",
            subject=subject,
            idempotency_key=idempotency_key,
            payload={
                "mission": "Mission 0",
                "handoff": 1,
                "status": status,
            },
        )

    def test_new_event_is_persisted(self) -> None:
        event = self.make_event()
        result = self.store.append(event)
        self.assertTrue(result.inserted)
        self.assertEqual(result.sequence, 1)
        self.assertEqual(result.event_id, event.event_id)
        self.assertEqual(self.store.count(), 1)

    def test_exact_duplicate_is_suppressed(self) -> None:
        event = self.make_event()
        first = self.store.append(event)
        second = self.store.append(event)
        self.assertTrue(first.inserted)
        self.assertFalse(second.inserted)
        self.assertEqual(first.sequence, second.sequence)
        self.assertEqual(self.store.count(), 1)

    def test_conflicting_duplicate_is_rejected(self) -> None:
        first_event = self.make_event()
        conflicting_event = EngineeringEvent(
            event_id=first_event.event_id,
            occurred_at=first_event.occurred_at,
            event_type=first_event.event_type,
            source=first_event.source,
            subject="Changed subject",
            idempotency_key=first_event.idempotency_key,
            payload=first_event.payload,
        )

        self.store.append(first_event)

        with self.assertRaises(IdempotencyConflictError):
            self.store.append(conflicting_event)

        self.assertEqual(self.store.count(), 1)

    def test_replay_preserves_sequence_order(self) -> None:
        self.store.append(self.make_event(idempotency_key="event-1", subject="First"))
        self.store.append(self.make_event(idempotency_key="event-2", subject="Second"))
        self.store.append(self.make_event(idempotency_key="event-3", subject="Third"))

        replayed = list(self.store.replay(after_sequence=1))
        self.assertEqual([item.sequence for item in replayed], [2, 3])
        self.assertEqual(
            [item.event.subject for item in replayed],
            ["Second", "Third"],
        )

    def test_database_uses_wal_mode(self) -> None:
        self.assertEqual(self.store.journal_mode(), "wal")

    def test_event_survives_store_recreation(self) -> None:
        event = self.make_event()
        result = self.store.append(event)
        reopened_store = EventStore(self.database_path)
        stored = reopened_store.get_by_sequence(result.sequence)

        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.event.event_id, event.event_id)
        self.assertEqual(stored.event.payload["status"], "started")

    def test_invalid_event_is_rejected(self) -> None:
        with self.assertRaises(EventValidationError):
            EngineeringEvent(
                event_type="",
                source="eens-test",
                subject="Invalid event",
                idempotency_key="invalid-event",
            )

    def test_database_schema_is_append_only_baseline(self) -> None:
        self.store.append(self.make_event())
        connection = sqlite3.connect(self.database_path)
        try:
            row = connection.execute("SELECT COUNT(*) FROM events").fetchone()
        finally:
            connection.close()
        self.assertEqual(row[0], 1)


if __name__ == "__main__":
    unittest.main()
