#!/usr/bin/env python3
"""Regression tests for Zeus Work Initiation Enforcement Mode."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.authority.engine import AuthorityGraph  # noqa: E402
from scripts.lib.authority_wop.compatibility import DecisionCode  # noqa: E402
from scripts.lib.work_initiation.shadow import ShadowAuthorizationService  # noqa: E402
from scripts.lib.wop.contract import (  # noqa: E402
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    RevocationRecord,
    WorkPackage,
    load_mapping,
)


FIXTURES = ROOT / "engineering" / "authorization" / "fixtures"
AUTHORITY = ROOT / "engineering" / "authority" / "fixtures"
NOW = datetime(2026, 7, 25, 0, 15, tzinfo=timezone.utc)
BASELINE = "a99de6f4cfd252c88a2d98184833be27877bab2c"


class RejectingVerifier:
    def verify(self, algorithm, key_id, signature, payload_digest):
        return False


class WorkInitiationEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ShadowAuthorizationService()
        self.graph = AuthorityGraph.load(AUTHORITY / "valid.yaml")
        self.wop = WorkPackage.load(FIXTURES / "enforcement-wop.yaml")
        self.state = EvaluationState.from_mapping(
            load_mapping(FIXTURES / "enforcement-evaluation.yaml", "evaluation")
        )
        self.receipt = PublicationReceipt.from_mapping(
            load_mapping(FIXTURES / "enforcement-receipt.yaml", "receipt")
        )
        self.lease = ExecutionLease.from_mapping(
            load_mapping(FIXTURES / "enforcement-lease.yaml", "lease")
        )

    def evaluate(self, legacy_authorized=False, mode="enforcement", **overrides):
        arguments = {
            "graph": self.graph,
            "wop": self.wop,
            "state": self.state,
            "receipt": self.receipt,
            "lease": self.lease,
            "reference_time": NOW,
            "legacy_authorized": legacy_authorized,
            "repository_identity": str(ROOT),
            "repository_baseline_commit": BASELINE,
            "expected_authority_node_id": "work-package",
            "enforcement_mode": mode,
        }
        arguments.update(overrides)
        return self.service.evaluate(**arguments)

    def mutate_state(self, **changes):
        value = dict(
            load_mapping(FIXTURES / "enforcement-evaluation.yaml", "evaluation")
        )
        value.update(changes)
        return EvaluationState.from_mapping(value)

    def mutate_wop(self, mutate):
        value = copy.deepcopy(self.wop.to_mapping())
        mutate(value)
        value["payload_digest"] = "0" * 64
        value["signature"]["value"] = "0" * 64
        digest = WorkPackage.from_mapping(value).calculated_digest()
        value["payload_digest"] = digest
        value["signature"]["value"] = digest
        wop = WorkPackage.from_mapping(value)
        receipt_value = dict(
            load_mapping(FIXTURES / "enforcement-receipt.yaml", "receipt")
        )
        receipt_value["payload_digest"] = digest
        lease_value = dict(
            load_mapping(FIXTURES / "enforcement-lease.yaml", "lease")
        )
        lease_value["payload_digest"] = digest
        return (
            wop,
            PublicationReceipt.from_mapping(receipt_value),
            ExecutionLease.from_mapping(lease_value),
        )

    def test_zeus_allow_overrides_legacy_deny(self) -> None:
        data = self.evaluate(legacy_authorized=False).data
        self.assertEqual(data["zeus_authorization_decision"], "AUTHORIZED")
        self.assertEqual(data["legacy_comparison_result"], "REJECTED")
        self.assertEqual(data["enforcement_decision"], "AUTHORIZED")
        self.assertEqual(data["authoritative_decision_source"], "ZEUS")
        self.assertEqual(data["enforcement_mode"], "ENFORCEMENT")
        self.assertEqual(data["schema_version"], 2)
        self.assertFalse(data["shadow_only"])

    def test_legacy_allow_cannot_override_zeus_denial(self) -> None:
        state = self.mutate_state(requested_effects=["execute-wop"])
        data = self.evaluate(legacy_authorized=True, state=state).data
        self.assertEqual(
            data["zeus_authorization_decision"], "PROHIBITED_EFFECT_REQUESTED"
        )
        self.assertEqual(data["legacy_comparison_result"], "AUTHORIZED")
        self.assertEqual(data["enforcement_decision"], "REJECTED")
        self.assertEqual(data["authoritative_decision_source"], "ZEUS")

    def test_missing_wop_fails_closed(self) -> None:
        data = self.service.validation_failure(
            reason="missing WOP",
            reference_time=NOW,
            legacy_authorized=True,
            repository_identity=str(ROOT),
            repository_baseline_commit=BASELINE,
            enforcement_mode="enforcement",
        ).data
        self.assertEqual(data["zeus_authorization_decision"], "VALIDATION_FAILURE")
        self.assertEqual(data["enforcement_decision"], "REJECTED")

    def test_unknown_authority_and_invalid_graph_fail_closed(self) -> None:
        wop, receipt, lease = self.mutate_wop(
            lambda value: value["authority_binding"].update(
                authority_node_id="unknown"
            )
        )
        unknown = self.evaluate(wop=wop, receipt=receipt, lease=lease).data
        self.assertEqual(unknown["zeus_authorization_decision"], "UNKNOWN_AUTHORITY")
        self.assertEqual(unknown["enforcement_decision"], "REJECTED")
        invalid = self.evaluate(
            graph=AuthorityGraph.load(AUTHORITY / "cycle.yaml")
        ).data
        self.assertEqual(
            invalid["zeus_authorization_decision"], "INVALID_AUTHORITY_GRAPH"
        )
        self.assertEqual(invalid["enforcement_decision"], "REJECTED")

    def test_observed_repository_and_baseline_mismatch_fail_closed(self) -> None:
        for field, value in (
            ("repository_identity", "/wrong/repository"),
            ("repository_baseline_commit", "0" * 40),
        ):
            with self.subTest(field=field):
                data = self.evaluate(**{field: value}).data
                self.assertEqual(
                    data["zeus_authorization_decision"],
                    "EXECUTION_CONTEXT_MISMATCH",
                )
                self.assertEqual(data["enforcement_decision"], "REJECTED")

    def test_capability_and_effect_boundaries_fail_closed(self) -> None:
        wop, receipt, lease = self.mutate_wop(
            lambda value: value["authorized_effects"][0].update(kind="publish")
        )
        capability = self.evaluate(wop=wop, receipt=receipt, lease=lease).data
        self.assertEqual(
            capability["zeus_authorization_decision"],
            "CAPABILITY_NOT_AUTHORIZED",
        )
        effect = self.evaluate(
            state=self.mutate_state(requested_effects=["unknown-effect"])
        ).data
        self.assertEqual(
            effect["zeus_authorization_decision"], "EFFECT_NOT_AUTHORIZED"
        )

    def test_expired_revoked_and_signature_failure_fail_closed(self) -> None:
        expired = self.evaluate(
            reference_time=datetime(2026, 9, 1, tzinfo=timezone.utc)
        ).data
        self.assertEqual(expired["zeus_authorization_decision"], "EXPIRED")
        revocation = RevocationRecord.from_mapping(
            load_mapping(FIXTURES / "enforcement-revocation.yaml", "revocation")
        )
        revoked = self.evaluate(
            reference_time=datetime(2026, 7, 25, 0, 45, tzinfo=timezone.utc),
            revocation=revocation,
        ).data
        self.assertEqual(revoked["zeus_authorization_decision"], "REVOKED")
        signature = self.evaluate(signature_verifier=RejectingVerifier()).data
        self.assertEqual(
            signature["zeus_authorization_decision"], "SIGNATURE_FAILURE"
        )
        for data in (expired, revoked, signature):
            self.assertEqual(data["enforcement_decision"], "REJECTED")

    def test_expired_lease_metadata_fails_closed(self) -> None:
        data = self.evaluate(
            reference_time=datetime(2026, 7, 25, 2, 0, tzinfo=timezone.utc)
        ).data
        self.assertEqual(data["zeus_authorization_decision"], "INVALID_LEASE")
        self.assertEqual(data["lease_status"], "INVALID_OR_ABSENT")
        self.assertEqual(data["enforcement_decision"], "REJECTED")

    def test_enforcement_adr_is_deterministic(self) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first.canonical_data.encode(), second.canonical_data.encode())
        self.assertEqual(first.data["decision_digest"], second.data["decision_digest"])

    def test_rollback_uses_legacy_allow_and_deny(self) -> None:
        legacy_allow = self.evaluate(
            legacy_authorized=True,
            mode="rollback",
            state=self.mutate_state(requested_effects=["execute-wop"]),
        ).data
        self.assertEqual(legacy_allow["enforcement_decision"], "AUTHORIZED")
        self.assertEqual(legacy_allow["authoritative_decision_source"], "LEGACY")
        self.assertEqual(legacy_allow["rollback_status"], "ACTIVE")
        legacy_deny = self.evaluate(
            legacy_authorized=False, mode="rollback"
        ).data
        self.assertEqual(legacy_deny["enforcement_decision"], "REJECTED")

    def test_default_shell_mode_fails_closed_without_wop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = f"""
