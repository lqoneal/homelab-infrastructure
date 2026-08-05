"""Regression tests for the single Zeus qualification decision owner."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.qualification_contract import resolve, view  # noqa: E402
from scripts.lib.emp.blocker_framework import operation, resolve_from_seed  # noqa: E402


class QualificationContractTests(unittest.TestCase):
    def test_one_fail_closed_decision_and_typed_blockers(self):
        value = resolve(ROOT)
        self.assertEqual(value["qualification_state"], "QUALIFIED_FOR_PUBLICATION")
        self.assertEqual(value["publication_state"], "PUBLICATION_PENDING_APPROVAL")
        self.assertEqual(value["remaining_blockers"], [])
        required = {"blocker_id", "category", "severity", "originating_controller", "authoritative_evidence", "governing_document", "corrective_wop", "publication_impact", "resolution_requirements"}
        self.assertTrue(all(required <= set(item) for item in value["remaining_blockers"]))

    def test_views_share_digest_and_state(self):
        contract = resolve(ROOT)
        for subject in ("qualification", "publication", "readiness", "blockers", "snapshot", "verify"):
            value = view(ROOT, subject)
            self.assertEqual(value.get("decision_digest") or value["contract"]["decision_digest"], contract["decision_digest"])
        self.assertTrue(view(ROOT, "readiness")["ready"])

    def test_blocker_lifecycle_is_complete_and_publication_uses_active_only(self):
        contract = resolve(ROOT)
        self.assertEqual(contract["active_blockers"], [])
        self.assertEqual(contract["remaining_blockers"], [])
        self.assertEqual(operation(ROOT, contract["blockers"], "graph")["active_blockers"], [])

    def test_duplicate_blocker_is_merged_deterministically(self):
        contract = resolve(ROOT)
        blocker = {"blocker_id": "TEST-DUPLICATE", "authoritative_evidence": "engineering/evidence/operation-beta/wop-zdcl02-broad-qualification-failure-reconciliation-001/BROAD-QUALIFICATION-RESULTS.md"}
        graph = resolve_from_seed(ROOT, [blocker, blocker])
        self.assertEqual(graph["duplicate_blockers_merged"], ["TEST-DUPLICATE"])
        self.assertEqual(len(graph["blockers"]), 1)


if __name__ == "__main__":
    unittest.main()
