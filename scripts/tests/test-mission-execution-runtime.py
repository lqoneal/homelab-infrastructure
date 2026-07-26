#!/usr/bin/env python3
"""ZEUS-P2-008 Mission Execution Runtime tests."""

from __future__ import annotations

import json
import runpy
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.mission_admission_runtime import (  # noqa: E402
    AdmissionStateStore,
    MissionAdmissionRuntime,
)
from scripts.lib.emp.mission_execution_runtime import (  # noqa: E402
    EensExecutionSink,
    ExecutionStateStore,
    FileEvidencePublisher,
    GATES,
    MissionExecutionError,
    MissionExecutionRuntime,
)

AT = datetime(2026, 7, 27, 7, 0, tzinfo=timezone.utc)


class RecordingHandler:
    def __init__(self):
        self.calls = []
        self.wait_once = False

    def execute(self, gate_id, context):
        self.calls.append(gate_id)
        if gate_id == "EXECUTE_WORK" and self.wait_once:
            self.wait_once = False
            return {"status": "WAITING", "reason": "DEPENDENCY"}
        return {
            "status": "COMPLETED",
            "artifacts": [f"{gate_id}.evidence"],
            "side_effects_performed": False,
        }


class MissionExecutionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.admissions = AdmissionStateStore(self.directory / "admissions")
        self.executions = ExecutionStateStore(self.directory / "executions")
        self.admission_runtime = MissionAdmissionRuntime(ROOT, self.admissions)
        self.admission = self.admission_runtime.start(
            {
                "mode": "qualification",
                "intent": "Qualify restartable mission execution",
                "mission_id": "ZEUS-P2-008-QUALIFICATION",
                "phase_id": "MISSION-EXECUTION",
                "repository": str(ROOT),
            },
            at=AT,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def runtime(self, **options):
        return MissionExecutionRuntime(
            ROOT, self.executions, self.admissions, **options
        )

    def test_qualification_completes_all_gates_with_immutable_evidence(self):
        state = self.runtime().start(self.admission["admission_id"], at=AT)
        self.assertEqual(state["state"], "Completed")
        self.assertEqual(state["completed_gates"], [gate["gate_id"] for gate in GATES])
        self.assertEqual(len(state["checkpoints"]), len(GATES))
        self.assertEqual(state["evidence"][-1]["event"], "EXECUTION_COMPLETED")
        self.assertFalse(
            state["evidence"][-1]["payload"]["operational_dispatch"]
        )
        published = list(
            (self.executions.directory / "published-evidence" / state["execution_id"]).glob(
                "*.json"
            )
        )
        self.assertEqual(len(published), len(state["evidence"]))
        self.assertTrue(all(path.stat().st_mode & 0o222 == 0 for path in published))

    def test_interruption_resume_skips_completed_gates_and_replay_is_idempotent(self):
        handler = RecordingHandler()
        runtime = self.runtime(gate_handler=handler)
        suspended = runtime.start(
            self.admission["admission_id"], at=AT, max_gates=2
        )
        self.assertEqual(suspended["state"], "Suspended")
        self.assertEqual(
            suspended["completed_gates"], ["VALIDATE_WOP", "PREPARE_EXECUTION"]
        )
        resumed = runtime.resume(suspended["execution_id"], at=AT)
        self.assertEqual(resumed["state"], "Completed")
        self.assertEqual(handler.calls, ["EXECUTE_WORK", "VERIFY_COMPLETION"])
        replay = runtime.run(resumed["execution_id"], at=AT)
        self.assertEqual(replay, resumed)

    def test_waiting_dependency_resumes_current_gate_without_duplicate_completion(self):
        handler = RecordingHandler()
        handler.wait_once = True
        runtime = self.runtime(gate_handler=handler)
        waiting = runtime.start(self.admission["admission_id"], at=AT)
        self.assertEqual(waiting["state"], "Waiting")
        self.assertEqual(waiting["current_gate"], "EXECUTE_WORK")
        resumed = runtime.resume(waiting["execution_id"], at=AT)
        self.assertEqual(resumed["state"], "Completed")
        self.assertEqual(
            resumed["completed_gates"].count("EXECUTE_WORK"), 1
        )
        self.assertEqual(handler.calls.count("EXECUTE_WORK"), 2)

    def test_operational_execution_remains_blocked_before_dispatch(self):
        fixture = runpy.run_path(
            str(ROOT / "scripts/tests/test-authority-resolution-runtime.py")
        )
        source = fixture["authoritative_state"]()
        source_path = self.directory / "authority.yaml"
        source_path.write_text(yaml.safe_dump(source, sort_keys=True))
        admission = MissionAdmissionRuntime(
            ROOT,
            self.admissions,
            authority_state_path=source_path,
            commissioning_probe=lambda root: {"commissioning_state": "READY"},
            enrollment_probe=lambda root: {
                "trust_compilation_ready": True,
                "missing_owners": [],
            },
        ).start(
            {
                "mode": "operational",
                "intent": "Exercise operational execution boundary",
                "mission_id": fixture["MISSION"],
                "work_item_id": fixture["WORK"],
                "principal_id": fixture["PRINCIPAL"],
                "repository": str(ROOT),
            },
            at=fixture["AT"],
        )
        state = self.runtime(gate_handler=RecordingHandler()).start(
            admission["admission_id"], at=fixture["AT"]
        )
        self.assertEqual(state["state"], "Waiting")
        self.assertEqual(state["current_gate"], "EXECUTE_WORK")
        self.assertEqual(
            state["wait_reason"]["category"], "OPERATIONAL_DISPATCH_DISABLED"
        )
        self.assertNotIn("EXECUTE_WORK", state["completed_gates"])

    def test_eens_adapter_receives_idempotent_execution_events(self):
        sink = EensExecutionSink(ROOT, self.directory / "eens.sqlite3")
        state = self.runtime(event_sink=sink).start(
            self.admission["admission_id"], at=AT
        )
        self.assertEqual(sink.store.count(), len(state["evidence"]))
        replay = self.runtime(event_sink=sink).run(state["execution_id"], at=AT)
        self.assertEqual(replay, state)
        self.assertEqual(sink.store.count(), len(state["evidence"]))

    def test_state_and_published_evidence_tampering_fail_closed(self):
        state = self.runtime().start(
            self.admission["admission_id"], at=AT, max_gates=1
        )
        evidence = state["evidence"][0]
        publisher = FileEvidencePublisher(
            self.executions.directory / "published-evidence"
        )
        changed = dict(evidence)
        changed["payload"] = {"tampered": True}
        with self.assertRaisesRegex(MissionExecutionError, "immutable"):
            publisher.publish(state["execution_id"], changed)

        path = self.executions.path(state["execution_id"])
        value = json.loads(path.read_text())
        value["completed_gates"] = []
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(MissionExecutionError, "digest"):
            self.executions.load(state["execution_id"])

    def test_cancel_is_terminal_and_preserves_history(self):
        runtime = self.runtime()
        state = runtime.start(self.admission["admission_id"], at=AT, max_gates=1)
        cancelled = runtime.cancel(state["execution_id"], at=AT, reason="operator")
        self.assertEqual(cancelled["state"], "Cancelled")
        self.assertEqual(cancelled["evidence"][-1]["event"], "EXECUTION_CANCELLED")
        self.assertEqual(runtime.run(cancelled["execution_id"], at=AT), cancelled)


if __name__ == "__main__":
    unittest.main()
