#!/usr/bin/env python3
"""Focused deterministic tests for the durable reconciliation receipt."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import lifecycle_baseline_reconciliation as reconciliation


class LifecycleBaselineReconciliationTests(unittest.TestCase):
    def mission(self):
        return {
            "mission_id": "MISSION-TEST-01",
            "wop_id": "WOP-TEST-01",
            "submission_id": "SUBMISSION-TEST-01",
            "admission_id": "ADMISSION-TEST-01",
            "bootstrap_id": "BOOTSTRAP-TEST-01",
            "receipt_provenance_baseline": "1" * 40,
            "submission_receipt": {"id": "SUBMISSION-TEST-01", "digest": "2" * 64},
            "admission_receipt": {"id": "ADMISSION-TEST-01", "digest": "3" * 64},
            "bootstrap_receipt": {"id": "BOOTSTRAP-TEST-01", "digest": "4" * 64},
            "lifecycle_state": "AWAITING_EXECUTION_DISPATCH",
            "readiness": "READY_FOR_EXECUTION_PROVIDER",
            "eligibility": "PROVIDER_EVALUATION_PENDING",
            "next_authorized_action": "EVALUATE_EXECUTION_PROVIDER",
            "authority": {"governance_authority": "operator-submitted WOP"},
        }

    def patches(self):
        identity = {
            "repository_id": "repo-test",
            "repository_identity": "git@example/repo",
            "repository_path": "/repo",
        }
        lineage = {
            "result": "PASS",
            "provenance_baseline": "1" * 40,
            "current_published_baseline": "a" * 40,
            "baseline_relationship": "ANCESTOR",
            "errors": [],
        }
        return identity, lineage

    def test_first_reconciliation_and_exact_replay_are_idempotent(self):
        identity, lineage = self.patches()
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with patch.object(reconciliation, "resolve_repository_identity", return_value=identity), \
                 patch.object(reconciliation, "resolve_baseline", return_value={"result": "PASS", "published_head": "a" * 40, "current_head": "a" * 40, "eos_baseline": "a" * 40}), \
                 patch.object(reconciliation, "resolve_provenance_lineage", return_value=lineage), \
                 patch.object(reconciliation, "_git", side_effect=["a" * 40] * 8):
                first = reconciliation.reconcile("/repo", runtime, self.mission())
                replay = reconciliation.reconcile("/repo", runtime, self.mission())
            self.assertEqual(first["result"], "PASS")
            self.assertEqual(first["reconciliation"], "CREATED")
            self.assertEqual(replay["reconciliation"], "IDEMPOTENT")
            self.assertEqual(first["reconciliation_id"], replay["reconciliation_id"])
            self.assertEqual(first["receipt_digest"], replay["receipt_digest"])

    def test_tampered_receipt_fails_closed(self):
        identity, lineage = self.patches()
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with patch.object(reconciliation, "resolve_repository_identity", return_value=identity), \
                 patch.object(reconciliation, "resolve_baseline", return_value={"result": "PASS", "published_head": "a" * 40, "current_head": "a" * 40, "eos_baseline": "a" * 40}), \
                 patch.object(reconciliation, "resolve_provenance_lineage", return_value=lineage), \
                 patch.object(reconciliation, "_git", side_effect=["a" * 40] * 4):
                created = reconciliation.reconcile("/repo", runtime, self.mission())
            path = Path(created["receipt_path"])
            value = json.loads(path.read_text())
            value["current_published_baseline"] = "b" * 40
            with self.assertRaisesRegex(reconciliation.LifecycleBaselineReconciliationError, "digest mismatch"):
                reconciliation._verify_record(
                    value,
                    repository=Path("/repo"),
                    expected=self.mission(),
                    current_published_baseline="a" * 40,
                )


if __name__ == "__main__":
    unittest.main()
