"""Runtime adapter for executing commands inside handoff lifecycles."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .lifecycle import HandoffLifecycleProducer
from .store import EventStore


@dataclass(frozen=True)
class HandoffCommandResult:
    """Result of a command wrapped by handoff lifecycle events."""

    returncode: int
    started_sequence: int
    terminal_sequence: int


class HandoffCommandRunner:
    """Execute a command and emit lifecycle events around it."""

    def __init__(
        self,
        store: EventStore,
        *,
        source: str = "engineering-handoff-runtime",
    ) -> None:
        if not source or not source.strip():
            raise ValueError("source must not be empty")

        self._producer = HandoffLifecycleProducer(
            store,
            source=source.strip(),
        )

    def run(
        self,
        *,
        mission: str,
        handoff: int,
        command: Sequence[str],
        cwd: Path | None = None,
    ) -> HandoffCommandResult:
        """Run the command, preserving its inherited streams and exit code."""

        normalized_command = [str(part) for part in command]

        if not normalized_command:
            raise ValueError("command must not be empty")
        if any(not part for part in normalized_command):
            raise ValueError("command arguments must not be empty")

        command_display = " ".join(normalized_command)

        started = self._producer.emit(
            state="started",
            mission=mission,
            handoff=handoff,
            detail=f"Command started: {command_display}",
        )

        try:
            completed_process = subprocess.run(
                normalized_command,
                cwd=cwd,
                check=False,
            )
        except FileNotFoundError:
            self._producer.emit(
                state="failed",
                mission=mission,
                handoff=handoff,
                detail=f"Command not found: {normalized_command[0]}",
            )
            raise
        except OSError as exc:
            self._producer.emit(
                state="failed",
                mission=mission,
                handoff=handoff,
                detail=f"Command launch failed: {exc}",
            )
            raise

        if completed_process.returncode == 0:
            terminal = self._producer.emit(
                state="completed",
                mission=mission,
                handoff=handoff,
                detail=f"Command exited with status 0: {command_display}",
            )
        else:
            terminal = self._producer.emit(
                state="failed",
                mission=mission,
                handoff=handoff,
                detail=(
                    f"Command exited with status "
                    f"{completed_process.returncode}: {command_display}"
                ),
            )

        return HandoffCommandResult(
            returncode=completed_process.returncode,
            started_sequence=started.sequence,
            terminal_sequence=terminal.sequence,
        )
