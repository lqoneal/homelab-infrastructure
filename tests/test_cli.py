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

    def run_cli(
        self,
        *arguments: str,
    ) -> tuple[int, str, str]:
        output = io.StringIO()
        errors = io.StringIO()

        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(errors),
        ):
            exit_code = main(list(arguments))

        return (
            exit_code,
            output.getvalue().strip(),
            errors.getvalue().strip(),
        )

    def append_sample_event(
        self,
        number: int = 1,
        *,
        event_type: str = "engineering.handoff.started",
    ) -> int:
        store = EventStore(self.database_path)
        result = store.append(
            EngineeringEvent(
                event_type=event_type,
                source="cli-test",
                subject=f"Handoff {number}",
                idempotency_key=f"cli-test-handoff-{number}-{event_type}",
                payload={"mission": "EENS", "handoff": number},
            )
        )
        return result.sequence

    def test_count_empty_store(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "count",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "0")
        self.assertEqual(errors, "")

    def test_count_persisted_events(self) -> None:
        self.append_sample_event()

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "count",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "1")
        self.assertEqual(errors, "")

    def test_explicit_database_path_is_resolved(self) -> None:
        resolved = resolve_database_path(str(self.database_path))
        self.assertEqual(resolved, self.database_path)

    def test_health_reports_wal_and_zero_events(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "health",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: ok", output)
        self.assertIn("journal_mode: wal", output)
        self.assertIn("event_count: 0", output)
        self.assertEqual(errors, "")

    def test_health_json_output(self) -> None:
        self.append_sample_event()

        exit_code, output, errors = self.run_cli(
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
        self.assertEqual(errors, "")

    def test_get_human_readable_output(self) -> None:
        sequence = self.append_sample_event()

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "get",
            str(sequence),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(f"sequence: {sequence}", output)
        self.assertIn(
            "event_type: engineering.handoff.started",
            output,
        )
        self.assertIn("source: cli-test", output)
        self.assertIn("subject: Handoff 1", output)
        self.assertIn(
            'payload: {"handoff": 1, "mission": "EENS"}',
            output,
        )
        self.assertEqual(errors, "")

    def test_get_json_output(self) -> None:
        sequence = self.append_sample_event()

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "get",
            str(sequence),
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["sequence"], sequence)
        self.assertEqual(
            result["event_type"],
            "engineering.handoff.started",
        )
        self.assertEqual(result["source"], "cli-test")
        self.assertEqual(result["subject"], "Handoff 1")
        self.assertEqual(
            result["payload"],
            {"mission": "EENS", "handoff": 1},
        )
        self.assertEqual(errors, "")

    def test_get_missing_sequence_returns_not_found(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "get",
            "999",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: event sequence 999 not found",
        )

    def test_get_rejects_nonpositive_sequence(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "get",
            "0",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: sequence must be greater than zero",
        )

    def test_replay_empty_store(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")

    def test_replay_preserves_sequence_order(self) -> None:
        first = self.append_sample_event(1)
        second = self.append_sample_event(
            2,
            event_type="engineering.handoff.completed",
        )

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
        )

        self.assertEqual(exit_code, 0)
        self.assertLess(
            output.index(f"sequence: {first}"),
            output.index(f"sequence: {second}"),
        )
        self.assertIn("subject: Handoff 1", output)
        self.assertIn("subject: Handoff 2", output)
        self.assertEqual(errors, "")

    def test_replay_after_sequence(self) -> None:
        first = self.append_sample_event(1)
        second = self.append_sample_event(2)

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
            "--after",
            str(first),
        )

        self.assertEqual(exit_code, 0)
        self.assertNotIn(f"sequence: {first}", output)
        self.assertIn(f"sequence: {second}", output)
        self.assertEqual(errors, "")

    def test_replay_limit(self) -> None:
        self.append_sample_event(1)
        self.append_sample_event(2)

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
            "--limit",
            "1",
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sequence"], 1)
        self.assertEqual(errors, "")

    def test_replay_json_output(self) -> None:
        self.append_sample_event(1)
        self.append_sample_event(
            2,
            event_type="engineering.handoff.completed",
        )

        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [event["sequence"] for event in result],
            [1, 2],
        )
        self.assertEqual(result[0]["subject"], "Handoff 1")
        self.assertEqual(result[1]["subject"], "Handoff 2")
        self.assertEqual(errors, "")

    def test_replay_rejects_negative_after(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
            "--after",
            "-1",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: --after must be zero or greater",
        )

    def test_replay_rejects_nonpositive_limit(self) -> None:
        exit_code, output, errors = self.run_cli(
            "--database",
            str(self.database_path),
            "replay",
            "--limit",
            "0",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: --limit must be greater than zero",
        )


if __name__ == "__main__":
    unittest.main()
