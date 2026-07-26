#!/usr/bin/env python3
"""Deterministic supervised WOP assignment and dispatch."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.lib.emp.wop_lifecycle import WopLifecycleManager


SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class DispatchError(ValueError):
    """Fail-closed dispatch validation error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise DispatchError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _identifier(prefix: str, material: Any) -> str:
    return prefix + "-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material)))


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        value, indent=2, sort_keys=True, separators=(",", ": ")
    ) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@dataclass(frozen=True)
class ExecutionAgent:
    identity: str
    supported_capabilities: tuple[str, ...]
    supported_platform: str
    protocol_version: str
    qualification_status: str
    trust_level: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionAgent":
        agent = cls(
            identity=str(value.get("identity", "")),
            supported_capabilities=tuple(
                sorted(set(value.get("supported_capabilities", [])))
            ),
            supported_platform=str(value.get("supported_platform", "")),
            protocol_version=str(value.get("protocol_version", "")),
            qualification_status=str(value.get("qualification_status", "")),
            trust_level=str(value.get("trust_level", "")),
        )
        agent.validate()
        return agent

    def validate(self) -> None:
        if not all(
            (self.identity, self.supported_platform, self.protocol_version, self.trust_level)
        ):
            raise DispatchError("execution agent registration is incomplete")
        if self.qualification_status not in {"qualified", "suspended", "revoked"}:
            raise DispatchError("execution agent qualification status is invalid")

    def supports(self, capabilities: Iterable[str], platform: str, protocol: str) -> bool:
        return (
            self.qualification_status == "qualified"
            and self.supported_platform == platform
            and self.protocol_version == protocol
            and set(capabilities) <= set(self.supported_capabilities)
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "protocol_version": self.protocol_version,
            "qualification_status": self.qualification_status,
            "supported_capabilities": list(self.supported_capabilities),
            "supported_platform": self.supported_platform,
            "trust_level": self.trust_level,
        }


class AgentRegistry:
    """Immutable-by-identity qualified execution-agent registry."""

    def __init__(self, agents: Iterable[ExecutionAgent]) -> None:
        values = list(agents)
        identities = [agent.identity for agent in values]
        if len(identities) != len(set(identities)):
            raise DispatchError("duplicate execution agent identity")
        self._agents = {agent.identity: agent for agent in values}

    @classmethod
    def load(cls, path: Path | str) -> "AgentRegistry":
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DispatchError(f"invalid execution agent registry: {error}") from error
        if value.get("schema_version") != 1:
            raise DispatchError("execution agent registry schema version must be 1")
        return cls(ExecutionAgent.from_mapping(item) for item in value.get("agents", []))

    def qualified(
        self, identity: str, capabilities: Iterable[str], platform: str, protocol: str
    ) -> ExecutionAgent:
        agent = self._agents.get(identity)
        if agent is None:
            raise DispatchError("unknown execution agent")
        if not agent.supports(capabilities, platform, protocol):
            raise DispatchError("execution agent is not qualified for assignment")
        return agent


@dataclass(frozen=True)
class HumanApproval:
    approval_id: str
    assignment_checksum: str
    approver: str
    decision: str
    approved_at: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "HumanApproval":
        result = cls(
            approval_id=str(value.get("approval_id", "")),
            assignment_checksum=str(value.get("assignment_checksum", "")),
            approver=str(value.get("approver", "")),
            decision=str(value.get("decision", "")),
            approved_at=str(value.get("approved_at", "")),
        )
        if (
            not result.approval_id
            or not SHA256.fullmatch(result.assignment_checksum)
            or not result.approver
            or not result.approved_at
        ):
            raise DispatchError("human approval record is incomplete")
        if result.decision != "approved":
            raise DispatchError("explicit human approval is required")
        return result


