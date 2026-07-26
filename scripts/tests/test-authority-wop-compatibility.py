#!/usr/bin/env python3
"""Regression tests for offline Authority/WOP compatibility."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.authority.engine import AuthorityGraph  # noqa: E402
from scripts.lib.authority_wop.compatibility import (  # noqa: E402
    CompatibilityEvaluator,
    DecisionCode,
    DigestFixtureSignatureVerifier,
)
from scripts.lib.wop.contract import (  # noqa: E402
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    RevocationRecord,
    WorkPackage,
    WorkPackageError,
    load_mapping,
)


FIXTURES = ROOT / "engineering" / "compatibility" / "fixtures"
AUTHORITY_FIXTURES = ROOT / "engineering" / "authority" / "fixtures"
NOW = datetime(2026, 7, 25, 0, 15, tzinfo=timezone.utc)


class RejectingSignatureVerifier:
    def verify(self, algorithm, key_id, signature, payload_digest):
        return False


class AuthorityWopCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = CompatibilityEvaluator()
        self.graph = AuthorityGraph.load(AUTHORITY_FIXTURES / "valid.yaml")
        self.wop = WorkPackage.load(FIXTURES / "valid-wop.yaml")
        self.state = EvaluationState.from_mapping(
            load_mapping(FIXTURES / "valid-evaluation.yaml", "evaluation")
        )
        self.receipt = PublicationReceipt.from_mapping(
            load_mapping(FIXTURES / "publication-receipt.yaml", "receipt")
        )
        self.lease = ExecutionLease.from_mapping(
            load_mapping(FIXTURES / "execution-lease.yaml", "lease")
        )
        self.signature = DigestFixtureSignatureVerifier()

    def evaluate(self, **overrides):
        arguments = {
            "graph": self.graph,
            "wop": self.wop,
            "state": self.state,
            "receipt": self.receipt,
            "lease": self.lease,
            "reference_time": NOW,
            "signature_verifier": self.signature,
        }
        arguments.update(overrides)
        return self.evaluator.evaluate(**arguments)

    def mutate_wop(self, mutate) -> WorkPackage:
        value = copy.deepcopy(self.wop.to_mapping())
        mutate(value)
        value["payload_digest"] = "0" * 64
        value["signature"]["value"] = "0" * 64
        digest = WorkPackage.from_mapping(value).calculated_digest()
        value["payload_digest"] = digest
        value["signature"]["value"] = digest
        return WorkPackage.from_mapping(value)

    def mutate_state(self, **changes) -> EvaluationState:
        value = dict(load_mapping(FIXTURES / "valid-evaluation.yaml", "evaluation"))
        value.update(changes)
        return EvaluationState.from_mapping(value)

    def rebound_records(self, wop: WorkPackage):
        receipt_value = dict(
            load_mapping(FIXTURES / "publication-receipt.yaml", "receipt")
        )
        receipt_value["wop_id"] = wop.wop_id
        receipt_value["payload_digest"] = wop.payload_digest
        lease_value = dict(load_mapping(FIXTURES / "execution-lease.yaml", "lease"))
        lease_value["wop_id"] = wop.wop_id
        lease_value["payload_digest"] = wop.payload_digest
        return (
            PublicationReceipt.from_mapping(receipt_value),
            ExecutionLease.from_mapping(lease_value),
        )

    def evaluate_mutated_wop(self, wop: WorkPackage, **overrides):
        receipt, lease = self.rebound_records(wop)
        return self.evaluate(wop=wop, receipt=receipt, lease=lease, **overrides)

    def assert_decision(self, expected: DecisionCode, **overrides):
        decision = self.evaluate(**overrides)
        self.assertEqual(decision.decision, expected, decision.to_json())
        self.assertEqual(decision.authorized, expected is DecisionCode.AUTHORIZED)
        return decision

    def test_valid_inputs_authorize_exact_chain_and_capability(self) -> None:
        decision = self.assert_decision(DecisionCode.AUTHORIZED)
        self.assertEqual(
            decision.authority_chain,
            ("work-package", "mission", "baseline", "governance", "charter", "organization"),
        )
        self.assertEqual(decision.effective_capabilities, ("execute",))
        self.assertEqual(decision.requested_capabilities, ("execute",))

    def test_unknown_authority_fails_closed(self) -> None:
        wop = self.mutate_wop(
            lambda value: value["authority_binding"].update(
                authority_node_id="unknown-node"
            )
        )
        decision = self.evaluate_mutated_wop(wop)
        self.assertEqual(decision.decision, DecisionCode.UNKNOWN_AUTHORITY)

    def test_invalid_graph_and_authority_expansion_fail_closed(self) -> None:
        for fixture in ("cycle.yaml", "authority-expansion.yaml"):
            with self.subTest(fixture=fixture):
                self.assert_decision(
                    DecisionCode.INVALID_AUTHORITY_GRAPH,
                    graph=AuthorityGraph.load(AUTHORITY_FIXTURES / fixture),
                )

    def test_authority_binding_mismatch_fails_closed(self) -> None:
        self.assert_decision(
            DecisionCode.AUTHORITY_BINDING_MISMATCH,
            expected_authority_node_id="mission",
        )

    def test_capability_outside_resolved_authority_fails_closed(self) -> None:
        wop = self.mutate_wop(
            lambda value: value["authorized_effects"][0].update(kind="publish")
        )
        decision = self.evaluate_mutated_wop(wop)
        self.assertEqual(
            decision.decision, DecisionCode.CAPABILITY_NOT_AUTHORIZED
        )

    def test_baseline_and_repository_context_mismatches_fail_closed(self) -> None:
        cases = {
            "baseline_commit": "0" * 40,
            "repository": "/wrong/repository",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                decision = self.assert_decision(
                    DecisionCode.EXECUTION_CONTEXT_MISMATCH,
                    state=self.mutate_state(**{field: value}),
                )
                self.assertIn(field, decision.reasons[0])

    def test_unauthorized_effect_fails_closed(self) -> None:
        self.assert_decision(
            DecisionCode.EFFECT_NOT_AUTHORIZED,
            state=self.mutate_state(requested_effects=["unknown-effect"]),
        )

    def test_prohibited_effect_overrides_unauthorized_effect(self) -> None:
        decision = self.assert_decision(
            DecisionCode.PROHIBITED_EFFECT_REQUESTED,
            state=self.mutate_state(requested_effects=["execute-production"]),
        )
        self.assertNotEqual(decision.decision, DecisionCode.EFFECT_NOT_AUTHORIZED)

    def test_prerequisite_and_dependency_failures(self) -> None:
        self.assert_decision(
            DecisionCode.PREREQUISITE_FAILURE,
            state=self.mutate_state(prerequisite_evidence=[]),
        )
        self.assert_decision(
            DecisionCode.DEPENDENCY_FAILURE,
            state=self.mutate_state(satisfied_dependencies=[]),
        )

    def test_expired_and_revoked_wops_fail_closed(self) -> None:
        self.assert_decision(
            DecisionCode.EXPIRED,
            reference_time=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        revocation = RevocationRecord.from_mapping(
            load_mapping(FIXTURES / "revocation-record.yaml", "revocation")
        )
        self.assert_decision(
            DecisionCode.REVOKED,
            reference_time=datetime(2026, 7, 25, 0, 45, tzinfo=timezone.utc),
            revocation=revocation,
        )

    def test_invalid_lease_and_receipt_fail_closed(self) -> None:
        invalid_lease = ExecutionLease.from_mapping(
            load_mapping(FIXTURES / "invalid-lease.yaml", "lease")
        )
        self.assert_decision(DecisionCode.INVALID_LEASE, lease=invalid_lease)
        invalid_receipt = PublicationReceipt.from_mapping(
            load_mapping(FIXTURES / "invalid-receipt.yaml", "receipt")
        )
        self.assert_decision(
            DecisionCode.INVALID_PUBLICATION_RECEIPT, receipt=invalid_receipt
        )

    def test_signature_failure_and_absence_fail_closed(self) -> None:
        self.assert_decision(
            DecisionCode.SIGNATURE_FAILURE,
            signature_verifier=RejectingSignatureVerifier(),
        )
        self.assert_decision(
            DecisionCode.SIGNATURE_FAILURE, signature_verifier=None
        )

    def test_malformed_wop_is_invalid_wop(self) -> None:
        malformed = WorkPackage.load(FIXTURES / "malformed-wop.yaml")
        decision = self.evaluate(wop=malformed)
        self.assertEqual(decision.decision, DecisionCode.INVALID_WOP)

    def test_invalid_revocation_is_validation_failure(self) -> None:
        value = dict(load_mapping(FIXTURES / "revocation-record.yaml", "revocation"))
        value["authority_node_id"] = "unpermitted"
        revocation = RevocationRecord.from_mapping(value)
        self.assert_decision(
            DecisionCode.VALIDATION_FAILURE, revocation=revocation
        )

    def test_duplicate_key_input_fails_closed_in_cli(self) -> None:
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "authority-wop-compatctl"),
                str(AUTHORITY_FIXTURES / "valid.yaml"),
                str(FIXTURES / "duplicate-key-wop.yaml"),
                str(FIXTURES / "valid-evaluation.yaml"),
                str(FIXTURES / "publication-receipt.yaml"),
                "--lease",
                str(FIXTURES / "execution-lease.yaml"),
                "--at",
                "2026-07-25T00:15:00+00:00",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            json.loads(result.stdout)["decision"], DecisionCode.VALIDATION_FAILURE.value
        )

    def test_repeated_evaluation_is_byte_equivalent_and_input_immutable(self) -> None:
        graph_before = self.graph.to_json()
        wop_before = self.wop.to_json()
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first.to_json().encode(), second.to_json().encode())
        self.assertEqual(first.input_digest, second.input_digest)
        self.assertEqual(self.graph.to_json(), graph_before)
        self.assertEqual(self.wop.to_json(), wop_before)

    def test_cli_authorizes_valid_fixture(self) -> None:
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "authority-wop-compatctl"),
                str(AUTHORITY_FIXTURES / "valid.yaml"),
                str(FIXTURES / "valid-wop.yaml"),
                str(FIXTURES / "valid-evaluation.yaml"),
                str(FIXTURES / "publication-receipt.yaml"),
                "--lease",
                str(FIXTURES / "execution-lease.yaml"),
                "--expected-authority",
                "work-package",
                "--at",
                "2026-07-25T00:15:00+00:00",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "AUTHORIZED")

    def test_fixture_matrix_names_all_required_negative_cases(self) -> None:
        matrix = load_mapping(FIXTURES / "scenarios.yaml", "scenario matrix")
        expected = {case["expected"] for case in matrix["cases"]}
        required = {code.value for code in DecisionCode}
        self.assertEqual(expected, required)


if __name__ == "__main__":
    unittest.main()
