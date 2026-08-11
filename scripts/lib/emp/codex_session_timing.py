"""Passive Codex session timing observability.

This component records timing information only. It does not own, alter,
intercept, replace, or authorize Zeus-managed lifecycle, transport,
provider/session binding, execution control, stdin/stdout, or EOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Sequence
import uuid


DEFAULT_LOG_ROOT = Path(
    "/data/engineering/logs/codex-session-timed"
)


def format_duration(seconds: float) -> str:
    value = max(0, int(round(float(seconds))))

    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_name(
        path.name + ".tmp-" + uuid.uuid4().hex
    )

    temporary.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


def _session_records(root: Path) -> list[dict[str, Any]]:
    directory = root / "sessions"

    if not directory.is_dir():
        return []

    records: list[dict[str, Any]] = []

    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(
                path.read_text(encoding="utf-8")
            )
        except Exception:
            continue

        if not isinstance(value, dict):
            continue

        duration = value.get("duration_seconds")

        if not isinstance(duration, (int, float)):
            continue

        records.append(value)

    return records


def _summary(root: Path) -> dict[str, Any]:
    records = _session_records(root)

    durations = [
        float(record["duration_seconds"])
        for record in records
    ]

    average = (
        sum(durations) / len(durations)
        if durations
        else 0.0
    )

    return {
        "session_count": len(records),
        "average_seconds": round(average, 3),
        "average_formatted": format_duration(average),
    }


def record_passive_managed_timing(
    *,
    repository_root: Path | str,
    duration_seconds: float,
    codex_session_id: str | None = None,
    execution_session_id: str | None = None,
    provider_session_id: str | None = None,
    log_root: Path | str | None = None,
) -> dict[str, Any]:
    duration = float(duration_seconds)

    if duration < 0:
        raise ValueError(
            "duration_seconds must be nonnegative"
        )

    repository = Path(repository_root).resolve()
    root = Path(
        DEFAULT_LOG_ROOT
        if log_root is None
        else log_root
    ).resolve()

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%S.%fZ")

    record_id = (
        "codex-session-"
        + timestamp
        + "-"
        + uuid.uuid4().hex[:12]
    )

    record = {
        "record_id": record_id,
        "recorded_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "repository_root": str(repository),
        "duration_seconds": round(duration, 3),
        "elapsed_seconds": round(duration, 3),
        "elapsed_formatted": format_duration(duration),
        "codex_session_id": codex_session_id,
        "execution_session_id": execution_session_id,
        "provider_session_id": provider_session_id,
        "observability_only": True,
    }

    session_path = (
        root
        / "sessions"
        / f"{record_id}.json"
    )

    _atomic_json(
        session_path,
        record,
    )

    summary = _summary(root)

    _atomic_json(
        root / "summary.json",
        summary,
    )

    latest = {
        **record,
        "running_average_seconds":
            summary["average_seconds"],
        "running_average_formatted":
            summary["average_formatted"],
        "session_count":
            summary["session_count"],
    }

    _atomic_json(
        root / "latest.json",
        latest,
    )

    return latest


def _dispatch_timed(
    command: Sequence[str],
    *,
    repository_root: Path,
) -> int:
    if not command:
        return 2

    started = time.monotonic()

    completed = subprocess.run(
        list(command),
        cwd=repository_root,
        check=False,
    )

    duration = time.monotonic() - started

    try:
        record_passive_managed_timing(
            repository_root=repository_root,
            duration_seconds=duration,
        )
    except Exception:
        pass

    return completed.returncode


def dispatch_cli(
    arguments: Sequence[str],
    *,
    repository_root: Path | str,
) -> int | None:
    args = list(arguments)

    if len(args) < 2:
        return None

    if args[0] != "codex" or args[1] != "timed":
        return None

    return _dispatch_timed(
        args[2:],
        repository_root=Path(
            repository_root
        ).resolve(),
    )
