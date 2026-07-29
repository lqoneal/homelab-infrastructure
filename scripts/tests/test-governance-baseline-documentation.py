#!/usr/bin/env python3
"""Qualification of the Operational Alpha Governance Baseline and freeze."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md"
STABILIZATION = ROOT / "docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md"
BASELINE = ROOT / "docs/project/milestones/2026-07-29-operational-alpha-governance-baseline-1.0.md"
INDEX = ROOT / "docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md"
VERIFY = ROOT / "scripts/verify.sh"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class GovernanceBaselineDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = normalized(POLICY)
        cls.stabilization = normalized(STABILIZATION)
        cls.baseline = normalized(BASELINE)
        cls.index = normalized(INDEX)
        cls.verify = VERIFY.read_text(encoding="utf-8")

    def test_baseline_is_identified_registered_and_pending_publication(self) -> None:
        self.assertIn("GOVERNANCE-BASELINE-OA-1.0", self.baseline)
        self.assertIn("document_id: MILESTONE-0009", self.baseline)
        self.assertIn("MILESTONE-0009", self.index)
        self.assertIn("persistence_status: Pending", self.baseline)
        self.assertIn("publication remain pending", self.baseline)

    def test_governance_freeze_directs_operational_consumption(self) -> None:
        self.assertIn("Governance operates as maintained operational infrastructure", self.policy)
        self.assertIn("shall consume constitutional governance", self.policy)
        self.assertIn("requires explicit Engineering Governance authorization", self.policy)
        for priority in (
            "Zeus Operational Alpha",
            "Engineering Management Platform",
            "Engineering Event and Notification Service",
            "mission execution",
            "operational capabilities",
        ):
            self.assertIn(priority, self.baseline)

    def test_constitutional_revision_updates_three_surfaces(self) -> None:
        for text in (self.policy, self.stabilization, self.baseline):
            self.assertIn("controlled documentation", text)
            self.assertIn("governance documentation qualification", text)
            self.assertIn("standard verification workflow", text)
        self.assertIn("blocks publication and baseline designation", self.stabilization)

    def test_standard_workflow_invokes_all_governance_documentation_tests(self) -> None:
        governance_tests = sorted(
            path.name
            for path in (ROOT / "scripts/tests").glob(
                "test-governance-*-documentation.py"
            )
        )
        self.assertTrue(governance_tests)
        for test_name in governance_tests:
            self.assertIn(test_name, self.verify)

    def test_standard_workflow_keeps_core_document_qualification_mandatory(self) -> None:
        for qualification in (
            "validate_controlled_documents.py",
            "test-controlled-document-relationships.py",
            "test-controlled-document-semantic-validation.py",
            "test-governance-bootstrap-documentation.py",
            "test-governance-mission-admission-documentation.py",
            "test-governance-baseline-documentation.py",
        ):
            self.assertIn(qualification, self.verify)


if __name__ == "__main__":
    unittest.main()
