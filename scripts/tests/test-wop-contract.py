#!/usr/bin/env python3
"""Regression tests for the immutable offline Work Package contract."""

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

from scripts.lib.wop.contract import (  # noqa: E402
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    RevocationRecord,
    WorkPackage,
    WorkPackageError,
    load_mapping,
)


FIXTURES = ROOT / "engineering" / "wop" / "fixtures"
VALID_WOP = FIXTURES / "valid-wop.yaml"
NOW = datetime(2026, 7, 25, 0, 15, tzinfo=timezone.utc)


class DigestSignatureVerifier:
    def verify(
        self, algorithm: str, key_id: str, signature: str, payload_digest: str
    ) -> bool:
        return (
            algorithm == "test-sha256"
            and key_id == "offline-test-key"
            and signature == payload_digest
        )


class WorkPackageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wop = WorkPackage.load(VALID_WOP)
        self.state = EvaluationState.from_mapping(
            load_mapping(FIXTURES / "valid-evaluation.yaml", "evaluation")
        )
        self.receipt = PublicationReceipt.from_mapping(
            load_mapping(FIXTURES / "publication-receipt.yaml", "receipt")
        )
        self.lease = ExecutionLease.from_mapping(
            load_mapping(FIXTURES / "execution-lease.yaml", "lease")
        )

    def decision(self, **overrides):
        arguments = {
            "state": self.state,
            "reference_time": NOW,
            "receipt": self.receipt,
            "lease": self.lease,
            "signature_verifier": DigestSignatureVerifier(),
        }
        arguments.update(overrides)
        return self.wop.evaluate(**arguments)

    def test_valid_contract_and_signature_validate(self) -> None:
        self.wop.validate(DigestSignatureVerifier())

    def test_model_does_not_expose_mutable_contract_state(self) -> None:
        detached = self.wop.data
        detached["authority_binding"]["authority_node_id"] = "tampered"
        self.assertEqual(
            self.wop.data["authority_binding"]["authority_node_id"], "work-package"
        )

    def test_tampering_fails_digest_validation(self) -> None:
        value = self.wop.to_mapping()
        value["execution_context"]["branch"] = "tampered"
        with self.assertRaisesRegex(
            WorkPackageError, "payload_digest does not match immutable WOP payload"
        ):
            WorkPackage.from_mapping(value).validate()

    def test_invalid_authority_binding_fails(self) -> None:
        with self.assertRaisesRegex(
            WorkPackageError, "authority_binding.authority_node_id"
        ):
            WorkPackage.load(
                FIXTURES / "invalid-authority-wop.yaml"
            ).validate()

    def test_valid_evaluation_is_allowed_and_deterministic(self) -> None:
        first = self.decision()
        second = self.decision()
        self.assertTrue(first.allowed)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first.to_mapping(), sort_keys=True),
            json.dumps(second.to_mapping(), sort_keys=True),
        )

    def test_invalid_context_is_denied(self) -> None:
        state = EvaluationState.from_mapping(
            load_mapping(
                FIXTURES / "invalid-context-evaluation.yaml", "evaluation"
            )
        )
        decision = self.decision(state=state)
        self.assertFalse(decision.allowed)
        self.assertIn("execution context mismatch: branch", decision.reasons)

    def test_malformed_context_fails_closed(self) -> None:
        value = dict(load_mapping(FIXTURES / "valid-evaluation.yaml", "evaluation"))
        value["baseline_commit"] = "short"
        with self.assertRaisesRegex(WorkPackageError, "full Git SHA"):
            EvaluationState.from_mapping(value)

    def test_unauthorized_and_prohibited_effects_are_denied(self) -> None:
        state = EvaluationState.from_mapping(
            load_mapping(
                FIXTURES / "unauthorized-effect-evaluation.yaml", "evaluation"
            )
        )
        decision = self.decision(state=state)
        self.assertFalse(decision.allowed)
        self.assertIn(
            "unauthorized effects requested: deploy-service",
            decision.reasons,
        )
        self.assertIn("prohibited effects requested: deploy-service", decision.reasons)

    def test_unsatisfied_prerequisites_and_dependencies_are_denied(self) -> None:
        state = EvaluationState.from_mapping(
            load_mapping(FIXTURES / "unsatisfied-evaluation.yaml", "evaluation")
        )
        decision = self.decision(state=state)
        self.assertFalse(decision.allowed)
        self.assertTrue(
            any(reason.startswith("unsatisfied prerequisites:") for reason in decision.reasons)
        )
        self.assertTrue(
            any(reason.startswith("unsatisfied dependencies:") for reason in decision.reasons)
        )

    def test_expired_contract_is_denied(self) -> None:
        decision = self.decision(
            reference_time=datetime(2026, 9, 1, tzinfo=timezone.utc)
        )
        self.assertFalse(decision.allowed)
        self.assertIn("WOP is expired", decision.reasons)

    def test_revoked_contract_is_denied(self) -> None:
        revocation = RevocationRecord.from_mapping(
            load_mapping(FIXTURES / "revocation-record.yaml", "revocation")
        )
        decision = self.decision(
            reference_time=datetime(2026, 7, 25, 0, 45, tzinfo=timezone.utc),
            revocation=revocation,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("WOP is revoked", decision.reasons)

    def test_missing_or_excessive_lease_is_denied(self) -> None:
        missing = self.decision(lease=None)
        self.assertIn("required execution lease is absent", missing.reasons)
        value = dict(load_mapping(FIXTURES / "execution-lease.yaml", "lease"))
        value["expires_at"] = "2026-07-25T02:02:00+00:00"
        excessive = self.decision(lease=ExecutionLease.from_mapping(value))
        self.assertIn("execution lease exceeds maximum duration", excessive.reasons)

    def test_mismatched_receipt_fails_closed(self) -> None:
        value = dict(load_mapping(FIXTURES / "publication-receipt.yaml", "receipt"))
        value["wop_id"] = "WOP-123e4567-e89b-42d3-a456-426614174099"
        decision = self.decision(receipt=PublicationReceipt.from_mapping(value))
        self.assertFalse(decision.allowed)
        self.assertIn(
            "publication receipt does not bind to immutable WOP", decision.reasons
        )

    def test_signature_interface_fails_closed(self) -> None:
        class RejectingVerifier:
            def verify(self, algorithm, key_id, signature, payload_digest):
                return False

        with self.assertRaisesRegex(WorkPackageError, "signature verification failed"):
            self.wop.validate(RejectingVerifier())

    def test_serialization_is_deterministic_and_round_trips(self) -> None:
        self.assertEqual(self.wop.to_json(), self.wop.to_json())
        self.assertEqual(self.wop.to_yaml(), self.wop.to_yaml())
        round_trip = WorkPackage.from_mapping(json.loads(self.wop.to_json()))
        self.assertEqual(round_trip.to_json(), self.wop.to_json())
        self.assertEqual(round_trip.calculated_digest(), self.wop.calculated_digest())

    def test_conflicting_effect_manifest_fails(self) -> None:
        value = copy.deepcopy(self.wop.to_mapping())
        value["prohibited_effects"].append("inspect-repository")
        value["payload_digest"] = "0" * 64
        errors = WorkPackage.from_mapping(value).validation_errors()
        self.assertIn(
            "effects cannot be both authorized and prohibited: inspect-repository",
            errors,
        )

    def test_cli_validate_and_evaluate(self) -> None:
        validate = subprocess.run(
            [str(ROOT / "scripts" / "wopctl"), "validate", str(VALID_WOP)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)
        evaluate = subprocess.run(
            [
                str(ROOT / "scripts" / "wopctl"),
                "evaluate",
                str(VALID_WOP),
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
        self.assertEqual(evaluate.returncode, 0, evaluate.stderr)
        self.assertTrue(json.loads(evaluate.stdout)["allowed"])


if __name__ == "__main__":
    unittest.main()