@dataclass(frozen=True)
class ExecutionAssignment:
    canonical_data: str

    @classmethod
    def create(
        cls,
        *,
        package: Mapping[str, Any],
        intended_agent: str,
        expected_evidence: Iterable[str],
        dispatch_timestamp: datetime,
        approval_reference: str,
    ) -> "ExecutionAssignment":
        material = {
            "authority_chain": list(package["authority_chain"]),
            "authorization_decision_record": package[
                "authorization_decision_digest"
            ],
            "baseline_commit": package["repository_baseline"],
            "dispatch_timestamp": utc_text(dispatch_timestamp),
            "expected_evidence_requirements": sorted(set(expected_evidence)),
            "human_approval_reference": approval_reference,
            "intended_execution_agent": intended_agent,
            "mission_id": package["mission_id"],
            "repository_identity": package["repository_identity"],
            "required_capabilities": sorted(package["requested_capabilities"]),
            "schema_version": 1,
            "wop_digest": package["wop_digest"],
            "wop_id": package["wop_id"],
        }
        material["assignment_id"] = _identifier("EA", material)
        material["assignment_checksum"] = digest(material)
        result = cls(canonical_json(material))
        result.validate()
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionAssignment":
        result = cls(canonical_json(value))
        result.validate()
        return result

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def unsigned_checksum(self) -> str:
        return digest(
            {key: value for key, value in self.data.items() if key != "assignment_checksum"}
        )

    def validate(self) -> None:
        value = self.data
        required = {
            "assignment_id", "assignment_checksum", "authority_chain",
            "authorization_decision_record", "baseline_commit", "dispatch_timestamp",
            "expected_evidence_requirements", "human_approval_reference",
            "intended_execution_agent", "mission_id", "repository_identity",
            "required_capabilities", "schema_version", "wop_digest", "wop_id",
        }
        if set(value) != required or value.get("schema_version") != 1:
            raise DispatchError("execution assignment shape is invalid")
        if not COMMIT.fullmatch(str(value["baseline_commit"])):
            raise DispatchError("execution assignment baseline is invalid")
        if not SHA256.fullmatch(str(value["wop_digest"])):
            raise DispatchError("execution assignment WOP digest is invalid")
        if not SHA256.fullmatch(str(value["authorization_decision_record"])):
            raise DispatchError("execution assignment ADR reference is invalid")
        if value["assignment_checksum"] != self.unsigned_checksum():
            raise DispatchError("execution assignment checksum mismatch")
        unsigned = {
            key: value[key]
            for key in value
            if key not in {"assignment_id", "assignment_checksum"}
        }
        if value["assignment_id"] != _identifier("EA", unsigned):
            raise DispatchError("execution assignment identity is not reproducible")

    def to_json(self) -> str:
        return json.dumps(
            self.data, indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"


class FileOutbox:
    """One-way assignment delivery without execution or monitoring."""

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)

    def deliver(self, assignment: ExecutionAssignment) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"{assignment.data['assignment_id']}.json"
        serialized = assignment.to_json()
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            if target.read_text(encoding="utf-8") != serialized:
                raise DispatchError("immutable assignment delivery collision")
        return target


