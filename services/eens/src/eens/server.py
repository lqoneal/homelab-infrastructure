"""Long-running notification service runtime."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from eens.notify import NotificationError


class NotificationService:
    """Repeatedly dispatch pending notifications until stopped."""

    def __init__(
        self,
        dispatcher: Any,
        *,
        poll_interval: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        error_handler: Callable[[NotificationError], None] | None = None,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError(
                "poll_interval must be greater than zero"
            )

        self._dispatcher = dispatcher
        self._poll_interval = float(poll_interval)
        self._sleep = sleep
        self._error_handler = error_handler or (lambda error: None)
        self._running = False

    def run_once(self) -> list[Any]:
        """Execute one notification dispatch cycle."""

        return self._dispatcher.dispatch()

    def run(self) -> None:
        """Run dispatch cycles until stop is requested."""

        self._running = True

        while self._running:
            try:
                self.run_once()
            except NotificationError as error:
                self._error_handler(error)

            self._sleep(self._poll_interval)

    def stop(self) -> None:
        """Request a clean service shutdown."""

        self._running = False
