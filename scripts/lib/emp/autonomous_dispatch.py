#!/usr/bin/env python3
"""Receipt-backed autonomous dispatch and provider-launch reconciliation.

The dispatch receipt is immutable authority.  This module owns only derived
launch/session state and requires an injected provider adapter to perform an
actual launch.  An absent adapter is a fail-closed blocker, never an implicit
acknowledgement.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Mapping

from scripts.lib.emp.canonical_authority_receipt import AuthorityReceiptError, normalize as normalize_authority


class AutonomousDispatchError(ValueError):
    """Dispatch cannot be reconciled to one lawful provider/session state."""


LAUNCH_STATES = (
    "DISPATCHED", "LAUNCH_PREPARED", "LAUNCH_REQUESTED", "PROVIDER_STARTING",
    "PROVIDER_ACKNOWLEDGED", "SESSION_MATERIALIZED", "SESSION_VERIFIED",
    "EXECUTING", "LAUNCH_BLOCKED", "LAUNCH_RETRYING", "LAUNCH_FAILED",
    "FAILOVER_PENDING", "ROLLBACK_REQUIRED", "TERMINATED",
)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _launch_id(transaction_id: str, dispatch_digest: str, provider_id: str) -> str:
    return "ZEUS-LAUNCH-" + str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps({
        "transaction_id": transaction_id, "dispatch_digest": dispatch_digest,
        "provider_id": provider_id,
    }, sort_keys=True, separators=(",", ":"))))


@contextmanager
def _lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


class LaunchStore:
    """Atomic launch journal; one terminal launch per Stage 1 transaction."""

    def __init__(self, root: Path | str):
        self.root = Path(root) / "autonomous-dispatch"
        self.journal = self.root / "launches.json"
        self.lock = self.root / "launch.lock"

    def load(self) -> dict[str, Any]:
        if not self.journal.exists():
            return {"schema_version": 1, "transactions": {}}
        try:
            value = json.loads(self.journal.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AutonomousDispatchError(f"launch journal is invalid: {error}") from error
        if not isinstance(value, dict) or not isinstance(value.get("transactions"), dict):
            raise AutonomousDispatchError("launch journal shape is invalid")
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        descriptor, raw = tempfile.mkstemp(dir=self.root, prefix=".launches.")
        temporary = Path(raw)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(dict(value), stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.journal)
        finally:
            temporary.unlink(missing_ok=True)


class AutonomousDispatchController:
    """Prepare, launch, verify, and replay one provider/session binding."""

    def __init__(self, store: LaunchStore, *, max_retries: int = 2):
        self.store = store
        self.max_retries = max_retries

    @staticmethod
    def _validate(authoritative: Mapping[str, Any]) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
        transaction_id = authoritative.get("instance_id") or authoritative.get("transaction_id")
        receipts = authoritative.get("receipts") or {}
        dispatch = receipts.get("dispatch")
        selection = receipts.get("provider_selection")
        if not transaction_id or not isinstance(dispatch, Mapping) or not isinstance(selection, Mapping):
            raise AutonomousDispatchError("DISPATCH_NOT_READY: dispatch and provider-selection receipts are required")
        required = ("receipt_id", "receipt_digest", "instance_id", "provider_id", "agent_id", "authority_snapshot_digest")
        missing = [field for field in required if not dispatch.get(field)]
        if missing:
            raise AutonomousDispatchError("DISPATCH_NOT_READY: missing dispatch fields: " + ", ".join(missing))
        if dispatch.get("instance_id") != transaction_id or selection.get("transaction_id") != transaction_id:
            raise AutonomousDispatchError("DIVERGENT_DISPATCH_TRANSACTION_IDENTITY")
        if selection.get("provider_id") != dispatch.get("provider_id") or selection.get("agent_id") != dispatch.get("agent_id"):
            raise AutonomousDispatchError("DIVERGENT_PROVIDER_BINDING")
        snapshot = (authoritative.get("authority_snapshot") or {}).get("authority_snapshot_digest")
        if dispatch.get("authority_snapshot_digest") != snapshot:
            raise AutonomousDispatchError("DIVERGENT_AUTHORITY_BINDING")
        try:
            normalized = normalize_authority(authoritative, source="AUTONOMOUS_DISPATCH")
        except AuthorityReceiptError as error:
            raise AutonomousDispatchError(f"AUTHORITY_RECEIPT_REJECTED:{error.code}") from error
        if normalized.get("authority_snapshot_digest") != snapshot:
            raise AutonomousDispatchError("DIVERGENT_AUTHORITY_RECEIPT")
        if authoritative.get("execution_mode") == "DEVELOPMENT" and authoritative.get("effect_profile", "").startswith("PRODUCTION"):
            raise AutonomousDispatchError("UNAUTHORIZED_EFFECT_PROFILE")
        return str(transaction_id), dispatch, selection

    def reconcile(
        self,
        authoritative: Mapping[str, Any],
        *,
        command: str = "submit",
        provider_launcher: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        session_materializer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        cleanup: Callable[[Mapping[str, Any]], None] | None = None,
        policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        transaction_id, dispatch, selection = self._validate(authoritative)
        provider_id = str(dispatch["provider_id"])
        dispatch_digest = str(dispatch["receipt_digest"])
        launch_id = _launch_id(transaction_id, dispatch_digest, provider_id)
        with _lock(self.store.lock):
            journal = self.store.load()
            previous = journal["transactions"].get(transaction_id)
            if previous and previous.get("launch_id") != launch_id:
                raise AutonomousDispatchError("DIVERGENT_LAUNCH_IDENTITY")
            if previous and previous.get("state") in {"EXECUTING", "SESSION_VERIFIED"}:
                return {**deepcopy(previous), "replay": True, "command": command}
            base = {
                "schema_version": 1, "launch_id": launch_id,
                "transaction_id": transaction_id, "wop_id": authoritative.get("wop_id"),
                "mission_id": authoritative.get("mission_id"), "provider_id": provider_id,
                "agent_id": dispatch["agent_id"], "dispatch_receipt_id": dispatch["receipt_id"],
                "dispatch_receipt_digest": dispatch_digest,
                "authority_snapshot_digest": dispatch["authority_snapshot_digest"],
                "state": "LAUNCH_PREPARED", "attempts": 0, "replay": False,
                "records_created": [], "records_preserved": [transaction_id, dispatch["receipt_id"]],
                "blockers": [], "next_authorized_action": "Launch the qualified provider adapter.",
            }
            if provider_launcher is None:
                base.update(state="LAUNCH_BLOCKED", blockers=["PROVIDER_LAUNCH_ADAPTER_UNAVAILABLE"],
                            next_authorized_action="Configure the qualified provider launch adapter; do not acknowledge launch manually.")
                base["receipt_id"] = "ZEUS-RECEIPT-LAUNCH-BLOCKED-" + _digest(base)[:24]
                base["receipt_digest"] = _digest(base)
                journal["transactions"][transaction_id] = base
                self.store.save(journal)
                return base

            attempts = 0
            result: Mapping[str, Any] | None = None
            failures: list[dict[str, Any]] = []
            while attempts <= self.max_retries:
                attempts += 1
                try:
                    candidate = provider_launcher({**base, "attempt": attempts, "provider": dict(selection)})
                    if not isinstance(candidate, Mapping) or candidate.get("acknowledged") is not True:
                        raise AutonomousDispatchError("LAUNCH_ACKNOWLEDGMENT_INVALID")
                    for field in ("process_id", "process_group_id", "health_digest"):
                        if not candidate.get(field):
                            raise AutonomousDispatchError("LAUNCH_ACKNOWLEDGMENT_INCOMPLETE: " + field)
                    result = candidate
                    break
                except Exception as error:
                    failures.append({"attempt": attempts, "error": str(error)})
                    if attempts <= self.max_retries:
                        base["state"] = "LAUNCH_RETRYING"
            if result is None:
                base.update(state="LAUNCH_FAILED", attempts=attempts, failures=failures,
                            blockers=["PROVIDER_LAUNCH_RETRY_EXHAUSTED"],
                            next_authorized_action="Preserve launch diagnostics and apply only an authorized provider policy.")
                base["receipt_id"] = "ZEUS-RECEIPT-LAUNCH-FAILED-" + _digest(base)[:24]
                base["receipt_digest"] = _digest(base)
                journal["transactions"][transaction_id] = base
                self.store.save(journal)
                return base

            session = None
            try:
                if session_materializer is not None:
                    session = dict(session_materializer({**base, **result}))
                if not session or session.get("execution_id") != transaction_id or not session.get("session_id"):
                    raise AutonomousDispatchError("SESSION_MATERIALIZATION_INVALID")
            except Exception:
                if cleanup is not None:
                    cleanup(result)
                base.update(state="ROLLBACK_REQUIRED", attempts=attempts,
                            blockers=["SESSION_MATERIALIZATION_FAILED"],
                            next_authorized_action="Retry reconciliation after rollback verification.")
                base["receipt_id"] = "ZEUS-RECEIPT-LAUNCH-ROLLBACK-" + _digest(base)[:24]
                base["receipt_digest"] = _digest(base)
                journal["transactions"][transaction_id] = base
                self.store.save(journal)
                return base

            base.update(state="EXECUTING", attempts=attempts, provider_process_id=result["process_id"],
                        provider_process_group_id=result["process_group_id"], provider_health_digest=result["health_digest"],
                        session_id=session["session_id"], records_created=["launch-request", "launch-acknowledgment", "session"],
                        next_authorized_action="Continue execution and monitor provider health.")
            base["launch_request_receipt_id"] = "ZEUS-RECEIPT-LAUNCH-REQUEST-" + _digest({"launch_id": launch_id})[:24]
            base["launch_acknowledgment_receipt_id"] = "ZEUS-RECEIPT-LAUNCH-ACK-" + _digest({"launch_id": launch_id, "health": result["health_digest"]})[:24]
            base["receipt_id"] = "ZEUS-RECEIPT-LAUNCH-" + _digest(base)[:24]
            base["receipt_digest"] = _digest(base)
            journal["transactions"][transaction_id] = base
            self.store.save(journal)
            return base
