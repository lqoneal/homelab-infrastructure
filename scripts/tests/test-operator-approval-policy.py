#!/usr/bin/env python3
"""Policy-driven approval boundary and automatic qualification tests."""
from pathlib import Path
import tempfile
import unittest
import yaml

from scripts.lib.emp.operator_approval_policy import resolve_operator_approval, OperatorApprovalPolicyError
from scripts.lib.emp.qualification_contract import qualify_administrative_transaction


class OperatorApprovalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.transaction = {"transaction_id": "ADMIN-1", "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE", "transaction_state": "REQUIRED", "objective": "Run the authorized administrative test.", "authorized_scope": ["scripts/tests"], "prohibited_scope": ["C03"], "acceptance_criteria": ["The authorized test passes."]}
        self.session = {"zeus_managed_session_created": "YES", "provider_process_owned_by": "ZEUS", "provider_process_state": "COMPLETED", "provider_exit_status": 0, "scope_verification": "PASS", "terminal_reconciliation": "PASS", "execution_session_integrity": "PASS", "authorized_scope_compliance": "PASS", "required_evidence_completeness": "PASS", "acceptance_criteria_verification": "PASS", "provider_terminal_record": "RETAINED", "actor_aware_mutation_attribution": "PASS", "out_of_scope_changes": [], "protected_actions_performed": [], "execution_contract": {"transaction_id": "ADMIN-1", "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE", "objective": "Run the authorized administrative test.", "authorized_scope": ["scripts/tests"], "prohibited_scope": ["C03"], "acceptance_criteria": ["The authorized test passes."], "lifecycle_boundary": {"current_gate": "C03"}, "protected_operations": ["GIT"], "required_verification": ["ACCEPTANCE_CRITERIA_EVALUATED"], "required_evidence": ["The authorized test passes."], "stop_conditions": ["STOP_ON_FAILURE"]}, "executed_transaction_id": "ADMIN-1", "transaction_objective_executed": "YES", "acceptance_criteria_evaluated": "YES", "acceptance_criteria_results": [{"criterion": "The authorized test passes.", "result": "PASS"}], "required_evidence_retained": "YES"}

    def policy(self, requirements):
        handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        yaml.safe_dump({"schema_version": 1, "policy_id": "TEST-POLICY", "requirements": requirements}, handle)
        handle.close()
        return handle.name

    def requirement(self, active=True):
        return {"requirement_id": "TEST-REQUIREMENT-1", "lifecycle_situation": "test", "applicability": {"all": [{"field": "transaction_type", "equals": "BOUNDED_ADMINISTRATIVE_CORRECTIVE"}]}, "required_operator_action": "OPERATOR_REVIEW_TEST", "authority_source": "TEST-AUTHORITY", "active": active, "rationale": "test reason", "resulting_transition": {"approval": "QUALIFICATION_ELIGIBLE", "rejection": "CORRECTIVE_RECONCILIATION_REQUIRED"}}

    def test_no_match_qualifies_and_provider_completion_is_not_qualification(self):
        result = qualify_administrative_transaction(self.transaction, self.session, None)
        self.assertEqual("PASS", result["result"])
        self.assertFalse(result["provider_completion_is_qualification"])

    def test_active_policy_stops_with_requirement_identity(self):
        result = qualify_administrative_transaction(self.transaction, self.session, None, policy_path=self.policy([self.requirement()]))
        self.assertEqual("TEST-REQUIREMENT-1", result["approval_requirement_id"])
        self.assertEqual("OPERATOR_REVIEW_TEST", result["next_authorized_action"])
        self.assertEqual("TEST-AUTHORITY", result["approval_authority_source"])
        self.assertEqual("QUALIFICATION_ELIGIBLE", result["approval_resulting_transition"]["approval"])

    def test_policy_deactivation_and_addition_change_behavior_without_code_change(self):
        inactive = qualify_administrative_transaction(self.transaction, self.session, None, policy_path=self.policy([self.requirement(False)]))
        self.assertEqual("PASS", inactive["result"])
        active = qualify_administrative_transaction(self.transaction, self.session, None, policy_path=self.policy([self.requirement(True)]))
        self.assertEqual("REQUIRED", active["qualification"])

    def test_malformed_and_ambiguous_policy_fail_closed(self):
        malformed = self.requirement(); malformed.pop("rationale")
        result = qualify_administrative_transaction(self.transaction, self.session, None, policy_path=self.policy([malformed]))
        self.assertEqual("OPERATOR_APPROVAL_POLICY_INVALID", result["blocker"])
        ambiguous = self.requirement(); second = dict(ambiguous, requirement_id="TEST-REQUIREMENT-2")
        result = qualify_administrative_transaction(self.transaction, self.session, None, policy_path=self.policy([ambiguous, second]))
        self.assertEqual("OPERATOR_APPROVAL_POLICY_INVALID", result["blocker"])


if __name__ == "__main__":
    unittest.main()
