#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts/zeus"
MISSION = "P2-038-CORRECTIVE"


class ZeusEngineeringExecutionTests(unittest.TestCase):
    def run_zeus(self, *arguments):
        result = subprocess.run(
            [str(ZEUS), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={"PATH": "/usr/bin:/bin", "ZEUS_NO_INTRO": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_zeus_snapshot_resolves_mission_contract(self):
        snapshot = self.run_zeus("mission", "snapshot", MISSION)
        self.assertEqual(snapshot["mission"]["id"], MISSION)
        self.assertEqual(snapshot["lifecycle"]["state"], "completed")
        self.assertEqual(snapshot["lifecycle"]["implementation_status"], "complete")
        self.assertEqual(snapshot["lifecycle"]["acceptance_status"], "not_recorded")

    def test_zeus_execution_interface_resolves_mission(self):
        snapshot = self.run_zeus("execution", "resolve", MISSION)
        self.assertEqual(snapshot["mission"]["id"], MISSION)
        self.assertEqual(snapshot["blockers"], [])

    def test_zeus_qualification_is_deterministic_and_complete(self):
        first = self.run_zeus("mission", "qualify", MISSION)
        second = self.run_zeus("mission", "qualify", MISSION)
        self.assertEqual(first, second)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(first["mission_contract_count"], 1)
        self.assertEqual(first["implementation_status"], "complete")
        self.assertEqual(first["acceptance_status"], "not_recorded")
        self.assertEqual(first["blockers"], [])
        self.assertEqual(
            first["approvals"]["operator_acceptance"]["state"], "not_recorded"
        )
        self.assertEqual(
            first["next_authorized_action"],
            "REQUEST_P2_038_CORRECTIVE_ACCEPTANCE",
        )


if __name__ == "__main__":
    unittest.main()
