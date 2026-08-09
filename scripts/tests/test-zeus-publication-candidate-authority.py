#!/usr/bin/env python3
"""Focused tests for mission-scoped publication candidate authority."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import publication_candidate_authority as authority


MISSION = "ZEUS-TEST-PUBLICATION-MISSION-01"
WOP = "WOP-ZEUS-TEST-PUBLICATION-001"


class CandidateAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Zeus Test"], check=True)
        (self.root / "engineering" / "evidence").mkdir(parents=True)
        (self.root / "engineering" / "docs").mkdir(parents=True)
        (self.root / "tracked.md").write_text("published\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.md"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "baseline"], check=True)
        head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        self.projection = {
            "result": "PASS", "repository_valid": True, "repository_id": "repo-test",
            "repository_root": str(self.root), "head": head, "origin_main": head,
            "eos_baseline": head, "eos_parity": True, "index_clean": True,
            "staged_paths": [], "unstaged_paths": [], "untracked_paths": [],
        }
        self.live = {"result": "PASS", "mission_id": MISSION, "wop_id": WOP,
                     "submission_id": "SUBMISSION-1", "admission_id": "ADMISSION-1",
                     "bootstrap_id": "BOOTSTRAP-1", "lifecycle_state": "AWAITING_EXECUTION_DISPATCH",
                     "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}

    def tearDown(self):
        self.tmp.cleanup()

    def _manifest(self, name: str, paths: list[str], *, package_text: str = "", state: str = "NOT_PERFORMED", intent: str = "", cohort: str = "") -> Path:
        package = self.root / "engineering" / "evidence" / name
        package.mkdir(parents=True)
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"{name}:{path}\n", encoding="utf-8")
        manifest = package / "PUBLICATION-CANDIDATE-MANIFEST.md"
        manifest.write_text(
            "---\n"
            f"mission_id: {MISSION}\n"
            f"wop_id: {WOP}\n"
            "qualification_state: QUALIFIED\n"
            f"publication_state: {state}\n"
            f"candidate_intent: {intent}\n"
            f"publication_cohort: {cohort}\n"
            "---\n"
            f"MISSION_ID={MISSION}\nWOP_ID={WOP}\n"
            + ("\n" + package_text + "\n" if package_text else "")
            + "\n".join(f"- `{path}`" for path in paths) + "\n",
            encoding="utf-8",
        )
        (package / "COMPLETION-REPORT.md").write_text(
            f"MISSION={MISSION}\nWOP_ID={WOP}\nSTATUS=AWAITING_OPERATOR_REVIEW\nPUBLICATION={state}\n",
            encoding="utf-8",
        )
        return manifest

    def _resolve(self):
        return authority.resolve(self.root, MISSION, lifecycle_projection=self.live)

    def _state_record(self, manifest: Path, **changes) -> Path:
        value = {
            "schema_version": 1,
            "record_type": authority.STATE_RECORD_TYPE,
            "result": "PASS",
            "mission_id": MISSION,
            "wop_id": WOP,
            "candidate_manifest": str(manifest.relative_to(self.root)),
            "qualification_state": "QUALIFIED",
            "publication_state": "NOT_PERFORMED",
        }
        value.update(changes)
        path = manifest.parent / authority.STATE_RECORD_NAME
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_one_qualified_manifest_and_replay_are_deterministic(self):
        self._manifest("one", ["scripts/one.py"])
        with patch.object(authority, "project_repository", return_value=self.projection):
            first = self._resolve()
            second = self._resolve()
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(first["candidate_paths"], ["scripts/one.py"])
        self.assertEqual(first["candidate_digest"], second["candidate_digest"])
        self.assertEqual(first["classification_digest"], second["classification_digest"])
        self.assertEqual(first["candidate_traceability"][0]["sources"][0]["authority"]["type"], "QUALIFIED_MISSION_EVIDENCE")

    def test_multiple_sources_union_and_dependency(self):
        first = self._manifest("first", ["scripts/one.py"], cohort="COHORT-1")
        second = self._manifest("second", ["scripts/two.py"], intent="dependency", cohort="COHORT-1")
        first_text = first.read_text(encoding="utf-8")
        first.write_text(first_text.replace("candidate_intent: \n", "dependencies: []\ncandidate_intent: \n"), encoding="utf-8")
        second_text = second.read_text(encoding="utf-8")
        second.write_text(second_text.replace("candidate_intent: dependency", "dependencies:\n  - " + str(first.relative_to(self.root)) + "\ncandidate_intent: dependency"), encoding="utf-8")
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["candidate_paths"], ["scripts/one.py", "scripts/two.py"])
        self.assertEqual(len(result["candidate_sources"]), 2)

    def test_overlapping_claims_require_explicit_shared_cohort(self):
        self._manifest("a", ["scripts/shared.py"])
        self._manifest("b", ["scripts/shared.py"])
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["ambiguous"][0]["path"], "scripts/shared.py")
        self.assertIn("publication cohort", result["ambiguous"][0]["reason"])

    def test_overlapping_claims_with_shared_cohort_are_deterministic(self):
        self._manifest("a", ["scripts/shared.py"], cohort="COHORT-1")
        self._manifest("b", ["scripts/shared.py"], cohort="COHORT-1")
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["candidate_paths"], ["scripts/shared.py"])

    def test_historical_and_already_published_sources_are_excluded(self):
        self._manifest("current", ["scripts/current.py"])
        self._manifest("historical", ["scripts/historical.py"], state="HISTORICAL_ONLY")
        published = self._manifest("published", ["tracked.md"], state="NOT_PERFORMED")
        (self.root / "tracked.md").write_text("published\n", encoding="utf-8")
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["candidate_paths"], ["scripts/current.py"])
        self.assertNotIn("scripts/historical.py", result["candidate_paths"])
        self.assertIn("tracked.md", result["already_published"])
        self.assertEqual(len(result["historical_sources"]), 1)

    def test_conflicting_current_claims_fail_closed(self):
        self._manifest("a", ["scripts/shared.py"], intent="implementation-a")
        self._manifest("b", ["scripts/shared.py"], intent="implementation-b")
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(result["ambiguous"])

    def test_missing_path_fails_closed(self):
        self._manifest("missing", ["scripts/does-not-exist.py"])
        (self.root / "scripts" / "does-not-exist.py").unlink()
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "FAIL")
        self.assertIn("scripts/does-not-exist.py", result["missing"])

    def test_machine_readable_state_record_is_authoritative_and_deterministic(self):
        manifest = self._manifest("machine-state", ["scripts/machine-state.py"])
        manifest.write_text(
            manifest.read_text(encoding="utf-8")
            .replace("qualification_state: QUALIFIED\n", "")
            .replace("publication_state: NOT_PERFORMED\n", ""),
            encoding="utf-8",
        )
        state_path = self._state_record(manifest)
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "PASS")
        source = next(item for item in result["candidate_sources"] if item["source_path"] == str(manifest.relative_to(self.root)))
        self.assertEqual(source["qualification_state"], "QUALIFIED")
        self.assertEqual(source["publication_state"], "QUALIFIED_UNPUBLISHED")
        self.assertEqual(source["qualification_publication_state_record"], str(state_path.relative_to(self.root)))

    def test_invalid_machine_readable_state_record_fails_closed(self):
        manifest = self._manifest("invalid-machine-state", ["scripts/invalid-machine-state.py"])
        self._state_record(manifest, mission_id="OTHER-MISSION")
        with patch.object(authority, "project_repository", return_value=self.projection):
            result = self._resolve()
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["blocked"][0]["code"], "QUALIFICATION_OR_PUBLICATION_STATE_UNRESOLVED")
        self.assertIn("state record invalid", result["blocked"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
