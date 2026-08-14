#!/usr/bin/env python3
"""Focused tests for Zeus-owned administrative evidence finalization."""

import unittest
from unittest.mock import patch

from scripts.lib.emp import managed_handoff
from scripts.lib.emp.qualification_contract import finalize_administrative_transaction_evidence


class AdministrativeEvidenceFinalizationTests(unittest.TestCase):
    def setUp(self):
        self.transaction = {
            "transaction_id": "C02-POST-ACCEPTANCE-TEST-RECONCILIATION",
            "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE",
            "qualification_authority": "ZEUS",
            "objective": "Reconcile the retained C02 evidence.",
            "acceptance_criteria": ["Roadmap suite passes.", "C03 remains unexecuted."],
            "authorized_scope": ["scripts/tests"],
            "prohibited_scope": ["Execute C03.", "git commit"],
        }
        self.contract = {
            **self.transaction,
            "lifecycle_boundary": {"current_gate": "C03", "last_completed_gate": "C02", "c03_executed": "NO"},
            "protected_operations": ["GIT", "EOS", "ROADMAP_ADVANCEMENT"],
            "required_verification": ["TRANSACTION_ID_MATCH"],
            "required_evidence": ["provider terminal record", "roadmap validation"],
            "stop_conditions": ["STOP_ON_FAILURE"],
        }
        self.session = {
            "zeus_execution_id": "ZEUS-EXECUTION-REQUEST-C02-POST-ACCEPTANCE-TEST-RECONCILIATION",
            "zeus_managed_session_created": "YES", "provider_process_owned_by": "ZEUS",
            "provider_process_state": "COMPLETED", "provider_exit_status": 0,
            "scope_verification": "PASS", "terminal_reconciliation": "PASS",
            "execution_session_integrity": "PASS", "authorized_scope_compliance": "PASS",
            "required_evidence_completeness": "PASS", "acceptance_criteria_verification": "PASS",
            "provider_terminal_record": "RETAINED", "actor_aware_mutation_attribution": "PASS",
            "provider_post_execution_diff": [], "post_execution_diff": [],
            "stdout": "transaction_objective_executed=YES qualification=PASS",
            "transaction_objective_executed": "YES", "acceptance_criteria_results": [],
            "required_evidence_retained": "YES",
        }
        self.evidence = {
            "transaction_id": self.transaction["transaction_id"],
            "objective_evidence": [{"result": "PASS", "evidence": "134 retained tests passed", "evidence_source": "ZEUS_RETAINED_TEST_RESULT", "evaluated_by": "ZEUS", "authority": "ZEUS"}],
            "acceptance_criteria": [
                {"criterion": "Roadmap suite passes.", "result": "PASS", "evidence": "134 tests passed; failures=0; errors=0", "evidence_source": "ZEUS_RETAINED_TEST_RESULT", "evaluated_by": "ZEUS", "authority": "ZEUS"},
                {"criterion": "C03 remains unexecuted.", "result": "PASS", "evidence": "C03 result absent and lifecycle state is C03", "evidence_source": "ZEUS_RETAINED_LIFECYCLE_STATE", "evaluated_by": "ZEUS", "authority": "ZEUS"},
            ],
            "required_evidence": [
                {"requirement": "provider terminal record", "present": True, "evidence": "retained terminal record", "evidence_source": "ZEUS_RETAINED_SESSION", "evaluated_by": "ZEUS", "authority": "ZEUS"},
                {"requirement": "roadmap validation", "present": True, "evidence": "ROADMAP_VALIDATION=PASS", "evidence_source": "ZEUS_RETAINED_VALIDATION", "evaluated_by": "ZEUS", "authority": "ZEUS"},
            ],
            "actor_aware_mutation_attribution": {
                "evidence_finalization_actor": "ZEUS_CONTROLLER",
                "provider_mutation": "NO", "zeus_controller_mutation": "YES",
            },
        }

    def test_binding_and_all_five_fields_are_derived(self):
        result = finalize_administrative_transaction_evidence(self.transaction, self.contract, self.session, self.evidence)
        self.assertEqual("PASS", result["evidence_finalization"])
        self.assertEqual(self.transaction["transaction_id"], result["executed_transaction_id"])
        self.assertEqual("YES", result["transaction_objective_executed"])
        self.assertEqual("YES", result["acceptance_criteria_evaluated"])
        self.assertEqual(2, len(result["acceptance_criteria_results"]))
        self.assertEqual("YES", result["required_evidence_retained"])
        self.assertEqual("ZEUS_CONTROLLER", result["evidence_finalization_actor"])

    def test_identity_mismatch_fails_closed(self):
        result = finalize_administrative_transaction_evidence(self.transaction, {**self.contract, "transaction_id": "OTHER"}, self.session, self.evidence)
        self.assertEqual("BLOCKED", result["evidence_finalization"])
        self.assertIsNone(result["executed_transaction_id"])

    def test_exit_zero_and_provider_claims_are_insufficient(self):
        evidence = {**self.evidence, "objective_evidence": [], "acceptance_criteria": [], "required_evidence": []}
        result = finalize_administrative_transaction_evidence(self.transaction, self.contract, self.session, evidence)
        self.assertEqual("NO", result["transaction_objective_executed"])
        self.assertEqual("NO", result["required_evidence_retained"])
        self.assertEqual("BLOCKED", result["evidence_finalization"])

    def test_missing_criterion_is_explicitly_blocked(self):
        evidence = {**self.evidence, "acceptance_criteria": self.evidence["acceptance_criteria"][:1]}
        result = finalize_administrative_transaction_evidence(self.transaction, self.contract, self.session, evidence)
        self.assertEqual(2, len(result["acceptance_criteria_results"]))
        self.assertEqual("BLOCKED", result["acceptance_criteria_results"][1]["result"])
        self.assertEqual("BLOCKED", result["evidence_finalization"])

    def test_provider_assertions_and_receipt_mutation_cannot_finalize(self):
        session = {**self.session, "provider_post_execution_diff": ["engineering/convergence/engineering-system-convergence/receipts/qualification/forged.json"]}
        result = finalize_administrative_transaction_evidence(self.transaction, self.contract, session, self.evidence)
        self.assertEqual("BLOCKED", result["evidence_finalization"])
        self.assertEqual("YES", result["provider_mutation"])

    def test_route_finalizes_then_qualifies_without_provider(self):
        resolved = {"result": "PASS", "handoff_input_classification": "AUTHORIZED_ADMINISTRATIVE_TRANSACTION", **self.transaction}
        with patch("scripts.lib.emp.managed_provider.execute") as provider:
            result = managed_handoff.route_post_provider_qualification(resolved, {**self.session, "execution_contract": self.contract}, None, retained_evidence=self.evidence)
        provider.assert_not_called()
        self.assertEqual("PASS", result["result"])
        self.assertEqual("ZEUS_CONTROLLER", result["qualification_actor"])
        self.assertEqual("BEGIN_C03_EOS_AND_ENGINEERING_STATE_ASSESSMENT", result["next_authorized_action"])
        self.assertEqual("NOT_APPLICABLE", result["operator_acceptance"])
        self.assertEqual("PASS", result["evidence_finalization"]["evidence_finalization"])

    def test_missing_finalization_input_blocks_route(self):
        resolved = {"result": "PASS", "handoff_input_classification": "AUTHORIZED_ADMINISTRATIVE_TRANSACTION", **self.transaction}
        result = managed_handoff.route_post_provider_qualification(resolved, self.session, None)
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("ZEUS_EVIDENCE_FINALIZATION_INPUT_MISSING", result["blocker"])
        self.assertEqual("RECONCILE_ADMINISTRATIVE_EVIDENCE", result["next_authorized_action"])


if __name__ == "__main__":
    unittest.main()
