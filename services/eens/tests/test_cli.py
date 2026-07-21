"""Tests for the EENS command-line interface."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def emit_arguments(self) -> tuple[str, ...]:
        return (
            "--database",
            str(self.database_path),
            "emit",
            "engineering.handoff.started",
            "--source",
            "cli-test",
            "--subject",
            "Operational Alpha Handoff 5",
            "--idempotency-key",
            "cli-test-handoff-5-started",
            "--payload",
            '{"mission":"EENS","handoff":5,"status":"started"}',
        )

    def test_emit_inserts_event(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.emit_arguments()
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: inserted", output)
        self.assertIn("sequence: 1", output)
        self.assertEqual(EventStore(self.database_path).count(), 1)
        self.assertEqual(errors, "")

    def test_emit_json_output(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.emit_arguments(),
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "inserted")
        self.assertTrue(result["inserted"])
        self.assertEqual(result["sequence"], 1)
        self.assertEqual(errors, "")

    def test_emit_persists_payload(self) -> None:
        self.run_cli(*self.emit_arguments())

        stored = EventStore(self.database_path).get_by_sequence(1)

        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(
            stored.event.payload,
            {"mission": "EENS", "handoff": 5, "status": "started"},
        )

    def test_emit_exact_duplicate_is_suppressed(self) -> None:
        first_code, _, first_errors = self.run_cli(
            *self.emit_arguments()
        )
        second_code, second_output, second_errors = self.run_cli(
            *self.emit_arguments()
        )

        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertIn("status: duplicate", second_output)
        self.assertIn("sequence: 1", second_output)
        self.assertEqual(EventStore(self.database_path).count(), 1)
        self.assertEqual(first_errors, "")
        self.assertEqual(second_errors, "")

    def test_emit_conflicting_duplicate_is_rejected(self) -> None:
        self.run_cli(*self.emit_arguments())

        arguments = list(self.emit_arguments())
        payload_index = arguments.index("--payload") + 1
        arguments[payload_index] = (
            '{"mission":"EENS","handoff":5,"status":"changed"}'
        )

        exit_code, output, errors = self.run_cli(*arguments)

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn("eens: idempotency conflict:", errors)
        self.assertEqual(EventStore(self.database_path).count(), 1)

    def test_emit_rejects_invalid_event_uuid(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.emit_arguments(),
            "--event-id",
            "not-a-uuid",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertIn("eens: invalid event:", errors)
        self.assertEqual(EventStore(self.database_path).count(), 0)

    def test_emit_accepts_explicit_identity_and_time(self) -> None:
        event_id = "11111111-1111-4111-8111-111111111111"
        occurred_at = "2026-07-21T12:00:00+00:00"

        exit_code, output, errors = self.run_cli(
            *self.emit_arguments(),
            "--event-id",
            event_id,
            "--occurred-at",
            occurred_at,
            "--json",
        )

        result = json.loads(output)
        stored = EventStore(self.database_path).get_by_sequence(1)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["event_id"], event_id)
        self.assertEqual(errors, "")
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.event.event_id, event_id)
        self.assertEqual(stored.event.occurred_at, occurred_at)


class HandoffCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
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

    def arguments(self, state: str = "started") -> tuple[str, ...]:
        return (
            "--database",
            str(self.database_path),
            "handoff",
            state,
            "--mission",
            "EENS Operational Alpha",
            "--handoff",
            "1",
        )

    def test_handoff_started_is_emitted(self) -> None:
        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertIn("status: inserted", output)
        self.assertIn(
            "event_type: engineering.handoff.started",
            output,
        )
        self.assertEqual(EventStore(self.database_path).count(), 1)
        self.assertEqual(errors, "")

    def test_handoff_exact_retry_is_duplicate(self) -> None:
        self.run_cli(*self.arguments())
        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertIn("status: duplicate", output)
        self.assertIn("sequence: 1", output)
        self.assertEqual(EventStore(self.database_path).count(), 1)
        self.assertEqual(errors, "")

    def test_handoff_json_output(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.arguments("completed"),
            "--detail",
            "Qualification passed.",
            "--json",
        )

        result = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["inserted"])
        self.assertEqual(
            result["event_type"],
            "engineering.handoff.completed",
        )
        self.assertEqual(errors, "")

    def test_handoff_rejects_nonpositive_number(self) -> None:
        arguments = list(self.arguments())
        arguments[arguments.index("--handoff") + 1] = "0"

        exit_code, output, errors = self.run_cli(*arguments)

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: --handoff must be greater than zero",
        )


class RunCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
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

    def base_arguments(self, handoff: int = 2) -> tuple[str, ...]:
        return (
            "--database",
            str(self.database_path),
            "run",
            "--mission",
            "EENS Operational Alpha",
            "--handoff",
            str(handoff),
            "--",
        )

    def test_run_success_returns_zero_and_emits_pair(self) -> None:
        exit_code, _, errors = self.run_cli(
            *self.base_arguments(),
            sys.executable,
            "-c",
            "raise SystemExit(0)",
        )

        events = list(EventStore(self.database_path).replay())

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(events), 2)
        self.assertEqual(
            events[-1].event.event_type,
            "engineering.handoff.completed",
        )
        self.assertEqual(errors, "")

    def test_run_failure_preserves_exit_code(self) -> None:
        exit_code, _, errors = self.run_cli(
            *self.base_arguments(3),
            sys.executable,
            "-c",
            "raise SystemExit(9)",
        )

        events = list(EventStore(self.database_path).replay())

        self.assertEqual(exit_code, 9)
        self.assertEqual(
            events[-1].event.event_type,
            "engineering.handoff.failed",
        )
        self.assertEqual(errors, "")

    def test_run_requires_command(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.base_arguments()
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: wrapped command is required after --",
        )

    def test_run_command_not_found_returns_127(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.base_arguments(4),
            "definitely-not-a-real-command-eens",
        )

        self.assertEqual(exit_code, 127)
        self.assertEqual(output, "")
        self.assertIn("eens: command not found:", errors)
        self.assertEqual(EventStore(self.database_path).count(), 2)


class ConsumeCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.database_path = root / "eens.sqlite3"
        self.checkpoint_path = root / "checkpoints.sqlite3"
        self.store = EventStore(self.database_path)

        for index in range(1, 4):
            self.store.append(
                EngineeringEvent(
                    event_type="engineering.test",
                    source="test",
                    subject=f"Event {index}",
                    idempotency_key=f"consume-event-{index}",
                    payload={"index": index},
                )
            )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
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

    def arguments(self) -> tuple[str, ...]:
        return (
            "--database",
            str(self.database_path),
            "consume",
            "--consumer",
            "notifications",
            "--checkpoint",
            str(self.checkpoint_path),
        )

    def test_consume_outputs_pending_events(self) -> None:
        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertIn("sequence: 1", output)
        self.assertIn("sequence: 3", output)
        self.assertEqual(errors, "")

    def test_consume_retry_outputs_nothing(self) -> None:
        self.run_cli(*self.arguments())
        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")

    def test_consume_limit(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "2",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("sequence: 1", output)
        self.assertIn("sequence: 2", output)
        self.assertNotIn("sequence: 3", output)
        self.assertEqual(errors, "")

    def test_consume_json_lines(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "1",
            "--json",
        )

        record = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(record["payload"], {"index": 1})
        self.assertEqual(errors, "")

    def test_consume_rejects_nonpositive_limit(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "0",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: --limit must be greater than zero",
        )


class NotifyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.database_path = root / "eens.sqlite3"
        self.checkpoint_path = root / "notify-checkpoints.sqlite3"
        self.store = EventStore(self.database_path)

        for index in range(1, 4):
            self.store.append(
                EngineeringEvent(
                    event_type="engineering.test",
                    source="test",
                    subject=f"Event {index}",
                    idempotency_key=f"notify-cli-event-{index}",
                    payload={"index": index},
                )
            )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
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

    def arguments(self) -> tuple[str, ...]:
        return (
            "--database",
            str(self.database_path),
            "notify",
            "ntfy",
            "--server",
            "https://ntfy.sh",
            "--topic",
            "engineering-test",
            "--checkpoint",
            str(self.checkpoint_path),
        )

    def test_notify_uses_environment_configuration(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {
                    "EENS_NTFY_SERVER": "https://env.example",
                    "EENS_NTFY_TOPIC": "env-topic",
                    "EENS_NTFY_TOKEN": "env-token",
                },
                clear=False,
            ),
            patch("eens.cli.NtfyNotifier") as notifier_class,
            patch("eens.cli.NotificationDispatcher") as dispatcher_class,
        ):
            dispatcher_class.return_value.dispatch.return_value = []

            exit_code, output, errors = self.run_cli(
                "--database",
                str(self.database_path),
                "notify",
                "ntfy",
                "--checkpoint",
                str(self.checkpoint_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")
        notifier_class.assert_called_once_with(
            server="https://env.example",
            topic="env-topic",
            token="env-token",
            timeout=10.0,
        )

    def test_notify_cli_configuration_overrides_environment(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {
                    "EENS_NTFY_SERVER": "https://env.example",
                    "EENS_NTFY_TOPIC": "env-topic",
                    "EENS_NTFY_TOKEN": "env-token",
                },
                clear=False,
            ),
            patch("eens.cli.NtfyNotifier") as notifier_class,
            patch("eens.cli.NotificationDispatcher") as dispatcher_class,
        ):
            dispatcher_class.return_value.dispatch.return_value = []

            exit_code, output, errors = self.run_cli(
                *self.arguments(),
                "--token",
                "cli-token",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")
        notifier_class.assert_called_once_with(
            server="https://ntfy.sh",
            topic="engineering-test",
            token="cli-token",
            timeout=10.0,
        )

    def test_notify_uses_default_server(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {
                    "EENS_NTFY_TOPIC": "env-topic",
                },
                clear=True,
            ),
            patch("eens.cli.NtfyNotifier") as notifier_class,
            patch("eens.cli.NotificationDispatcher") as dispatcher_class,
        ):
            dispatcher_class.return_value.dispatch.return_value = []

            exit_code, output, errors = self.run_cli(
                "--database",
                str(self.database_path),
                "notify",
                "ntfy",
                "--checkpoint",
                str(self.checkpoint_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")
        notifier_class.assert_called_once_with(
            server="https://ntfy.sh",
            topic="env-topic",
            token=None,
            timeout=10.0,
        )

    @patch("eens.notify.urllib.request.urlopen")
    def test_notify_delivers_pending_events(
        self,
        urlopen: MagicMock,
    ) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertIn("sequence: 1", output)
        self.assertIn("sequence: 3", output)
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(errors, "")

    @patch("eens.notify.urllib.request.urlopen")
    def test_notify_retry_outputs_nothing(
        self,
        urlopen: MagicMock,
    ) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        self.run_cli(*self.arguments())
        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(errors, "")

    @patch("eens.notify.urllib.request.urlopen")
    def test_notify_limit(
        self,
        urlopen: MagicMock,
    ) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "2",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("sequence: 1", output)
        self.assertIn("sequence: 2", output)
        self.assertNotIn("sequence: 3", output)
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(errors, "")

    @patch("eens.notify.urllib.request.urlopen")
    def test_notify_json_lines(
        self,
        urlopen: MagicMock,
    ) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "1",
            "--json",
        )

        record = json.loads(output)

        self.assertEqual(exit_code, 0)
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(record["status_code"], 200)
        self.assertEqual(
            record["endpoint"],
            "https://ntfy.sh/engineering-test",
        )
        self.assertEqual(errors, "")

    def test_notify_rejects_nonpositive_limit(self) -> None:
        exit_code, output, errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "0",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            errors,
            "eens: --limit must be greater than zero",
        )

    @patch("eens.notify.urllib.request.urlopen")
    def test_notify_failure_returns_one_and_preserves_event(
        self,
        urlopen: MagicMock,
    ) -> None:
        import urllib.error

        urlopen.side_effect = urllib.error.URLError(
            "network unavailable"
        )

        exit_code, output, errors = self.run_cli(*self.arguments())

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn(
            "eens: notification delivery failed:",
            errors,
        )

        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.side_effect = None
        urlopen.return_value = response
        urlopen.reset_mock()

        retry_code, retry_output, retry_errors = self.run_cli(
            *self.arguments(),
            "--limit",
            "1",
        )

        self.assertEqual(retry_code, 0)
        self.assertIn("sequence: 1", retry_output)
        self.assertEqual(retry_errors, "")




class ServiceCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.database_path = root / "eens.sqlite3"
        self.checkpoint_path = root / "consumers.sqlite3"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
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

    def test_service_ntfy_runs_notification_service(self) -> None:
        with (
            patch("eens.cli.NtfyNotifier") as notifier_class,
            patch("eens.cli.NotificationDispatcher") as dispatcher_class,
            patch("eens.cli.NotificationService") as service_class,
        ):
            exit_code, output, errors = self.run_cli(
                "--database",
                str(self.database_path),
                "service",
                "ntfy",
                "--server",
                "https://ntfy.sh",
                "--topic",
                "engineering-test",
                "--consumer",
                "ntfy-service",
                "--checkpoint",
                str(self.checkpoint_path),
                "--timeout",
                "7.5",
                "--poll-interval",
                "2.0",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "")
        self.assertEqual(errors, "")

        notifier_class.assert_called_once_with(
            server="https://ntfy.sh",
            topic="engineering-test",
            token=None,
            timeout=7.5,
        )
        dispatcher_class.assert_called_once()
        service_class.assert_called_once_with(
            dispatcher_class.return_value,
            poll_interval=2.0,
            error_handler=unittest.mock.ANY,
        )
        service_class.return_value.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
