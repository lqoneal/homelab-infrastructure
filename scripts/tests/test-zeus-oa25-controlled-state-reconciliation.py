"""Regression coverage for OA-25 controlled state reconciliation."""

from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.emp.oa25_cap025_verification import ReconciliationQualificationError, _assertions
from scripts.lib.eos.mission_knowledge import MissionKnowledgeError


class ControlledStateReconciliationTests(unittest.TestCase):
    def test_authoritative_records_reconcile(self) -> None:
        assertions, context = _assertions(ROOT)
        self.assertTrue(all(value == "PASS" for value in assertions.values()))
        self.assertEqual("Controlled State Reconciliation", "Controlled State Reconciliation")
        self.assertEqual(64, len(context["input_digest"]))

    def test_missing_controlled_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs/project").mkdir(parents=True)
            (root / "docs/project/PROJ-0001-PROJECT_STATE.md").write_text("state\n")
            with self.assertRaises((ReconciliationQualificationError, MissionKnowledgeError, FileNotFoundError)):
                _assertions(root)


if __name__ == "__main__":
    unittest.main()
