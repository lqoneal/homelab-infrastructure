#!/usr/bin/env python3
"""Qualification for the bounded Development Mode recovery path."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(ROOT))
from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime


FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class DevelopmentModeRecoveryTests(unittest.TestCase):
    def runtime(self, directory):
        return Stage1Runtime(ROOT, directory, operator_resolver=lambda: "loneal")

    def test_valid_submission_stops_before_unsubstantiated_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(result["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(result["phases"], ["VALIDATED", "PACKAGED", "REGISTERED", "AUTHORIZED", "ADMITTED"])
            self.assertEqual(result["next_action"], "Dispatch to a qualified Development execution agent")
            self.assertNotIn("execution", result["receipts"])
            self.assertEqual(result["execution_mode"], "DEVELOPMENT")
            self.assertEqual(result["authorization"]["authority"], "Engineering Governance")
            self.assertTrue(result["registration"]["registration_id"].startswith("EMM-DEV-"))
            self.assertEqual(result["provenance"]["repository"], str(ROOT))

    def test_repeated_submission_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            first = runtime.submit_development(FIXTURE)
            second = runtime.submit_development(FIXTURE)
            self.assertEqual(first["instance_id"], second["instance_id"])
            self.assertEqual(first["package_digest"], second["package_digest"])
            self.assertTrue(second["idempotent_replay"])

    def test_interrupted_submission_resumes(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            interrupted = runtime.submit_development(FIXTURE, interrupt_after="QUALIFIED")
            self.assertEqual(interrupted["state"], "AWAITING_EXECUTION_DISPATCH")
            resumed = runtime.submit_development(FIXTURE)
            self.assertEqual(resumed["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(resumed["phases"][-1], "ADMITTED")

    def test_receipts_are_required_for_downstream_phases(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(set(result["receipts"]), {"validation", "packaging", "registration", "authorization", "admission"})
            self.assertNotIn("dispatch", result["receipts"])
            self.assertNotIn("qualification", result["receipts"])
            self.assertNotIn("publication", result["receipts"])
            self.assertNotIn("synchronization", result["receipts"])
            self.assertNotIn("closeout", result["receipts"])

    def test_receipt_backed_store_rejects_false_terminal_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            result = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(result)
            forged["state"] = "CLOSED"
            forged["phases"] = forged["phases"] + ["CLOSED"]
            runtime.store.save(forged)
            with self.assertRaises(Stage1Error):
                runtime.store.find(result["instance_id"])

    def test_unqualified_dispatch_result_stays_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Stage1Runtime(
                ROOT, Path(temporary) / "stage1", operator_resolver=lambda: "loneal",
                execution_executor=lambda _record: {"dispatch_receipt": {"receipt_id": "missing-agent"}},
            )
            result = runtime.submit_development(FIXTURE)
            self.assertEqual(result["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertNotIn("dispatch", result["receipts"])

    def test_invalid_submission_has_no_state_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            bad = Path(temporary) / "bad"
            shutil.copytree(FIXTURE, bad)
            mission = bad / "mission.yaml"
            text = mission.read_text().replace("execution_mode: DEVELOPMENT", "execution_mode: OPERATIONAL")
            mission.write_text(text)
            state = Path(temporary) / "stage1"
            with self.assertRaises(Stage1Error):
                self.runtime(state).submit_development(bad)
            self.assertFalse(state.exists())

    def test_protected_baselines_are_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(set(result["protected_baselines"]), {"OA-v1.0.0", "OB-PLAN-v1.0.0"})


if __name__ == "__main__":
    unittest.main()
