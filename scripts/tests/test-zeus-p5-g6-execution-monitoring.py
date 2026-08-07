#!/usr/bin/env python3
"""Focused read-only P5-G6 execution monitoring tests."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp import execution_monitoring
from scripts.lib.emp.runtime_paths import runtime_identity


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
EXECUTION = "EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e"


class ExecutionMonitoringTests(unittest.TestCase):
    def test_canonical_roadmap_resolves_revision_aware_position(self):
        value = execution_monitoring._roadmap(ROOT)
        self.assertEqual(value["phase_current"], 5)
        self.assertEqual(value["phase_total"], 12)
        self.assertEqual(value["gate_current"], 6)
        self.assertEqual(value["gate_total"], 10)
        self.assertEqual(value["gate_id"], "P5-G6")

    def test_current_execution_projection_is_read_only_and_source_bound(self):
        value = execution_monitoring.status(ROOT, EXECUTION)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["mission_id"], MISSION)
        self.assertEqual(value["execution_state"], "EXECUTING")
        self.assertEqual(value["execution_liveness"], "ALIVE")
        self.assertEqual(value["provider_liveness"], "ALIVE")
        self.assertEqual(value["provider_process_state"], "RUNNING")
        self.assertEqual(value["mission_work_state"], "STARTED")
        self.assertEqual(value["repository_work_state"], "NOT_STARTED")
        self.assertEqual(value["progress_state"], "ACTIVE")
        self.assertEqual(value["last_progress_event"], "MISSION_WORK_STARTED")
        self.assertEqual(value["phase"], {"current": 5, "total": 12, "id": "P5"})
        self.assertEqual(value["gate"]["current"], 6)
        self.assertEqual(value["gate"]["total"], 10)
        self.assertTrue(value["read_only"])
        self.assertEqual(value["replay"], "IDEMPOTENT")
        self.assertIn("execution_start_transaction", value["source_records"])

    def test_verifier_exposes_independent_checks(self):
        value = execution_monitoring.verify(ROOT, EXECUTION)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["verification_result"], "PASS")
        self.assertTrue(all(result == "PASS" for result in value["checks"].values()))

    def test_provider_bound_active_projection_is_execution_active(self):
        value = execution_monitoring.status(ROOT, EXECUTION)
        self.assertEqual(value["provider_process_state"], "RUNNING")
        self.assertEqual(value["execution_state"], "EXECUTING")

    def test_executing_mission_work_started_does_not_start_repository_work(self):
        transaction = {"execution_started": True, "mission_work_started": False,
                       "repository_work_started": False}
        record = {"execution_state": "EXECUTING", "mission_work_started": True,
                  "repository_work_started": False, "last_progress_event": "MISSION_WORK_STARTED"}
        self.assertEqual(execution_monitoring._derive_work_states(transaction, record), (True, False))

    def test_ready_boundary_before_begin_is_not_started(self):
        transaction = {"execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
                       "execution_started": True, "mission_work_started": False,
                       "repository_work_started": False}
        self.assertEqual(execution_monitoring._derive_work_states(transaction, None), (False, False))

    def test_work_state_derivation_converges_for_replay_status_and_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "runtime-identity.json").write_text(json.dumps({
                **runtime_identity(ROOT), "runtime_root": str(runtime)
            }))
            (runtime / "execution-start-transactions").mkdir()
            (runtime / "execution-monitoring").mkdir()
            transaction = {"execution_id": EXECUTION, "mission_id": MISSION, "wop_id": "WOP-BETA",
                           "execution_session_id": "EXECUTION-SESSION", "provider_session_id": "PROVIDER-SESSION",
                           "provider_id": "PROVIDER", "provider_invocation_id": "INVOCATION",
                           "execution_started": True, "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
                           "mission_work_started": False, "repository_work_started": False}
            transaction["artifact_digest"] = execution_monitoring._digest(transaction)
            (runtime / "execution-start-transactions" / f"{EXECUTION}.json").write_text(json.dumps(transaction))
            record = {"execution_id": EXECUTION, "execution_state": "EXECUTING",
                      "execution_monitoring_active": True, "mission_work_started": True,
                      "repository_work_started": False, "progress_state": "ACTIVE",
                      "last_progress_event": "MISSION_WORK_STARTED"}
            record["record_digest"] = execution_monitoring._digest(record)
            (runtime / "execution-monitoring" / f"{EXECUTION}.json").write_text(json.dumps(record))
            status = execution_monitoring.status(ROOT, EXECUTION, runtime_root=runtime)
            verified = execution_monitoring.verify(ROOT, EXECUTION, runtime_root=runtime)
            self.assertEqual(status["mission_work_state"], "STARTED")
            self.assertEqual(status["repository_work_state"], "NOT_STARTED")
            self.assertEqual(verified["mission_work_state"], status["mission_work_state"])
            self.assertEqual(verified["repository_work_state"], status["repository_work_state"])
            self.assertEqual(verified["verification_result"], "PASS")

    def test_contradictory_monitoring_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "execution-start-transactions").mkdir()
            (runtime / "execution-monitoring").mkdir()
            transaction = {
                "execution_id": EXECUTION, "mission_id": MISSION, "wop_id": "WOP-BETA",
                "execution_session_id": "SESSION", "provider_id": "PROVIDER",
                "provider_invocation_id": "INVOCATION", "execution_started": False,
                "provider_process_bound": True, "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
                "artifact_digest": "fixture",
            }
            transaction["artifact_digest"] = execution_monitoring._digest(
                {key: value for key, value in transaction.items() if key != "artifact_digest"}
            )
            (runtime / "execution-start-transactions" / f"{EXECUTION}.json").write_text(json.dumps(transaction))
            (runtime / "execution-monitoring" / f"{EXECUTION}.json").write_text(json.dumps({
                "execution_id": EXECUTION, "execution_state": "EXECUTING",
            }))
            # Exercise the deterministic contradiction rule without invoking
            # runtime discovery or creating any authoritative state.
            with self.assertRaises(execution_monitoring.ExecutionMonitoringError) as raised:
                execution_monitoring._projection(
                    ROOT, runtime,
                    runtime / "execution-start-transactions" / f"{EXECUTION}.json",
                    execution_monitoring._load(runtime / "execution-start-transactions" / f"{EXECUTION}.json"),
                )
            self.assertEqual(raised.exception.code, "EXECUTION_STATE_CONFLICT")

    def test_cli_status_and_verify_are_machine_readable(self):
        for action in ("status", "verify"):
            result = subprocess.run([str(ROOT / "scripts/zeus"), "execution", action, EXECUTION, "--json"],
                                    cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            value = json.loads(result.stdout)
            self.assertEqual(value["result"], "PASS")
            self.assertEqual(value["phase"]["total"], 12)


if __name__ == "__main__":
    unittest.main()
