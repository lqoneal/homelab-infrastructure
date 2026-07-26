#!/usr/bin/env python3
"""Deterministic atomic post-qualification reconciliation and WOP closeout."""

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

from scripts.lib.emp.evidence_qualification import (
    DigestFixtureSignatureVerifier,
    EvidencePackage,
    QualificationReport,
)
from scripts.lib.emp.wop_dispatch import ExecutionAssignment


class ReconciliationError(ValueError):
    """Fail-closed reconciliation error."""


RECORD_KINDS = {
    "project_state",
    "work_registry",
    "mission_registry",
    "wop_lifecycle",
    "execution_session",
    "qualification_history",
    "completion_records",
    "resume_state",
    "progress_tracking",
    "controlled_document",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ReconciliationError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def identifier(prefix: str, material: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))


@dataclass(frozen=True)
class ReconciliationUpdate:
    target_record: str
    record_kind: str
    expected_current_revision: str
    resulting_value: Any
    modification_reason: str

    @property
    def expected_resulting_revision(self) -> str:
        return digest(self.resulting_value)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "expected_current_revision": self.expected_current_revision,
            "expected_resulting_revision": self.expected_resulting_revision,
            "modification_reason": self.modification_reason,
            "record_kind": self.record_kind,
            "resulting_value": deepcopy(self.resulting_value),
            "target_record": self.target_record,
        }


@dataclass(frozen=True)
class ReconciliationPlan:
    canonical_data: str

    @classmethod
    def create(
        cls,
        *,
        wop_id: str,
        qualification_report_id: str,
        updates: Iterable[ReconciliationUpdate],
        declared_scope: Iterable[str],
        approval_reference: str,
    ) -> "ReconciliationPlan":
        scope = sorted(set(declared_scope))
        values = sorted(
            (update.to_mapping() for update in updates),
            key=lambda item: (item["record_kind"], item["target_record"]),
        )
        targets = [item["target_record"] for item in values]
        if len(targets) != len(set(targets)):
            raise ReconciliationError("reconciliation targets must be unique")
        if not approval_reference:
            raise ReconciliationError("approved plan reference is required")
        for item in values:
            if item["record_kind"] not in RECORD_KINDS:
                raise ReconciliationError("unknown authoritative record kind")
            if item["target_record"] not in scope:
                raise ReconciliationError(
                    "reconciliation target is outside WOP declared scope"
                )
        material = {
            "approval_reference": approval_reference,
            "declared_scope": scope,
            "originating_wop": wop_id,
            "qualification_report_reference": qualification_report_id,
            "schema_version": 1,
            "targets": values,
        }
        material["plan_id"] = identifier("RECONCILIATION", material)
        material["plan_digest"] = digest(material)
        result = cls(canonical_json(material))
        result.validate()
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReconciliationPlan":
        result = cls(canonical_json(value))
        result.validate()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def validate(self) -> None:
        value = self.data
        required = {
            "approval_reference",
            "declared_scope",
            "originating_wop",
            "plan_digest",
            "plan_id",
            "qualification_report_reference",
            "schema_version",
            "targets",
        }
        if set(value) != required or value.get("schema_version") != 1:
            raise ReconciliationError("Reconciliation Plan shape is invalid")
        targets = value["targets"]
        if targets != sorted(
            targets, key=lambda item: (item["record_kind"], item["target_record"])
        ):
            raise ReconciliationError("Reconciliation Plan ordering is invalid")
        unsigned = {
            key: item for key, item in value.items() if key != "plan_digest"
        }
        if value["plan_digest"] != digest(unsigned):
            raise ReconciliationError("Reconciliation Plan digest mismatch")
        identity_material = {
            key: item for key, item in unsigned.items() if key != "plan_id"
        }
        if value["plan_id"] != identifier("RECONCILIATION", identity_material):
            raise ReconciliationError("Reconciliation Plan identity mismatch")
        for target in targets:
            if target["record_kind"] not in RECORD_KINDS:
                raise ReconciliationError("unknown authoritative record kind")
            if target["expected_resulting_revision"] != digest(
                target["resulting_value"]
            ):
                raise ReconciliationError("planned resulting revision mismatch")
            if target["target_record"] not in value["declared_scope"]:
                raise ReconciliationError(
                    "Reconciliation Plan exceeds its declared scope"
                )


