"""ntfy notification delivery for EENS events."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping

from .consumer import EventConsumer
from .store import StoredEvent


class NotificationError(RuntimeError):
    """Raised when a notification cannot be delivered."""


@dataclass(frozen=True, slots=True)
class NotificationResult:
    """Result of one successful notification delivery."""

    sequence: int
    endpoint: str
    status_code: int


class NotificationDispatcher:
    """Deliver pending events and acknowledge successful deliveries."""

    def __init__(
        self,
        consumer: EventConsumer,
        notifier: "NtfyNotifier",
    ) -> None:
        self._consumer = consumer
        self._notifier = notifier

    def dispatch(
        self,
        *,
        limit: int | None = None,
    ) -> list[NotificationResult]:
        """Deliver pending events in order and checkpoint each success."""

        results: list[NotificationResult] = []

        for stored_event in self._consumer.pending(limit=limit):
            result = self._notifier.send(stored_event)
            self._consumer.acknowledge(stored_event.sequence)
            results.append(result)

        return results


class NtfyNotifier:
    """Deliver EENS events to an ntfy topic over HTTP."""

    def __init__(
        self,
        *,
        server: str,
        topic: str,
        token: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        normalized_server = server.strip().rstrip("/")
        normalized_topic = topic.strip().strip("/")

        if not normalized_server:
            raise ValueError("server must not be empty")
        if not normalized_topic:
            raise ValueError("topic must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self._server = normalized_server
        self._topic = normalized_topic
        self._token = token.strip() if token and token.strip() else None
        self._timeout = timeout

    @property
    def endpoint(self) -> str:
        """Return the resolved ntfy topic endpoint."""

        return f"{self._server}/{self._topic}"

    def send(self, stored_event: StoredEvent) -> NotificationResult:
        """Deliver one stored event to ntfy."""

        request = urllib.request.Request(
            self.endpoint,
            data=self._format_message(stored_event).encode("utf-8"),
            method="POST",
        )
        request.add_header(
            "Title",
            stored_event.event.subject,
        )
        request.add_header(
            "Tags",
            "gear",
        )
        request.add_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )

        if self._token is not None:
            request.add_header(
                "Authorization",
                f"Bearer {self._token}",
            )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout,
            ) as response:
                status_code = int(response.status)
        except urllib.error.HTTPError as exc:
            raise NotificationError(
                f"ntfy rejected event sequence "
                f"{stored_event.sequence}: HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise NotificationError(
                f"ntfy transport failed for event sequence "
                f"{stored_event.sequence}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise NotificationError(
                f"ntfy transport failed for event sequence "
                f"{stored_event.sequence}: {exc}"
            ) from exc

        if status_code < 200 or status_code >= 300:
            raise NotificationError(
                f"ntfy rejected event sequence "
                f"{stored_event.sequence}: HTTP {status_code}"
            )

        return NotificationResult(
            sequence=stored_event.sequence,
            endpoint=self.endpoint,
            status_code=status_code,
        )

    @staticmethod
    def _format_message(stored_event: StoredEvent) -> str:
        """Format one stored event as an ntfy message."""

        event = stored_event.event
        lines = [
            f"Sequence: {stored_event.sequence}",
            f"Event: {event.event_type}",
            f"Source: {event.source}",
            f"Occurred: {event.occurred_at}",
        ]

        if event.payload:
            lines.append(
                "Payload: "
                + json.dumps(
                    dict(event.payload),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

        return "\n".join(lines)


def redact_headers(
    headers: Mapping[str, str],
) -> dict[str, str]:
    """Return headers with authorization values redacted."""

    return {
        key: "<redacted>"
        if key.lower() == "authorization"
        else value
        for key, value in headers.items()
    }
