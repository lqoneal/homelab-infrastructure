#!/usr/bin/env python3
"""Deterministic supervision and replay of dispatched execution assignments."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol

from scripts.lib.emp.wop_dispatch import ExecutionAssignment


class OversightError(ValueError):
    """Fail-closed execution oversight error."""


class ExecutionState(str, Enum):
    DISPATCHED = "Dispatched"
    ACCEPTED = "Accepted"
    INITIALIZING = "Initializing"
    RUNNING = "Running"
    WAITING_APPROVAL = "Waiting Approval"
    PAUSED = "Paused"
    RESUMING = "Resuming"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


TERMINAL = {
    ExecutionState.COMPLETED,
    ExecutionState.FAILED,
    ExecutionState.CANCELLED,
}
TRANSITIONS = {
    ExecutionState.DISPATCHED: {
        ExecutionState.ACCEPTED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.ACCEPTED: {
        ExecutionState.INITIALIZING,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.INITIALIZING: {
        ExecutionState.RUNNING,
        ExecutionState.PAUSED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.RUNNING: {
        ExecutionState.WAITING_APPROVAL,
        ExecutionState.PAUSED,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.WAITING_APPROVAL: {
        ExecutionState.RESUMING,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.PAUSED: {
        ExecutionState.RESUMING,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.RESUMING: {
        ExecutionState.RUNNING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.COMPLETED: set(),
    ExecutionState.FAILED: set(),
    ExecutionState.CANCELLED: set(),
}


class ApprovalStatus(str, Enum):
    NONE = "none"
    REQUESTED = "requested"
    AWAITING = "awaiting"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise OversightError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise OversightError("invalid event timestamp") from error
    if result.tzinfo is None:
        raise OversightError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def identifier(prefix: str, material: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))


class EventAuthenticator(Protocol):
    def verify(self, envelope: Mapping[str, Any]) -> bool: ...


class DigestFixtureAuthenticator:
    """Offline EENS authentication interface used by fixtures."""

    def verify(self, envelope: Mapping[str, Any]) -> bool:
        unsigned = {
            key: value for key, value in envelope.items() if key != "authentication_digest"
        }
        return envelope.get("authentication_digest") == digest(unsigned)


@dataclass(frozen=True)
class ExecutionEvent:
    canonical_data: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionEvent":
        result = cls(canonical_json(value))
        result.validate()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def validate(self) -> None:
        value = self.data
        required = {
            "current_event_hash",
            "event_identifier",
            "event_payload_digest",
            "execution_agent",
            "execution_state",
            "previous_event_hash",
            "producing_component",
            "sequence",
            "timestamp",
        }
        if set(value) != required:
            raise OversightError("execution event shape is invalid")
        ExecutionState(value["execution_state"])
        parse_time(value["timestamp"])
        if not isinstance(value["sequence"], int) or value["sequence"] < 1:
            raise OversightError("execution event sequence is invalid")
        unsigned = {
            key: item for key, item in value.items() if key != "current_event_hash"
        }
        if value["current_event_hash"] != digest(unsigned):
            raise OversightError("execution event hash mismatch")


class OversightStore:
    """Canonical, atomically replaced session inventory."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "schema_version": 1,
                "manager_id": "EMP-EXECUTION-OVERSIGHT",
                "sessions": {},
                "assignments": {},
            }
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise OversightError(f"invalid oversight store: {error}") from error
        if not isinstance(value, dict):
            raise OversightError("oversight store root must be an object")
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            value, indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"
        descriptor, temporary = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


