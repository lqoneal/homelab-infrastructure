#!/usr/bin/env python3
"""Current-convergence qualification for OA-04 context reconstruction."""

import unittest
from pathlib import Path

from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.eos.operational_alpha_status import resolve


ROOT = Path(__file__).resolve().parents[2]
WOP = "WOP-48f1d7d1-4995-5f3e-9b5e-fb2f69595111"


class OA04CurrentContextTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ConvergenceRuntime(ROOT)

    def test_exact_current_context_is_resolvable(self):
        entity, wop, _ = self.runtime._wop(WOP, 1)
        self.assertEqual(WOP, entity["entity_id"])
        self.assertEqual("ACTIVE", wop["status"])
        self.assertEqual("OA-04-PROJECT-AND-OPERATIONAL-CONTEXT-RECONSTRUCTION", wop["phase_id"])

    def test_authority_plan_and_activation_bind_the_same_wop(self):
        authority, _ = self.runtime._authority("AR-OA-04-001")
        _, plan, _ = self.runtime.operational_gate_plan(wop_id=WOP, revision=1)
        _, activation, _ = self.runtime.activation_record(activation_id="ACT-OA-04-001")
        for item in (authority, plan, activation):
            self.assertEqual(WOP, item["implementation_wop"]["wop_id"])
        self.assertIn("EXECUTE_WORK", plan["gate_plan"]["gates"])

    def test_current_status_is_convergence_only(self):
        status = resolve(ROOT)
        self.assertEqual("OA-04", status["active_gate"])
        self.assertEqual("ACTIVE", status["status"])
        self.assertEqual("EXCLUDED_EVIDENCE_ONLY", status["historical_progressive_runtime"])


if __name__ == "__main__":
    unittest.main()
