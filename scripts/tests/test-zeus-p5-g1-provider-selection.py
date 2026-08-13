"""Focused P5-G1 provider-selection qualification."""
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
CURRENT_LIFECYCLE_MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
RUNTIME = Path("/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57")
STAGE_DIRS = (
    "provider-selection", "selected-providers", "provider-qualifications",
    "provider-selection-receipts", "provider-selection-journals", "dispatch-readiness",
)


def run(*args: str) -> dict:
    result = subprocess.run([str(ROOT / "scripts/zeus"), *args, "--json"], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class ProviderSelectionQualification(unittest.TestCase):
    def test_live_selection_and_replay_are_deterministic(self) -> None:
        first = run("provider", "verify", MISSION)
        second = run("provider", "select", MISSION)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(second["result"], "PASS")
        self.assertEqual(second["duplicate_provider_selection"], "IDEMPOTENT")
        self.assertEqual(second["provider_id"], "zeus-local-loneal-01")
        self.assertEqual(second["next_authorized_action"], "EVALUATE_PROVIDER_DISPATCH")

    def test_exact_stage_cardinality_and_downstream_boundary(self) -> None:
        value = run("provider", "artifacts", MISSION)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(len(value["artifacts"]), 6)
        for directory in STAGE_DIRS:
            mission_records = [
                json.loads(path.read_text())
                for path in (RUNTIME / directory).glob("*.json")
                if json.loads(path.read_text()).get("mission_id") == MISSION
            ]
            self.assertEqual(len(mission_records), 1)
        # Historical Beta downstream records are preserved.  Operation Beta's
        # current lifecycle has independently advanced to one receipt-backed,
        # idle execution session; it has not crossed the mission-work boundary.
        sessions = [
            json.loads(path.read_text())
            for path in (RUNTIME / "execution-sessions").glob("*.json")
            if json.loads(path.read_text()).get("mission_id") == CURRENT_LIFECYCLE_MISSION
        ]
        self.assertEqual(len(sessions), 1)
        self.assertFalse(sessions[0]["mission_work_started"])
        self.assertFalse(sessions[0]["repository_work_started"])

    def test_mission_projection_and_read_only_verification(self) -> None:
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in RUNTIME.rglob("*") if path.is_file()}
        value = run("provider", "verify", MISSION)
        mission = run("mission", "verify", MISSION)
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in RUNTIME.rglob("*") if path.is_file()}
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        self.assertEqual(mission["result"], "PASS")
        self.assertEqual(mission["lifecycle"]["provider_selected"], True)
        self.assertEqual(mission["next_authorized_action"], "FOLLOW_CURRENT_OPERATION_BETA_AUTHORITY")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
