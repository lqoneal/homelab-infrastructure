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

    def test_blocker_lifecycle_is_complete_and_publication_uses_active_only(self):
        contract = resolve(ROOT)
        for blocker in contract["active_blockers"]:
            self.assertEqual(blocker["lifecycle_state"], "ACTIVE")
            self.assertTrue(blocker["publication_blocking"])
            self.assertTrue(blocker["verification_digest"])
            self.assertTrue(blocker["owning_component"])
            self.assertTrue(blocker["owning_transaction"])
            self.assertTrue(blocker["owning_mission"])
            self.assertTrue(blocker["owning_execution"])
            self.assertTrue(blocker["owning_authority"])
        self.assertEqual(
            [item["blocker_id"] for item in contract["active_blockers"]],
            [item["blocker_id"] for item in contract["remaining_blockers"]],
        )
        self.assertEqual(operation(ROOT, contract["blockers"], "verify", "QUAL-001")["result"], "PASS")
        self.assertEqual(operation(ROOT, contract["blockers"], "resolve", "QUAL-001")["result"], "UNRESOLVED")

    def test_duplicate_blocker_is_merged_deterministically(self):
        contract = resolve(ROOT)
        graph = resolve_from_seed(ROOT, [contract["blockers"][0], contract["blockers"][0]])
        self.assertEqual(graph["duplicate_blockers_merged"], [contract["blockers"][0]["blocker_id"]])
        self.assertEqual(len(graph["blockers"]), 1)


if __name__ == "__main__":
    unittest.main()
