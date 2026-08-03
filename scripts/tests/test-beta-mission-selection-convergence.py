"""Qualification for the canonical Beta mission-selection projections."""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BetaMissionSelectionConvergenceTests(unittest.TestCase):
    def run_zeus(self, *args):
        return subprocess.run([str(ROOT / "scripts/zeus"), *args, "--json"], cwd=ROOT,
                              text=True, capture_output=True, check=False)

    def test_selection_commands_use_cagf(self):
        for action in ("list", "queue", "next", "recommend", "health"):
            result = self.run_zeus("mission", action)
            self.assertEqual(result.returncode, 0, (action, result.stderr))
            value = json.loads(result.stdout)
            self.assertEqual(value["recommended_mission"], "CAGF-01", action)
            self.assertEqual(value["selection_source"], "operational_beta._selected_card")

    def test_beta_inspection_views_are_supported(self):
        for action in ("authority", "contract", "snapshot"):
            result = self.run_zeus("mission", action, "CAGF-01")
            self.assertEqual(result.returncode, 0, (action, result.stderr))
            value = json.loads(result.stdout)
            self.assertEqual(value["result"], "PASS")
            self.assertEqual(value["mission_id"], "CAGF-01")

    def test_human_and_json_selection_agree(self):
        machine = json.loads(self.run_zeus("mission", "recommend").stdout)
        human = subprocess.run([str(ROOT / "scripts/zeus"), "mission", "recommend"], cwd=ROOT,
                               text=True, capture_output=True, check=False)
        self.assertEqual(human.returncode, 0)
        self.assertIn(machine["recommended_mission"], human.stdout)
        self.assertIn(machine["next_authorized_action"], human.stdout)


if __name__ == "__main__":
    unittest.main()
