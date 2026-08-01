"""Regression coverage for OA-27 exact-result operator decisions."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.emp.oa27_cap027_verification import (  # noqa: E402
    OperatorAcceptanceError,
    bind_decision,
)


class OperatorAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decision = {
            "schema_version": 1, "mission_id": "OA-27", "gate_id": "OA-27",
            "decision": "ACCEPT", "operator": "operator-1",
            "decided_at": "2026-08-01T00:00:00Z", "qualified_result": "PASS",
            "evidence_manifest_digest": "a" * 64, "repository_identity": "/repo",
            "baseline_commit": "b" * 40, "authority_source": "MKM/PMCT/OA-27-GATE",
            "execution_identity": "EXEC-027", "agent_identity": "QUALIFIER-027",
        }

    def test_exact_result_decision_is_bound(self) -> None:
        result = bind_decision(self.decision)
        self.assertEqual(result["decision_status"], "ACCEPTED")
        self.assertTrue(result["acceptance_is_explicit"])

    def test_malformed_or_mismatched_decisions_fail_closed(self) -> None:
        for key, value in (("qualified_result", "FAIL"), ("decision", "MAYBE"), ("gate_id", "OA-28")):
            candidate = dict(self.decision)
            candidate[key] = value
            with self.subTest(key=key):
                with self.assertRaises(OperatorAcceptanceError):
                    bind_decision(candidate)


if __name__ == "__main__":
    unittest.main()