set +e
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_platform_legacy_qualify() {{ return 0; }}
eos_project_root() {{ echo '{ROOT}'; }}
eos_runtime_dir() {{ echo '{directory}'; }}
unset EOS_AUTHORIZATION_MODE EOS_SHADOW_AUTHORITY_GRAPH EOS_SHADOW_WOP EOS_SHADOW_STATE EOS_SHADOW_RECEIPT
eos_platform_qualify homelab >/dev/null
test "$?" -eq 77
test "$(find '{directory}/authorization-decisions' -name 'ADR-*.json' | wc -l)" -eq 1
"""
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_default_shell_mode_zeus_allow_overrides_legacy_deny(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            current_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            wop_value = copy.deepcopy(self.wop.to_mapping())
            wop_value["execution_context"]["baseline_commit"] = current_head
            wop_value["payload_digest"] = "0" * 64
            wop_value["signature"]["value"] = "0" * 64
            digest = WorkPackage.from_mapping(wop_value).calculated_digest()
            wop_value["payload_digest"] = digest
            wop_value["signature"]["value"] = digest
            state_value = dict(
                load_mapping(FIXTURES / "enforcement-evaluation.yaml", "evaluation")
            )
            state_value["baseline_commit"] = current_head
            receipt_value = dict(
                load_mapping(FIXTURES / "enforcement-receipt.yaml", "receipt")
            )
            receipt_value["payload_digest"] = digest
            lease_value = dict(
                load_mapping(FIXTURES / "enforcement-lease.yaml", "lease")
            )
            lease_value["payload_digest"] = digest
            generated = {
                "wop.yaml": wop_value,
                "state.yaml": state_value,
                "receipt.yaml": receipt_value,
                "lease.yaml": lease_value,
            }
            for name, value in generated.items():
                (temporary / name).write_text(
                    yaml.safe_dump(value, sort_keys=False), encoding="utf-8"
                )
            script = f"""
set +e
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_platform_legacy_qualify() {{ return 9; }}
eos_project_root() {{ echo '{ROOT}'; }}
eos_runtime_dir() {{ echo '{directory}'; }}
export EOS_SHADOW_AUTHORITY_GRAPH='{AUTHORITY / "valid.yaml"}'
export EOS_SHADOW_WOP='{temporary / "wop.yaml"}'
export EOS_SHADOW_STATE='{temporary / "state.yaml"}'
export EOS_SHADOW_RECEIPT='{temporary / "receipt.yaml"}'
export EOS_SHADOW_LEASE='{temporary / "lease.yaml"}'
export EOS_SHADOW_EXPECTED_AUTHORITY='work-package'
export EOS_SHADOW_EVALUATION_TIME='2026-07-25T00:15:00+00:00'
unset EOS_AUTHORIZATION_MODE
eos_platform_qualify homelab >/dev/null
test "$?" -eq 0
"""
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_execution_or_dispatch_capability_is_introduced(self) -> None:
        source = (ROOT / "scripts/lib/work_initiation/shadow.py").read_text()
        for prohibited in ("execute_wop(", "dispatch_work(", "acquire_lease("):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
