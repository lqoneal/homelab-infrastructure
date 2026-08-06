#!/usr/bin/env python3
"""Focused P4-G3A Operation Beta authority projection tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path.home() / ".local" / "state" / "zeus-runtime" / "homelab-6bd83f9079d6fc57"


class OperationBetaAuthorityTests(unittest.TestCase):
    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), "--runtime-root", str(RUNTIME), *args],
            cwd=ROOT, env={**os.environ, "ZEUS_NO_INTRO": "1"},
            text=True, capture_output=True, check=False,
        )

    def test_authority_resolves_beta_without_manual_governance_policy(self):
        result = self.cli("authority", "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["authority_integrity"], "PASS")
        self.assertEqual(value["authority_framework"], "OPERATION_BETA")
        self.assertEqual(value["authority_resolution"], "PASS")
        self.assertEqual(value["authority_digest_validation"], "PASS")
        self.assertEqual(value["active_operation"], "BETA")
        self.assertEqual(value["authority_source"], "Operation Beta")
        self.assertEqual(value["oa_authority"], "SUPERSEDED")
        self.assertNotIn("manual-governance-wop-authority-policy.yaml", json.dumps(value))

    def test_status_uses_beta_projection(self):
        result = self.cli("status", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["authority_framework"], "OPERATION_BETA")
        self.assertEqual(value["active_operation"], "BETA")
        self.assertNotEqual(value.get("active_gate"), "OA-08")

    def test_operation_beta_and_mission_projections_remain_pass(self):
        operation = self.cli("operation", "verify", "BETA", "--json")
        mission = self.cli("mission", "list", "--json")
        self.assertEqual(operation.returncode, 0, operation.stderr)
        self.assertEqual(mission.returncode, 0, mission.stderr)
        self.assertEqual(json.loads(operation.stdout)["result"], "PASS")
        self.assertEqual(json.loads(mission.stdout)["operation"], "BETA")


if __name__ == "__main__":
    unittest.main()
