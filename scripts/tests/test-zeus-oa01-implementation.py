#!/usr/bin/env python3
"""OA-01 implementation-completion and resume integration tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts/zeus"
PACKAGE = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001"


class ZeusOA01ImplementationTests(unittest.TestCase):
    def run_zeus(self, *arguments: str):
        result = subprocess.run(
            [str(ZEUS), *arguments],
            cwd=ROOT,
            env={**os.environ, "ZEUS_TESTING": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_accepted_oa01_artifacts_remain_immutable_and_discoverable(self):
        state = PACKAGE / "runtime/state.json"
        evidence = PACKAGE / "runtime/evidence/OA-01/IMPLEMENTATION.json"
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (state, evidence)
        }
        marker = PACKAGE / "runtime/evidence/OA-01/VERIFIED"
        marker_before = (
            hashlib.sha256(marker.read_bytes()).hexdigest()
            if marker.exists() else None
        )
        first = self.run_zeus("gate", "receipt", "OA-01")
        second = self.run_zeus("gate", "receipt", "OA-01")
        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (state, evidence)
        }
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertEqual(first["gate_id"], "OA-01")
        self.assertEqual(first["integrity"], "PASS")
        marker_after = (
            hashlib.sha256(marker.read_bytes()).hexdigest()
            if marker.exists() else None
        )
        self.assertEqual(marker_before, marker_after)
        blockers = self.run_zeus("mission", "blockers")
        runtime = json.loads(state.read_text())
        oa02 = runtime["gates"]["OA-02"]["state"]
        expected = {
            "IMPLEMENTATION_REQUIRED": "OA-02_IMPLEMENTATION_REQUIRED",
            "AWAITING_OPERATOR_VERIFICATION": (
                "OA-02_OPERATOR_ACCEPTANCE_REQUIRED"
                if (PACKAGE / "runtime/evidence/OA-02/VERIFIED").exists()
                else "OA-02_OPERATOR_VERIFICATION_REQUIRED"
            ),
            "ACCEPTED": (
                f"{runtime['active_gate']}_OPERATOR_ACCEPTANCE_REQUIRED"
                if (
                    PACKAGE / f"runtime/evidence/{runtime['active_gate']}/VERIFIED"
                ).exists()
                else f"{runtime['active_gate']}_"
                + (
                    "OPERATOR_VERIFICATION_REQUIRED"
                    if runtime["gates"][runtime["active_gate"]]["state"]
                    == "AWAITING_OPERATOR_VERIFICATION"
                    else "IMPLEMENTATION_REQUIRED"
                )
            ),
        }
        self.assertIn(oa02, expected)
        self.assertEqual(blockers["blockers"], [expected[oa02]])


if __name__ == "__main__":
    unittest.main()
