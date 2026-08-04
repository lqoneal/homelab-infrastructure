"""Disposable qualification for exact-process Zeus execution termination."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.execution_termination import process_diagnostics
from scripts.lib.emp.mission_execution_runtime import ExecutionStateStore, MissionExecutionError, MissionExecutionRuntime
from scripts.lib.emp.native_session import NativeSessionStore, session_identifier
from scripts.lib.emp.mission_admission_runtime import AdmissionStateStore


AT = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)


def proc_start(pid: int) -> str:
    with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
        return handle.read().split()[21]


class HungTerminationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.executions = ExecutionStateStore(root / "executions")
        self.admissions = AdmissionStateStore(root / "admissions")
        self.sessions = NativeSessionStore(root / "native-sessions")
        self.runtime = MissionExecutionRuntime(ROOT, self.executions, self.admissions, session_store=self.sessions)
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except OSError:
                    pass
            process.wait()
        self.tmp.cleanup()

    def fixture(self, *, ignore_term=False, mission="FIXTURE-HUNG-MISSION", child_file=None):
        if child_file:
            code = "import os,signal,time; child=os.fork(); p=%r; f=open(p,'w') if child else None; f.write(str(child)) if f else None; f.close() if f else None; time.sleep(60) if not child else None; signal.signal(signal.SIGTERM, signal.SIG_IGN) if %r else None; time.sleep(60)" % (str(child_file), ignore_term)
        else:
            code = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN) if %r else None; time.sleep(60)" % ignore_term
        process = subprocess.Popen([sys.executable, "-c", code], start_new_session=True)
        self.processes.append(process)
        time.sleep(0.05)
        execution_id = "MISSION-EXECUTION-FIXTURE-" + str(len(self.processes))
        session_id = session_identifier(execution_id)
        session = self.sessions.create({
            "operation": "BETA", "mission_id": mission, "wop_id": "WOP-FIXTURE-001",
            "wop_revision": "1", "submission_id": "SUB-FIXTURE-001", "admission_id": "ADM-FIXTURE-001",
            "execution_id": execution_id, "repository_identity": str(ROOT), "admitted_baseline": "fixture-baseline",
            "principal": "fixture-principal", "submitter": "fixture-operator", "execution_agent": "fixture-agent",
            "session_classification": "DISPOSABLE_HUNG_EXECUTION", "authorized_effect_profile": "NO_EFFECTS",
            "process_pid": process.pid, "process_group_id": os.getpgid(process.pid),
            "process_session_id": os.getsid(process.pid), "process_start_time": proc_start(process.pid),
            "last_heartbeat": "2026-08-04T11:59:00Z", "last_provider_event": "fixture-start",
            "last_lifecycle_progress": "EXECUTE_WORK", "elapsed_inactivity": 60,
        }, at=AT)
        self.sessions.transition(session_id, "VERIFIED", at=AT, event="SESSION_VERIFIED", current_gate="EXECUTE_WORK", next_action="Execute fixture")
        self.sessions.transition(session_id, "ACTIVE", at=AT, event="SESSION_ACTIVE", current_gate="EXECUTE_WORK", next_action="Execute fixture")
        state = {
            "schema_version": 1, "runtime_version": "fixture", "execution_id": execution_id,
            "admission_id": "ADM-FIXTURE-001", "mode": "qualification", "mission_id": mission,
            "wop_id": "WOP-FIXTURE-001", "wop_submission_digest": "fixture-wop-digest", "repository": str(ROOT),
            "repository_baseline": "fixture-baseline", "state": "Executing", "current_gate": "EXECUTE_WORK",
            "completed_gates": ["VALIDATE_WOP", "PREPARE_EXECUTION"], "checkpoints": [], "evidence": [],
            "failure": None, "wait_reason": None, "created_at": "2026-08-04T11:58:00Z",
            "updated_at": "2026-08-04T11:59:00Z", "session_id": session_id,
        }
        self.executions.save(state)
        return execution_id, process

    def test_graceful_stop_preserves_identity_and_receipts(self):
        execution_id, process = self.fixture()
        stopped = self.runtime.stop(execution_id, at=AT, graceful_timeout=0.5)
        process.wait(timeout=1)
        self.assertEqual(stopped["state"], "Interrupted")
        self.assertEqual(stopped["stop_result"], "STOPPED")
        self.assertEqual(stopped["termination_receipt"]["receipt_type"], "EXECUTION_TERMINATION")
        self.assertEqual(self.sessions.load(stopped["session_id"])["lifecycle_state"], "INTERRUPTED")
        self.assertEqual(stopped["mission_id"], "FIXTURE-HUNG-MISSION")
        replay = self.runtime.stop(execution_id, at=AT, graceful_timeout=0)
        self.assertEqual(replay["stop_result"], "ALREADY_STOPPED")
        self.assertEqual(replay["termination_receipt"]["receipt_id"], stopped["termination_receipt"]["receipt_id"])

    def test_forced_stop_and_unrelated_process_protection(self):
        execution_id, target = self.fixture(ignore_term=True)
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
        self.processes.append(unrelated)
        stopped = self.runtime.stop(execution_id, at=AT, graceful_timeout=0.05)
        target.wait(timeout=1)
        self.assertTrue(stopped["termination_receipt"]["forced"])
        self.assertIsNone(unrelated.poll())

    def test_forced_stop_cleans_children_in_the_recorded_process_group(self):
        child_file = Path(self.tmp.name) / "child.pid"
        execution_id, parent = self.fixture(ignore_term=True, child_file=child_file)
        child_pid = int(child_file.read_text(encoding="utf-8"))
        stopped = self.runtime.stop(execution_id, at=AT, graceful_timeout=0.05)
        parent.wait(timeout=1)
        self.assertTrue(stopped["termination_receipt"]["forced"])
        deadline = time.time() + 1
        while time.time() < deadline and Path(f"/proc/{child_pid}").exists():
            time.sleep(0.02)
        self.assertFalse(Path(f"/proc/{child_pid}").exists())

    def test_missing_session_and_terminal_execution_fail_closed(self):
        execution_id = "MISSION-EXECUTION-NO-SESSION"
        self.executions.save({"execution_id": execution_id, "mission_id": "MISSING", "state": "Executing", "evidence": []})
        with self.assertRaisesRegex(MissionExecutionError, "no active native session"):
            self.runtime.stop(execution_id, at=AT)
        terminal = "MISSION-EXECUTION-TERMINAL"
        self.executions.save({"execution_id": terminal, "mission_id": "TERMINAL", "state": "Completed", "evidence": []})
        with self.assertRaisesRegex(MissionExecutionError, "terminal execution"):
            self.runtime.stop(terminal, at=AT)

    def test_interrupted_execution_cannot_advance_from_provider_output(self):
        execution_id, process = self.fixture()
        self.runtime.stop(execution_id, at=AT, graceful_timeout=0.2)
        result = self.runtime.run(execution_id, at=AT)
        self.assertEqual(result["state"], "Interrupted")
        self.assertEqual(result["execution_id"], execution_id)

    def test_read_only_process_diagnostics_expose_ownership_and_hung_fields(self):
        execution_id, process = self.fixture()
        diagnostics = self.runtime.execution_diagnostics(execution_id)
        self.assertTrue(diagnostics["ownership_proven"])
        self.assertTrue(diagnostics["termination_eligible"])
        self.assertEqual(diagnostics["last_provider_event"], "fixture-start")
        self.assertEqual(diagnostics["process_group_id"], os.getpgid(process.pid))

    def test_unproven_process_ownership_fails_closed_with_diagnostics(self):
        execution_id, process = self.fixture()
        session = self.sessions.load(session_identifier(execution_id))
        session["process_group_id"] = os.getpgrp()
        self.sessions.save(session)
        with self.assertRaisesRegex(MissionExecutionError, "PROCESS_OWNERSHIP_UNPROVEN"):
            self.runtime.stop(execution_id, at=AT)
        state = self.executions.load(execution_id)
        self.assertEqual(state["state"], "TerminationFailed")
        self.assertEqual(state["termination_failure"]["category"], "PROCESS_OWNERSHIP_UNPROVEN")
        self.assertIsNone(process.poll())


if __name__ == "__main__":
    unittest.main()
