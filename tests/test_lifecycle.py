"""Tests for standardized handoff lifecycle production."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.lifecycle import HandoffLifecycleProducer
from eens.store import EventStore, IdempotencyConflictError


class HandoffLifecycleProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )
        self.store = EventStore(self.database_path)
        self.producer = HandoffLifecycleProducer(self.store)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_started_event_is_standardized(self) -> None:
        result = self.producer.emit(
            state="started",
            mission="EENS Operational Alpha",
            handoff=1,
        )

        self.assertTrue(result.inserted)
        self.assertEqual(result.sequence, 1)
        self.assertEqual(
            result.event.event_type,
            "engineering.handoff.started",
        )
        self.assertEqual(
            result.event.idempotency_key,
            "handoff:EENS Operational Alpha:1:started",
        )
        self.assertEqual(
            result.event.payload,
            {
                "mission": "EENS Operational Alpha",
                "handoff": 1,
                "status": "started",
            },
        )

    def test_completed_event_accepts_detail(self) -> None:
        result = self.producer.emit(
            state="completed",
            mission="EENS Operational Alpha",
            handoff=1,
            detail="All qualification tests passed.",
        )

        self.assertEqual(
            result.event.payload["detail"],
            "All qualification tests passed.",
        )

    def test_exact_retry_is_suppressed(self) -> None:
        first = self.producer.emit(
            state="started",
            mission="EENS Operational Alpha",
            handoff=2,
        )
        second = self.producer.emit(
            state="started",
            mission="EENS Operational Alpha",
            handoff=2,
        )

        self.assertTrue(first.inserted)
        self.assertFalse(second.inserted)
        self.assertEqual(second.sequence, first.sequence)
        self.assertEqual(self.store.count(), 1)

    def test_changed_retry_conflicts(self) -> None:
        self.producer.emit(
            state="failed",
            mission="EENS Operational Alpha",
            handoff=3,
            detail="First failure",
        )

        with self.assertRaises(IdempotencyConflictError):
            self.producer.emit(
                state="failed",
                mission="EENS Operational Alpha",
                handoff=3,
                detail="Changed failure",
            )

    def test_invalid_handoff_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.producer.emit(
                state="started",
                mission="EENS",
                handoff=0,
            )

    def test_invalid_state_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.producer.emit(
                state="paused",
                mission="EENS",
                handoff=1,
            )


if __name__ == "__main__":
    unittest.main()