class ExecutionOversight:
    """Authoritative runtime records without engineering execution."""

    def __init__(self, store: OversightStore) -> None:
        self.store = store
        self._data = store.load()
        self.validate()

    @property
    def data(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def create_session(
        self,
        assignment: ExecutionAssignment,
        dispatch_event: Mapping[str, Any],
        *,
        created_at: datetime,
    ) -> dict[str, Any]:
        assignment.validate()
        ea = assignment.data
        if ea["assignment_id"] in self._data["assignments"]:
            raise OversightError("one Execution Session per Assignment is enforced")
        if (
            dispatch_event.get("assignment_id") != ea["assignment_id"]
            or dispatch_event.get("assignment_checksum") != ea["assignment_checksum"]
            or dispatch_event.get("wop_id") != ea["wop_id"]
            or dispatch_event.get("from") != "Ready"
            or dispatch_event.get("to") != "Dispatched"
        ):
            raise OversightError("dispatch evidence does not bind the assignment")
        event_unsigned = {
            key: value
            for key, value in dispatch_event.items()
            if key != "event_digest"
        }
        if dispatch_event.get("event_digest") != digest(event_unsigned):
            raise OversightError("dispatch evidence digest mismatch")
        material = {
            "assignment_id": ea["assignment_id"],
            "creation_timestamp": utc_text(created_at),
            "repository_identity": ea["repository_identity"],
            "wop_id": ea["wop_id"],
        }
        session_id = identifier("SESSION", material)
        genesis = self._ledger_event(
            sequence=1,
            event_id=identifier("EVENT", {"session_id": session_id, "genesis": material}),
            timestamp=material["creation_timestamp"],
            component="EMP-DISPATCH",
            agent=ea["intended_execution_agent"],
            state=ExecutionState.DISPATCHED,
            payload={
                "assignment_checksum": ea["assignment_checksum"],
                "checkpoint": "dispatch-delivered",
                "event_type": "session_created",
            },
            previous="GENESIS",
        )
        session = {
            "session_id": session_id,
            "assignment_id": ea["assignment_id"],
            "mission_id": ea["mission_id"],
            "wop_id": ea["wop_id"],
            "repository_identity": ea["repository_identity"],
            "baseline_commit": ea["baseline_commit"],
            "execution_agent_identity": ea["intended_execution_agent"],
            "creation_timestamp": material["creation_timestamp"],
            "event_ledger": [genesis],
            "event_payloads": {
                genesis["event_identifier"]: {
                    "assignment_checksum": ea["assignment_checksum"],
                    "checkpoint": "dispatch-delivered",
                    "event_type": "session_created",
                }
            },
        }
        self._data["sessions"][session_id] = session
        self._data["assignments"][ea["assignment_id"]] = session_id
        try:
            self._persist()
        except Exception:
            self._data["sessions"].pop(session_id, None)
            self._data["assignments"].pop(ea["assignment_id"], None)
            raise
        return self.reconstruct(session_id)

    def ingest_eens_event(
        self,
        session_id: str,
        envelope: Mapping[str, Any],
        *,
        authenticator: EventAuthenticator,
    ) -> dict[str, Any]:
        session = self._session(session_id)
        required = {
            "assignment_id",
            "authentication_digest",
            "baseline_commit",
            "event_identifier",
            "execution_agent",
            "execution_state",
            "payload",
            "producing_component",
            "repository_identity",
            "session_id",
            "timestamp",
        }
        if set(envelope) != required:
            raise OversightError("EENS event envelope shape is invalid")
        if envelope["producing_component"] != "EENS":
            raise OversightError("EENS is the required execution event source")
        if not authenticator.verify(envelope):
            raise OversightError("EENS event authentication failed")
        if (
            envelope["session_id"] != session_id
            or envelope["assignment_id"] != session["assignment_id"]
            or envelope["repository_identity"] != session["repository_identity"]
            or envelope["baseline_commit"] != session["baseline_commit"]
            or envelope["execution_agent"] != session["execution_agent_identity"]
        ):
            raise OversightError("EENS event binding mismatch")
        if any(
            event["event_identifier"] == envelope["event_identifier"]
            for event in session["event_ledger"]
        ):
            raise OversightError("duplicate execution event identifier")
        return self._append(
            session,
            event_id=envelope["event_identifier"],
            timestamp=envelope["timestamp"],
            component="EENS",
            agent=envelope["execution_agent"],
            state=ExecutionState(envelope["execution_state"]),
            payload=envelope["payload"],
        )

    def detect_interruption(
        self,
        session_id: str,
        *,
        cause: str,
        detected_at: datetime,
        heartbeat_timeout: timedelta | None = None,
    ) -> dict[str, Any]:
        allowed = {
            "agent_disconnect",
            "heartbeat_timeout",
            "unexpected_termination",
            "repository_mismatch",
            "assignment_mismatch",
        }
        if cause not in allowed:
            raise OversightError("unknown interruption cause")
        session = self._session(session_id)
        replay = self.reconstruct(session_id)
        if replay["current_execution_state"] in {
            state.value for state in TERMINAL
        }:
            raise OversightError("terminal sessions cannot be interrupted")
        timestamp = utc_text(detected_at)
        if cause == "heartbeat_timeout":
            if heartbeat_timeout is None:
                raise OversightError("heartbeat timeout duration is required")
            last = parse_time(session["event_ledger"][-1]["timestamp"])
            if detected_at.astimezone(timezone.utc) - last <= heartbeat_timeout:
                raise OversightError("heartbeat timeout has not elapsed")
        target = ExecutionState.PAUSED
        current = ExecutionState(replay["current_execution_state"])
        if target not in TRANSITIONS[current] and current is not target:
            target = ExecutionState.FAILED
        payload = {
            "checkpoint": replay["current_checkpoint"],
            "event_type": "interruption_detected",
            "interruption_cause": cause,
        }
        event_id = identifier(
            "EVENT",
            {
                "cause": cause,
                "detected_at": timestamp,
                "previous": session["event_ledger"][-1]["current_event_hash"],
                "session_id": session_id,
            },
        )
        return self._append(
            session,
            event_id=event_id,
            timestamp=timestamp,
            component="EMP-OVERSIGHT",
            agent=session["execution_agent_identity"],
            state=target,
            payload=payload,
        )

    def reconstruct(self, session_id: str) -> dict[str, Any]:
        session = self._session(session_id)
        state = ExecutionState.DISPATCHED
        previous = "GENESIS"
        checkpoint = None
        approval = ApprovalStatus.NONE
        milestones: list[str] = []
        pending_milestones: list[str] = []
        interruptions: list[dict[str, str]] = []
        last_time: datetime | None = None
        for sequence, event_value in enumerate(session["event_ledger"], start=1):
            event = ExecutionEvent.from_mapping(event_value)
            value = event.data
            if value["sequence"] != sequence:
                raise OversightError("execution event sequence is not contiguous")
            if value["previous_event_hash"] != previous:
                raise OversightError("execution event hash chain is broken")
            timestamp = parse_time(value["timestamp"])
            if last_time is not None and timestamp < last_time:
                raise OversightError("execution event timestamps are not ordered")
            target = ExecutionState(value["execution_state"])
            if sequence == 1:
                if target is not ExecutionState.DISPATCHED:
                    raise OversightError("session genesis must be Dispatched")
            elif target != state and target not in TRANSITIONS[state]:
                raise OversightError(
                    f"illegal execution transition: {state.value} -> {target.value}"
                )
            payload = session["event_payloads"].get(value["event_identifier"])
            if payload is None or digest(payload) != value["event_payload_digest"]:
                raise OversightError("execution event payload digest mismatch")
            event_type = payload.get("event_type")
            if event_type == "approval_requested":
                if target is not ExecutionState.WAITING_APPROVAL:
                    raise OversightError("approval request must wait for approval")
                approval = ApprovalStatus.AWAITING
            if event_type == "approval_decision":
                decision = ApprovalStatus(payload.get("approval_status"))
                if decision not in {
                    ApprovalStatus.APPROVED,
                    ApprovalStatus.REJECTED,
                    ApprovalStatus.EXPIRED,
                }:
                    raise OversightError("approval decision is invalid")
                if approval is not ApprovalStatus.AWAITING:
                    raise OversightError("approval decision has no pending request")
                approval = decision
            if target is ExecutionState.RESUMING and state is ExecutionState.WAITING_APPROVAL:
                if approval is not ApprovalStatus.APPROVED:
                    raise OversightError("resuming requires explicit approval")
            if payload.get("checkpoint"):
                checkpoint = payload["checkpoint"]
            milestone = payload.get("milestone")
            if milestone:
                if payload.get("milestone_status") == "completed":
                    if milestone not in milestones:
                        milestones.append(milestone)
                    if milestone in pending_milestones:
                        pending_milestones.remove(milestone)
                elif milestone not in pending_milestones:
                    pending_milestones.append(milestone)
            if event_type == "interruption_detected":
                interruptions.append(
                    {
                        "cause": payload["interruption_cause"],
                        "event_identifier": value["event_identifier"],
                        "timestamp": value["timestamp"],
                    }
                )
            state = target
            previous = value["current_event_hash"]
            last_time = timestamp
        resume_eligible = (
            state in {ExecutionState.PAUSED, ExecutionState.WAITING_APPROVAL}
            and approval not in {ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED}
        )
        snapshot = {
            "approval_status": approval.value,
            "assignment_id": session["assignment_id"],
            "completed_milestones": milestones,
            "creation_timestamp": session["creation_timestamp"],
            "current_checkpoint": checkpoint,
            "current_execution_state": state.value,
            "execution_agent_identity": session["execution_agent_identity"],
            "expected_restart_point": checkpoint if resume_eligible else None,
            "interruption_history": interruptions,
            "last_received_event": session["event_ledger"][-1]["event_identifier"],
            "mission_id": session["mission_id"],
            "pending_milestones": pending_milestones,
            "repository_identity": session["repository_identity"],
            "baseline_commit": session["baseline_commit"],
            "resume_eligibility": resume_eligible,
            "session_id": session_id,
            "wop_id": session["wop_id"],
        }
        snapshot["session_digest"] = digest(snapshot)
        return snapshot

    def validate(self) -> None:
        if (
            self._data.get("schema_version") != 1
            or self._data.get("manager_id") != "EMP-EXECUTION-OVERSIGHT"
            or not isinstance(self._data.get("sessions"), dict)
            or not isinstance(self._data.get("assignments"), dict)
        ):
            raise OversightError("execution oversight store shape is invalid")
        if len(self._data["assignments"]) != len(set(self._data["assignments"])):
            raise OversightError("assignment mapping is not one-to-one")
        for assignment_id, session_id in self._data["assignments"].items():
            session = self._data["sessions"].get(session_id)
            if session is None or session.get("assignment_id") != assignment_id:
                raise OversightError("assignment/session inventory mismatch")
        if set(self._data["assignments"].values()) != set(self._data["sessions"]):
            raise OversightError("every session must have one assignment")
        for session_id in sorted(self._data["sessions"]):
            if self._data["sessions"][session_id].get("session_id") != session_id:
                raise OversightError("session identity mismatch")
            self.reconstruct(session_id)

    def save(self) -> None:
        self._persist()

    def _append(
        self,
        session: dict[str, Any],
        *,
        event_id: str,
        timestamp: str,
        component: str,
        agent: str,
        state: ExecutionState,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        replay = self.reconstruct(session["session_id"])
        current = ExecutionState(replay["current_execution_state"])
        if current in TERMINAL:
            raise OversightError("terminal execution state is immutable")
        if state != current and state not in TRANSITIONS[current]:
            raise OversightError(
                f"illegal execution transition: {current.value} -> {state.value}"
            )
        if parse_time(timestamp) < parse_time(session["event_ledger"][-1]["timestamp"]):
            raise OversightError("execution event timestamp is out of order")
        event = self._ledger_event(
            sequence=len(session["event_ledger"]) + 1,
            event_id=event_id,
            timestamp=timestamp,
            component=component,
            agent=agent,
            state=state,
            payload=payload,
            previous=session["event_ledger"][-1]["current_event_hash"],
        )
        session["event_ledger"].append(event)
        session["event_payloads"][event_id] = deepcopy(dict(payload))
        try:
            self._persist()
        except Exception:
            session["event_ledger"].pop()
            session["event_payloads"].pop(event_id, None)
            raise
        return deepcopy(event)

    @staticmethod
    def _ledger_event(
        *,
        sequence: int,
        event_id: str,
        timestamp: str,
        component: str,
        agent: str,
        state: ExecutionState,
        payload: Mapping[str, Any],
        previous: str,
    ) -> dict[str, Any]:
        event = {
            "event_identifier": event_id,
            "timestamp": timestamp,
            "producing_component": component,
            "execution_agent": agent,
            "execution_state": state.value,
            "event_payload_digest": digest(payload),
            "previous_event_hash": previous,
            "sequence": sequence,
        }
        event["current_event_hash"] = digest(event)
        return event

    def _persist(self) -> None:
        self.validate()
        self.store.save(self._data)

    def _session(self, session_id: str) -> dict[str, Any]:
        try:
            return self._data["sessions"][session_id]
        except KeyError as error:
            raise OversightError(f"unknown Execution Session: {session_id}") from error
