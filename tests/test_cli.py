"""Tests for the EENS command-line interface."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.cli import main, resolve_database_path
from eens.events import EngineeringEvent
from eens.store import EventStore


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(list(arguments))

        return exit_code, output.getvalue().strip()

    def test_count_empty_store(self) -> None:
        exit_code, output = self.run_cli(
            "--database",
            str(self.database_path),
            "count",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "0")

    def test_count_persisted_events(self) -> None:
        store = EventStore(self.database_path)

        store.append(
            EngineeringEvent(
                event_type="engineering.handoff.started",
                source="cli-test",
                subject="Handoff 1",
                idempotency_key="cli-test-handoff-1",
            )
        )

        exit_code, output = self.run_cli(
            "--database",
            str(self.database_path),
            "count",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "1")

    def test_explicit_database_path_is_resolved(self) -> None:
        resolved = resolve_database_path(str(self.database_path))
        self.assertEqual(resolved, self.database_path)

    def test_health_reports_wal_and_zero_events(self) -> None:
        exit_code, output = self.run_cli(
            "--database",
            str(self.database_path),
            "health",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: ok", output)
        self.assertIn("journal_mode: wal", output)
        self.assertIn("event_count: 0", output)

    def test_health_json_output(self) -> None:
        store = EventStore(self.database_path)
        store.append(
            EngineeringEvent(
                event_type="engineering.handoff.completed",
                source="cli-test",
                subject="Handoff 1",
                idempotency_key="cli-test-handoff-1-completed",
            )
        )

        exit_code, output = self.run_cli(
            "--database",
            str(self.database_path),
            "health",
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["journal_mode"], "wal")
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["database"], str(self.database_path))


if __name__ == "__main__":
    unittest.main()
