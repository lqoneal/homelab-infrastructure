#!/usr/bin/env python3
"""Conformance tests for the SPEC-0014 convergence runtime."""

from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.convergence_runtime import ConvergenceRuntime, ConvergenceRuntimeError
from scripts.lib.emp.operational_gate_handler import OperationalExecutionContextService


class ConvergenceRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ConvergenceRuntime(ROOT)

    def test_ready_wop_without_authority_fails_closed(self):
        value = self.runtime.resolve(
            wop_id="WOP-OA-01-IMPLEMENTATION-001", revision=1,
            action="activate", correlation_id="test-no-authority",
        )
        self.assertEqual("PRECONDITION_FAILED", value["outcome"])
        self.assertEqual(["SUBMITTED_WOP_AUTHORITY_REQUIRED"], value["reasons"])
        self.assertTrue(value["receipt_digest"])

    def test_artifacts_and_synchronization_are_derived_and_directional(self):
        artifact = self.runtime.generated_artifact(
            artifact_id="TEST-PROJECTION",
            source_entities=[{"entity_type": "ImplementationWOP", "entity_id": "WOP-OA-01-IMPLEMENTATION-001", "revision": "1"}],
        )
        self.assertEqual("Derived", artifact["classification"])
        receipt = self.runtime.resolve(
            wop_id="WOP-OA-01-IMPLEMENTATION-001", revision=1,
            action="inspect", correlation_id="test-sync",
        )
        plan = self.runtime.synchronization_plan(receipt)
        self.assertEqual("authoritative_to_derived", plan["direction"])
        self.assertEqual("convergence.resolution", self.runtime.eens_event(receipt)["event_type"])
        self.assertEqual("EMP", self.runtime.emp_receipt(receipt)["consumer"])
        self.assertEqual("NOT_READY", self.runtime.qualify(receipt)["result"])

    def test_execution_flow_is_not_admitted_without_authority(self):
        flow = self.runtime.execution_flow(
            wop_id="WOP-OA-01-IMPLEMENTATION-001", revision=1,
            action="execute", correlation_id="test-execution-flow",
        )
        self.assertFalse(flow["execution_admitted"])
        self.assertEqual("PRECONDITION_FAILED", flow["authority_receipt"]["outcome"])

    def test_explicit_manual_governance_wop_resolves_only_allowlisted_action(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/manual").mkdir(parents=True)
            (root / "engineering/authority").mkdir(parents=True)
            policy = {
                "policy_id": "MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY", "revision": "1.0",
                "classification": "Authoritative", "authoritative_owner": "Engineering Governance",
                "lifecycle_state": "ACTIVE", "mode": "MANUAL_GOVERNANCE",
            }
            wop = {
                "wop_id": "WOP-MANUAL", "revision": 1, "status": "READY",
                "mission_id": "MISSION-MANUAL", "phase_id": "PHASE-MANUAL",
                "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"},
                "manual_governance_authority": {
                    "policy_id": policy["policy_id"], "policy_revision": "1.0",
                    "delegation_state": "ACTIVE",
                    "governance_submission": {
                        "submitted": True, "submitted_by": "Engineering Governance",
                        "submission_id": "WOP-MANUAL", "directive_id": "CCD-MANUAL-001",
                    },
                    "permitted_actions": ["create_authority_record"],
                },
            }
            policy_path = root / "engineering/authority/manual-policy.yaml"
            wop_path = root / "engineering/work-orders/manual/immutable-wop.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=True))
            wop_path.write_text(yaml.safe_dump(wop, sort_keys=True))
            digest = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.1",
                   "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                {"entity_type": "ImplementationWOP", "entity_id": "WOP-MANUAL", "revision": 1,
                 "authoritative_owner": "WOP Owner", "classification": "Authoritative",
                 "source": "engineering/work-orders/manual/immutable-wop.yaml", "source_digest": digest(wop_path)},
                {"entity_type": "ManualGovernanceWOPAuthorityPolicy",
                 "entity_id": policy["policy_id"], "revision": "1.0",
                 "authoritative_owner": "Engineering Governance", "classification": "Authoritative",
                 "source": "engineering/authority/manual-policy.yaml", "source_digest": digest(policy_path)},
            ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(
                yaml.safe_dump(emm, sort_keys=True)
            )
            runtime = ConvergenceRuntime(root)
            resolved = runtime.resolve(
                wop_id="WOP-MANUAL", revision=1, action="create_authority_record",
                correlation_id="manual-governance",
            )
            self.assertEqual("RESOLVED", resolved["outcome"])
            self.assertEqual("SUBMITTED_WOP", resolved["authority_mode"])
            generated = runtime.operational_wop(
                intent="create subordinate artifact",
                flow=runtime.execution_flow(
                    wop_id="WOP-MANUAL", revision=1,
                    action="create_authority_record", correlation_id="manual-wop",
                ),
            )
            self.assertEqual(
                "SUBMITTED_WOP", generated["wop"]["authority_lineage"]["mode"]
            )
            self.assertEqual("WOP-MANUAL", generated["wop"]["authority_lineage"]["submission_id"])
            denied = runtime.resolve(
                wop_id="WOP-MANUAL", revision=1, action="execute",
                correlation_id="manual-governance-denied",
            )
            self.assertEqual("INTEGRITY_FAILURE", denied["outcome"])
            self.assertIn("does not permit", denied["reasons"][0])

    def test_repository_bootstrap_artifacts_resolve_without_lifecycle_effect(self):
        value = self.runtime.bootstrap_gate_action_specification(
            root_wop_id="WOP-OA-01-ROOT-ADMISSION-001", revision=1,
            correlation_id="test-bootstrap-artifacts",
        )
        self.assertEqual("RESOLVED", value["outcome"])
        self.assertEqual("NONE", value["lifecycle_effect"])
        self.assertEqual("OA-01-BOOTSTRAP-GATE-ACTIONS", value["action_specification"]["id"])
        self.assertEqual("SUBMITTED_WOP", value["authority_receipt"]["authority_mode"])

    def test_published_framework_creates_only_nonpersisted_candidates(self):
        candidate = self.runtime.artifact_candidate(
            kind="authority_record", root_wop_id="WOP-OA-01-ROOT-ADMISSION-001",
            root_revision=2, target_wop_id="WOP-OA-01-IMPLEMENTATION-001",
            target_revision=1, identifier="AR-OA-01-TEST",
            permitted_actions=["execute_first_gate"],
        )
        self.assertTrue(candidate["publication_required"])
        self.assertEqual("NONE", candidate["lifecycle_effect"])
        self.assertEqual("DRAFT", candidate["candidate"]["lifecycle_state"])
        self.assertEqual("AR-OA-01-TEST", candidate["candidate"]["authority_record_id"])

    def test_active_authority_and_wop_resolve_only_when_exactly_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/demo").mkdir(parents=True)
            (root / "engineering/authority-records").mkdir(parents=True)
            wop = {
                "wop_id": "WOP-DEMO", "revision": 1, "status": "ACTIVE",
                "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"},
            }
            authority = {
                "authority_record_id": "AR-DEMO", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                "lifecycle_state": "ACTIVE", "permitted_actions": ["inspect"],
                "implementation_wop": {"wop_id": "WOP-DEMO", "revision": 1},
            }
            (root / "engineering/work-orders/demo/immutable-wop.yaml").write_text(yaml.safe_dump(wop))
            (root / "engineering/authority-records/AR-DEMO.yaml").write_text(yaml.safe_dump(authority))
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.0", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                {"entity_type": "ImplementationWOP", "entity_id": "WOP-DEMO", "revision": 1, "authoritative_owner": "WOP Owner", "classification": "Authoritative", "source": "engineering/work-orders/demo/immutable-wop.yaml"},
                {"entity_type": "AuthorityRecord", "entity_id": "AR-DEMO", "revision": 1, "authoritative_owner": "Governance", "classification": "Authoritative", "source": "engineering/authority-records/AR-DEMO.yaml"},
            ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(yaml.safe_dump(emm))
            runtime = ConvergenceRuntime(root)
            resolved = runtime.resolve(wop_id="WOP-DEMO", revision=1, action="inspect", correlation_id="test", authority_record_id="AR-DEMO")
            self.assertEqual("RESOLVED", resolved["outcome"])
            flow = runtime.execution_flow(wop_id="WOP-DEMO", revision=1, action="inspect", correlation_id="flow", authority_record_id="AR-DEMO")
            self.assertTrue(flow["execution_admitted"])
            self.assertEqual("PASS", flow["qualification"]["result"])

    def test_emm_lifecycle_transition_projects_active_without_mutating_immutable_wop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/demo").mkdir(parents=True)
            (root / "engineering/lifecycle-transitions/records").mkdir(parents=True)
            wop = {
                "wop_id": "WOP-DEMO", "revision": 1, "status": "READY",
                "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"},
            }
            specification = {
                "specification_id": "OPERATIONAL-ALPHA-IMPLEMENTATION-WOP-LIFECYCLE-TRANSITION",
                "revision": "1.0", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                "lifecycle_state": "READY", "transition_artifact": {
                    "entity_type": "ImplementationWOPLifecycleTransition",
                    "allowed_transitions": [{"from": "READY", "to": "ACTIVE", "execution_state": "NOT_STARTED"}],
                },
            }
            transition = {
                "transition_id": "TR-DEMO", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                "lifecycle_state": "ACTIVE", "implementation_wop": {"wop_id": "WOP-DEMO", "revision": 1},
                "source_lifecycle_state": "READY", "target_lifecycle_state": "ACTIVE",
                "execution_state": "NOT_STARTED", "authority_lineage": {"receipt": "demo"},
                "reconciliation": {"state": "complete"},
            }
            wop_path = root / "engineering/work-orders/demo/immutable-wop.yaml"
            spec_path = root / "engineering/lifecycle-transitions/spec.yaml"
            transition_path = root / "engineering/lifecycle-transitions/records/TR-DEMO.yaml"
            for path, value in ((wop_path, wop), (spec_path, specification), (transition_path, transition)):
                path.write_text(yaml.safe_dump(value), encoding="utf-8")
            digest_path = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.0",
                   "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                       {"entity_type": "ImplementationWOP", "entity_id": "WOP-DEMO", "revision": 1,
                        "authoritative_owner": "WOP Owner", "classification": "Authoritative",
                        "source": "engineering/work-orders/demo/immutable-wop.yaml", "source_digest": digest_path(wop_path)},
                       {"entity_type": "ImplementationWOPLifecycleTransitionSpecification",
                        "entity_id": "OPERATIONAL-ALPHA-IMPLEMENTATION-WOP-LIFECYCLE-TRANSITION", "revision": "1.0",
                        "authoritative_owner": "Governance", "classification": "Authoritative",
                        "source": "engineering/lifecycle-transitions/spec.yaml", "source_digest": digest_path(spec_path)},
                       {"entity_type": "ImplementationWOPLifecycleTransition", "entity_id": "TR-DEMO", "revision": 1,
                        "implementation_wop_id": "WOP-DEMO", "implementation_wop_revision": 1,
                        "authoritative_owner": "Governance", "classification": "Authoritative",
                        "source": "engineering/lifecycle-transitions/records/TR-DEMO.yaml", "source_digest": digest_path(transition_path)},
                   ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(yaml.safe_dump(emm), encoding="utf-8")
            _, effective, _ = ConvergenceRuntime(root)._wop("WOP-DEMO", 1)
            self.assertEqual("ACTIVE", effective["status"])
            self.assertEqual("TR-DEMO", effective["effective_lifecycle_transition"]["transition_id"])
            self.assertEqual("READY", yaml.safe_load(wop_path.read_text(encoding="utf-8"))["status"])

    def test_execution_contract_blocks_without_an_emm_registered_gate_plan(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as workspace:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/demo").mkdir(parents=True)
            (root / "engineering/authority-records").mkdir(parents=True)
            (root / "engineering/execution").mkdir(parents=True)
            wop = {"wop_id": "WOP-DEMO", "revision": 1, "status": "ACTIVE",
                   "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"}}
            authority = {"authority_record_id": "AR-DEMO", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                         "lifecycle_state": "ACTIVE", "permitted_actions": ["execute"],
                         "implementation_wop": {"wop_id": "WOP-DEMO", "revision": 1}}
            contract = {"contract_id": "OPERATIONAL-ALPHA-EXECUTION-CONTRACT", "revision": "1.0",
                        "classification": "Authoritative", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                        "lifecycle_state": "READY", "gate_plan_resolution": {"entity_type": "OperationalGatePlan"}}
            wop_path = root / "engineering/work-orders/demo/immutable-wop.yaml"
            authority_path = root / "engineering/authority-records/AR-DEMO.yaml"
            contract_path = root / "engineering/execution/operational-alpha-execution-contract.yaml"
            for path, value in ((wop_path, wop), (authority_path, authority), (contract_path, contract)):
                path.write_text(yaml.safe_dump(value, sort_keys=True))
            digest = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.1",
                   "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                {"entity_type": "ImplementationWOP", "entity_id": "WOP-DEMO", "revision": 1,
                 "authoritative_owner": "WOP Owner", "classification": "Authoritative",
                 "source": "engineering/work-orders/demo/immutable-wop.yaml", "source_digest": digest(wop_path)},
                {"entity_type": "AuthorityRecord", "entity_id": "AR-DEMO", "revision": 1,
                 "authoritative_owner": "Governance", "classification": "Authoritative",
                 "source": "engineering/authority-records/AR-DEMO.yaml", "source_digest": digest(authority_path)},
                {"entity_type": "OperationalExecutionContract", "entity_id": "OPERATIONAL-ALPHA-EXECUTION-CONTRACT", "revision": "1.0",
                 "authoritative_owner": "Infrastructure", "classification": "Authoritative",
                 "source": "engineering/execution/operational-alpha-execution-contract.yaml", "source_digest": digest(contract_path)},
            ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(yaml.safe_dump(emm, sort_keys=True))
            runtime = ConvergenceRuntime(root)
            flow = runtime.execution_flow(wop_id="WOP-DEMO", revision=1, action="execute", correlation_id="contract", authority_record_id="AR-DEMO")
            with self.assertRaisesRegex(ConvergenceRuntimeError, "OperationalGatePlan/WOP-DEMO"):
                runtime.operational_execution_context(
                    flow=flow, execution_id="EXECUTION-DEMO", mission_id="MISSION-DEMO", repository=root,
                    repository_baseline="a" * 40, wop_submission_digest="b" * 64, workspace=workspace,
                )

    def test_execution_contract_builds_context_only_from_authoritative_plan(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as workspace:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/demo").mkdir(parents=True)
            (root / "engineering/authority-records").mkdir(parents=True)
            (root / "engineering/execution/plans").mkdir(parents=True)
            wop = {"wop_id": "WOP-DEMO", "revision": 1, "status": "ACTIVE",
                   "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"}}
            authority = {"authority_record_id": "AR-DEMO", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                         "lifecycle_state": "ACTIVE", "permitted_actions": ["execute"],
                         "implementation_wop": {"wop_id": "WOP-DEMO", "revision": 1}}
            contract = {"contract_id": "OPERATIONAL-ALPHA-EXECUTION-CONTRACT", "revision": "1.0",
                        "classification": "Authoritative", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                        "lifecycle_state": "READY", "gate_plan_resolution": {"entity_type": "OperationalGatePlan"}}
            plan = {"gate_plan_id": "PLAN-DEMO", "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                    "lifecycle_state": "ACTIVE", "implementation_wop": {"wop_id": "WOP-DEMO", "revision": 1},
                    "gate_plan": {"gates": {"EXECUTE_WORK": {"dependencies": [], "actions": [{
                        "action_id": "verify", "action_type": "verify_artifact", "path": "artifact.txt", "content_digest": "c" * 64
                    }]}}}}
            wop_path = root / "engineering/work-orders/demo/immutable-wop.yaml"
            authority_path = root / "engineering/authority-records/AR-DEMO.yaml"
            contract_path = root / "engineering/execution/operational-alpha-execution-contract.yaml"
            plan_path = root / "engineering/execution/plans/WOP-DEMO.yaml"
            for path, value in ((wop_path, wop), (authority_path, authority), (contract_path, contract), (plan_path, plan)):
                path.write_text(yaml.safe_dump(value, sort_keys=True))
            digest = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.1",
                   "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                {"entity_type": "ImplementationWOP", "entity_id": "WOP-DEMO", "revision": 1, "authoritative_owner": "WOP Owner", "classification": "Authoritative", "source": "engineering/work-orders/demo/immutable-wop.yaml", "source_digest": digest(wop_path)},
                {"entity_type": "AuthorityRecord", "entity_id": "AR-DEMO", "revision": 1, "authoritative_owner": "Governance", "classification": "Authoritative", "source": "engineering/authority-records/AR-DEMO.yaml", "source_digest": digest(authority_path)},
                {"entity_type": "OperationalExecutionContract", "entity_id": "OPERATIONAL-ALPHA-EXECUTION-CONTRACT", "revision": "1.0", "authoritative_owner": "Infrastructure", "classification": "Authoritative", "source": "engineering/execution/operational-alpha-execution-contract.yaml", "source_digest": digest(contract_path)},
                {"entity_type": "OperationalGatePlan", "entity_id": "WOP-DEMO", "revision": 1, "authoritative_owner": "WOP Owner", "classification": "Authoritative", "source": "engineering/execution/plans/WOP-DEMO.yaml", "source_digest": digest(plan_path)},
            ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(yaml.safe_dump(emm, sort_keys=True))
            runtime = ConvergenceRuntime(root)
            flow = runtime.execution_flow(wop_id="WOP-DEMO", revision=1, action="execute", correlation_id="contract", authority_record_id="AR-DEMO")
            context = runtime.operational_execution_context(
                flow=flow, execution_id="EXECUTION-DEMO", mission_id="MISSION-DEMO", repository=root,
                repository_baseline="a" * 40, wop_submission_digest="b" * 64, workspace=workspace,
            )
            OperationalExecutionContextService.validate(context)
            self.assertEqual("PLAN-DEMO", plan["gate_plan_id"])
            self.assertEqual("EXECUTE_WORK", next(iter(context["gate_plan"]["gates"])))

    def test_completed_execution_allows_only_verification_without_authority_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engineering/metadata").mkdir(parents=True)
            (root / "engineering/work-orders/demo").mkdir(parents=True)
            (root / "engineering/authority-records").mkdir(parents=True)
            wop = {
                "wop_id": "WOP-COMPLETED", "revision": 1, "status": "ACTIVE",
                "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"},
                "lifecycle": {"execution_state": "COMPLETED"},
            }
            authority = {
                "authority_record_id": "AR-COMPLETED",
                "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
                "lifecycle_state": "ACTIVE", "permitted_actions": ["execute_mission"],
                "implementation_wop": {"wop_id": "WOP-COMPLETED", "revision": 1},
            }
            wop_path = root / "engineering/work-orders/demo/immutable-wop.yaml"
            authority_path = root / "engineering/authority-records/AR-COMPLETED.yaml"
            wop_path.write_text(yaml.safe_dump(wop), encoding="utf-8")
            authority_path.write_text(yaml.safe_dump(authority), encoding="utf-8")
            digest_path = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            emm = {"schema_version": 1, "emm_id": "TEST", "version": "1.0",
                   "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [
                       {"entity_type": "ImplementationWOP", "entity_id": "WOP-COMPLETED", "revision": 1,
                        "authoritative_owner": "WOP Owner", "classification": "Authoritative",
                        "source": "engineering/work-orders/demo/immutable-wop.yaml", "source_digest": digest_path(wop_path)},
                       {"entity_type": "AuthorityRecord", "entity_id": "AR-COMPLETED", "revision": 1,
                        "authoritative_owner": "Governance", "classification": "Authoritative",
                        "source": "engineering/authority-records/AR-COMPLETED.yaml", "source_digest": digest_path(authority_path)},
                   ]}
            (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(
                yaml.safe_dump(emm), encoding="utf-8"
            )
            runtime = ConvergenceRuntime(root)
            verified = runtime.resolve(
                wop_id="WOP-COMPLETED", revision=1, action="verify",
                correlation_id="completed-verification", authority_record_id="AR-COMPLETED",
            )
            self.assertEqual("RESOLVED", verified["outcome"])
            self.assertEqual("COMPLETED_EXECUTION", verified["verification_scope"])
            rejected = runtime.resolve(
                wop_id="WOP-COMPLETED", revision=1, action="generate_wop",
                correlation_id="completed-verification-denied", authority_record_id="AR-COMPLETED",
            )
            self.assertEqual("PRECONDITION_FAILED", rejected["outcome"])
            self.assertIn("AUTHORITY_RECORD_NOT_APPLICABLE", rejected["reasons"])


if __name__ == "__main__":
    unittest.main()
