"""Zeus-owned Codex session adapter for the P5-G6 controlled boundary.

The adapter is the only normal path from a verified execution-start record to
Codex.  It owns the session binding and process identity, while the provider
never owns mission authority.  Verification is read-only; ``start``,
``resume``, and ``stop`` are the only mutating operations.
"""

from __future__ import annotations

import json
import os
import sqlite3
import signal
import socket
import stat
import subprocess
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_identity import resolve as resolve_repository
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos import operational_beta
from scripts.lib.emp.codex_reconciliation import process_identity
from scripts.lib.emp import managed_work_contract


CONTRACT = "ZEUS-P5-G6-CODEX-ADAPTER"
VERSION = "1"
PROVIDER_ID = "zeus-local-loneal-01"
ADAPTER_ID = "zeus-codex-process-v1"
STAGE_DIR = "codex-sessions"
LOG_DIR = "codex-logs"
EVENT_DIR = "codex-events"
CODEX_HOME_DIR = "codex-home"
ACTIVE_TRANSITION_DIR = "execution-active-transitions"
MONITORING_DIR = "execution-monitoring"
HISTORY_RECONCILIATION_RECEIPT_DIR = "codex-history-reconciliation-receipts"
ACTIVE_STATES = {"ACTIVE", "RESUMED"}
STOPPED_STATES = {"INTERRUPTED", "STOPPED", "FAILED"}


class CodexAdapterError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED",
                 details: Mapping[str, Any] | None = None, lifecycle_next_action: str | None = None,
                 recovery_action: str | None = None):
        self.code, self.message, self.next_action = code, message, next_action
        self.details = dict(details or {})
        self.lifecycle_next_action = lifecycle_next_action
        self.recovery_action = recovery_action or next_action
        super().__init__(message)


def _execution_verification_error(execution: Mapping[str, Any]) -> CodexAdapterError:
    blockers = execution.get("blockers") or []
    blocker = blockers[0] if blockers and isinstance(blockers[0], Mapping) else {}
    return CodexAdapterError(
        str(blocker.get("code") or "EXECUTION_START_FAILURE"),
        str(blocker.get("message") or "execution-start verification failed"),
        next_action=str(execution.get("next_authorized_action") or "STOP_FAIL_CLOSED"),
    )


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root:
        return Path(runtime_root).resolve()
    return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()


def _session_path(runtime: Path, session_id: str) -> Path:
    path = (runtime / STAGE_DIR / f"{session_id}.json").resolve()
    try:
        path.relative_to((runtime / STAGE_DIR).resolve())
    except ValueError as error:
        raise CodexAdapterError("SESSION_PATH_ESCAPE", "Codex session path escapes runtime") from error
    return path


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception as error:
        raise CodexAdapterError("SESSION_ARTIFACT_INVALID", f"{path}: {error}") from error
    supplied = value.get("state_digest")
    unsigned = {key: item for key, item in value.items() if key != "state_digest"}
    if supplied != digest(unsigned):
        raise CodexAdapterError("SESSION_DIGEST_MISMATCH", f"{path} digest mismatch")
    return value


