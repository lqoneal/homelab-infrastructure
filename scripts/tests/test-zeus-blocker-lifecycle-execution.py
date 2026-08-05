import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.blocker_lifecycle import BlockerLifecycleError, execute, execute_blocker, transition  # noqa: E402
from scripts.lib.emp.qualification_contract import resolve  # noqa: E402


class BlockerLifecycleExecutionTests(unittest.TestCase):
    def setUp(self):
        self.blockers = [{
            "blocker_id": "TEST-QUALIFICATION",
            "lifecycle_state": "ACTIVE",
            "blocker_digest": "test-blocker-digest",
            "auto_resolvable": False,
            "operator_action_required": True,
        }]

    def test_operator_blocker_is_revalidated_without_fabricated_retirement(self):
        result = execute_blocker(self.blockers[0])
        self.assertEqual(result["result"], "OPERATOR_ACTION_REQUIRED")
        self.assertEqual(result["blocker"]["lifecycle_state"], "ACTIVE")
        self.assertEqual([item["to"] for item in result["transitions"]], ["RESOLVING", "REVALIDATING", "ACTIVE"])
        self.assertTrue(all(item["verified"] for item in result["transitions"]))

    def test_auto_resolvable_blocker_reaches_retired_only_after_corrective(self):
        blocker = {**self.blockers[0], "auto_resolvable": True, "operator_action_required": False}
        result = execute_blocker(blocker, corrective=lambda _: True)
        self.assertEqual(result["result"], "RETIRED")
        self.assertEqual(result["blocker"]["lifecycle_state"], "RETIRED")
        self.assertEqual([item["to"] for item in result["transitions"]], ["RESOLVING", "REVALIDATING", "RESOLVED", "RETIRED"])

    def test_invalid_skip_is_rejected(self):
        with self.assertRaises(BlockerLifecycleError):
            transition(self.blockers[0], "RETIRED")

    def test_execute_is_deterministic_and_recomputes(self):
        first = execute(self.blockers)
        second = execute(self.blockers)
        self.assertEqual(first, second)
        self.assertTrue(first["reevaluated"])
        self.assertTrue(first["decision_recomputed"])
        self.assertEqual(first["active_blockers"], ["TEST-QUALIFICATION"])


if __name__ == "__main__":
    unittest.main()
