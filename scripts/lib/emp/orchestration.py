#!/usr/bin/env python3
"""Deterministic human-governed EMP mission orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.lib.emp.wop_admission import verify_accepted_record


class OrchestrationError(ValueError):
    """Fail-closed orchestration error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise OrchestrationError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def identity(prefix: str, value: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(value)))


class OrchestrationStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": 1, "missions": {}, "selection_records": {},
                "approval_requests": {}, "configured_policy": None,
            }
        try:
            value = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise OrchestrationError(f"invalid orchestration store: {error}") from error
        if not isinstance(value, dict):
            raise OrchestrationError("orchestration store must be an object")
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
        descriptor, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=".zeus.")
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


@dataclass(frozen=True)
class SelectionDecisionRecord:
    canonical_data: str

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def to_json(self) -> str:
        return json.dumps(self.data, indent=2, sort_keys=True) + "\n"

    def validate(self) -> None:
        value = self.data
        checksum = value.pop("checksum", None)
        if checksum != digest(value):
            raise OrchestrationError("Selection Decision Record checksum mismatch")
        material = {k: v for k, v in value.items() if k != "selection_id"}
        if value["selection_id"] != identity("SELECTION", material):
            raise OrchestrationError("Selection Decision Record identity mismatch")


class MissionOrchestrator:
    """Business logic consumed by the deliberately thin operator interface."""

    def __init__(self, store: OrchestrationStore):
        self.store = store
        self._data = store.load()
        self.validate()

    @property
    def data(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def submit(
        self, *, admission_record: Path | str, repository_identity: str,
        baseline_commit: str, priority: int, staging_order: int,
        dependencies: Iterable[str], required_approvals: Iterable[str],
        resources_available: bool, blocking_conditions: Iterable[str],
        estimated_impact: str, affected_repositories: Iterable[str],
        queue_timestamp: datetime,
    ) -> dict[str, Any]:
        record = json.loads(Path(admission_record).read_text())
        wop_id, mission_id = record.get("wop_id"), record.get("mission_id")
        if not verify_accepted_record(
            admission_record, expected_repository=repository_identity,
            expected_wop=wop_id,
        ):
            raise OrchestrationError("only an ACCEPTED admission record may enter queue")
        if mission_id in self._data["missions"]:
            raise OrchestrationError("mission is already queued")
        if not isinstance(priority, int) or priority < 0:
            raise OrchestrationError("priority must be a non-negative integer")
        mission = {
            "mission_id": mission_id, "wop_id": wop_id, "staging_status": "staged",
            "priority": priority, "staging_order": staging_order,
            "dependencies": sorted(set(dependencies)), "dependency_status": {},
            "admission_status": "ACCEPTED", "admission_id": record["admission_id"],
            "authorization_status": "not_authorized",
            "queue_timestamp": utc_text(queue_timestamp), "eligibility_state": "unknown",
            "eligibility_reasons": [], "operator_decision_history": [],
            "required_approvals": sorted(set(required_approvals)),
            "repository_identity": repository_identity,
            "compatible_baseline": baseline_commit,
            "required_execution_resources_available": bool(resources_available),
            "blocking_conditions": sorted(set(blocking_conditions)),
            "mission_state": "staged", "estimated_impact": estimated_impact,
            "affected_repositories": sorted(set(affected_repositories)),
            "selection_id": None, "approval_request_id": None,
        }
        self._data["missions"][mission_id] = mission
        self._persist()
        return deepcopy(mission)

    def evaluate(self, *, observed_repository: str, observed_baseline: str,
                 completed_missions: Iterable[str]) -> list[dict[str, Any]]:
        completed = set(completed_missions)
        result = []
        for mission in self._data["missions"].values():
            reasons = []
            dep = {item: item in completed for item in mission["dependencies"]}
            if mission["admission_status"] != "ACCEPTED":
                reasons.append("ADMISSION_NOT_ACCEPTED")
            if not mission["required_approvals"]:
                reasons.append("REQUIRED_APPROVAL_CONFIGURATION_MISSING")
            if not all(dep.values()):
                reasons.append("DEPENDENCY_UNSATISFIED")
            if mission["repository_identity"] != observed_repository:
                reasons.append("REPOSITORY_IDENTITY_MISMATCH")
            if mission["compatible_baseline"] != observed_baseline:
                reasons.append("BASELINE_MISMATCH")
            if not mission["required_execution_resources_available"]:
                reasons.append("EXECUTION_RESOURCES_UNAVAILABLE")
            if mission["blocking_conditions"]:
                reasons.append("BLOCKING_CONDITION")
            if mission["mission_state"] != "staged":
                reasons.append("MISSION_STATE_INVALID")
            mission["dependency_status"] = dep
            mission["eligibility_reasons"] = sorted(reasons)
            mission["eligibility_state"] = "eligible" if not reasons else "blocked"
            result.append(deepcopy(mission))
        self._persist()
        return sorted(result, key=self._order)

    def select(self, *, policy_id: str, timestamp: datetime) -> SelectionDecisionRecord:
        if not policy_id or self._data["configured_policy"] != policy_id:
            raise OrchestrationError("selection requires an explicitly configured policy")
        candidates = sorted(
            (m for m in self._data["missions"].values()
             if m["eligibility_state"] == "eligible"), key=self._order
        )
        if not candidates:
            raise OrchestrationError("no eligible mission")
        selected = candidates[0]
        rejected = []
        for mission in sorted(self._data["missions"].values(), key=self._order):
            if mission["mission_id"] == selected["mission_id"]:
                continue
            reasons = mission["eligibility_reasons"] or ["LOWER_POLICY_ORDER"]
            rejected.append({"mission_id": mission["mission_id"],
                             "reason_codes": sorted(reasons)})
        material = {
            "selected_mission": selected["mission_id"],
            "eligible_mission_set": sorted(m["mission_id"] for m in candidates),
            "rejected_mission_set": rejected,
            "dependency_evaluations": {
                m["mission_id"]: m["dependency_status"]
                for m in sorted(self._data["missions"].values(), key=self._order)
            },
            "priority_evaluations": {
                m["mission_id"]: m["priority"] for m in candidates
            },
            "policy_evaluations": {"policy_id": policy_id,
                                   "ordering": "priority,staging_order,queue_timestamp,mission_id"},
            "timestamp": utc_text(timestamp),
        }
        material["selection_id"] = identity("SELECTION", material)
        material["checksum"] = digest(material)
        decision = SelectionDecisionRecord(canonical_json(material))
        decision.validate()
        approval_material = {
            "selection_id": material["selection_id"], "mission_id": selected["mission_id"],
            "wop_id": selected["wop_id"],
        }
        request_id = identity("APPROVAL", approval_material)
        self._data["selection_records"][material["selection_id"]] = decision.data
        self._data["approval_requests"][request_id] = {
            **approval_material, "approval_request_id": request_id, "status": "PENDING",
            "estimated_impact": selected["estimated_impact"],
            "affected_repositories": selected["affected_repositories"], "history": [],
        }
        selected["selection_id"] = material["selection_id"]
        selected["approval_request_id"] = request_id
        selected["mission_state"] = "selected"
        selected["staging_status"] = "selected"
        self._persist()
        return decision

    def decide(self, approval_id: str, decision: str, *, operator: str,
               timestamp: datetime) -> dict[str, Any]:
        if decision not in {"APPROVE", "DECLINE"}:
            raise OrchestrationError("operator decision must be APPROVE or DECLINE")
        request = self._data["approval_requests"].get(approval_id)
        if request is None or request["status"] != "PENDING":
            raise OrchestrationError("approval request is unknown or terminal")
        request["status"] = "APPROVED" if decision == "APPROVE" else "DECLINED"
        event = {"decision": decision, "operator": operator,
                 "timestamp": utc_text(timestamp)}
        request["history"].append(event)
        mission = self._data["missions"][request["mission_id"]]
        mission["operator_decision_history"].append(event)
        if decision == "APPROVE":
            mission["authorization_status"] = "pending_existing_authorization"
            mission["mission_state"] = "approval_granted"
            mission["lifecycle_handoff"] = {
                "target": "Engineering Work Initiation",
                "admission_id": mission["admission_id"], "wop_id": mission["wop_id"],
                "operator_approval_id": approval_id,
            }
        else:
            mission["authorization_status"] = "not_authorized"
            mission["mission_state"] = "declined"
        self._persist()
        return deepcopy(request)

    def configure_policy(self, policy_id: str) -> None:
        if not policy_id:
            raise OrchestrationError("policy identifier is required")
        self._data["configured_policy"] = policy_id
        self._persist()

    def status(self) -> dict[str, Any]:
        missions = list(self._data["missions"].values())
        return {
            "staged_missions": sorted(m["mission_id"] for m in missions if m["mission_state"] == "staged"),
            "eligible_missions": sorted(m["mission_id"] for m in missions if m["eligibility_state"] == "eligible"),
            "blocked_missions": sorted(m["mission_id"] for m in missions if m["eligibility_state"] == "blocked"),
            "active_execution": [], "qualification_state": {}, "reconciliation_state": {},
            "completed_missions": sorted(m["mission_id"] for m in missions if m["mission_state"] == "completed"),
            "outstanding_approvals": sorted(k for k, v in self._data["approval_requests"].items() if v["status"] == "PENDING"),
        }

    def validate(self) -> None:
        required = {"schema_version", "missions", "selection_records",
                    "approval_requests", "configured_policy"}
        if set(self._data) != required or self._data["schema_version"] != 1:
            raise OrchestrationError("orchestration store shape is invalid")
        for record in self._data["selection_records"].values():
            SelectionDecisionRecord(canonical_json(record)).validate()

    @staticmethod
    def _order(mission: Mapping[str, Any]) -> tuple[Any, ...]:
        return (-mission["priority"], mission["staging_order"],
                mission["queue_timestamp"], mission["mission_id"])

    def _persist(self) -> None:
        self.validate()
        self.store.save(self._data)
