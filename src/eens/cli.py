"""Command-line interface for EENS."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .store import EventStore


DEFAULT_DATABASE_PATH = Path("runtime/db/eens.sqlite3")


def resolve_database_path(value: str | None = None) -> Path:
    """Resolve the database path from an argument, environment, or default."""

    candidate = value or os.environ.get("EENS_DB_PATH")
    if candidate:
        return Path(candidate).expanduser()
    return DEFAULT_DATABASE_PATH


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

    return parser


def run_count(database_path: Path) -> int:
    """Execute the count command."""

    store = EventStore(database_path)
    print(store.count())
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the EENS command-line interface."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    database_path = resolve_database_path(arguments.database)

    try:
        if arguments.command == "count":
            return run_count(database_path)
    except OSError as exc:
        print(f"eens: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {arguments.command}")
    return 2
