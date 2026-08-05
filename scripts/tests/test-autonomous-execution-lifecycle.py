#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.autonomous_execution_lifecycle import (  # noqa: E402
    AutonomousLifecycleController,
    AutonomousLifecycleError,
    AutonomousLifecycleStore,
)


class AutonomousLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.controller = AutonomousLifecycleController(AutonomousLifecycleStore(self.root))
        self.authoritative = {
            "instance_id": "ZEUS-DEVELOPMENT-TEST-001",
            "mission_id": "MISSION-TEST-001",
            "wop_id": "WOP-TEST-001",
            "execution_mode": "DEVELOPMENT",
            "state": "DISPATCHED",
            "package_digest": "a" * 64,
            "authorization": {"authority": "Engineering Governance"},
            "receipts": {"authorization": {"receipt_id": "AUTH-1"}, "dispatch": {"receipt_id": "DISPATCH-1"}},
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_runtime_is_planned_and_replayed(self):
        first = self.controller.reconcile(self.authoritative, {}, command="status")
        second = self.controller.reconcile(self.authoritative, {}, command="status")
        self.assertEqual(first["desired_state"], "AUTONOMOUS_CORRECTION")
        self.assertEqual(first["corrections"][0]["classification"], "MISSING_EXECUTION_PROJECTION")
        self.assertTrue(second["replay"])
        self.assertEqual(first["reconciliation_receipt_id"], second["reconciliation_receipt_id"])

    def test_publication_requires_explicit_policy_approval(self):
        value = dict(self.authoritative, state="PUBLICATION_READY", receipts={"authorization": {"receipt_id": "AUTH-1"}, "dispatch": {"receipt_id": "DISPATCH-1"}, "independent_verification": {"result": "PASS"}})
        result = self.controller.reconcile(value, {"execution": {"execution_id": value["instance_id"]}}, policy={"publication_approval_required": True})
        self.assertIn("PUBLICATION_APPROVAL_REQUIRED", result["blockers"])

    def test_conflicting_authority_fails_closed(self):
        value = dict(self.authoritative, authorization={"authority": "Untrusted Actor"})
        with self.assertRaises(AutonomousLifecycleError):
            self.controller.reconcile(value)


if __name__ == "__main__":
    unittest.main()
