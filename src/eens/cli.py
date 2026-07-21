"""Command-line interface for EENS."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .events import EngineeringEvent
from .lifecycle import HandoffLifecycleProducer
from .runtime import HandoffCommandRunner
from .consumer import EventConsumer
from .notify import (
    NotificationDispatcher,
    NotificationError,
    NtfyNotifier,
)
from .server import NotificationService
from .store import EventStore, IdempotencyConflictError, StoredEvent


DEFAULT_DATABASE_PATH = Path("runtime/db/eens.sqlite3")


def resolve_database_path(value: str | None = None) -> Path:
    """Resolve the database path from an argument, environment, or default."""

    candidate = value or os.environ.get("EENS_DB_PATH")
    if candidate:
        return Path(candidate).expanduser()
    return DEFAULT_DATABASE_PATH


def resolve_ntfy_server(value: str | None = None) -> str:
    """Resolve the ntfy server from an argument, environment, or default."""

    return value or os.environ.get(
        "EENS_NTFY_SERVER",
        "https://ntfy.sh",
    )


def resolve_ntfy_topic(value: str | None = None) -> str | None:
    """Resolve the ntfy topic from an argument or environment."""

    return value or os.environ.get("EENS_NTFY_TOPIC")


def resolve_ntfy_token(value: str | None = None) -> str | None:
    """Resolve the optional ntfy token from an argument or environment."""

    return value or os.environ.get("EENS_NTFY_TOKEN")


def parse_payload(value: str) -> dict[str, Any]:
    """Parse and validate a JSON object payload."""

    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"payload must be valid JSON: {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError(
            "payload must be a JSON object"
        )

    return payload


def build_parser() -> argparse.ArgumentParser:
    """Build the EENS command-line parser."""

    parser = argparse.ArgumentParser(
        prog="eens",
        description="Engineering Event & Notification System",
    )
    parser.add_argument(
        "--database",
        help="SQLite database path; overrides EENS_DB_PATH",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "count",
        help="Print the number of persisted engineering events",
    )

    health_parser = subparsers.add_parser(
        "health",
        help="Report EENS event-store health",
    )
    health_parser.add_argument(
        "--json",
        action="store_true",
        help="Print health information as JSON",
    )

    get_parser = subparsers.add_parser(
        "get",
        help="Retrieve one event by durable sequence number",
    )
    get_parser.add_argument(
        "sequence",
        type=int,
        help="Durable event sequence number",
    )
    get_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the stored event as JSON",
    )

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay stored events in durable sequence order",
    )
    replay_parser.add_argument(
        "--after",
        type=int,
        default=0,
        help="Replay events with sequence numbers greater than this value",
    )
    replay_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of events to return",
    )
    replay_parser.add_argument(
        "--json",
        action="store_true",
        help="Print replay results as a JSON array",
    )

    emit_parser = subparsers.add_parser(
        "emit",
        help="Validate and persist an engineering event",
    )
    emit_parser.add_argument(
        "event_type",
        help="Engineering event type",
    )
    emit_parser.add_argument(
        "--source",
        required=True,
        help="Event producer or originating component",
    )
    emit_parser.add_argument(
        "--subject",
        required=True,
        help="Human-readable event subject",
    )
    emit_parser.add_argument(
        "--idempotency-key",
        required=True,
        help="Stable key used for duplicate suppression",
    )
    emit_parser.add_argument(
        "--payload",
        type=parse_payload,
        default={},
        help="JSON object payload; defaults to {}",
    )
    emit_parser.add_argument(
        "--event-id",
        help="Optional UUID event identifier",
    )
    emit_parser.add_argument(
        "--occurred-at",
        help="Optional ISO-8601 event timestamp",
    )
    emit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the append result as JSON",
    )

    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Emit a standardized engineering handoff lifecycle event",
    )
    handoff_parser.add_argument(
        "state",
        choices=("started", "completed", "failed"),
        help="Handoff lifecycle state",
    )
    handoff_parser.add_argument(
        "--mission",
        required=True,
        help="Mission name",
    )
    handoff_parser.add_argument(
        "--handoff",
        required=True,
        type=int,
        help="Mission-scoped handoff number",
    )
    handoff_parser.add_argument(
        "--source",
        default="engineering-handoff-lifecycle",
        help="Lifecycle producer identity",
    )
    handoff_parser.add_argument(
        "--detail",
        help="Optional completion or failure detail",
    )
    handoff_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the lifecycle result as JSON",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run a command inside a handoff lifecycle",
    )
    run_parser.add_argument(
        "--mission",
        required=True,
        help="Mission name",
    )
    run_parser.add_argument(
        "--handoff",
        required=True,
        type=int,
        help="Mission-scoped handoff number",
    )
    run_parser.add_argument(
        "--source",
        default="engineering-handoff-runtime",
        help="Runtime producer identity",
    )
    run_parser.add_argument(
        "--cwd",
        help="Optional working directory for the wrapped command",
    )
    run_parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="Command to execute; precede it with --",
    )

    consume_parser = subparsers.add_parser(
        "consume",
        help="Consume persisted events using a durable checkpoint",
    )
    consume_parser.add_argument(
        "--consumer",
        required=True,
        help="Stable consumer identity",
    )
    consume_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of events to consume",
    )
    consume_parser.add_argument(
        "--checkpoint",
        help="Optional explicit checkpoint database path",
    )
    consume_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON object per consumed event",
    )

    notify_parser = subparsers.add_parser(
        "notify",
        help="Deliver pending events through a notification transport",
    )
    notify_subparsers = notify_parser.add_subparsers(
        dest="notify_transport",
        required=True,
    )

    ntfy_parser = notify_subparsers.add_parser(
        "ntfy",
        help="Deliver pending events to an ntfy topic",
    )
    ntfy_parser.add_argument(
        "--server",
        help=(
            "ntfy server base URL; overrides EENS_NTFY_SERVER "
            "(default: https://ntfy.sh)"
        ),
    )
    ntfy_parser.add_argument(
        "--topic",
        help="ntfy topic name; overrides EENS_NTFY_TOPIC",
    )
    ntfy_parser.add_argument(
        "--token",
        help="Optional ntfy access token",
    )
    ntfy_parser.add_argument(
        "--consumer",
        default="ntfy",
        help="Stable notification consumer identity",
    )
    ntfy_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of events to deliver",
    )
    ntfy_parser.add_argument(
        "--checkpoint",
        help="Optional explicit checkpoint database path",
    )
    ntfy_parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds",
    )
    ntfy_parser.add_argument(
        "--json",
        action="store_true",
        help="Print one JSON object per delivered event",
    )

    service_parser = subparsers.add_parser(
        "service",
        help="Run a long-running notification service",
    )
    service_subparsers = service_parser.add_subparsers(
        dest="service_transport",
        required=True,
    )

    service_ntfy_parser = service_subparsers.add_parser(
        "ntfy",
        help="Continuously deliver pending events to an ntfy topic",
    )
    service_ntfy_parser.add_argument(
        "--server",
        help=(
            "ntfy server base URL; overrides EENS_NTFY_SERVER "
            "(default: https://ntfy.sh)"
        ),
    )
    service_ntfy_parser.add_argument(
        "--topic",
        help="ntfy topic name; overrides EENS_NTFY_TOPIC",
    )
    service_ntfy_parser.add_argument(
        "--token",
        help="Optional ntfy access token",
    )
    service_ntfy_parser.add_argument(
        "--consumer",
        default="ntfy-service",
        help="Stable notification consumer identity",
    )
    service_ntfy_parser.add_argument(
        "--checkpoint",
        help="Optional explicit checkpoint database path",
    )
    service_ntfy_parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds",
    )
    service_ntfy_parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds between notification dispatch cycles",
    )

    return parser


def stored_event_to_dict(stored_event: StoredEvent) -> dict[str, Any]:
    """Convert a stored event to a serializable dictionary."""

    event = stored_event.event
    return {
        "sequence": stored_event.sequence,
        "stored_at": stored_event.stored_at,
        "fingerprint": stored_event.fingerprint,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "source": event.source,
        "subject": event.subject,
        "occurred_at": event.occurred_at,
        "idempotency_key": event.idempotency_key,
        "payload": event.payload,
    }


def run_count(database_path: Path) -> int:
    """Execute the count command."""

    store = EventStore(database_path)
    print(store.count())
    return 0


def run_health(database_path: Path, *, json_output: bool = False) -> int:
    """Execute the health command."""

    store = EventStore(database_path)
    event_count = store.count()
    journal_mode = store.journal_mode()
    healthy = journal_mode == "wal"

    result = {
        "status": "ok" if healthy else "degraded",
        "database": str(database_path),
        "journal_mode": journal_mode,
        "event_count": event_count,
    }

    if json_output:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"database: {result['database']}")
        print(f"journal_mode: {result['journal_mode']}")
        print(f"event_count: {result['event_count']}")

    return 0 if healthy else 1


def run_get(
    database_path: Path,
    sequence: int,
    *,
    json_output: bool = False,
) -> int:
    """Execute the get command."""

    if sequence < 1:
        print("eens: sequence must be greater than zero", file=sys.stderr)
        return 2

    store = EventStore(database_path)
    stored_event = store.get_by_sequence(sequence)

    if stored_event is None:
        print(f"eens: event sequence {sequence} not found", file=sys.stderr)
        return 1

    result = stored_event_to_dict(stored_event)

    if json_output:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"sequence: {result['sequence']}")
        print(f"stored_at: {result['stored_at']}")
        print(f"fingerprint: {result['fingerprint']}")
        print(f"event_id: {result['event_id']}")
        print(f"event_type: {result['event_type']}")
        print(f"source: {result['source']}")
        print(f"subject: {result['subject']}")
        print(f"occurred_at: {result['occurred_at']}")
        print(f"idempotency_key: {result['idempotency_key']}")
        print(
            "payload: "
            + json.dumps(result["payload"], sort_keys=True)
        )

    return 0


def run_replay(
    database_path: Path,
    *,
    after: int = 0,
    limit: int | None = None,
    json_output: bool = False,
) -> int:
    """Execute the replay command."""

    if after < 0:
        print("eens: --after must be zero or greater", file=sys.stderr)
        return 2

    if limit is not None and limit < 1:
        print("eens: --limit must be greater than zero", file=sys.stderr)
        return 2

    store = EventStore(database_path)
    events = [
        stored_event_to_dict(stored_event)
        for stored_event in store.replay(after_sequence=after, limit=limit)
    ]

    if json_output:
        print(json.dumps(events, sort_keys=True))
        return 0

    for index, event in enumerate(events):
        if index:
            print()
        print(f"sequence: {event['sequence']}")
        print(f"event_type: {event['event_type']}")
        print(f"source: {event['source']}")
        print(f"subject: {event['subject']}")
        print(f"occurred_at: {event['occurred_at']}")
        print(
            "payload: "
            + json.dumps(event["payload"], sort_keys=True)
        )

    return 0


def _matching_existing_event(
    store: EventStore,
    *,
    event_type: str,
    source: str,
    subject: str,
    idempotency_key: str,
    payload: dict[str, Any],
    event_id: str | None,
    occurred_at: str | None,
) -> StoredEvent | None:
    """Resolve an existing idempotent request before generating metadata."""

    for stored_event in store.replay():
        existing = stored_event.event

        if existing.idempotency_key != idempotency_key:
            continue

        matches = (
            existing.event_type == event_type
            and existing.source == source
            and existing.subject == subject
            and existing.payload == payload
            and (event_id is None or existing.event_id == event_id)
            and (
                occurred_at is None
                or existing.occurred_at == occurred_at
            )
        )

        if not matches:
            raise IdempotencyConflictError(
                f"idempotency key already belongs to sequence "
                f"{stored_event.sequence}"
            )

        return stored_event

    return None


def run_emit(
    database_path: Path,
    *,
    event_type: str,
    source: str,
    subject: str,
    idempotency_key: str,
    payload: dict[str, Any],
    event_id: str | None = None,
    occurred_at: str | None = None,
    json_output: bool = False,
) -> int:
    """Execute the emit command."""

    store = EventStore(database_path)

    try:
        existing = _matching_existing_event(
            store,
            event_type=event_type,
            source=source,
            subject=subject,
            idempotency_key=idempotency_key,
            payload=payload,
            event_id=event_id,
            occurred_at=occurred_at,
        )

        if existing is not None:
            output = {
                "status": "duplicate",
                "inserted": False,
                "sequence": existing.sequence,
                "event_id": existing.event.event_id,
                "fingerprint": existing.fingerprint,
            }
        else:
            event_arguments: dict[str, Any] = {
                "event_type": event_type,
                "source": source,
                "subject": subject,
                "idempotency_key": idempotency_key,
                "payload": payload,
            }

            if event_id is not None:
                event_arguments["event_id"] = event_id

            if occurred_at is not None:
                event_arguments["occurred_at"] = occurred_at

            event = EngineeringEvent(**event_arguments)
            result = store.append(event)

            output = {
                "status": (
                    "inserted" if result.inserted else "duplicate"
                ),
                "inserted": result.inserted,
                "sequence": result.sequence,
                "event_id": event.event_id,
                "fingerprint": event.fingerprint(),
            }
    except IdempotencyConflictError as exc:
        print(f"eens: idempotency conflict: {exc}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(f"eens: invalid event: {exc}", file=sys.stderr)
        return 2

    if json_output:
        print(json.dumps(output, sort_keys=True))
    else:
        print(f"status: {output['status']}")
        print(f"sequence: {output['sequence']}")
        print(f"event_id: {output['event_id']}")
        print(f"fingerprint: {output['fingerprint']}")

    return 0



def run_handoff(
    database_path: Path,
    *,
    state: str,
    mission: str,
    handoff: int,
    source: str,
    detail: str | None = None,
    json_output: bool = False,
) -> int:
    """Emit a standardized engineering handoff lifecycle event."""

    if handoff < 1:
        print("eens: --handoff must be greater than zero", file=sys.stderr)
        return 2

    try:
        result = HandoffLifecycleProducer(
            EventStore(database_path),
            source=source,
        ).emit(
            state=state,
            mission=mission,
            handoff=handoff,
            detail=detail,
        )
    except (TypeError, ValueError) as exc:
        print(f"eens: invalid handoff event: {exc}", file=sys.stderr)
        return 2
    except IdempotencyConflictError as exc:
        print(f"eens: idempotency conflict: {exc}", file=sys.stderr)
        return 1

    output = {
        "status": "inserted" if result.inserted else "duplicate",
        "inserted": result.inserted,
        "sequence": result.sequence,
        "event_type": result.event.event_type,
        "idempotency_key": result.event.idempotency_key,
        "event_id": result.event.event_id,
        "fingerprint": result.event.fingerprint(),
    }

    if json_output:
        print(json.dumps(output, sort_keys=True))
    else:
        print(f"status: {output['status']}")
        print(f"sequence: {output['sequence']}")
        print(f"event_type: {output['event_type']}")
        print(f"idempotency_key: {output['idempotency_key']}")
        print(f"event_id: {output['event_id']}")
        print(f"fingerprint: {output['fingerprint']}")

    return 0


def run_wrapped_command(
    database_path: Path,
    *,
    mission: str,
    handoff: int,
    source: str,
    cwd: str | None,
    command_args: list[str],
) -> int:
    """Execute a command inside a standardized handoff lifecycle."""

    if handoff < 1:
        print("eens: --handoff must be greater than zero", file=sys.stderr)
        return 2

    normalized_command = list(command_args)
    if normalized_command and normalized_command[0] == "--":
        normalized_command = normalized_command[1:]

    if not normalized_command:
        print("eens: wrapped command is required after --", file=sys.stderr)
        return 2

    try:
        result = HandoffCommandRunner(
            EventStore(database_path),
            source=source,
        ).run(
            mission=mission,
            handoff=handoff,
            command=normalized_command,
            cwd=Path(cwd).expanduser() if cwd else None,
        )
    except FileNotFoundError as exc:
        print(f"eens: command not found: {exc.filename}", file=sys.stderr)
        return 127
    except NotADirectoryError as exc:
        print(f"eens: invalid working directory: {exc}", file=sys.stderr)
        return 2
    except (TypeError, ValueError) as exc:
        print(f"eens: invalid runtime request: {exc}", file=sys.stderr)
        return 2
    except IdempotencyConflictError as exc:
        print(f"eens: idempotency conflict: {exc}", file=sys.stderr)
        return 1

    return result.returncode


def run_consume(
    database_path: Path,
    *,
    consumer_name: str,
    limit: int | None,
    checkpoint_path: str | None,
    json_output: bool,
) -> int:
    """Consume events and advance a durable per-consumer checkpoint."""

    if limit is not None and limit < 1:
        print("eens: --limit must be greater than zero", file=sys.stderr)
        return 2

    checkpoint_database = (
        Path(checkpoint_path).expanduser()
        if checkpoint_path
        else database_path.with_name(
            f"{database_path.stem}.consumers.sqlite3"
        )
    )

    try:
        consumer = EventConsumer(
            EventStore(database_path),
            checkpoint_database,
            consumer_name=consumer_name,
        )
        consumed = consumer.consume(limit=limit)
    except (TypeError, ValueError) as exc:
        print(f"eens: invalid consumer request: {exc}", file=sys.stderr)
        return 2

    for stored_event in consumed:
        event = stored_event.event
        output = {
            "sequence": stored_event.sequence,
            "event_type": event.event_type,
            "source": event.source,
            "subject": event.subject,
            "occurred_at": event.occurred_at,
            "payload": event.payload,
            "event_id": event.event_id,
            "idempotency_key": event.idempotency_key,
            "fingerprint": stored_event.fingerprint,
        }

        if json_output:
            print(json.dumps(output, sort_keys=True))
        else:
            print(f"sequence: {output['sequence']}")
            print(f"event_type: {output['event_type']}")
            print(f"source: {output['source']}")
            print(f"subject: {output['subject']}")
            print(f"occurred_at: {output['occurred_at']}")
            print(
                "payload: "
                + json.dumps(output["payload"], sort_keys=True)
            )
            print()

    return 0

def run_notify_ntfy(
    database_path: Path,
    *,
    server: str,
    topic: str,
    token: str | None,
    consumer_name: str,
    limit: int | None,
    checkpoint_path: str | None,
    timeout: float,
    json_output: bool,
) -> int:
    """Deliver pending events to ntfy using a durable checkpoint."""

    if limit is not None and limit < 1:
        print("eens: --limit must be greater than zero", file=sys.stderr)
        return 2

    checkpoint_database = (
        Path(checkpoint_path).expanduser()
        if checkpoint_path
        else database_path.with_name(
            f"{database_path.stem}.consumers.sqlite3"
        )
    )

    try:
        consumer = EventConsumer(
            EventStore(database_path),
            checkpoint_database,
            consumer_name=consumer_name,
        )
        notifier = NtfyNotifier(
            server=server,
            topic=topic,
            token=token,
            timeout=timeout,
        )
        delivered = NotificationDispatcher(
            consumer,
            notifier,
        ).dispatch(limit=limit)
    except NotificationError as exc:
        print(f"eens: notification delivery failed: {exc}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(f"eens: invalid notification request: {exc}", file=sys.stderr)
        return 2

    for result in delivered:
        output = {
            "sequence": result.sequence,
            "endpoint": result.endpoint,
            "status_code": result.status_code,
        }

        if json_output:
            print(json.dumps(output, sort_keys=True))
        else:
            print(f"sequence: {output['sequence']}")
            print(f"endpoint: {output['endpoint']}")
            print(f"status_code: {output['status_code']}")
            print()

    return 0


def run_service_ntfy(
    database_path: Path,
    *,
    server: str,
    topic: str | None,
    token: str | None,
    consumer_name: str,
    checkpoint_path: str | None,
    timeout: float,
    poll_interval: float,
) -> int:
    """Continuously deliver pending events to ntfy."""

    checkpoint_database = (
        Path(checkpoint_path).expanduser()
        if checkpoint_path
        else database_path.with_name(
            f"{database_path.stem}.consumers.sqlite3"
        )
    )

    def report_error(error: NotificationError) -> None:
        print(
            f"eens: notification delivery failed: {error}",
            file=sys.stderr,
        )

    consumer = EventConsumer(
        EventStore(database_path),
        checkpoint_database,
        consumer_name=consumer_name,
    )
    notifier = NtfyNotifier(
        server=server,
        topic=topic,
        token=token,
        timeout=timeout,
    )
    dispatcher = NotificationDispatcher(
        consumer,
        notifier,
    )
    service = NotificationService(
        dispatcher,
        poll_interval=poll_interval,
        error_handler=report_error,
    )
    service.run()

    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the EENS command-line interface."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    database_path = resolve_database_path(arguments.database)

    try:
        if arguments.command == "count":
            return run_count(database_path)

        if arguments.command == "health":
            return run_health(
                database_path,
                json_output=arguments.json,
            )

        if arguments.command == "get":
            return run_get(
                database_path,
                arguments.sequence,
                json_output=arguments.json,
            )

        if arguments.command == "replay":
            return run_replay(
                database_path,
                after=arguments.after,
                limit=arguments.limit,
                json_output=arguments.json,
            )

        if arguments.command == "emit":
            return run_emit(
                database_path,
                event_type=arguments.event_type,
                source=arguments.source,
                subject=arguments.subject,
                idempotency_key=arguments.idempotency_key,
                payload=arguments.payload,
                event_id=arguments.event_id,
                occurred_at=arguments.occurred_at,
                json_output=arguments.json,
            )

        if arguments.command == "handoff":
            return run_handoff(
                database_path,
                state=arguments.state,
                mission=arguments.mission,
                handoff=arguments.handoff,
                source=arguments.source,
                detail=arguments.detail,
                json_output=arguments.json,
            )

        if arguments.command == "run":
            return run_wrapped_command(
                database_path,
                mission=arguments.mission,
                handoff=arguments.handoff,
                source=arguments.source,
                cwd=arguments.cwd,
                command_args=arguments.command_args,
            )

        if arguments.command == "consume":
            return run_consume(
                database_path,
                consumer_name=arguments.consumer,
                limit=arguments.limit,
                checkpoint_path=arguments.checkpoint,
                json_output=arguments.json,
            )

        if (
            arguments.command == "service"
            and arguments.service_transport == "ntfy"
        ):
            return run_service_ntfy(
                database_path,
                server=resolve_ntfy_server(arguments.server),
                topic=resolve_ntfy_topic(arguments.topic),
                token=resolve_ntfy_token(arguments.token),
                consumer_name=arguments.consumer,
                checkpoint_path=arguments.checkpoint,
                timeout=arguments.timeout,
                poll_interval=arguments.poll_interval,
            )

        if (
            arguments.command == "notify"
            and arguments.notify_transport == "ntfy"
        ):
            return run_notify_ntfy(
                database_path,
                server=resolve_ntfy_server(arguments.server),
                topic=resolve_ntfy_topic(arguments.topic),
                token=resolve_ntfy_token(arguments.token),
                consumer_name=arguments.consumer,
                limit=arguments.limit,
                checkpoint_path=arguments.checkpoint,
                timeout=arguments.timeout,
                json_output=arguments.json,
            )

    except OSError as exc:
        print(f"eens: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {arguments.command}")
    return 2
