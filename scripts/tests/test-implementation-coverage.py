#!/usr/bin/env python3
"""Regression tests for additive implementation coverage validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/lib/implementation_coverage.py"
SPEC = importlib.util.spec_from_file_location("implementation_coverage", MODULE_PATH)
coverage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(coverage)


POLICY = {
    "authority": "SPEC-0001",
    "discovery": {"roots": ["src"]},
    "categories": {
        "Library": {"documentation": "mandatory"},
        "Generated Artifact": {"documentation": "prohibited"},
        "External Dependency": {"documentation": "prohibited"},
    },
    "classification_rules": [
        {
            "category": "Generated Artifact",
            "patterns": ["**/generated/**"],
            "evidence": "generated",
        },
        {
            "category": "External Dependency",
            "patterns": ["**/vendor/**"],
            "evidence": "external",
        },
        {"category": "Library", "patterns": ["src/**"], "evidence": "source"},
    ],
}


def declaration(
    synchronization_id: str,
    implementation: str,
    documentation: str = "docs/SPEC-TEST.md",
    recursive: bool = False,
) -> dict:
    return {
        "synchronization_id": synchronization_id,
        "documentation": {
            "document_id": "SPEC-TEST",
            "repository_locator": documentation,
        },
        "implementation": {
            "repository_locator": implementation,
            **({"coverage_scope": "recursive"} if recursive else {}),
        },
    }


class ImplementationCoverageTests(unittest.TestCase):
    def test_repository_report_is_deterministic_and_complete(self) -> None:
        policy = coverage.load_policy(
            ROOT / "engineering/validation/implementation-coverage.yaml"
        )
        synchronization = coverage.load_policy(
            ROOT / "engineering/validation/implementation-synchronization.yaml"
        )
        first = coverage.analyze(ROOT, synchronization, policy)
        second = coverage.analyze(ROOT, synchronization, policy)
        self.assertEqual(first, second)
        self.assertEqual(0, first["coverage_metrics"]["documentation_debt"])
        self.assertEqual(100.0, first["coverage_metrics"]["documentation_coverage_percentage"])
        self.assertEqual([], first["synchronization_gaps"])

    def test_ordered_classification_is_deterministic(self) -> None:
        generated = coverage.classify_artifact("src/generated/client.py", POLICY)
        external = coverage.classify_artifact("src/vendor/client.py", POLICY)
        library = coverage.classify_artifact("src/client.py", POLICY)
        self.assertEqual("Generated Artifact", generated["category"])
        self.assertEqual("External Dependency", external["category"])
        self.assertEqual("Library", library["category"])

    def test_undocumented_and_orphan_findings_include_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "src/undocumented.py").write_text("x = 1\n", encoding="utf-8")
            metadata = {
                "repository": {"repository_id": "fixture"},
                "synchronizations": [
                    declaration("SYNC-MISSING", "src/missing.py"),
                ],
            }
            report = coverage.analyze(root, metadata, POLICY)
            self.assertEqual(1, report["coverage_metrics"]["undocumented_artifacts"])
            self.assertEqual(1, report["coverage_metrics"]["orphan_declarations"])
            self.assertEqual(
                ["src/undocumented.py"],
                report["orphan_findings"]["undocumented_implementation"],
            )
            self.assertTrue(report["synchronization_gaps"][0]["evidence"])
            self.assertTrue(report["orphan_declarations"][0]["evidence"])

    def test_recursive_declaration_covers_each_discovered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src/nested").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "src/a.py").write_text("", encoding="utf-8")
            (root / "src/nested/b.py").write_text("", encoding="utf-8")
            (root / "docs/SPEC-TEST.md").write_text("# Test\n", encoding="utf-8")
            metadata = {
                "synchronizations": [
                    declaration("SYNC-TREE", "src", recursive=True),
                ]
            }
            report = coverage.analyze(root, metadata, POLICY)
            self.assertEqual(2, report["coverage_metrics"]["synchronized_artifacts"])
            self.assertEqual(100.0, report["coverage_metrics"]["synchronization_coverage_percentage"])


if __name__ == "__main__":
    unittest.main()
