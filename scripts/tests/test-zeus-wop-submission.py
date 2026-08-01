#!/usr/bin/env python3
"""Qualification for the mission-oriented WOP submission resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))


class ZeusWopSubmissionTests(unittest.TestCase):
    def run_zeus(self, *args: str) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory(prefix="zeus-beta03-") as temporary:
            state = Path(temporary) / "operator.json"
            shutil.copy(ROOT / ".zeus/runtime/operator-interface-state.json", state)
            environment = {
                **os.environ,
                "ZEUS_TESTING": "1",
                "ZEUS_OPERATOR_STATE": str(state),
                "ZEUS_NO_INTRO": "1",
                "ZEUS_STAGE1_STATE": str(Path(temporary) / "stage1"),
            }
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/zeus"), *args, "--json"],
                cwd=ROOT, env=environment, text=True,
                capture_output=True, check=False,
            )
            return result.returncode, json.loads(result.stdout)

    def test_mission_id_fails_closed_without_authoritative_package(self):
        from scripts.lib.emp.mission_submission import submit_by_mission

        with patch("scripts.lib.emp.mission_submission._package_candidates", return_value=[]):
            value = submit_by_mission(ROOT, "ZDCL-01", state_directory=ROOT / ".zeus/runtime/stage1")
        code = 78
        self.assertEqual(code, 78)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["resolution"], "WOP_PACKAGE_UNAVAILABLE")
        self.assertEqual(value["mission_id"], "ZDCL-01")
        self.assertEqual(value["family"], "ZDCL")
        self.assertEqual(value["title"], "Native session foundation")

    def test_mission_id_submission_reuses_published_package(self):
        from scripts.lib.emp.mission_submission import submit_by_mission

        record = {
            "wop_id": "WOP-ZDCL-01-FOUNDATION-001",
            "package_digest": "a" * 64,
            "instance_id": "ZEUS-MISSION-test",
            "state": "STAGED",
        }
        with patch("scripts.lib.emp.mission_submission.Stage1Runtime.submit", return_value=record):
            value = submit_by_mission(ROOT, "ZDCL-01", state_directory=ROOT / ".zeus/runtime/stage1")
        code = 0
        self.assertEqual(code, 0)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["resolution"], "AUTHORITATIVE_PACKAGE_REUSED")
        self.assertEqual(value["mission_id"], "ZDCL-01")
        self.assertEqual(value["family"], "ZDCL")
        self.assertEqual(value["wop_id"], "WOP-ZDCL-01-FOUNDATION-001")
        self.assertTrue(value["package_digest"])
        self.assertTrue(value["submission_id"])
        self.assertEqual(value["selection_rationale"], "first eligible mission in the authoritative Beta sequence")
        self.assertTrue(value["authority"])
        self.assertEqual(value["queue_state"], "STAGED")
        self.assertEqual(value["admission_readiness"], "READY")
        self.assertIn("zeus admit-mission start", value["next_authorized_action"])

    def test_non_beta_mission_is_not_routed_to_legacy_submission(self):
        code, value = self.run_zeus("mission", "submit", "OA-30")
        self.assertEqual(code, 78)
        self.assertEqual(value["resolution"], "NON_BETA_MISSION")


if __name__ == "__main__":
    unittest.main()
