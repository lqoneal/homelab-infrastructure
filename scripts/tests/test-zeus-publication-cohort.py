#!/usr/bin/env python3
"""Focused tests for source-level Zeus Publication Cohort authority."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import publication_candidate_authority as candidate_authority
from scripts.lib.emp import publication_cohort
from scripts.lib.emp import publication_transaction


MISSION = "ZEUS-TEST-PUBLICATION-COHORT-01"
WOP = "WOP-ZEUS-TEST-PUBLICATION-COHORT-001"


class PublicationCohortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime_temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.runtime_temp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Zeus Test"], check=True)
        (self.root / "tracked.md").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.md"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "baseline"], check=True)
        head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        self.projection = {
            "result": "PASS", "repository_valid": True, "repository_id": "repo-cohort-test",
            "repository_root": str(self.root), "head": head, "origin_main": head,
            "eos_baseline": head, "eos_parity": True, "index_clean": True,
            "staged_paths": [], "unstaged_paths": [], "untracked_paths": [],
        }
        self.live = {"result": "PASS", "mission_id": MISSION, "wop_id": WOP,
                     "submission_id": "SUBMISSION-1", "admission_id": "ADMISSION-1",
                     "bootstrap_id": "BOOTSTRAP-1", "lifecycle_state": "AWAITING_EXECUTION_DISPATCH",
                     "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}

    def tearDown(self) -> None:
        self.runtime_temp.cleanup()
        self.temp.cleanup()

    def manifest(self, name: str, paths: list[str]) -> Path:
        package = self.root / "engineering" / "evidence" / name
        package.mkdir(parents=True)
        for value in paths:
            target = self.root / value
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"{name}:{value}\n", encoding="utf-8")
        manifest = package / "PUBLICATION-CANDIDATE-MANIFEST.md"
        manifest.write_text(
            "---\n"
            f"mission_id: {MISSION}\n"
            f"wop_id: {WOP}\n"
            "qualification_state: QUALIFIED\n"
            "publication_state: NOT_PERFORMED\n"
            "---\n"
            + "\n".join(f"- `{value}`" for value in paths)
            + "\n",
            encoding="utf-8",
        )
        (package / "COMPLETION-REPORT.md").write_text(
            f"MISSION={MISSION}\nWOP_ID={WOP}\nSTATUS=AWAITING_OPERATOR_REVIEW\nPUBLICATION=NOT_PERFORMED\n",
            encoding="utf-8",
        )
        return manifest

    def test_same_cohort_shared_path_is_authorized_and_replayable(self) -> None:
        self.manifest("a", ["scripts/shared.py"])
        self.manifest("b", ["scripts/shared.py"])
        with patch.object(publication_cohort, "project_repository", return_value=self.projection):
            cohort = publication_cohort.establish(self.root, MISSION, runtime_root=self.runtime, lifecycle_projection=self.live, supersedes_publication_id="PUBLICATION-OLD")
            replay = publication_cohort.establish(self.root, MISSION, runtime_root=self.runtime, lifecycle_projection=self.live, supersedes_publication_id="PUBLICATION-OLD")
        self.assertEqual(cohort["result"], "PASS")
        self.assertEqual(cohort["cohort_authority_result"], "PASS")
        self.assertEqual(cohort["source_count"], 2)
        self.assertTrue(replay["replayed"])
        with patch.object(candidate_authority, "project_repository", return_value=self.projection), patch.object(publication_cohort, "project_repository", return_value=self.projection):
            resolved = candidate_authority.resolve(self.root, MISSION, runtime_root=self.runtime, lifecycle_projection=self.live)
        self.assertEqual(resolved["result"], "PASS")
        self.assertEqual(resolved["candidate_paths"], ["scripts/shared.py"])
        self.assertEqual(resolved["cohort"]["cohort_id"], cohort["cohort_id"])

    def test_unqualified_new_source_stales_cohort_fail_closed(self) -> None:
        self.manifest("a", ["scripts/a.py"])
        with patch.object(publication_cohort, "project_repository", return_value=self.projection):
            cohort = publication_cohort.establish(self.root, MISSION, runtime_root=self.runtime, lifecycle_projection=self.live)
        self.assertEqual(cohort["result"], "PASS")
        self.manifest("later", ["scripts/later.py"])
        with patch.object(publication_cohort, "project_repository", return_value=self.projection):
            current = publication_cohort.inspect(self.root, MISSION, runtime_root=self.runtime, lifecycle_projection=self.live)
        self.assertEqual(current["result"], "FAIL")
        self.assertEqual(current["next_authorized_action"], "RECONCILE_PUBLICATION_COHORT_AUTHORITY")

    def test_superseded_predecessor_is_not_current_without_mutating_it(self) -> None:
        old = {"publication_id": "PUBLICATION-OLD", "current_state": "PREPUBLICATION_VERIFIED"}
        new = {"publication_id": "PUBLICATION-NEW", "current_state": "PUBLICATION_DISCOVERED", "supersedes_publication_id": "PUBLICATION-OLD"}
        active = publication_transaction._active_transactions([old, new])
        self.assertEqual([item["publication_id"] for item in active], ["PUBLICATION-NEW"])
        self.assertEqual(old["current_state"], "PREPUBLICATION_VERIFIED")


if __name__ == "__main__":
    unittest.main()
