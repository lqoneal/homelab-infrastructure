#!/usr/bin/env python3
"""Regression tests for the Progressive OA successive-gate controller."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.emp import progressive_oa


class ProgressiveOATest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = self.root / progressive_oa.PACKAGE_PATH
        self.package.mkdir(parents=True)
        gates = []
        for number in range(1, 31):
            gates.append({
                "gate_id": f"OA-{number:02d}",
                "title": f"Gate {number}",
                "mission_objective": f"Objective {number}",
                "capability_being_established": f"Capability {number}",
                "authoritative_source_references": ["source"],
                "rationale": "required",
                "exact_success_criteria": ["PASS"],
                "required_evidence": ["evidence"],
            })
        (self.package / "gate-specification.yaml").write_text(
            yaml.safe_dump({"gates": gates})
        )

    def tearDown(self):
        os.environ.pop("ZEUS_PROGRESSIVE_OA_STATE", None)
        self.temporary.cleanup()

    def test_controller_selects_only_first_gate_and_replays(self):
        first = progressive_oa.controller(self.root)
        second = progressive_oa.controller(self.root)
        self.assertEqual(first["active_gate"], "OA-01")
        self.assertEqual(first, second)
        state = progressive_oa.load_state(self.root)
        self.assertEqual(state["gates"]["OA-01"]["state"], "IMPLEMENTATION_REQUIRED")
        self.assertEqual(state["gates"]["OA-02"]["state"], "PENDING")

    def test_acceptance_enables_immediate_successor_exactly_once(self):
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-01"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
        progressive_oa._write_state(self.root, state)
        evidence = self.package / "runtime/evidence/OA-01"
        evidence.mkdir(parents=True)
        (evidence / "VERIFIED").write_text("verified\n")
        first, replay1 = progressive_oa.decide(
            self.root, "OA-01", "ACCEPTED", "operator", "2026-07-29T05:00:00Z"
        )
        self.assertFalse(replay1)
        self.assertEqual(progressive_oa.load_state(self.root)["active_gate"], "OA-02")
        verified = progressive_oa.verify_receipt(self.root, "OA-01")
        self.assertEqual(verified["integrity"], "PASS")
        second, replay2 = progressive_oa.decide(
            self.root, "OA-01", "ACCEPTED", "operator", "2026-07-29T05:00:00Z"
        )
        self.assertTrue(replay2)
        self.assertEqual(first, second)

    def test_rejection_stops_fail_closed(self):
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-01"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
        progressive_oa._write_state(self.root, state)
        evidence = self.package / "runtime/evidence/OA-01"
        evidence.mkdir(parents=True)
        (evidence / "VERIFIED").write_text("verified\n")
        progressive_oa.decide(
            self.root, "OA-01", "REJECTED", "operator", "2026-07-29T05:00:00Z"
        )
        state = progressive_oa.load_state(self.root)
        self.assertEqual(state["status"], "STOPPED_FAIL_CLOSED")
        self.assertEqual(state["active_gate"], "OA-01")
        self.assertEqual(state["gates"]["OA-02"]["state"], "PENDING")


if __name__ == "__main__":
    unittest.main()
