#!/usr/bin/env python3
"""Machine-safe Git and canonical repository projection qualification."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from scripts.lib.emp.repository_projection import project  # noqa: E402
from scripts.lib.eos.state_sync import render  # noqa: E402


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class RepositoryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Projection Test")
        git(self.root, "config", "user.email", "projection@example.invalid")
        (self.root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        git(self.root, "add", "tracked.txt")
        git(self.root, "commit", "-q", "-m", "baseline")
        head = git(self.root, "rev-parse", "HEAD")
        git(self.root, "update-ref", "refs/remotes/origin/main", head)

    def tearDown(self):
        self.temporary.cleanup()

    def test_clean_projection_is_json_ready_and_read_only(self):
        first = project(self.root, self.base / "eos-workspace")
        second = project(self.root, self.base / "eos-workspace")
        self.assertEqual(first, second)
        self.assertEqual(first["result"], "PASS")
        self.assertTrue(first["repository_valid"])
        self.assertTrue(first["index_clean"])
        self.assertTrue(first["worktree_clean"])
        self.assertEqual(first["head"], first["origin_main"])
        self.assertTrue(first["read_only"])
        json.dumps(first, sort_keys=True)

    def test_tracked_dirty_staged_and_untracked_state(self):
        (self.root / "tracked.txt").write_text("unstaged\n", encoding="utf-8")
        (self.root / "file with spaces\tand-tab.txt").write_text("untracked\n", encoding="utf-8")
        value = project(self.root, self.base / "eos-workspace")
        self.assertTrue(value["index_clean"])
        self.assertFalse(value["tracked_worktree_clean"])
        self.assertTrue(value["untracked_present"])
        self.assertFalse(value["worktree_clean"])
        self.assertIn("file with spaces\tand-tab.txt", value["untracked_paths"])

        git(self.root, "add", "tracked.txt")
        staged = project(self.root, self.base / "eos-workspace")
        self.assertIn("tracked.txt", staged["staged_paths"])
        self.assertFalse(staged["index_clean"])

    def test_head_origin_mismatch_and_ancestry_are_projected(self):
        (self.root / "next.txt").write_text("next\n", encoding="utf-8")
        git(self.root, "add", "next.txt")
        git(self.root, "commit", "-q", "-m", "next")
        value = project(self.root, self.base / "eos-workspace")
        self.assertFalse(value["repository_valid"])
        self.assertEqual(value["baseline_state_classification"], "UNAUTHORIZED_DIVERGENCE")
        self.assertFalse(value["head_origin_parity"])
        self.assertEqual(value["ahead_count"], 1)
        self.assertEqual(value["behind_count"], 0)
        self.assertTrue(value["origin_main_ancestor_of_head"])
        self.assertFalse(value["head_ancestor_of_origin_main"])

    def test_non_descendant_refs_are_explicitly_projected(self):
        original_head = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-q", "--orphan", "alternate")
        git(self.root, "rm", "-q", "-rf", ".")
        (self.root / "alternate.txt").write_text("alternate\n", encoding="utf-8")
        git(self.root, "add", "alternate.txt")
        git(self.root, "commit", "-q", "-m", "alternate")
        alternate_head = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-q", "--detach", original_head)
        git(self.root, "update-ref", "refs/remotes/origin/main", alternate_head)
        value = project(self.root, self.base / "eos-workspace")
        self.assertFalse(value["head_origin_parity"])
        self.assertFalse(value["origin_main_ancestor_of_head"])
        self.assertFalse(value["head_ancestor_of_origin_main"])

    def test_unavailable_origin_fails_closed(self):
        git(self.root, "update-ref", "-d", "refs/remotes/origin/main")
        value = project(self.root, self.base / "eos-workspace")
        self.assertEqual(value["result"], "FAIL")
        self.assertFalse(value["repository_valid"])

    def test_invalid_repository_fails_closed(self):
        value = project(self.root / "missing", self.base / "eos-workspace")
        self.assertEqual(value["result"], "FAIL")
        self.assertFalse(value["repository_valid"])

    def test_detached_head_is_explicit(self):
        head = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-q", "--detach", head)
        value = project(self.root, self.base / "eos-workspace")
        self.assertTrue(value["repository_valid"])
        self.assertTrue(value["detached_head"])
        self.assertIsNone(value["branch"])

    def test_eos_mismatch_is_reported_and_fails_projection(self):
        workspace = self.base / "eos-workspace"
        (self.root / "engineering/eos").mkdir(parents=True)
        (self.root / "engineering/registry").mkdir(parents=True)
        (self.root / "engineering/execution").mkdir(parents=True)
        (self.root / "docs/project").mkdir(parents=True)
        (self.root / "engineering/eos/repository-eos-authority.yaml").write_text(
            "schema_version: 1\ncanonical_platform_state: repository\nrecords: []\n",
            encoding="utf-8",
        )
        (self.root / "engineering/registry/work-registry.yaml").write_text(
            "schema_version: 1\nrevision: 1\n", encoding="utf-8"
        )
        (self.root / "engineering/execution/execution-interface.yaml").write_text(
            "schema_version: 2\n", encoding="utf-8"
        )
        (self.root / "docs/project/PROJ-0001-PROJECT_STATE.md").write_text(
            "---\ndocument_id: PROJ-0001\nversion: 1.0\nstatus: Active\nphase: Test\n---\n\n# State\n",
            encoding="utf-8",
        )
        for path, content in render(self.root, workspace, "homelab").items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        state = workspace / "eos/state/EOS-STATE.md"
        state.write_text(
            state.read_text(encoding="utf-8").replace(
                git(self.root, "rev-parse", "HEAD"),
                "0" * 40,
            ),
            encoding="utf-8",
        )
        value = project(self.root, workspace)
        self.assertEqual(value["result"], "FAIL")
        self.assertFalse(value["eos_parity"])
        self.assertFalse(value["repository_valid"])

    def test_cli_projection_is_machine_readable_and_non_mutating(self):
        before = git(self.root, "status", "--porcelain=v2", "--branch")
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "repository", "projection", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        after = git(self.root, "status", "--porcelain=v2", "--branch")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