class SupervisedDispatcher:
    """Cross the dispatch boundary once, only with explicit approval."""

    def __init__(
        self,
        *,
        lifecycle: WopLifecycleManager,
        ledger_path: Path | str,
        registry: AgentRegistry,
        outbox: FileOutbox,
    ) -> None:
        self.lifecycle = lifecycle
        self.ledger_path = Path(ledger_path)
        self.registry = registry
        self.outbox = outbox
        self._ledger = self._load_ledger()
        self.validate()

    def _load_ledger(self) -> dict[str, Any]:
        if not self.ledger_path.is_file():
            return {
                "schema_version": 1,
                "dispatcher_id": "EMP-WOP-DISPATCH",
                "dispatches": {},
            }
        try:
            return json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DispatchError(f"invalid dispatch ledger: {error}") from error

    def prepare(
        self,
        *,
        wop_id: str,
        intended_agent: str,
        expected_evidence: Iterable[str],
        timestamp: datetime,
        approval_reference: str,
        repository_identity: str,
        repository_baseline: str,
        authorization_record: Mapping[str, Any],
        platform: str,
        protocol_version: str,
    ) -> ExecutionAssignment:
        package = self._ready_package(wop_id)
        self._validate_context(
            package, repository_identity, repository_baseline, authorization_record
        )
        self.registry.qualified(
            intended_agent,
            package["requested_capabilities"],
            platform,
            protocol_version,
        )
        return ExecutionAssignment.create(
            package=package,
            intended_agent=intended_agent,
            expected_evidence=expected_evidence,
            dispatch_timestamp=timestamp,
            approval_reference=approval_reference,
        )

    def dispatch(
        self,
        assignment: ExecutionAssignment,
        approval: HumanApproval,
        *,
        repository_identity: str,
        repository_baseline: str,
        authorization_record: Mapping[str, Any],
        platform: str,
        protocol_version: str,
    ) -> dict[str, Any]:
        assignment.validate()
        value = assignment.data
        package = self._ready_package(value["wop_id"])
        self._validate_context(
            package, repository_identity, repository_baseline, authorization_record
        )
        self.registry.qualified(
            value["intended_execution_agent"],
            value["required_capabilities"],
            platform,
            protocol_version,
        )
        if approval.assignment_checksum != value["assignment_checksum"]:
            raise DispatchError("human approval does not bind this assignment")
        if approval.approval_id != value["human_approval_reference"]:
            raise DispatchError("human approval reference mismatch")
        if value["wop_id"] in self._ledger["dispatches"]:
            raise DispatchError("WOP has already been dispatched")
        delivered = self.outbox.deliver(assignment)
        event = {
            "assignment_checksum": value["assignment_checksum"],
            "assignment_id": value["assignment_id"],
            "delivery_artifact": delivered.name,
            "from": "Ready",
            "human_approval_reference": approval.approval_id,
            "to": "Dispatched",
            "wop_id": value["wop_id"],
        }
        event["event_digest"] = digest(event)
        self._ledger["dispatches"][value["wop_id"]] = event
        self.validate()
        _atomic_write(self.ledger_path, self._ledger)
        return dict(event)

    def status(self, wop_id: str) -> str:
        if wop_id in self._ledger["dispatches"]:
            return "Dispatched"
        return self._ready_package(wop_id)["state"]

    def validate(self) -> None:
        if (
            self._ledger.get("schema_version") != 1
            or self._ledger.get("dispatcher_id") != "EMP-WOP-DISPATCH"
            or not isinstance(self._ledger.get("dispatches"), dict)
        ):
            raise DispatchError("dispatch ledger shape is invalid")
        for wop_id, event in self._ledger["dispatches"].items():
            if (
                event.get("wop_id") != wop_id
                or event.get("from") != "Ready"
                or event.get("to") != "Dispatched"
            ):
                raise DispatchError("dispatch transition is invalid")
            unsigned = {key: value for key, value in event.items() if key != "event_digest"}
            if event.get("event_digest") != digest(unsigned):
                raise DispatchError("dispatch event digest mismatch")

    def _ready_package(self, wop_id: str) -> Mapping[str, Any]:
        packages = self.lifecycle.data["packages"]
        package = packages.get(wop_id)
        if package is None:
            raise DispatchError("unknown WOP")
        if package.get("state") != "Ready":
            raise DispatchError("dispatch requires Ready lifecycle state")
        return package

    @staticmethod
    def _validate_context(
        package: Mapping[str, Any],
        repository_identity: str,
        repository_baseline: str,
        authorization_record: Mapping[str, Any],
    ) -> None:
        if (
            package["repository_identity"] != repository_identity
            or package["repository_baseline"] != repository_baseline
            or authorization_record.get("schema_version") != 2
            or authorization_record.get("authoritative_decision_source") != "ZEUS"
            or authorization_record.get("enforcement_decision") != "AUTHORIZED"
            or authorization_record.get("wop_id") != package["wop_id"]
            or authorization_record.get("decision_digest")
            != package["authorization_decision_digest"]
            or authorization_record.get("repository_identity") != repository_identity
            or authorization_record.get("repository_baseline_commit")
            != repository_baseline
        ):
            raise DispatchError("Zeus authorization or repository context is invalid")
