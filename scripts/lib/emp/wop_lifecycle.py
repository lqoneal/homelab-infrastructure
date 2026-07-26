#!/usr/bin/env python3
"""Deterministic, repository-backed WOP lifecycle management."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.lib.wop.contract import WorkPackage


SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class LifecycleError(ValueError):
    """Fail-closed lifecycle validation error."""


class DispatchBoundaryError(LifecycleError):
    """Raised whenever a caller attempts to cross Ready."""


class LifecycleState(str, Enum):
    DRAFT = "Draft"
    STAGED = "Staged"
    ELIGIBLE = "Eligible"
    SELECTED = "Selected"
    AUTHORIZED = "Authorized"
    RESERVED = "Reserved"
    READY = "Ready"


LIFECYCLE = tuple(LifecycleState)
TRANSITIONS = tuple(zip(LIFECYCLE, LIFECYCLE[1:]))
NEXT_STATE = {source: target for source, target in TRANSITIONS}


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class QueueStatus(str, Enum):
    STAGED = "staged"
    ELIGIBLE = "eligible"
    SELECTED = "selected"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    COMPLETE = "complete"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise LifecycleError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise LifecycleError("invalid lifecycle timestamp") from error
    if result.tzinfo is None:
        raise LifecycleError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def _uuid(prefix: str, material: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    wop_id: str
    mission_id: str
    authority_chain: tuple[str, ...]
    requested_capabilities: tuple[str, ...]
    repository_baseline: str
    expected_execution_agent: str
    created_at: str
    expires_at: str
    planning_only: bool = True
    grants_authority: bool = False
    is_execution_lease: bool = False

    @classmethod
    def create(
        cls,
        *,
        wop_id: str,
        mission_id: str,
        authority_chain: Iterable[str],
        requested_capabilities: Iterable[str],
        repository_baseline: str,
        expected_execution_agent: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> "Reservation":
        if not COMMIT.fullmatch(repository_baseline):
            raise LifecycleError("reservation baseline must be a full Git SHA")
        if not expected_execution_agent:
            raise LifecycleError("reservation expected agent is required")
        created = utc_text(created_at)
        expires = utc_text(expires_at)
        if parse_time(expires) <= parse_time(created):
            raise LifecycleError("reservation expiration must follow creation")
        material = {
            "authority_chain": list(authority_chain),
            "created_at": created,
            "expected_execution_agent": expected_execution_agent,
            "expires_at": expires,
            "mission_id": mission_id,
            "repository_baseline": repository_baseline,
            "requested_capabilities": sorted(requested_capabilities),
            "wop_id": wop_id,
        }
        return cls(
            reservation_id=_uuid("RESERVATION", material),
            wop_id=wop_id,
            mission_id=mission_id,
            authority_chain=tuple(material["authority_chain"]),
            requested_capabilities=tuple(material["requested_capabilities"]),
            repository_baseline=repository_baseline,
            expected_execution_agent=expected_execution_agent,
            created_at=created,
            expires_at=expires,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "authority_chain": list(self.authority_chain),
            "created_at": self.created_at,
            "expected_execution_agent": self.expected_execution_agent,
            "expires_at": self.expires_at,
            "grants_authority": self.grants_authority,
            "is_execution_lease": self.is_execution_lease,
            "mission_id": self.mission_id,
            "planning_only": self.planning_only,
            "repository_baseline": self.repository_baseline,
            "requested_capabilities": list(self.requested_capabilities),
            "reservation_id": self.reservation_id,
            "wop_id": self.wop_id,
        }


class LifecycleStore:
    """Canonical JSON persistence with atomic replacement."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "schema_version": 1,
                "manager_id": "EMP-WOP-LIFECYCLE",
                "packages": {},
                "queue": [],
            }
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise LifecycleError(f"invalid lifecycle store: {error}") from error
        if not isinstance(value, dict):
            raise LifecycleError("lifecycle store root must be an object")
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


