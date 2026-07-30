#!/usr/bin/env python3
"""OA-05 Mission Staging Contract qualification."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


_SOURCE = Path(__file__).with_name("test-zeus-stage1-runtime.py")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_SPEC = importlib.util.spec_from_file_location("zeus_stage1_tests", _SOURCE)
assert _SPEC and _SPEC.loader
stage1 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(stage1)


class OA05MissionStagingContractTests(stage1.ZeusStage1RuntimeTests):
    """Run the production staging contract's positive and fail-closed cases."""

    def test_replay_preserves_exact_contract_and_creates_no_duplicate(self):
        first = self.runtime().submit(self.package, at=self.at)
        second = self.runtime().submit(self.package, at=self.at)
        self.assertEqual(first["staging_contract"], second["staging_contract"])
        self.assertEqual(
            first["staging_contract_digest"], second["staging_contract_digest"]
        )
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(1, self.runtime().status()["states"]["STAGED"])

    def test_restart_recovers_complete_staged_contract(self):
        first = self.runtime().submit(self.package, at=self.at)
        recovered = self.runtime().show(first["instance_id"])
        self.assertEqual("STAGED", recovered["state"])
        self.assertEqual(first["staging_contract"], recovered["staging_contract"])
        self.assertEqual(
            first["staging_contract_digest"], recovered["staging_contract_digest"]
        )


class OA05CumulativeLifecycleTests(unittest.TestCase):
    """Prove the current cumulative boundary without reopening prior gates."""

    def test_oa01_through_oa05_receipts_are_current_and_valid(self):
        from scripts.lib.emp import progressive_oa

        for gate_id in ("OA-01", "OA-02", "OA-03", "OA-04", "OA-05"):
            result = progressive_oa.verify_receipt(ROOT, gate_id)
            self.assertEqual("PASS", result["integrity"])

    def test_oa06_is_active_pending_and_later_gates_are_pending(self):
        from scripts.lib.emp import progressive_oa

        state = progressive_oa.load_state(ROOT)
        self.assertEqual("OA-06", state["active_gate"])
        self.assertEqual("ACCEPTED", state["gates"]["OA-05"]["state"])
        self.assertIsNotNone(state["gates"]["OA-05"]["acceptance_receipt"])
        for number in range(6, 31):
            item = state["gates"][f"OA-{number:02d}"]
            self.assertEqual("PENDING", item["state"])
            self.assertIsNone(item["acceptance_receipt"])

    def test_live_staging_has_no_dispatch_execution_or_declaration(self):
        from scripts.lib.emp import progressive_oa
        from scripts.lib.emp.stage1_runtime import Stage1Runtime

        stage1_directory = ROOT / ".zeus/runtime/stage1"
        status = Stage1Runtime(ROOT, stage1_directory).status()
        self.assertEqual(0, status["mission_count"])
        self.assertEqual(0, status["states"]["STAGED"])
        self.assertFalse(progressive_oa.status(ROOT)["declaration_authorized"])
        state = json.loads(
            (ROOT / progressive_oa.PACKAGE_PATH / "runtime/state.json").read_text()
        )
        self.assertNotEqual("DECLARATION_PREPARATION_COMPLETE", state["status"])


if __name__ == "__main__":
    unittest.main()
