#!/usr/bin/env python3
"""Immutable Evidence Packages and independent deterministic qualification."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from scripts.lib.emp.wop_dispatch import ExecutionAssignment


class QualificationError(ValueError):
    """Fail-closed evidence qualification error."""


class QualificationDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"
    UNVERIFIABLE = "UNVERIFIABLE"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def artifact_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise QualificationError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def identifier(prefix: str, material: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))


class PackageSignatureVerifier(Protocol):
    def verify(self, evidence_package: "EvidencePackage") -> bool: ...


class DigestFixtureSignatureVerifier:
    """Offline signature interface for deterministic qualification fixtures."""

    def verify(self, evidence_package: "EvidencePackage") -> bool:
        signature = evidence_package.data.get("package_signature", {})
        if not isinstance(signature, Mapping):
            return False
        return (
            signature.get("algorithm") == "sha256-digest-fixture"
            and signature.get("value") == evidence_package.data.get("package_checksum")
        )


@dataclass(frozen=True)
class EvidenceItem:
    artifact_identifier: str
    artifact_type: str
    producing_component: str
    digest: str
    wop_objective: str
    verification_requirement: str
    classification: str

    @classmethod
    def create(
        cls,
        *,
        artifact_identifier: str,
        artifact_type: str,
        producing_component: str,
        content: bytes,
        wop_objective: str,
        verification_requirement: str,
        classification: str,
    ) -> "EvidenceItem":
        item = cls(
            artifact_identifier=artifact_identifier,
            artifact_type=artifact_type,
            producing_component=producing_component,
            digest=artifact_digest(content),
            wop_objective=wop_objective,
            verification_requirement=verification_requirement,
            classification=classification,
        )
        item.validate()
        return item

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceItem":
        item = cls(
            artifact_identifier=str(value.get("artifact_identifier", "")),
            artifact_type=str(value.get("artifact_type", "")),
            producing_component=str(value.get("producing_component", "")),
            digest=str(value.get("digest", "")),
            wop_objective=str(value.get("wop_objective", "")),
            verification_requirement=str(
                value.get("verification_requirement", "")
            ),
            classification=str(value.get("classification", "")),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if not all(
            (
                self.artifact_identifier,
                self.artifact_type,
                self.producing_component,
                self.wop_objective,
                self.verification_requirement,
            )
        ):
            raise QualificationError("evidence manifest item is incomplete")
        if self.classification not in {"required", "optional"}:
            raise QualificationError("evidence classification is invalid")
        if len(self.digest) != 64:
            raise QualificationError("evidence artifact digest is invalid")

    def to_mapping(self) -> dict[str, str]:
        return {
            "artifact_identifier": self.artifact_identifier,
            "artifact_type": self.artifact_type,
            "classification": self.classification,
            "digest": self.digest,
            "producing_component": self.producing_component,
            "verification_requirement": self.verification_requirement,
            "wop_objective": self.wop_objective,
        }


@dataclass(frozen=True)
class EvidencePackage:
    canonical_data: str

    @classmethod
    def create(
        cls,
        *,
        assignment: ExecutionAssignment,
        execution_session_id: str,
        execution_agent_identity: str,
        evidence_items: Iterable[EvidenceItem],
        required_evidence: Iterable[str],
        produced_evidence: Iterable[str],
        completion_metadata: Mapping[str, Any],
        package_timestamp: datetime,
        signature_key_id: str,
    ) -> "EvidencePackage":
        assignment.validate()
        ea = assignment.data
        items = sorted(
            (item.to_mapping() for item in evidence_items),
            key=lambda item: item["artifact_identifier"],
        )
        identifiers = [item["artifact_identifier"] for item in items]
        if len(identifiers) != len(set(identifiers)):
            raise QualificationError("evidence manifest identifiers must be unique")
        material = {
            "artifact_digests": {
                item["artifact_identifier"]: item["digest"] for item in items
            },
            "assignment_id": ea["assignment_id"],
            "baseline_commit": ea["baseline_commit"],
            "completion_metadata": deepcopy(dict(completion_metadata)),
            "evidence_manifest": items,
            "execution_agent_identity": execution_agent_identity,
            "execution_session_id": execution_session_id,
            "mission_id": ea["mission_id"],
            "package_timestamp": utc_text(package_timestamp),
            "produced_evidence_declarations": sorted(set(produced_evidence)),
            "repository_identity": ea["repository_identity"],
            "required_evidence_declarations": sorted(set(required_evidence)),
            "schema_version": 1,
            "wop_id": ea["wop_id"],
        }
        material["evidence_package_id"] = identifier("EP", material)
        material["package_checksum"] = digest(material)
        material["package_signature"] = {
            "algorithm": "sha256-digest-fixture",
            "key_id": signature_key_id,
            "value": material["package_checksum"],
        }
        result = cls(canonical_json(material))
        result.validate_structure()
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidencePackage":
        result = cls(canonical_json(value))
        result.validate_structure()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def validate_structure(self) -> None:
        value = self.data
        required = {
            "artifact_digests",
            "assignment_id",
            "baseline_commit",
            "completion_metadata",
            "evidence_manifest",
            "evidence_package_id",
            "execution_agent_identity",
            "execution_session_id",
            "mission_id",
            "package_checksum",
            "package_signature",
            "package_timestamp",
            "produced_evidence_declarations",
            "repository_identity",
            "required_evidence_declarations",
            "schema_version",
            "wop_id",
        }
        if set(value) != required or value.get("schema_version") != 1:
            raise QualificationError("Evidence Package shape is invalid")
        items = [EvidenceItem.from_mapping(item) for item in value["evidence_manifest"]]
        identifiers = [item.artifact_identifier for item in items]
        if identifiers != sorted(identifiers) or len(identifiers) != len(
            set(identifiers)
        ):
            raise QualificationError("evidence manifest ordering or identity is invalid")
        expected_digests = {
            item.artifact_identifier: item.digest for item in items
        }
        if value["artifact_digests"] != expected_digests:
            raise QualificationError("artifact digest map disagrees with manifest")
        unsigned = {
            key: item
            for key, item in value.items()
            if key not in {"package_checksum", "package_signature"}
        }
        identity_material = {
            key: item for key, item in unsigned.items() if key != "evidence_package_id"
        }
        if value["evidence_package_id"] != identifier("EP", identity_material):
            raise QualificationError("Evidence Package identity is not reproducible")
        checksum_material = dict(unsigned)
        if value["package_checksum"] != digest(checksum_material):
            raise QualificationError("Evidence Package checksum mismatch")

    def to_json(self) -> str:
        return json.dumps(
            self.data, indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"


@dataclass(frozen=True)
class QualificationContract:
    wop_id: str
    mission_id: str
    assignment_id: str
    repository_identity: str
    baseline_commit: str
    required_evidence: tuple[str, ...]
    expected_evidence: tuple[str, ...]
    prohibited_evidence: tuple[str, ...]
    required_verification_steps: tuple[str, ...]
    objectives: tuple[tuple[str, tuple[str, ...]], ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "QualificationContract":
        objectives = tuple(
            (name, tuple(sorted(set(evidence_ids))))
            for name, evidence_ids in sorted(value.get("objectives", {}).items())
        )
        result = cls(
            wop_id=str(value.get("wop_id", "")),
            mission_id=str(value.get("mission_id", "")),
            assignment_id=str(value.get("assignment_id", "")),
            repository_identity=str(value.get("repository_identity", "")),
            baseline_commit=str(value.get("baseline_commit", "")),
            required_evidence=tuple(sorted(set(value.get("required_evidence", [])))),
            expected_evidence=tuple(sorted(set(value.get("expected_evidence", [])))),
            prohibited_evidence=tuple(
                sorted(set(value.get("prohibited_evidence", [])))
            ),
            required_verification_steps=tuple(
                sorted(set(value.get("required_verification_steps", [])))
            ),
            objectives=objectives,
        )
        if not all(
            (
                result.wop_id,
                result.mission_id,
                result.assignment_id,
                result.repository_identity,
                result.baseline_commit,
                result.objectives,
            )
        ):
            raise QualificationError("WOP qualification contract is incomplete")
        return result


@dataclass(frozen=True)
class QualificationReport:
    canonical_data: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "QualificationReport":
        result = cls(canonical_json(value))
        result.validate()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def validate(self) -> None:
        value = self.data
        required = {
            "completeness_evaluation",
            "deterministic_digest",
            "evidence_package_id",
            "integrity_results",
            "missing_evidence",
            "qualification_decision",
            "qualification_id",
            "qualified_objectives",
            "reason_codes",
            "timestamp",
            "unexpected_evidence",
            "unqualified_objectives",
        }
        if set(value) != required:
            raise QualificationError("Qualification Report shape is invalid")
        QualificationDecision(value["qualification_decision"])
        unsigned = {
            key: item for key, item in value.items() if key != "deterministic_digest"
        }
        if value["deterministic_digest"] != digest(unsigned):
            raise QualificationError("Qualification Report digest mismatch")
        identity_material = {
            key: item
            for key, item in unsigned.items()
            if key != "qualification_id"
        }
        if value["qualification_id"] != identifier(
            "QUALIFICATION", identity_material
        ):
            raise QualificationError("Qualification Report identity mismatch")

    def to_json(self) -> str:
        return json.dumps(
            self.data, indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"


class QualificationEngine:
    """Qualify evidence independently of execution-agent assertions."""

    def evaluate(
        self,
        *,
        evidence_package: EvidencePackage,
        artifacts: Mapping[str, bytes],
        contract: QualificationContract,
        assignment: ExecutionAssignment,
        execution_session: Mapping[str, Any],
        signature_verifier: PackageSignatureVerifier,
    ) -> QualificationReport:
        package = evidence_package.data
        integrity: dict[str, bool] = {}
        reasons: list[str] = []
        try:
            evidence_package.validate_structure()
            integrity["package_structure"] = True
        except QualificationError:
            integrity["package_structure"] = False
            reasons.append("PACKAGE_INTEGRITY_FAILURE")
        integrity["signature"] = signature_verifier.verify(evidence_package)
        if not integrity["signature"]:
            reasons.append("SIGNATURE_FAILURE")
        assignment_data = assignment.data
        bindings = {
            "assignment": package.get("assignment_id") == contract.assignment_id
            == assignment_data.get("assignment_id"),
            "mission": package.get("mission_id") == contract.mission_id
            == assignment_data.get("mission_id"),
            "wop": package.get("wop_id") == contract.wop_id
            == assignment_data.get("wop_id"),
            "repository": package.get("repository_identity")
            == contract.repository_identity
            == assignment_data.get("repository_identity")
            == execution_session.get("repository_identity"),
            "baseline": package.get("baseline_commit") == contract.baseline_commit
            == assignment_data.get("baseline_commit")
            == execution_session.get("baseline_commit"),
            "session": package.get("execution_session_id")
            == execution_session.get("session_id"),
            "agent": package.get("execution_agent_identity")
            == assignment_data.get("intended_execution_agent")
            == execution_session.get("execution_agent_identity"),
        }
        integrity.update({f"binding_{key}": value for key, value in bindings.items()})
        if not all(bindings.values()):
            reasons.append("IDENTITY_BINDING_FAILURE")
        raw_manifest = package.get("evidence_manifest", [])
        if not isinstance(raw_manifest, list):
            raw_manifest = []
        manifest = {
            str(item.get("artifact_identifier")): item
            for item in raw_manifest
            if isinstance(item, Mapping) and item.get("artifact_identifier")
        }
        artifact_checks = {
            artifact_id: artifact_id in artifacts
            and artifact_digest(artifacts[artifact_id]) == item.get("digest")
            for artifact_id, item in manifest.items()
        }
        integrity["artifact_digests"] = all(artifact_checks.values())
        integrity["artifact_set_exact"] = set(artifacts) == set(manifest)
        if not integrity["artifact_digests"] or not integrity["artifact_set_exact"]:
            reasons.append("ARTIFACT_INTEGRITY_FAILURE")

        raw_produced = package.get("produced_evidence_declarations", [])
        produced = set(raw_produced) if isinstance(raw_produced, list) else set()
        manifest_ids = set(manifest)
        declared_matches_manifest = produced == manifest_ids
        integrity["declarations_match_manifest"] = declared_matches_manifest
        if not declared_matches_manifest:
            reasons.append("DECLARATION_MISMATCH")
        raw_required = package.get("required_evidence_declarations", [])
        required = set(contract.required_evidence) | (
            set(raw_required) if isinstance(raw_required, list) else set()
        )
        expected = set(contract.expected_evidence)
        missing = sorted((required | expected) - produced)
        prohibited = sorted(set(contract.prohibited_evidence) & produced)
        unexpected = sorted(produced - (required | expected))
        completion_metadata = package.get("completion_metadata", {})
        if not isinstance(completion_metadata, Mapping):
            completion_metadata = {}
        raw_steps = completion_metadata.get("completed_verification_steps", [])
        verification_steps = set(raw_steps) if isinstance(raw_steps, list) else set()
        missing_steps = sorted(
            set(contract.required_verification_steps) - verification_steps
        )
        completion_asserted = (
            completion_metadata.get("execution_complete") is True
        )
        session_complete = (
            execution_session.get("current_execution_state") == "Completed"
        )

        qualified_objectives = []
        unqualified_objectives = []
        for objective, evidence_ids in contract.objectives:
            if set(evidence_ids) <= produced and not (
                set(evidence_ids) & set(prohibited)
            ):
                qualified_objectives.append(objective)
            else:
                unqualified_objectives.append(objective)

        integrity_failed = not all(integrity.values())
        if integrity_failed:
            decision = QualificationDecision.UNVERIFIABLE
        elif prohibited:
            reasons.append("PROHIBITED_EVIDENCE_PRESENT")
            decision = QualificationDecision.FAIL
        elif not completion_asserted or not session_complete:
            reasons.append("EXECUTION_STATE_INCONSISTENT")
            decision = QualificationDecision.FAIL
        elif missing or missing_steps or unqualified_objectives:
            if missing:
                reasons.append("REQUIRED_EVIDENCE_MISSING")
            if missing_steps:
                reasons.append("VERIFICATION_STEP_MISSING")
            if unqualified_objectives:
                reasons.append("OBJECTIVE_UNSUPPORTED")
            decision = QualificationDecision.INCOMPLETE
        else:
            reasons.append("EVIDENCE_CONTRACT_SATISFIED")
            decision = QualificationDecision.PASS
        completeness = {
            "completion_asserted": completion_asserted,
            "execution_session_completed": session_complete,
            "missing_verification_steps": missing_steps,
            "required_count": len(required | expected),
            "produced_count": len(produced),
        }
        timestamp = package.get("package_timestamp", "")
        identity_material = {
            "completeness_evaluation": completeness,
            "evidence_package_id": package.get("evidence_package_id", ""),
            "integrity_results": dict(sorted(integrity.items())),
            "missing_evidence": missing,
            "qualification_decision": decision.value,
            "qualified_objectives": sorted(qualified_objectives),
            "reason_codes": sorted(set(reasons)),
            "timestamp": timestamp,
            "unexpected_evidence": unexpected,
            "unqualified_objectives": sorted(unqualified_objectives),
        }
        report = dict(identity_material)
        report["qualification_id"] = identifier("QUALIFICATION", identity_material)
        report["deterministic_digest"] = digest(report)
        return QualificationReport.from_mapping(report)


class QualificationHistory:
    """Append-only replayable history of immutable reports."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._data = self._load()
        self.validate()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "schema_version": 1,
                "history_id": "EMP-QUALIFICATION-HISTORY",
                "packages": {},
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise QualificationError(f"invalid qualification history: {error}") from error

    def record(self, report: QualificationReport) -> None:
        report.validate()
        package_id = report.data["evidence_package_id"]
        entries = self._data["packages"].setdefault(package_id, [])
        entries.append(report.data)
        try:
            self.validate()
            self._save()
        except Exception:
            entries.pop()
            if not entries:
                self._data["packages"].pop(package_id, None)
            raise

    def replay(self, evidence_package_id: str) -> list[QualificationReport]:
        return [
            QualificationReport.from_mapping(item)
            for item in self._data["packages"].get(evidence_package_id, [])
        ]

    def validate(self) -> None:
        if (
            self._data.get("schema_version") != 1
            or self._data.get("history_id") != "EMP-QUALIFICATION-HISTORY"
            or not isinstance(self._data.get("packages"), dict)
        ):
            raise QualificationError("qualification history shape is invalid")
        for package_id, reports in self._data["packages"].items():
            if not reports:
                raise QualificationError("qualification history cannot be empty")
            canonical = None
            for value in reports:
                report = QualificationReport.from_mapping(value)
                if report.data["evidence_package_id"] != package_id:
                    raise QualificationError("qualification history binding mismatch")
                if canonical is None:
                    canonical = report.canonical_data
                elif report.canonical_data != canonical:
                    raise QualificationError(
                        "re-qualification result is not deterministic"
                    )

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            self._data, indent=2, sort_keys=True, separators=(",", ": ")
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
