"""Tests for the handoff command runtime adapter."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.runtime import HandoffCommandRunner
from eens.store import EventStore


class HandoffCommandRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )
        self.store = EventStore(self.database_path)
        self.runner = HandoffCommandRunner(self.store)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_success_emits_started_then_completed(self) -> None:
        result = self.runner.run(
            mission="EENS Operational Alpha",
            handoff=2,
            command=[sys.executable, "-c", "raise SystemExit(0)"],
        )

        events = list(self.store.replay())

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            [item.event.event_type for item in events],
            [
                "engineering.handoff.started",
                "engineering.handoff.completed",
            ],
        )
        self.assertEqual(result.started_sequence, 1)
        self.assertEqual(result.terminal_sequence, 2)

    def test_failure_emits_started_then_failed(self) -> None:
        result = self.runner.run(
            mission="EENS Operational Alpha",
            handoff=3,
            command=[sys.executable, "-c", "raise SystemExit(7)"],
        )

        events = list(self.store.replay())

        self.assertEqual(result.returncode, 7)
        self.assertEqual(
            [item.event.event_type for item in events],
            [
                "engineering.handoff.started",
                "engineering.handoff.failed",
            ],
        )
        self.assertIn(
            "status 7",
            events[1].event.payload["detail"],
        )

    def test_command_not_found_emits_failed(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.runner.run(
                mission="EENS Operational Alpha",
                handoff=4,
                command=["definitely-not-a-real-command-eens"],
            )

        events = list(self.store.replay())

        self.assertEqual(len(events), 2)
        self.assertEqual(
            events[1].event.event_type,
            "engineering.handoff.failed",
        )
        self.assertIn(
            "Command not found",
            events[1].event.payload["detail"],
        )

    def test_empty_command_is_rejected_without_events(self) -> None:
        with self.assertRaises(ValueError):
            self.runner.run(
                mission="EENS Operational Alpha",
                handoff=5,
                command=[],
            )

        self.assertEqual(self.store.count(), 0)

    def test_working_directory_is_applied(self) -> None:
        result = self.runner.run(
            mission="EENS Operational Alpha",
            handoff=6,
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "raise SystemExit(0 if Path.cwd().name else 1)"
                ),
            ],
            cwd=Path(self.temp_directory.name),
        )

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
