#!/usr/bin/env python3
"""Regression tests for additive implementation synchronization validation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/lib/document_synchronization.py"
SPEC = importlib.util.spec_from_file_location("document_synchronization", MODULE_PATH)
assert SPEC and SPEC.loader
synchronization = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(synchronization)


class SynchronizationTests(unittest.TestCase):
    def test_all_drift_classifications(self) -> None:
        cases = [
            (dict(exists=True, superseded=False, implementation_changed=False, documentation_changed=False), "PASS"),
            (dict(exists=True, superseded=False, implementation_changed=True, documentation_changed=True), "OUT_OF_SYNC"),
            (dict(exists=True, superseded=False, implementation_changed=True, documentation_changed=False), "IMPLEMENTATION_CHANGED"),
            (dict(exists=True, superseded=False, implementation_changed=False, documentation_changed=True), "DOCUMENT_CHANGED"),
            (dict(exists=False, superseded=False, implementation_changed=None, documentation_changed=None), "MISSING_ARTIFACT"),
            (dict(exists=True, superseded=True, implementation_changed=True, documentation_changed=True), "SUPERSEDED"),
            (dict(exists=True, superseded=False, implementation_changed=None, documentation_changed=False), "UNKNOWN"),
        ]
        for arguments, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(expected, synchronization.classify(**arguments))

    def test_fingerprints_and_reports_are_deterministic(self) -> None:
        metadata = synchronization.load_metadata(
            ROOT / "engineering/validation/implementation-synchronization.yaml"
        )
        first = synchronization.analyze(ROOT, metadata)
        second = synchronization.analyze(ROOT, metadata)
        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )
        self.assertEqual([], synchronization.validate_metadata(metadata))
        self.assertEqual(
            set(synchronization.DRIFT_STATES),
            set(first["summary"]),
        )

    def test_directory_hash_includes_names_kinds_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "nested/item").write_text("value", encoding="utf-8")
            first = synchronization.sha256_path(root)
            second = synchronization.sha256_path(root)
            self.assertEqual(first, second)
            (root / "nested/item").write_text("changed", encoding="utf-8")
            self.assertNotEqual(first, synchronization.sha256_path(root))

    def test_repository_inventory_hash_excludes_ignored_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "checkout"
            subprocess.run(
                ["git", "clone", "--shared", "--quiet", str(ROOT), str(checkout)],
                check=True,
            )
            first = synchronization.fingerprint(
                checkout, "scripts", "repository_inventory"
            )
            ignored = checkout / "scripts/__pycache__/coverage-ignored.pyc"
            ignored.parent.mkdir(parents=True, exist_ok=True)
            ignored.write_bytes(b"generated")
            second = synchronization.fingerprint(
                checkout, "scripts", "repository_inventory"
            )
            self.assertEqual(first, second)

    def test_reverse_graph_traversal_is_transitive(self) -> None:
        declarations = [
            {
                "documentation": {"document_id": "SPEC"},
                "implementation": {"repository_locator": "scripts/tool"},
                "downstream_documentation": ["PROC"],
            },
            {
                "documentation": {"document_id": "PROC"},
                "implementation": {"repository_locator": "scripts/other"},
                "downstream_documentation": ["GUIDE"],
            },
        ]
        graph = synchronization.build_graph(declarations)
        self.assertEqual(
            ["GUIDE", "PROC", "SPEC"],
            synchronization.affected_documentation(graph, {"scripts/tool"}),
        )

    def test_qualification_analysis_never_decides_approval(self) -> None:
        impact = synchronization.qualification_impact("OUT_OF_SYNC", {})
        self.assertIsNone(impact["approval_decision"])
        self.assertTrue(impact["automatic_decision_prohibited"])
        self.assertIn("independent_qualification_required", impact["assessment"])

    def test_repository_commit_fingerprint_accepts_descendant(self) -> None:
        head = synchronization.git_output(ROOT, "rev-parse", "HEAD")
        parent = synchronization.git_output(ROOT, "rev-parse", "HEAD^")
        self.assertTrue(
            synchronization.fingerprint_matches(
                ROOT, "repository_commit", parent, head
            )
        )
        self.assertFalse(
            synchronization.fingerprint_matches(
                ROOT, "repository_commit", "0" * 40, head
            )
        )


if __name__ == "__main__":
    unittest.main()
