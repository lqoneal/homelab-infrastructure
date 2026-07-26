#!/usr/bin/env python3
"""Regression tests for Work Initiation Shadow Authorization Mode."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.authority.engine import AuthorityGraph  # noqa: E402
from scripts.lib.work_initiation.shadow import ShadowAuthorizationService  # noqa: E402
from scripts.lib.wop.contract import (  # noqa: E402
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    WorkPackage,
    load_mapping,
)


COMPATIBILITY = ROOT / "engineering" / "compatibility" / "fixtures"
AUTHORITY = ROOT / "engineering" / "authority" / "fixtures" / "valid.yaml"
QUALIFICATION = (
    ROOT
    / "engineering"
    / "authorization"
    / "fixtures"
    / "qualification-scenarios.yaml"
)
NOW = datetime(2026, 7, 25, 0, 15, tzinfo=timezone.utc)


class WorkInitiationShadowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ShadowAuthorizationService()
        self.graph = AuthorityGraph.load(AUTHORITY)
        self.wop = WorkPackage.load(COMPATIBILITY / "valid-wop.yaml")
        self.state = EvaluationState.from_mapping(
            load_mapping(COMPATIBILITY / "valid-evaluation.yaml", "evaluation")
        )
        self.receipt = PublicationReceipt.from_mapping(
            load_mapping(
                COMPATIBILITY / "publication-receipt.yaml", "publication receipt"
            )
        )
        self.lease = ExecutionLease.from_mapping(
            load_mapping(COMPATIBILITY / "execution-lease.yaml", "execution lease")
        )

    def evaluate(self, legacy_authorized=True, state=None):
        return self.service.evaluate(
            graph=self.graph,
            wop=self.wop,
            state=state or self.state,
            receipt=self.receipt,
            lease=self.lease,
            reference_time=NOW,
            legacy_authorized=legacy_authorized,
            repository_identity=str(ROOT),
            repository_baseline_commit="3e1e34904700e688eba801502e114a677fd8a724",
            expected_authority_node_id="work-package",
        )

    def test_agreement_record_is_complete_and_legacy_enforced(self) -> None:
        record = self.evaluate().data
        required = {
            "evaluation_id",
            "evaluation_timestamp",
            "repository_identity",
            "repository_baseline_commit",
            "authority_node",
            "authority_chain",
            "mission",
            "phase",
            "work_item",
            "wop_id",
            "execution_context",
            "requested_capabilities",
            "resolved_capabilities",
            "authorized_effects",
            "prohibited_effects",
            "prerequisite_evaluation",
            "dependency_evaluation",
            "lease_status",
            "receipt_status",
            "signature_status",
            "legacy_authorization_decision",
            "zeus_authorization_decision",
            "agreement_status",
            "disagreement_classification",
            "first_divergent_decision_point",
            "structured_reason_code",
            "decision_digest",
            "software_versions",
        }
        self.assertTrue(required <= set(record))
        self.assertEqual(record["agreement_status"], "AGREEMENT")
        self.assertEqual(record["zeus_authorization_decision"], "AUTHORIZED")
        self.assertEqual(record["enforcement_authority"], "LEGACY")
        self.assertEqual(record["enforcement_decision"], "AUTHORIZED")
        self.assertTrue(record["shadow_only"])

    def test_legacy_deny_zeus_allow_is_observational(self) -> None:
        record = self.evaluate(legacy_authorized=False).data
        self.assertEqual(record["agreement_status"], "DISAGREEMENT")
        self.assertEqual(
            record["disagreement_classification"], "LEGACY_DENY_ZEUS_ALLOW"
        )
        self.assertEqual(record["enforcement_decision"], "REJECTED")
        self.assertEqual(record["zeus_authorization_decision"], "AUTHORIZED")

    def test_legacy_allow_zeus_deny_is_observational(self) -> None:
        value = dict(load_mapping(COMPATIBILITY / "valid-evaluation.yaml", "evaluation"))
        value["requested_effects"] = ["execute-production"]
        state = EvaluationState.from_mapping(value)
        record = self.evaluate(state=state).data
        self.assertEqual(
            record["disagreement_classification"], "LEGACY_ALLOW_ZEUS_DENY"
        )
        self.assertEqual(
            record["first_divergent_decision_point"],
            "PROHIBITED_EFFECT_REQUESTED",
        )
        self.assertEqual(record["enforcement_decision"], "AUTHORIZED")

    def test_identical_inputs_produce_identical_records_and_digests(self) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(
            first.data["decision_digest"], second.data["decision_digest"]
        )
        self.assertEqual(first.data["evaluation_id"], second.data["evaluation_id"])

    def test_immutable_record_persistence_is_idempotent(self) -> None:
        record = self.evaluate()
        with tempfile.TemporaryDirectory() as directory:
            first = record.persist(directory)
            second = record.persist(directory)
            self.assertEqual(first, second)
            self.assertEqual(first.read_text(encoding="utf-8"), record.to_json())

    def test_missing_wop_fails_closed_but_preserves_legacy_allow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    str(ROOT / "scripts" / "work-initiation-shadow"),
                    "--repository",
                    str(ROOT),
                    "--legacy-decision",
                    "authorized",
                    "--output-directory",
                    directory,
                    "--at",
                    "2026-07-25T00:15:00+00:00",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            record = json.loads(Path(summary["adr"]).read_text(encoding="utf-8"))
            self.assertEqual(record["zeus_authorization_decision"], "VALIDATION_FAILURE")
            self.assertEqual(record["enforcement_decision"], "AUTHORIZED")

    def test_cli_valid_evaluation_retains_adr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    str(ROOT / "scripts" / "work-initiation-shadow"),
                    "--repository",
                    str(ROOT),
                    "--legacy-decision",
                    "authorized",
                    "--output-directory",
                    directory,
                    "--at",
                    "2026-07-25T00:15:00+00:00",
                    "--authority-graph",
                    str(AUTHORITY),
                    "--wop",
                    str(COMPATIBILITY / "valid-wop.yaml"),
                    "--state",
                    str(COMPATIBILITY / "valid-evaluation.yaml"),
                    "--receipt",
                    str(COMPATIBILITY / "publication-receipt.yaml"),
                    "--lease",
                    str(COMPATIBILITY / "execution-lease.yaml"),
                    "--expected-authority",
                    "work-package",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["shadow_decision"], "AUTHORIZED")
            self.assertEqual(summary["agreement"], "AGREEMENT")
            self.assertTrue(Path(summary["adr"]).is_file())

    def test_shell_wrapper_returns_legacy_denial_after_shadow_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = f"""