@dataclass(frozen=True)
class CompletionRecord:
    canonical_data: str

    @classmethod
    def create(
        cls,
        *,
        mission_id: str,
        wop_id: str,
        assignment_id: str,
        session_id: str,
        qualification_report_id: str,
        evidence_package_id: str,
        repository_identity: str,
        baseline_before: str,
        baseline_after: str,
        reconciliation_summary: str,
        modified_records: Iterable[str],
        completion_timestamp: datetime,
        plan_id: str,
    ) -> "CompletionRecord":
        material = {
            "assignment_id": assignment_id,
            "baseline_after_reconciliation": baseline_after,
            "baseline_before_reconciliation": baseline_before,
            "completion_timestamp": utc_text(completion_timestamp),
            "evidence_package_id": evidence_package_id,
            "execution_session_id": session_id,
            "mission_id": mission_id,
            "modified_authoritative_records": sorted(set(modified_records)),
            "qualification_report_id": qualification_report_id,
            "reconciliation_plan_id": plan_id,
            "reconciliation_summary": reconciliation_summary,
            "repository_identity": repository_identity,
            "schema_version": 1,
            "wop_id": wop_id,
        }
        material["completion_id"] = identifier("COMPLETION", material)
        material["deterministic_digest"] = digest(material)
        result = cls(canonical_json(material))
        result.validate()
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CompletionRecord":
        result = cls(canonical_json(value))
        result.validate()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def validate(self) -> None:
        value = self.data
        required = {
            "assignment_id",
            "baseline_after_reconciliation",
            "baseline_before_reconciliation",
            "completion_id",
            "completion_timestamp",
            "deterministic_digest",
            "evidence_package_id",
            "execution_session_id",
            "mission_id",
            "modified_authoritative_records",
            "qualification_report_id",
            "reconciliation_plan_id",
            "reconciliation_summary",
            "repository_identity",
            "schema_version",
            "wop_id",
        }
        if set(value) != required or value.get("schema_version") != 1:
            raise ReconciliationError("Completion Record shape is invalid")
        unsigned = {
            key: item for key, item in value.items() if key != "deterministic_digest"
        }
        if value["deterministic_digest"] != digest(unsigned):
            raise ReconciliationError("Completion Record digest mismatch")
        identity_material = {
            key: item for key, item in unsigned.items() if key != "completion_id"
        }
        if value["completion_id"] != identifier("COMPLETION", identity_material):
            raise ReconciliationError("Completion Record identity mismatch")


