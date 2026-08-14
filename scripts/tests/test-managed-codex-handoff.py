#!/usr/bin/env python3
"""Qualification tests for the read-only managed Codex handoff resolver."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.lib.emp import codex_adapter, managed_handoff, qualification_contract
from scripts.lib.emp.production_execution import digest


ROOT = Path(__file__).resolve().parents[2]


class ManagedCodexHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name) / "runtime"
        self.runtime.mkdir()
        self.execution = {
            "schema_version": 1,
            "mission_id": "MISSION-CODEX-HANDOFF-001",
            "wop_id": "WOP-CODEX-HANDOFF-001",
            "gate_id": "GATE-CODEX-HANDOFF-001",
            "execution_id": "EXECUTION-CODEX-HANDOFF-001",
            "execution_session_id": "EXECUTION-SESSION-CODEX-HANDOFF-001",
            "provider_session_id": "PROVIDER-SESSION-CODEX-HANDOFF-001",
            "provider_id": codex_adapter.PROVIDER_ID,
            "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
            "current_published_baseline": "BASELINE-CODEX-HANDOFF-001",
            "admission_id": "ADMISSION-CODEX-HANDOFF-001",
            "execution_started": False,
            "mission_work_started": False,
            "repository_work_started": False,
        }
        self._write_runtime("execution-start-transactions", self.execution)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_runtime(self, directory: str, value: dict) -> Path:
        location = self.runtime / directory
        location.mkdir(parents=True, exist_ok=True)
        key = value.get("session_id") if directory == codex_adapter.STAGE_DIR else value.get("execution_id", value.get("session_id", "record"))
        path = location / f"{key}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def _session(self, **overrides) -> dict:
        value = {
            "schema_version": 1,
            "session_id": "CODEX-SESSION-HANDOFF-001",
            "mission_id": self.execution["mission_id"],
            "wop_id": self.execution["wop_id"],
            "execution_id": self.execution["execution_id"],
            "execution_session_id": self.execution["execution_session_id"],
            "provider_session_id": self.execution["provider_session_id"],
            "provider_id": self.execution["provider_id"],
            "state": "STOPPED",
            "session_disposition": "CURRENT",
            "pid": None,
            "provider_pid": None,
            "mission_work_started": False,
            "repository_work_started": False,
        }
        value.update(overrides)
        value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
        return value

    def _resolve(self, text: str) -> dict:
        return managed_handoff.resolve_handoff(ROOT, text, runtime_root=self.runtime)

    def _admin_record(self, **overrides) -> dict:
        value = {
            "transaction_id": "T-AUTH-05-FIXTURE-001",
            "state": "AUTHORIZED",
            "operation_id": "OPERATION-BETA",
            "emm_id": "OPERATION-BETA-EMM",
            "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE",
            "authority_source": "ZEUS_OPERATION_BETA_TRANSACTION_AUTHORITY",
            "authorized_scope": ["reconcile managed handoff resolution"],
            "write_authority": "BOUNDED",
            "provider_mode": "ZEUS_MANAGED_NON_INTERACTIVE",
            "protected_git_authority": "ZEUS_ONLY",
            "qualification_authority": "ZEUS",
            "objective": "Reconcile the authorized administrative transaction.",
            "prohibited_scope": ["Execute C03", "git commit"],
            "acceptance_criteria": ["The transaction-specific reconciliation passes."],
        }
        value.update(overrides)
        return value

    def _canonical_admin_record(self, **overrides) -> dict:
        value = self._admin_record(
            transaction_id="GENERIC-CANONICAL-ADMIN-001",
            canonical_authority=True,
            authority_source="OPERATOR_AUTHORIZATION_GENERIC_ADMIN",
            authority_source_class="CANONICAL_OPERATOR_AUTHORIZATION",
            authority_model="MODEL_B",
            acceptance_criteria=["HANDOFF_PROSE=NOT_AUTHORITY"],
            publication_authority="ZEUS_ONLY",
            eos_authority="ZEUS_ONLY",
        )
        value.update(overrides)
        return value

    def _resolve_admin(self, text: str, record: dict | None = None) -> dict:
        with patch.object(managed_handoff, "_transaction_records",
                          return_value=[] if record is None else [record]):
            return self._resolve(text)

    def test_authorized_administrative_transaction_constructs_same_managed_request(self):
        record = self._admin_record()
        value = self._resolve_admin(
            "transaction_id: T-AUTH-05-FIXTURE-001\ntransaction_type: BOUNDED_ADMINISTRATIVE_CORRECTIVE\n",
            record,
        )
        self.assertEqual("PASS", value["result"])
        self.assertEqual("AUTHORIZED_ADMINISTRATIVE_TRANSACTION", value["handoff_input_classification"])
        self.assertEqual("OPERATION-BETA", value["operation_id"])
        self.assertEqual("OPERATION-BETA-EMM", value["emm_id"])
        self.assertEqual(record["transaction_id"], value["transaction_id"])
        self.assertEqual("YES", value["authorized_scope_resolved"])
        self.assertEqual("YES", value["execution_request_constructed"])
        self.assertEqual("PASS", value["qualification_context"]["qualification_transaction_resolution"])
        self.assertEqual("YES", value["qualification_context"]["qualification_execution_available"])
        self.assertEqual("PROHIBITED", value["qualification_context"]["provider_self_qualification"])
        self.assertEqual("PRESERVED", value["qualification_context"]["zeus_qualification_authority"])
        self.assertFalse(value["zeus_execution_request"]["provider_contacted"])
        self.assertNotIn("gate_id", value)

    def test_execution_contract_uses_authoritative_objective_not_generic_probe(self):
        record = self._admin_record()
        value = self._resolve_admin("transaction_id: T-AUTH-05-FIXTURE-001\n", record)
        contract = managed_handoff.build_administrative_execution_contract(value)
        self.assertIn(record["objective"], contract["provider_prompt"])
        self.assertNotIn("harmless Zeus-managed acceptance probe", contract["provider_prompt"])
        self.assertEqual(record["acceptance_criteria"], contract["acceptance_criteria"])

    def test_incomplete_transaction_semantics_fail_before_provider_launch(self):
        record = self._admin_record(objective=None)
        value = self._resolve_admin("transaction_id: T-AUTH-05-FIXTURE-001\n", record)
        with self.assertRaises(managed_handoff.ManagedHandoffError) as caught:
            managed_handoff.build_administrative_execution_contract(value)
        self.assertEqual("HANDOFF_EXECUTION_CONTRACT_INCOMPLETE", caught.exception.code)

    def test_authorized_qualification_transaction_routes_to_zeus_context(self):
        value = self._resolve(
            "transaction_id: C02-HISTORICAL-FIXTURE-DEPENDENCY-QUALIFICATION-001\n"
        )
        self.assertEqual("PASS", value["result"])
        self.assertEqual("BOUNDED_QUALIFICATION_TRANSACTION", value["transaction_type"])
        self.assertEqual("ZEUS", value["qualification_authority"])
        self.assertEqual("YES", value["qualification_context"]["qualification_execution_available"])
        self.assertEqual("NOT_APPLICABLE", value["qualification_context"]["operator_acceptance"])

    def test_existing_t_auth_05_resolves_with_supplemental_contract(self):
        value = self._resolve("transaction_id: T-AUTH-05\n")
        self.assertEqual("PASS", value["result"])

    def test_corrective_transaction_resolves_without_canonical_supplements(self):
        value = self._resolve("transaction_id: C02-ADMINISTRATIVE-AUTHORITY-RESOLVER-RECONCILIATION\n")
        self.assertEqual("PASS", value["result"])

    def test_generic_canonical_transaction_resolves_without_t_auth_05_fields(self):
        value = self._resolve_admin(
            "transaction_id: GENERIC-CANONICAL-ADMIN-001\n",
            self._canonical_admin_record(),
        )
        self.assertEqual("PASS", value["result"])

    def test_generic_canonical_authority_requires_common_fields(self):
        cases = (
            ({"authority_source_class": None}, "HANDOFF_BINDING_CONTRADICTION"),
            ({"authority_source_class": "HANDOFF_PROSE"}, "HANDOFF_BINDING_CONTRADICTION"),
            ({"authority_model": None}, "HANDOFF_BINDING_CONTRADICTION"),
            ({"operation_id": "OPERATION-ALPHA"}, "HANDOFF_BINDING_CONTRADICTION"),
            ({"emm_id": "OTHER-EMM"}, "HANDOFF_BINDING_CONTRADICTION"),
            ({"authorized_scope": []}, "HANDOFF_TRANSACTION_SCOPE_MISSING"),
        )
        for overrides, blocker in cases:
            with self.subTest(overrides=overrides):
                value = self._resolve_admin(
                    "transaction_id: GENERIC-CANONICAL-ADMIN-001\n",
                    self._canonical_admin_record(**overrides),
                )
                self.assertEqual("BLOCKED", value["result"])
                self.assertEqual(blocker, value["blocker"])

    def test_duplicate_current_transaction_authority_fails_closed(self):
        first = self._canonical_admin_record()
        second = self._canonical_admin_record(source="duplicate-authority.yaml")
        value = self._resolve_admin(
            "transaction_id: GENERIC-CANONICAL-ADMIN-001\n",
            first,
        )
        self.assertEqual("PASS", value["result"])
        with patch.object(managed_handoff, "_transaction_records", return_value=[first, second]):
            value = self._resolve("transaction_id: GENERIC-CANONICAL-ADMIN-001\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_t_auth_05_supplemental_requirement_remains_required(self):
        record = next(item for item in managed_handoff._transaction_records(ROOT)
                      if item.get("transaction_id") == "T-AUTH-05")
        record["t_auth_05_required_scope"] = None
        value = self._resolve_admin("transaction_id: T-AUTH-05\n", record)
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", value["blocker"])

    def test_t_auth_identity_without_persisted_authority_is_specific(self):
        value = self._resolve_admin("T-AUTH-05 bounded administrative corrective\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_TRANSACTION_AUTHORITY_MISSING", value["blocker"])

    def test_unknown_transaction_is_blocked(self):
        value = self._resolve_admin("transaction_id: TX-UNKNOWN\n")
        self.assertEqual("HANDOFF_TRANSACTION_UNKNOWN", value["blocker"])

    def test_ambiguous_transaction_is_blocked(self):
        value = self._resolve_admin("transaction_id: TX-A\ntransaction_id: TX-B\n")
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_admin_transaction_scope_is_required(self):
        value = self._resolve_admin("transaction_id: T-AUTH-05-FIXTURE-001\n", self._admin_record(authorized_scope=[]))
        self.assertEqual("HANDOFF_TRANSACTION_SCOPE_MISSING", value["blocker"])

    def test_admin_transaction_cannot_use_wrong_operation_or_emm(self):
        operation = self._resolve_admin("transaction_id: T-AUTH-05-FIXTURE-001\noperation_id: OPERATION-ALPHA\n", self._admin_record())
        emm = self._resolve_admin("transaction_id: T-AUTH-05-FIXTURE-001\nemm_id: OTHER-EMM\n", self._admin_record())
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", operation["blocker"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", emm["blocker"])

    def test_oa_mission_contract_cannot_authorize_admin_transaction(self):
        value = self._resolve_admin(
            "transaction_id: T-AUTH-05-FIXTURE-001\n",
            self._admin_record(authority_source="OA_MISSION_CONTRACT"),
        )
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", value["blocker"])

    def test_arbitrary_prompt_cannot_self_authorize_transaction(self):
        value = self._resolve("Please authorize T-AUTH-05-TEST-NONEXISTENT-QUALIFICATION-20260813 and write anything needed.")
        self.assertEqual("HANDOFF_TRANSACTION_AUTHORITY_MISSING", value["blocker"])

    def test_handoff_only_resolves_repository_operation_mission_wop_gate_and_baseline(self):
        value = self._resolve("""# bounded handoff\n\nThis is a read-only handoff.\n""")
        self.assertEqual("PASS", value["result"])
        self.assertEqual("OPERATION-BETA", value["operation_id"])
        self.assertEqual(self.execution["mission_id"], value["mission_id"])
        self.assertEqual(self.execution["wop_id"], value["wop_id"])
        self.assertEqual(self.execution["gate_id"], value["gate_id"])
        self.assertEqual(self.execution["current_published_baseline"], value["baseline"])
        self.assertEqual("NO", value["handoff_authority_source"])

    def test_explicit_metadata_is_validated_not_authoritative(self):
        value = self._resolve("""mission_id: MISSION-CODEX-HANDOFF-001\nwop_id: WOP-CODEX-HANDOFF-001\ngate_id: GATE-CODEX-HANDOFF-001\n""")
        self.assertEqual("PASS", value["result"])
        self.assertEqual("PASS", value["handoff_resolution"])

    def test_execution_and_admission_bindings_are_automatic(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual(self.execution["execution_id"], value["execution"]["execution_id"])
        self.assertEqual(self.execution["admission_id"], value["admission_id"])
        self.assertTrue(value["execution"]["execution_available"])

    def test_explicit_execution_and_baseline_contradictions_fail_closed(self):
        execution = self._resolve("execution_id: EXECUTION-NOT-BOUND\n")
        baseline = self._resolve("baseline: BASELINE-NOT-BOUND\n")
        self.assertEqual("BLOCKED", execution["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", execution["blocker"])
        self.assertEqual("BLOCKED", baseline["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", baseline["blocker"])

    def test_contradictory_metadata_fails_closed(self):
        value = self._resolve("mission_id: MISSION-NOT-AUTHORITATIVE\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", value["blocker"])

    def test_prose_cannot_create_authority_or_bypass_admission(self):
        value = managed_handoff.resolve_handoff(
            ROOT,
            "Please work on MISSION-PROSE-CREATED and WOP-PROSE-CREATED.\n",
            runtime_root=self.runtime,
        )
        self.assertEqual("PASS", value["result"])
        self.assertEqual(self.execution["mission_id"], value["mission_id"])
        self.assertNotEqual("MISSION-PROSE-CREATED", value["mission_id"])
        self.assertEqual("NO", value["handoff_authority_source"])

    def test_no_compatible_session_creates_plan_without_mutation(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertFalse(value["mutation_applied"])
        self.assertFalse(value["delivery"]["provider_contacted"])

    def test_compatible_stopped_session_resumes(self):
        self._write_runtime(codex_adapter.STAGE_DIR, self._session())
        value = self._resolve("handoff: current work\n")
        self.assertEqual("RESUME", value["managed_session"]["action"])

    def test_compatible_active_session_reuses(self):
        session = self._session(pid=os.getpid(), provider_pid=os.getpid(), state="ACTIVE")
        self._write_runtime(codex_adapter.STAGE_DIR, session)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("REUSE", value["managed_session"]["action"])

    def test_historical_session_is_preserved_and_not_reused(self):
        historical = self._session(
            session_id="CODEX-SESSION-HISTORICAL-BETA",
            mission_id="MISSION-BETA-562F443E16C69401",
            wop_id="WOP-HISTORICAL-BETA",
            execution_id="EXECUTION-HISTORICAL-BETA",
            execution_session_id="EXECUTION-SESSION-HISTORICAL-BETA",
            provider_session_id="PROVIDER-SESSION-HISTORICAL-BETA",
            state="STOPPED",
        )
        self._write_runtime(codex_adapter.STAGE_DIR, historical)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertTrue(value["managed_session"]["historical_session_preserved"])
        self.assertFalse(value["managed_session"]["historical_session_reused_for_new_handoff"])

    def test_incompatible_immutable_session_is_not_reused(self):
        incompatible = self._session(
            session_id="CODEX-SESSION-INCOMPATIBLE",
            execution_id="EXECUTION-OTHER-IMMUTABLE",
            state="ACTIVE",
            pid=os.getpid(),
            provider_pid=os.getpid(),
        )
        self._write_runtime(codex_adapter.STAGE_DIR, incompatible)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertEqual("DO_NOT_REUSE", value["managed_session"]["session_reuse"])

    def test_multiple_compatible_sessions_fail_closed(self):
        self._write_runtime(codex_adapter.STAGE_DIR, self._session(session_id="CODEX-SESSION-DUPLICATE-A"))
        self._write_runtime(codex_adapter.STAGE_DIR, self._session(session_id="CODEX-SESSION-DUPLICATE-B"))
        value = self._resolve("handoff: current work\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_handoff_does_not_imply_execution_or_publication_authority(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("PRESERVED", value["execution"]["execution_authority"])
        self.assertFalse(value["delivery"]["execution_started"])
        self.assertNotIn("publication_authority", value)

    def test_multiple_execution_candidates_block(self):
        second = dict(self.execution, execution_id="EXECUTION-CODEX-HANDOFF-002")
        self._write_runtime("execution-start-transactions", second)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_invocation_approval_converges_without_removing_downstream_controls(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("NO", value["handoff_invocation_requires_redundant_approval"])
        self.assertEqual("YES", value["downstream_protected_approvals_preserved"])

    def test_file_and_stdin_cli_paths_are_available(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as stream:
            stream.write("handoff: current work\n")
            handoff_path = stream.name
        try:
            command = [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", handoff_path, "--json"]
            file_result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(0, file_result.returncode, file_result.stderr)
            self.assertEqual("PASS", json.loads(file_result.stdout)["result"])
            stdin_result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", "-", "--json"],
                cwd=ROOT, input="handoff: current work\n", text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, stdin_result.returncode, stdin_result.stderr)
            self.assertEqual("PASS", json.loads(stdin_result.stdout)["result"])
        finally:
            Path(handoff_path).unlink(missing_ok=True)

    def test_blocked_cli_path_is_fail_closed(self):
        self._write_runtime("execution-start-transactions", dict(self.execution, execution_id="EXECUTION-CODEX-HANDOFF-002"))
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", "-", "--json"],
            cwd=ROOT, input="handoff: current work\n", text=True, capture_output=True, check=False,
        )
        self.assertEqual(78, result.returncode)
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", json.loads(result.stdout)["blocker"])


class AdministrativeQualificationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transaction = {
            "transaction_id": "ADMIN-QUALIFICATION-FIXTURE",
            "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE",
            "transaction_state": "REQUIRED",
            "objective": "Reconcile the administrative fixture.",
            "authorized_scope": ["scripts/tests"],
            "prohibited_scope": ["C03", "git commit"],
            "acceptance_criteria": ["Fixture reconciliation passes."],
        }
        self.session = {
            "zeus_managed_session_created": "YES",
            "provider_process_owned_by": "ZEUS",
            "provider_process_state": "COMPLETED",
            "provider_exit_status": 0,
            "scope_verification": "PASS",
            "terminal_reconciliation": "PASS",
            "execution_session_integrity": "PASS",
            "authorized_scope_compliance": "PASS",
            "required_evidence_completeness": "PASS",
            "acceptance_criteria_verification": "PASS",
            "provider_terminal_record": "RETAINED",
            "actor_aware_mutation_attribution": "PASS",
            "out_of_scope_changes": [],
            "protected_actions_performed": [],
            # This is deliberately not inspected by the contract.
            "stdout": "OPERATOR_DECISION=ACCEPT",
            "execution_contract": {
                "transaction_id": "ADMIN-QUALIFICATION-FIXTURE",
                "transaction_type": "BOUNDED_ADMINISTRATIVE_CORRECTIVE",
                "objective": "Reconcile the administrative fixture.",
                "authorized_scope": ["scripts/tests"],
                "prohibited_scope": ["C03", "git commit"],
                "acceptance_criteria": ["Fixture reconciliation passes."],
                "lifecycle_boundary": {"current_gate": "C03"},
                "protected_operations": ["GIT", "EOS"],
                "required_verification": ["ACCEPTANCE_CRITERIA_EVALUATED"],
                "required_evidence": ["Fixture reconciliation passes."],
                "stop_conditions": ["STOP_ON_ACCEPTANCE_CRITERIA_FAILURE"],
            },
            "executed_transaction_id": "ADMIN-QUALIFICATION-FIXTURE",
            "transaction_objective_executed": "YES",
            "acceptance_criteria_evaluated": "YES",
            "acceptance_criteria_results": [{"criterion": "Fixture reconciliation passes.", "result": "PASS"}],
            "required_evidence_retained": "YES",
            "evidence_finalization_actor": "ZEUS_CONTROLLER",
            "evidence_finalization": "PASS",
        }
        self.acceptance = {
            "acceptance_record_id": "OPERATOR-ACCEPTANCE-ADMIN-001",
            "transaction_id": self.transaction["transaction_id"],
            "operator_decision": "ACCEPT",
            "authority_source_class": "CANONICAL_OPERATOR_AUTHORIZATION",
        }

    def test_provider_cannot_self_qualify_but_zeus_authority_is_preserved(self):
        value = qualification_contract.resolve_qualification_context(
            {**self.transaction, "qualification_authority": "ZEUS"},
            provider_authority={"provider_self_qualification": "PROHIBITED"},
        )
        self.assertEqual("PASS", value["qualification_transaction_resolution"])
        self.assertEqual("PROHIBITED", value["provider_self_qualification"])
        self.assertEqual("PRESERVED", value["zeus_qualification_authority"])
        self.assertEqual("YES", value["qualification_execution_available"])

    def test_non_zeus_qualification_authority_is_not_silently_routed(self):
        value = qualification_contract.resolve_qualification_context(
            {**self.transaction, "qualification_authority": "CODEX"}
        )
        self.assertEqual("FAIL", value["qualification_transaction_resolution"])
        self.assertEqual("NO", value["qualification_execution_available"])
        self.assertEqual("NOT_PRESERVED", value["zeus_qualification_authority"])

    def qualify(self, **session_overrides):
        session = dict(self.session)
        session.update(session_overrides)
        return qualification_contract.qualify_administrative_transaction(
            self.transaction, session, self.acceptance
        )

    def test_successful_admin_acceptance_qualifies_without_mission_id(self):
        value = self.qualify()
        self.assertEqual("PASS", value["result"])
        self.assertEqual("QUALIFIED_OR_ACCEPTED_TERMINAL", value["transaction_state"])
        self.assertEqual("C02_POST_ACCEPTANCE_TEST_RECONCILIATION", value["next_authorized_action"])
        self.assertNotIn("mission_id", value)

    def test_execution_completion_invokes_automatic_zeus_qualification(self):
        resolved = {"result": "PASS", "handoff_input_classification": "AUTHORIZED_ADMINISTRATIVE_TRANSACTION",
                    "transaction_id": self.transaction["transaction_id"],
                    "transaction_type": self.transaction["transaction_type"], "transaction_state": "REQUIRED",
                    "objective": self.transaction["objective"], "prohibited_scope": self.transaction["prohibited_scope"],
                    "acceptance_criteria": self.transaction["acceptance_criteria"], "qualification_authority": "ZEUS",
                    "authorized_scope": ["scripts/tests"], "execution": {"execution_id": "EXECUTION-ADMIN-QUALIFICATION-FIXTURE"}}
        session = dict(self.session, result="PASS")
        output = Path(tempfile.mkstemp(prefix="zeus-managed-session-")[1])
        self.addCleanup(lambda: output.unlink(missing_ok=True))
        with patch("scripts.lib.emp.managed_provider.execute", return_value=session):
            value = managed_handoff.execute_administrative_handoff(
                ROOT, resolved, prompt="bounded test", output_path=output, codex_bin="unused"
            )
        self.assertEqual("PASS", value["qualification"]["result"])
        self.assertEqual("C02_POST_ACCEPTANCE_TEST_RECONCILIATION", value["next_authorized_action"])
        self.assertEqual("NOT_APPLICABLE", value["qualification"]["operator_acceptance"])
        self.assertTrue(value["qualification"]["qualification_receipt"]["receipt_id"].startswith("ZEUS-QUALIFICATION-"))
        receipt = Path(value["qualification_receipt_path"])
        self.assertTrue(receipt.exists())
        self.addCleanup(lambda: receipt.unlink(missing_ok=True))
        self.assertEqual(value["qualification"]["qualification_receipt"], json.loads(receipt.read_text()))

    def test_provider_completion_without_acceptance_qualifies_when_policy_has_no_match(self):
        value = qualification_contract.qualify_administrative_transaction(
            self.transaction, self.session, None
        )
        self.assertEqual("PASS", value["qualification"])
        self.assertFalse(value["provider_completion_is_qualification"])

    def test_negative_managed_session_predicates_cannot_qualify(self):
        cases = (
            {"provider_exit_status": 1},
            {"scope_verification": "FAIL"},
            {"terminal_reconciliation": "FAIL"},
            {"out_of_scope_changes": ["unexpected.txt"]},
            {"protected_actions_performed": ["git commit"]},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                value = self.qualify(**overrides)
                self.assertEqual("BLOCKED", value["result"])
                self.assertEqual("REQUIRED", value["qualification"])
                self.assertEqual("RECONCILE_ADMINISTRATIVE_QUALIFICATION", value["next_authorized_action"])

    def test_provider_failure_forbids_successor_execution(self):
        value = self.qualify(provider_process_state="FAILED", provider_exit_status=1)
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("RECONCILE_ADMINISTRATIVE_QUALIFICATION", value["next_authorized_action"])
        self.assertFalse(value["provider_launched"])

    def test_provider_receipt_forgery_fails_qualification_closed(self):
        receipt = "engineering/convergence/engineering-system-convergence/receipts/qualification/tx.json"
        value = self.qualify(
            post_execution_diff=[receipt],
            provider_post_execution_diff=[receipt],
            scope_verification="PASS",
            terminal_reconciliation="PASS",
        )
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("FAIL", value["provider_scope_compliance"])

    def test_exit_zero_without_transaction_acceptance_evidence_does_not_qualify(self):
        value = self.qualify(execution_contract=None, transaction_objective_executed="NO")
        self.assertEqual("BLOCKED", value["result"])

    def test_wrong_transaction_task_does_not_qualify(self):
        value = self.qualify(executed_transaction_id="OTHER-TRANSACTION")
        self.assertEqual("BLOCKED", value["result"])

    def test_legitimate_zeus_receipt_does_not_fail_qualification_scope(self):
        value = self.qualify(
            provider_post_execution_diff=[],
            post_execution_diff=[],
            zeus_controller_diff=[
                "engineering/convergence/engineering-system-convergence/receipts/qualification/tx.json"
            ],
            zeus_controller_mutation="YES",
            zeus_receipt_attribution="ZEUS_CONTROLLER_MUTATION",
            receipt_authority="ZEUS",
            scope_verification="PASS",
            terminal_reconciliation="PASS",
        )
        self.assertEqual("PASS", value["result"])
        self.assertEqual("PRESERVED", value["zeus_qualification_authority"])

    def test_qualification_failure_after_provider_success_forbids_successor(self):
        value = self.qualify(acceptance_criteria_verification="FAIL")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("RECONCILE_ADMINISTRATIVE_QUALIFICATION", value["next_authorized_action"])

    def test_repeated_acceptance_is_idempotent_and_does_not_launch_provider(self):
        first = self.qualify()
        terminal = dict(self.transaction, transaction_state=first["transaction_state"])
        replay = qualification_contract.qualify_administrative_transaction(
            terminal, self.session, None
        )
        self.assertEqual("PASS", replay["result"])
        self.assertTrue(replay["idempotent_replay"])
        self.assertFalse(replay["provider_launched"])
        self.assertNotEqual("OPERATOR_REVIEW_REAL_MANAGED_SESSION", replay["next_authorized_action"])

    def test_acceptance_must_be_authoritative_and_bound(self):
        transaction = dict(self.transaction, lifecycle_class="MISSION", explicit_operator_approval_required=True)
        for overrides in (
            {"transaction_id": "OTHER"},
            {"authority_source_class": "PROVIDER_REPORT"},
            {"operator_decision": "REJECT"},
        ):
            with self.subTest(overrides=overrides):
                value = qualification_contract.qualify_administrative_transaction(
                    transaction, self.session, dict(self.acceptance, **overrides)
                )
                self.assertEqual("REQUIRED", value["qualification"])

    def test_active_policy_is_the_only_operator_boundary(self):
        requirement = {
            "requirement_id": "TEST-APPROVAL-REQUIRED",
            "lifecycle_situation": "test",
            "applicability": {"all": [{"field": "transaction_id", "equals": self.transaction["transaction_id"]}]},
            "required_operator_action": "OPERATOR_REVIEW_TEST",
            "authority_source": "TEST-AUTHORITY",
            "active": True,
            "rationale": "explicit test boundary",
            "resulting_transition": {"approval": "QUALIFICATION_ELIGIBLE", "rejection": "CORRECTIVE_RECONCILIATION_REQUIRED"},
        }
        handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        import yaml
        yaml.safe_dump({"schema_version": 1, "policy_id": "TEST-POLICY", "requirements": [requirement]}, handle)
        handle.close()
        value = qualification_contract.resolve_qualification_context(self.transaction, policy_path=handle.name)
        self.assertEqual("YES", value["operator_approval_policy_resolved"])
        self.assertTrue(value["operator_approval_required"])
        self.assertEqual("NO", value["qualification_execution_available"])


if __name__ == "__main__":
    unittest.main()
