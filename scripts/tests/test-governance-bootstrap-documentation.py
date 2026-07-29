#!/usr/bin/env python3
"""Qualification of the consultation-only Governance Bootstrap model."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = {
    "charter": ROOT / "docs/charters/CHAR-0001-ENGINEERING_CHARTER.md",
    "policy": ROOT / "docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md",
    "execution": ROOT / "docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md",
    "governance": ROOT / "docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md",
    "control": ROOT / "docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md",
    "bootstrap": ROOT / "docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md",
    "authority": ROOT / "docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md",
    "genesis": ROOT / "docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md",
}


def normalized(value: str) -> str:
    return " ".join(value.split())


class GovernanceBootstrapDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = {
            name: path.read_text(encoding="utf-8")
            for name, path in DOCUMENTS.items()
        }
        cls.current = "\n".join(cls.documents.values())
        cls.normalized = normalized(cls.current)

    def test_constitutional_ownership_is_explicit(self) -> None:
        self.assertIn("owner: Engineering Governance", self.documents["charter"])
        self.assertIn("owner: Engineering Governance", self.documents["policy"])
        self.assertIn("owner: Engineering Governance", self.documents["execution"])
        self.assertIn("owner: Engineering Governance", self.documents["governance"])
        self.assertIn("owner: Engineering Governance", self.documents["genesis"])
        self.assertIn("owner: Lawrence O'Neal", self.documents["bootstrap"])
        self.assertIn(
            "authority_domain: Engineering Governance",
            self.documents["bootstrap"],
        )
        self.assertIn("owner: EOS Program", self.documents["control"])
        self.assertIn("owner: EOS Program", self.documents["authority"])
        self.assertIn(
            "No subordinate record",
            self.documents["authority"],
        )
        self.assertIn(
            "No subordinate controlled document may conflict with this Charter",
            self.documents["charter"],
        )

    def test_bootstrap_is_detection_suspension_and_consultation(self) -> None:
        for concept in (
            "Governance Bootstrap Condition",
            "suspend execution",
            "Bootstrap Detection Report",
            "Engineering Governance verification",
            "GOVERNANCE_CORRECTION_REQUIRED",
            "controlled-document revision",
            "normal Mission Contract resolution",
        ):
            self.assertIn(concept, self.normalized)
        self.assertIn(
            "detection and consultation condition only",
            normalized(self.documents["charter"]),
        )
        self.assertIn(
            "consultation grants no execution authority",
            normalized(self.documents["policy"]).lower(),
        )

    def test_bootstrap_returns_only_through_normal_authority(self) -> None:
        bootstrap = normalized(self.documents["bootstrap"])
        execution = normalized(self.documents["execution"])
        self.assertIn("re-run normal authority resolution", bootstrap)
        self.assertIn(
            "normal Mission Contract resolution independently succeeds",
            execution,
        )
        self.assertIn("If authority resolves, continue normal execution.", bootstrap)

    def test_bootstrap_cannot_change_mission_governance_or_authorize_execution(self) -> None:
        bootstrap = normalized(self.documents["bootstrap"])
        self.assertIn("distinct from Mission Admission", bootstrap)
        self.assertIn("Mission Activation", bootstrap)
        self.assertIn(
            "alter an existing admission or activation decision",
            bootstrap,
        )
        self.assertIn("authorize execution", bootstrap)
        self.assertIn(
            "cannot substitute for controlled-document revision, Mission Admission, "
            "Mission Activation, or Mission Contract resolution",
            normalized(self.documents["genesis"]),
        )

    def test_no_alternate_bootstrap_authority_path_remains(self) -> None:
        prohibited = (
            "BOOTSTRAP_CONFIRMED",
            "BOOTSTRAP_NOT_CONFIRMED",
            "activate only the bounded bootstrap",
            "bootstrap authority restores",
            "time-limited bootstrap authority",
            "bootstrap activation",
        )
        for phrase in prohibited:
            self.assertNotIn(phrase, self.current)


if __name__ == "__main__":
    unittest.main()
