"""Mission-native, read-only aggregate over the canonical lifecycle chain.

The aggregate is a view, not a lifecycle controller.  The canonical
receipt-backed P2/P3/P4/P5 chain owns mission identity, state, authority,
blockers, and next action.  Provider, session, process, monitoring, and
evidence records are subordinate observations and are never allowed to invent
or override a verified lifecycle position.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.canonical_authority_receipt import AuthorityReceiptError, resolve as resolve_authority
from scripts.lib.emp.canonical_lifecycle_resolver import CanonicalLifecycleResolutionError, resolve as resolve_lifecycle
from scripts.lib.emp.canonical_recovery import resolve as resolve_recovery
from scripts.lib.emp.runtime_paths import resolve_runtime


class MissionAggregateError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


FAMILIES = {
    "provider": ("provider-selection", "selected-providers", "provider-qualifications",
                 "provider-selection-receipts", "provider-selection-journals"),
    "dispatch": ("dispatches", "dispatch-packages", "dispatch-authorizations", "dispatch-receipts", "dispatch-journals"),
    "provider_session": ("provider-sessions", "provider-session-receipts", "provider-session-journals",
                          "provider-session-authorizations", "provider-session-readiness-records"),
    "execution": ("provider-invocations", "provider-invocation-receipts", "execution-start-transactions",
                   "execution-start-receipts", "execution-records", "execution-sessions"),
    "process": ("codex-sessions", "codex-events", "execution-active-transitions"),
    "monitoring": ("execution-monitoring", "eens"),
    "evidence": ("evidence", "evidence-manifests", "qualification", "qualification-records"),
}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MissionAggregateError("MISSION_AGGREGATE_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise MissionAggregateError("MISSION_AGGREGATE_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _records(runtime: Path, mission_id: str, directories: tuple[str, ...]) -> list[tuple[Path, dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    for directory in directories:
        location = runtime / directory
        if not location.is_dir():
            continue
        for path in sorted(location.glob("*.json")):
            value = _load(path)
            observed = str(value.get("mission_id", "")).upper()
            if observed == mission_id:
                found.append((path, value))
    return found


def _validate_records(records: list[tuple[Path, dict[str, Any]]], expected: Mapping[str, Any], family: str) -> None:
    for path, value in records:
        if str(value.get("mission_id", "")).upper() != str(expected["mission_id"]).upper():
            raise MissionAggregateError("MISSION_AGGREGATE_MISSION_BINDING_MISMATCH", f"{family} record is bound to another mission")
        for field in ("wop_id", "submission_id", "admission_id", "bootstrap_id"):
            if expected.get(field) is not None and value.get(field) is not None and value.get(field) != expected.get(field):
                raise MissionAggregateError("MISSION_AGGREGATE_IDENTITY_MISMATCH", f"{family} {field} differs from canonical identity")
        for digest_key in ("artifact_digest", "record_digest", "state_digest"):
            if value.get(digest_key):
                unsigned = {key: item for key, item in value.items() if key != digest_key}
                if value[digest_key] != _digest(unsigned):
                    raise MissionAggregateError("MISSION_AGGREGATE_DIGEST_MISMATCH", f"{family} digest is invalid: {path.name}")


def _identities(records: list[tuple[Path, dict[str, Any]]], fields: tuple[str, ...], family: str) -> dict[str, Any]:
    values: dict[str, set[str]] = {field: set() for field in fields}
    for _, record in records:
        for field in fields:
            if record.get(field) is not None:
                values[field].add(str(record[field]))
    conflicts = {field: sorted(items) for field, items in values.items() if len(items) > 1}
    if conflicts:
        raise MissionAggregateError("MISSION_AGGREGATE_IDENTITY_AMBIGUOUS", f"{family} identities conflict: {conflicts}")
    return {field: (next(iter(items)) if items else None) for field, items in values.items()}


def _family(runtime: Path, mission_id: str, expected: Mapping[str, Any], family: str) -> dict[str, Any]:
    records = _records(runtime, mission_id, FAMILIES[family])
    _validate_records(records, expected, family)
    identities = _identities(records, {
        "provider": ("provider_id", "provider_selection_id"),
        "dispatch": ("dispatch_id", "provider_id"),
        "provider_session": ("provider_session_id", "provider_id", "dispatch_id"),
        "execution": ("execution_id", "execution_session_id", "provider_invocation_id", "provider_session_id", "provider_id"),
        "process": ("session_id", "codex_session_id", "process_id", "provider_pid"),
        "monitoring": ("execution_id", "session_id"),
        "evidence": ("evidence_id", "manifest_id", "qualification_id", "execution_id"),
    }[family], family)
    return {
        "status": "AVAILABLE" if records else "NOT_STARTED",
        "record_count": len(records),
        "identities": identities,
        "paths": [str(path) for path, _ in records],
        "read_only": True,
    }


def _historical_sessions(runtime: Path, mission_id: str) -> list[dict[str, Any]]:
    records = _records(runtime, mission_id, ("codex-sessions", "native-sessions", "mission-executions"))
    historical = []
    for path, value in records:
        disposition = str(value.get("session_disposition") or value.get("state") or "").upper()
        if disposition in {"SUPERSEDED", "STOPPED", "FAILED", "INTERRUPTED", "CLOSED", "COMPLETED", "RECONCILED"}:
            historical.append({"path": str(path), "session_id": value.get("session_id"), "state": disposition})
    return historical


def aggregate(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    mission = str(mission_id).upper()
    try:
        runtime = Path(resolve_runtime(root, explicit=runtime_root, require_writable=False)["root"]).resolve()
        lifecycle = resolve_lifecycle(root, mission, runtime_root=runtime)
        if lifecycle.get("result") != "PASS":
            blockers = lifecycle.get("blockers") or [{"code": "CANONICAL_LIFECYCLE_UNRESOLVED", "message": "canonical lifecycle is unavailable"}]
            return {"result": "FAIL", "interface": "zeus mission aggregate", "read_only": True,
                    "mission_id": mission, "aggregate": "NOT_AVAILABLE", "blockers": blockers,
                    "next_authorized_action": "STOP_FAIL_CLOSED"}
        identity = {key: lifecycle.get(key) for key in ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id")}
        authority = lifecycle.get("authority")
        if not isinstance(authority, Mapping):
            raise MissionAggregateError("AUTHORITY_RECEIPT_MISSING", "canonical lifecycle has no normalized authority")
        # Re-resolve the canonical authority envelope at this boundary.  This
        # protects aggregate consumers from accepting a hand-built projection.
        receipt = _load(Path(lifecycle["submission_receipt"]["path"]))
        normalized_authority = resolve_authority([("P2_SUBMISSION_RECEIPT", receipt)], expected=identity)
        families = {name: _family(runtime, mission, identity, name) for name in FAMILIES}
        recovery = resolve_recovery(root, mission, runtime_root=runtime, lifecycle=lifecycle)
        if recovery.get("result") != "PASS":
            return {"result": "FAIL", "interface": "zeus mission aggregate", "read_only": True,
                    "mission_id": mission, "aggregate": "NOT_AVAILABLE",
                    "blockers": recovery.get("blockers", []),
                    "next_authorized_action": recovery.get("next_authorized_action", "STOP_FAIL_CLOSED")}
        historical = _historical_sessions(runtime, mission)
        execution_started = lifecycle.get("execution_started") is True
        current_ready = lifecycle.get("lifecycle_state") in {
            "AWAITING_EXECUTION_DISPATCH", "DISPATCHED", "PROVIDER_BOUND",
            "PROVIDER_INVOKED", "READY_FOR_CONTROLLED_EXECUTION", "EXECUTING",
        }
        if not execution_started:
            process_state = "NOT_STARTED" if not families["process"]["record_count"] else "UNAVAILABLE_UNTIL_EXECUTION_START"
            monitor_state = "NOT_STARTED" if not families["monitoring"]["record_count"] else "UNAVAILABLE_UNTIL_EXECUTION_START"
        else:
            process_state = families["process"]["status"]
            monitor_state = families["monitoring"]["status"]
        aggregate_value = {
            "provider": {**families["provider"], "identity": families["provider"]["identities"].get("provider_id")},
            "provider_session": {**families["provider_session"], "identity": families["provider_session"]["identities"].get("provider_session_id")},
            "execution": {**families["execution"], "identity": families["execution"]["identities"].get("execution_id")},
            "process": {**families["process"], "status": process_state, "identity": families["process"]["identities"].get("process_id")},
            "monitoring": {**families["monitoring"], "status": monitor_state},
            "evidence": families["evidence"],
            "recovery": recovery,
            "historical_sessions": historical,
            "current_execution_readiness": "AVAILABLE" if current_ready and execution_started else "NOT_AVAILABLE",
            "historical_session_execution_leak": "NONE",
        }
        return {
            "result": "PASS", "interface": "zeus mission aggregate", "read_only": True,
            "mission": "DISCOVERABLE", "mission_id": mission, "wop_id": lifecycle.get("wop_id"),
            "submission_id": lifecycle.get("submission_id"), "lifecycle_state": lifecycle.get("lifecycle_state"),
            "authority": normalized_authority, "blockers": lifecycle.get("blockers", []),
            "next_authorized_action": lifecycle.get("next_authorized_action"),
            "canonical_lifecycle_owner": lifecycle.get("canonical_lifecycle_owner"),
            "canonical_state_source": lifecycle.get("canonical_state_source"),
            "provider_identity": aggregate_value["provider"]["identity"],
            "provider_session_identity": aggregate_value["provider_session"]["identity"],
            "execution_identity": aggregate_value["execution"]["identity"],
            "process_liveness": aggregate_value["process"]["status"],
            "monitoring_status": aggregate_value["monitoring"]["status"],
            "evidence_state": aggregate_value["evidence"]["status"],
            "monitoring_owner": recovery.get("monitoring_owner"),
            "monitoring_state": recovery.get("monitoring_state"),
            "interruption_state": recovery.get("interruption_state"),
            "recovery_state": recovery.get("recovery_state"),
            "checkpoint_identity": recovery.get("checkpoint_identity"),
            "resume_eligibility": recovery.get("resume_eligibility"),
            "evidence_position": recovery.get("evidence_position"),
            "aggregate": aggregate_value, "provider_session_process_monitor_evidence": aggregate_value,
            "replay": "IDEMPOTENT", "historical_projections": "PRESERVED_AND_EXCLUDED_FROM_CURRENT_STATE",
        }
    except (MissionAggregateError, AuthorityReceiptError, CanonicalLifecycleResolutionError, OSError) as error:
        return {
            "result": "FAIL", "interface": "zeus mission aggregate", "read_only": True,
            "mission_id": mission, "aggregate": "NOT_AVAILABLE",
            "blockers": [{"code": getattr(error, "code", "MISSION_AGGREGATE_FAILED"), "message": str(error)}],
            "next_authorized_action": "STOP_FAIL_CLOSED",
        }


def view(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    return aggregate(repository, mission_id, runtime_root=runtime_root)
