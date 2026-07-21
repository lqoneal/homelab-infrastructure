"""Durable event consumption with independent checkpoints."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .store import EventStore, StoredEvent


CHECKPOINT_SCHEMA = """
CREATE TABLE IF NOT EXISTS consumer_checkpoints (
    consumer_name TEXT PRIMARY KEY,
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


class EventConsumer:
    """Read EENS events once per named consumer."""

    def __init__(
        self,
        store: EventStore,
        checkpoint_path: Path,
        *,
        consumer_name: str,
    ) -> None:
        normalized_name = consumer_name.strip()
        if not normalized_name:
            raise ValueError("consumer_name must not be empty")

        self._store = store
        self._checkpoint_path = Path(checkpoint_path)
        self._consumer_name = normalized_name
        self._initialize_checkpoint_store()

    def pending(
        self,
        *,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        """Return pending events without advancing the checkpoint."""

        if limit is not None and limit < 1:
            raise ValueError("limit must be greater than zero")

        return list(
            self._store.replay(
                after_sequence=self.checkpoint(),
                limit=limit,
            )
        )

    def acknowledge(self, sequence: int) -> None:
        """Advance the checkpoint through a successfully processed event."""

        if sequence < 1:
            raise ValueError("sequence must be greater than zero")

        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO consumer_checkpoints (
                        consumer_name,
                        sequence,
                        updated_at
                    )
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(consumer_name) DO UPDATE SET
                        sequence = excluded.sequence,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE excluded.sequence > consumer_checkpoints.sequence
                    """,
                    (self._consumer_name, sequence),
                )

    def consume(
        self,
        *,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        """Return pending events and advance the checkpoint."""

        events = self.pending(limit=limit)

        if events:
            self.acknowledge(events[-1].sequence)

        return events

    def checkpoint(self) -> int:
        """Return the current checkpoint for this consumer."""

        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT sequence
                FROM consumer_checkpoints
                WHERE consumer_name = ?
                """,
                (self._consumer_name,),
            ).fetchone()

        return 0 if row is None else int(row[0])

    def _initialize_checkpoint_store(self) -> None:
        self._checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(CHECKPOINT_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._checkpoint_path)
