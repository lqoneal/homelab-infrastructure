#!/usr/bin/env python3
"""Regression coverage for the shared Zeus controller presentation contract."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts" / "zeus"


class ZeusControllerInterfaceTests(unittest.TestCase):
    def run_zeus(self, *arguments):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment.update({
                "ZEUS_NO_INTRO": "1",
                "ZEUS_TESTING": "1",
                "ZEUS_OPERATOR_STATE": str(Path(directory) / "operator-state.json"),
            })
            return subprocess.run(
                [str(ZEUS), *arguments], cwd=ROOT, env=environment,
                text=True, capture_output=True, check=False,
            )

    def test_default_is_operator_text(self):
        result = self.run_zeus("mission", "readiness", "OA-11")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Mission readiness", result.stdout)
        self.assertNotEqual(result.stdout[:1], "{")

    def test_verify_is_deterministic_json(self):
        result = self.run_zeus("mission", "readiness", "OA-11", "--verify")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["mission_id"], "OA-11")

    def test_blocker_selector_uses_requested_mission(self):
        result = self.run_zeus("mission", "blockers", "OA-11", "--verify")
        self.assertEqual(result.returncode, 0)
        value = json.loads(result.stdout)
        self.assertEqual(value["mission_id"], "OA-11")
        self.assertEqual(value["blocking_conditions"], [])
        self.assertEqual(value["missing_capabilities"], [])

    def test_active_controllers_share_current_model_state(self):
        commands = (
            ("mission", "state", "OA-15"),
            ("mission", "explain", "OA-15"),
            ("mission", "readiness", "OA-15"),
            ("mission", "blockers", "OA-15"),
            ("mission", "prerequisites", "OA-15"),
        )
        for command in commands:
            result = self.run_zeus(*command, "--verify")
            self.assertEqual(result.returncode, 0, command)
            value = json.loads(result.stdout)
            self.assertEqual(value["mission_id"], "OA-15", command)
            self.assertIn("OA-15", json.dumps(value), command)
            self.assertIn("COMPLETED", json.dumps(value), command)

    def test_next_action_uses_model_current_mission(self):
        result = self.run_zeus("next-action", "--json")
        self.assertEqual(result.returncode, 0)
        value = json.loads(result.stdout)
        self.assertEqual(value["current_mission"], "OA-16")
        self.assertIsNone(value["next_authorized_action"]["wop"])


if __name__ == "__main__":
    unittest.main()
