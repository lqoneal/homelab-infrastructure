#!/usr/bin/env python3
"""Qualification for durable accepted-gate carry-forward."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.lib.emp.gate_carry_forward import (
    GateCarryForwardError,
    assess_changes,
    create_record,
    record_path,
    resolve_record,
)


class Service:
    def __init__(self, receipt: Path, fields: dict[str, str]):
        self.receipt = receipt
        self.fields = fields

    def _valid_receipts(self, gate: str):
        return [(self.receipt, self.fields)] if gate == "OA-01" else []


class GateCarryForwardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.email", "t@invalid"], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.name", "Test"], check=True)
        (self.root / "scripts").mkdir()
        (self.root / "scripts/zeus").write_text("dispatcher_status = 'PREPARED'\n")
        subprocess.run(["git", "-C", self.root, "add", "."], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-qm", "accepted"], check=True)
        self.prior = subprocess.check_output(
            ["git", "-C", self.root, "rev-parse", "HEAD"], text=True
        ).strip()
        (self.root / "scripts/zeus").write_text(
            "dispatcher_status = 'PREPARED'\noperational_dispatch = 'DISABLED'\n"
        )
        subprocess.run(["git", "-C", self.root, "commit", "-qam", "presentation"], check=True)
        self.head = subprocess.check_output(
            ["git", "-C", self.root, "rev-parse", "HEAD"], text=True
        ).strip()
        runtime = self.root / ".zeus/runtime/authority"
        runtime.mkdir(parents=True)
        (runtime / "active-publication.json").write_text(
            json.dumps({"transaction_id": "AUTHORITY-PUBLICATION-successor"})
        )
        self.receipt = self.root / "OA-01.approved"
        self.receipt.write_text("accepted\n")
        self.service = Service(self.receipt, {"approved_head": self.prior})
        self.binding = SimpleNamespace(
            gate="OA-01", qualified_head=self.head, run_id="PMCT-current",
            evidence_digest="a" * 64,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_unaffected_successor_is_carried_forward_and_idempotent(self):
        record, replay = create_record(self.root, self.service, self.binding)
        repeated, replay2 = create_record(self.root, self.service, self.binding)
        self.assertFalse(replay)
        self.assertTrue(replay2)
        self.assertEqual(record["carry_forward_decision"], "CARRY_FORWARD")
        self.assertFalse(record["oa01_revalidation_required"])
        self.assertEqual(record["affected_gate_analysis"], [])
        self.assertEqual(resolve_record(self.root, self.binding), repeated)

    def test_material_change_requires_revalidation(self):
        protected = self.root / "scripts/lib/emp"
        protected.mkdir(parents=True)
        (protected / "gate_approval.py").write_text("changed\n")
        subprocess.run(["git", "-C", self.root, "add", "."], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-qm", "protected"], check=True)
        assessment = assess_changes(
            self.root, self.prior,
            subprocess.check_output(
                ["git", "-C", self.root, "rev-parse", "HEAD"], text=True
            ).strip(),
        )
        self.assertEqual(assessment["assessment_result"], "AFFECTED")
        self.assertIn("OA01_OPERATOR_EVIDENCE", assessment["affected_oa01_criteria"])

    def test_tampering_invalidates_record(self):
        create_record(self.root, self.service, self.binding)
        path = record_path(self.root)
        value = json.loads(path.read_text())
        value["carry_forward_decision"] = "CARRY_FORWARD-TAMPERED"
        path.write_text(json.dumps(value))
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        )
        self.assertIsNone(resolve_record(self.root, self.binding))

    def test_non_ancestor_is_rejected(self):
        with self.assertRaises(GateCarryForwardError):
            assess_changes(self.root, "f" * 40, self.head)


if __name__ == "__main__":
    unittest.main()
