"""Command-line interface for EENS."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .events import EngineeringEvent
from .store import EventStore, IdempotencyConflictError, StoredEvent


DEFAULT_DATABASE_PATH = Path("runtime/db/eens.sqlite3")


def resolve_database_path(value: str | None = None) -> Path:
    """Resolve the database path from an argument, environment, or default."""

    candidate = value or os.environ.get("EENS_DB_PATH")
    if candidate:
        return Path(candidate).expanduser()
    return DEFAULT_DATABASE_PATH


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
    except OSError as exc:
        print(f"eens: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {arguments.command}")
    return 2
