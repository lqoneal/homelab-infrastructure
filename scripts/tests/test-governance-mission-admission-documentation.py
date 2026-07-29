#!/usr/bin/env python3
"""Qualification of the constitutional mission lifecycle documentation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = {
    "charter": ROOT / "docs/charters/CHAR-0001-ENGINEERING_CHARTER.md",
    "policy": ROOT / "docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md",
    "procedure": ROOT / "docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md",
    "control": ROOT / "docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md",
    "bootstrap": ROOT / "docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md",
    "authority": ROOT / "docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md",
    "genesis": ROOT / "docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md",
}

LIFECYCLE = (
    "Engineering Governance",
    "Manual WOP Submission",
    "Mission Admission",
    "Repository Identity Verification",
    "Repository Integrity Verification",
    "Package Integrity Verification",
    "Mission Activation",
    "Mission Contract Resolution",
    "Execution Verification",
    "Mission Execution",
)
GOVERNANCE_STATES = ("Submitted", "Admitted", "Activated", "Revoked", "Completed")
EXECUTION_STATES = (
    "Pending Verification",
    "Verification Failed",
    "Ready",
    "Executing",
    "Suspended",
    "Failed",
    "Completed",
)


def normalized(value: str) -> str:
    return " ".join(value.split())


def assert_ordered(test: unittest.TestCase, text: str, terms: tuple[str, ...]) -> None:
    cursor = -1
    for term in terms:
        position = text.find(term, cursor + 1)
        test.assertGreater(position, cursor, f"{term!r} is absent or out of order")
        cursor = position


class GovernanceMissionLifecycleDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = {
            name: path.read_text(encoding="utf-8")
            for name, path in DOCUMENTS.items()
        }

    def test_admission_is_governance_intent_only(self) -> None:
        for name in ("charter", "policy", "procedure", "control"):
            text = normalized(self.documents[name])
            self.assertIn("sole Mission Admission Authority", text)
            self.assertIn("Engineering Governance", text)
        charter = normalized(self.documents["charter"])
        self.assertIn("records Governance intent", charter)
        self.assertIn("Admission remains valid until", charter)
        for excluded_effect in (
            "repository readiness",
            "package validity",
            "execution authority",
            "activation",
            "Mission Contract resolution",
            "execution readiness",
        ):
            self.assertIn(excluded_effect, charter)

    def test_activation_is_a_separate_governance_decision(self) -> None:
        for name in ("charter", "policy", "procedure", "control"):
            text = normalized(self.documents[name])
            self.assertIn("Mission Activation Authority", text)
            self.assertIn("execution qualification", text)
        self.assertIn(
            "does not guarantee successful execution",
            normalized(self.documents["procedure"]),
        )

    def test_governance_and_execution_states_are_independent(self) -> None:
        for name in ("charter", "policy", "procedure", "control"):
            text = normalized(self.documents[name])
            for state in GOVERNANCE_STATES:
                self.assertIn(state, text)
            for state in EXECUTION_STATES:
                self.assertIn(state, text)
        procedure = normalized(self.documents["procedure"])
        self.assertIn(
            "Governance state changes only through Engineering Governance",
            procedure,
        )
        self.assertIn(
            "Execution state changes through objective execution events",
            procedure,
        )

    def test_verification_failure_blocks_execution_and_preserves_admission(self) -> None:
        procedure = normalized(self.documents["procedure"])
        control = normalized(self.documents["control"])
        self.assertIn("Mission Status: ADMITTED Execution Status: BLOCKED", procedure)
        self.assertIn("preserve the admitted mission", procedure)
        self.assertIn("without reversing or invalidating admission", control)
        self.assertIn(
            "shall never reinterpret a blocked mission as not admitted",
            procedure,
        )

    def test_blocked_mission_resumes_without_readmission(self) -> None:
        for name in ("charter", "procedure", "control"):
            self.assertIn(
                "without a new Mission Admission",
                normalized(self.documents[name]),
            )
        self.assertIn(
            "resume execution qualification",
            normalized(self.documents["control"]),
        )

    def test_canonical_lifecycle_is_ordered_consistently(self) -> None:
        for name in ("procedure", "control"):
            assert_ordered(self, normalized(self.documents[name]), LIFECYCLE)

    def test_bootstrap_is_independent_of_admission_and_activation(self) -> None:
        bootstrap = normalized(self.documents["bootstrap"])
        self.assertIn("distinct from Mission Admission", bootstrap)
        self.assertIn("Mission Activation", bootstrap)
        self.assertIn(
            "alter an existing admission or activation decision",
            bootstrap,
        )
        self.assertIn("authorize execution", bootstrap)

    def test_execution_agents_do_not_own_governance_decisions(self) -> None:
        charter = normalized(self.documents["charter"])
        policy = normalized(self.documents["policy"])
        procedure = normalized(self.documents["procedure"])
        self.assertIn("execution agent shall never activate", charter)
        self.assertIn("shall not admit, revoke, or activate missions", policy)
        self.assertIn(
            "never independently admit, revoke, or activate a mission",
            procedure,
        )

    def test_superseded_admission_semantics_are_absent(self) -> None:
        current = "\n".join(
            self.documents[name]
            for name in ("charter", "policy", "procedure", "control")
        )
        prohibited = (
            "admitted after successful objective verification",
            "verification shall result in recorded admission",
            "fail an admission verification",
            "admission denial",
            "execution-agent admission authority",
        )
        for phrase in prohibited:
            self.assertNotIn(phrase, current)


if __name__ == "__main__":
    unittest.main()
