#!/usr/bin/env python3
"""Focused T-AUTH-01 Model-B authority qualification."""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from scripts.lib.eos.execution_interface import ExecutionInterface
from scripts.lib.eos.model_b_authority import EMM_ID, WOP_DIGEST, WOP_ID, resolve


class ModelBAuthorityTests(unittest.TestCase):
    root = Path(__file__).parents[2]

    def test_current_model_b_chain(self):
        value = resolve(self.root)
        self.assertEqual(value["emm_id"], EMM_ID)
        self.assertEqual(value["wop_id"], WOP_ID)
        self.assertEqual(value["wop_digest"], WOP_DIGEST)
        self.assertTrue(value["emm_wop_binding"])
        self.assertTrue(value["roadmap_wop_binding"])
        self.assertTrue(value["roadmap_emm_binding"])
        self.assertTrue(value["current_wop_not_superseded"])
        self.assertFalse(value["legacy_oa_execution_dependency"])
        self.assertFalse(value["legacy_mission_contract_execution_dependency"])

    def test_execution_interface_uses_model_b(self):
        value = ExecutionInterface(self.root).current_authority()
        self.assertEqual(value["operation"], "OPERATION-BETA")
        self.assertEqual(value["authority_model"], "MODEL_B")

    def test_wop_digest_is_exact(self):
        path = self.root / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), WOP_DIGEST)


if __name__ == "__main__":
    unittest.main()