set +e
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_platform_legacy_qualify() {{ return 7; }}
eos_project_root() {{ echo '{ROOT}'; }}
eos_runtime_dir() {{ echo '{directory}'; }}
eos_platform_qualify homelab
status=$?
test "$status" -eq 7
test "$(find '{directory}/authorization-decisions' -type f | wc -l)" -eq 1
"""
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_shadow_record_failure_cannot_change_legacy_allow(self) -> None:
        script = f"""
set +e
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_platform_legacy_qualify() {{ return 0; }}
eos_project_root() {{ echo '{ROOT}'; }}
eos_runtime_dir() {{ echo '/dev/null/not-writable'; }}
eos_platform_qualify homelab >/dev/null 2>&1
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

    def test_repository_resume_and_derived_state_are_not_authority_inputs(self) -> None:
        record = self.service.validation_failure(
            reason="no valid WOP",
            reference_time=NOW,
            legacy_authorized=True,
            repository_identity=str(ROOT),
            repository_baseline_commit="3e1e34904700e688eba801502e114a677fd8a724",
        ).data
        self.assertEqual(record["zeus_authorization_decision"], "VALIDATION_FAILURE")
        self.assertNotIn("resume", record["requested_capabilities"])
        self.assertEqual(record["authority_chain"], [])

    def test_qualification_matrix_has_two_agreements_and_two_disagreements(
        self,
    ) -> None:
        matrix = load_mapping(QUALIFICATION, "qualification scenarios")
        results = []
        for scenario in matrix["scenarios"]:
            state = self.state
            if scenario["requested_effects"] != ["verify-compatibility"]:
                value = dict(
                    load_mapping(
                        COMPATIBILITY / "valid-evaluation.yaml", "evaluation"
                    )
                )
                value["requested_effects"] = scenario["requested_effects"]
                state = EvaluationState.from_mapping(value)
            record = self.evaluate(
                legacy_authorized=scenario["legacy_authorized"], state=state
            ).data
            self.assertEqual(
                record["agreement_status"], scenario["expected_agreement"]
            )
            results.append(record["agreement_status"])
        self.assertEqual(results.count("AGREEMENT"), 2)
        self.assertEqual(results.count("DISAGREEMENT"), 2)


if __name__ == "__main__":
    unittest.main()
