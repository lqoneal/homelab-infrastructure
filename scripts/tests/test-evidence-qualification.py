#!/usr/bin/env python3
"""Regression tests for immutable evidence qualification."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.evidence_qualification import (
    DigestFixtureSignatureVerifier,
    EvidenceItem,
    EvidencePackage,
    QualificationContract,
    QualificationDecision,
    QualificationEngine,
    QualificationError,
    QualificationHistory,
    QualificationReport,
    canonical_json,
)
from scripts.lib.emp.wop_dispatch import ExecutionAssignment


REPOSITORY = str(ROOT)
BASELINE = "d7d65892f9f06001aa0f6d75d2dc82e00eea8d6d"
TIMESTAMP = datetime(2026, 7, 25, 3, 0, tzinfo=timezone.utc)


class EvidenceQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.history_path = Path(temporary.name) / "qualification-history.json"
        package = {
            "authority_chain": ["work-package", "mission", "governance"],
            "authorization_decision_digest": "1" * 64,
            "repository_baseline": BASELINE,
            "repository_identity": REPOSITORY,
            "mission_id": "EMP-MISSION-ZEUS-EVIDENCE-QUALIFICATION",
            "requested_capabilities": ["execute"],
            "wop_digest": "2" * 64,
            "wop_id": "WOP-623e4567-e89b-42d3-a456-426614174000",
        }
        self.assignment = ExecutionAssignment.create(
            package=package,
            intended_agent="supervised-agent-1",
            expected_evidence=("test-results", "change-report"),
            dispatch_timestamp=TIMESTAMP,
            approval_reference="APPROVAL-MISSION-L-001",
        )
        self.session = {
            "session_id": "SESSION-723e4567-e89b-42d3-a456-426614174000",
            "assignment_id": self.assignment.data["assignment_id"],
            "repository_identity": REPOSITORY,
            "baseline_commit": BASELINE,
            "execution_agent_identity": "supervised-agent-1",
            "current_execution_state": "Completed",
        }
        self.artifacts = {
            "change-report": b"bounded implementation diff",
            "test-results": b"124 tests passed",
        }
        self.contract = QualificationContract.from_mapping(
            {
                "assignment_id": self.assignment.data["assignment_id"],
                "baseline_commit": BASELINE,
                "expected_evidence": ["change-report", "test-results"],
                "mission_id": self.assignment.data["mission_id"],
                "objectives": {
                    "implementation": ["change-report"],
                    "verification": ["test-results"],
                },
                "prohibited_evidence": ["self-attestation"],
                "repository_identity": REPOSITORY,
                "required_evidence": ["change-report", "test-results"],
                "required_verification_steps": ["regression", "validators"],
                "wop_id": self.assignment.data["wop_id"],
            }
        )
        self.engine = QualificationEngine()

    def item(self, artifact_id: str, content: bytes, classification="required"):
        return EvidenceItem.create(
            artifact_identifier=artifact_id,
            artifact_type="engineering-report",
            producing_component="qualified-execution-agent",
            content=content,
            wop_objective=(
                "verification" if artifact_id == "test-results" else "implementation"
            ),
            verification_requirement=artifact_id,
            classification=classification,
        )

    def evidence_package(
        self,
        *,
        artifacts=None,
        produced=None,
        required=None,
        completion=True,
    ):
        artifacts = self.artifacts if artifacts is None else artifacts
        items = [
            self.item(artifact_id, content)
            for artifact_id, content in artifacts.items()
        ]
        return EvidencePackage.create(
            assignment=self.assignment,
            execution_session_id=self.session["session_id"],
            execution_agent_identity="supervised-agent-1",
            evidence_items=items,
            required_evidence=required
            if required is not None
            else ("change-report", "test-results"),
            produced_evidence=produced
            if produced is not None
            else tuple(artifacts),
            completion_metadata={
                "completed_verification_steps": ["regression", "validators"],
                "execution_complete": completion,
            },
            package_timestamp=TIMESTAMP,
            signature_key_id="mission-l-agent-fixture",
        )

    def qualify(
        self,
        evidence_package=None,
        *,
        artifacts=None,
        contract=None,
        session=None,
        verifier=None,
    ):
        package = evidence_package or self.evidence_package()
        return self.engine.evaluate(
            evidence_package=package,
            artifacts=self.artifacts if artifacts is None else artifacts,
            contract=contract or self.contract,
            assignment=self.assignment,
            execution_session=session or self.session,
            signature_verifier=verifier or DigestFixtureSignatureVerifier(),
        )

    def test_pass_scenario(self) -> None:
        report = self.qualify()
        self.assertEqual(report.data["qualification_decision"], "PASS")
        self.assertEqual(
            report.data["qualified_objectives"],
            ["implementation", "verification"],
        )
        self.assertEqual(report.data["missing_evidence"], [])

    def test_incomplete_missing_evidence_scenario(self) -> None:
        package = self.evidence_package(
            artifacts={"change-report": self.artifacts["change-report"]},
            produced=("change-report",),
        )
        report = self.qualify(
            package, artifacts={"change-report": self.artifacts["change-report"]}
        )
        self.assertEqual(report.data["qualification_decision"], "INCOMPLETE")
        self.assertEqual(report.data["missing_evidence"], ["test-results"])
        self.assertIn("verification", report.data["unqualified_objectives"])

    def test_fail_prohibited_evidence_scenario(self) -> None:
        artifacts = {**self.artifacts, "self-attestation": b"trust me"}
        package = self.evidence_package(artifacts=artifacts)
        report = self.qualify(package, artifacts=artifacts)
        self.assertEqual(report.data["qualification_decision"], "FAIL")
        self.assertIn("PROHIBITED_EVIDENCE_PRESENT", report.data["reason_codes"])

    def test_fail_execution_state_inconsistent(self) -> None:
        session = {**self.session, "current_execution_state": "Running"}
        report = self.qualify(session=session)
        self.assertEqual(report.data["qualification_decision"], "FAIL")
        self.assertIn("EXECUTION_STATE_INCONSISTENT", report.data["reason_codes"])

    def test_unverifiable_artifact_digest_scenario(self) -> None:
        report = self.qualify(artifacts={**self.artifacts, "test-results": b"tampered"})
        self.assertEqual(report.data["qualification_decision"], "UNVERIFIABLE")
        self.assertIn("ARTIFACT_INTEGRITY_FAILURE", report.data["reason_codes"])

    def test_unverifiable_signature_scenario(self) -> None:
        class RejectSignature:
            @staticmethod
            def verify(_package):
                return False

        report = self.qualify(verifier=RejectSignature())
        self.assertEqual(report.data["qualification_decision"], "UNVERIFIABLE")
        self.assertIn("SIGNATURE_FAILURE", report.data["reason_codes"])

    def test_unverifiable_package_checksum_scenario(self) -> None:
        value = self.evidence_package().data
        value["package_checksum"] = "0" * 64
        package = EvidencePackage(canonical_json(value))
        report = self.qualify(package)
        self.assertEqual(report.data["qualification_decision"], "UNVERIFIABLE")
        self.assertIn("PACKAGE_INTEGRITY_FAILURE", report.data["reason_codes"])

    def test_malformed_manifest_still_returns_one_unverifiable_decision(self) -> None:
        value = self.evidence_package().data
        value["evidence_manifest"] = [{"malformed": True}]
        package = EvidencePackage(canonical_json(value))
        report = self.qualify(package)
        self.assertEqual(report.data["qualification_decision"], "UNVERIFIABLE")
        self.assertIn("PACKAGE_INTEGRITY_FAILURE", report.data["reason_codes"])

    def test_all_identity_bindings_are_enforced(self) -> None:
        mutations = (
            {"assignment_id": "EA-wrong"},
            {"mission_id": "MISSION-wrong"},
            {"wop_id": "WOP-wrong"},
            {"repository_identity": "/wrong"},
            {"baseline_commit": "0" * 40},
            {"execution_session_id": "SESSION-wrong"},
            {"execution_agent_identity": "wrong-agent"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = self.evidence_package().data
                value.update(mutation)
                package = EvidencePackage(canonical_json(value))
                report = self.qualify(package)
                self.assertEqual(
                    report.data["qualification_decision"], "UNVERIFIABLE"
                )
                self.assertIn(
                    "IDENTITY_BINDING_FAILURE", report.data["reason_codes"]
                )

    def test_manifest_ordering_and_identity_are_deterministic(self) -> None:
        first = self.evidence_package(
            artifacts={
                "test-results": self.artifacts["test-results"],
                "change-report": self.artifacts["change-report"],
            }
        )
        second = self.evidence_package(
            artifacts={
                "change-report": self.artifacts["change-report"],
                "test-results": self.artifacts["test-results"],
            }
        )
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(
            [
                item["artifact_identifier"]
                for item in first.data["evidence_manifest"]
            ],
            ["change-report", "test-results"],
        )

    def test_duplicate_manifest_identity_fails(self) -> None:
        item = self.item("change-report", self.artifacts["change-report"])
        with self.assertRaisesRegex(QualificationError, "unique"):
            EvidencePackage.create(
                assignment=self.assignment,
                execution_session_id=self.session["session_id"],
                execution_agent_identity="supervised-agent-1",
                evidence_items=(item, item),
                required_evidence=("change-report",),
                produced_evidence=("change-report",),
                completion_metadata={
                    "completed_verification_steps": ["regression", "validators"],
                    "execution_complete": True,
                },
                package_timestamp=TIMESTAMP,
                signature_key_id="key",
            )

    def test_declarations_must_have_supporting_artifacts(self) -> None:
        package = self.evidence_package(
            artifacts={"change-report": self.artifacts["change-report"]},
            produced=("change-report", "test-results"),
        )
        report = self.qualify(
            package, artifacts={"change-report": self.artifacts["change-report"]}
        )
        self.assertEqual(report.data["qualification_decision"], "UNVERIFIABLE")
        self.assertIn("DECLARATION_MISMATCH", report.data["reason_codes"])

    def test_missing_verification_step_is_incomplete(self) -> None:
        package = self.evidence_package()
        value = package.data
        value["completion_metadata"]["completed_verification_steps"] = ["regression"]
        # Rebuild a valid immutable package with the reduced declaration.
        package = EvidencePackage.create(
            assignment=self.assignment,
            execution_session_id=self.session["session_id"],
            execution_agent_identity="supervised-agent-1",
            evidence_items=[
                self.item(key, content) for key, content in self.artifacts.items()
            ],
            required_evidence=("change-report", "test-results"),
            produced_evidence=("change-report", "test-results"),
            completion_metadata={
                "completed_verification_steps": ["regression"],
                "execution_complete": True,
            },
            package_timestamp=TIMESTAMP,
            signature_key_id="key",
        )
        report = self.qualify(package)
        self.assertEqual(report.data["qualification_decision"], "INCOMPLETE")
        self.assertIn("VERIFICATION_STEP_MISSING", report.data["reason_codes"])

    def test_agent_assertion_never_substitutes_for_evidence(self) -> None:
        package = self.evidence_package(
            artifacts={},
            produced=(),
            completion=True,
        )
        report = self.qualify(package, artifacts={})
        self.assertNotEqual(report.data["qualification_decision"], "PASS")
        self.assertIn("REQUIRED_EVIDENCE_MISSING", report.data["reason_codes"])

    def test_identical_input_produces_byte_identical_report(self) -> None:
        package = self.evidence_package()
        first = self.qualify(package)
        second = self.qualify(package)
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(first.to_json(), second.to_json())

    def test_report_tampering_fails(self) -> None:
        value = self.qualify().data
        value["qualification_decision"] = "FAIL"
        with self.assertRaisesRegex(QualificationError, "digest"):
            QualificationReport.from_mapping(value)

    def test_repeated_qualification_history_replays_identically(self) -> None:
        report = self.qualify()
        history = QualificationHistory(self.history_path)
        history.record(report)
        history.record(self.qualify())
        replay = history.replay(report.data["evidence_package_id"])
        self.assertEqual(len(replay), 2)
        self.assertEqual(replay[0].canonical_data, replay[1].canonical_data)
        restarted = QualificationHistory(self.history_path)
        self.assertEqual(
            restarted.replay(report.data["evidence_package_id"])[0].canonical_data,
            report.canonical_data,
        )

    def test_history_rejects_non_deterministic_requalification(self) -> None:
        report = self.qualify()
        conflicting = self.qualify(
            session={**self.session, "current_execution_state": "Running"}
        )
        history = QualificationHistory(self.history_path)
        history.record(report)
        with self.assertRaisesRegex(QualificationError, "not deterministic"):
            history.record(conflicting)
        replay = history.replay(report.data["evidence_package_id"])
        self.assertEqual(len(replay), 1)
        self.assertEqual(replay[0].canonical_data, report.canonical_data)

    def test_cli_validates_and_replays_history(self) -> None:
        report = self.qualify()
        history = QualificationHistory(self.history_path)
        history.record(report)
        command = [str(ROOT / "scripts/evidence-qualifyctl"), str(self.history_path)]
        validate = subprocess.run(
            command + ["validate"], text=True, capture_output=True
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)
        replay = subprocess.run(
            command
            + [
                "replay",
                "--package",
                report.data["evidence_package_id"],
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(
            json.loads(replay.stdout)[0]["qualification_decision"], "PASS"
        )

    def test_exact_four_decision_scenario_matrix(self) -> None:
        reports = [
            self.qualify(),
            self.qualify(
                self.evidence_package(
                    artifacts={"change-report": self.artifacts["change-report"]},
                    produced=("change-report",),
                ),
                artifacts={"change-report": self.artifacts["change-report"]},
            ),
            self.qualify(
                self.evidence_package(
                    artifacts={**self.artifacts, "self-attestation": b"trust me"}
                ),
                artifacts={**self.artifacts, "self-attestation": b"trust me"},
            ),
            self.qualify(artifacts={**self.artifacts, "test-results": b"tampered"}),
        ]
        self.assertEqual(
            sorted(report.data["qualification_decision"] for report in reports),
            sorted(decision.value for decision in QualificationDecision),
        )

    def test_no_reconciliation_closeout_execution_dispatch_or_approval_api(self) -> None:
        forbidden = {
            "reconcile",
            "close_wop",
            "complete_mission",
            "select_mission",
            "execute",
            "dispatch",
            "retry",
            "approve",
            "update_project_state",
            "update_registry",
        }
        self.assertTrue(forbidden.isdisjoint(set(dir(self.engine))))


if __name__ == "__main__":
    unittest.main()
