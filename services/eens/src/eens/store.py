"""Durable SQLite event storage for EENS."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .events import EngineeringEvent, utc_now


class EventStoreError(RuntimeError):
    """Base exception for event-store failures."""


class IdempotencyConflictError(EventStoreError):
    """Raised when an idempotency key is reused for different content."""


@dataclass(frozen=True, slots=True)
class AppendResult:
    """Result returned after attempting to append an event."""

    sequence: int
    event_id: str
    fingerprint: str
    inserted: bool


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """Persisted event and storage metadata."""

    sequence: int
    event: EngineeringEvent
    fingerprint: str
    stored_at: str


class EventStore:
    """Append-only SQLite event store."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    schema_version TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    canonical_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_type
                    ON events(event_type);

                CREATE INDEX IF NOT EXISTS idx_events_occurred_at
                    ON events(occurred_at);
                """
            )

    def append(self, event: EngineeringEvent) -> AppendResult:
        canonical = event.canonical_json()
        fingerprint = event.fingerprint()
        stored_at = utc_now()

        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    """
                    SELECT sequence, event_id, fingerprint
                    FROM events
                    WHERE idempotency_key = ?
                    """,
                    (event.idempotency_key,),
                ).fetchone()

                if existing is not None:
                    connection.execute("COMMIT")
                    if existing["fingerprint"] == fingerprint:
                        return AppendResult(
                            sequence=existing["sequence"],
                            event_id=existing["event_id"],
                            fingerprint=existing["fingerprint"],
                            inserted=False,
                        )
                    raise IdempotencyConflictError(
                        "idempotency key already exists with different content: "
                        f"{event.idempotency_key}"
                    )

                cursor = connection.execute(
                    """
                    INSERT INTO events (
                        event_id,
                        schema_version,
                        event_type,
                        source,
                        subject,
                        idempotency_key,
                        occurred_at,
                        payload_json,
                        canonical_json,
                        fingerprint,
                        stored_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.schema_version,
                        event.event_type,
                        event.source,
                        event.subject,
                        event.idempotency_key,
                        event.occurred_at,
                        json.dumps(
                            dict(event.payload),
                            ensure_ascii=False,
                            separators=(",", ":"),
                            sort_keys=True,
                        ),
                        canonical,
                        fingerprint,
                        stored_at,
                    ),
                )

                sequence = int(cursor.lastrowid)
                connection.execute("COMMIT")
                return AppendResult(
                    sequence=sequence,
                    event_id=event.event_id,
                    fingerprint=fingerprint,
                    inserted=True,
                )
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def get_by_sequence(self, sequence: int) -> StoredEvent | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM events WHERE sequence = ?",
                (sequence,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_stored_event(row)

    def replay(
        self,
        after_sequence: int = 0,
        limit: int | None = None,
    ) -> Iterator[StoredEvent]:
        if after_sequence < 0:
            raise ValueError("after_sequence must be zero or greater")
        if limit is not None and limit <= 0:
            raise ValueError("limit must be greater than zero")

        sql = """
            SELECT *
            FROM events
            WHERE sequence > ?
            ORDER BY sequence ASC
        """
        parameters: list[int] = [after_sequence]

        if limit is not None:
            sql += " LIMIT ?"
            parameters.append(limit)

        with closing(self._connect()) as connection:
            rows = connection.execute(sql, parameters).fetchall()

        for row in rows:
            yield self._row_to_stored_event(row)

    def count(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS event_count FROM events"
            ).fetchone()
        return int(row["event_count"])

    def journal_mode(self) -> str:
        with closing(self._connect()) as connection:
            row = connection.execute("PRAGMA journal_mode").fetchone()
        return str(row[0]).lower()

    @staticmethod
    def _row_to_stored_event(row: sqlite3.Row) -> StoredEvent:
        event = EngineeringEvent(
            event_id=row["event_id"],
            schema_version=row["schema_version"],
            event_type=row["event_type"],
            source=row["source"],
            subject=row["subject"],
            idempotency_key=row["idempotency_key"],
            occurred_at=row["occurred_at"],
            payload=json.loads(row["payload_json"]),
        )
        return StoredEvent(
            sequence=row["sequence"],
            event=event,
            fingerprint=row["fingerprint"],
            stored_at=row["stored_at"],
        )
