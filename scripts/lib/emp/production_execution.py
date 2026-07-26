#!/usr/bin/env python3
"""Production bindings for dispatcher readiness, invocation, EENS, and evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


class ProductionExecutionError(ValueError):
    """Production execution state is not valid or ready."""


SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
LIFECYCLE_EVENTS = (
    "mission.selected", "authority.resolved", "wop.resolved",
    "admission.accepted", "dispatch.authorized", "assignment.created",
    "agent.selected", "agent.invocation.requested", "agent.invocation.accepted",
    "execution.started", "progress.reported", "approval.required",
    "approval.resolved", "execution.interrupted", "execution.resumed",
    "execution.completed", "execution.failed", "evidence.submitted",
    "evidence.qualified", "reconciliation.started",
    "reconciliation.completed", "mission.closed",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ProductionExecutionError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def identifier(prefix: str, value: Any) -> str:
    return f"{prefix}-{uuid.uuid5(uuid.NAMESPACE_URL, canonical_bytes(value).decode())}"


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path: Path | str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProductionExecutionError(f"invalid controlled JSON record: {error}") from error
    if not isinstance(value, dict):
        raise ProductionExecutionError("controlled JSON record must be an object")
    return value


def verify_ssh_signature(
    payload: bytes, signature: Path | str, allowed_signers: Path | str,
    principal: str, namespace: str,
) -> None:
    result = subprocess.run(
        ["ssh-keygen", "-Y", "verify", "-f", str(allowed_signers),
         "-I", principal, "-n", namespace, "-s", str(signature)],
        input=payload, capture_output=True, check=False,
    )
    if result.returncode:
        raise ProductionExecutionError(
            "detached signature verification failed: "
            + result.stderr.decode(errors="replace").strip()
        )


def sign_ssh(payload: bytes, key: Path | str, namespace: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile() as stream:
        stream.write(payload)
        stream.flush()
        result = subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-q", "-f", str(key), "-n", namespace,
             stream.name], capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise ProductionExecutionError(result.stderr.strip())
        generated = Path(stream.name + ".sig")
        destination.write_bytes(generated.read_bytes())
        generated.unlink()


ACTIVATION_FIELDS = {
    "schema_version", "dispatcher_id", "implementation_version",
    "repository_identity", "repository_baseline", "policy_version", "status",
    "activating_authority", "activated_at", "supported_mission_classes",
    "supported_agent_classes", "eens_configuration", "evidence_configuration",
    "reconciliation_adapters", "revoked", "suspended", "record_digest",
}


def validate_activation(
    value: Mapping[str, Any], *, repository: str, baseline: str,
    require_active: bool = True,
) -> dict[str, Any]:
    record = deepcopy(dict(value))
    if set(record) != ACTIVATION_FIELDS or record.get("schema_version") != 1:
        raise ProductionExecutionError("dispatcher activation shape is invalid")
    expected = digest({k: v for k, v in record.items() if k != "record_digest"})
    if record["record_digest"] != expected:
        raise ProductionExecutionError("dispatcher activation digest mismatch")
    if record["repository_identity"] != repository:
        raise ProductionExecutionError("dispatcher activation repository mismatch")
    if record["repository_baseline"] != baseline:
        raise ProductionExecutionError("dispatcher activation baseline mismatch")
    if record["revoked"] or record["suspended"]:
        raise ProductionExecutionError("dispatcher activation is unavailable")
    if require_active and record["status"] != "ACTIVE":
        raise ProductionExecutionError("dispatcher is not active")
    return record


AGENT_REQUIRED = {
    "agent_id", "agent_type", "host_identity", "service_identity",
    "supported_mission_classes", "supported_tools", "repository_access_scope",
    "execution_constraints", "qualification_status", "qualification_evidence",
    "active", "last_validated_at", "trust_binding", "eens_identity",
    "evidence_signing_identity", "interruption_resume_capable",
    "concurrency_limit",
}


def validate_agent(
    value: Mapping[str, Any], *, mission_class: str, repository: str,
    require_qualified: bool = True,
) -> dict[str, Any]:
    agent = deepcopy(dict(value))
    if set(agent) != AGENT_REQUIRED:
        raise ProductionExecutionError("execution-agent registration shape is invalid")
    if not agent["agent_id"] or agent["agent_type"] == "fixture":
        raise ProductionExecutionError("fixture or unidentified agent is prohibited")
    if require_qualified and (
        agent["qualification_status"] != "QUALIFIED" or not agent["active"]
    ):
        raise ProductionExecutionError("execution agent is not active and qualified")
    if mission_class not in agent["supported_mission_classes"]:
        raise ProductionExecutionError("execution agent mission capability mismatch")
    if repository not in agent["repository_access_scope"]:
        raise ProductionExecutionError("execution agent repository scope mismatch")
    if not agent["qualification_evidence"] or not agent["trust_binding"]:
        raise ProductionExecutionError("execution agent trust or qualification is incomplete")
    if not agent["eens_identity"] or not agent["evidence_signing_identity"]:
        raise ProductionExecutionError("execution agent production identities are incomplete")
    if not agent["interruption_resume_capable"] or int(agent["concurrency_limit"]) < 1:
        raise ProductionExecutionError("execution agent lifecycle capability is insufficient")
    return agent


def load_registry(path: Path | str) -> list[dict[str, Any]]:
    value = load_json(path)
    if value.get("schema_version") != 2 or set(value) != {
        "schema_version", "registry_id", "agents", "registry_digest"
    }:
        raise ProductionExecutionError("production agent registry shape is invalid")
    unsigned = {k: v for k, v in value.items() if k != "registry_digest"}
    if value["registry_digest"] != digest(unsigned):
        raise ProductionExecutionError("production agent registry digest mismatch")
    identities = [item.get("agent_id") for item in value["agents"]]
    if len(identities) != len(set(identities)):
        raise ProductionExecutionError("duplicate production agent identity")
    return deepcopy(value["agents"])


class AuthenticatedEventLog:
    """Durable signed append-only event log with replay checkpoints."""

    def __init__(self, directory: Path | str, *, key: Path | str,
                 allowed_signers: Path | str, principal: str) -> None:
        self.directory = Path(directory)
        self.key = Path(key)
        self.allowed_signers = Path(allowed_signers)
        self.principal = principal

    def emit(self, event_type: str, mission_id: str, assignment_id: str,
             payload: Mapping[str, Any], *, at: datetime,
             idempotency_key: str) -> dict[str, Any]:
        material = {
            "schema_version": 1, "event_type": event_type,
            "mission_id": mission_id, "assignment_id": assignment_id,
            "producer": self.principal, "occurred_at": utc_text(at),
            "idempotency_key": idempotency_key, "payload": deepcopy(dict(payload)),
        }
        material["event_id"] = identifier("EENS", material)
        material["event_digest"] = digest(material)
        path = self.directory / f"{material['event_id']}.json"
        signature = path.with_suffix(".json.sig")
        if path.exists():
            if load_json(path) != material:
                raise ProductionExecutionError("EENS idempotency collision")
            verify_ssh_signature(canonical_bytes(material), signature,
                                 self.allowed_signers, self.principal, "zeus-eens")
            return material
        atomic_write(path, material)
        sign_ssh(canonical_bytes(material), self.key, "zeus-eens", signature)
        verify_ssh_signature(canonical_bytes(material), signature,
                             self.allowed_signers, self.principal, "zeus-eens")
        return material

    def replay(self, consumer: str, checkpoint: Path | str) -> list[dict[str, Any]]:
        events = sorted(
            (load_json(path) for path in self.directory.glob("EENS-*.json")),
            key=lambda item: (item["occurred_at"], item["event_id"]),
        )
        current = load_json(checkpoint).get("event_id") if Path(checkpoint).exists() else None
        if current:
            positions = [index for index, event in enumerate(events)
                         if event["event_id"] == current]
            events = events[positions[0] + 1:] if positions else events
        if events:
            atomic_write(Path(checkpoint), {
                "consumer": consumer, "event_id": events[-1]["event_id"],
                "event_digest": events[-1]["event_digest"],
            })
        return events


class LocalAuthenticatedAgent:
    """Local implementation of the production invocation contract."""

    def __init__(
        self, registration: Mapping[str, Any], state_directory: Path | str,
        handler: Callable[[Mapping[str, Any]], Mapping[str, Any]], *,
        agent_key: Path | str, allowed_signers: Path | str,
        invoking_principal: str,
    ) -> None:
        self.registration = deepcopy(dict(registration))
        self.directory = Path(state_directory)
        self.handler = handler
        self.agent_key = Path(agent_key)
        self.allowed_signers = Path(allowed_signers)
        self.invoking_principal = invoking_principal

    def invoke(self, assignment: Mapping[str, Any], wop: Mapping[str, Any],
               *, invocation_token: Mapping[str, Any]) -> dict[str, Any]:
        if invocation_token.get("assignment_digest") != digest(assignment):
            raise ProductionExecutionError("agent invocation authentication failed")
        verify_ssh_signature(
            canonical_bytes({
                "assignment_digest": invocation_token["assignment_digest"],
                "invoking_principal": invocation_token.get("invoking_principal"),
            }),
            str(invocation_token.get("signature_path", "")),
            self.allowed_signers, self.invoking_principal, "zeus-agent-invocation",
        )
        if assignment["intended_execution_agent"] != self.registration["agent_id"]:
            raise ProductionExecutionError("assignment agent binding mismatch")
        if assignment["wop_digest"] != digest(wop):
            raise ProductionExecutionError("authoritative WOP transmission mismatch")
        target = self.directory / f"{assignment['assignment_id']}.json"
        if target.exists():
            terminal = load_json(target)
            verify_ssh_signature(
                canonical_bytes(terminal), target.with_suffix(".json.sig"),
                self.allowed_signers, self.registration["service_identity"],
                "zeus-agent-result",
            )
            return terminal
        result = deepcopy(dict(self.handler(deepcopy(wop))))
        terminal = {
            "schema_version": 1, "assignment_id": assignment["assignment_id"],
            "agent_id": self.registration["agent_id"],
            "execution_identity": identifier("EXECUTION", assignment),
            "status": result.get("status"), "evidence_locators": result.get(
                "evidence_locators", []),
            "resume_token": result.get("resume_token"),
        }
        if terminal["status"] not in {"ACCEPTED", "COMPLETED", "INTERRUPTED", "FAILED"}:
            raise ProductionExecutionError("agent returned invalid terminal status")
        terminal["result_digest"] = digest(terminal)
        atomic_write(target, terminal)
        sign_ssh(
            canonical_bytes(terminal), self.agent_key, "zeus-agent-result",
            target.with_suffix(".json.sig"),
        )
        return terminal


def create_evidence_attestation(
    *, evidence: Mapping[str, Any], key: Path | str, signature_path: Path | str,
) -> dict[str, Any]:
    """Seal execution evidence; the signer may not act as its qualifier."""
    required = {
        "wop_id", "mission_id", "assignment_id", "agent_id",
        "repository_identity", "repository_baseline", "executed_gate",
        "action_record", "started_at", "completed_at", "output_locator",
        "validation_result",
    }
    if not required.issubset(evidence):
        raise ProductionExecutionError("execution evidence is incomplete")
    record = deepcopy(dict(evidence))
    record["evidence_digest"] = digest(record)
    sign_ssh(
        canonical_bytes(record), key, "zeus-execution-evidence", Path(signature_path)
    )
    return record


def independently_qualify_evidence(
    record: Mapping[str, Any], *, signature_path: Path | str,
    allowed_signers: Path | str, agent_principal: str,
    qualifier_principal: str, expected: Mapping[str, Any],
) -> dict[str, Any]:
    if qualifier_principal == agent_principal:
        raise ProductionExecutionError("execution evidence cannot be self-qualified")
    value = deepcopy(dict(record))
    supplied = value.pop("evidence_digest", None)
    if supplied != digest(value):
        raise ProductionExecutionError("execution evidence digest mismatch")
    value["evidence_digest"] = supplied
    verify_ssh_signature(
        canonical_bytes(value), signature_path, allowed_signers,
        agent_principal, "zeus-execution-evidence",
    )
    checks = {
        key: value.get(key) == expected.get(key)
        for key in (
            "wop_id", "mission_id", "assignment_id", "agent_id",
            "repository_identity", "repository_baseline", "executed_gate",
        )
    }
    checks["validation_result"] = value.get("validation_result") == "PASS"
    checks["output_digest"] = bool(
        SHA256.fullmatch(str(value.get("output_digest", "")))
    )
    decision = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "schema_version": 1, "evidence_digest": supplied,
        "agent_principal": agent_principal,
        "qualifier_principal": qualifier_principal,
        "checks": checks, "decision": decision,
    }
    report["qualification_digest"] = digest(report)
    return report


class LiveReconciliationAdapters:
    """Scoped, restartable adapters for live authoritative JSON records."""

    KINDS = {
        "mission_state", "work_item_state", "wop_state", "assignment_state",
        "execution_state", "evidence_state", "approval_state", "project_state",
        "work_registry", "completion_registry", "operational_resume",
        "controlled_documentation", "eens_checkpoint",
    }

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def reconcile(
        self, kind: str, relative_path: str, value: Mapping[str, Any],
        *, expected_digest: str | None,
    ) -> dict[str, Any]:
        if kind not in self.KINDS:
            raise ProductionExecutionError("unknown reconciliation adapter")
        target = (self.root / relative_path).resolve()
        if self.root not in target.parents:
            raise ProductionExecutionError("reconciliation target exceeds configured scope")
        observed = digest(load_json(target)) if target.exists() else None
        if observed != expected_digest:
            raise ProductionExecutionError("reconciliation optimistic-lock mismatch")
        proposed = deepcopy(dict(value))
        if target.exists() and load_json(target) == proposed:
            return {"status": "UNCHANGED", "digest": digest(proposed), "path": relative_path}
        atomic_write(target, proposed)
        return {"status": "UPDATED", "digest": digest(proposed), "path": relative_path}


def dispatch_readiness(
    *, repository: str, baseline: str, activation_path: Path | str,
    registry_path: Path | str, mission_class: str,
    required_paths: Iterable[Path | str],
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    activation = None
    agents: list[dict[str, Any]] = []
    try:
        activation = validate_activation(
            load_json(activation_path), repository=repository, baseline=baseline
        )
    except (ProductionExecutionError, OSError) as error:
        blockers.append({"code": "DISPATCHER_ACTIVATION_INVALID", "detail": str(error)})
    try:
        for candidate in load_registry(registry_path):
            try:
                agents.append(validate_agent(
                    candidate, mission_class=mission_class, repository=repository
                ))
            except ProductionExecutionError:
                continue
        if not agents:
            raise ProductionExecutionError("no matching active qualified agent")
    except (ProductionExecutionError, OSError) as error:
        blockers.append({"code": "EXECUTION_AGENT_UNAVAILABLE", "detail": str(error)})
    for path in required_paths:
        if not Path(path).exists():
            blockers.append({
                "code": "PRODUCTION_DEPENDENCY_UNAVAILABLE", "detail": str(path)
            })
    return {
        "dispatch_permitted": not blockers,
        "dispatcher_status": activation["status"] if activation else "UNAVAILABLE",
        "eligible_agents": [item["agent_id"] for item in agents],
        "blocking_reasons": blockers,
    }
