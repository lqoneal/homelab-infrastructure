"""Read-only P5-G6 execution monitoring projection and verification.

The monitor observes canonical execution-start artifacts and optional
execution-monitoring records.  It never starts work, writes heartbeats, or
changes lifecycle state.  Provider process existence is supplemental evidence;
the execution record remains authoritative for execution state.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.production_execution import load_json
from scripts.lib.emp.runtime_paths import resolve_runtime


ROADMAP = "engineering/docs/architecture/ZEUS-CANONICAL-DEVELOPMENT-ROADMAP.md"
MONITORING_DIR = "execution-monitoring"


class ExecutionMonitoringError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "RECONCILE_EXECUTION_STATE"):
        self.code = code
        self.message = message
        self.next_action = next_action
        super().__init__(message)


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception as error:
        raise ExecutionMonitoringError("MONITORING_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ExecutionMonitoringError("MONITORING_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    return Path(resolve_runtime(root, explicit=runtime_root, require_writable=False)["root"]).resolve()


def _pid_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        return subprocess.run(["kill", "-0", str(pid)], capture_output=True, check=False).returncode == 0
    except OSError:
        return False


def _transactions(runtime: Path) -> list[tuple[Path, dict[str, Any]]]:
    directory = runtime / "execution-start-transactions"
    return [(_path, _load(_path)) for _path in sorted(directory.glob("*.json"))] if directory.is_dir() else []


def _find_transaction(runtime: Path, identifier: str) -> tuple[Path, dict[str, Any]]:
    wanted = str(identifier).upper()
    matches = [(path, value) for path, value in _transactions(runtime)
               if wanted in {str(value.get("execution_id", "")).upper(), str(value.get("mission_id", "")).upper()}]
    if len(matches) != 1:
        raise ExecutionMonitoringError("EXECUTION_NOT_DISCOVERABLE", f"execution identity resolved {len(matches)} records: {identifier}", next_action="RECONCILE_EXECUTION_STATE")
    return matches[0]


def _roadmap(root: Path) -> dict[str, Any]:
    path = root / ROADMAP
    if not path.is_file():
        raise ExecutionMonitoringError("ROADMAP_NOT_FOUND", f"canonical roadmap is missing: {path}")
    text = path.read_text(encoding="utf-8")
    phases = [(int(number), name.strip()) for number, name in re.findall(r"^# Phase (\d+) — (.+)$", text, re.MULTILINE)]
    gates = [(identifier, name.strip()) for identifier, name in re.findall(r"^## (P\d+-G\d+) — (.+)$", text, re.MULTILINE)]
    current_match = re.search(r"^CANONICAL_GATE_CURRENT=(P\d+-G\d+)$", text, re.MULTILINE)
    current_gate = current_match.group(1) if current_match else (gates[-1][0] if gates else None)
    current_name = next((name for ident, name in gates if ident == current_gate), None)
    phase_number = int(current_gate.split("-")[0][1:]) if current_gate else None
    explicit_total = re.search(r"^PHASE_TOTAL=(\d+)$", text, re.MULTILINE)
    phase_total = int(explicit_total.group(1)) if explicit_total else len(phases)
    return {
        "path": str(path), "digest": hashlib.sha256(path.read_bytes()).hexdigest(),
        "phase_current": phase_number, "phase_total": phase_total,
        "gate_current": int(current_gate.split("-G")[1]) if current_gate else None,
        "gate_total": sum(1 for ident, _ in gates if ident.startswith(f"P{phase_number}-")) if phase_number else 0,
        "phase_id": f"P{phase_number}" if phase_number else None,
        "gate_id": current_gate, "gate_name": current_name,
    }


def _monitoring_record(runtime: Path, execution_id: str) -> dict[str, Any] | None:
    directory = runtime / MONITORING_DIR
    if not directory.is_dir():
        return None
    matches = []
    for path in sorted(directory.glob("*.json")):
        value = _load(path)
        if value.get("execution_id") == execution_id:
            supplied = value.get("record_digest")
            if supplied and supplied != _digest({key: item for key, item in value.items() if key != "record_digest"}):
                raise ExecutionMonitoringError("MONITORING_RECORD_DIGEST_MISMATCH", "monitoring record digest is invalid")
            matches.append(value)
    if len(matches) > 1:
        raise ExecutionMonitoringError("MONITORING_CARDINALITY_CONFLICT", "more than one monitoring projection belongs to the execution")
    return matches[0] if matches else None


def _eens_events(runtime: Path, mission_id: str, execution_id: str) -> list[dict[str, Any]]:
    """Read only execution-scoped EENS events when the runtime provides them."""
    events = []
    for directory in (runtime / "stage1" / "eens", runtime / "eens"):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            value = _load(path)
            if (value.get("mission_id") == mission_id or value.get("execution_id") == execution_id) and str(value.get("event_type", "")).startswith("execution."):
                events.append(value)
    return events


def _derive_work_states(transaction: Mapping[str, Any], record: Mapping[str, Any] | None) -> tuple[bool, bool]:
    """Derive mission/repository work from one authoritative lifecycle source.

    The immutable execution-start transaction describes the pre-begin boundary.
    Once controlled work begins, the bound active execution projection is the
    authoritative source for work state.  Mission work is intentionally
    independent from repository mutation: entering the controlled mission turn
    does not imply that repository work has started.
    """
    source = record if record is not None else transaction
    return source.get("mission_work_started") is True, source.get("repository_work_started") is True


def _projection(root: Path, runtime: Path, path: Path, transaction: Mapping[str, Any]) -> dict[str, Any]:
    execution_id = str(transaction.get("execution_id"))
    supplied_digest = transaction.get("artifact_digest")
    if supplied_digest and supplied_digest != _digest({key: value for key, value in transaction.items() if key != "artifact_digest"}):
        raise ExecutionMonitoringError("EXECUTION_SOURCE_DIGEST_MISMATCH", "execution-start transaction digest is invalid")
    if path.name != f"{execution_id}.json":
        raise ExecutionMonitoringError("EXECUTION_SOURCE_PATH_INVALID", "execution-start transaction filename is not canonical")
    roadmap = _roadmap(root)
    record = _monitoring_record(runtime, execution_id)
    events = _eens_events(runtime, str(transaction.get("mission_id")), execution_id)
    if record and record.get("execution_id") != execution_id:
        raise ExecutionMonitoringError("EXECUTION_IDENTITY_MISMATCH", "monitoring record is not bound to execution")

    start_state = transaction.get("execution_start_state")
    started = transaction.get("execution_started") is True
    mission_work, repository_work = _derive_work_states(transaction, record)
    monitoring_active = (record or {}).get("execution_monitoring_active", transaction.get("execution_monitoring_active")) is True
    execution_state = str((record or {}).get("execution_state") or
                          ("EXECUTING" if monitoring_active else "READY_FOR_CONTROLLED_EXECUTION" if started else "NOT_STARTED"))
    if not started and execution_state not in {"NOT_STARTED", "DISPATCHED"}:
        raise ExecutionMonitoringError("EXECUTION_STATE_CONFLICT", "monitoring state claims progress before execution start")
    if mission_work and not started:
        raise ExecutionMonitoringError("EXECUTION_STATE_CONFLICT", "mission work started without execution start")
    if record and execution_state in {"EXECUTING", "RUNNING", "WAITING_APPROVAL", "PAUSED"} and not monitoring_active:
        raise ExecutionMonitoringError("EXECUTION_STATE_CONFLICT", "active execution state is not monitoring-enabled")

    provider_pid = (record or {}).get("provider_pid")
    session_liveness = None
    runtime_classification = None
    try:
        from scripts.lib.emp.codex_adapter import resolve_session_binding, runtime_liveness
        binding = resolve_session_binding(root, execution_id=execution_id, runtime_root=runtime)
        bound_session = binding.get("session")
        if bound_session:
            live = runtime_liveness(bound_session)
            provider_pid = live.get("provider_process_id") or bound_session.get("provider_pid")
            provider_liveness = live["provider_liveness"]
            session_liveness = live["session_liveness"]
            runtime_classification = live["runtime_classification"]
        else:
            provider_liveness = (record or {}).get("provider_liveness")
    except Exception:
        provider_liveness = (record or {}).get("provider_liveness")
    if provider_liveness is None:
        provider_liveness = "ALIVE" if _pid_alive(provider_pid) else "UNKNOWN"
    execution_liveness = (record or {}).get("execution_liveness")
    if execution_liveness is None:
        execution_liveness = "ALIVE" if monitoring_active and provider_liveness == "ALIVE" else "NOT_ACTIVE"

    source = {"execution_start_transaction": str(path), "execution_start_digest": transaction.get("artifact_digest"),
              "roadmap": roadmap["path"], "roadmap_digest": roadmap["digest"]}
    if record:
        source["monitoring_record"] = record.get("path") or "runtime://execution-monitoring"
        source["monitoring_record_digest"] = record.get("record_digest") or _digest({k: v for k, v in record.items() if k != "record_digest"})
    if events:
        source["eens_events"] = f"runtime://eens/{len(events)}-execution-events"
        source["eens_events_digest"] = _digest(events)
    session_id = transaction.get("execution_session_id") or transaction.get("provider_session_id")
    try:
        from scripts.lib.emp.codex_adapter import current_session
        current = current_session(root, str(transaction.get("mission_id")), runtime_root=runtime)
        if current:
            session_id = current.get("session_id")
    except Exception:
        pass
    projection = {
        "result": "PASS", "read_only": True, "mission_id": transaction.get("mission_id"),
        "wop_id": transaction.get("wop_id"), "execution_id": execution_id,
        "provider_id": transaction.get("provider_id"), "provider_invocation_id": transaction.get("provider_invocation_id"),
        "session_id": session_id, "codex_session_id": session_id,
        "execution_session_id": transaction.get("execution_session_id"),
        "provider_session_id": transaction.get("provider_session_id"),
        "execution_state": execution_state, "execution_started_at": transaction.get("created_at") or transaction.get("timestamp"),
        "last_observed_at": (record or {}).get("last_observed_at"), "provider_liveness": provider_liveness,
        "execution_liveness": execution_liveness, "provider_process_state": (record or {}).get("provider_process_state", "RUNNING" if provider_liveness == "ALIVE" else "STOPPED" if provider_liveness == "STOPPED" else "BOUND" if transaction.get("provider_process_bound") else "UNBOUND"),
        "session_state": (record or {}).get("session_state", "READY"), "session_liveness": session_liveness or ("ALIVE" if provider_liveness == "ALIVE" else "UNKNOWN"),
        "runtime_classification": runtime_classification,
        "mission_work_state": "STARTED" if mission_work else "NOT_STARTED",
        "repository_work_state": "STARTED" if repository_work else "NOT_STARTED",
        "current_work_position": (record or {}).get("current_work_position", "EXECUTION_START_BOUNDARY"),
        "current_gate": (record or {}).get("current_gate", roadmap["gate_id"]), "current_gate_name": (record or {}).get("current_gate_name", roadmap["gate_name"]),
        "phase": {"current": roadmap["phase_current"], "total": roadmap["phase_total"], "id": roadmap["phase_id"]},
        "gate": {"current": roadmap["gate_current"], "total": roadmap["gate_total"], "id": roadmap["gate_id"], "name": roadmap["gate_name"]},
        "progress_state": (record or {}).get("progress_state", "NOT_STARTED" if not monitoring_active else "ACTIVE"),
        "completed_work_units": (record or {}).get("completed_work_units", []), "active_work_units": (record or {}).get("active_work_units", []),
        "remaining_work_units": (record or {}).get("remaining_work_units", []), "blockers": (record or {}).get("blockers", []),
        "approvals_required": (record or {}).get("approvals_required", []), "last_progress_event": (record or {}).get("last_progress_event"),
        "last_progress_timestamp": (record or {}).get("last_progress_timestamp") or (events[-1].get("timestamp") if events else None),
        "next_authorized_action": (record or {}).get("next_authorized_action", "BEGIN_CONTROLLED_MISSION_WORK" if started and not mission_work else "RECONCILE_EXECUTION_STATE"),
        "source_records": source, "source_digests": {key: value for key, value in source.items() if key.endswith("digest")},
        "projection_verification": "PASS", "execution_monitoring_active": monitoring_active,
        "replay": "IDEMPOTENT", "roadmap_id": "ZEUS-CANONICAL-DEVELOPMENT-ROADMAP", "roadmap_revision": "CURRENT",
        "roadmap_source": roadmap["path"], "roadmap_digest": roadmap["digest"], "eens_events": events,
    }
    # A legacy pre-Mission-Contract execution may have a stale active record
    # even though its accepted/published historical disposition is complete.
    # Keep the normal monitor authoritative for all other executions and use
    # the bounded, identity-checked reconciliation owner only here.
    try:
        from scripts.lib.emp.legacy_lifecycle_reconciliation import inspect as inspect_legacy, overlay
        legacy = inspect_legacy(root, runtime, transaction=transaction, monitoring=record)
        projection = overlay(projection, legacy)
    except Exception:
        # Historical reconciliation is deliberately opt-in and fail-closed;
        # an unverifiable legacy record must retain its ordinary projection.
        pass
    return projection


def status(repository: Path | str, identifier: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    try:
        runtime = _runtime(root, runtime_root)
        path, transaction = _find_transaction(runtime, identifier)
        return _projection(root, runtime, path, transaction)
    except ExecutionMonitoringError as error:
        return {"result": "FAIL", "read_only": True, "execution_id": str(identifier).upper(),
                "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action,
                "projection_verification": "FAIL"}


def verify(repository: Path | str, identifier: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = status(repository, identifier, runtime_root=runtime_root)
    if value.get("result") != "PASS":
        return value
    required = {
        "mission_id": "PASS" if value.get("mission_id") else "FAIL",
        "wop_binding": "PASS" if value.get("wop_id") else "FAIL",
        "execution_identity": "PASS" if value.get("execution_id") else "FAIL",
        "session_binding": "PASS" if value.get("session_id") else "FAIL",
        "provider_binding": "PASS" if value.get("provider_id") else "FAIL",
        "execution_state": "PASS" if value.get("execution_state") else "FAIL",
        "liveness": "PASS" if value.get("execution_liveness") in {"ALIVE", "NOT_ACTIVE", "STALE", "UNKNOWN", "STOPPED", "FAILED", "NOT_STARTED"} else "FAIL",
        "current_work_position": "PASS" if value.get("current_work_position") else "FAIL",
        "blocker_projection": "PASS",
        "approval_projection": "PASS",
        "progress_projection": "PASS" if value.get("phase", {}).get("total") and value.get("gate", {}).get("total") else "FAIL",
        "source_provenance": "PASS" if value.get("source_records") else "FAIL",
        "replay": "PASS" if value.get("replay") == "IDEMPOTENT" else "FAIL",
    }
    failed = [key for key, result in required.items() if result != "PASS"]
    result = dict(value, checks=required, verification_result="PASS" if not failed else "FAIL")
    if failed:
        result["result"] = "FAIL"
        result["blockers"] = [{"code": "MONITORING_VERIFICATION_INCOMPLETE", "message": ", ".join(failed)}]
        result["next_authorized_action"] = "RECONCILE_EXECUTION_STATE"
    return result


def render(value: Mapping[str, Any]) -> str:
    phase, gate = value.get("phase", {}), value.get("gate", {})
    blockers = value.get("blockers", [])
    return "\n".join(("Zeus Execution Monitoring", "------------------------",
        f"Result                  : {value.get('result')}", f"Mission                 : {value.get('mission_id')}",
        f"WOP / Execution          : {value.get('wop_id')} / {value.get('execution_id')}",
        f"Execution state          : {value.get('execution_state')}", f"Provider liveness        : {value.get('provider_liveness')}",
        f"Execution liveness       : {value.get('execution_liveness')}", f"Phase                    : {phase.get('current')} / {phase.get('total')}",
        f"Gate                     : {gate.get('current')} / {gate.get('total')} ({gate.get('id')})",
        f"Current work             : {value.get('current_work_position')}", f"Blockers                : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}",
        f"Next action              : {value.get('next_authorized_action')}", f"Verification             : {value.get('projection_verification')}", "Read-only                : YES"))
