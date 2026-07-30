#!/usr/bin/env python3
"""Isolated canonical repository policy tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.repository import (
    RepositoryPolicyError,
    observe,
    require_canonical_write,
)


class RepositoryPolicyTests(unittest.TestCase):
    def repository(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "homelab"
        root.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", root], check=True)
        subprocess.run(
            ["git", "-C", root, "remote", "add", "origin", "test://canonical"],
            check=True,
        )
        (root / "README").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", root, "add", "README"], check=True)
        subprocess.run(
            [
                "git", "-C", root, "-c", "user.name=test", "-c",
                "user.email=test@example.invalid", "commit", "-qm", "fixture",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", root, "update-ref", "refs/remotes/origin/main", "HEAD"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", root, "branch", "--set-upstream-to=origin/main"],
            check=True,
            capture_output=True,
        )
        return root

    def test_explicit_expected_identity_passes(self) -> None:
        root = self.repository()
        result = observe(
            root,
            expected_root=root.resolve(),
            expected_remote="test://canonical",
            repository_search_roots=(root.parent,),
        )
        self.assertTrue(result.allowed, result.data)

    def test_wrong_root_and_remote_fail_closed(self) -> None:
        root = self.repository()
        result = observe(
            root,
            expected_root=Path("/wrong"),
            expected_remote="wrong",
            repository_search_roots=(root.parent,),
        )
        checks = {item["check"] for item in result.data["failures"]}
        self.assertEqual(checks, {"canonical_root", "remote_identity"})

    def test_production_write_guard_rejects_fixture(self) -> None:
        with self.assertRaises(RepositoryPolicyError):
            require_canonical_write(self.repository())


if __name__ == "__main__":
    unittest.main()
