#!/usr/bin/env python3
"""Receipt-backed autonomous lifecycle orchestration.

This module is deliberately an orchestrator, not an authority source.  Stage 1
and its receipts remain authoritative; this controller only derives desired
state, records recovery plans, and gates transitions that require approval.
Derived state is persisted atomically and replayed by deterministic identity.
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
from typing import Any, Mapping

from scripts.lib.emp.canonical_authority_receipt import AuthorityReceiptError, normalize as normalize_authority


class AutonomousLifecycleError(ValueError):
    """The lifecycle cannot be resolved to one lawful state."""


LIFECYCLE_STATES = (
    "SOURCE_DISCOVERED", "SOURCE_VALIDATED", "PACKAGE_CREATED",
    "PACKAGE_VERIFIED", "PACKAGE_REGISTERED", "AUTHORITY_RESOLVED",
    "MISSION_ADMITTED", "ADMISSION_PERSISTED", "ADMISSION_VERIFIED",
    "PROVIDER_SELECTED", "DISPATCHED", "EXECUTION_CREATED",
    "EXECUTION_PERSISTED", "SESSION_CREATED", "EXECUTION_STARTED",
    "EXECUTION_MONITORED", "SELF_DIAGNOSIS", "AUTONOMOUS_CORRECTION",
    "RECONCILIATION", "RESUME", "QUALIFICATION", "PUBLICATION_PREPARATION",
    "PUBLICATION_APPROVAL", "PUBLICATION", "EOS_SYNCHRONIZATION",
    "CANONICAL_RECONCILIATION", "MISSION_ACTIVATION", "MISSION_CLOSEOUT",
    "ARCHIVED",
)

RECEIPT_STATE = {
    "validation": "SOURCE_VALIDATED", "packaging": "PACKAGE_VERIFIED",
    "registration": "PACKAGE_REGISTERED", "authorization": "AUTHORITY_RESOLVED",
    "admission": "ADMISSION_VERIFIED", "provider_selection": "PROVIDER_SELECTED",
    "dispatch": "DISPATCHED", "execution": "EXECUTION_PERSISTED",
    "session": "SESSION_CREATED", "independent_verification": "QUALIFICATION",
    "publication": "PUBLICATION", "synchronization": "EOS_SYNCHRONIZATION",
    "closeout": "MISSION_CLOSEOUT",
}


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _identity(value: Mapping[str, Any]) -> str:
    transaction = value.get("instance_id") or value.get("transaction_id")
    if not transaction:
        raise AutonomousLifecycleError("authoritative transaction identity is absent")
    return "ZEUS-AUTONOMOUS-LIFECYCLE-" + str(uuid.uuid5(uuid.NAMESPACE_URL, str(transaction)))


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


class AutonomousLifecycleStore:
    """Atomic journal store for derived lifecycle snapshots."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.path = self.root / "autonomous-lifecycle"
        self.journal = self.path / "journal.json"
        self.lock = self.path / "lifecycle.lock"

    def load(self) -> dict[str, Any]:
        if not self.journal.is_file():
            return {"schema_version": 1, "transactions": {}}
        try:
            value = json.loads(self.journal.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AutonomousLifecycleError(f"lifecycle journal is invalid: {error}") from error
        if not isinstance(value, dict) or not isinstance(value.get("transactions"), dict):
            raise AutonomousLifecycleError("lifecycle journal shape is invalid")
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        descriptor, raw = tempfile.mkstemp(dir=self.path, prefix=".journal.")
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


class AutonomousLifecycleController:
    """Resolve and persist one deterministic lifecycle snapshot.

    ``authoritative`` is a Stage 1 record.  ``derived`` contains operational
    projections discovered by the caller.  The controller may repair its own
    journal, but it never changes the authoritative input or silently approves
    publication/destructive work.
    """

    def __init__(self, store: AutonomousLifecycleStore, *, dispatch_controller=None):
        self.store = store
        self.dispatch_controller = dispatch_controller

    @staticmethod
    def _state(authoritative: Mapping[str, Any]) -> str:
        receipts = authoritative.get("receipts") or {}
        states = [RECEIPT_STATE[key] for key in receipts if key in RECEIPT_STATE]
        if authoritative.get("state") in {"QUALIFIED", "PUBLICATION_READY", "PUBLISHED", "SYNCHRONIZED", "CLOSED"}:
            return {"QUALIFIED": "QUALIFICATION", "PUBLICATION_READY": "PUBLICATION_PREPARATION", "PUBLISHED": "PUBLICATION", "SYNCHRONIZED": "EOS_SYNCHRONIZATION", "CLOSED": "MISSION_CLOSEOUT"}[authoritative["state"]]
        return states[-1] if states else "SOURCE_DISCOVERED"

    @staticmethod
    def _validate_authority(authoritative: Mapping[str, Any]) -> None:
        if authoritative.get("execution_mode") == "DEVELOPMENT" and authoritative.get("authorization", {}).get("authority") not in {None, "Engineering Governance"}:
            raise AutonomousLifecycleError("authority chain is not Engineering Governance")
        receipts = authoritative.get("receipts") or {}
        if "authorization" not in receipts and authoritative.get("state") not in {"VALIDATED", "REJECTED"}:
            raise AutonomousLifecycleError("authorization receipt is absent")
        try:
            normalize_authority(authoritative, source="AUTONOMOUS_LIFECYCLE")
        except AuthorityReceiptError as error:
            raise AutonomousLifecycleError(f"canonical authority receipt rejected: {error.code}: {error}") from error

    def plan(self, authoritative: Mapping[str, Any], derived: Mapping[str, Any] | None = None, *, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
        self._validate_authority(authoritative)
        transaction_id = authoritative.get("instance_id") or authoritative.get("transaction_id")
        current = self._state(authoritative)
        derived = derived or {}
        corrections: list[dict[str, Any]] = []
        blockers: list[str] = []
        if current in {"DISPATCHED", "EXECUTION_PERSISTED", "EXECUTION_STARTED", "EXECUTION_MONITORED"} and not derived.get("execution"):
            corrections.append({"classification": "MISSING_EXECUTION_PROJECTION", "action": "runtime_reconciliation"})
        if current in {"SESSION_CREATED", "EXECUTION_STARTED", "EXECUTION_MONITORED"} and not derived.get("session"):
            corrections.append({"classification": "MISSING_SESSION_PROJECTION", "action": "session_reconciliation"})
        publication_required = bool((policy or {}).get("publication_approval_required", True))
        if current in {"QUALIFICATION", "PUBLICATION_PREPARATION"} and publication_required and not (policy or {}).get("publication_approved"):
            blockers.append("PUBLICATION_APPROVAL_REQUIRED")
        if derived.get("conflict"):
            blockers.append(str(derived["conflict"]))
        desired = "AUTONOMOUS_CORRECTION" if corrections else current
        material = {"transaction_id": transaction_id, "current": current, "desired": desired, "corrections": corrections, "blockers": blockers}
        return {"schema_version": 1, "plan_id": _identity(authoritative), "transaction_id": transaction_id,
                "wop_id": authoritative.get("wop_id"), "mission_id": authoritative.get("mission_id"),
                "authoritative_state": current, "desired_state": desired, "corrections": corrections,
                "blockers": blockers, "next_action": "Resolve blockers before resuming" if blockers else "Apply the reconciliation plan and continue the authorized lifecycle",
                "plan_digest": canonical_digest(material)}

    def reconcile(self, authoritative: Mapping[str, Any], derived: Mapping[str, Any] | None = None, *, command: str = "status", policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
        plan = self.plan(authoritative, derived, policy=policy)
        transaction_id = plan["transaction_id"]
        with _lock(self.store.lock):
            journal = self.store.load()
            previous = journal["transactions"].get(transaction_id)
            replay = bool(previous and previous.get("plan_digest") == plan["plan_digest"] and previous.get("command") == command)
            snapshot = {**plan, "command": command, "replay": replay, "authority_source": "STAGE1_RECEIPT_CHAIN",
                        "immutable_identities_preserved": [transaction_id, authoritative.get("wop_id"), authoritative.get("package_digest")],
                        "reconciliation_receipt_id": "ZEUS-RECEIPT-LIFECYCLE-" + plan["plan_digest"][:24]}
            snapshot["snapshot_digest"] = canonical_digest(snapshot)
            journal["transactions"][transaction_id] = snapshot
            self.store.save(journal)
        if (policy or {}).get("autonomous_dispatch") and self.dispatch_controller is not None and plan["authoritative_state"] == "DISPATCHED":
            dispatch_result = self.dispatch_controller.reconcile(
                authoritative, command=command,
                provider_launcher=(policy or {}).get("provider_launcher"),
                session_materializer=(policy or {}).get("session_materializer"),
                cleanup=(policy or {}).get("cleanup"),
                policy=policy,
            )
            snapshot["autonomous_dispatch"] = dispatch_result
            snapshot["snapshot_digest"] = canonical_digest(snapshot)
            with _lock(self.store.lock):
                journal = self.store.load()
                journal["transactions"][transaction_id] = snapshot
                self.store.save(journal)
        return snapshot
