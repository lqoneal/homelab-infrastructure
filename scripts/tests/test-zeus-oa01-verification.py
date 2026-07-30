#!/usr/bin/env python3
"""Operator-visible OA-01 mission verification interface tests."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.lib.emp import oa01_gate_verification


ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts/zeus"


class ZeusOA01VerificationTests(unittest.TestCase):
    def run_zeus(self, action: str):
        result = subprocess.run(
            [str(ZEUS), "mission", action],
            cwd=ROOT,
            env={**os.environ, "ZEUS_TESTING": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_current_mission_is_deterministic_and_authority_bound(self):
        first = self.run_zeus("show")
        second = self.run_zeus("show")
        self.assertEqual(first, second)
        self.assertEqual(first["governance_state"], "AUTHORIZED")
        self.assertEqual(first["mission_contract"]["lifecycle"], "active")
        self.assertEqual(
            first["progressive_wop"]["package_id"],
            "GH-ZEUS-OA-PROGRESSIVE-001",
        )

    def test_governance_and_execution_state_are_independent(self):
        value = self.run_zeus("state")
        self.assertIn("governance_state", value)
        self.assertIn("execution_state", value)
        self.assertNotEqual(value["governance_state"], value["execution_state"])

    def test_acceptance_observations_have_independent_commands(self):
        blockers = self.run_zeus("blockers")
        readiness = self.run_zeus("readiness")
        authority = self.run_zeus("authority")
        next_action = self.run_zeus("next")
        contract = self.run_zeus("contract")
        self.assertEqual(blockers["blockers"], readiness["blockers"])
        self.assertIn("authority_source", authority)
        self.assertIn("next_authorized_action", next_action)
        self.assertEqual(contract["resolution"], "AUTHORIZED")

    def test_interruption_before_marker_leaves_only_nonqualifying_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            material = {
                "bindings": {
                    "repository_identity": root.name,
                    "repository_root": str(root),
                    "branch": "main",
                    "head": "a" * 40,
                    "authority_source": "authority.yaml",
                },
                "working_tree": {"entries": [], "digest": "b" * 64},
            }

            def result(_root, arguments):
                negative = arguments[-1:] == ["UNKNOWN-OA01-MISSION"]
                return {
                    "command": arguments,
                    "exit_code": 78 if negative else 0,
                    "stdout": "" if negative else "{}\n",
                    "stderr": "FAIL\n" if negative else "",
                    "stdout_sha256": "c" * 64,
                    "stderr_sha256": "d" * 64,
                }

            with (
                mock.patch.object(
                    oa01_gate_verification, "_current_material",
                    return_value=material,
                ),
                mock.patch.object(
                    oa01_gate_verification, "_run", side_effect=result,
                ),
                mock.patch.dict(
                    os.environ, {"ZEUS_OA01_INTERRUPT_BEFORE_MARKER": "1"},
                ),
            ):
                with self.assertRaisesRegex(
                    oa01_gate_verification.OA01GateVerificationError,
                    "interrupted before marker",
                ):
                    oa01_gate_verification.verify(root)
            evidence = (
                root / oa01_gate_verification.progressive_oa.PACKAGE_PATH
                / "runtime/evidence/OA-01/VERIFICATION.json"
            )
            self.assertTrue(evidence.is_file())
            self.assertFalse(evidence.with_name("VERIFIED").exists())


if __name__ == "__main__":
    unittest.main()
