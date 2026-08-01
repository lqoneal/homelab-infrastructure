"""Regression coverage for OA-26 evidence-calculated completion."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.emp.oa26_cap026_verification import (
    CompletionDeterminationError,
    OBJECTIVE,
    determine_completion,
)


class CompletionDeterminationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = {
            "schema_version": 1, "mission_id": "OA-26", "gate_id": "OA-26",
            "objective": OBJECTIVE, "wop_id": "WOP-OA-26-EXECUTION-001",
            "repository_identity": "/repo", "baseline_commit": "a" * 40,
            "authority_source": "MKM/PMCT/OA-26-GATE",
            "execution_identity": "EXEC-001", "agent_identity": "QUALIFIER-001",
            "assertions": {
                "authority_binding": "PASS", "repository_binding": "PASS",
                "baseline_binding": "PASS", "positive_completion": "PASS",
                "negative_fail_closed": "PASS", "replay_stability": "PASS",
                "interruption_recovery": "PASS", "acceptance_separation": "PASS",
            },
            "evidence_manifest_digest": "b" * 64,
        }

    def test_completion_is_calculated_before_acceptance(self) -> None:
        result = determine_completion(self.evidence)
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["acceptance_status"], "PENDING")
        self.assertTrue(result["completion_is_distinct_from_acceptance"])

    def test_invalid_evidence_fails_closed(self) -> None:
        malformed = dict(self.evidence)
        malformed["assertions"] = dict(self.evidence["assertions"])
        malformed["assertions"]["positive_completion"] = "FAIL"
        with self.assertRaises(CompletionDeterminationError):
            determine_completion(malformed)


if __name__ == "__main__":
    unittest.main()
