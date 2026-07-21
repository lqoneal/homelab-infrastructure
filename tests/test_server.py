"""Tests for the EENS notification service runtime."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eens.server import NotificationService


class NotificationServiceTests(unittest.TestCase):
    def test_run_once_dispatches_pending_events(self) -> None:
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = ["result"]

        service = NotificationService(
            dispatcher,
            poll_interval=1.0,
        )

        results = service.run_once()

        self.assertEqual(results, ["result"])
        dispatcher.dispatch.assert_called_once_with()

    def test_nonpositive_poll_interval_is_rejected(self) -> None:
        dispatcher = MagicMock()

        with self.assertRaisesRegex(
            ValueError,
            "poll_interval must be greater than zero",
        ):
            NotificationService(
                dispatcher,
                poll_interval=0,
            )

    def test_run_stops_when_requested(self) -> None:
        dispatcher = MagicMock()
        service = NotificationService(
            dispatcher,
            poll_interval=0.01,
        )

        dispatcher.dispatch.side_effect = service.stop

        service.run()

        dispatcher.dispatch.assert_called_once_with()

    def test_run_sleeps_after_each_dispatch_cycle(self) -> None:
        dispatcher = MagicMock()
        sleep = MagicMock()

        service = NotificationService(
            dispatcher,
            poll_interval=2.5,
            sleep=sleep,
        )

        dispatcher.dispatch.side_effect = service.stop

        service.run()

        sleep.assert_called_once_with(2.5)


    def test_notification_failure_is_reported_and_retried(self) -> None:
        from eens.notify import NotificationError

        dispatcher = MagicMock()
        sleep = MagicMock()
        error_handler = MagicMock()

        service = NotificationService(
            dispatcher,
            poll_interval=2.0,
            sleep=sleep,
            error_handler=error_handler,
        )

        dispatch_count = 0

        def dispatch() -> None:
            nonlocal dispatch_count
            dispatch_count += 1

            if dispatch_count == 1:
                raise NotificationError("delivery failed")

            service.stop()

        dispatcher.dispatch.side_effect = dispatch

        service.run()

        self.assertEqual(dispatcher.dispatch.call_count, 2)
        error_handler.assert_called_once()
        error = error_handler.call_args.args[0]
        self.assertIsInstance(error, NotificationError)
        self.assertEqual(str(error), "delivery failed")
        self.assertEqual(sleep.call_count, 2)

    def test_unexpected_error_terminates_service(self) -> None:
        dispatcher = MagicMock()
        sleep = MagicMock()
        error_handler = MagicMock()

        service = NotificationService(
            dispatcher,
            poll_interval=2.0,
            sleep=sleep,
            error_handler=error_handler,
        )

        dispatcher.dispatch.side_effect = RuntimeError("unexpected")

        with self.assertRaisesRegex(RuntimeError, "unexpected"):
            service.run()

        error_handler.assert_not_called()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
