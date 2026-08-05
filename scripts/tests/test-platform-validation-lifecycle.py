#!/usr/bin/env python3
"""Disposable coverage for published and prepublication EOS classifications."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.eos.validation_lifecycle import classify


def run(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


class ValidationLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.remote = Path(self.temp.name) / "remote.git"
        self.workspace = Path(self.temp.name) / "workspace"
        self.root.mkdir()
        self.workspace.joinpath("eos/state").mkdir(parents=True)
        self.workspace.joinpath("eos/checkpoints").mkdir(parents=True)
        run(self.root, "init", "-q")
        run(self.root, "config", "user.name", "Lifecycle Test")
        run(self.root, "config", "user.email", "lifecycle@example.invalid")
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        run(self.root, "remote", "add", "origin", str(self.remote))
        (self.root / "README.md").write_text("baseline\n", encoding="utf-8")
        run(self.root, "add", "README.md")
        run(self.root, "commit", "-q", "-m", "baseline")
        run(self.root, "branch", "-M", "main")
        run(self.root, "push", "-q", "-u", "origin", "main")
        self.main = run(self.root, "rev-parse", "HEAD")
        self._write_eos(self.main)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_eos(self, commit: str) -> None:
        (self.workspace / "eos/state/EOS-STATE.md").write_text(
            f"---\ndocument_id: EOS-STATE\nrepository_commit: {commit}\n---\n", encoding="utf-8"
        )
        checkpoint = self.workspace / "eos/checkpoints/checkpoint.md"
        checkpoint.write_text(f"# EOS Checkpoint\nCommit: `{commit}`\n", encoding="utf-8")
        (self.workspace / "eos/state/ACTIVE-CHECKPOINT").write_text(f"{checkpoint}\n", encoding="utf-8")

    def test_published_main_requires_strict_parity(self) -> None:
        result = classify(self.root, self.workspace)
        self.assertEqual(result["classification"], "PUBLISHED")
        self.assertTrue(result["valid"])

    def test_clean_remote_aligned_candidate_is_unpublished(self) -> None:
        run(self.root, "switch", "-q", "-c", "prepublication/test-candidate")
        (self.root / "README.md").write_text("candidate\n", encoding="utf-8")
        run(self.root, "add", "README.md")
        run(self.root, "commit", "-q", "-m", "candidate")
        run(self.root, "push", "-q", "-u", "origin", "HEAD")
        result = classify(self.root, self.workspace)
        self.assertEqual(result["classification"], "UNPUBLISHED_CANDIDATE")
        self.assertTrue(result["valid"])
        self.assertEqual(result["eos_baseline"], self.main)

    def test_dirty_and_local_remote_divergence_fail_closed(self) -> None:
        run(self.root, "switch", "-q", "-c", "prepublication/test-candidate")
        run(self.root, "push", "-q", "-u", "origin", "HEAD")
        (self.root / "README.md").write_text("dirty\n", encoding="utf-8")
        self.assertEqual(classify(self.root, self.workspace)["classification"], "DIRTY")
        (self.root / "README.md").write_text("candidate\n", encoding="utf-8")
        run(self.root, "add", "README.md")
        run(self.root, "commit", "-q", "-m", "candidate")
        self.assertEqual(classify(self.root, self.workspace)["classification"], "DIVERGENT_CANDIDATE")

    def test_stale_eos_and_outdated_candidate_fail_closed(self) -> None:
        run(self.root, "switch", "-q", "-c", "prepublication/test-candidate")
        run(self.root, "push", "-q", "-u", "origin", "HEAD")
        self._write_eos("0" * 40)
        self.assertEqual(classify(self.root, self.workspace)["classification"], "EOS_STALE")


if __name__ == "__main__":
    unittest.main()
