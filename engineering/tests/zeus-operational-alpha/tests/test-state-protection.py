import importlib.util
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class ProtectionTests(unittest.TestCase):
    def test_authorized_transition_flag_is_not_a_bypass(self):
        with tempfile.TemporaryDirectory(dir=pmct.REPOSITORY) as temporary:
            with patch.dict(os.environ, {"PMCT_RUNTIME_ROOT": temporary}):
                with self.assertRaisesRegex(pmct.PmctError, "no authorized"):
                    pmct.evidence_run(
                        pmct.matrix()["gates"][18], authorized_transition=True
                    )

    def test_runtime_must_remain_scoped(self):
        with patch.dict(os.environ, {"PMCT_RUNTIME_ROOT": "/tmp"}, clear=False):
            with self.assertRaisesRegex(pmct.PmctError, "scoped"):
                pmct.safe_runtime()

    def test_oa01_adapter_satisfies_current_observable_contract(self):
        state = pmct.inspect_state()
        checks = pmct.evaluate(pmct.matrix()["gates"][0], state)
        mandatory = {item["assertion"]: item["passed"] for item in checks if item["mandatory"]}
        if state["baseline_matches"]:
            if state["oa01_operator_verification_evidence"] == "PRESENT":
                self.assertEqual(
                    {
                        key for key, passed in mandatory.items() if not passed
                    },
                    {
                        "next_action_prioritizes_oa01_verification",
                        "oa01_verification_ready_not_executed",
                    },
                )
                self.assertEqual(
                    state["oa01_operator_verification_readiness"], "PASS"
                )
            else:
                self.assertTrue(all(mandatory.values()))
                self.assertEqual(
                    state["oa01_operator_verification_readiness"], "READY"
                )
        else:
            self.assertFalse(mandatory["published_baseline_current"])
            self.assertEqual(
                state["oa01_operator_verification_readiness"], "NOT_READY"
            )
        expected_evidence = (
            state["oa01_operator_verification_evidence"]
            if state["baseline_matches"] else "MISMATCHED"
        )
        self.assertEqual(
            state["oa01_operator_verification_evidence"], expected_evidence
        )

    def test_oa02_requires_current_binding_oa01_operator_acceptance(self):
        gate = pmct.matrix()["gates"][1]
        state = {"repository_identity_valid": True, "command_availability": {
            command: {"available": True} for command in gate["required_commands"]
        }}
        checks = []
        service = unittest.mock.Mock()
        service.binding.return_value = object()
        service._matching_receipt.return_value = None
        capability = {"gates": {"OA-01": {
            "status": "PASS", "operator_acceptance": "RECORDED"
        }}}
        with patch.object(pmct, "load_state", return_value=capability), patch.object(
            pmct.GateApprovalService, "configured", return_value=service
        ):
            result, reasons = pmct.classify(gate, state, checks)
        self.assertEqual(result, "BLOCKED")
        self.assertIn(
            "prerequisite gate operator acceptance is not recorded: OA-01",
            reasons,
        )

    def test_oa02_current_binding_receipt_overrides_stale_runtime_ledger(self):
        gate = pmct.matrix()["gates"][1]
        state = {"repository_identity_valid": True, "command_availability": {
            command: {"available": True} for command in gate["required_commands"]
        }}
        service = unittest.mock.Mock()
        service.binding.return_value = object()
        service._matching_receipt.return_value = {"decision": "ACCEPT"}
        capability = {"gates": {"OA-01": {
            "status": "PASS", "operator_acceptance": "NOT_RECORDED"
        }}}
        with patch.object(pmct, "load_state", return_value=capability), patch.object(
            pmct.GateApprovalService, "configured", return_value=service
        ):
            result, _ = pmct.classify(gate, state, [])
        self.assertEqual(result, "PASS")

    def test_oa02_adapter_and_decision_inputs_are_deterministic(self):
        gate = pmct.matrix()["gates"][1]
        first = pmct.evaluate(gate, pmct.inspect_state())
        second = pmct.evaluate(gate, pmct.inspect_state())
        normalized = lambda checks: pmct.sha256(pmct.canonical([
            {
                "assertion": item["assertion"],
                "passed": item["passed"],
                "mandatory": item["mandatory"],
                "detail": item["detail"],
            }
            for item in checks
        ]))
        self.assertEqual(normalized(first), normalized(second))
        mandatory = {
            item["assertion"]: item["passed"]
            for item in first if item["mandatory"]
        }
        self.assertTrue(mandatory["positive_path_adapter"])
        self.assertTrue(mandatory["negative_path_adapter"])
        self.assertTrue(mandatory["idempotency_adapter"])

    def test_stale_verification_does_not_block_ready_current_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            wop = Path(temporary)
            record = wop / "operator-verifications/OA-01.verification.json"
            record.parent.mkdir(parents=True)
            record.write_text(json.dumps({
                "gate": "OA-01",
                "qualified_repository_head": "0" * 40,
                "verification_result": "PASS",
            }))
            checksum = hashlib.sha256(record.read_bytes()).hexdigest()
            record.with_suffix(record.suffix + ".sha256").write_text(
                f"{checksum}  {record.name}\n"
            )
            with patch.dict(os.environ, {"ZEUS_GATE_WOP": str(wop)}):
                state = pmct.oa01_verification_state(
                    head="1" * 40, prerequisites_ready=True
                )
        self.assertEqual(
            state, {"readiness": "READY", "evidence": "ABSENT"}
        )

    def test_mismatched_verification_remains_not_ready_without_prerequisites(self):
        with tempfile.TemporaryDirectory() as temporary:
            wop = Path(temporary)
            record = wop / "operator-verifications/OA-01.verification.json"
            record.parent.mkdir(parents=True)
            record.write_text(json.dumps({
                "gate": "OA-01",
                "qualified_repository_head": "0" * 40,
                "verification_result": "PASS",
            }))
            checksum = hashlib.sha256(record.read_bytes()).hexdigest()
            record.with_suffix(record.suffix + ".sha256").write_text(
                f"{checksum}  {record.name}\n"
            )
            with patch.dict(os.environ, {"ZEUS_GATE_WOP": str(wop)}):
                state = pmct.oa01_verification_state(
                    head="1" * 40, prerequisites_ready=False
                )
        self.assertEqual(
            state, {"readiness": "NOT_READY", "evidence": "MISMATCHED"}
        )


if __name__ == "__main__":
    unittest.main()
