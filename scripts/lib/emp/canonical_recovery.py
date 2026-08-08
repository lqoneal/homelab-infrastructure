"""Receipt-backed monitoring, interruption, checkpoint, and resume contract.

This module is deliberately a bounded recovery boundary, not a second
lifecycle controller.  The canonical P2/P3/P4 chain remains the owner of
mission lifecycle state.  Recovery records describe an execution that has
already started and are accepted only when every identity and digest binding
can be reconstructed.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.canonical_lifecycle_resolver import resolve as resolve_lifecycle


CONTRACT = {"id": "ZEUS-CANONICAL-RECOVERY", "version": "1"}
CHECKPOINT_DIR = "recovery-checkpoints"
INTERRUPTION_DIR = "recovery-interruptions"
RESUME_DIR = "recovery-resumes"
_IDENTITY_FIELDS = (
    "mission_id", "wop_id", "execution_id", "provider_id", "session_id",
    "repository_identity", "repository_baseline", "source_digest",
)
_ALLOWED_CAUSES = {
    "provider_process_died", "codex_session_died", "heartbeat_expired",
    "session_record_without_process", "unbound_process", "repository_mismatch",
    "assignment_mismatch", "operator_interrupt", "unknown_runtime_failure",
}
_TERMINAL_CHECKPOINTS = {"COMPLETED", "SUPERSEDED", "RECONCILED", "FAILED", "STALE"}


class RecoveryError(ValueError):
    """Recovery evidence is missing, stale, ambiguous, or contradictory."""

    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code = code
        self.message = message
        self.next_action = next_action
        super().__init__(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _unsigned(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError("RECOVERY_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise RecoveryError("RECOVERY_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _require(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if not isinstance(value.get(field), str) or not value[field].strip()]
    if missing:
        raise RecoveryError("RECOVERY_IDENTITY_INCOMPLETE", f"{label} is missing: {', '.join(missing)}")


def _same_identity(expected: Mapping[str, Any], observed: Mapping[str, Any], label: str) -> None:
    mismatches = [field for field in _IDENTITY_FIELDS
                  if expected.get(field) is not None and observed.get(field) != expected.get(field)]
    if mismatches:
        raise RecoveryError("RECOVERY_IDENTITY_MISMATCH", f"{label} differs for: {', '.join(mismatches)}")


def _atomic_create(path: Path, value: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = dict(value)
    if path.exists():
        existing = _load(path)
        if existing != candidate:
            raise RecoveryError("RECOVERY_REPLAY_DIVERGED", f"immutable recovery record differs: {path}")
        return existing, False
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(candidate, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            existing = _load(path)
            if existing != candidate:
                raise RecoveryError("RECOVERY_REPLAY_DIVERGED", f"immutable recovery record differs: {path}")
            return existing, False
        return candidate, True
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _validate_checkpoint(value: Mapping[str, Any], *, expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if value.get("contract") != CONTRACT or value.get("record_type") != "RECOVERY_CHECKPOINT":
        raise RecoveryError("CHECKPOINT_CONTRACT_INVALID", "checkpoint contract is not canonical")
    supplied = value.get("checkpoint_digest")
    if supplied != digest(_unsigned(value, "checkpoint_digest")):
        raise RecoveryError("CHECKPOINT_DIGEST_MISMATCH", "checkpoint digest is invalid")
    _require(value, _IDENTITY_FIELDS, "checkpoint identity")
    if expected:
        _same_identity(expected, value, "checkpoint")
    if value.get("checkpoint_status") not in {"RESUMABLE", "COMPLETED", "SUPERSEDED", "RECONCILED", "FAILED", "STALE"}:
        raise RecoveryError("CHECKPOINT_STATE_INVALID", "checkpoint status is invalid")
    completed = value.get("completed_work_units")
    if not isinstance(completed, list) or len(completed) != len(set(completed)):
        raise RecoveryError("CHECKPOINT_WORK_POSITION_INVALID", "completed work position is not deterministic")
    current = value.get("current_work_units", [])
    if not isinstance(current, list) or set(completed) & set(current):
        raise RecoveryError("CHECKPOINT_WORK_POSITION_INVALID", "current work overlaps completed work")
    for field in ("lifecycle_position", "evidence_position"):
        if not isinstance(value.get(field), Mapping):
            raise RecoveryError("CHECKPOINT_POSITION_MISSING", f"checkpoint {field} is missing")
    return dict(value)


def create_checkpoint(runtime_root: Path | str, *, mission_id: str, wop_id: str,
                       execution_id: str, provider_id: str, session_id: str,
                       repository_identity: str, repository_baseline: str,
                       source_digest: str, lifecycle_position: Mapping[str, Any],
                       evidence_position: Mapping[str, Any],
                       completed_work_units: list[str],
                       current_work_units: list[str] | None = None,
                       checkpoint_status: str = "RESUMABLE") -> dict[str, Any]:
    """Create one immutable, deterministic checkpoint or return its replay."""
    material = {
        "mission_id": mission_id, "wop_id": wop_id, "execution_id": execution_id,
        "provider_id": provider_id, "session_id": session_id,
        "repository_identity": repository_identity, "repository_baseline": repository_baseline,
        "source_digest": source_digest, "lifecycle_position": deepcopy(dict(lifecycle_position)),
        "evidence_position": deepcopy(dict(evidence_position)),
        "completed_work_units": list(completed_work_units),
        "current_work_units": list(current_work_units or []),
        "checkpoint_status": checkpoint_status,
    }
    _require(material, _IDENTITY_FIELDS, "checkpoint identity")
    if checkpoint_status not in {"RESUMABLE", "COMPLETED", "SUPERSEDED", "RECONCILED", "FAILED", "STALE"}:
        raise RecoveryError("CHECKPOINT_STATE_INVALID", "checkpoint status is invalid")
    checkpoint_id = "CHECKPOINT-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))
    value = {"contract": CONTRACT, "record_type": "RECOVERY_CHECKPOINT",
             "checkpoint_id": checkpoint_id, **material}
    value["checkpoint_digest"] = digest(value)
    _validate_checkpoint(value)
    record, inserted = _atomic_create(Path(runtime_root) / CHECKPOINT_DIR / f"{checkpoint_id}.json", value)
    return {"result": "PASS", "checkpoint": record, "checkpoint_id": checkpoint_id,
            "checkpoint_replay": "NEW" if inserted else "IDEMPOTENT", "read_only": False}


def record_interruption(runtime_root: Path | str, *, checkpoint_id: str, cause: str,
                        observed_at: str, provider_process_state: str,
                        session_process_state: str, heartbeat_expired: bool = False,
                        repository_mutation_state: str = "UNKNOWN",
                        lifecycle_receipt_state: str = "UNKNOWN") -> dict[str, Any]:
    """Persist a deterministic interruption receipt bound to one checkpoint."""
    if cause not in _ALLOWED_CAUSES:
        raise RecoveryError("INTERRUPTION_CAUSE_INVALID", f"unsupported interruption cause: {cause}")
    checkpoint_path = Path(runtime_root) / CHECKPOINT_DIR / f"{checkpoint_id}.json"
    checkpoint = _validate_checkpoint(_load(checkpoint_path))
    if checkpoint["checkpoint_status"] in _TERMINAL_CHECKPOINTS:
        raise RecoveryError("CHECKPOINT_NOT_RESUMABLE", "terminal checkpoint cannot receive interruption")
    order = "MUTATION_BEFORE_RECEIPT" if repository_mutation_state == "MUTATED" and lifecycle_receipt_state == "ABSENT" else \
        "RECEIPT_BEFORE_MUTATION" if repository_mutation_state == "ABSENT" and lifecycle_receipt_state == "PERSISTED" else \
        "BOTH_PRESENT" if repository_mutation_state == "MUTATED" and lifecycle_receipt_state == "PERSISTED" else "UNRESOLVED"
    material = {
        "contract": CONTRACT, "record_type": "RECOVERY_INTERRUPTION_RECEIPT",
        "checkpoint_id": checkpoint_id, "mission_id": checkpoint["mission_id"],
        "wop_id": checkpoint["wop_id"], "execution_id": checkpoint["execution_id"],
        "provider_id": checkpoint["provider_id"], "session_id": checkpoint["session_id"],
        "repository_identity": checkpoint["repository_identity"],
        "repository_baseline": checkpoint["repository_baseline"],
        "source_digest": checkpoint["source_digest"], "cause": cause,
        "observed_at": observed_at, "provider_process_state": provider_process_state,
        "session_process_state": session_process_state, "heartbeat_expired": bool(heartbeat_expired),
        "repository_mutation_state": repository_mutation_state,
        "lifecycle_receipt_state": lifecycle_receipt_state,
        "mutation_receipt_order": order, "interruption_state": "INTERRUPTED",
    }
    interruption_id = "INTERRUPTION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))
    value = {**material, "interruption_id": interruption_id}
    value["interruption_digest"] = digest(value)
    path = Path(runtime_root) / INTERRUPTION_DIR / f"{interruption_id}.json"
    record, inserted = _atomic_create(path, value)
    return {"result": "PASS", "interruption": record, "interruption_id": interruption_id,
            "interruption_replay": "NEW" if inserted else "IDEMPOTENT", "read_only": False}


def _records(runtime: Path, directory: str, mission_id: str) -> list[tuple[Path, dict[str, Any]]]:
    location = runtime / directory
    if not location.is_dir():
        return []
    result = []
    for path in sorted(location.glob("*.json")):
        value = _load(path)
        if str(value.get("mission_id", "")).upper() == mission_id.upper():
            result.append((path, value))
    return result


def resolve(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
            execution_id: str | None = None, expected: Mapping[str, Any] | None = None,
            lifecycle: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Resolve monitoring/recovery without changing the canonical lifecycle."""
    root = Path(repository).resolve()
    mission = str(mission_id).upper()
    try:
        runtime = Path(runtime_root).resolve() if runtime_root is not None else None
        lifecycle_value = dict(lifecycle) if lifecycle is not None else resolve_lifecycle(root, mission, runtime_root=runtime)
        if lifecycle_value.get("result") != "PASS":
            return {"result": "FAIL", "read_only": True, "mission_id": mission,
                    "recovery_state": "UNAVAILABLE", "blockers": lifecycle_value.get("blockers", []),
                    "next_authorized_action": "STOP_FAIL_CLOSED"}
        if runtime is None:
            from scripts.lib.emp.runtime_paths import resolve_runtime
            runtime = Path(resolve_runtime(root, require_writable=False)["root"]).resolve()
        canonical_identity = {field: lifecycle_value.get(field) for field in ("mission_id", "wop_id", "submission_id")}
        lifecycle_binding = {field: lifecycle_value.get(field) for field in
                             ("repository_identity", "repository_baseline", "source_digest")
                             if lifecycle_value.get(field) is not None}
        checkpoint_expected = {**canonical_identity, **lifecycle_binding, **(expected or {})}
        if expected:
            _same_identity(expected, lifecycle_value, "canonical lifecycle")
        candidates = _records(runtime, CHECKPOINT_DIR, mission)
        checkpoints = [_validate_checkpoint(value, expected=checkpoint_expected) for _, value in candidates]
        if execution_id:
            matching = [value for value in checkpoints if value.get("execution_id") == execution_id]
            if not matching:
                raise RecoveryError("RECOVERY_EXECUTION_NOT_FOUND", "requested execution has no identity-bound checkpoint")
            checkpoints = matching
        if not checkpoints:
            return {
                "result": "PASS", "read_only": True, "mission_id": mission,
                "monitoring_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
                "monitoring_state": "NOT_STARTED",
                "recovery_state": "NOT_STARTED", "interruption_state": "NOT_STARTED",
                "checkpoint_identity": None, "checkpoint_count": 0,
                "resume_eligibility": "NOT_AVAILABLE", "resume_execution_id": None,
                "completed_work_units": [], "evidence_position": None,
                "provider_session_liveness": "NOT_STARTED",
                "blockers": [], "next_authorized_action": lifecycle_value.get("next_authorized_action"),
                "replay": "IDEMPOTENT", "read_only_projection": True,
            }
        if len(checkpoints) != 1:
            raise RecoveryError("CHECKPOINT_CARDINALITY_CONFLICT", f"{len(checkpoints)} checkpoints resolve for {mission}")
        checkpoint = checkpoints[0]
        if lifecycle_value.get("execution_started") is not True:
            raise RecoveryError("CHECKPOINT_BEFORE_EXECUTION_START", "checkpoint exists before canonical execution start")
        if checkpoint["checkpoint_status"] == "STALE":
            raise RecoveryError("CHECKPOINT_STALE", "checkpoint is stale and cannot be resumed")
        if checkpoint["checkpoint_status"] in _TERMINAL_CHECKPOINTS:
            return {"result": "PASS", "read_only": True, "mission_id": mission,
                    "monitoring_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
                    "monitoring_state": "HISTORICAL",
                    "recovery_state": "HISTORICAL", "interruption_state": "RECONCILED",
                    "checkpoint_identity": checkpoint["checkpoint_id"], "checkpoint_count": 1,
                    "resume_eligibility": "NO", "resume_execution_id": None,
                    "completed_work_units": checkpoint["completed_work_units"],
                    "evidence_position": checkpoint["evidence_position"], "provider_session_liveness": "HISTORICAL",
                    "blockers": [{"code": "CHECKPOINT_NOT_RESUMABLE", "message": "historical checkpoint is not reusable"}],
                    "next_authorized_action": "RECONCILE_EXECUTION_STATE", "replay": "IDEMPOTENT", "read_only_projection": True}
        interruptions = _records(runtime, INTERRUPTION_DIR, mission)
        relevant = [value for _, value in interruptions if value.get("checkpoint_id") == checkpoint["checkpoint_id"]]
        for interruption in relevant:
            if interruption.get("interruption_digest") != digest(_unsigned(interruption, "interruption_digest")):
                raise RecoveryError("INTERRUPTION_DIGEST_MISMATCH", "interruption receipt digest is invalid")
            _same_identity(checkpoint, interruption, "interruption")
        if len(relevant) > 1 and len({item.get("interruption_id") for item in relevant}) != len(relevant):
            raise RecoveryError("INTERRUPTION_CARDINALITY_CONFLICT", "duplicate interruption identities resolve")
        return {
            "result": "PASS", "read_only": True, "mission_id": mission,
            "monitoring_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
            "monitoring_state": "INTERRUPTED" if relevant else "CHECKPOINTED",
            "recovery_state": "INTERRUPTED" if relevant else "CHECKPOINTED",
            "interruption_state": relevant[-1].get("interruption_state") if relevant else "NOT_RECORDED",
            "checkpoint_identity": checkpoint["checkpoint_id"], "checkpoint_count": 1,
            "resume_eligibility": "READY" if relevant else "NOT_AVAILABLE",
            "resume_execution_id": checkpoint["execution_id"],
            "completed_work_units": checkpoint["completed_work_units"],
            "current_work_units": checkpoint["current_work_units"],
            "evidence_position": checkpoint["evidence_position"],
            "provider_session_liveness": "OBSERVATIONAL_ONLY",
            "interruption_receipts": relevant, "checkpoint": checkpoint,
            "blockers": [], "next_authorized_action": "RESUME_FROM_CHECKPOINT" if relevant else "RECONCILE_EXECUTION_STATE",
            "replay": "IDEMPOTENT", "read_only_projection": True,
        }
    except RecoveryError as error:
        return {"result": "FAIL", "read_only": True, "mission_id": mission,
                "recovery_state": "UNAVAILABLE", "blockers": [{"code": error.code, "message": error.message}],
                "next_authorized_action": error.next_action, "read_only_projection": True}


