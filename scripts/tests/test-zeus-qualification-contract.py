"""Regression tests for the single Zeus qualification decision owner."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.qualification_contract import resolve, view  # noqa: E402


class QualificationContractTests(unittest.TestCase):
    def test_one_fail_closed_decision_and_typed_blockers(self):
        value = resolve(ROOT)
        self.assertEqual(value["qualification_state"], "NOT_QUALIFIED")
        self.assertEqual(value["publication_state"], "PUBLICATION_BLOCKED")
        self.assertEqual([item["blocker_id"] for item in value["remaining_blockers"]], ["QUAL-001", "QUAL-002"])
        required = {"blocker_id", "category", "severity", "originating_controller", "authoritative_evidence", "governing_document", "corrective_wop", "publication_impact", "resolution_requirements"}
        self.assertTrue(all(required <= set(item) for item in value["remaining_blockers"]))

    def test_views_share_digest_and_state(self):
        contract = resolve(ROOT)
        for subject in ("qualification", "publication", "readiness", "blockers", "snapshot", "verify"):
            value = view(ROOT, subject)
            self.assertEqual(value.get("decision_digest") or value["contract"]["decision_digest"], contract["decision_digest"])
        self.assertFalse(view(ROOT, "readiness")["ready"])


if __name__ == "__main__":
    unittest.main()
