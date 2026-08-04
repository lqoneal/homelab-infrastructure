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
from scripts.lib.emp.gate_handlers import (
    GateHandlerError,
    GateHandlerFramework,
    HandlerRegistry,
    LegacyHandlerAdapter,
    qualification_framework,
)
from scripts.lib.emp.mission_admission_runtime import (
    AdmissionStateStore,
    MissionAdmissionError,
)
from scripts.lib.emp.wop_admission import AdmissionController, submission_digest
from scripts.lib.emp.runtime_paths import runtime_path
from scripts.lib.emp.native_session import NativeSessionStore, NativeSessionError
from scripts.lib.emp.execution_termination import ExecutionTerminator, TerminationError, process_diagnostics, termination_receipt


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
    "Interrupted",
    "TerminationFailed",
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


def operational_workspace_path(repository_root: Path | str, execution_id: str) -> Path:
    """Return a stable derived workspace outside the controlled repository."""
    repository = Path(repository_root).resolve()
    workspace = (Path(tempfile.gettempdir()) / "zeus-operational-workspaces" / execution_id).resolve()
    if workspace == repository or repository in workspace.parents:
        raise MissionExecutionError("operational handler workspace must be isolated from repository")
    return workspace


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


class MissionExecutionRuntime:
    VERSION = "zeus-mission-execution/1"

    def __init__(
        self,
        repository_root: Path | str,
        store: ExecutionStateStore,
        admission_store: AdmissionStateStore,
        *,
        gate_handler=None,
        handler_framework: GateHandlerFramework | None = None,
        evidence_publisher=None,
        event_sink=None,
        operational_dispatch_enabled: bool = False,
        operational_context_provider=None,
        session_store: NativeSessionStore | None = None,
    ):
        self.root = Path(repository_root).resolve()
        self.store = store
        self.admission_store = admission_store
        if gate_handler is not None and handler_framework is not None:
            raise MissionExecutionError(
                "gate_handler and handler_framework are mutually exclusive"
            )
        if gate_handler is not None:
            registry = HandlerRegistry()
            adapter = LegacyHandlerAdapter(
                gate_handler, ("EXECUTE_WORK", "VERIFY_COMPLETION")
            )
            registry.register(adapter)
            registry.activate_registered(adapter.manifest.handler_id)
            handler_framework = GateHandlerFramework(registry, isolated=False)
        self.handler_framework = handler_framework
        self.evidence_publisher = evidence_publisher or FileEvidencePublisher(
            store.directory / "published-evidence"
        )
        self.event_sink = event_sink
        self.operational_dispatch_enabled = operational_dispatch_enabled
        self.operational_context_provider = operational_context_provider
        self.session_store = session_store or NativeSessionStore(store.directory.parent / "native-sessions")

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
        self._append_evidence(
            state,
            "EXECUTION_CREATED",
            {
                "state": "Pending",
                "execution_id": execution_id,
                "mission_id": wop["mission_id"],
                "wop_id": wop["wop_id"],
                "repository": str(self.root),
                "operator": admission["request"].get(
                    "operator_id", admission["request"].get("principal_id", "UNKNOWN")
                ),
            },
            at,
        )
        self.store.save(state)
        if state["mode"] == "operational" and state["mission_id"] == "ZDCL-01":
            request = admission["request"]
            binding = admission["artifacts"]["authority_context"]["admission"]
            session = self.session_store.create({
                "operation": "BETA", "mission_id": state["mission_id"], "wop_id": state["wop_id"],
                "wop_revision": binding["wop_revision"], "submission_id": request["submission_id"],
                "admission_id": admission_id, "execution_id": execution_id,
                "repository_identity": str(self.root), "admitted_baseline": state["repository_baseline"],
                "principal": request["principal_id"], "submitter": request["submitter_identity"],
                "execution_agent": "Codex", "session_classification": "DEVELOPMENT_IMPLEMENTATION",
                "authorized_effect_profile": "ZDCL-01-NATIVE-SESSION-FOUNDATION",
                "authority_references": {"mission_contract": binding["authority"]["source"], "wop": state["wop_id"], "admission": admission_id, "execution": execution_id},
            }, at=at)
            state["session_id"] = session["session_id"]
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
        if state["state"] == "Interrupted":
            return state
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
            self._session_gate_start(state, gate["gate_id"], at)
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
            if state.get("session_id"):
                self.session_store.checkpoint(state["session_id"], checkpoint, at=at)
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
        if state.get("session_id"):
            session = self.session_store.load(state["session_id"])
            if session["lifecycle_state"] in {"ACTIVE", "RESUMED"}:
                self.session_store.transition(state["session_id"], "VERIFYING", at=at, event="SESSION_VERIFICATION_STARTED", current_gate="VERIFY_COMPLETION", next_action="Verify operational execution and evidence chain.")
            self.session_store.transition(state["session_id"], "COMPLETED", at=at, event="SESSION_COMPLETED", current_gate=None, next_action="Proceed through qualification, acceptance, synchronization, and lifecycle closeout.")
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
        if state["state"] not in {"Suspended", "Waiting", "Interrupted"}:
            raise MissionExecutionError("only suspended or waiting execution may resume")
        state["state"] = "Resuming"
        if state.get("session_id"):
            self.session_store.transition(state["session_id"], "RESUMED", at=at, event="SESSION_RESUMED", current_gate=state["current_gate"], next_action=f"Resume execution at {state['current_gate']}.")
        state["wait_reason"] = None
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.run(execution_id, at=at, max_gates=max_gates)

    def suspend(self, execution_id: str, *, at: datetime, reason: str):
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            raise MissionExecutionError("terminal execution cannot be suspended")
        state["state"] = "Suspended"
        if state.get("session_id"):
            self.session_store.transition(state["session_id"], "SUSPENDED", at=at, event="SESSION_SUSPENDED", payload={"reason": reason or "OPERATOR"}, current_gate=state["current_gate"], next_action=f"Resume session {state['session_id']}.")
        self._append_evidence(
            state, "EXECUTION_SUSPENDED", {"reason": reason or "OPERATOR"}, at
        )
        state["updated_at"] = self._time(at)
        self.store.save(state)
        return self.store.load(execution_id)

    def execution_for_mission(self, mission_id: str) -> str:
        matches = []
        for path in sorted(self.store.directory.glob("MISSION-EXECUTION-*.json")):
            try:
                state = self.store.load(path.stem)
            except MissionExecutionError:
                continue
            if state.get("mission_id") == mission_id:
                matches.append(state["execution_id"])
        if not matches:
            raise MissionExecutionError("no execution belongs to mission " + mission_id)
        if len(matches) != 1:
            raise MissionExecutionError("mission identity is ambiguous: " + mission_id)
        return matches[0]

    def execution_diagnostics(self, execution_id: str) -> dict[str, Any]:
        state = self.store.load(execution_id)
        if not state.get("session_id"):
            raise MissionExecutionError("execution has no active native session")
        session = self.session_store.load(state["session_id"])
        return {
            "execution_id": execution_id, "mission_id": state["mission_id"],
            "execution_state": state["state"], "session_id": session["session_id"],
            "session_state": session["lifecycle_state"], **process_diagnostics(session),
        }

    def stop(self, execution_id: str, *, at: datetime, graceful_timeout: float = 2.0) -> dict[str, Any]:
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            raise MissionExecutionError("terminal execution cannot be stopped")
        if not state.get("session_id"):
            raise MissionExecutionError("execution has no active native session")
        session = self.session_store.load(state["session_id"])
        if session.get("execution_id") != execution_id or session.get("mission_id") != state.get("mission_id"):
            raise MissionExecutionError("execution session identity mismatch")
        if session["lifecycle_state"] == "INTERRUPTED" or state["state"] == "Interrupted":
            return {**state, "stop_result": "ALREADY_STOPPED", "termination_diagnostic": process_diagnostics(session)}
        if session["lifecycle_state"] not in {"ACTIVE", "RESUMED", "STOP_REQUESTED", "TERMINATING"}:
            raise MissionExecutionError("no active execution session exists")
        if session["lifecycle_state"] in {"ACTIVE", "RESUMED"}:
            self.session_store.transition(state["session_id"], "STOP_REQUESTED", at=at, event="SESSION_STOP_REQUESTED", current_gate=state.get("current_gate"), next_action="Terminate the exact recorded execution process.")
        self.session_store.transition(state["session_id"], "TERMINATING", at=at, event="SESSION_TERMINATING", current_gate=state.get("current_gate"), next_action="Complete bounded process termination.")
        session = self.session_store.load(state["session_id"])
        try:
            result = ExecutionTerminator().stop(session, graceful_timeout=graceful_timeout)
        except TerminationError as error:
            state["state"] = "TerminationFailed"
            state["termination_failure"] = {"category": error.category, "message": str(error), "diagnostics": error.diagnostics}
            self._append_evidence(state, "EXECUTION_TERMINATION_FAILED", state["termination_failure"], at)
            state["updated_at"] = self._time(at)
            self.store.save(state)
            self.session_store.transition(state["session_id"], "FAILED", at=at, event="SESSION_TERMINATION_FAILED", payload={"category": error.category, "message": str(error), "diagnostics": error.diagnostics}, next_action="Preserve termination diagnostics and investigate the exact execution identity.")
            raise MissionExecutionError(f"{error.category}: {error}") from error
        receipt = termination_receipt(session, result=result, at=at)
        state["state"] = "Interrupted"
        state["termination_receipt"] = receipt
        self._append_evidence(state, "EXECUTION_TERMINATED", {"termination_receipt": receipt, "diagnostics": result["diagnostics"]}, at)
        state["updated_at"] = self._time(at)
        self.store.save(state)
        self.session_store.transition(state["session_id"], "INTERRUPTED", at=at, event="SESSION_INTERRUPTED", payload={"termination_receipt_id": receipt["receipt_id"], "forced": result.get("forced", False)}, current_gate=state.get("current_gate"), next_action=f"scripts/zeus resume {state['mission_id']}")
        return {**self.store.load(execution_id), "stop_result": result["result"], "termination_receipt": receipt, "termination_diagnostic": result["diagnostics"]}

    def cancel(self, execution_id: str, *, at: datetime, reason: str):
        state = self.store.load(execution_id)
        if state["state"] in TERMINAL_STATES:
            return state
        state["state"] = "Cancelled"
        state["current_gate"] = None
        self._append_evidence(
            state, "EXECUTION_CANCELLED", {"reason": reason or "OPERATOR"}, at
        )
        if state.get("session_id"):
            self.session_store.transition(state["session_id"], "CANCELLED", at=at, event="SESSION_CANCELLED", payload={"reason": reason or "OPERATOR"}, current_gate=None, next_action="Create a fresh admission before any further work.")
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
        framework = self.handler_framework
        if framework is None and state["mode"] == "qualification":
            framework = qualification_framework(self.root)
        if framework is None:
            raise ExecutionBlocked(
                "EXECUTION_HANDLER_UNAVAILABLE",
                "no controlled execution handler is configured",
            )
        operational_context = None
        if state["mode"] == "operational":
            if self.operational_context_provider is None:
                if state["mission_id"] != "ZDCL-01":
                    raise ExecutionBlocked("OPERATIONAL_CONTEXT_UNAVAILABLE", "no operational execution context provider is configured")
                operational_context = {"profile": "ZDCL-01", "session_id": state.get("session_id"), "effect_profile": "ZDCL-01-NATIVE-SESSION-FOUNDATION", "dry_run": False}
            else:
                operational_context = self.operational_context_provider(deepcopy(state), deepcopy(wop))
        try:
            return framework.execute(
                mode=state["mode"],
                gate_id=gate_id,
                context={
                "execution_id": state["execution_id"],
                "gate_idempotency_key": (
                    f"{state['execution_id']}:{gate_id}"
                ),
                "mission_id": state["mission_id"],
                "repository": str(self.root),
                "wop": deepcopy(wop),
                "completed_gates": list(state["completed_gates"]),
                "checkpoints": deepcopy(state["checkpoints"]),
                "cancellation_requested": False,
                "retry_count": sum(
                    1
                    for item in state["evidence"]
                    if item["event"] == "GATE_STARTED"
                    and item["payload"].get("gate_id") == gate_id
                )
                - 1,
                "operational_context": operational_context,
                "at": self._time(at),
                },
            )
        except GateHandlerError as error:
            raise ExecutionBlocked(
                "GATE_HANDLER_FAILURE",
                str(error),
                {"gate_id": gate_id, "retryable": True},
            ) from error

    def _load_admission(self, admission_id):
        try:
            admission = self.admission_store.load(admission_id)
        except MissionAdmissionError as error:
            raise MissionExecutionError(str(error)) from error
        if admission.get("status") != "DECIDED":
            raise MissionExecutionError("mission admission is not decided")
        if admission.get("admission_state") in {"STALE", "SUPERSEDED", "CANCELLED", "REJECTED", "CONSUMED", "COMPLETED"}:
            raise MissionExecutionError(
                f"mission admission {admission_id} is not executable: "
                f"state={admission.get('admission_state')}"
            )
        admitted_baseline = admission.get("artifacts", {}).get("repository_baseline")
        current_baseline = self._git("rev-parse", "HEAD")
        if admitted_baseline != current_baseline:
            raise MissionExecutionError(
                "stale admission cannot authorize execution: "
                f"admission={admission_id} admitted_baseline={admitted_baseline} "
                f"current_baseline={current_baseline}; create a replacement admission"
            )
        request = admission.get("request", {})
        if request.get("repository_baseline") not in (None, current_baseline):
            raise MissionExecutionError("admission request baseline binding is stale")
        if admission.get("request", {}).get("mission_id") == "ZDCL-01" and not request.get("submission_id"):
            raise MissionExecutionError("admission submission binding is unresolved")
        if self._cancelled_execution_for_admission(admission_id):
            raise MissionExecutionError(
                f"admission {admission_id} is non-executable after incompatible cancellation; "
                "create a superseding admission"
            )
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

    def _cancelled_execution_for_admission(self, admission_id: str) -> bool:
        for path in sorted(runtime_path(self.root, "mission-executions").glob("MISSION-EXECUTION-*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if value.get("admission_id") != admission_id or value.get("state") != "Cancelled":
                continue
            reason = " ".join(
                str(item.get("payload", {}).get("reason", ""))
                for item in value.get("evidence", [])
                if item.get("event") == "EXECUTION_CANCELLED"
            )
            return "baseline" in reason.lower() or "supersed" in reason.lower()
        return False

    def _validate_binding(self, state, admission):
        wop = admission["artifacts"]["wop_result"]["wop"]
        if (
            wop["wop_id"] != state["wop_id"]
            or wop["submission_digest"] != state["wop_submission_digest"]
        ):
            raise MissionExecutionError("execution and admission WOP binding mismatch")
        if Path(state["repository"]).resolve() != self.root:
            raise MissionExecutionError("execution repository identity mismatch")

    def _session_gate_start(self, state, gate_id, at):
        if not state.get("session_id"):
            return
        session = self.session_store.load(state["session_id"])
        target = None
        if gate_id == "VALIDATE_WOP" and session["lifecycle_state"] == "CREATED": target = "VERIFIED"
        elif gate_id == "PREPARE_EXECUTION" and session["lifecycle_state"] == "VERIFIED": target = "ACTIVE"
        elif session["lifecycle_state"] == "RESUMED": target = "ACTIVE"
        if target:
            self.session_store.transition(state["session_id"], target, at=at, event=f"SESSION_{target}", current_gate=gate_id, next_action=f"Execute gate {gate_id}.")

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