def request_resume(runtime_root: Path | str, *, resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Create an idempotent resume request; no provider or mission work runs."""
    if resolved.get("result") != "PASS" or resolved.get("resume_eligibility") != "READY":
        raise RecoveryError("RESUME_NOT_ELIGIBLE", "resume requires one verified interrupted checkpoint")
    checkpoint = resolved.get("checkpoint")
    if not isinstance(checkpoint, Mapping):
        raise RecoveryError("CHECKPOINT_MISSING", "resume checkpoint is unavailable")
    material = {
        "contract": CONTRACT, "record_type": "RECOVERY_RESUME_REQUEST",
        "checkpoint_id": checkpoint["checkpoint_id"], "mission_id": checkpoint["mission_id"],
        "wop_id": checkpoint["wop_id"], "execution_id": checkpoint["execution_id"],
        "provider_id": checkpoint["provider_id"], "session_id": checkpoint["session_id"],
        "repository_baseline": checkpoint["repository_baseline"], "source_digest": checkpoint["source_digest"],
        "resume_execution_id": checkpoint["execution_id"],
        "completed_work_units_skipped": checkpoint["completed_work_units"],
        "resume_state": "READY", "duplicate_execution_prevented": True,
        "execution_identity_preserved": True,
    }
    resume_id = "RESUME-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))
    value = {**material, "resume_id": resume_id}
    value["resume_digest"] = digest(value)
    record, inserted = _atomic_create(Path(runtime_root) / RESUME_DIR / f"{resume_id}.json", value)
    return {"result": "PASS", "resume": record, "resume_id": resume_id,
            "resume_replay": "NEW" if inserted else "IDEMPOTENT", "read_only": False}


def view(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
         lifecycle: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return resolve(repository, mission_id, runtime_root=runtime_root, lifecycle=lifecycle)
