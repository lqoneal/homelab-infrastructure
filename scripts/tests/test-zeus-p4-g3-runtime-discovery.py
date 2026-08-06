#!/usr/bin/env python3
"""Focused read-only discovery checks for authoritative P4-G3 materialization."""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"


class P4G3RuntimeDiscoveryTests(unittest.TestCase):
    def run_zeus(self, *args):
        return subprocess.run([str(ROOT / "scripts/zeus"), *args], cwd=ROOT, text=True,
                              capture_output=True, check=False)

    def test_materialized_mission_is_discoverable_read_only(self):
        before = {p: p.read_bytes() for p in Path("/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57").rglob("*.json")}
        for action in ("status", "blockers", "next", "snapshot"):
            result = self.run_zeus("mission", action, MISSION, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value["mission"], "DISCOVERABLE")
            self.assertEqual(value["bootstrap_state"], "READY_FOR_EXECUTION_PROVIDER")
            self.assertTrue(value["provider_ready"])
            self.assertTrue(value["provider_selected"])
            self.assertEqual(value["next_action"], "BEGIN_CONTROLLED_MISSION_WORK")
        after = {p: p.read_bytes() for p in Path("/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57").rglob("*.json")}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