class WopLifecycleManager:
    """EMP lifecycle manager that terminates at the dispatch boundary."""

    def __init__(self, store: LifecycleStore) -> None:
        self.store = store
        self._data = store.load()
        self.validate()

    @property
    def data(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def register(
        self,
        *,
        wop: WorkPackage,
        authorization_record: Mapping[str, Any],
        repository_identity: str,
        repository_baseline: str,
        priority: int,
        staging_order: int,
        mission_dependencies: Iterable[str] = (),
        required_approvals: Iterable[str] = (),
        required_evidence: Iterable[str] = (),
        reconciliation_updates: Mapping[str, Iterable[str]] | None = None,
    ) -> dict[str, Any]:
        wop.validate()
        self._validate_authorization(
            wop, authorization_record, repository_identity, repository_baseline
        )
        if wop.wop_id in self._data["packages"]:
            raise LifecycleError(f"WOP already registered: {wop.wop_id}")
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
            raise LifecycleError("queue priority must be a non-negative integer")
        if (
            not isinstance(staging_order, int)
            or isinstance(staging_order, bool)
            or staging_order < 0
        ):
            raise LifecycleError("staging order must be a non-negative integer")
        binding = wop.data["authority_binding"]
        capabilities = sorted(
            {
                effect["kind"]
                for effect in wop.data["authorized_effects"]
                if isinstance(effect, Mapping)
            }
        )
        approvals = {
            approval_id: {
                "approval_id": approval_id,
                "required": True,
                "status": ApprovalStatus.PENDING.value,
                "history": [],
            }
            for approval_id in sorted(set(required_approvals))
        }
        reconciliation = {
            key: sorted(set(values))
            for key, values in sorted((reconciliation_updates or {}).items())
        }
        package = {
            "wop_id": wop.wop_id,
            "wop_digest": wop.payload_digest,
            "mission_id": binding["mission_id"],
            "phase_id": binding["phase_id"],
            "work_item_id": binding["work_item_id"],
            "authority_node_id": binding["authority_node_id"],
            "authority_chain": list(authorization_record["authority_chain"]),
            "requested_capabilities": capabilities,
            "repository_identity": repository_identity,
            "repository_baseline": repository_baseline,
            "authorization_decision_digest": authorization_record["decision_digest"],
            "prerequisites": sorted(
                item["evidence_ref"]
                for item in wop.data["prerequisites"]
                if item.get("required") is True
            ),
            "wop_dependencies": sorted(
                item["wop_id"]
                for item in wop.data["dependencies"]
                if item.get("required") is True
            ),
            "mission_dependencies": sorted(set(mission_dependencies)),
            "state": LifecycleState.DRAFT.value,
            "history": [],
            "approvals": approvals,
            "reservation": None,
            "evidence_plan": {
                state.value: {
                    "required": sorted(set(required_evidence)),
                    "produced": [],
                    "missing": sorted(set(required_evidence)),
                    "completion_expectations": [
                        f"retain expected evidence for {state.value} without qualification"
                    ],
                    "qualification_performed": False,
                }
                for state in LIFECYCLE
            },
            "reconciliation_plan": reconciliation,
            "reconciliation_performed": False,
        }
        queue_entry = {
            "mission_id": binding["mission_id"],
            "wop_id": wop.wop_id,
            "priority": priority,
            "staging_order": staging_order,
            "dependencies": sorted(set(mission_dependencies)),
            "status": QueueStatus.STAGED.value,
        }
        self._data["packages"][wop.wop_id] = package
        self._data["queue"].append(queue_entry)
        self._sort_queue()
        self._persist_validated()
        return deepcopy(package)

    def set_approval(
        self,
        wop_id: str,
        approval_id: str,
        status: ApprovalStatus,
        *,
        actor: str,
        timestamp: datetime,
        reason: str,
    ) -> dict[str, Any]:
        package = self._package(wop_id)
        checkpoint = package["approvals"].get(approval_id)
        if checkpoint is None:
            raise LifecycleError(f"unknown approval checkpoint: {approval_id}")
        current = ApprovalStatus(checkpoint["status"])
        allowed = {
            ApprovalStatus.PENDING: {
                ApprovalStatus.APPROVED,
                ApprovalStatus.REJECTED,
                ApprovalStatus.SUPERSEDED,
            },
            ApprovalStatus.APPROVED: {ApprovalStatus.SUPERSEDED},
            ApprovalStatus.REJECTED: {ApprovalStatus.SUPERSEDED},
            ApprovalStatus.SUPERSEDED: set(),
        }
        if status not in allowed[current]:
            raise LifecycleError(
                f"invalid approval transition: {current.value} -> {status.value}"
            )
        event = {
            "actor": actor,
            "from": current.value,
            "reason": reason,
            "timestamp": utc_text(timestamp),
            "to": status.value,
        }
        event["digest"] = digest(event)
        checkpoint["history"].append(event)
        checkpoint["status"] = status.value
        self._persist_validated()
        return deepcopy(checkpoint)

    def set_queue_status(self, mission_id: str, status: QueueStatus) -> None:
        if status not in (QueueStatus.BLOCKED, QueueStatus.DEFERRED, QueueStatus.STAGED):
            raise LifecycleError("manual queue status must be blocked, deferred or staged")
        entry = self._queue_entry(mission_id)
        if entry["status"] == QueueStatus.COMPLETE.value:
            raise LifecycleError("completed mission queue entry is immutable")
        entry["status"] = status.value
        self._persist_validated()

    def select_next(self, completed_missions: Iterable[str]) -> str:
        completed = set(completed_missions)
        candidates = [
            entry
            for entry in self._data["queue"]
            if self._data["packages"][entry["wop_id"]]["state"]
            == LifecycleState.ELIGIBLE.value
            and entry["status"]
            not in (QueueStatus.BLOCKED.value, QueueStatus.DEFERRED.value)
            and set(entry["dependencies"]) <= completed
        ]
        if not candidates:
            raise LifecycleError("no eligible mission is selectable")
        candidates.sort(
            key=lambda item: (
                item["priority"],
                item["staging_order"],
                item["mission_id"],
                item["wop_id"],
            )
        )
        selected = candidates[0]
        for entry in self._data["queue"]:
            if entry["status"] == QueueStatus.SELECTED.value:
                entry["status"] = QueueStatus.ELIGIBLE.value
        selected["status"] = QueueStatus.SELECTED.value
        self._persist_validated()
        return selected["mission_id"]

    def transition(
        self,
        wop_id: str,
        target: LifecycleState,
        *,
        authorization_record: Mapping[str, Any],
        repository_identity: str,
        repository_baseline: str,
        prerequisite_evidence: Iterable[str] = (),
        satisfied_dependencies: Iterable[str] = (),
        timestamp: datetime,
        actor: str,
        reservation: Reservation | None = None,
    ) -> dict[str, Any]:
        package = self._package(wop_id)
        current = LifecycleState(package["state"])
        if current is LifecycleState.READY:
            raise DispatchBoundaryError("Ready is terminal; dispatch boundary is closed")
        expected = NEXT_STATE[current]
        if target is not expected:
            raise LifecycleError(
                f"illegal lifecycle transition: {current.value} -> {target.value}"
            )
        self._validate_stored_authorization(
            package,
            authorization_record,
            repository_identity,
            repository_baseline,
        )
        if target in (
            LifecycleState.ELIGIBLE,
            LifecycleState.SELECTED,
            LifecycleState.AUTHORIZED,
            LifecycleState.RESERVED,
            LifecycleState.READY,
        ):
            self._validate_prerequisites_and_dependencies(
                package, prerequisite_evidence, satisfied_dependencies
            )
        queue = self._queue_entry(package["mission_id"])
        if target is LifecycleState.ELIGIBLE:
            queue["status"] = QueueStatus.ELIGIBLE.value
        if target is LifecycleState.SELECTED:
            if queue["status"] != QueueStatus.SELECTED.value:
                raise LifecycleError("mission must be selected by deterministic queue")
        if target is LifecycleState.AUTHORIZED:
            pending = sorted(
                approval_id
                for approval_id, checkpoint in package["approvals"].items()
                if checkpoint["required"]
                and checkpoint["status"] != ApprovalStatus.APPROVED.value
            )
            if pending:
                raise LifecycleError("required approvals not approved: " + ",".join(pending))
        if target is LifecycleState.RESERVED:
            if reservation is None:
                raise LifecycleError("planning reservation is required")
            self._validate_reservation(package, reservation)
            package["reservation"] = reservation.to_mapping()
        if target is LifecycleState.READY:
            if package["reservation"] is None:
                raise LifecycleError("Ready requires a planning reservation")
            if parse_time(package["reservation"]["expires_at"]) <= timestamp.astimezone(
                timezone.utc
            ):
                raise LifecycleError("planning reservation is expired")

        previous_digest = (
            package["history"][-1]["event_digest"] if package["history"] else "GENESIS"
        )
        event = {
            "actor": actor,
            "authorization_decision_digest": authorization_record["decision_digest"],
            "from": current.value,
            "previous_digest": previous_digest,
            "sequence": len(package["history"]) + 1,
            "timestamp": utc_text(timestamp),
            "to": target.value,
        }
        event["event_digest"] = digest(event)
        package["history"].append(event)
        package["state"] = target.value
        self._persist_validated()
        return deepcopy(event)

    def record_expected_evidence(
        self,
        wop_id: str,
        evidence_ids: Iterable[str],
        phase: LifecycleState | None = None,
    ) -> None:
        package = self._package(wop_id)
        phase_name = (phase or LifecycleState(package["state"])).value
        plan = package["evidence_plan"][phase_name]
        produced = sorted(set(plan["produced"]) | set(evidence_ids))
        plan["produced"] = produced
        plan["missing"] = sorted(
            set(plan["required"]) - set(produced)
        )
        self._persist_validated()

    def reconstruct(self, wop_id: str) -> dict[str, Any]:
        package = self._package(wop_id)
        state = LifecycleState.DRAFT
        previous = "GENESIS"
        for sequence, event in enumerate(package["history"], start=1):
            if event["sequence"] != sequence:
                raise LifecycleError("lifecycle event sequence is not contiguous")
            if event["from"] != state.value or event["to"] != NEXT_STATE[state].value:
                raise LifecycleError("lifecycle event transition is not deterministic")
            if event["previous_digest"] != previous:
                raise LifecycleError("lifecycle event hash chain is broken")
            unsigned = {key: value for key, value in event.items() if key != "event_digest"}
            if event["event_digest"] != digest(unsigned):
                raise LifecycleError("lifecycle event digest mismatch")
            previous = event["event_digest"]
            state = LifecycleState(event["to"])
        if package["state"] != state.value:
            raise LifecycleError("persisted lifecycle state disagrees with replay")
        return {
            "wop_id": wop_id,
            "state": state.value,
            "completed_transitions": [
                f"{event['from']}->{event['to']}" for event in package["history"]
            ],
            "pending_transition": (
                None
                if state is LifecycleState.READY
                else f"{state.value}->{NEXT_STATE[state].value}"
            ),
            "evidence_expectations": deepcopy(package["evidence_plan"]),
            "approval_status": {
                key: value["status"] for key, value in sorted(package["approvals"].items())
            },
            "reservation_status": (
                "absent" if package["reservation"] is None else "planned"
            ),
        }

    def validate(self) -> None:
        if self._data.get("schema_version") != 1:
            raise LifecycleError("lifecycle store schema_version must be 1")
        if self._data.get("manager_id") != "EMP-WOP-LIFECYCLE":
            raise LifecycleError("lifecycle manager identity mismatch")
        if not isinstance(self._data.get("packages"), dict):
            raise LifecycleError("lifecycle packages must be an object")
        if not isinstance(self._data.get("queue"), list):
            raise LifecycleError("mission queue must be a list")
        wop_ids = set(self._data["packages"])
        queue_wops = [entry.get("wop_id") for entry in self._data["queue"]]
        if len(queue_wops) != len(set(queue_wops)):
            raise LifecycleError("mission queue contains duplicate WOPs")
        if set(queue_wops) != wop_ids:
            raise LifecycleError("mission queue and WOP inventory disagree")
        expected_queue = sorted(
            self._data["queue"],
            key=lambda item: (
                item["priority"],
                item["staging_order"],
                item["mission_id"],
                item["wop_id"],
            ),
        )
        if self._data["queue"] != expected_queue:
            raise LifecycleError("mission queue ordering is not canonical")
        for wop_id in sorted(wop_ids):
            self.reconstruct(wop_id)
            package = self._data["packages"][wop_id]
            if set(package.get("evidence_plan", {})) != {
                state.value for state in LIFECYCLE
            }:
                raise LifecycleError("evidence planning is incomplete by phase")
            for checkpoint in package.get("approvals", {}).values():
                self._validate_approval_history(checkpoint)
            reservation = package.get("reservation")
            if reservation and (
                reservation.get("planning_only") is not True
                or reservation.get("grants_authority") is not False
                or reservation.get("is_execution_lease") is not False
            ):
                raise LifecycleError("reservation crossed its planning boundary")
            if reservation:
                material = {
                    "authority_chain": reservation["authority_chain"],
                    "created_at": reservation["created_at"],
                    "expected_execution_agent": reservation[
                        "expected_execution_agent"
                    ],
                    "expires_at": reservation["expires_at"],
                    "mission_id": reservation["mission_id"],
                    "repository_baseline": reservation["repository_baseline"],
                    "requested_capabilities": reservation[
                        "requested_capabilities"
                    ],
                    "wop_id": reservation["wop_id"],
                }
                if reservation["reservation_id"] != _uuid("RESERVATION", material):
                    raise LifecycleError("reservation identity is not reproducible")
                if parse_time(reservation["expires_at"]) <= parse_time(
                    reservation["created_at"]
                ):
                    raise LifecycleError("reservation interval is invalid")

    def save(self) -> None:
        self._persist_validated()

    def _persist_validated(self) -> None:
        self.validate()
        self.store.save(self._data)

    def _package(self, wop_id: str) -> dict[str, Any]:
        try:
            return self._data["packages"][wop_id]
        except KeyError as error:
            raise LifecycleError(f"unknown WOP: {wop_id}") from error

    def _queue_entry(self, mission_id: str) -> dict[str, Any]:
        matches = [
            entry for entry in self._data["queue"] if entry["mission_id"] == mission_id
        ]
        if len(matches) != 1:
            raise LifecycleError(f"mission queue identity is not unique: {mission_id}")
        return matches[0]

    def _sort_queue(self) -> None:
        self._data["queue"].sort(
            key=lambda item: (
                item["priority"],
                item["staging_order"],
                item["mission_id"],
                item["wop_id"],
            )
        )

    @staticmethod
    def _validate_authorization(
        wop: WorkPackage,
        record: Mapping[str, Any],
        repository_identity: str,
        repository_baseline: str,
    ) -> None:
        errors = []
        if record.get("schema_version") != 2:
            errors.append("authorization ADR schema version 2 is required")
        if record.get("authoritative_decision_source") != "ZEUS":
            errors.append("Zeus authorization source is required")
        if record.get("enforcement_decision") != "AUTHORIZED":
            errors.append("WOP is not authorized")
        if record.get("wop_id") != wop.wop_id:
            errors.append("authorization WOP identity mismatch")
        if record.get("repository_identity") != repository_identity:
            errors.append("authorization repository identity mismatch")
        if record.get("repository_baseline_commit") != repository_baseline:
            errors.append("authorization repository baseline mismatch")
        execution_context = wop.data.get("execution_context", {})
        if execution_context.get("repository") != repository_identity:
            errors.append("WOP repository identity mismatch")
        if execution_context.get("baseline_commit") != repository_baseline:
            errors.append("WOP repository baseline mismatch")
        if not SHA256.fullmatch(str(record.get("decision_digest", ""))):
            errors.append("authorization decision digest is invalid")
        chain = record.get("authority_chain")
        if not isinstance(chain, list) or not chain:
            errors.append("authorization chain is required")
        if errors:
            raise LifecycleError("; ".join(sorted(errors)))

    @staticmethod
    def _validate_approval_history(checkpoint: Mapping[str, Any]) -> None:
        state = ApprovalStatus.PENDING
        allowed = {
            ApprovalStatus.PENDING: {
                ApprovalStatus.APPROVED,
                ApprovalStatus.REJECTED,
                ApprovalStatus.SUPERSEDED,
            },
            ApprovalStatus.APPROVED: {ApprovalStatus.SUPERSEDED},
            ApprovalStatus.REJECTED: {ApprovalStatus.SUPERSEDED},
            ApprovalStatus.SUPERSEDED: set(),
        }
        for event in checkpoint.get("history", []):
            if event.get("from") != state.value:
                raise LifecycleError("approval history origin mismatch")
            target = ApprovalStatus(event.get("to"))
            if target not in allowed[state]:
                raise LifecycleError("approval history transition is invalid")
            unsigned = {key: value for key, value in event.items() if key != "digest"}
            if event.get("digest") != digest(unsigned):
                raise LifecycleError("approval history digest mismatch")
            state = target
        if checkpoint.get("status") != state.value:
            raise LifecycleError("approval status disagrees with history")

    def _validate_stored_authorization(
        self,
        package: Mapping[str, Any],
        record: Mapping[str, Any],
        repository_identity: str,
        repository_baseline: str,
    ) -> None:
        if (
            record.get("schema_version") != 2
            or record.get("authoritative_decision_source") != "ZEUS"
            or record.get("enforcement_decision") != "AUTHORIZED"
            or record.get("wop_id") != package["wop_id"]
            or record.get("decision_digest")
            != package["authorization_decision_digest"]
            or repository_identity != package["repository_identity"]
            or repository_baseline != package["repository_baseline"]
            or record.get("repository_identity") != repository_identity
            or record.get("repository_baseline_commit") != repository_baseline
        ):
            raise LifecycleError("lifecycle authority verification failed")

    @staticmethod
    def _validate_prerequisites_and_dependencies(
        package: Mapping[str, Any],
        prerequisite_evidence: Iterable[str],
        satisfied_dependencies: Iterable[str],
    ) -> None:
        required_prerequisites = set(package["prerequisites"])
        if not required_prerequisites <= set(prerequisite_evidence):
            raise LifecycleError("lifecycle prerequisites are unsatisfied")
        required_dependencies = set(package["wop_dependencies"])
        if not required_dependencies <= set(satisfied_dependencies):
            raise LifecycleError("lifecycle dependencies are unsatisfied")

    @staticmethod
    def _validate_reservation(
        package: Mapping[str, Any], reservation: Reservation
    ) -> None:
        if (
            reservation.wop_id != package["wop_id"]
            or reservation.mission_id != package["mission_id"]
            or list(reservation.authority_chain) != package["authority_chain"]
            or list(reservation.requested_capabilities)
            != package["requested_capabilities"]
            or reservation.repository_baseline != package["repository_baseline"]
            or not reservation.planning_only
            or reservation.grants_authority
            or reservation.is_execution_lease
        ):
            raise LifecycleError("reservation does not match lifecycle authority boundary")
