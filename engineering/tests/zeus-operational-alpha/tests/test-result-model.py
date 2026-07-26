import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class ResultTests(unittest.TestCase):
    def test_result_vocabulary_is_closed(self):
        self.assertEqual(
            pmct.CONTROLLED_RESULTS,
            {"PASS", "FAIL", "BLOCKED", "NOT_READY",
             "EXPECTED_NOT_YET_IMPLEMENTED", "NOT_APPLICABLE"},
        )

    def test_failed_mandatory_assertion_cannot_pass(self):
        gate = pmct.matrix()["gates"][0]
        state = pmct.inspect_state()
        result, _ = pmct.classify(
            gate, state, [pmct.assertion("mandatory", False, "failed")]
        )
        self.assertNotEqual(result, "PASS")

    def test_initial_state_has_no_pass(self):
        state = pmct.load_state()
        self.assertEqual(state["overall_result"], "NOT_READY")
        self.assertFalse(any(item["status"] == "PASS" for item in state["gates"].values()))


if __name__ == "__main__":
    unittest.main()
