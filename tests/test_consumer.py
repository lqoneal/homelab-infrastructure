"""Tests for durable event consumption."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.consumer import EventConsumer
from eens.events import EngineeringEvent
from eens.store import EventStore


class EventConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.database_path = root / "eens.sqlite3"
        self.checkpoint_path = root / "consumer.sqlite3"
        self.store = EventStore(self.database_path)

        for index in range(1, 4):
            self.store.append(
                EngineeringEvent(
                    event_type="engineering.test",
                    source="test",
                    subject=f"Event {index}",
                    idempotency_key=f"event-{index}",
                    payload={"index": index},
                )
            )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def consumer(self, name: str = "notifications") -> EventConsumer:
        return EventConsumer(
            self.store,
            self.checkpoint_path,
            consumer_name=name,
        )

    def test_first_consume_returns_all_events(self) -> None:
        events = self.consumer().consume()

        self.assertEqual(
            [event.sequence for event in events],
            [1, 2, 3],
        )

    def test_pending_does_not_advance_checkpoint(self) -> None:
        consumer = self.consumer()

        events = consumer.pending()

        self.assertEqual(
            [event.sequence for event in events],
            [1, 2, 3],
        )
        self.assertEqual(consumer.checkpoint(), 0)

    def test_acknowledge_advances_checkpoint(self) -> None:
        consumer = self.consumer()

        consumer.acknowledge(2)

        self.assertEqual(consumer.checkpoint(), 2)
        self.assertEqual(
            [event.sequence for event in consumer.pending()],
            [3],
        )

    def test_acknowledge_never_moves_checkpoint_backward(self) -> None:
        consumer = self.consumer()

        consumer.acknowledge(3)
        consumer.acknowledge(1)

        self.assertEqual(consumer.checkpoint(), 3)

    def test_invalid_acknowledgement_is_rejected(self) -> None:
        consumer = self.consumer()

        with self.assertRaises(ValueError):
            consumer.acknowledge(0)

    def test_second_consume_returns_no_events(self) -> None:
        consumer = self.consumer()
        consumer.consume()

        self.assertEqual(consumer.consume(), [])
        self.assertEqual(consumer.checkpoint(), 3)

    def test_limit_advances_incrementally(self) -> None:
        consumer = self.consumer()

        first = consumer.consume(limit=2)
        second = consumer.consume(limit=2)

        self.assertEqual(
            [event.sequence for event in first],
            [1, 2],
        )
        self.assertEqual(
            [event.sequence for event in second],
            [3],
        )
        self.assertEqual(consumer.checkpoint(), 3)

    def test_checkpoint_survives_recreation(self) -> None:
        self.consumer().consume(limit=1)

        recreated = self.consumer()

        self.assertEqual(recreated.checkpoint(), 1)
        self.assertEqual(
            [event.sequence for event in recreated.consume()],
            [2, 3],
        )

    def test_consumers_have_independent_checkpoints(self) -> None:
        first = self.consumer("notifications")
        second = self.consumer("audit")

        first.consume(limit=2)
        second_events = second.consume()

        self.assertEqual(first.checkpoint(), 2)
        self.assertEqual(second.checkpoint(), 3)
        self.assertEqual(
            [event.sequence for event in second_events],
            [1, 2, 3],
        )

    def test_empty_consumer_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EventConsumer(
                self.store,
                self.checkpoint_path,
                consumer_name="  ",
            )


if __name__ == "__main__":
    unittest.main()
