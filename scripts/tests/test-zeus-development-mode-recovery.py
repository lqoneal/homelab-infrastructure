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

    def test_valid_submission_generates_authority_and_closes(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(result["state"], "CLOSED")
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
            self.assertEqual(interrupted["state"], "INTERRUPTED")
            resumed = runtime.submit_development(FIXTURE)
            self.assertEqual(resumed["state"], "CLOSED")
            self.assertEqual(resumed["phases"][-1], "CLOSED")

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
