"""Zeus-owned reconciliation of Codex session and listener projections.

The controller is intentionally small and fail-closed.  It inventories only
receipt-backed session records, validates recorded process identity before any
signal is sent, and writes reconciliation receipts through Zeus.  A dry run
never mutates runtime state; mutation requires explicit operator approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import time
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.production_execution import atomic_write, digest, load_json


RECEIPT_DIR = "codex-reconciliation-receipts"
SESSION_DIRS = ("codex-sessions", "codex-interactive-sessions")
PROCESS_FIELDS = ("pid", "provider_pid", "listener_pid", "remote_client_pid")
TERMINAL_STATES = {"STOPPED", "FAILED", "DETACHED", "INTERRUPTED"}
ACTIVE_STATES = {"ACTIVE", "ATTACHED", "ATTACHING", "READY", "RESUMED",
                 "THREAD_READY", "AWAITING_OPERATOR_INPUT", "TURN_ACTIVE",
                 "INTERACTIVE_SESSION_OPEN"}


class ReconciliationError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code, self.message, self.next_action = code, message, next_action
        super().__init__(message)


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root is None:
        from scripts.lib.emp.runtime_paths import resolve_runtime
        return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()
    runtime = Path(runtime_root).resolve()
    try:
        runtime.relative_to(root)
    except ValueError:
        return runtime
    raise ReconciliationError("RUNTIME_INSIDE_REPOSITORY", "runtime must not be inside the repository")


def process_identity(pid: Any) -> dict[str, Any]:
    """Return a stable Linux process identity without trusting pid alone."""
    if not isinstance(pid, int) or pid <= 0:
        return {"pid": pid, "alive": False, "identity": "INVALID"}
    proc = Path("/proc") / str(pid)
    try:
        stat = (proc / "stat").read_text(encoding="utf-8")
        starttime = stat.rsplit(")", 1)[1].split()[19]
        executable = os.readlink(proc / "exe")
        command = (proc / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace").strip()
    except (OSError, IndexError, ValueError):
        return {"pid": pid, "alive": False, "identity": "NOT_RUNNING"}
    material = {"pid": pid, "starttime": starttime, "executable": executable, "command": command}
    return {**material, "alive": True, "identity": hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()}


def _identity_matches(expected: Mapping[str, Any] | None, observed: Mapping[str, Any]) -> str:
    if not observed.get("alive"):
        return "NOT_RUNNING"
    if not expected:
        return "UNVERIFIED"
    keys = ("pid", "starttime", "executable", "command", "identity")
    return "PASS" if all(expected.get(key) == observed.get(key) for key in keys) else "FAIL"


def _load_record(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = load_json(path)
        supplied = value.get("state_digest")
        unsigned = {key: item for key, item in value.items() if key != "state_digest"}
        if supplied != digest(unsigned):
            return None, "DIGEST_MISMATCH"
        return value, None
    except (OSError, ValueError, json.JSONDecodeError):
        return None, "MALFORMED_RECORD"


def _record_digest(value: Mapping[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "state_digest"}
    return digest(unsigned)


def _inventory(runtime: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for directory_name in SESSION_DIRS:
        directory = runtime / directory_name
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
            value, error = _load_record(path)
            if error:
                entries.append({"path": str(path), "record_type": directory_name,
                                "disposition": "ORPHAN_CORRUPT_RECORD", "reason": error,
                                "eligible_for_mutation": False})
                continue
            assert value is not None
            processes = []
            for field in PROCESS_FIELDS:
                pid = value.get(field)
                if not isinstance(pid, int) or pid <= 0:
                    continue
                observed = process_identity(pid)
                match = _identity_matches(value.get(f"{field}_identity"), observed)
                processes.append({"field": field, "pid": pid, "observed": observed,
                                  "identity_validation": match})
            state = value.get("state")
            live = [item for item in processes if item["observed"].get("alive")]
            verified_live = [item for item in live if item["identity_validation"] == "PASS"]
            unverified_live = [item for item in live if item["identity_validation"] != "PASS"]
            if unverified_live:
                disposition, eligible, reason = "ORPHAN_IDENTITY_UNVERIFIED", False, "live process identity is not receipt-bound"
            elif state in ACTIVE_STATES and verified_live:
                disposition, eligible, reason = "RETAIN_ACTIVE", False, "active receipt-bound process"
            elif verified_live and state in TERMINAL_STATES | {None}:
                disposition, eligible, reason = "ORPHAN_LIVE_PROCESS", True, "terminal session retains a live receipt-bound process"
            elif state in ACTIVE_STATES and not live:
                disposition, eligible, reason = "ORPHAN_STALE_SESSION", False, "active receipt has no live process"
            else:
                disposition, eligible, reason = "RECONCILED", False, "no live process remains"
            entries.append({"path": str(path), "session_id": value.get("session_id"),
                            "mission_id": value.get("mission_id"), "state": state,
                            "record_type": directory_name, "record_digest": _record_digest(value),
                            "processes": processes, "disposition": disposition,
                            "reason": reason, "eligible_for_mutation": eligible})
    by_mission: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        mission = entry.get("mission_id")
        if mission:
            by_mission.setdefault(str(mission), []).append(entry)
    for mission, matches in by_mission.items():
        if len(matches) > 1:
            for entry in matches:
                entry["cardinality_conflict"] = {"mission_id": mission, "observed": len(matches), "required": 1}
                entry["disposition"] = "ORPHAN_CARDINALITY_CONFLICT"
                entry["eligible_for_mutation"] = False
                entry["reason"] = "more than one session record claims the same mission"
    return entries


def _receipt_path(runtime: Path, reconciliation_id: str) -> Path:
    return runtime / RECEIPT_DIR / f"{reconciliation_id}.json"


def _reconciliation_id(entries: list[dict[str, Any]]) -> str:
    material = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return "CODEX-RECON-" + hashlib.sha256(material.encode()).hexdigest()[:24]


def reconcile(repository: Path | str, *, runtime_root: Path | str | None = None,
              approve: bool = False, terminate: bool = True) -> dict[str, Any]:
    """Inventory or explicitly reconcile one disposable/authoritative runtime."""
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    entries = _inventory(runtime)
    reconciliation_id = _reconciliation_id(entries)
    receipt_path = _receipt_path(runtime, reconciliation_id)
    receipt_candidates = [receipt_path]
    receipt_dir = runtime / RECEIPT_DIR
    if receipt_dir.is_dir():
        # A terminated process necessarily changes the live inventory.  Match
        # a prior approved receipt by immutable record identity as well as by
        # the current inventory hash so replay remains deterministic.
        receipt_candidates.extend(sorted(receipt_dir.glob("*.json")))
    current_records = {(item.get("record_type"), item.get("session_id"), item.get("record_digest"))
                       for item in entries if item.get("record_digest")}
    for candidate in receipt_candidates:
        if not candidate.is_file():
            continue
        receipt = load_json(candidate)
        recorded = {(item.get("record_type"), item.get("session_id"), item.get("record_digest"))
                    for item in receipt.get("entries", []) if item.get("record_digest")}
        if candidate == receipt_path or (recorded and recorded == current_records and receipt.get("operator_approved")):
            return {"result": "PASS", "replayed": True, "read_only": not approve,
                    "runtime_root": str(runtime), "reconciliation": receipt}
    eligible = [entry for entry in entries if entry["eligible_for_mutation"]]
    cardinality = {}
    for entry in entries:
        conflict = entry.get("cardinality_conflict")
        if conflict:
            cardinality[conflict["mission_id"]] = conflict
    terminated: list[dict[str, Any]] = []
    if approve and terminate:
        for entry in eligible:
            for process in entry["processes"]:
                if process["identity_validation"] != "PASS" or not process["observed"].get("alive"):
                    continue
                pid = process["pid"]
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except OSError as error:
                    raise ReconciliationError("PROCESS_TERMINATION_FAILED", f"pid {pid}: {error}") from error
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and process_identity(pid).get("alive"):
                    time.sleep(0.02)
                remaining = process_identity(pid)
                terminated.append({"pid": pid, "field": process["field"],
                                   "identity": process["observed"], "remaining": remaining,
                                   "result": "PASS" if not remaining.get("alive") else "TIMEOUT"})
        if any(item["result"] != "PASS" for item in terminated):
            raise ReconciliationError("PROCESS_TERMINATION_INCOMPLETE", "one or more receipt-backed processes remain alive")
    receipt = {"schema_version": 1, "contract": "ZEUS-P5-G6-CODEX-RECONCILIATION",
               "reconciliation_id": reconciliation_id, "repository": str(root),
               "runtime_root": str(runtime), "read_only": not approve,
               "operator_approved": approve, "entries": entries,
               "cardinality": cardinality,
               "termination_receipts": terminated,
               "authoritative_runtime_updates": "ZEUS_CONTROLLER_ONLY",
               "result": "PASS", "unreconciled_orphans": len(eligible) if not approve else 0,
               "receipt_digest": None}
    receipt["receipt_digest"] = digest(receipt)
    if approve:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(receipt_path, receipt)
    return {"result": "PASS", "replayed": False, "read_only": not approve,
            "runtime_root": str(runtime), "reconciliation": receipt}


def inventory(repository: Path | str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = reconcile(repository, runtime_root=runtime_root, approve=False)
    return value
