"""Exact-process termination for a Zeus execution session."""

from __future__ import annotations

import os
import signal
import time
from datetime import datetime, timezone
from typing import Any, Mapping


class TerminationError(ValueError):
    """Fail-closed termination-control error."""

    def __init__(self, category: str, message: str, diagnostics: Any = None):
        self.category = category
        self.diagnostics = diagnostics
        super().__init__(message)


def _proc_start_time(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            fields = handle.read().split()
    except (OSError, ValueError):
        return None
    return fields[21] if len(fields) > 21 else None


def _proc_state(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            fields = handle.read().split()
    except (OSError, ValueError):
        return None
    return fields[2] if len(fields) > 2 else None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return _proc_state(pid) not in {None, "Z"}


def process_diagnostics(session: Mapping[str, Any]) -> dict[str, Any]:
    pid = session.get("process_pid")
    pgid = session.get("process_group_id")
    recorded_start = session.get("process_start_time")
    valid_identity = isinstance(pid, int) and pid > 0 and isinstance(pgid, int) and pgid > 0
    current_pgid = None
    current_sid = None
    current_start = None
    alive = False
    if valid_identity:
        alive = _alive(pid)
        try:
            current_pgid = os.getpgid(pid)
        except OSError:
            current_pgid = None
        try:
            current_sid = os.getsid(pid)
        except OSError:
            current_sid = None
        current_start = _proc_start_time(pid)
    ownership = bool(
        valid_identity and current_pgid == pgid
        and (session.get("process_session_id") is None or current_sid == session.get("process_session_id"))
        and (recorded_start is None or current_start == str(recorded_start))
        and pgid != os.getpgrp()
    )
    return {
        "process_pid": pid,
        "process_group_id": pgid,
        "process_session_id": session.get("process_session_id"),
        "provider_id": session.get("provider_id"),
        "provider_execution_id": session.get("provider_execution_id"),
        "execution_agent": session.get("execution_agent"),
        "recorded_process_start_time": recorded_start,
        "current_process_start_time": current_start,
        "current_process_group_id": current_pgid,
        "current_process_session_id": current_sid,
        "process_state": "ACTIVE" if alive else "STOPPED",
        "process_identity_valid": valid_identity,
        "elapsed_inactivity": session.get("elapsed_inactivity"),
        "last_heartbeat": session.get("last_heartbeat"),
        "last_provider_event": session.get("last_provider_event"),
        "last_lifecycle_progress": session.get("last_lifecycle_progress"),
        "ownership_proven": ownership,
        "termination_eligible": ownership and alive,
    }


class ExecutionTerminator:
    """Terminate exactly the process group bound to one execution session."""

    def __init__(self, *, sleep=time.sleep, monotonic=time.monotonic):
        self.sleep = sleep
        self.monotonic = monotonic

    def stop(self, session: Mapping[str, Any], *, graceful_timeout: float = 2.0) -> dict[str, Any]:
        if graceful_timeout < 0:
            raise TerminationError("INVALID_TIMEOUT", "graceful timeout must not be negative")
        diagnostics = process_diagnostics(session)
        if not diagnostics["process_identity_valid"]:
            raise TerminationError("PROCESS_OWNERSHIP_UNPROVEN", "recorded process identity is incomplete", diagnostics)
        if not diagnostics["termination_eligible"]:
            if diagnostics["process_state"] in {"STOPPED", "ABSENT"}:
                return {"result": "ALREADY_STOPPED", "forced": False, "diagnostics": diagnostics}
            raise TerminationError("PROCESS_OWNERSHIP_UNPROVEN", "recorded process ownership cannot be proven", diagnostics)
        pgid = diagnostics["process_group_id"]
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return {"result": "ALREADY_STOPPED", "forced": False, "diagnostics": process_diagnostics(session)}
        deadline = self.monotonic() + graceful_timeout
        while _alive(diagnostics["process_pid"]) and self.monotonic() < deadline:
            self.sleep(min(0.02, max(0.0, deadline - self.monotonic())))
        forced = _alive(diagnostics["process_pid"])
        if forced:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                forced = False
            deadline = self.monotonic() + max(0.2, graceful_timeout)
            while _alive(diagnostics["process_pid"]) and self.monotonic() < deadline:
                self.sleep(0.02)
        final = process_diagnostics(session)
        if final["process_state"] == "ACTIVE":
            raise TerminationError("TERMINATION_FAILED", "exact process group remained active after escalation", final)
        return {"result": "STOPPED", "forced": forced, "diagnostics": final}


def termination_receipt(session: Mapping[str, Any], *, result: Mapping[str, Any], at: datetime) -> dict[str, Any]:
    from scripts.lib.emp.authority_resolution import digest
    if at.tzinfo is None:
        raise TerminationError("INVALID_TIMESTAMP", "termination timestamp must include timezone")
    material = {
        "receipt_type": "EXECUTION_TERMINATION",
        "execution_id": session["execution_id"], "session_id": session["session_id"],
        "mission_id": session["mission_id"], "result": result["result"],
        "forced": bool(result.get("forced", False)),
        "process_pid": session.get("process_pid"), "process_group_id": session.get("process_group_id"),
        "observed_at": at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return {**material, "receipt_id": "ZEUS-TERMINATION-" + digest(material)[:32], "receipt_digest": digest(material)}
