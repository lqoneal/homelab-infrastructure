"""Zeus-owned autonomous mission lifecycle projection.

Stage 1 receipts remain immutable authority.  This service owns only a
derived, transaction-scoped lifecycle ledger and its read-only projections.
It deliberately stops at policy boundaries (publication approval, external
credentials, physical actions, and EOS mutation) and is safe to replay.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Store


class AutonomousDeliveryError(ValueError):
    """The autonomous lifecycle cannot be resolved to one lawful state."""


PHASES = (
    "SOURCE_DISCOVERED", "SOURCE_VALIDATED", "PACKAGE_CREATED", "PACKAGE_VERIFIED",
    "PACKAGE_REGISTERED", "AUTHORITY_RESOLVED", "MISSION_ADMITTED", "ADMISSION_PERSISTED",
    "ADMISSION_VERIFIED", "PROVIDER_SELECTED", "DISPATCHED", "EXECUTION_CREATED",
    "EXECUTION_PERSISTED", "EXECUTION_VERIFIED", "SESSION_CREATED", "EXECUTION_STARTED",
    "EXECUTION_MONITORED", "SELF_DIAGNOSIS", "AUTONOMOUS_CORRECTION", "RECONCILIATION",
    "RESUME", "QUALIFICATION", "PUBLICATION_PREPARATION", "PUBLICATION_APPROVAL",
    "PUBLICATION", "EOS_SYNCHRONIZATION", "MISSION_CLOSEOUT",
)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(dict(value), stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def _lock(runtime_root: Path, transaction_id: str):
    path = runtime_root / "autonomous-lifecycle" / "locks" / f"{transaction_id}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def _phase(record: Mapping[str, Any], admission_exists: bool, execution_exists: bool) -> str:
    state = record.get("state")
    if state == "CLOSED":
        return "MISSION_CLOSEOUT"
    if state == "SYNCHRONIZED":
        return "EOS_SYNCHRONIZATION"
    if state == "PUBLISHED":
        return "PUBLICATION"
    if state == "QUALIFIED":
        return "QUALIFICATION"
    if execution_exists:
        return "EXECUTION_VERIFIED"
    if admission_exists:
        return "ADMISSION_VERIFIED"
    if state in {"DISPATCHED", "EXECUTING", "QUALIFYING", "BLOCKED"}:
        return "DISPATCHED"
    return str(state or "SOURCE_DISCOVERED")


def _find(store: Stage1Store, identifier: str | None) -> dict[str, Any]:
    records = store.all()
    if identifier:
        matches = [item for item in records if identifier in {
            item.get("instance_id"), item.get("mission_id"), item.get("wop_id")
        }]
    else:
        matches = [item for item in records if item.get("state") not in {"CLOSED", "REJECTED"}]
    if len(matches) != 1:
        raise AutonomousDeliveryError(
            f"autonomous lifecycle identity resolved {len(matches)} transactions: {identifier or 'active'}"
        )
    return matches[0]


def _load_projection(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AutonomousDeliveryError(f"CORRUPTED_RECORD: {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise AutonomousDeliveryError(f"CORRUPTED_RECORD: {path.name}")
    return value


def reconcile(root: Path | str, stage1_directory: Path | str, runtime_root: Path | str,
              *, identifier: str | None = None, command: str = "status") -> dict[str, Any]:
    """Reconcile one submitted transaction into a durable lifecycle snapshot."""
    root = Path(root).resolve()
    runtime_root = Path(runtime_root).resolve()
    record = _find(Stage1Store(stage1_directory), identifier)
    transaction_id = str(record["instance_id"])
    with _lock(runtime_root, transaction_id):
        admission_id = ((record.get("receipts") or {}).get("admission") or {}).get("admission_id")
        admission = _load_projection(runtime_root / "mission-admissions" / f"{admission_id}.json") if admission_id else None
        execution = _load_projection(runtime_root / "mission-executions" / f"{transaction_id}.json")
        runtime_summary = record.get("runtime_reconciliation") or {}
        reconciliation_error = None
        if (not admission or not execution) and (record.get("receipts") or {}).get("dispatch"):
            try:
                from scripts.lib.emp.runtime_reconciliation import reconcile as reconcile_runtime
                runtime_result = reconcile_runtime(
                    root, stage1_directory, runtime_root / "mission-admissions",
                    runtime_root / "mission-executions", command=f"autonomous:{command}",
                    execution_id=transaction_id,
                )
                runtime_summary = runtime_result.get("reconciliation", runtime_summary)
                admission = _load_projection(runtime_root / "mission-admissions" / f"{runtime_result['admission_id']}.json")
                execution = _load_projection(runtime_root / "mission-executions" / f"{transaction_id}.json")
                admission_id = runtime_result["admission_id"]
            except (OSError, ValueError) as error:
                reconciliation_error = str(error)
        blockers: list[dict[str, Any]] = []
        if record.get("state") == "BLOCKED":
            blockers.append({"code": (record.get("failure") or {}).get("classification", "TRANSACTION_BLOCKED"), "detail": (record.get("failure") or {}).get("message", "Stage 1 transaction is blocked")})
        if not admission or not execution:
            blockers.append({"code": "RUNTIME_PROJECTION_INCOMPLETE", "detail": "admission and execution projections must be reconciled before autonomous continuation"})
        if reconciliation_error:
            blockers.append({"code": "RUNTIME_RECONCILIATION_FAILED", "detail": reconciliation_error})
        publication_boundary = record.get("state") in {"QUALIFIED", "PUBLICATION_READY"}
        if publication_boundary and not record.get("receipts", {}).get("publication"):
            blockers.append({"code": "PUBLICATION_AUTHORITY_BOUNDARY", "detail": "publication requires the governed publication workflow"})
        phase = _phase(record, admission is not None, execution is not None)
        if blockers:
            next_action = "Resolve blockers through the governed Zeus lifecycle; no resubmission is required."
            classification = "BLOCKED"
        elif phase in {"DISPATCHED", "EXECUTION_VERIFIED"}:
            next_action = f"Continue autonomous execution for {transaction_id}; provider launch and gate policy remain receipt-bound."
            classification = "READY_FOR_AUTONOMOUS_CONTINUATION"
        else:
            next_action = "Continue through the next receipt-backed lifecycle phase."
            classification = "ALREADY_CANONICAL"
        unsigned = {
            "schema_version": 1, "record_type": "ZEUS_AUTONOMOUS_MISSION_LIFECYCLE",
            "transaction_id": transaction_id, "mission_id": record.get("mission_id"),
            "wop_id": record.get("wop_id"), "command": command,
            "repository": str(root), "repository_baseline": record.get("repository_baseline"),
            "phase": phase, "phases": list(PHASES[:PHASES.index(phase) + 1]) if phase in PHASES else [phase],
            "classification": classification, "blockers": blockers,
            "admission_id": admission_id, "execution_id": transaction_id,
            "session_id": (execution or {}).get("session_id"),
            "authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest"),
            "package_digest": record.get("package_digest"), "source_digest": record.get("source_digest"),
            "provider_id": ((record.get("receipts") or {}).get("dispatch") or {}).get("provider_id"),
            "dispatch_receipt_id": ((record.get("receipts") or {}).get("dispatch") or {}).get("receipt_id"),
            "runtime_reconciliation": runtime_summary,
            "derived_records": {"admission": bool(admission), "execution": bool(execution)},
            "immutable_authority": {"stage1": transaction_id, "receipts_preserved": True},
            "next_authorized_action": next_action, "updated_at": _now(),
        }
        if existing := _load_projection(runtime_root / "autonomous-lifecycle" / "transactions" / f"{transaction_id}.json"):
            prior = dict(existing)
            prior.pop("state_digest", None)
            candidate = dict(unsigned)
            candidate.pop("updated_at", None)
            prior_without_time = dict(prior)
            prior_without_time.pop("updated_at", None)
            if candidate == prior_without_time:
                unsigned["updated_at"] = prior.get("updated_at", unsigned["updated_at"])
        snapshot = {**unsigned, "state_digest": _digest(unsigned)}
        path = runtime_root / "autonomous-lifecycle" / "transactions" / f"{transaction_id}.json"
        existing = _load_projection(path)
        replayed = existing == snapshot
        if not replayed:
            _atomic(path, snapshot)
        return {"result": "PASS", "replayed": replayed, "snapshot": snapshot,
                "snapshot_path": str(path), "receipt_backed": True}


def status(root: Path | str, stage1_directory: Path | str, runtime_root: Path | str, identifier: str | None = None) -> dict[str, Any]:
    return reconcile(root, stage1_directory, runtime_root, identifier=identifier, command="status")


def blockers(root: Path | str, stage1_directory: Path | str, runtime_root: Path | str, identifier: str | None = None) -> dict[str, Any]:
    return reconcile(root, stage1_directory, runtime_root, identifier=identifier, command="blockers")["snapshot"]


def next_action(root: Path | str, stage1_directory: Path | str, runtime_root: Path | str, identifier: str | None = None) -> dict[str, Any]:
    return reconcile(root, stage1_directory, runtime_root, identifier=identifier, command="next")["snapshot"]


def snapshot(root: Path | str, stage1_directory: Path | str, runtime_root: Path | str, identifier: str | None = None) -> dict[str, Any]:
    return reconcile(root, stage1_directory, runtime_root, identifier=identifier, command="snapshot")["snapshot"]