def _save(runtime: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("state_digest", None)
    unsigned["state_digest"] = digest(unsigned)
    atomic_write(_session_path(runtime, str(unsigned["session_id"])), unsigned)
    return unsigned


def _append_event(runtime: Path, session_id: str, event: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    directory = runtime / EVENT_DIR / session_id
    directory.mkdir(parents=True, exist_ok=True)
    # Readiness/exit marker JSON files share this directory but are not journal
    # events.  Counting them created sequence gaps and broke the event chain.
    existing = sorted(directory.glob("[0-9][0-9][0-9][0-9].json"))
    sequence = len(existing) + 1
    material = {"schema_version": 1, "sequence": sequence, "session_id": session_id,
                "event": event, "payload": dict(payload),
                "previous_event_digest": None}
    if existing:
        previous = load_json(existing[-1])
        material["previous_event_digest"] = previous.get("event_digest")
    material["event_digest"] = digest(material)
    path = directory / f"{sequence:04d}.json"
    if path.exists():
        current = load_json(path)
        if current != material:
            raise CodexAdapterError("EVENT_CONFLICT", f"event {path} conflicts with immutable state")
    else:
        atomic_write(path, material)
    return material


def _authority(root: Path) -> dict[str, Any]:
    value = operational_beta.authority(root, include_current_execution=False)
    required = {"authority_framework": "OPERATION_BETA", "authority_integrity": "PASS",
                "authority_resolution": "PASS", "authority_digest_validation": "PASS",
                "oa_authority": "SUPERSEDED"}
    if any(value.get(key) != expected for key, expected in required.items()):
        raise CodexAdapterError("AUTHORITY_FAILURE", "published Operation Beta authority chain failed")
    return {"framework": "OPERATION_BETA", "source": "published Operation Beta authority chain",
            "digest": value.get("authority_digest"), "integrity": "PASS", "oa_authority": "SUPERSEDED"}


def _package(root: Path, mission_id: str, runtime: Path) -> dict[str, Any]:
    from scripts.lib.emp.execution_start import verify as verify_execution_start
    execution = verify_execution_start(root, mission_id, runtime_root=runtime)
    if execution.get("result") != "PASS":
        raise _execution_verification_error(execution)
    if execution.get("mission_id") != mission_id:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution-start mission binding differs from requested mission")
    if not execution.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISSING", "execution-start has no bound WOP")
    if not execution.get("execution_session_id") or not execution.get("provider_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISSING", "execution-start session bindings are incomplete")
    if not execution.get("provider_id") or not execution.get("provider_invocation_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISSING", "execution-start provider bindings are incomplete")
    if execution.get("blockers") or execution.get("approvals_required"):
        raise CodexAdapterError("EXECUTION_BLOCKED", "execution has an active blocker or outstanding approval")
    if execution.get("execution_start_state") != "READY_FOR_CONTROLLED_EXECUTION":
        raise CodexAdapterError("EXECUTION_STATE_INVALID", "execution is not at READY_FOR_CONTROLLED_EXECUTION")
    if execution.get("next_authorized_action") != "BEGIN_CONTROLLED_MISSION_WORK":
        raise CodexAdapterError("EXECUTION_NOT_READY", "execution is not at the controlled mission-work boundary")
    if execution.get("mission_work_started"):
        raise CodexAdapterError("MISSION_WORK_ALREADY_STARTED", "mission work is already active")
    authority = _authority(root)
    identity = resolve_repository(root)
    execution_id = execution["execution_id"]
    package = {
        "schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
        "mission_id": mission_id, "wop_id": execution.get("wop_id"), "execution_id": execution_id,
        "execution_session_id": execution["execution_session_id"],
        "provider_id": execution["provider_id"], "provider_invocation_id": execution["provider_invocation_id"],
        "provider_session_id": execution.get("provider_session_id"),
        "repository": str(root), "repository_identity": identity["repository_identity"],
        "repository_id": identity["repository_id"], "repository_fingerprint": identity["repository_fingerprint"],
        "current_published_baseline": execution["current_published_baseline"],
        "execution_start_provenance_baseline": execution.get("execution_start_provenance_baseline"),
        "execution_start_baseline_relationship": execution.get("execution_start_baseline_relationship"),
        "execution_package_digest": None, "execution_authority_digest": None,
        "scope": {"owner": "Zeus", "mission_work_started": False,
                  "repository_work_started": False, "operator_approval_required": False,
                  "stop_boundary": "FIRST_CONTROLLED_EXECUTION_BOUNDARY",
                  "sandbox": "workspace-write"},
        "work_authority": {"source": "operator-submitted WOP",
                            "wop_id": execution.get("wop_id"),
                            "admission_id": execution.get("admission_id")},
        "authority": authority,
    }
    start_transaction = runtime / "execution-start-transactions" / f"{execution_id}.json"
    if start_transaction.is_file():
        transaction = load_json(start_transaction)
        package["execution_package_digest"] = transaction.get("execution_package_digest")
        package["execution_authority_digest"] = transaction.get("execution_authority_digest")
    package["package_digest"] = digest(package)
    return package


def _existing(runtime: Path, mission_id: str) -> dict[str, Any] | None:
    matches = []
    directory = runtime / STAGE_DIR
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
        value = _load(path)
        if value.get("mission_id") == mission_id:
            matches.append(value)
    current = [value for value in matches if value.get("session_disposition") != "SUPERSEDED"
               and value.get("state") != "SUPERSEDED"]
    if len(current) > 1:
        raise CodexAdapterError("SESSION_CARDINALITY_CONFLICT", "more than one current Codex session belongs to the mission")
    if current:
        return current[0]
    return None


def _all_sessions(runtime: Path, mission_id: str | None = None) -> list[dict[str, Any]]:
    directory = runtime / STAGE_DIR
    values = [_load(path) for path in sorted(directory.glob("*.json"))] if directory.is_dir() else []
    return [value for value in values if mission_id is None or value.get("mission_id") == mission_id]


def _history_reconciliation_receipt_path(runtime: Path, reconciliation_digest: str) -> Path:
    return runtime / HISTORY_RECONCILIATION_RECEIPT_DIR / f"CODEX-HISTORY-RECONCILIATION-{reconciliation_digest[:32]}.json"


def _history_reconciliation_receipt_material(session: Mapping[str, Any], reconciliation: Mapping[str, Any],
                                             *, decision: str, operator_action: bool) -> dict[str, Any]:
    """Build the identity-bound history decision without generic gate semantics."""
    history_digest = digest(dict(reconciliation))
    return {
        "schema_version": 1,
        "record_type": "CODEX_HISTORY_RECONCILIATION_DECISION",
        "decision": decision,
        "operator_action": operator_action,
        "mission_id": session.get("mission_id"),
        "wop_id": session.get("wop_id"),
        "execution_id": session.get("execution_id"),
        "execution_session_id": session.get("execution_session_id"),
        "provider_session_id": session.get("provider_session_id"),
        "provider_id": session.get("provider_id"),
        "codex_session_id": session.get("session_id"),
        "history_disposition": reconciliation.get("history_disposition"),
        "history_digest": history_digest,
        "mission_work_actually_occurred": reconciliation.get("mission_work_actually_occurred"),
        "repository_work_actually_occurred": reconciliation.get("repository_work_actually_occurred"),
        "history_safe_for_thread_recovery": reconciliation.get("history_safe_for_thread_recovery"),
        "reconciliation_required": reconciliation.get("reconciliation_required"),
    }


def _persist_history_reconciliation_receipt(runtime: Path, material: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(material)
    unsigned.pop("receipt_digest", None)
    value = {**unsigned, "receipt_digest": digest(unsigned)}
    path = _history_reconciliation_receipt_path(runtime, str(value["history_digest"]))
    if path.is_file():
        existing = load_json(path)
        if existing != value:
            raise CodexAdapterError("RECONCILIATION_DECISION_CONFLICT",
                                    "history reconciliation decision conflicts with the canonical receipt")
        return {**existing, "receipt_path": str(path), "replay": "IDEMPOTENT"}
    atomic_write(path, value)
    return {**value, "receipt_path": str(path), "replay": "APPLIED"}


def _load_history_reconciliation_decision(runtime: Path, session: Mapping[str, Any],
                                          reconciliation: Mapping[str, Any]) -> dict[str, Any] | None:
    path = _history_reconciliation_receipt_path(runtime, digest(dict(reconciliation)))
    if not path.is_file():
        return None
    value = load_json(path)
    supplied = value.get("receipt_digest")
    unsigned = {key: item for key, item in value.items() if key != "receipt_digest"}
    if supplied != digest(unsigned):
        raise CodexAdapterError("RECONCILIATION_DECISION_DIGEST_MISMATCH",
                                "history reconciliation decision receipt digest mismatch")
    expected = _history_reconciliation_receipt_material(session, reconciliation,
                                                        decision=value.get("decision", ""),
                                                        operator_action=value.get("operator_action", False))
    if any(value.get(field) != expected.get(field) for field in expected):
        raise CodexAdapterError("RECONCILIATION_DECISION_BINDING_MISMATCH",
                                "history reconciliation decision is not bound to the current identities/evidence")
    return value


def _reconciliation_acceptance(runtime: Path, session: Mapping[str, Any],
                               reconciliation: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve automatic no-work proof or an explicit non-authoritative decision."""
    if reconciliation.get("history_disposition") == "NO_WORK_EVENTS":
        verified_no_work = (
            reconciliation.get("reconciliation_required") is False
            and reconciliation.get("history_safe_for_thread_recovery") is True
            and reconciliation.get("mission_work_actually_occurred") == "NO"
            and reconciliation.get("repository_work_actually_occurred") == "NO"
            and not (reconciliation.get("reconciled_projection") or {}).get("mission_work_started")
            and not (reconciliation.get("reconciled_projection") or {}).get("repository_work_started")
        )
        if verified_no_work:
            return _history_reconciliation_receipt_material(
                session, reconciliation, decision="AUTOMATICALLY_SATISFIED_NO_WORK_EVENTS", operator_action=False
            )
    if reconciliation.get("history_disposition") != "EVENTS_NON_AUTHORITATIVE":
        raise CodexAdapterError("RECONCILIATION_NOT_ACCEPTED",
                                "accepted non-authoritative reconciliation is required")
    decision = _load_history_reconciliation_decision(runtime, session, reconciliation)
    if decision is None:
        raise CodexAdapterError("RECONCILIATION_NOT_ACCEPTED",
                                "accepted non-authoritative reconciliation is required")
    if decision.get("decision") != "ACCEPTED":
        raise CodexAdapterError("RECONCILIATION_REJECTED",
                                "history reconciliation was explicitly rejected")
    return decision


def accept_reconciliation(repository: Path | str, mission_id: str, session_id: str, *,
                          runtime_root: Path | str | None = None, decision: str = "ACCEPTED") -> dict[str, Any]:
    """Record an explicit decision for a non-authoritative Codex history."""
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    mission = str(mission_id).upper()
    matches = [value for value in _all_sessions(runtime, mission) if value.get("session_id") == session_id]
    if len(matches) != 1:
        raise CodexAdapterError("OLD_SESSION_NOT_FOUND", "the requested Codex session is not uniquely discoverable")
    session = matches[0]
    reconciliation = reconcile_session_history(root, mission, runtime_root=runtime, session=session)
    if reconciliation.get("mission_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_MISSION_WORK", "prior mission work prevents reconciliation acceptance")
    if reconciliation.get("repository_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_REPOSITORY_WORK", "prior repository work prevents reconciliation acceptance")
    if reconciliation.get("history_disposition") != "EVENTS_NON_AUTHORITATIVE" or not reconciliation.get(
            "history_safe_for_thread_recovery"):
        raise CodexAdapterError("RECONCILIATION_DECISION_INVALID",
                                "explicit acceptance applies only to safe non-authoritative histories")
    if decision not in {"ACCEPTED", "REJECTED"}:
        raise CodexAdapterError("RECONCILIATION_DECISION_INVALID", "decision must be ACCEPTED or REJECTED")
    material = _history_reconciliation_receipt_material(
        session, reconciliation, decision=decision, operator_action=True
    )
    receipt = _persist_history_reconciliation_receipt(runtime, material)
    return {"result": "PASS", "mission_id": mission, "session_id": session_id,
            "decision": decision, "history_disposition": reconciliation.get("history_disposition"),
            "history_digest": material["history_digest"], "receipt": receipt,
            "read_only": False}


def _execution_records(runtime: Path) -> list[dict[str, Any]]:
    directory = runtime / "execution-start-transactions"
    records = [load_json(path) for path in sorted(directory.glob("*.json"))] if directory.is_dir() else []
    monitoring_directory = runtime / MONITORING_DIR
    merged = []
    for record in records:
        monitoring_path = monitoring_directory / f"{record.get('execution_id')}.json"
        if monitoring_path.is_file():
            monitoring = load_json(monitoring_path)
            if monitoring.get("execution_id") != record.get("execution_id"):
                raise CodexAdapterError("EXECUTION_BINDING_MISMATCH", "monitoring record differs from execution identity")
            record = {**record, **{key: value for key, value in monitoring.items()
                                   if key not in {"mission_id", "execution_id", "execution_session_id",
                                                  "provider_session_id", "provider_id"}}}
        merged.append(record)
    return merged


def _session_execution_binding(session: Mapping[str, Any], executions: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Return the exact execution record owning a managed session."""
    matches = [execution for execution in executions
               if all(session.get(field) == execution.get(field) for field in (
                   "mission_id", "execution_id", "execution_session_id", "provider_session_id", "provider_id"))]
    if len(matches) > 1:
        raise CodexAdapterError("EXECUTION_BINDING_AMBIGUOUS", "managed session has multiple exact execution bindings")
    return dict(matches[0]) if matches else None


def _historical_session(session: Mapping[str, Any], live: Mapping[str, Any]) -> bool:
    """Classify history from lifecycle evidence, never from age or file order."""
    if session.get("session_disposition") == "SUPERSEDED" or session.get("state") == "SUPERSEDED":
        return True
    if session.get("state") == "RECONCILED_HISTORICAL":
        return True
    return bool(session.get("mission_work_started")) and not live.get("session_live")


def resolve_managed_runtime(repository: Path | str, *, mission_id: str | None = None,
                            selector: str = "latest", runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Resolve managed runtime identity using lifecycle authority precedence.

    Mission-qualified bindings are considered first.  Within that scope an
    exact live execution/provider/session binding outranks every historical
    record.  Timestamps and filesystem order are only a final deterministic
    tie-breaker among records already in the same authority class.
    """
    if selector not in {"active", "latest"}:
        raise CodexAdapterError("RUNTIME_SELECTOR_INVALID", "managed runtime selector must be active or latest")
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    wanted = str(mission_id).upper() if mission_id else None
    executions = _execution_records(runtime)
    candidates = []
    for session in _all_sessions(runtime, wanted):
        if session.get("session_disposition") == "SUPERSEDED" or session.get("state") == "SUPERSEDED":
            continue
        execution = _session_execution_binding(session, executions)
        live = runtime_liveness(session)
        authoritative = execution is not None and all(
            session.get(field) == execution.get(field)
            for field in ("mission_id", "execution_id", "execution_session_id", "provider_session_id", "provider_id")
        )
        historical = _historical_session(session, live)
        recorded_live = (execution or {}).get("provider_liveness") == "ALIVE" or (execution or {}).get("execution_liveness") == "ALIVE"
        live_state = bool(live.get("runtime_process_present") or live.get("provider_process_present") or recorded_live)
        candidates.append({"session": session, "execution": execution, "liveness": live,
                           "authoritative": authoritative, "historical": historical,
                           "live_state": live_state})
    live_candidates = [item for item in candidates if item["live_state"] and not item["historical"]]
    live_authoritative = [item for item in live_candidates if item["authoritative"]]
    if selector == "active":
        selected = live_authoritative or live_candidates
        if not selected:
            return {"result": "PASS", "selector": selector, "mission_id": wanted,
                    "resolution": "NO_LIVE_MANAGED_RUNTIME", "session": None, "candidates": len(candidates),
                    "read_only": True}
    else:
        selected = live_authoritative or live_candidates or [item for item in candidates if item["authoritative"] and not item["historical"]] or candidates
        if not selected:
            return {"result": "PASS", "selector": selector, "mission_id": wanted,
                    "resolution": "NO_MANAGED_RUNTIME", "session": None, "candidates": 0,
                    "read_only": True}
    # Stable authority-first order.  No timestamp can promote historical
    # state above live execution/provider/session state.
    def rank(item: Mapping[str, Any]) -> tuple[Any, ...]:
        execution = item.get("execution") or {}
        session = item["session"]
        return (
            int(item["authoritative"]), int(item["live_state"]), int(not item["historical"]),
            int(execution.get("execution_monitoring_active") is True),
            int(execution.get("execution_started") is True),
            str(session.get("updated_at") or session.get("start_timestamp") or ""),
            str(session.get("session_id") or ""),
        )
    selected = sorted(selected, key=rank, reverse=True)
    if len(selected) > 1 and rank(selected[0]) == rank(selected[1]):
        raise CodexAdapterError("MANAGED_RUNTIME_AMBIGUOUS", "multiple managed runtimes have equal canonical authority")
    chosen = selected[0]
    return {"result": "PASS", "selector": selector, "mission_id": wanted or chosen["session"].get("mission_id"),
            "resolution": "MISSION_QUALIFIED_LIVE" if wanted and chosen["live_state"] and not chosen["historical"]
            else "LIVE_MANAGED_RUNTIME" if chosen["live_state"] and not chosen["historical"]
            else "HISTORICAL_FALLBACK", "session": chosen["session"], "execution": chosen["execution"],
            "liveness": chosen["liveness"], "authoritative": chosen["authoritative"],
            "historical": chosen["historical"], "candidates": len(candidates), "read_only": True}


def status_selector(repository: Path | str, *, selector: str, mission_id: str | None = None,
                    runtime_root: Path | str | None = None) -> dict[str, Any]:
    resolved = resolve_managed_runtime(repository, mission_id=mission_id, selector=selector, runtime_root=runtime_root)
    session = resolved.get("session")
    if not session:
        return {"result": "PASS", "mission_id": resolved.get("mission_id"), "state": "NOT_STARTED",
                "managed": True, "selector": selector, "runtime_resolution": resolved.get("resolution"),
                "candidates": resolved.get("candidates", 0), "read_only": True,
                "blockers": [], "next_authorized_action": "START_CODEX_SESSION"}
    value = status(repository, str(session["mission_id"]), runtime_root=runtime_root)
    value.update({"selector": selector, "runtime_resolution": resolved["resolution"],
                  "runtime_resolution_policy": "MISSION_QUALIFIED_LIVE>LIVE_EXECUTION_PROVIDER_SESSION>HISTORICAL_RECONCILED",
                  "resolved_runtime_session_id": session.get("session_id"),
                  "resolved_execution_id": session.get("execution_id"),
                  "resolved_execution_session_id": session.get("execution_session_id"),
                  "resolved_provider_session_id": session.get("provider_session_id"),
                  "resolved_provider_id": session.get("provider_id"),
                  "runtime_candidate_count": resolved.get("candidates", 0)})
    return value


def current_session(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any] | None:
    """Resolve the one current managed session while retaining superseded history."""
    return _existing(_runtime(Path(repository).resolve(), runtime_root), str(mission_id).upper())


def resolve_session_binding(repository: Path | str, *, mission_id: str | None = None,
                            execution_id: str | None = None,
                            runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Resolve the execution, provider, and Codex session namespaces together.

    ``session_id`` historically meant the Codex-managed session in monitoring,
    while execution-start artifacts use ``execution_session_id``.  Keep those
    identities explicit and require one matching managed session rather than
    guessing from a display projection.
    """
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    wanted_mission = str(mission_id).upper() if mission_id else None
    wanted_execution = str(execution_id).upper() if execution_id else None
    transactions = []
    directory = runtime / "execution-start-transactions"
    if directory.is_dir():
        transactions = [load_json(path) for path in sorted(directory.glob("*.json"))]
    matches = [value for value in transactions
               if (wanted_execution and str(value.get("execution_id", "")).upper() == wanted_execution)
               or (wanted_mission and str(value.get("mission_id", "")).upper() == wanted_mission)]
    if len(matches) != 1:
        raise CodexAdapterError("EXECUTION_BINDING_AMBIGUOUS", "execution binding is not uniquely discoverable")
    execution = matches[0]
    if wanted_mission and str(execution.get("mission_id", "")).upper() != wanted_mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution binding differs from requested mission")
    if wanted_execution and str(execution.get("execution_id", "")).upper() != wanted_execution:
        raise CodexAdapterError("EXECUTION_BINDING_MISMATCH", "execution binding differs from requested execution")
    sessions = _all_sessions(runtime, execution.get("mission_id"))
    candidates = [value for value in sessions
                  if value.get("execution_id") == execution.get("execution_id")
                  and value.get("execution_session_id") == execution.get("execution_session_id")
                  and value.get("provider_session_id") == execution.get("provider_session_id")
                  and value.get("provider_id") == execution.get("provider_id")]
    if len(candidates) > 1:
        raise CodexAdapterError("CODEX_SESSION_BINDING_AMBIGUOUS", "multiple Codex sessions share the execution binding")
    session = candidates[0] if candidates else None
    return {
        "result": "PASS", "mission_id": execution.get("mission_id"),
        "wop_id": execution.get("wop_id"), "execution_id": execution.get("execution_id"),
        "execution_session_id": execution.get("execution_session_id"),
        "provider_session_id": execution.get("provider_session_id"),
        "provider_id": execution.get("provider_id"),
        "codex_session_id": session.get("session_id") if session else None,
        "session_id": session.get("session_id") if session else None,
        "session_state": session.get("state") if session else None,
        "session_disposition": session.get("session_disposition") if session else None,
        "session_event_directory": session.get("event_directory") if session else None,
        "session": session, "execution": execution,
        "mapping_cardinality": "ONE" if session else "EXECUTION_ONLY",
        "read_only": True,
    }


def runtime_liveness(session: Mapping[str, Any]) -> dict[str, Any]:
    """Project process, provider, and managed-session liveness together.

    A recorded PID is only a locator.  ``process_identity`` verifies that the
    PID currently exists and is not a zombie; it is not treated as evidence
    that mission work is active.  This projection is shared by status,
    monitoring, and supersession safety checks.
    """
    process = process_identity(session.get("pid"))
    provider_pid = _marker_provider_pid(session) or session.get("provider_pid")
    provider = process_identity(provider_pid)
    process_present = bool(process.get("alive"))
    provider_present = bool(provider.get("alive"))
    any_present = process_present or provider_present
    session_live = process_present and provider_present
    return {
        "session_record_state": session.get("state"),
        "runtime_process_state": process.get("process_state") if process_present else "STOPPED",
        "runtime_process_present": process_present,
        "runtime_process_id": session.get("pid") if process_present else None,
        "runtime_process_identity": process,
        "runtime_process_owns_codex_session": ("YES" if process_present else "NO"),
        "provider_process_present": provider_present,
        "provider_process_id": provider_pid if provider_present else None,
        "provider_process_identity": provider,
        "provider_liveness": "ALIVE" if provider_present else "STOPPED" if provider_pid else "UNKNOWN",
        "mission_work_active": bool(session.get("mission_work_started")) and session_live,
        "repository_work_active": bool(session.get("repository_work_started")) and session_live,
        "session_live": session_live,
        "session_liveness": "ALIVE" if session_live else "PARTIAL" if any_present else "STOPPED",
        "runtime_classification": ("TRANSPORT_LIVE_IDLE" if any_present and not session.get("mission_work_started")
                                    else "TRANSPORT_LIVE_ACTIVE_WORK" if session_live and session.get("mission_work_started")
                                    else "TRANSPORT_STOPPED"),
    }


def _thread_from_response(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Extract the native Codex thread contract from one JSON-RPC payload."""
    if not isinstance(value, Mapping):
        return None
    result = value.get("result") if isinstance(value.get("result"), Mapping) else value
    thread = result.get("thread") if isinstance(result, Mapping) else None
    if not isinstance(thread, Mapping) or not thread.get("id"):
        return None
    return {
        "native_thread_id": thread.get("id"),
        "native_session_id": thread.get("sessionId"),
        "native_thread_path": thread.get("path"),
        "native_thread_cwd": thread.get("cwd"),
        "native_thread_ephemeral": bool(thread.get("ephemeral", False)),
        "native_thread_history_mode": thread.get("historyMode"),
        "native_thread_forked_from_id": thread.get("forkedFromId"),
        "native_thread_status": thread.get("status"),
    }


def _native_thread_candidate(session: Mapping[str, Any]) -> dict[str, Any]:
    """Discover, but never persist, the native thread bound to a Zeus wrapper.

    Current records carry the identity directly.  Older interrupted records can
    be recovered from their pending transaction or provider log.  A log entry
    is identity evidence only; persistence is established separately.
    """
    candidates: list[dict[str, Any]] = []
    if session.get("native_thread_id"):
        value = {key: session.get(key) for key in (
            "native_thread_id", "native_session_id", "native_thread_path",
            "native_thread_cwd", "native_thread_ephemeral",
            "native_thread_history_mode", "native_thread_forked_from_id",
            "native_thread_status",
        )}
        return {**value, "native_thread_identity_state": "ESTABLISHED",
                "native_thread_identity_source": "ZEUS_SESSION_RECORD",
                "native_thread_identity_sources": ["ZEUS_SESSION_RECORD"]}
    pending = session.get("pending_controlled_work")
    if isinstance(pending, Mapping):
        thread = _thread_from_response(pending.get("thread_response"))
        if thread is None and pending.get("thread_id"):
            thread = {"native_thread_id": pending.get("thread_id")}
        if thread:
            return {**thread, "native_thread_identity_state": "ESTABLISHED",
                    "native_thread_identity_source": "PENDING_CONTROLLED_WORK",
                    "native_thread_identity_sources": ["PENDING_CONTROLLED_WORK"]}
    log_path = Path(str(session.get("log_path") or ""))
    if log_path.is_file():
        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    thread = _thread_from_response(payload)
                    if thread:
                        candidates.append({**thread, "native_thread_identity_source": "APP_SERVER_LOG"})
        except OSError:
            pass
    identities = sorted({str(item.get("native_thread_id")) for item in candidates
                         if item.get("native_thread_id")})
    if not identities:
        return {"native_thread_identity_state": "NOT_CREATED", "native_thread_identity_source": None}
    if len(identities) != 1:
        return {"native_thread_identity_state": "AMBIGUOUS", "native_thread_candidates": identities,
                "native_thread_identity_source": "CONFLICTING_EVIDENCE"}
    thread_id = identities[0]
    matching = [item for item in candidates if str(item.get("native_thread_id")) == thread_id]
    merged: dict[str, Any] = {"native_thread_identity_state": "ESTABLISHED",
                              "native_thread_id": thread_id}
    for item in matching:
        for key, value in item.items():
            if value is not None and key not in merged:
                merged[key] = value
    merged["native_thread_identity_sources"] = sorted({str(item.get("native_thread_identity_source"))
                                                         for item in matching})
    return merged


def _contains_identity(value: Any, identity: str) -> bool:
    if value == identity:
        return True
    if isinstance(value, Mapping):
        return any(_contains_identity(item, identity) for item in value.values())
    if isinstance(value, list):
        return any(_contains_identity(item, identity) for item in value)
    return False


def _native_thread_persistence(runtime: Path, session: Mapping[str, Any],
                               candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate native rollout persistence without starting an app-server."""
    identity = dict(candidate or _native_thread_candidate(session))
    state = identity.get("native_thread_identity_state")
    if state != "ESTABLISHED":
        return {**identity, "thread_persisted": False, "thread_readable": False,
                "thread_persistence_state": state, "thread_resume_eligible": False}
    thread_id = str(identity["native_thread_id"])
    codex_home = Path(str((session.get("startup_diagnostics") or {}).get("codex_home")
                          or runtime / CODEX_HOME_DIR / str(session.get("session_id")))).resolve()
    raw_path = identity.get("native_thread_path")
    paths: list[Path] = []
    if raw_path:
        paths.append(Path(str(raw_path)).resolve())
    if codex_home.is_dir():
        for directory in (codex_home / "sessions", codex_home / "archived_sessions"):
            if directory.is_dir():
                paths.extend(path.resolve() for path in directory.rglob(f"*{thread_id}*.jsonl"))
    unique_paths = sorted({path for path in paths}, key=str)
    if len(unique_paths) > 1:
        return {**identity, "codex_home": str(codex_home), "thread_persisted": False,
                "thread_readable": False, "thread_persistence_state": "AMBIGUOUS",
                "thread_persistence_candidates": [str(path) for path in unique_paths],
                "thread_resume_eligible": False}
    path = unique_paths[0] if unique_paths else None
    if path is not None:
        try:
            path.relative_to(codex_home)
        except ValueError:
            return {**identity, "codex_home": str(codex_home), "thread_persisted": False,
                    "thread_readable": False, "thread_persistence_state": "PATH_ESCAPE",
                    "thread_resume_eligible": False}
    readable = False
    identity_present = False
    if path is not None and path.is_file():
        try:
            with path.open("r", encoding="utf-8") as stream:
                for index, line in enumerate(stream):
                    if index >= 32:
                        break
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    readable = True
                    if _contains_identity(payload, thread_id):
                        identity_present = True
                        break
        except (OSError, UnicodeError, json.JSONDecodeError):
            readable = False
    index_match = False
    index_paths: list[str] = []
    for database in sorted(codex_home.glob("state_*.sqlite")) if codex_home.is_dir() else ():
        try:
            connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
            try:
                row = connection.execute("SELECT rollout_path, cwd FROM threads WHERE id = ?", (thread_id,)).fetchone()
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            continue
        if row:
            index_match = True
            if row[0]:
                index_paths.append(str(row[0]))
    persisted = bool(path and path.is_file() and readable and identity_present)
    persistence_state = "VALID" if persisted else "MISSING" if path is None or not path.is_file() else "INVALID"
    return {**identity, "codex_home": str(codex_home),
            "native_thread_path": str(path) if path else raw_path,
            "thread_persisted": persisted, "thread_readable": readable,
            "thread_identity_verified_in_rollout": identity_present,
            "thread_indexed": index_match, "thread_index_paths": sorted(set(index_paths)),
            "thread_persistence_state": persistence_state,
            "thread_resume_eligible": persisted and not bool(identity.get("native_thread_ephemeral"))}


def thread_lifecycle(repository: Path | str, session: Mapping[str, Any], *,
                     runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Project transport and persisted-thread state as independent axes."""
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    transport = runtime_liveness(session)
    thread = _native_thread_persistence(runtime, session)
    thread_id = thread.get("native_thread_id")
    ownership_conflicts = []
    if thread_id:
        for other in _all_sessions(runtime):
            if other.get("session_id") == session.get("session_id"):
                continue
            other_thread = _native_thread_candidate(other)
            if other_thread.get("native_thread_id") == thread_id:
                other_liveness = runtime_liveness(other)
                if other_liveness.get("runtime_process_present") or other_liveness.get("provider_process_present"):
                    ownership_conflicts.append(str(other.get("session_id")))
    transport_alive = bool(transport.get("session_live"))
    partial_transport_owner = bool(
        transport.get("runtime_process_present") or transport.get("provider_process_present")) and not transport_alive
    valid_thread = bool(thread.get("thread_resume_eligible"))
    fork_required = bool(session.get("thread_fork_required"))
    if ownership_conflicts:
        classification = "THREAD_RECOVERY_BLOCKED"
        action = "RESOLVE_CODEX_THREAD_OWNERSHIP_CONFLICT"
    elif partial_transport_owner:
        classification = "THREAD_RECOVERY_BLOCKED"
        action = "RESOLVE_CODEX_TRANSPORT_OWNERSHIP"
    elif valid_thread and fork_required:
        classification = "THREAD_FORK_REQUIRED"
        action = "RESTART_CODEX_TRANSPORT_AND_FORK_THREAD" if not transport_alive else "FORK_CODEX_THREAD"
    elif valid_thread and transport_alive:
        classification = "ACTIVE_OR_ATTACHABLE"
        action = "ATTACH_OR_CONTINUE"
    elif valid_thread:
        classification = "TRANSPORT_STOPPED_THREAD_RESUMABLE"
        action = "RESTART_CODEX_TRANSPORT_AND_RESUME_THREAD"
    elif thread.get("native_thread_identity_state") == "NOT_CREATED":
        classification = "TRANSPORT_READY_THREAD_NOT_CREATED" if transport_alive else "TRANSPORT_STOPPED_THREAD_NOT_CREATED"
        action = "BEGIN_CONTROLLED_MISSION_WORK" if transport_alive else "RESTART_CODEX_TRANSPORT"
    else:
        classification = "THREAD_RECOVERY_BLOCKED"
        action = "RECONCILE_CODEX_THREAD_RECOVERY"
    return {
        **thread,
        "transport_liveness": "ALIVE" if transport_alive else transport.get("session_liveness", "STOPPED"),
        "transport_process_identity": transport.get("runtime_process_identity"),
        "provider_transport_identity": transport.get("provider_process_identity"),
        "transport_replacement_required": not transport_alive,
        "transport_replacement_safe": not ownership_conflicts and not partial_transport_owner,
        "transport_ownership_ambiguous": partial_transport_owner,
        "thread_identity": thread_id,
        "thread_resume_supported": session.get("provider_mode", "APP_SERVER_MANAGED") == "APP_SERVER_MANAGED",
        "thread_fork_supported": session.get("provider_mode", "APP_SERVER_MANAGED") == "APP_SERVER_MANAGED",
        "thread_fork_required": fork_required,
        "thread_replacement_required": thread.get("native_thread_identity_state") != "NOT_CREATED" and not valid_thread,
        "thread_ownership_conflicts": ownership_conflicts,
        "runtime_classification": classification,
        "runtime_recovery_action": action,
    }


def _liveness_fingerprint(session: Mapping[str, Any], projection: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return stable facts for mutation-time liveness comparison.

    Observation timestamps and derived presentation fields are intentionally
    excluded.  Process identity digests prevent a reused PID from comparing
    equal to the original process when the runtime records contain identity
    evidence.
    """
    process = projection.get("runtime_process_identity") or {}
    provider = projection.get("provider_process_identity") or {}
    return (
        session.get("session_id"),
        bool(projection.get("runtime_process_present")),
        bool(projection.get("provider_process_present")),
        process.get("process_identity_digest"),
        provider.get("process_identity_digest"),
        projection.get("runtime_classification"),
    )


def _provider_liveness_snapshot(sessions: list[Mapping[str, Any]], provider_id: str) -> dict[str, Any]:
    """Resolve one canonical provider/session liveness snapshot."""
    projections = [
        (dict(session), runtime_liveness(session))
        for session in sessions
        if session.get("provider_id") == provider_id
    ]
    live = [
        {"session_id": session.get("session_id"), "liveness": projection}
        for session, projection in projections
        if projection.get("runtime_process_present") or projection.get("provider_process_present")
    ]
    return {
        "live_sessions": live,
        "fingerprints": [_liveness_fingerprint(session, projection) for session, projection in projections],
    }


def _verify_managed_runtime_stopped(session: Mapping[str, Any]) -> dict[str, Any]:
    """Prove a predecessor endpoint is stopped before recording supersession."""
    control_socket = session.get("control_socket")
    if not control_socket:
        return {"result": "PASS", "endpoint": "ABSENT", "session_id": session.get("session_id")}
    path = Path(str(control_socket))
    if not path.exists():
        return {"result": "PASS", "endpoint": "ABSENT", "session_id": session.get("session_id")}
    if not stat.S_ISSOCK(path.stat().st_mode):
        raise CodexAdapterError("STALE_CONTROL_SOCKET", "predecessor control path is not a Unix socket",
                                next_action="RECONCILE_PROVIDER_SESSION", recovery_action="RECONCILE_PROVIDER_SESSION")
    try:
        probe = _probe_control_transport(str(path), str(session.get("session_id")),
                                         expected_broker_pid=session.get("pid"),
                                         expected_provider_pid=session.get("provider_pid"))
    except CodexAdapterError as error:
        if error.code in {"PROVIDER_CONTROL_FAILED", "PROVIDER_CONTROL_TIMEOUT"}:
            return {"result": "PASS", "endpoint": "REFUSED", "session_id": session.get("session_id")}
        raise
    raise CodexAdapterError("ACTIVE_SESSION_PROTECTION", "predecessor control endpoint is still live",
                            next_action="RECONCILE_PROVIDER_SESSION", recovery_action="RECONCILE_PROVIDER_SESSION",
                            details={"probe": probe})


def supersede_session(repository: Path | str, mission_id: str, old_session_id: str, *,
                      reason: str = "NON_AUTHORITATIVE_RECONCILED_HISTORY",
                      runtime_root: Path | str | None = None,
                      expected_wop_id: str | None = None,
                      expected_execution_id: str | None = None,
                      expected_provider_id: str | None = None) -> dict[str, Any]:
    """Replace only a historical Zeus wrapper that never acquired a thread.

    Transport recovery belongs to ``resume`` and native thread recovery.  This
    compatibility path never removes history and refuses every wrapper that
    has established or ambiguous native thread identity; new-thread authority
    must come from a separate canonical policy.
    """
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    mission = str(mission_id).upper(); provider = expected_provider_id or PROVIDER_ID
    sessions = _all_sessions(runtime)
    requested_session_id = old_session_id
    predecessors = [value for value in sessions if value.get("session_id") == old_session_id]
    if not predecessors:
        # The operator-facing target may be the bound execution-session or
        # provider-session identity.  Resolve it only when exactly one Codex
        # record owns the complete immutable binding.
        aliases = [value for value in sessions
                   if old_session_id in {value.get("execution_session_id"), value.get("provider_session_id")}
                   and value.get("mission_id") == mission]
        if len(aliases) == 1:
            predecessors = aliases
        elif len(aliases) > 1:
            raise CodexAdapterError("CODEX_SESSION_BINDING_AMBIGUOUS", "session alias resolves to multiple Codex sessions")
    if len(predecessors) != 1:
        raise CodexAdapterError("OLD_SESSION_NOT_FOUND", "the requested stale session is not uniquely discoverable")
    old = predecessors[0]
    # From this point onward all lineage is recorded against the actual
    # Codex-managed identity, while the caller's alias is retained for audit.
    old_session_id = str(old["session_id"])
    if old.get("mission_id") != mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "stale session is bound to another mission")
    if old.get("provider_id") != provider:
        raise CodexAdapterError("PROVIDER_BINDING_MISMATCH", "stale session is bound to another provider")
    native = _native_thread_candidate(old)
    if native.get("native_thread_identity_state") != "NOT_CREATED":
        raise CodexAdapterError(
            "THREAD_REPLACEMENT_AUTHORITY_REQUIRED",
            "a Zeus wrapper with native thread identity cannot be superseded without canonical new-thread authority",
            next_action="AUTHORIZE_NEW_CODEX_THREAD",
            details={"native_thread_id": native.get("native_thread_id"),
                     "native_thread_identity_state": native.get("native_thread_identity_state")},
        )

    reconciliation = reconcile_session_history(root, mission, runtime_root=runtime, session=old)
    if reconciliation.get("history_disposition") == "INDETERMINATE":
        raise CodexAdapterError("AMBIGUOUS_HISTORY", "session history is indeterminate")
    if reconciliation.get("mission_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_MISSION_WORK", "prior mission work prevents session replacement")
    if reconciliation.get("repository_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_REPOSITORY_WORK", "prior repository work prevents session replacement")
    reconciliation_acceptance = _reconciliation_acceptance(runtime, old, reconciliation)
    execution = _package(root, mission, runtime)
    for field, expected in (("wop_id", expected_wop_id), ("execution_id", expected_execution_id), ("provider_id", expected_provider_id)):
        if expected is not None and execution.get(field) != expected:
            raise CodexAdapterError(f"{field.upper()}_BINDING_MISMATCH", f"execution binding differs for {field}")
    for field in ("execution_id", "provider_id", "execution_session_id", "provider_session_id"):
        if old.get(field) and execution.get(field) != old.get(field):
            raise CodexAdapterError("SESSION_BINDING_MISMATCH", f"stale session binding differs for {field}")
    if old.get("wop_id") and execution.get("wop_id") != old.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISMATCH", "stale session is bound to another WOP")

    precheck = _provider_liveness_snapshot(sessions, provider)
    linked = [value for value in sessions if value.get("supersedes_session") == old_session_id]
    if len(linked) > 1:
        raise CodexAdapterError("SESSION_SUCCESSOR_CONFLICT", "stale session has multiple replacements")
    if linked:
        replacement = linked[0]
        if replacement.get("mission_id") != mission or replacement.get("execution_id") != execution["execution_id"] or replacement.get("provider_id") != provider:
            raise CodexAdapterError("SESSION_BINDING_MISMATCH", "existing replacement has divergent bindings")
        return {"result": "PASS", "replay": "IDEMPOTENT", "mutation_applied": False,
                "requested_session_id": requested_session_id,
                "old_session_id": old_session_id, "new_session_id": replacement["session_id"],
                "old_session_disposition": "SUPERSEDED", "old_session_preserved": True,
                "supersedes_session": old_session_id, "session_binding": "PASS",
                "canonical_package_binding": "PASS", "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}

    # Re-resolve immediately before the first durable supersession write.  A
    # provider can stop after preflight or appear during the transaction; the
    # mutation must not guess across that boundary.
    mutation_check = _provider_liveness_snapshot(sessions, provider)
    if mutation_check["fingerprints"] != precheck["fingerprints"]:
        raise CodexAdapterError(
            "LIVENESS_CHANGED_DURING_TRANSACTION",
            "provider/session liveness changed between supersession checks",
            details={"precheck": precheck, "mutation_check": mutation_check},
        )
    if mutation_check["live_sessions"]:
        raise CodexAdapterError(
            "ACTIVE_SESSION_PROTECTION",
            "an existing provider/session runtime is active",
            details={"mutation_check": mutation_check},
        )

    stop_verification = _verify_managed_runtime_stopped(old)
    replacement_id = identifier("CODEX-SESSION-REPLACEMENT", {
        "old_session_id": old_session_id, "mission_id": mission, "execution_id": execution["execution_id"],
        "provider_id": provider, "reason": reason,
    })
    event_directory = runtime / EVENT_DIR / replacement_id
    replacement = dict(execution, schema_version=1, contract={"id": CONTRACT, "version": VERSION},
                       session_id=replacement_id, state="READY", pid=None, provider_pid=None,
                       control_socket=None, remote_endpoint=None, log_path=str(runtime / LOG_DIR / f"{replacement_id}.jsonl"),
                       event_directory=str(event_directory), path=str(_session_path(runtime, replacement_id)),
                       mission_work_started=False, repository_work_started=False, started_by="zeus",
                       operator_approval=False, app_server_handshake="NOT_RUN", startup_diagnostics=None,
                       execution_mode="ZEUS_MANAGED", session_mode="ZEUS_MANAGED", provider_mode="APP_SERVER_MANAGED",
                       provider_transport="STDIO", remote_capable=False, readiness_result="PASS",
                       session_disposition="CURRENT", supersedes_session=old_session_id,
                       supersession_reason=reason, supersession_reconciliation=reconciliation,
                       predecessor_runtime_stop_verification=stop_verification,
                       canonical_package_binding="PASS")
    replacement["log_path"] = str(runtime / LOG_DIR / f"{replacement_id}.jsonl")
    old = dict(old, state="SUPERSEDED", session_disposition="SUPERSEDED", superseded_by=replacement_id,
               supersession_reason=reason, supersession_reconciliation=reconciliation,
               reconciliation_acceptance=reconciliation_acceptance)
    if reconciliation_acceptance.get("decision") == "AUTOMATICALLY_SATISFIED_NO_WORK_EVENTS":
        reconciliation_acceptance = _persist_history_reconciliation_receipt(
            runtime, {**reconciliation_acceptance, "operator_action": False}
        )
        old["reconciliation_acceptance"] = reconciliation_acceptance
    replacement["reconciliation_acceptance"] = reconciliation_acceptance
    _save(runtime, old)
    _append_event(runtime, replacement_id, "CODEX_SESSION_REPLACED", {
        "supersedes_session": old_session_id, "reason": reason, "mission_id": mission,
        "wop_id": execution.get("wop_id"), "execution_id": execution.get("execution_id"), "provider_id": provider,
    })
    saved = _save(runtime, replacement)
    return {"result": "PASS", "replay": "APPLIED", "mutation_applied": True,
            "requested_session_id": requested_session_id,
            "old_session_id": old_session_id, "new_session_id": saved["session_id"],
            "old_session_disposition": "SUPERSEDED", "old_session_preserved": True,
            "supersedes_session": old_session_id, "session_binding": "PASS",
            "canonical_package_binding": "PASS", "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}


def reconcile_session_history(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
                               session: Mapping[str, Any] | None = None,
                               execution_projection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Reconcile Codex session work history without changing runtime state.

    Session events are evidence, not proof of applied mission work.  A work
    event is authoritative only when it carries the bound identity and has
    corroboration in the canonical execution/active-transition records.  The
    result is deliberately a projection: applying a session supersession or
    other runtime mutation remains a separate, explicitly authorized action.
    """
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    mission = str(mission_id).upper()
    current = dict(session) if session is not None else _existing(runtime, mission)
    if not current:
        return {"result": "PASS", "mission_id": mission, "history_disposition": "NO_SESSION",
                "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
                "reconciliation_required": False, "transport_replacement_required": False,
                "thread_replacement_required": False, "read_only": True}

    event_directory = Path(str(current.get("event_directory") or runtime / EVENT_DIR / current["session_id"]))
    # Read only numbered journal events.  Readiness markers such as
    # ``app-server-ready.json`` live beside the journal but are not events.
    paths = sorted(event_directory.glob("[0-9][0-9][0-9][0-9].json")) if event_directory.is_dir() else []
    events: list[dict[str, Any]] = []
    chain_errors: list[str] = []
    expected = 1
    for path in paths:
        try:
            event = load_json(path)
        except Exception as error:
            chain_errors.append(f"INVALID_EVENT:{path.name}:{error}")
            continue
        events.append(event)
        if event.get("sequence") != expected:
            chain_errors.append(f"SEQUENCE_GAP:{expected}:{event.get('sequence')}")
        if event.get("session_id") != current.get("session_id"):
            chain_errors.append(f"SESSION_BINDING:{path.name}")
        unsigned = {key: value for key, value in event.items() if key != "event_digest"}
        if event.get("event_digest") != digest(unsigned):
            chain_errors.append(f"EVENT_DIGEST:{path.name}")
        previous = events[-2].get("event_digest") if len(events) > 1 else None
        if event.get("previous_event_digest") != previous:
            chain_errors.append(f"PREVIOUS_DIGEST:{path.name}")
        expected += 1

    work_events = [event for event in events if event.get("event") in
                   {"MISSION_WORK_STARTED", "MISSION_WORK_RESUMED"}]
    execution = dict(execution_projection or {})
    if not execution:
        try:
            from scripts.lib.emp.execution_start import verify as verify_execution_start
            execution = verify_execution_start(root, mission, runtime_root=runtime)
        except Exception as error:
            chain_errors.append(f"EXECUTION_SOURCE_UNAVAILABLE:{error}")

    execution_id = current.get("execution_id")
    active_path = _active_path(runtime, str(execution_id)) if execution_id else None
    active_record = load_json(active_path) if active_path and active_path.is_file() else None
    authoritative_execution_work = execution.get("mission_work_started") is True
    authoritative_repository_work = execution.get("repository_work_started") is True
    active_work = bool(active_record and active_record.get("mission_work_started") is True)
    repository_receipts = list((runtime / "repository-work-receipts").glob("*.json")) if (runtime / "repository-work-receipts").is_dir() else []
    corroborating_work = authoritative_execution_work or active_work
    corroborating_repository = authoritative_repository_work or bool(repository_receipts)

    missing_provenance = []
    for event in work_events:
        payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
        for field in ("execution_id", "mission_id", "wop_id", "session_id", "provider_id", "source_digest"):
            if not (event.get(field) or payload.get(field)):
                missing_provenance.append(f"{event.get('event')}:{field}")

    if work_events and corroborating_work:
        disposition = "HISTORICAL_WORK_CONFIRMED"
        mission_work = "YES"
    elif work_events and not corroborating_work and (chain_errors or missing_provenance):
        disposition = "EVENTS_NON_AUTHORITATIVE"
        mission_work = "NO"
    elif work_events:
        disposition = "INDETERMINATE"
        mission_work = "INDETERMINATE"
    else:
        disposition = "NO_WORK_EVENTS"
        mission_work = "YES" if authoritative_execution_work else "NO"

    if corroborating_repository:
        repository_work = "YES"
    elif disposition == "INDETERMINATE":
        repository_work = "INDETERMINATE"
    else:
        repository_work = "NO"

    safe_no_work = disposition in {"EVENTS_NON_AUTHORITATIVE", "NO_WORK_EVENTS"} and not corroborating_work and not corroborating_repository
    thread = thread_lifecycle(root, current, runtime_root=runtime)
    return {
        "result": "PASS" if disposition != "INDETERMINATE" else "FAIL",
        "mission_id": mission, "session_id": current.get("session_id"),
        "execution_id": execution_id, "provider_id": current.get("provider_id"),
        "mission_work_event_count": sum(event.get("event") == "MISSION_WORK_STARTED" for event in events),
        "mission_work_resumed_event_count": sum(event.get("event") == "MISSION_WORK_RESUMED" for event in events),
        "event_ids": [event.get("event_digest") for event in work_events],
        "event_provenance": "INSUFFICIENT" if missing_provenance else "PRESENT",
        "event_authority": "NON_AUTHORITATIVE" if disposition == "EVENTS_NON_AUTHORITATIVE" else "CORROBORATED" if corroborating_work else "NOT_ESTABLISHED",
        "chain_errors": chain_errors, "missing_provenance": missing_provenance,
        "mission_work_actually_occurred": mission_work,
        "repository_work_actually_occurred": repository_work,
        "corroborating_execution_evidence": {"execution_work": authoritative_execution_work, "active_record": active_work},
        "corroborating_repository_evidence": {"execution_work": authoritative_repository_work, "receipt_count": len(repository_receipts)},
        "history_disposition": disposition,
        "previous_projection": {"mission_work_started": current.get("mission_work_started"),
                                 "repository_work_started": current.get("repository_work_started"),
                                 "scope": current.get("scope")},
        "reconciled_projection": {"mission_work_started": mission_work == "YES",
                                   "repository_work_started": repository_work == "YES",
                                   "execution_state": execution.get("execution_start_state"),
                                   "next_authorized_action": execution.get("next_authorized_action")},
        "reconciliation_required": bool(work_events and (chain_errors or missing_provenance or disposition != "NO_WORK_EVENTS")),
        "transport_liveness": thread.get("transport_liveness"),
        "transport_replacement_required": thread.get("transport_replacement_required"),
        "transport_replacement_safe": thread.get("transport_replacement_safe"),
        "thread_identity": thread.get("thread_identity"),
        "thread_persisted": thread.get("thread_persisted"),
        "thread_resume_supported": thread.get("thread_resume_supported"),
        "thread_resume_eligible": thread.get("thread_resume_eligible"),
        "thread_fork_supported": thread.get("thread_fork_supported"),
        "thread_fork_required": thread.get("thread_fork_required"),
        "thread_replacement_required": thread.get("thread_replacement_required"),
        "history_safe_for_thread_recovery": safe_no_work,
        "read_only": True,
    }


def _process_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _provider_control_ready(session: Mapping[str, Any]) -> bool:
    """Return whether the bound provider runtime can accept control traffic.

    PID presence is not sufficient here: retirement can leave stale PID
    metadata behind, and the broker's Unix socket is the actual control
    resource used by the active transition.  Reuse the canonical liveness
    projection and require the persisted control channel to exist before
    treating a session as resumable/idempotently live.
    """
    liveness = runtime_liveness(session)
    control_socket = session.get("control_socket")
    # Legacy synthetic fixtures do not carry broker ownership receipts. Real
    # Zeus-managed sessions always do; a missing receipt is therefore stale.
    if session.get("provider_mode") != "APP_SERVER_MANAGED":
        return bool(liveness.get("session_live") and control_socket and Path(str(control_socket)).exists())
    if not liveness.get("session_live") or not control_socket:
        return False
    ready_path = Path(str(session.get("event_directory") or "")) / "app-server-ready.json"
    try:
        ready = load_json(ready_path)
        if ready.get("result") != "PASS" or ready.get("handshake") != "PASS":
            return False
        if ready.get("session_id") != session.get("session_id"):
            return False
        if ready.get("control_socket") != str(control_socket):
            return False
        expected_provider = _marker_provider_pid(session) or session.get("provider_pid")
        if ready.get("broker_pid") != session.get("pid") or ready.get("provider_pid") != expected_provider:
            return False
        broker_identity = process_identity(session.get("pid"))
        provider_identity = process_identity(expected_provider)
        if not broker_identity.get("alive") or not provider_identity.get("alive"):
            return False
        if ready.get("broker_identity", {}).get("identity_digest") != broker_identity.get("process_identity_digest"):
            return False
        if ready.get("provider_identity", {}).get("identity_digest") != provider_identity.get("process_identity_digest"):
            return False
        _probe_control_transport(str(control_socket), str(session.get("session_id")),
                                 expected_broker_pid=session.get("pid"),
                                 expected_provider_pid=expected_provider)
        return True
    except (OSError, ValueError, KeyError, CodexAdapterError, json.JSONDecodeError):
        return False


def _startup_paths(runtime: Path, session_id: str) -> dict[str, Path]:
    # AF_UNIX is limited to a small byte-sized path on Linux.  Keep durable
    # receipts in the runtime tree, but put the ephemeral control socket in a
    # short shared runtime location so deep repository/runtime roots cannot
    # make launch fail mysteriously.
    socket_root = Path("/tmp/zeus-sockets")
    socket_name = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24] + ".sock"
    control = socket_root / socket_name
    if len(os.fsencode(str(control))) > 107:
        raise CodexAdapterError("AF_UNIX_PATH_TOO_LONG",
                                f"control socket path exceeds AF_UNIX limit: {control}",
                                next_action="SHORTEN_RUNTIME_SOCKET_LOCATION")
    return {
        "codex_home": runtime / CODEX_HOME_DIR / session_id,
        "ready": runtime / EVENT_DIR / session_id / "app-server-ready.json",
        "exited": runtime / EVENT_DIR / session_id / "app-server-exited.json",
        "control": control,
    }


def _control_transport_request(control_socket: str, request: Mapping[str, Any], *, timeout: float = 3.0) -> dict[str, Any]:
    """Exchange one bounded line-delimited control request without provider assumptions."""
    if not control_socket:
        raise CodexAdapterError("CONTROL_CHANNEL_MISSING", "bound provider session has no control channel",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(control_socket)
            client.sendall((json.dumps(dict(request), separators=(",", ":")) + "\n").encode())
            wanted = request.get("id")
            buffer = b""
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                chunk = client.recv(65536)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, _, buffer = buffer.partition(b"\n")
                    if not line:
                        continue
                    try:
                        value = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if value.get("id") == wanted:
                        return value
    except (OSError, TimeoutError) as error:
        raise CodexAdapterError("PROVIDER_CONTROL_FAILED", str(error),
                                next_action="RECONCILE_PROVIDER_SESSION",
                                lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION") from error
    raise CodexAdapterError("PROVIDER_CONTROL_TIMEOUT", "provider control endpoint did not answer",
                            next_action="RECONCILE_PROVIDER_SESSION",
                            lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                            recovery_action="RECONCILE_PROVIDER_SESSION")


def _probe_control_transport(control_socket: str, session_id: str, *, expected_broker_pid: int | None = None,
                             expected_provider_pid: int | None = None) -> dict[str, Any]:
    """Prove the socket is the live Zeus broker for this exact managed session."""
    path = Path(str(control_socket))
    if not path.exists() or not stat.S_ISSOCK(path.stat().st_mode):
        raise CodexAdapterError("STALE_CONTROL_SOCKET", "managed control endpoint is missing or is not a Unix socket",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="SUPERSEDE_CODEX_SESSION")
    response = _control_transport_request(str(path), {
        "jsonrpc": "2.0", "id": f"zeus-transport-probe-{session_id}",
        "method": "zeus/transport/probe", "params": {"session_id": session_id},
    })
    result = response.get("result") or {}
    if result.get("result") != "PASS" or result.get("session_id") != session_id:
        raise CodexAdapterError("CONTROL_SOCKET_OWNERSHIP_MISMATCH", "control endpoint does not belong to the bound successor session",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="SUPERSEDE_CODEX_SESSION", details={"probe": response})
    if expected_broker_pid is not None and result.get("broker_pid") != expected_broker_pid:
        raise CodexAdapterError("CONTROL_SOCKET_OWNERSHIP_MISMATCH", "control endpoint broker identity differs from the managed session",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="SUPERSEDE_CODEX_SESSION", details={"probe": response})
    if expected_provider_pid is not None and result.get("provider_pid") != expected_provider_pid:
        raise CodexAdapterError("PROVIDER_PROCESS_IDENTITY_MISMATCH", "control endpoint provider identity differs from the managed session",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="SUPERSEDE_CODEX_SESSION", details={"probe": response})
    if result.get("provider_alive") is not True:
        raise CodexAdapterError("PROVIDER_NOT_ALIVE", "managed provider died while control transport was being verified",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION", details={"probe": response})
    return result


def _marker_provider_pid(session: Mapping[str, Any]) -> int | None:
    path = Path(str(session.get("event_directory", ""))) / "app-server-ready.json"
    if not path.is_file():
        return None
    try:
        value = load_json(path)
        pid = value.get("provider_pid")
        return pid if isinstance(pid, int) else None
    except Exception:
        return None


def _prepare_codex_home(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    source_home = Path.home() / ".codex"
    for name in ("auth.json", "config.toml"):
        target = path / name
        source = source_home / name
        if source.is_file() and not target.exists():
            try:
                target.symlink_to(source)
            except FileExistsError:
                pass


def _launch_handshake(root: Path, runtime: Path, session_id: str, log_path: Path,
                      codex_bin: str) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    paths = _startup_paths(runtime, session_id)
    _prepare_codex_home(paths["codex_home"])
    if paths["control"].exists():
        # Never unlink a live or foreign endpoint merely because a session is
        # being resumed. A refused connection is the only safe stale-socket
        # case; a reachable/mismatched endpoint is an ownership conflict.
        if not stat.S_ISSOCK(paths["control"].stat().st_mode):
            raise CodexAdapterError("STALE_CONTROL_SOCKET", "existing managed control path is not a Unix socket",
                                    next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                    recovery_action="SUPERSEDE_CODEX_SESSION")
        try:
            _probe_control_transport(str(paths["control"]), session_id)
        except CodexAdapterError as error:
            if error.code not in {"PROVIDER_CONTROL_FAILED", "PROVIDER_CONTROL_TIMEOUT"}:
                raise
        else:
            raise CodexAdapterError("CONTROL_SOCKET_OWNERSHIP_CONFLICT", "existing control endpoint is live; refusing to replace it",
                                    next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                    recovery_action="RECONCILE_PROVIDER_SESSION")
    for marker in (paths["ready"], paths["exited"], paths["control"]):
        if marker.exists():
            marker.unlink()
    command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker",
               "--root", str(root), "--codex-home", str(paths["codex_home"]),
               "--log", str(log_path), "--ready", str(paths["ready"]),
               "--exited", str(paths["exited"]), "--session-id", session_id,
               "--codex-bin", codex_bin]
    command.extend(["--control", str(paths["control"])])
    broker = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              start_new_session=True)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if paths["ready"].is_file():
            value = load_json(paths["ready"])
            if value.get("result") != "PASS":
                code = str(value.get("error_code") or "APP_SERVER_HANDSHAKE_FAILED")
                raise CodexAdapterError(code, value.get("error", "Codex handshake failed"),
                                        next_action="RECONCILE_PROVIDER_SESSION",
                                        lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                        recovery_action="RECONCILE_PROVIDER_SESSION", details={"startup": value})
            try:
                value["transport_probe"] = _probe_control_transport(
                    str(value.get("control_socket") or paths["control"]), session_id,
                    expected_broker_pid=broker.pid, expected_provider_pid=value.get("provider_pid"),
                )
            except CodexAdapterError:
                if broker.poll() is None:
                    broker.terminate()
                    try:
                        broker.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        broker.kill()
                raise
            return broker, value
        if broker.poll() is not None:
            raise CodexAdapterError("APP_SERVER_HANDSHAKE_FAILED", "Codex app-server broker exited before handshake")
        time.sleep(0.1)
    raise CodexAdapterError("APP_SERVER_HANDSHAKE_TIMEOUT", "Codex app-server handshake timed out")


def session_identifier(package: Mapping[str, Any]) -> str:
    """Derive the stable Codex identity from immutable execution bindings."""
    return identifier("CODEX-SESSION", {"execution_id": package["execution_id"],
        "provider_id": package["provider_id"], "repository_identity": package["repository_identity"],
        "contract": [CONTRACT, VERSION]})


def _verify_session_package_binding(session: Mapping[str, Any], package: Mapping[str, Any]) -> None:
    """Verify durable lifecycle identity without freezing mutable baselines.

    Current publication and authority digests can advance while an execution
    remains at its controlled boundary.  They are revalidated by ``_package``;
    only the immutable Zeus/provider/repository bindings must equal the saved
    wrapper record.
    """
    fields = (
        "mission_id", "wop_id", "execution_id", "execution_session_id",
        "provider_id", "provider_session_id", "provider_invocation_id",
        "repository", "repository_identity", "repository_id", "repository_fingerprint",
    )
    mismatches = [field for field in fields
                  if session.get(field) is not None and session.get(field) != package.get(field)]
    if mismatches:
        raise CodexAdapterError("SESSION_INPUT_MISMATCH",
                                "existing Codex session has a different immutable binding",
                                details={"mismatched_fields": mismatches})


def _result(session: Mapping[str, Any], *, read_only: bool = True,
            repository: Path | str | None = None,
            runtime_root: Path | str | None = None) -> dict[str, Any]:
    liveness = runtime_liveness(session)
    root = Path(repository or str(session.get("repository"))).resolve()
    lifecycle = thread_lifecycle(root, session, runtime_root=runtime_root)
    provider_pid = _marker_provider_pid(session) or session.get("provider_pid")
    alive = liveness["session_live"]
    state = session.get("state")
    if state in ACTIVE_STATES and not alive:
        state = "INTERRUPTED"
    blockers = []
    if lifecycle["runtime_classification"] == "THREAD_RECOVERY_BLOCKED":
        blockers.append({"code": "THREAD_RECOVERY_BLOCKED",
                         "message": "native Codex thread is missing, invalid, ambiguous, or concurrently owned"})
    return {"result": "PASS", "mission_id": session["mission_id"], "session_id": session["session_id"],
            "codex_session_id": session["session_id"], "execution_session_id": session.get("execution_session_id"),
            "provider_session_id": session.get("provider_session_id"),
            "execution_id": session["execution_id"], "provider_id": session["provider_id"],
            "state": state, "process_alive": alive, "pid": session.get("pid"),
            "provider_pid": provider_pid,
            "provider_process": "RUNNING" if liveness["provider_process_present"] else "STOPPED",
            "provider_liveness": liveness["provider_liveness"],
            "runtime_process_present": liveness["runtime_process_present"],
            "runtime_process_owns_codex_session": liveness["runtime_process_owns_codex_session"],
            "session_liveness": liveness["session_liveness"],
            "runtime_classification": lifecycle["runtime_classification"],
            "app_server_handshake": session.get("app_server_handshake", "NOT_RUN"),
            "execution_mode": session.get("execution_mode", "ZEUS_MANAGED"),
            "session_mode": session.get("session_mode", "ZEUS_MANAGED"),
            "interactive": False, "managed": True,
            "provider_mode": session.get("provider_mode", "APP_SERVER_MANAGED"),
            "transport": session.get("provider_transport", "STDIO"),
            "remote_capable": bool(session.get("remote_capable", False)),
            "endpoint_uri": session.get("remote_endpoint"),
            "readiness_result": session.get("readiness_result", "NOT_RUN"),
            "startup_diagnostics": session.get("startup_diagnostics"),
            "mission_bound": True, "execution_bound": True, "repository_bound": True,
            "authority": "PASS", "session_identity": "PASS", "provider_identity": "PASS",
            "sandbox": (session.get("scope") or {}).get("sandbox", "workspace-write"),
            "execution_monitoring": "ACTIVE" if alive else "INACTIVE",
            "mission_work_started": bool(session.get("mission_work_started")),
            "repository_work_started": bool(session.get("repository_work_started")),
            "zeus_session_id": session["session_id"],
            "transport_id": {"broker_pid": session.get("pid"), "provider_pid": provider_pid,
                             "control_socket": session.get("control_socket")},
            "native_codex_thread_id": lifecycle.get("thread_identity"),
            "thread_identity": lifecycle.get("thread_identity"),
            "thread_persisted": lifecycle.get("thread_persisted"),
            "thread_readable": lifecycle.get("thread_readable"),
            "thread_persistence_state": lifecycle.get("thread_persistence_state"),
            "thread_resume_supported": lifecycle.get("thread_resume_supported"),
            "thread_resume_eligible": lifecycle.get("thread_resume_eligible"),
            "thread_fork_supported": lifecycle.get("thread_fork_supported"),
            "thread_fork_required": lifecycle.get("thread_fork_required"),
            "thread_replacement_required": lifecycle.get("thread_replacement_required"),
            "thread_ownership_conflicts": lifecycle.get("thread_ownership_conflicts"),
            "transport_liveness": lifecycle.get("transport_liveness"),
            "transport_replacement_required": lifecycle.get("transport_replacement_required"),
            "transport_replacement_safe": lifecycle.get("transport_replacement_safe"),
            "replay": "IDEMPOTENT", "package_digest": session.get("package_digest"),
            "logs": session.get("log_path"), "artifacts": {"session": session.get("path"),
            "events": session.get("event_directory")}, "blockers": blockers, "read_only": read_only,
            "lifecycle_next_action": lifecycle["runtime_recovery_action"],
            "runtime_recovery_action": lifecycle["runtime_recovery_action"],
            "next_authorized_action": lifecycle["runtime_recovery_action"]}


def status(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    session = _existing(runtime, str(mission_id).upper())
    if not session:
        return {"result": "PASS", "mission_id": str(mission_id).upper(), "state": "NOT_STARTED",
                "mission_bound": False, "execution_bound": False, "repository_bound": False,
                "blockers": [], "read_only": True, "next_authorized_action": "START_CODEX_SESSION"}
    value = _result(session, repository=root, runtime_root=runtime)
    try:
        value["history_reconciliation"] = reconcile_session_history(repository, mission_id,
                                                                       runtime_root=runtime, session=session)
        reconciliation = value["history_reconciliation"]
    except CodexAdapterError as error:
        value["history_reconciliation"] = {"result": "FAIL", "history_disposition": "INDETERMINATE",
                                            "blockers": [{"code": error.code, "message": error.message}],
                                            "read_only": True}
    try:
        from scripts.lib.emp import execution_monitoring
        from scripts.lib.emp.legacy_lifecycle_reconciliation import inspect as inspect_legacy
        transaction_path, transaction = execution_monitoring._find_transaction(runtime, session["execution_id"])
        monitoring = execution_monitoring._monitoring_record(runtime, str(transaction["execution_id"]))
        legacy = inspect_legacy(repository, runtime, transaction=transaction, monitoring=monitoring)
        value.update({"state": "RECONCILED_HISTORICAL", "execution_monitoring": "INACTIVE",
                      "mission_work_started": True, "repository_work_started": False,
                      "next_authorized_action": "OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION",
                      "legacy_reconciliation": legacy})
    except Exception:
        pass
    return value


def _active_path(runtime: Path, execution_id: str) -> Path:
    directory = (runtime / ACTIVE_TRANSITION_DIR).resolve()
    path = (directory / f"{execution_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise CodexAdapterError("ACTIVE_TRANSITION_PATH_ESCAPE", "active transition path escapes runtime") from error
    return path


def _monitoring_path(runtime: Path, execution_id: str) -> Path:
    directory = (runtime / MONITORING_DIR).resolve()
    path = (directory / f"{execution_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise CodexAdapterError("MONITORING_PATH_ESCAPE", "monitoring path escapes runtime") from error
    return path


def _read_active(runtime: Path, execution_id: str) -> dict[str, Any] | None:
    path = _active_path(runtime, execution_id)
    if not path.is_file():
        return None
    value = load_json(path)
    supplied = value.get("record_digest")
    unsigned = {key: item for key, item in value.items() if key != "record_digest"}
    if supplied != digest(unsigned):
        raise CodexAdapterError("ACTIVE_TRANSITION_DIGEST_MISMATCH", "active transition digest mismatch")
    return value


def _write_projection(runtime: Path, execution_id: str, value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("record_digest", None)
    unsigned["record_digest"] = digest(unsigned)
    atomic_write(_active_path(runtime, execution_id), unsigned)
    atomic_write(_monitoring_path(runtime, execution_id), unsigned)
    return unsigned


def _control_request(control_socket: str, request: Mapping[str, Any], *, timeout: float = 15.0) -> dict[str, Any]:
    """Send one bounded JSON-RPC request through the already-bound broker."""
    if not control_socket:
        raise CodexAdapterError("CONTROL_CHANNEL_MISSING", "bound provider session has no control channel",
                                next_action="RECONCILE_PROVIDER_SESSION")
    deadline = time.monotonic() + timeout
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(max(0.1, timeout))
            client.connect(control_socket)
            client.sendall((json.dumps(dict(request), separators=(",", ":")) + "\n").encode())
            wanted = request.get("id")
            buffer = b""
            while time.monotonic() < deadline:
                chunk = client.recv(65536)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, _, buffer = buffer.partition(b"\n")
                    if not line:
                        continue
                    try:
                        value = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if value.get("id") == wanted:
                        if value.get("error"):
                            raise CodexAdapterError("PROVIDER_REQUEST_REJECTED", str(value["error"]),
                                                    next_action="RECONCILE_PROVIDER_SESSION")
                        return value
    except ConnectionResetError as error:
        raise CodexAdapterError("PROVIDER_TRANSPORT_RESET", str(error),
                                next_action="RECONCILE_PROVIDER_SESSION",
                                lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION") from error
    except (OSError, TimeoutError) as error:
        raise CodexAdapterError("PROVIDER_CONTROL_FAILED", str(error),
                                next_action="RECONCILE_PROVIDER_SESSION",
                                lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION") from error
    raise CodexAdapterError("PROVIDER_REQUEST_TIMEOUT", "provider did not acknowledge controlled mission work",
                            next_action="RECONCILE_PROVIDER_SESSION",
                            lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                            recovery_action="RECONCILE_PROVIDER_SESSION")


def _validate_native_thread_response(response: Mapping[str, Any], *, expected_thread_id: str | None,
                                     repository: Path, forked_from_id: str | None = None,
                                     expected_native_session_id: str | None = None,
                                     expected_thread_path: str | None = None) -> dict[str, Any]:
    """Validate the installed app-server thread response against Zeus bindings."""
    thread = _thread_from_response(response)
    if thread is None:
        raise CodexAdapterError("NATIVE_THREAD_RESPONSE_INVALID",
                                "Codex app-server did not return a native thread object",
                                next_action="RECONCILE_CODEX_THREAD_RECOVERY")
    thread_id = str(thread["native_thread_id"])
    if expected_thread_id is not None and thread_id != expected_thread_id:
        raise CodexAdapterError("NATIVE_THREAD_IDENTITY_MISMATCH",
                                "Codex app-server resumed a different native thread",
                                next_action="RECONCILE_CODEX_THREAD_RECOVERY",
                                details={"expected_thread_id": expected_thread_id,
                                         "actual_thread_id": thread_id})
    if expected_native_session_id is not None and thread.get("native_session_id") != expected_native_session_id:
        raise CodexAdapterError("NATIVE_SESSION_IDENTITY_MISMATCH",
                                "Codex app-server returned a different persisted session lineage",
                                next_action="RECONCILE_CODEX_THREAD_RECOVERY")
    if expected_thread_path is not None:
        actual_path = thread.get("native_thread_path")
        if not actual_path or Path(str(actual_path)).resolve() != Path(expected_thread_path).resolve():
            raise CodexAdapterError("NATIVE_THREAD_PATH_MISMATCH",
                                    "Codex app-server returned a different persisted rollout",
                                    next_action="RECONCILE_CODEX_THREAD_RECOVERY")
    if forked_from_id is not None:
        if thread_id == forked_from_id or thread.get("native_thread_forked_from_id") != forked_from_id:
            raise CodexAdapterError("NATIVE_THREAD_LINEAGE_MISMATCH",
                                    "Codex app-server fork response did not preserve native lineage",
                                    next_action="RECONCILE_CODEX_THREAD_RECOVERY")
    cwd = thread.get("native_thread_cwd")
    if cwd and Path(str(cwd)).resolve() != repository.resolve():
        raise CodexAdapterError("REPOSITORY_BINDING_MISMATCH",
                                "native Codex thread is bound to another repository",
                                next_action="RECONCILE_CODEX_THREAD_RECOVERY",
                                details={"expected_repository": str(repository.resolve()), "thread_cwd": cwd})
    return thread


def _terminate_replacement_transport(process: subprocess.Popen[Any]) -> None:
    """Retire a replacement transport that failed before authoritative commit."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def _authoritative_controlled_work_evidence(value: Mapping[str, Any], execution: Mapping[str, Any]) -> bool:
    """Require bound provider evidence before treating an active projection as work."""
    evidence = value.get("execution_evidence")
    if not isinstance(evidence, Mapping) or evidence.get("provider_acknowledged") is not True:
        return False
    supplied_digest = evidence.get("evidence_digest")
    if not supplied_digest or supplied_digest != digest({key: item for key, item in evidence.items()
                                                         if key != "evidence_digest"}):
        return False
    if value.get("execution_evidence_digest") != supplied_digest:
        return False
    required = ("mission_id", "wop_id", "execution_id", "execution_session_id",
                "provider_session_id", "provider_id", "codex_session_id", "thread_id", "turn_id")
    if any(not evidence.get(field) for field in required):
        return False
    return all(evidence.get(field) == execution.get(field) for field in (
        "mission_id", "wop_id", "execution_id", "execution_session_id",
        "provider_session_id", "provider_id"))


def begin_controlled_mission_work(repository: Path | str, mission_id: str, *, approval: bool = False,
                                  prompt: str | None = None, runtime_root: Path | str | None = None,
                                  codex_bin: str = "codex", launch: bool = True) -> dict[str, Any]:
    """Consume the bound execution-start boundary exactly once.

    The immutable P5-G5 execution-start artifacts remain unchanged.  This
    operation verifies them, uses the same provider/session identity, asks
    the bound broker to create a controlled turn, then atomically records the
    active projection consumed by P5-G6 monitoring.
    """
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission = str(mission_id).upper()
    from scripts.lib.emp.execution_start import verify as verify_execution_start
    execution = verify_execution_start(root, mission, runtime_root=runtime)
    if execution.get("result") != "PASS":
        raise _execution_verification_error(execution)
    if execution.get("mission_id") != mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution-start mission binding differs from requested mission")
    if not execution.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISSING", "execution-start has no bound WOP")
    if not execution.get("execution_session_id") or not execution.get("provider_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISSING", "execution-start session bindings are incomplete")
    if not execution.get("provider_id") or not execution.get("provider_invocation_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISSING", "execution-start provider bindings are incomplete")
    if execution.get("blockers") or execution.get("approvals_required"):
        raise CodexAdapterError("EXECUTION_BLOCKED", "execution has an active blocker or outstanding approval")
    if execution.get("execution_start_state") != "READY_FOR_CONTROLLED_EXECUTION":
        raise CodexAdapterError("EXECUTION_STATE_INVALID", "execution is not at READY_FOR_CONTROLLED_EXECUTION")
    if execution.get("next_authorized_action") != "BEGIN_CONTROLLED_MISSION_WORK":
        raise CodexAdapterError("EXECUTION_NOT_READY", "execution is not at the controlled mission-work boundary")
    execution_id = execution["execution_id"]
    existing_active = _read_active(runtime, execution_id)
    if existing_active:
        if not _authoritative_controlled_work_evidence(existing_active, execution):
            raise CodexAdapterError("ACTIVE_EVIDENCE_INVALID", "active execution projection has no authoritative provider-work evidence",
                                    next_action="RECONCILE_EXECUTION_STATE")
        return dict(existing_active, result="PASS", replay="IDEMPOTENT", duplicate_execution="NO",
                    read_only=False, mutation_applied=False)
    if not approval:
        raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for controlled mission work",
                                next_action="APPROVE_CONTROLLED_MISSION_WORK")
    authority = _authority(root)
    session = _existing(runtime, mission)
    session_reconciliation = None
    if session and session.get("execution_id") != execution_id:
        raise CodexAdapterError("EXECUTION_IDENTITY_MISMATCH", "provider session is bound to another execution")
    if session and session.get("provider_id") != execution.get("provider_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISMATCH", "provider session is bound to another provider")
    if session and session.get("execution_session_id") and session.get("execution_session_id") != execution.get("execution_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISMATCH", "provider session is bound to another execution session")
    if session and session.get("provider_session_id") and session.get("provider_session_id") != execution.get("provider_session_id"):
        raise CodexAdapterError("PROVIDER_SESSION_BINDING_MISMATCH", "provider session identity differs from execution-start binding")
    if session and session.get("repository_work_started") is True:
        raise CodexAdapterError("REPOSITORY_WORK_STATE_CONFLICT", "provider session claims repository work before authoritative controlled-work transition",
                                next_action="RECONCILE_EXECUTION_STATE")
    if not session:
        if not launch:
            raise CodexAdapterError("SESSION_NOT_READY", "bound provider session is not available")
        start(repository, mission, approval=approval, prompt=prompt, runtime_root=runtime, codex_bin=codex_bin)
        session = _existing(runtime, mission)
    elif not _provider_control_ready(session):
        session_reconciliation = reconcile_session_history(root, mission, runtime_root=runtime, session=session)
        if not _provider_control_ready(session):
            if not launch:
                lifecycle = thread_lifecycle(root, session, runtime_root=runtime)
                raise CodexAdapterError("SESSION_NOT_READY", "bound provider transport is not live",
                                        next_action=lifecycle["runtime_recovery_action"], details=lifecycle)
            resume(repository, mission, approval=approval, runtime_root=runtime, codex_bin=codex_bin)
            session = _existing(runtime, mission)
    if not session or not _provider_control_ready(session):
        raise CodexAdapterError("PROVIDER_NOT_ALIVE", "bound provider session is not live",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION")
    if session.get("mission_work_started"):
        raise CodexAdapterError("MISSION_WORK_STATE_CONFLICT", "provider session already claims mission work")
    request_id = f"zeus-controlled-work-{execution_id}"
    instruction = prompt or "Begin the bounded Zeus-controlled mission-work turn. Do not publish, synchronize EOS, or perform unrelated work; stop at the operator acceptance boundary and report progress."
    pending = session.get("pending_controlled_work") or {}
    if pending.get("request_id") == request_id and pending.get("thread_id") and pending.get("thread_response"):
        thread_response = pending["thread_response"]
        thread_id = pending["thread_id"]
    else:
        # Readiness is re-proven adjacent to thread/start; a historical
        # handshake receipt never authorizes controlled mission work.
        if not _provider_control_ready(session):
            raise CodexAdapterError("PROVIDER_NOT_ALIVE", "provider control transport is not live immediately before thread/start",
                                    next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                    recovery_action="RECONCILE_PROVIDER_SESSION")
        lifecycle = thread_lifecycle(root, session, runtime_root=runtime)
        if lifecycle.get("thread_identity"):
            if not lifecycle.get("thread_resume_eligible"):
                raise CodexAdapterError("THREAD_RECOVERY_BLOCKED",
                                        "an existing native thread cannot be safely loaded",
                                        next_action="RECONCILE_CODEX_THREAD_RECOVERY", details=lifecycle)
            thread_id = lifecycle["thread_identity"]
            thread_response = _control_request(session.get("control_socket"), {
                "jsonrpc": "2.0", "id": f"{request_id}-read", "method": "thread/read",
                "params": {"threadId": thread_id, "includeTurns": False},
            })
            _validate_native_thread_response(
                thread_response, expected_thread_id=str(thread_id), repository=root,
                expected_native_session_id=lifecycle.get("native_session_id"),
            )
        else:
            thread_response = _control_request(session.get("control_socket"), {
                "jsonrpc": "2.0", "id": request_id, "method": "thread/start",
                "params": {"cwd": str(root), "approvalPolicy": "on-request", "sandbox": "workspace-write",
                            "instructions": instruction},
            })
            native_thread = _validate_native_thread_response(
                thread_response, expected_thread_id=None, repository=root)
            thread_id = native_thread["native_thread_id"]
            session = dict(session, **native_thread,
                           native_thread_loaded_transport_pid=session.get("pid"),
                           native_thread_loaded_provider_pid=session.get("provider_pid"))
        session = _save(runtime, dict(session, pending_controlled_work={
            "request_id": request_id, "thread_id": thread_id, "thread_response": thread_response,
            "thread_response_digest": digest(thread_response), "instruction_digest": digest({"instruction": instruction}),
        }))
    if not _provider_control_ready(session):
        raise CodexAdapterError("PROVIDER_NOT_ALIVE", "provider control transport is not live immediately before turn/start",
                                next_action="RECONCILE_PROVIDER_SESSION", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION")
    turn_response = _control_request(session.get("control_socket"), {
        "jsonrpc": "2.0", "id": f"{request_id}-turn", "method": "turn/start",
        "params": {"threadId": thread_id, "input": [{"type": "text", "text": instruction}]},
    })
    turn_result = turn_response.get("result") or {}
    turn_id = (turn_result.get("turn") or {}).get("id") or turn_result.get("turnId") or turn_result.get("id")
    if not turn_id:
        raise CodexAdapterError("TURN_ID_MISSING", "provider did not return a controlled turn identity",
                                next_action="RECONCILE_EXECUTION_STATE", lifecycle_next_action="BEGIN_CONTROLLED_MISSION_WORK",
                                recovery_action="RECONCILE_PROVIDER_SESSION")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    execution_evidence = {
        "schema_version": 1, "record_type": "CONTROLLED_MISSION_WORK_EVIDENCE",
        "mission_id": mission, "wop_id": execution.get("wop_id"), "execution_id": execution_id,
        "execution_session_id": execution.get("execution_session_id"),
        "provider_session_id": execution.get("provider_session_id"), "provider_id": execution.get("provider_id"),
        "codex_session_id": session["session_id"], "thread_id": thread_id, "turn_id": turn_id,
        "request_id": request_id, "provider_acknowledged": True,
        "provider_control_method": "turn/start",
        "thread_response_digest": digest(thread_response), "turn_response_digest": digest(turn_response),
        "source": "BOUND_ZEUS_MANAGED_PROVIDER_CONTROL_RESPONSE",
    }
    execution_evidence["evidence_digest"] = digest(execution_evidence)
    active = {
        "schema_version": 1, "record_type": "BOUND_ACTIVE_EXECUTION", "result": "PASS",
        "mission_id": mission, "wop_id": execution.get("wop_id"), "execution_id": execution_id,
        "execution_session_id": execution.get("execution_session_id"), "provider_session_id": execution.get("provider_session_id"),
        "provider_id": execution.get("provider_id"), "provider_invocation_id": execution.get("provider_invocation_id"),
        "session_id": session["session_id"], "runtime_transaction_id": identifier("ACTIVE-EXECUTION", {"execution_id": execution_id, "session_id": session["session_id"]}),
        "authority": authority, "execution_state": "EXECUTING", "execution_monitoring_active": True,
        "mission_work_started": True, "repository_work_started": False,
        "execution_evidence": execution_evidence, "execution_evidence_digest": execution_evidence["evidence_digest"],
        "provider_process_state": "RUNNING", "provider_liveness": "ALIVE", "execution_liveness": "ALIVE",
        "session_state": "ACTIVE", "current_work_position": "P5-G6:CONTROLLED_MISSION_WORK",
        "current_gate": "P5-G6", "current_gate_name": "Execution Monitoring Foundation",
        "progress_state": "ACTIVE", "completed_work_units": [], "active_work_units": ["CONTROLLED_MISSION_WORK"],
        "remaining_work_units": [], "blockers": [], "approvals_required": [],
        "last_progress_event": "MISSION_WORK_STARTED", "last_progress_timestamp": now,
        "next_authorized_action": "CONTINUE_CONTROLLED_MISSION_WORK", "source_records": {
            "execution_start": execution.get("artifacts", {}).get("execution_start_transaction", {}).get("path"),
            "provider_session": session.get("path"), "provider_invocation_id": execution.get("provider_invocation_id"),
            "provider_control": "runtime://bound-provider-control",
        }, "source_digests": {"execution_start_provenance_baseline": execution.get("execution_start_provenance_baseline")},
        "created_at": now,
    }
    session = dict(session, state="ACTIVE", mission_work_started=True, repository_work_started=False,
                   pending_controlled_work=None,
                   execution_monitoring_active=True, active_execution_id=execution_id,
                   last_progress_event="MISSION_WORK_STARTED", last_progress_timestamp=now)
    projection = _write_projection(runtime, execution_id, active)
    try:
        saved_session = _save(runtime, session)
    except Exception as error:
        for path in (_active_path(runtime, execution_id), _monitoring_path(runtime, execution_id)):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise CodexAdapterError("ACTIVE_STATE_COMMIT_FAILED", str(error),
                                next_action="RECONCILE_EXECUTION_STATE") from error
    _append_event(runtime, session["session_id"], "MISSION_WORK_STARTED", {
        "execution_id": execution_id, "wop_id": execution.get("wop_id"), "current_work_position": active["current_work_position"]})
    result = dict(projection, result="PASS", session_id=saved_session["session_id"], replay="APPLIED",
                duplicate_execution="NO", mutation_applied=True, read_only=False)
    if session_reconciliation is not None:
        result["session_reconciliation"] = session_reconciliation
    return result


def start(repository: Path | str, mission_id: str, *, approval: bool = False,
           prompt: str | None = None, runtime_root: Path | str | None = None,
           codex_bin: str = "codex", launch: bool = True, _resume: bool = False,
           _fork_thread: bool = False) -> dict[str, Any]:
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission_id = str(mission_id).upper()
    package = _package(root, mission_id, runtime)
    existing = _existing(runtime, mission_id)
    session_id = existing.get("session_id") if existing and existing.get("session_disposition") == "CURRENT" else session_identifier(package)
    if existing:
        if existing.get("session_id") != session_id:
            raise CodexAdapterError("SESSION_INPUT_MISMATCH", "existing Codex wrapper identity differs")
        _verify_session_package_binding(existing, package)
        if _provider_control_ready(existing):
            return _result(existing, read_only=False, repository=root, runtime_root=runtime) | {
                "duplicate_codex_session": "IDEMPOTENT"}
        if not _resume:
            raise CodexAdapterError("SESSION_INTERRUPTED", "existing Codex session is not live; use Zeus resume")
        if not approval:
            raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED",
                                    "--approve is required to replace a stopped Codex transport",
                                    next_action="APPROVE_CODEX_TRANSPORT_RECOVERY")
        lifecycle = thread_lifecycle(root, existing, runtime_root=runtime)
        if lifecycle.get("thread_ownership_conflicts"):
            raise CodexAdapterError("DUPLICATE_THREAD_OWNER",
                                    "another authoritative live transport owns the native Codex thread",
                                    next_action="RESOLVE_CODEX_THREAD_OWNERSHIP_CONFLICT",
                                    details=lifecycle)
        if lifecycle.get("runtime_classification") == "THREAD_RECOVERY_BLOCKED":
            raise CodexAdapterError("THREAD_RECOVERY_BLOCKED",
                                    "native Codex thread cannot be proven readable and resumable",
                                    next_action="RECONCILE_CODEX_THREAD_RECOVERY",
                                    details=lifecycle)
        if _fork_thread and not lifecycle.get("thread_fork_supported"):
            raise CodexAdapterError("THREAD_FORK_UNSUPPORTED",
                                    "installed Codex provider does not support native thread fork")
        if _fork_thread and not lifecycle.get("thread_resume_eligible"):
            raise CodexAdapterError("THREAD_FORK_NOT_ELIGIBLE",
                                    "native thread must be valid before it can be forked",
                                    next_action="RECONCILE_CODEX_THREAD_RECOVERY")
        log_path = Path(existing["log_path"])
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, codex_bin)
        resumed = dict(existing)
        try:
            thread_id = lifecycle.get("thread_identity")
            native_thread = None
            if thread_id:
                read_response = _control_request(diagnostics.get("control_socket"), {
                    "jsonrpc": "2.0", "id": f"zeus-thread-read-{thread_id}",
                    "method": "thread/read", "params": {"threadId": thread_id, "includeTurns": False},
                })
                _validate_native_thread_response(
                    read_response, expected_thread_id=str(thread_id), repository=root,
                    expected_native_session_id=lifecycle.get("native_session_id"),
                    expected_thread_path=lifecycle.get("native_thread_path"),
                )
                method = "thread/fork" if _fork_thread else "thread/resume"
                response = _control_request(diagnostics.get("control_socket"), {
                    "jsonrpc": "2.0", "id": f"zeus-{method.replace('/', '-')}-{thread_id}",
                    "method": method, "params": {"threadId": thread_id},
                })
                native_thread = _validate_native_thread_response(
                    response, expected_thread_id=None if _fork_thread else str(thread_id),
                    repository=root, forked_from_id=str(thread_id) if _fork_thread else None,
                    expected_native_session_id=None if _fork_thread else lifecycle.get("native_session_id"),
                    expected_thread_path=None if _fork_thread else lifecycle.get("native_thread_path"),
                )
                resumed.update(native_thread)
                resumed["native_thread_resume_response_digest"] = digest(response)
                resumed["native_thread_loaded_transport_pid"] = process.pid
                resumed["native_thread_loaded_provider_pid"] = diagnostics["provider_pid"]
                if _fork_thread:
                    resumed["thread_fork_required"] = False
                    resumed["native_thread_lineage_parent_id"] = thread_id
        except Exception:
            _terminate_replacement_transport(process)
            raise
        resumed.update(state="ACTIVE" if existing.get("mission_work_started") else "READY",
                       pid=process.pid, provider_pid=diagnostics["provider_pid"],
                       command=diagnostics["command"], app_server_handshake="PASS",
                       startup_diagnostics=diagnostics["environment"],
                       control_socket=diagnostics.get("control_socket"),
                       control_socket_owner_session_id=session_id,
                       control_socket_owner_pid=process.pid,
                       broker_identity=diagnostics.get("broker_identity"),
                       provider_identity=diagnostics.get("provider_identity"),
                       remote_endpoint=diagnostics.get("remote_endpoint"),
                       execution_mode="ZEUS_MANAGED", session_mode="ZEUS_MANAGED",
                       provider_mode="APP_SERVER_MANAGED", provider_transport="STDIO",
                       remote_capable=False, readiness_result="PASS",
                       mission_work_started=bool(existing.get("mission_work_started")),
                       repository_work_started=bool(existing.get("repository_work_started")))
        saved = _save(runtime, resumed)
        _append_event(runtime, session_id, "CODEX_TRANSPORT_REPLACED", {
            "pid": process.pid, "provider_pid": diagnostics["provider_pid"]})
        if lifecycle.get("thread_identity"):
            _append_event(runtime, session_id,
                          "CODEX_THREAD_FORKED" if _fork_thread else "CODEX_THREAD_RESUMED", {
                              "thread_id_before": lifecycle.get("thread_identity"),
                              "thread_id_after": saved.get("native_thread_id"),
                              "native_lineage_preserved": True})
        return _result(saved, read_only=False, repository=root, runtime_root=runtime) | {
            "duplicate_codex_session": "FORKED" if _fork_thread else "RESUMED",
            "transport_replacement_result": "PASS",
            "thread_resume_result": "FORKED" if _fork_thread else
            "PASS" if lifecycle.get("thread_identity") else "NOT_APPLICABLE",
            "thread_id_before": lifecycle.get("thread_identity"),
            "thread_id_after": saved.get("native_thread_id"),
            "same_native_thread": bool(lifecycle.get("thread_identity")) and not _fork_thread and
            lifecycle.get("thread_identity") == saved.get("native_thread_id")}
    if package["provider_id"] != PROVIDER_ID:
        raise CodexAdapterError("PROVIDER_SUBSTITUTION", "unsupported provider identity")
    log_path = runtime / LOG_DIR / f"{session_id}.jsonl"; log_path.parent.mkdir(parents=True, exist_ok=True)
    event_directory = runtime / EVENT_DIR / session_id
    command = [codex_bin, "app-server", "--stdio"]
    session = {"schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
               **package, "session_id": session_id, "state": "CREATED", "pid": None,
               "command": command, "log_path": str(log_path), "event_directory": str(event_directory),
               "mission_work_started": False, "repository_work_started": False,
               "started_by": "zeus", "operator_approval": False, "path": str(_session_path(runtime, session_id)),
               "app_server_handshake": "NOT_RUN", "startup_diagnostics": None,
               "execution_mode": "ZEUS_MANAGED", "session_mode": "ZEUS_MANAGED",
               "provider_mode": "APP_SERVER_MANAGED", "provider_transport": "STDIO",
               "remote_capable": False, "readiness_result": "NOT_RUN"}
    _append_event(runtime, session_id, "CODEX_SESSION_CREATED", {"pid": None, "authority": package["authority"]})
    _save(runtime, session)
    try:
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, codex_bin)
    except CodexAdapterError as error:
        session["state"] = "FAILED"; session["failure"] = error.message
        _append_event(runtime, session_id, "CODEX_SESSION_FAILED", {"code": error.code, "message": error.message})
        _save(runtime, session)
        raise
    session["state"] = "READY"; session["pid"] = process.pid
    session["provider_pid"] = diagnostics["provider_pid"]
    session["command"] = diagnostics["command"]
    session["app_server_handshake"] = "PASS"
    session["startup_diagnostics"] = diagnostics["environment"]
    session["control_socket"] = diagnostics.get("control_socket")
    session["control_socket_owner_session_id"] = session_id
    session["control_socket_owner_pid"] = process.pid
    session["broker_identity"] = diagnostics.get("broker_identity")
    session["provider_identity"] = diagnostics.get("provider_identity")
    session["remote_endpoint"] = diagnostics.get("remote_endpoint")
    session["execution_mode"] = "ZEUS_MANAGED"; session["session_mode"] = "ZEUS_MANAGED"
    session["provider_mode"] = "APP_SERVER_MANAGED"; session["provider_transport"] = "STDIO"
    session["remote_capable"] = False; session["readiness_result"] = "PASS"
    session["mission_work_started"] = False; session["repository_work_started"] = False
    _append_event(runtime, session_id, "CODEX_PROCESS_BOUND", {"pid": process.pid,
                                                               "provider_pid": diagnostics["provider_pid"]})
    _append_event(runtime, session_id, "APP_SERVER_HANDSHAKE_COMPLETED", {"provider_pid": diagnostics["provider_pid"]})
    saved = _save(runtime, session)
    return _result(saved, read_only=False, repository=root, runtime_root=runtime) | {
        "duplicate_codex_session": "NEW"}


def resume(repository: Path | str, mission_id: str, *, approval: bool = False,
           runtime_root: Path | str | None = None, codex_bin: str = "codex",
           work_contract: Path | str | None = None, fork_thread: bool = False) -> dict[str, Any]:
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission_id = str(mission_id).upper(); session = _existing(runtime, mission_id)
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    contract_result = None
    if work_contract is not None:
        if not approval:
            raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for a managed work-contract continuation",
                                    next_action="APPROVE_MANAGED_WORK_CONTRACT")
        resolved = resolve_managed_runtime(root, mission_id=mission_id, selector="latest", runtime_root=runtime)
        authoritative = resolved.get("session")
        if not authoritative:
            raise CodexAdapterError("STALE_RUNTIME_BINDING", "no authoritative managed runtime exists for work-contract continuation")
        if authoritative.get("session_id") != session.get("session_id"):
            raise CodexAdapterError("STALE_RUNTIME_BINDING", "requested session is not the canonical managed runtime",
                                    details={"requested_session_id": session.get("session_id"),
                                            "canonical_session_id": authoritative.get("session_id")})
        binding = dict(authoritative)
        binding["runtime_classification"] = (resolved.get("liveness") or {}).get("runtime_classification")
        try:
            contract_result = managed_work_contract.ingest(
                work_contract, runtime=runtime, mission_id=mission_id, binding=binding,
            )
        except managed_work_contract.WorkContractError as error:
            raise CodexAdapterError(error.code, error.message, details=error.details) from error
    if _provider_control_ready(session):
        if fork_thread:
            raise CodexAdapterError("LIVE_THREAD_FORK_REQUIRES_DEDICATED_AUTHORITY",
                                    "a live authoritative thread cannot be forked through transport recovery")
        value = _result(session, read_only=False, repository=root, runtime_root=runtime) | {
            "duplicate_codex_session": "IDEMPOTENT"}
        if contract_result:
            value.update({"work_contract": contract_result, "work_contract_digest": contract_result["contract_payload_digest"],
                          "work_contract_source_digest": contract_result["source_digest"],
                          "work_contract_replay": contract_result["replay"]})
        return value
    value = start(repository, mission_id, approval=approval, runtime_root=runtime, codex_bin=codex_bin,
                 prompt="Resume the Zeus-bound controlled mission-work session. Reconcile prior state before any work; stop at the operator boundary.",
                 _resume=True, _fork_thread=fork_thread)
    if contract_result:
        value.update({"work_contract": contract_result, "work_contract_digest": contract_result["contract_payload_digest"],
                      "work_contract_source_digest": contract_result["source_digest"],
                      "work_contract_replay": contract_result["replay"]})
    return value


def stop(repository: Path | str, mission_id: str, *, approval: bool = False,
         runtime_root: Path | str | None = None) -> dict[str, Any]:
    runtime = _runtime(Path(repository).resolve(), runtime_root); session = _existing(runtime, str(mission_id).upper())
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    if _process_alive(session.get("pid")):
        try:
            os.killpg(session["pid"], signal.SIGTERM)
        except OSError as error:
            raise CodexAdapterError("SESSION_STOP_FAILED", str(error)) from error
    session = dict(session); session["state"] = "STOPPED"; session["stopped_by"] = "zeus"
    _append_event(runtime, session["session_id"], "CODEX_SESSION_STOPPED", {"pid": session.get("pid")})
    saved = _save(runtime, session)
    return _result(saved, read_only=False)


def logs(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = status(repository, mission_id, runtime_root=runtime_root)
    if value.get("state") == "NOT_STARTED":
        return value | {"logs": None}
    path = Path(value["logs"]); value["log_content"] = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    return value


def artifacts(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    return status(repository, mission_id, runtime_root=runtime_root)


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Read-only adapter verification, including the immutable package binding."""
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    session = _existing(runtime, str(mission_id).upper())
    if not session:
        return status(root, mission_id, runtime_root=runtime)
    package = _package(root, str(mission_id).upper(), runtime)
    if package["package_digest"] != session.get("package_digest"):
        raise CodexAdapterError("SESSION_INPUT_MISMATCH", "current execution package differs from Codex session binding")
    return _result(session)
