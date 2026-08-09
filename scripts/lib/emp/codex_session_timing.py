"""Passive timing records for direct and future Zeus-managed Codex sessions.

This module deliberately owns timing records only.  It does not discover,
launch, attach to, signal, reconcile, or otherwise manage a Zeus runtime or
provider session.  The managed-session API accepts lifecycle timestamps from
an owner that already has those timestamps; it never reads managed runtime
state.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "zeus-codex-session-timing/1"
DEFAULT_LOG_ROOT = Path("/data/engineering/logs/codex-session-timed")
LOG_ROOT_ENV = "ZEUS_CODEX_TIMING_ROOT"
SESSION_CLASS_DIRECT = "DIRECT"
SESSION_CLASS_MANAGED = "ZEUS_MANAGED"


class TimingPersistenceError(RuntimeError):
    """The child result is valid, but the timing record could not be saved."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def format_duration(seconds: int | float | Decimal) -> str:
    """Format seconds by rounding to the nearest whole second, half up."""
    rounded = int(Decimal(str(seconds)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    hours, remainder = divmod(max(0, rounded), 3600)
    minutes, seconds_part = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"
    return f"{minutes:02d}:{seconds_part:02d}"


def average_statistics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = [record for record in records if record.get("record_status") == "COMPLETED"]
    total = sum(Decimal(str(record["elapsed_seconds"])) for record in eligible)
    average = (total / len(eligible)) if eligible else Decimal("0")
    # Six decimal places preserves precise source timing while keeping the
    # derived JSON stable. Formatting uses the unrounded Decimal value.
    average_json = float(average.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
    return {
        "sample_count": len(eligible),
        "average_seconds": average_json,
        "average_formatted": format_duration(average),
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return timestamp(value)
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, default=_json_value)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            # Directory fsync is not available on every supported filesystem;
            # the rename remains atomic and the file itself was fsynced.
            pass
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise TimingPersistenceError(f"atomic timing write failed for {path}: {error}") from error


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


@dataclass
class TimingObservation:
    record_id: str
    started_at: datetime
    started_monotonic: float
    context: dict[str, Any]
    _final_record: dict[str, Any] | None = None


class TimingStore:
    """Append-only records with a lock-protected derived summary."""

    def __init__(self, root: Path | str = DEFAULT_LOG_ROOT):
        self.root = Path(root).expanduser().resolve()
        self.sessions = self.root / "sessions"
        self.summary_path = self.root / "summary.json"
        self.latest_path = self.root / "latest.json"
        self.lock_path = self.root / ".timing.lock"

    def _lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.sessions.mkdir(parents=True, exist_ok=True)
        stream = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        return stream

    @staticmethod
    def _unlock(stream) -> None:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()

    def start(self, context: Mapping[str, Any] | None = None, *, started_at: datetime | None = None,
              started_monotonic: float | None = None) -> TimingObservation:
        return TimingObservation(
            record_id=str(uuid.uuid4()),
            started_at=(started_at or utc_now()).astimezone(timezone.utc),
            started_monotonic=time.monotonic() if started_monotonic is None else started_monotonic,
            context=dict(context or {}),
        )

    def _record_path(self, record_id: str) -> Path:
        if not record_id or Path(record_id).name != record_id or record_id in {".", ".."}:
            raise TimingPersistenceError("timing record ID must be a single safe path component")
        return self.sessions / f"{record_id}.json"

    def finalize(self, observation: TimingObservation, *, child_exit_code: int | None,
                 termination_classification: str | None = None,
                 ended_at: datetime | None = None, ended_monotonic: float | None = None) -> dict[str, Any]:
        if observation._final_record is not None:
            return dict(observation._final_record)
        end = (ended_at or utc_now()).astimezone(timezone.utc)
        monotonic_end = time.monotonic() if ended_monotonic is None else ended_monotonic
        elapsed = monotonic_end - observation.started_monotonic
        if elapsed < 0:
            raise TimingPersistenceError("monotonic end timestamp precedes start timestamp")
        record = self.record(
            record_id=observation.record_id,
            started_at=observation.started_at,
            ended_at=end,
            elapsed_seconds=elapsed,
            child_exit_code=child_exit_code,
            termination_classification=termination_classification,
            context=observation.context,
        )
        observation._final_record = dict(record)
        return record

    def record(self, *, record_id: str, started_at: datetime, ended_at: datetime,
               elapsed_seconds: int | float | Decimal, child_exit_code: int | None,
               termination_classification: str | None = None,
               context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if Decimal(str(elapsed_seconds)) < 0:
            raise TimingPersistenceError("elapsed seconds cannot be negative")
        record_path = self._record_path(record_id)
        lock = self._lock()
        try:
            existing = _load_json(record_path)
            if existing is not None:
                if existing.get("record_id") != record_id or existing.get("record_status") != "COMPLETED":
                    if existing.get("record_id") not in {None, record_id}:
                        raise TimingPersistenceError(f"record identity conflict: {record_path}")
                    # A crash can leave a same-name incomplete artifact. It is
                    # ignored by aggregation and safely promoted atomically
                    # by this finalization.
                else:
                    self._refresh_summary_locked()
                    return existing
            started = started_at.astimezone(timezone.utc)
            ended = ended_at.astimezone(timezone.utc)
            precise_elapsed = float(Decimal(str(elapsed_seconds)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
            value: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "record_status": "COMPLETED",
                "record_id": record_id,
                "start_timestamp_utc": timestamp(started),
                "end_timestamp_utc": timestamp(ended),
                "elapsed_seconds": precise_elapsed,
                "elapsed_formatted": format_duration(precise_elapsed),
                "child_exit_code": child_exit_code,
                "termination_classification": termination_classification,
                "repository_root": None,
                "working_directory": None,
                "invocation_mode": None,
                "command_surface": [],
                "mission_id": None,
                "execution_id": None,
                "codex_session_id": None,
                "zeus_managed": False,
                "execution_classification": SESSION_CLASS_DIRECT,
                "log_sequence": None,
                "replay_identity": record_id,
            }
            context_keys = {
                "repository_root", "working_directory", "invocation_mode", "command_surface",
                "mission_id", "execution_id", "codex_session_id", "zeus_managed",
                "execution_classification", "log_sequence", "replay_identity",
                "execution_session_id", "provider_session_id", "metadata",
            }
            for key, item in dict(context or {}).items():
                if key in context_keys:
                    value[key] = item
                else:
                    value.setdefault("metadata", {})[key] = item
            _atomic_json(record_path, value)
            self._refresh_summary_locked()
            return value
        finally:
            self._unlock(lock)

    def _valid_records_locked(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not self.sessions.is_dir():
            return records
        for path in sorted(self.sessions.glob("*.json")):
            value = _load_json(path)
            if not value or value.get("schema_version") != SCHEMA_VERSION:
                continue
            if value.get("record_status") != "COMPLETED" or not value.get("record_id"):
                continue
            try:
                elapsed = Decimal(str(value["elapsed_seconds"]))
                started = parse_timestamp(value["start_timestamp_utc"])
                ended = parse_timestamp(value["end_timestamp_utc"])
                if not elapsed.is_finite() or elapsed < 0 or ended < started:
                    continue
            except (InvalidOperation, KeyError, TypeError, ValueError):
                continue
            records.append(value)
        return records

    def _refresh_summary_locked(self) -> dict[str, Any]:
        records = self._valid_records_locked()
        statistics = average_statistics(records)
        summary = {
            "schema_version": SCHEMA_VERSION,
            "summary_type": "RUNNING_AVERAGE",
            "generated_at_utc": timestamp(utc_now()),
            "eligible_record_ids": [item["record_id"] for item in records],
            **statistics,
        }
        _atomic_json(self.summary_path, summary)
        latest = max(records, key=lambda item: (item["end_timestamp_utc"], item["record_id"]), default=None)
        _atomic_json(self.latest_path, latest or {"schema_version": SCHEMA_VERSION, "record_status": "EMPTY"})
        return summary

    def summary(self) -> dict[str, Any]:
        lock = self._lock()
        try:
            return self._refresh_summary_locked()
        finally:
            self._unlock(lock)

    def records(self) -> list[dict[str, Any]]:
        lock = self._lock()
        try:
            return self._valid_records_locked()
        finally:
            self._unlock(lock)


def timing_root() -> Path:
    return Path(os.environ.get(LOG_ROOT_ENV, str(DEFAULT_LOG_ROOT))).expanduser()


def direct_context(command_args: Sequence[str], *, repository_root: Path | str,
                  working_directory: Path | str, codex_bin: str) -> dict[str, Any]:
    """Build metadata only from explicit operator context; never read Zeus runtime state."""
    return {
        "repository_root": str(Path(repository_root).resolve()),
        "working_directory": str(Path(working_directory).resolve()),
        "invocation_mode": "DIRECT_CODEX_CLI",
        "command_surface": [codex_bin, *command_args],
        "mission_id": os.environ.get("ZEUS_CODEX_TIMING_MISSION_ID"),
        "execution_id": os.environ.get("ZEUS_CODEX_TIMING_EXECUTION_ID"),
        "codex_session_id": os.environ.get("ZEUS_CODEX_TIMING_CODEX_SESSION_ID"),
        "log_sequence": os.environ.get("ZEUS_CODEX_TIMING_LOG_SEQUENCE"),
        "zeus_managed": False,
        "execution_classification": SESSION_CLASS_DIRECT,
    }


def record_passive_managed_timing(store: TimingStore, *, record_id: str, start_timestamp: datetime,
                                  end_timestamp: datetime, elapsed_seconds: int | float | Decimal,
                                  mission_id: str | None = None, execution_id: str | None = None,
                                  codex_session_id: str | None = None,
                                  execution_session_id: str | None = None,
                                  provider_session_id: str | None = None,
                                  log_sequence: str | None = None,
                                  replay_identity: str | None = None) -> dict[str, Any]:
    """Record timestamps supplied by Zeus lifecycle ownership, passively.

    A future managed hook may call this after an owner emits a terminal event.
    It intentionally accepts timestamps/identities as data and performs no
    runtime discovery, process access, transport I/O, or lifecycle mutation.
    """
    return store.record(
        record_id=record_id,
        started_at=start_timestamp,
        ended_at=end_timestamp,
        elapsed_seconds=elapsed_seconds,
        child_exit_code=None,
        termination_classification=None,
        context={
            "repository_root": None,
            "working_directory": None,
            "invocation_mode": "PASSIVE_LIFECYCLE_EVENT",
            "command_surface": [],
            "mission_id": mission_id,
            "execution_id": execution_id,
            "codex_session_id": codex_session_id,
            "execution_session_id": execution_session_id,
            "provider_session_id": provider_session_id,
            "zeus_managed": True,
            "execution_classification": SESSION_CLASS_MANAGED,
            "log_sequence": log_sequence,
            "replay_identity": replay_identity or record_id,
        },
    )


def _termination_label(returncode: int) -> str | None:
    return f"SIGNAL_{signal.Signals(-returncode).name}" if returncode < 0 else None


def run_direct(command_args: Sequence[str], *, repository_root: Path | str,
               codex_bin: str | None = None, store: TimingStore | None = None) -> int:
    """Run a direct Codex child with inherited stdio and preserve its result."""
    executable = codex_bin or os.environ.get("ZEUS_CODEX_BIN", "codex")
    selected_store = store or TimingStore(timing_root())
    observation = selected_store.start(direct_context(command_args, repository_root=repository_root,
                                                      working_directory=Path.cwd(), codex_bin=executable))
    child: subprocess.Popen[bytes] | None = None
    forwarded: list[int] = []
    old_handlers: dict[int, Any] = {}

    def forward(signum: int, _frame: Any) -> None:
        forwarded.append(signum)
        if child is not None and child.poll() is None:
            try:
                child.send_signal(signum)
            except ProcessLookupError:
                pass

    signals = [item for item in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)
               if hasattr(signal, item.name)]
    try:
        child = subprocess.Popen([executable, *command_args])
        for item in signals:
            old_handlers[item] = signal.getsignal(item)
            signal.signal(item, forward)
        child.wait()
        child_code = child.returncode
    except OSError as error:
        print(f"CODEX_LAUNCH_FAILURE={error}", file=sys.stderr)
        child_code = 127
    finally:
        for item, handler in old_handlers.items():
            signal.signal(item, handler)

    try:
        record = selected_store.finalize(
            observation,
            child_exit_code=child_code,
            termination_classification=_termination_label(child_code),
        )
        summary = selected_store.summary()
        print(f"CODEX_EXIT_CODE={child_code}")
        print(f"CODEX_DURATION_SECONDS={record['elapsed_seconds']}")
        print(f"CODEX_DURATION={record['elapsed_formatted']}")
        print(f"CODEX_TIMING_SAMPLE_COUNT={summary['sample_count']}")
        print(f"CODEX_AVERAGE_SECONDS={summary['average_seconds']}")
        print(f"CODEX_AVERAGE_DURATION={summary['average_formatted']}")
        print(f"CODEX_TIMING_RECORD={selected_store._record_path(record['record_id'])}")
    except (OSError, TimingPersistenceError) as error:
        print(f"CODEX_TIMING_LOG_FAILURE={error}", file=sys.stderr)

    if child_code < 0:
        # Restore the original handler first, then let the wrapper die from
        # the same signal. This preserves normal shell signal semantics.
        os.kill(os.getpid(), -child_code)
    return child_code


def run_timing_command(arguments: Sequence[str], *, repository_root: Path | str) -> int:
    if not arguments or arguments[0] in {"--help", "-h"}:
        print("Usage: scripts/zeus codex timed <CODEX_ARGUMENT> [CODEX_ARGUMENT ...]")
        print("Runs the direct Codex CLI with inherited stdio and records passive timing data.")
        return 0
    return run_direct(arguments, repository_root=repository_root)


def run_summary_command(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="scripts/zeus codex timing summary")
    parser.add_argument("--json", action="store_true")
    parsed = parser.parse_args(list(arguments))
    try:
        value = TimingStore(timing_root()).summary()
    except (OSError, TimingPersistenceError) as error:
        print(f"CODEX_TIMING_LOG_FAILURE={error}", file=sys.stderr)
        return 78
    if parsed.json:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(f"sample_count={value['sample_count']}")
        print(f"average_seconds={value['average_seconds']}")
        print(f"average_formatted={value['average_formatted']}")
    return 0


def dispatch_cli(arguments: Sequence[str], *, repository_root: Path | str) -> int | None:
    """Dispatch only the isolated timing subcommands; return None otherwise."""
    if len(arguments) >= 2 and arguments[0:2] == ["codex", "timed"]:
        return run_timing_command(arguments[2:], repository_root=repository_root)
    if len(arguments) >= 3 and arguments[0:3] == ["codex", "timing", "summary"]:
        return run_summary_command(arguments[3:])
    return None
