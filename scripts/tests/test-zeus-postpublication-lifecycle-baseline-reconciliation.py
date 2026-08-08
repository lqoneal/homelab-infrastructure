#!/usr/bin/env python3
"""Focused deterministic tests for the durable reconciliation receipt."""

from __future__ import annotations

import json
import subprocess
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
                 patch.object(reconciliation, "resolve_commit_lineage", return_value=lineage), \
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
                 patch.object(reconciliation, "resolve_commit_lineage", return_value=lineage), \
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

    def test_live_projection_resolves_without_a_new_reconciliation_receipt(self):
        live = {
            "result": "PASS",
            "provenance_baseline": "1" * 40,
            "current_published_baseline": "a" * 40,
            "baseline_relationship": "ANCESTOR",
            "errors": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(reconciliation, "_current_records", return_value=[]), \
                 patch.object(reconciliation, "resolve_provenance_lineage", return_value=live), \
                 patch.object(reconciliation, "resolve_baseline", return_value={"result": "PASS", "eos_baseline": "a" * 40}):
                value = reconciliation.verify_current(
                    "/repo", Path(temporary),
                    expected={"mission_id": "MISSION-TEST-01", "receipt_provenance_baseline": "1" * 40},
                    current_published_baseline="a" * 40,
                )
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "LIVE_PROJECTION")
        self.assertEqual(value["current_receipt_count"], 0)

    def test_stale_receipt_is_supplemental_when_live_baseline_is_a_descendant(self):
        live = {"result": "PASS", "baseline_relationship": "ANCESTOR", "errors": []}
        historical = {
            "result": "PASS",
            "classification": "HISTORICAL_SUPPLEMENTAL",
            "recorded_baseline": "b" * 40,
            "lineage": {"result": "PASS"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(reconciliation, "_current_records", return_value=[(Path(temporary) / "old.json", {"receipt_digest": "d" * 64})]), \
                 patch.object(reconciliation, "resolve_provenance_lineage", return_value=live), \
                 patch.object(reconciliation, "resolve_baseline", return_value={"result": "PASS", "eos_baseline": "a" * 40}), \
                 patch.object(reconciliation, "_verify_record", return_value=historical):
                value = reconciliation.verify_current(
                    "/repo", Path(temporary),
                    expected={"mission_id": "MISSION-TEST-01", "receipt_provenance_baseline": "1" * 40},
                    current_published_baseline="a" * 40,
                )
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "LIVE_PROJECTION")
        self.assertEqual(value["historical_receipt_count"], 1)
        self.assertEqual(value["latest_historical_baseline"], "b" * 40)

    def test_duplicate_current_receipts_fail_closed(self):
        live = {"result": "PASS", "baseline_relationship": "IDENTICAL", "errors": []}
        current = {
            "result": "PASS",
            "classification": "CURRENT_CANONICAL",
            "recorded_baseline": "a" * 40,
            "lineage": {"result": "PASS"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            records = [(Path(temporary) / "one.json", {}), (Path(temporary) / "two.json", {})]
            with patch.object(reconciliation, "_current_records", return_value=records), \
                 patch.object(reconciliation, "resolve_provenance_lineage", return_value=live), \
                 patch.object(reconciliation, "resolve_baseline", return_value={"result": "PASS", "eos_baseline": "a" * 40}), \
                 patch.object(reconciliation, "_verify_record", return_value=current):
                with self.assertRaisesRegex(reconciliation.LifecycleBaselineReconciliationError, "more than one current"):
                    reconciliation.verify_current(
                        "/repo", Path(temporary),
                        expected={"mission_id": "MISSION-TEST-01", "receipt_provenance_baseline": "1" * 40},
                        current_published_baseline="a" * 40,
                    )

    def test_three_sequential_publications_resolve_without_receipt_editing(self):
        root = Path(__file__).resolve().parents[2]
        commits = [
            subprocess.check_output(["git", "-C", str(root), "rev-parse", ref], text=True).strip()
            for ref in ("32796dffb43a47f4f9516a0936fe89f0bec0ee80", "7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c", "4305b95216ca4022e176e00922ecb50fae318dec", "HEAD")
        ]
        for provenance, target in zip(commits, commits[1:]):
            value = reconciliation.resolve_commit_lineage(root, provenance, target)
            self.assertEqual(value["result"], "PASS")
            self.assertIn(value["baseline_relationship"], {"IDENTICAL", "ANCESTOR"})


if __name__ == "__main__":
    unittest.main()
