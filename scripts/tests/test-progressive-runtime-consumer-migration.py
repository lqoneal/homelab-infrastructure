#!/usr/bin/env python3
"""T04 qualification for Progressive Runtime Layer consumer migration."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts/zeus"


class ProgressiveRuntimeConsumerMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ZEUS.read_text()
        cls.tree = ast.parse(cls.source)

    def test_cli_consumes_canonical_service(self):
        self.assertIn(
            "from scripts.lib.emp.progressive_gate import "
            "ProgressiveGateError, ProgressiveGateService",
            self.source,
        )
        calls = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"verify", "approve", "decline"}
        ]
        self.assertTrue(any(node.func.attr == "verify" for node in calls))
        self.assertTrue(any(node.func.attr == "approve" for node in calls))
        self.assertTrue(any(node.func.attr == "decline" for node in calls))

    def test_cli_has_no_direct_progressive_decision_call(self):
        self.assertNotIn("progressive_oa.decide(", self.source)

    def test_cli_has_no_gate_specific_verification_dispatch(self):
        for name in (
            "verify_oa01_gate",
            "verify_oa02_gate",
            "verify_oa03_gate",
            "verify_oa04_gate",
            "verify_oa05_gate",
        ):
            self.assertNotIn(name, self.source)

    def test_legacy_owners_remain_present(self):
        for relative in (
            "scripts/lib/emp/gate_approval.py",
            "scripts/lib/emp/gate_carry_forward.py",
            "scripts/lib/emp/oa02_lifecycle.py",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
