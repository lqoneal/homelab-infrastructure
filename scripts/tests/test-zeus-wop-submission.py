#!/usr/bin/env python3
"""Qualification for the mission-oriented WOP submission resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
            }
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/zeus"), *args, "--json"],
                cwd=ROOT, env=environment, text=True,
                capture_output=True, check=False,
            )
            return result.returncode, json.loads(result.stdout)

    def test_mission_id_fails_closed_without_authoritative_package(self):
        code, value = self.run_zeus("mission", "submit", "ZDCL-01")
        self.assertEqual(code, 78)
        self.assertEqual(value["result"], "BLOCKED")
        self.assertEqual(value["resolution"], "WOP_PACKAGE_UNAVAILABLE")
        self.assertEqual(value["mission_id"], "ZDCL-01")

    def test_non_beta_mission_is_not_routed_to_legacy_submission(self):
        code, value = self.run_zeus("mission", "submit", "OA-30")
        self.assertEqual(code, 78)
        self.assertEqual(value["resolution"], "NON_BETA_MISSION")


if __name__ == "__main__":
    unittest.main()
