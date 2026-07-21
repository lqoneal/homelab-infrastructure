"""Tests for ntfy notification delivery."""

from __future__ import annotations

import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.consumer import EventConsumer
from eens.events import EngineeringEvent
from eens.notify import (
    NotificationDispatcher,
    NotificationError,
    NotificationResult,
    NtfyNotifier,
)
from eens.store import EventStore


class NtfyNotifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(self.temp_directory.name) / "eens.sqlite3"
        )
        store = EventStore(database_path)
        result = store.append(
            EngineeringEvent(
                event_type="engineering.handoff.completed",
                source="test-runtime",
                subject="Handoff completed",
                idempotency_key="notify-test-event",
                payload={
                    "mission": "Notification Qualification",
                    "handoff": 2,
                },
            )
        )
        self.stored_event = store.get_by_sequence(result.sequence)
        assert self.stored_event is not None

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_endpoint_is_normalized(self) -> None:
        notifier = NtfyNotifier(
            server="https://ntfy.sh/",
            topic="/engineering-test/",
        )

        self.assertEqual(
            notifier.endpoint,
            "https://ntfy.sh/engineering-test",
        )

    def test_empty_server_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NtfyNotifier(
                server=" ",
                topic="engineering-test",
            )

    def test_empty_topic_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NtfyNotifier(
                server="https://ntfy.sh",
                topic=" ",
            )

    def test_invalid_timeout_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NtfyNotifier(
                server="https://ntfy.sh",
                topic="engineering-test",
                timeout=0,
            )

    @patch("eens.notify.urllib.request.urlopen")
    def test_successful_delivery(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        notifier = NtfyNotifier(
            server="https://ntfy.sh",
            topic="engineering-test",
        )

        result = notifier.send(self.stored_event)

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://ntfy.sh/engineering-test",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertIn(
            b"Sequence: 1",
            request.data,
        )
        self.assertIn(
            b"Event: engineering.handoff.completed",
            request.data,
        )
        self.assertIn(
            b'"mission": "Notification Qualification"',
            request.data,
        )
        self.assertEqual(result.sequence, 1)
        self.assertEqual(result.status_code, 200)

    @patch("eens.notify.urllib.request.urlopen")
    def test_bearer_token_is_added(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        notifier = NtfyNotifier(
            server="https://ntfy.sh",
            topic="engineering-test",
            token="secret-token",
        )

        notifier.send(self.stored_event)

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer secret-token",
        )

    @patch("eens.notify.urllib.request.urlopen")
    def test_http_error_is_wrapped(self, urlopen: MagicMock) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            url="https://ntfy.sh/engineering-test",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )

        notifier = NtfyNotifier(
            server="https://ntfy.sh",
            topic="engineering-test",
        )

        with self.assertRaisesRegex(
            NotificationError,
            "HTTP 403",
        ):
            notifier.send(self.stored_event)

    @patch("eens.notify.urllib.request.urlopen")
    def test_transport_error_is_wrapped(
        self,
        urlopen: MagicMock,
    ) -> None:
        urlopen.side_effect = urllib.error.URLError(
            "network unavailable"
        )

        notifier = NtfyNotifier(
            server="https://ntfy.sh",
            topic="engineering-test",
        )

        with self.assertRaisesRegex(
            NotificationError,
            "network unavailable",
        ):
            notifier.send(self.stored_event)

    @patch("eens.notify.urllib.request.urlopen")
    def test_non_success_status_is_rejected(
        self,
        urlopen: MagicMock,
    ) -> None:
        response = MagicMock()
        response.status = 500
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urlopen.return_value = response

        notifier = NtfyNotifier(
            server="https://ntfy.sh",
            topic="engineering-test",
        )

        with self.assertRaisesRegex(
            NotificationError,
            "HTTP 500",
        ):
            notifier.send(self.stored_event)


class NotificationDispatcherTests(unittest.TestCase):
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
                    source="test-runtime",
                    subject=f"Event {index}",
                    idempotency_key=f"dispatcher-event-{index}",
                    payload={"index": index},
                )
            )

        self.consumer = EventConsumer(
            self.store,
            self.checkpoint_path,
            consumer_name="notifications",
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_successful_dispatch_advances_each_event(self) -> None:
        notifier = MagicMock()
        notifier.send.side_effect = [
            NotificationResult(1, "https://ntfy.sh/test", 200),
            NotificationResult(2, "https://ntfy.sh/test", 200),
            NotificationResult(3, "https://ntfy.sh/test", 200),
        ]
        dispatcher = NotificationDispatcher(
            self.consumer,
            notifier,
        )

        results = dispatcher.dispatch()

        self.assertEqual(
            [result.sequence for result in results],
            [1, 2, 3],
        )
        self.assertEqual(self.consumer.checkpoint(), 3)
        self.assertEqual(notifier.send.call_count, 3)

    def test_failure_preserves_failed_event(self) -> None:
        notifier = MagicMock()
        notifier.send.side_effect = [
            NotificationResult(1, "https://ntfy.sh/test", 200),
            NotificationError("delivery failed"),
        ]
        dispatcher = NotificationDispatcher(
            self.consumer,
            notifier,
        )

        with self.assertRaisesRegex(
            NotificationError,
            "delivery failed",
        ):
            dispatcher.dispatch()

        self.assertEqual(self.consumer.checkpoint(), 1)
        self.assertEqual(
            [
                event.sequence
                for event in self.consumer.pending()
            ],
            [2, 3],
        )
        self.assertEqual(notifier.send.call_count, 2)

    def test_retry_resumes_with_failed_event(self) -> None:
        failing_notifier = MagicMock()
        failing_notifier.send.side_effect = [
            NotificationResult(1, "https://ntfy.sh/test", 200),
            NotificationError("delivery failed"),
        ]
        dispatcher = NotificationDispatcher(
            self.consumer,
            failing_notifier,
        )

        with self.assertRaises(NotificationError):
            dispatcher.dispatch()

        succeeding_notifier = MagicMock()
        succeeding_notifier.send.side_effect = [
            NotificationResult(2, "https://ntfy.sh/test", 200),
            NotificationResult(3, "https://ntfy.sh/test", 200),
        ]
        retry_dispatcher = NotificationDispatcher(
            self.consumer,
            succeeding_notifier,
        )

        results = retry_dispatcher.dispatch()

        self.assertEqual(
            [result.sequence for result in results],
            [2, 3],
        )
        self.assertEqual(self.consumer.checkpoint(), 3)

    def test_limit_restricts_dispatch(self) -> None:
        notifier = MagicMock()
        notifier.send.side_effect = [
            NotificationResult(1, "https://ntfy.sh/test", 200),
            NotificationResult(2, "https://ntfy.sh/test", 200),
        ]
        dispatcher = NotificationDispatcher(
            self.consumer,
            notifier,
        )

        results = dispatcher.dispatch(limit=2)

        self.assertEqual(
            [result.sequence for result in results],
            [1, 2],
        )
        self.assertEqual(self.consumer.checkpoint(), 2)
        self.assertEqual(
            [
                event.sequence
                for event in self.consumer.pending()
            ],
            [3],
        )



if __name__ == "__main__":
    unittest.main()