class AuthoritativeStateStore:
    """One-file authoritative state transaction boundary."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "schema_version": 1,
                "store_id": "EMP-AUTHORITATIVE-ENGINEERING-STATE",
                "records": {},
                "completion_records": {},
            }
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ReconciliationError(f"invalid authoritative state: {error}") from error
        validate_store(value)
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        validate_store(value)
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


def validate_store(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema_version") != 1
        or value.get("store_id") != "EMP-AUTHORITATIVE-ENGINEERING-STATE"
        or not isinstance(value.get("records"), dict)
        or not isinstance(value.get("completion_records"), dict)
    ):
        raise ReconciliationError("authoritative state store shape is invalid")
    for record_id, record in value["records"].items():
        if (
            not isinstance(record, Mapping)
            or record.get("record_id") != record_id
            or record.get("record_kind") not in RECORD_KINDS
            or record.get("revision") != digest(record.get("value"))
        ):
            raise ReconciliationError("authoritative record revision is invalid")
    for completion_id, record in value["completion_records"].items():
        completion = CompletionRecord.from_mapping(record)
        if completion.data["completion_id"] != completion_id:
            raise ReconciliationError("completion inventory identity mismatch")


class ConsistencyVerifier:
    """Cross-record closeout consistency verification."""

    REQUIRED_KINDS = {
        "project_state",
        "work_registry",
        "mission_registry",
        "wop_lifecycle",
        "execution_session",
        "qualification_history",
        "resume_state",
        "progress_tracking",
    }

    def verify(
        self,
        state: Mapping[str, Any],
        *,
        wop_id: str,
        mission_id: str,
        qualification_report_id: str,
        completion_id: str,
    ) -> None:
        records = list(state["records"].values())
        by_kind = {
            record["record_kind"]: record["value"]
            for record in records
            if record["record_kind"] in self.REQUIRED_KINDS
        }
        missing = sorted(self.REQUIRED_KINDS - set(by_kind))
        if missing:
            raise ReconciliationError(
                "required authoritative closeout records missing: " + ",".join(missing)
            )
        if by_kind["project_state"].get("current_status") != "reconciled":
            raise ReconciliationError("Project State is not reconciled")
        if by_kind["work_registry"].get("wops", {}).get(wop_id) != "Closed":
            raise ReconciliationError("Work Registry WOP is not Closed")
        if by_kind["mission_registry"].get("missions", {}).get(mission_id) != "completed":
            raise ReconciliationError("mission registry state is not completed")
        lifecycle = by_kind["wop_lifecycle"]
        required_path = [
            "Ready",
            "Dispatched",
            "Executing",
            "Qualified",
            "Reconciling",
            "Closed",
        ]
        if lifecycle.get("state") != "Closed" or lifecycle.get("history") != required_path:
            raise ReconciliationError("WOP lifecycle closeout path is inconsistent")
        if by_kind["execution_session"].get("closeout_status") != "Closed":
            raise ReconciliationError("Execution Session closeout is inconsistent")
        if (
            qualification_report_id
            not in by_kind["qualification_history"].get("qualification_reports", [])
        ):
            raise ReconciliationError("qualification history is inconsistent")
        resume = by_kind["resume_state"]
        if (
            resume.get("completed_wop") != wop_id
            or resume.get("completed_mission") != mission_id
            or resume.get("current_engineering_status") != "reconciled"
            or "pending_work" not in resume
            or "next_eligible_mission" not in resume
        ):
            raise ReconciliationError("resume synchronization is inconsistent")
        if (
            by_kind["progress_tracking"].get("completed_wop") != wop_id
            or by_kind["progress_tracking"].get("qualification_report_id")
            != qualification_report_id
        ):
            raise ReconciliationError("progress tracking is inconsistent")
        completion = state["completion_records"].get(completion_id)
        if completion is None:
            raise ReconciliationError("Completion Record is missing")
        CompletionRecord.from_mapping(completion)


class ReconciliationEngine:
    """Execute approved scoped closeout as one logical transaction."""

    def __init__(self, store: AuthoritativeStateStore) -> None:
        self.store = store
        self._state = store.load()

    @property
    def state(self) -> dict[str, Any]:
        return deepcopy(self._state)

    def execute(
        self,
        *,
        plan: ReconciliationPlan,
        qualification_report: QualificationReport,
        evidence_package: EvidencePackage,
        assignment: ExecutionAssignment,
        execution_session: Mapping[str, Any],
        artifacts: Mapping[str, bytes],
        repository_identity: str,
        baseline_before: str,
        baseline_after: str,
        mission_id: str,
        wop_id: str,
        completion_timestamp: datetime,
        reconciliation_summary: str,
        wop_declared_scope: Iterable[str],
    ) -> CompletionRecord:
        plan.validate()
        qualification_report.validate()
        assignment.validate()
        self._qualification_gate(
            qualification_report=qualification_report,
            evidence_package=evidence_package,
            assignment=assignment,
            execution_session=execution_session,
            artifacts=artifacts,
            repository_identity=repository_identity,
            baseline_before=baseline_before,
            mission_id=mission_id,
            wop_id=wop_id,
        )
        expected_completion = CompletionRecord.create(
            mission_id=mission_id,
            wop_id=wop_id,
            assignment_id=assignment.data["assignment_id"],
            session_id=execution_session["session_id"],
            qualification_report_id=qualification_report.data["qualification_id"],
            evidence_package_id=evidence_package.data["evidence_package_id"],
            repository_identity=repository_identity,
            baseline_before=baseline_before,
            baseline_after=baseline_after,
            reconciliation_summary=reconciliation_summary,
            modified_records=[
                target["target_record"] for target in plan.data["targets"]
            ],
            completion_timestamp=completion_timestamp,
            plan_id=plan.data["plan_id"],
        )
        completion_id = expected_completion.data["completion_id"]
        existing = self._state["completion_records"].get(completion_id)
        if existing is not None:
            existing_record = CompletionRecord.from_mapping(existing)
            if existing_record.canonical_data != expected_completion.canonical_data:
                raise ReconciliationError("immutable Completion Record collision")
            return existing_record
        if plan.data["originating_wop"] != wop_id or plan.data[
            "qualification_report_reference"
        ] != qualification_report.data["qualification_id"]:
            raise ReconciliationError("Reconciliation Plan authority binding mismatch")
        supplied_scope = sorted(set(wop_declared_scope))
        if plan.data["declared_scope"] != supplied_scope:
            raise ReconciliationError("WOP reconciliation scope binding mismatch")

        candidate = deepcopy(self._state)
        for target in plan.data["targets"]:
            record = candidate["records"].get(target["target_record"])
            if record is None:
                raise ReconciliationError(
                    f"unknown authoritative target: {target['target_record']}"
                )
            if (
                record["record_kind"] != target["record_kind"]
                or record["revision"] != target["expected_current_revision"]
            ):
                raise ReconciliationError("authoritative target revision mismatch")
            record["value"] = deepcopy(target["resulting_value"])
            record["revision"] = target["expected_resulting_revision"]
        candidate["completion_records"][completion_id] = expected_completion.data
        ConsistencyVerifier().verify(
            candidate,
            wop_id=wop_id,
            mission_id=mission_id,
            qualification_report_id=qualification_report.data["qualification_id"],
            completion_id=completion_id,
        )
        self.store.save(candidate)
        self._state = candidate
        return expected_completion

    @staticmethod
    def _qualification_gate(
        *,
        qualification_report: QualificationReport,
        evidence_package: EvidencePackage,
        assignment: ExecutionAssignment,
        execution_session: Mapping[str, Any],
        artifacts: Mapping[str, bytes],
        repository_identity: str,
        baseline_before: str,
        mission_id: str,
        wop_id: str,
    ) -> None:
        report = qualification_report.data
        package = evidence_package.data
        assignment_data = assignment.data
        if report["qualification_decision"] != "PASS":
            raise ReconciliationError("PASS Qualification Report is required")
        try:
            evidence_package.validate_structure()
        except Exception as error:
            raise ReconciliationError("Evidence Package integrity failed") from error
        if not DigestFixtureSignatureVerifier().verify(evidence_package):
            raise ReconciliationError("Evidence Package signature failed")
        manifest = {
            item["artifact_identifier"]: item["digest"]
            for item in package["evidence_manifest"]
        }
        actual = {
            artifact_id: hashlib.sha256(content).hexdigest()
            for artifact_id, content in artifacts.items()
        }
        if actual != manifest:
            raise ReconciliationError("Evidence Package artifact digest failed")
        bindings = (
            report["evidence_package_id"] == package["evidence_package_id"],
            package["repository_identity"] == repository_identity,
            package["baseline_commit"] == baseline_before,
            package["assignment_id"] == assignment_data["assignment_id"],
            package["execution_session_id"] == execution_session.get("session_id"),
            package["wop_id"] == wop_id == assignment_data["wop_id"],
            package["mission_id"] == mission_id == assignment_data["mission_id"],
            execution_session.get("current_execution_state") == "Completed",
        )
        if not all(bindings):
            raise ReconciliationError("qualification reconciliation binding failed")
