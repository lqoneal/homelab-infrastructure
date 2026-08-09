#!/usr/bin/env python3
"""Regression coverage for transaction-scoped Publication Cohort revalidation."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import publication_candidate_authority as candidate_authority
from scripts.lib.emp import publication_cohort
from scripts.lib.emp import publication_transaction
from scripts.lib.emp.production_execution import atomic_write


MISSION = "ZEUS-TEST-TRANSACTION-COHORT-01"
WOP = "WOP-ZEUS-TEST-TRANSACTION-COHORT-001"


class TransactionCohortRevalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.root = base / "repo"
        self.runtime = base / "runtime"
        self.root.mkdir()
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Zeus Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "zeus@example.invalid"], check=True)
        (self.root / "README.md").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "baseline"], check=True)
        head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        self.projection = {
            "result": "PASS", "repository_id": "repo-transaction-cohort",
            "repository_root": str(self.root), "head": head, "origin_main": head,
            "eos_baseline": head, "eos_parity": True, "index_clean": True,
            "staged_paths": [], "unstaged_paths": [], "untracked_paths": [],
        }
        self.live = {"result": "PASS", "mission_id": MISSION, "wop_id": WOP,
                     "submission_id": "SUBMISSION-1", "admission_id": "ADMISSION-1",
                     "bootstrap_id": "BOOTSTRAP-1", "lifecycle_state": "READY",
                     "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}
        self.manifest = self._manifest("member", "scripts/member.py", "QUALIFIED")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _manifest(self, name: str, path: str, qualification: str = "QUALIFIED") -> Path:
        package = self.root / "engineering" / "evidence" / name
        package.mkdir(parents=True, exist_ok=True)
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"{name}:{path}\n", encoding="utf-8")
        manifest = package / "PUBLICATION-CANDIDATE-MANIFEST.md"
        manifest.write_text(
            "---\n"
            f"mission_id: {MISSION}\n"
            f"wop_id: {WOP}\n"
            f"qualification_state: {qualification}\n"
            "publication_state: NOT_PERFORMED\n"
            "---\n"
            f"- `{path}`\n",
            encoding="utf-8",
        )
        (package / "COMPLETION-REPORT.md").write_text(
            f"MISSION={MISSION}\nWOP_ID={WOP}\nSTATUS=AWAITING_OPERATOR_REVIEW\nPUBLICATION=NOT_PERFORMED\n",
            encoding="utf-8",
        )
        return manifest

    def _patches(self):
        return (
            patch.object(candidate_authority, "project_repository", return_value=self.projection),
            patch.object(publication_cohort, "project_repository", return_value=self.projection),
            patch.object(candidate_authority, "resolve_lifecycle", return_value=self.live),
            patch.object(publication_transaction, "project_repository", return_value=self.projection),
        )

    def _authority_and_record(self):
        with self._patches()[0], self._patches()[1]:
            cohort = publication_cohort.establish(
                self.root, MISSION, runtime_root=self.runtime,
                lifecycle_projection=self.live,
            )
        with self._patches()[0], self._patches()[2]:
            authority = candidate_authority.resolve(
                self.root, MISSION, runtime_root=self.runtime,
                lifecycle_projection=self.live, cohort_id=cohort["cohort_id"],
            )
        record = {
            "publication_id": "PUBLICATION-abcdef12-3456-7890-abcd-ef1234567890",
            "mission_id": MISSION, "wop_id": WOP,
            "repository_id": self.projection["repository_id"],
            "publication_cohort_id": cohort["cohort_id"],
            "candidate_paths": authority["candidate_paths"],
            "candidate_digest": authority["candidate_digest"],
            "candidate_authority_digest": authority["candidate_authority_digest"],
            "classification_digest": "frozen-worktree-classification",
            "cohort_authority_required": True,
        }
        return cohort, authority, record

    def _revalidate(self, record):
        with self._patches()[0], self._patches()[2], self._patches()[3]:
            return publication_transaction._revalidate_authority(self.root, record, self.runtime)

    def test_unchanged_revalidation_and_replay_are_identical(self):
        cohort, authority, record = self._authority_and_record()
        first = self._revalidate(record)
        second = self._revalidate(record)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(first["cohort_id"], cohort["cohort_id"])
        self.assertEqual(first["candidate_digest"], authority["candidate_digest"])
        self.assertEqual(first["candidate_authority_digest"], authority["candidate_authority_digest"])
        self.assertEqual(first["candidate_digest"], second["candidate_digest"])
        self.assertEqual(first["candidate_authority_digest"], second["candidate_authority_digest"])

    def test_new_qualified_source_outside_cohort_is_ignored(self):
        _, _, record = self._authority_and_record()
        self._manifest("outsider", "scripts/outsider.py")
        current = self._revalidate(record)
        self.assertEqual(current["result"], "PASS")

    def test_member_manifest_change_stales(self):
        _, _, record = self._authority_and_record()
        self.manifest.write_text(self.manifest.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
        current = self._revalidate(record)
        self.assertEqual(current["result"], "FAIL")
        self.assertTrue(any("cohort member manifest" in value for value in current["drift_inputs"]))

    def test_member_qualification_change_stales(self):
        _, _, record = self._authority_and_record()
        self.manifest.write_text(self.manifest.read_text(encoding="utf-8").replace("QUALIFIED", "BLOCKED"), encoding="utf-8")
        current = self._revalidate(record)
        self.assertEqual(current["result"], "FAIL")
        self.assertTrue(current["drift_inputs"])

    def test_member_path_content_change_stales(self):
        _, _, record = self._authority_and_record()
        (self.root / "scripts/member.py").write_text("changed\n", encoding="utf-8")
        current = self._revalidate(record)
        self.assertEqual(current["result"], "FAIL")
        self.assertIn("candidate/path content digest", current["drift_inputs"])

    def test_missing_and_mismatched_cohort_fail_closed(self):
        _, _, record = self._authority_and_record()
        missing = dict(record, publication_cohort_id="COHORT-missing")
        self.assertEqual(self._revalidate(missing)["result"], "FAIL")
        mismatch = dict(record, mission_id="OTHER-MISSION")
        current = self._revalidate(mismatch)
        self.assertEqual(current["result"], "FAIL")

    def test_cohort_membership_change_stales(self):
        cohort, _, record = self._authority_and_record()
        persisted = publication_cohort.load_bound(self.root, cohort["cohort_id"], runtime_root=self.runtime)
        persisted["source_ids"] = [*persisted["source_ids"], "source-added-after-freeze"]
        atomic_write(self.runtime / "publication-cohorts" / f"{cohort['cohort_id']}.json", persisted)
        current = self._revalidate(record)
        self.assertEqual(current["result"], "FAIL")
        self.assertIn("cohort identity/membership digest", current["drift_inputs"])

    def test_stage_precondition_rejects_non_durable_milestone_without_staging(self):
        _, _, record = self._authority_and_record()
        (self.root / "scripts/member.py").write_text("changed\n", encoding="utf-8")
        publication_transaction._save(self.runtime, {**record, "current_state": "PREPUBLICATION_VERIFIED", "milestones": {}})
        with self.assertRaises(publication_transaction.PublicationTransactionError) as error:
            publication_transaction.stage(self.root, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "PREPUBLICATION_AUTHORITY_NOT_DURABLE")
        staged = subprocess.check_output(["git", "-C", str(self.root), "diff", "--cached", "--name-only"], text=True)
        self.assertEqual(staged, "")


if __name__ == "__main__":
    unittest.main()
