#!/usr/bin/env python3
"""Persistent, restartable, evidence-driven Zeus Mission Execution Runtime."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.authority_resolution import canonical_json, digest
from scripts.lib.emp.mission_admission_runtime import (
    AdmissionStateStore,
    MissionAdmissionError,
)
from scripts.lib.emp.wop_admission import AdmissionController, submission_digest


class MissionExecutionError(ValueError):
    """Execution request, state, evidence, or transition is invalid."""


class ExecutionBlocked(MissionExecutionError):
    def __init__(self, category: str, message: str, diagnostics: Any = None):
        self.category = category
        self.diagnostics = diagnostics
        super().__init__(message)


EXECUTION_STATES = (
    "Pending",
    "Authorized",
    "Preparing",
    "Executing",
    "Waiting",
    "Suspended",
    "Resuming",
    "Verifying",
    "Completed",
    "Failed",
    "Cancelled",
)

GATES = (
    {"gate_id": "VALIDATE_WOP", "state": "Authorized"},
    {"gate_id": "PREPARE_EXECUTION", "state": "Preparing"},
    {"gate_id": "EXECUTE_WORK", "state": "Executing"},
    {"gate_id": "VERIFY_COMPLETION", "state": "Verifying"},
)

TERMINAL_STATES = {"Completed", "Failed", "Cancelled"}


def execution_identifier(admission_id: str, wop_digest: str) -> str:
    return "MISSION-EXECUTION-" + str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            canonical_json(
                {"admission_id": admission_id, "wop_digest": wop_digest}
            ),
        )
    )


class ExecutionStateStore:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def path(self, execution_id: str) -> Path:
        return self.directory / f"{execution_id}.json"

    def load(self, execution_id: str) -> dict[str, Any]:
        try:
            value = json.loads(self.path(execution_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MissionExecutionError(f"invalid execution state: {error}") from error
        if not isinstance(value, dict):
            raise MissionExecutionError("execution state must be an object")
        supplied = value.pop("state_digest", None)
        if supplied != digest(value):
            raise MissionExecutionError("execution state digest mismatch")
        self._validate_evidence(value.get("evidence", []))
        value["state_digest"] = supplied
        return value

    def save(self, value: Mapping[str, Any]) -> Path:
        data = deepcopy(dict(value))
        data.pop("state_digest", None)
        self._validate_evidence(data.get("evidence", []))
        data["state_digest"] = digest(data)
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=self.directory, prefix=".execution."
        )
        path = self.path(str(data["execution_id"]))
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(data, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return path

    @staticmethod
    def _validate_evidence(entries):
        previous = None
        for sequence, entry in enumerate(entries, 1):
            material = deepcopy(entry)
            supplied = material.pop("evidence_digest", None)
            material.pop("publication", None)
            if material.get("sequence") != sequence:
                raise MissionExecutionError("execution evidence sequence mismatch")
            if material.get("previous_evidence_digest") != previous:
                raise MissionExecutionError("execution evidence chain mismatch")
            if supplied != digest(material):
                raise MissionExecutionError("execution evidence digest mismatch")
            previous = supplied


class FileEvidencePublisher:
    """Create-only immutable execution evidence publication."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def publish(self, execution_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
        directory = self.directory / execution_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{int(evidence['sequence']):04d}.json"
        payload = json.dumps(dict(evidence), indent=2, sort_keys=True) + "\n"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        except FileExistsError:
            existing = path.read_text(encoding="utf-8")
            if existing != payload:
                raise MissionExecutionError(
                    "published execution evidence is immutable"
                )
            return {"path": str(path), "inserted": False}
        with os.fdopen(descriptor, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return {"path": str(path), "inserted": True}


class EensExecutionSink:
    """Optional adapter to the existing append-only EENS EventStore."""

    def __init__(self, repository_root: Path | str, database_path: Path | str):
        import sys

        source = Path(repository_root) / "services/eens/src"
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))
        from eens.events import EngineeringEvent
        from eens.store import EventStore

        self.event_type = EngineeringEvent
        self.store = EventStore(database_path)

    def emit(self, execution_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
        event = self.event_type(
            event_type=f"zeus.execution.{str(evidence['event']).lower()}",
            source="zeus-mission-execution-runtime",
            subject=execution_id,
            idempotency_key=f"{execution_id}:{evidence['evidence_digest']}",
            occurred_at=str(evidence["observed_at"]),
            payload=dict(evidence),
        )
        result = self.store.append(event)
        return {
            "sequence": result.sequence,
            "event_id": result.event_id,
            "inserted": result.inserted,
        }


class QualificationGateHandler:
    """Non-mutating gate handler used only for qualification execution."""

    def execute(self, gate_id, context):
        if gate_id == "EXECUTE_WORK":
            return {
                "result": "QUALIFIED_SIMULATION",
                "side_effects_performed": False,
                "artifacts": [],
            }
        return {"result": "PASS", "side_effects_performed": False, "artifacts": []}


class MissionExecutionRuntime:
    VERSION = "zeus-mission-execution/1"

    def __init__(
        self,
        repository_root: Path | str,
        store: ExecutionStateStore,
        admission_store: AdmissionStateStore,
        *,
        gate_handler=None,
        evidence_publisher=None,
        event_sink=None,
        operational_dispatch_enabled: bool = False,
    ):
        self.root = Path(repository_root).resolve()
        self.store = store
        self.admission_store = admission_store
        self.gate_handler = gate_handler
        self.evidence_publisher = evidence_publisher or FileEvidencePublisher(
            store.directory / "published-evidence"
        )
        self.event_sink = event_sink
        self.operational_dispatch_enabled = operational_dispatch_enabled

    def start(
        self,
        admission_id: str,
        *,
        at: datetime,
        max_gates: int | None = None,
    ) -> dict[str, Any]:
        admission = self._load_admission(admission_id)
        wop_result = admission.get("artifacts", {}).get("wop_result")
        if not isinstance(wop_result, dict) or not isinstance(wop_result.get("wop"), dict):
            raise MissionExecutionError("admission has no qualified WOP")
        wop = wop_result["wop"]
        execution_id = execution_identifier(admission_id, wop["submission_digest"])
        if self.store.path(execution_id).exists():
            return self.run(execution_id, at=at, max_gates=max_gates)
        state = {
            "schema_version": 1,
            "runtime_version": self.VERSION,
            "execution_id": execution_id,
            "admission_id": admission_id,
            "mode": admission["request"]["mode"],
            "mission_id": wop["mission_id"],
            "wop_id": wop["wop_id"],
            "wop_submission_digest": wop["submission_digest"],
            "repository": str(self.root),
            "repository_baseline": admission["artifacts"]["repository_baseline"],
            "state": "Pending",
            "current_gate": GATES[0]["gate_id"],
            "completed_gates": [],
            "checkpoints": [],
            "evidence": [],
            "failure": None,
            "wait_reason": None,
            "created_at": self._time(at),
            "updated_at": self._time(at),
        }
        self.store.save(state)
        self._append_evidence(state, "EXECUTION_CREATED", {"state": "Pending"}, at)
        self.store.save(state)
        return self.run(execution_id, at=at, max_gates=max_gates)

    def run(
        self,
        execution_id: str,
        *,
        at: datetime,
        max_gates: int | None = None,
    ) -> dict[str, Any]:
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            return state
        if state["state"] in {"Suspended", "Waiting"}:
            return state
        admission = self._load_admission(state["admission_id"])
        self._validate_binding(state, admission)
        if state["state"] == "Resuming":
            self._append_evidence(
                state,
                "RECOVERY_ACTION",
                {"action": "RESUME", "next_gate": state["current_gate"]},
                at,
            )
        executed = 0
        while state["current_gate"]:
            if max_gates is not None and executed >= max_gates:
                state["state"] = "Suspended"
                self._append_evidence(
                    state,
                    "EXECUTION_INTERRUPTED",
                    {"next_gate": state["current_gate"], "reason": "BOUNDED_RUN"},
                    at,
                )
                state["updated_at"] = self._time(at)
                self.store.save(state)
                return self.store.load(execution_id)
            gate = next(item for item in GATES if item["gate_id"] == state["current_gate"])
            state["state"] = gate["state"]
            self._append_evidence(
                state, "GATE_STARTED", {"gate_id": gate["gate_id"]}, at
            )
            state["updated_at"] = self._time(at)
            self.store.save(state)
            try:
                result = self._execute_gate(gate["gate_id"], state, admission, at)
            except ExecutionBlocked as error:
                state["state"] = "Waiting"
                state["wait_reason"] = {
                    "category": error.category,
                    "message": str(error),
                    "diagnostics": error.diagnostics,
                }
                self._append_evidence(state, "GATE_WAITING", state["wait_reason"], at)
                self.store.save(state)
                return self.store.load(execution_id)
            except Exception as error:
                state["state"] = "Failed"
                state["failure"] = {
                    "gate_id": gate["gate_id"],
                    "category": "GATE_EXECUTION_FAILURE",
                    "message": str(error),
                }
                self._append_evidence(state, "EXECUTION_FAILED", state["failure"], at)
                self.store.save(state)
                return self.store.load(execution_id)
            if result.get("status") == "WAITING":
                state["state"] = "Waiting"
                state["wait_reason"] = deepcopy(result)
                self._append_evidence(state, "GATE_WAITING", result, at)
                self.store.save(state)
                return self.store.load(execution_id)
            checkpoint = {
                "gate_id": gate["gate_id"],
                "gate_index": GATES.index(gate),
                "result_digest": digest(result),
                "completed_at": self._time(at),
            }
            checkpoint["checkpoint_digest"] = digest(checkpoint)
            state["completed_gates"].append(gate["gate_id"])
            state["checkpoints"].append(checkpoint)
            self._append_evidence(
                state,
                "GATE_COMPLETED",
                {"gate_id": gate["gate_id"], "result": result, "checkpoint": checkpoint},
                at,
            )
            index = GATES.index(gate) + 1
            state["current_gate"] = GATES[index]["gate_id"] if index < len(GATES) else None
            state["updated_at"] = self._time(at)
            self.store.save(state)
            executed += 1
        state["state"] = "Completed"
        self._append_evidence(
            state,
            "EXECUTION_COMPLETED",
            {
                "completed_gates": list(state["completed_gates"]),
                "operational_dispatch": False,
            },
            at,
        )
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.store.load(execution_id)

    def resume(self, execution_id: str, *, at: datetime, max_gates=None):
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            return state
        if state["state"] not in {"Suspended", "Waiting"}:
            raise MissionExecutionError("only suspended or waiting execution may resume")
        state["state"] = "Resuming"
        state["wait_reason"] = None
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.run(execution_id, at=at, max_gates=max_gates)

    def suspend(self, execution_id: str, *, at: datetime, reason: str):
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            raise MissionExecutionError("terminal execution cannot be suspended")
        state["state"] = "Suspended"
        self._append_evidence(
            state, "EXECUTION_SUSPENDED", {"reason": reason or "OPERATOR"}, at
        )
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.store.load(execution_id)

    def cancel(self, execution_id: str, *, at: datetime, reason: str):
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            return state
        state["state"] = "Cancelled"
        state["current_gate"] = None
        self._append_evidence(
            state, "EXECUTION_CANCELLED", {"reason": reason or "OPERATOR"}, at
        )
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.store.load(execution_id)

    def _execute_gate(self, gate_id, state, admission, at):
        wop = admission["artifacts"]["wop_result"]["wop"]
        if gate_id == "VALIDATE_WOP":
            if submission_digest(wop) != wop["submission_digest"]:
                raise ExecutionBlocked("WOP_INTEGRITY", "WOP digest mismatch")
            failures = AdmissionController().validate(wop, str(self.root))
            if failures:
                raise ExecutionBlocked(
                    "WOP_VALIDATION",
                    "WOP validation failed",
                    {"failures": [item.to_mapping() for item in failures]},
                )
            return {"validation": "PASS", "submission_digest": wop["submission_digest"]}
        if gate_id == "PREPARE_EXECUTION":
            baseline = self._git("rev-parse", "HEAD")
            if baseline != state["repository_baseline"]:
                raise ExecutionBlocked(
                    "REPOSITORY_DRIFT",
                    "repository baseline changed after admission",
                    {"admitted": state["repository_baseline"], "observed": baseline},
                )
            return {"repository_verification": "PASS", "baseline_commit": baseline}
        if state["mode"] == "operational" and not self.operational_dispatch_enabled:
            raise ExecutionBlocked(
                "OPERATIONAL_DISPATCH_DISABLED",
                "operational mission dispatch is not enabled",
                {"production_activated": False, "dispatch_permitted": False},
            )
        handler = self.gate_handler
        if handler is None and state["mode"] == "qualification":
            handler = QualificationGateHandler()
        if handler is None:
            raise ExecutionBlocked(
                "EXECUTION_HANDLER_UNAVAILABLE",
                "no controlled execution handler is configured",
            )
        return handler.execute(
            gate_id,
            {
                "execution_id": state["execution_id"],
                "gate_idempotency_key": (
                    f"{state['execution_id']}:{gate_id}"
                ),
                "mission_id": state["mission_id"],
                "wop": deepcopy(wop),
                "at": self._time(at),
            },
        )

    def _load_admission(self, admission_id):
        try:
            admission = self.admission_store.load(admission_id)
        except MissionAdmissionError as error:
            raise MissionExecutionError(str(error)) from error
        if admission.get("status") != "DECIDED":
            raise MissionExecutionError("mission admission is not decided")
        decision = admission.get("artifacts", {}).get("admission_decision", {})
        mode = admission.get("request", {}).get("mode")
        permitted = (
            mode == "qualification"
            and decision.get("admission_decision") == "QUALIFICATION_ONLY"
        ) or (
            mode == "operational"
            and decision.get("admission_decision") == "ACCEPTED"
        )
        if not permitted:
            raise MissionExecutionError("mission admission does not qualify for execution")
        return admission

    def _validate_binding(self, state, admission):
        wop = admission["artifacts"]["wop_result"]["wop"]
        if (
            wop["wop_id"] != state["wop_id"]
            or wop["submission_digest"] != state["wop_submission_digest"]
        ):
            raise MissionExecutionError("execution and admission WOP binding mismatch")
        if Path(state["repository"]).resolve() != self.root:
            raise MissionExecutionError("execution repository identity mismatch")

    def _append_evidence(self, state, event, payload, at):
        previous = (
            state["evidence"][-1]["evidence_digest"] if state["evidence"] else None
        )
        material = {
            "sequence": len(state["evidence"]) + 1,
            "event": event,
            "observed_at": self._time(at),
            "previous_evidence_digest": previous,
            "payload": deepcopy(payload),
        }
        material["evidence_digest"] = digest(material)
        publication = self.evidence_publisher.publish(
            state["execution_id"], material
        )
        material["publication"] = publication
        # Publication metadata is outside the sealed evidence material.
        state["evidence"].append(material)
        if self.event_sink is not None:
            self.event_sink.emit(state["execution_id"], material)

    def _git(self, *arguments):
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise ExecutionBlocked(
                "REPOSITORY_FAILURE",
                "repository verification command failed",
                {"stderr": result.stderr.strip()},
            )
        return result.stdout.strip()

    @staticmethod
    def _time(value):
        if value.tzinfo is None:
            raise MissionExecutionError("timestamp must include timezone")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
