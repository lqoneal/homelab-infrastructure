#!/usr/bin/env python3
"""Qualification of the read-only Operation Beta controller projections."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts" / "zeus"


class BetaControllerTests(unittest.TestCase):
    def run_zeus(self, *args):
        with tempfile.TemporaryDirectory(dir="/home/loneal") as directory:
            env = os.environ.copy()
            env.update({"ZEUS_NO_INTRO": "1", "ZEUS_TESTING": "1",
                        "ZEUS_OPERATOR_STATE": str(Path(directory) / "operator-state.json")})
            return subprocess.run([str(ZEUS), *args], cwd=ROOT, env=env,
                                  text=True, capture_output=True, check=False)

    def test_operation_verify_is_integrity_bound(self):
        result = self.run_zeus("operation", "verify", "BETA")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["production_baseline"], "OA-v1.0.0")
        self.assertEqual(value["development_baseline"], "OB-PLAN-v1.0.0")
        self.assertEqual(value["mission_families"], ["ZDCL", "CAGF", "EPE"])

    def test_family_roadmaps_and_mission_views_share_authority(self):
        for family, mission in (("ZDCL", "ZDCL-01"), ("CAGF", "CAGF-01"), ("EPE", "EPE-01")):
            roadmap = self.run_zeus("mission", "roadmap", family, "--verify")
            state = self.run_zeus("mission", "status", mission, "--verify")
            self.assertEqual(roadmap.returncode, 0, roadmap.stderr)
            self.assertEqual(state.returncode, 0, state.stderr)
            self.assertEqual(json.loads(roadmap.stdout)["roadmap_family"], family)
            self.assertEqual(json.loads(state.stdout)["family"], family)

    def test_beta_next_action_selects_zdcl_foundation(self):
        result = self.run_zeus("operation", "next-action", "BETA", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["recommended_mission"], "ZDCL-01")
        self.assertIn("ZDCL-01", value["next_authorized_action"])

    def test_unknown_family_fails_closed(self):
        result = self.run_zeus("mission", "roadmap", "UNKNOWN", "--verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BETA_UNKNOWN_MISSION_FAMILY", result.stderr)


if __name__ == "__main__":
    unittest.main()
