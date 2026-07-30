import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
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

    def test_controlled_state_records_current_demonstrated_passes(self):
        state = pmct.load_state()
        self.assertEqual(state["overall_result"], "NOT_READY")
        self.assertEqual(
            state["gates"]["OA-01"]["gate_status"],
            "AWAITING_OPERATOR_VERIFICATION",
        )
        self.assertEqual(
            state["gates"]["OA-01"]["operator_acceptance"], "NOT_RECORDED"
        )
        passed = [
            gate for gate, item in state["gates"].items()
            if item["status"] == "PASS"
        ]
        self.assertEqual(passed, ["OA-01", "OA-02"])

    def test_completed_run_atomically_updates_capability_state(self):
        with tempfile.TemporaryDirectory(dir=pmct.REPOSITORY) as temporary:
            root = Path(temporary)
            state_path = root / "capability-state.yaml"
            state_path.write_bytes(pmct.STATE_PATH.read_bytes())
            runtime = root / "runtime"
            isolated_state = pmct.inspect_state()
            isolated_state.update({
                "published_baseline": isolated_state["head"],
                "baseline_matches": True,
                "dispatcher_active": False,
                "dispatcher_status": "PREPARED",
                "production_agent_count": 0,
                "production_qualified_agent_count": 0,
                "oa01_operator_verification_readiness": "READY",
                "oa01_operator_verification_evidence": "ABSENT",
            })
            isolated_state["next_action_probe"] = {
                **isolated_state["next_action_probe"],
                "zeus_mode": "BETA",
                "operational_dispatch": "DISABLED",
                "next_authorized_action": {
                    "code": "RUN_OA-01_VERIFICATION",
                },
            }
            with (
                patch.object(pmct, "STATE_PATH", state_path),
                patch.object(pmct, "inspect_state", return_value=isolated_state),
                patch.dict(
                    os.environ, {"PMCT_RUNTIME_ROOT": str(runtime)}, clear=False
                ),
            ):
                result, _ = pmct.evidence_run(pmct.matrix()["gates"][0])
                state = pmct.load_state()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(state["last_run_id"], result["run_id"])
        self.assertEqual(state["last_evaluated_gate"], "OA-01")
        self.assertEqual(state["gates"]["OA-01"]["status"], "PASS")
        self.assertEqual(
            state["gates"]["OA-01"]["gate_status"],
            "AWAITING_OPERATOR_VERIFICATION",
        )
        self.assertEqual(state["gates"]["OA-01"]["operator_verification"], "PENDING")
        self.assertEqual(state["gates"]["OA-01"]["operator_acceptance"], "NOT_RECORDED")
        self.assertEqual(state["overall_result"], "NOT_READY")
        self.assertEqual(state["updated_at"][-1], "Z")


if __name__ == "__main__":
    unittest.main()
