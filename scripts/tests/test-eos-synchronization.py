#!/usr/bin/env python3
"""Repository–EOS synchronization qualification tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.state_sync import SynchronizationError, render  # noqa: E402


class EosSynchronizationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "repository"
        self.workspace = self.base / "workspace"
        for path in (
            "engineering/eos",
            "engineering/registry",
            "engineering/execution",
            "docs/project",
        ):
            (self.root / path).mkdir(parents=True, exist_ok=True)
        (self.root / "engineering/eos/repository-eos-authority.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "canonical_platform_state": "repository",
                    "records": [],
                }
            )
        )
        (self.root / "engineering/registry/work-registry.yaml").write_text(
            "schema_version: 1\nrevision: 1\n"
        )
        (self.root / "engineering/execution/execution-interface.yaml").write_text(
            "schema_version: 2\n"
        )
        (self.root / "docs/project/PROJ-0001-PROJECT_STATE.md").write_text(
            "---\ndocument_id: PROJ-0001\nversion: 1.0\nstatus: Active\n"
            "phase: Test\n---\n\n# State\n"
        )
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test"], check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "config",
                "user.email",
                "test@example.invalid",
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", "baseline"],
            check=True,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_render_is_deterministic_and_repository_authoritative(self):
        first = render(self.root, self.workspace, "homelab")
        second = render(self.root, self.workspace, "homelab")
        self.assertEqual(first, second)
        state = first[self.workspace / "eos/state/EOS-STATE.md"].decode()
        self.assertIn("authority: repository", state)
        self.assertIn("project_state: PROJ-0001@1.0", state)

    def test_repository_change_changes_projection(self):
        first = render(self.root, self.workspace, "homelab")
        project = self.root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        project.write_text(project.read_text() + "\nupdated\n")
        second = render(self.root, self.workspace, "homelab")
        self.assertNotEqual(
            first[self.workspace / "eos/state/EOS-STATE.md"],
            second[self.workspace / "eos/state/EOS-STATE.md"],
        )

    def test_unsupported_matrix_version_fails_before_projection(self):
        matrix = self.root / "engineering/eos/repository-eos-authority.yaml"
        matrix.write_text("schema_version: 2\ncanonical_platform_state: repository\n")
        with self.assertRaises(SynchronizationError):
            render(self.root, self.workspace, "homelab")
        self.assertFalse((self.workspace / "eos/state").exists())

    def test_inactive_project_state_fails_closed(self):
        project = self.root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        project.write_text(project.read_text().replace("status: Active", "status: Draft"))
        with self.assertRaises(SynchronizationError):
            render(self.root, self.workspace, "homelab")


if __name__ == "__main__":
    unittest.main()
