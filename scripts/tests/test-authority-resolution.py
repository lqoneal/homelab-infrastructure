#!/usr/bin/env python3
"""Regression tests for the offline Authority Resolution Engine."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.authority import (  # noqa: E402
    AuthorityGraph,
    AuthorityValidationError,
)


FIXTURES = ROOT / "engineering/authority/fixtures"
CLI = ROOT / "scripts/authorityctl"


class AuthorityResolutionTests(unittest.TestCase):
    def load(self, name: str) -> AuthorityGraph:
        return AuthorityGraph.load(FIXTURES / name)

    def assert_invalid(self, name: str, phrase: str) -> None:
        graph = self.load(name)
        with self.assertRaises(AuthorityValidationError) as context:
            graph.validate()
        self.assertIn(phrase, str(context.exception))

    def test_valid_graph(self) -> None:
        graph = self.load("valid.yaml")
        graph.validate()
        self.assertEqual(len(graph.nodes), 7)
        self.assertEqual(len(graph.edges), 6)

    def test_deterministic_resolution(self) -> None:
        graph = self.load("valid.yaml")
        first = graph.resolve("session")
        second = graph.resolve("session")
        self.assertEqual(first, second)
        self.assertEqual(
            first.path,
            (
                "session",
                "work-package",
                "mission",
                "baseline",
                "governance",
                "charter",
                "organization",
            ),
        )
        self.assertEqual(first.root_id, "organization")
        self.assertEqual(first.effective_capabilities, frozenset({"execute"}))

    def test_cycle_rejected(self) -> None:
        self.assert_invalid("cycle.yaml", "authority cycle detected")

    def test_multi_parent_rejected(self) -> None:
        self.assert_invalid("multi-parent.yaml", "expected 1 authority parent(s), found 2")

    def test_multiple_roots_rejected(self) -> None:
        self.assert_invalid("multiple-roots.yaml", "exactly one root authority is required")

    def test_orphan_rejected(self) -> None:
        self.assert_invalid("orphan.yaml", "orphan authority parent does not resolve")

    def test_rank_violation_rejected(self) -> None:
        self.assert_invalid("rank-violation.yaml", "authority rank must decrease")

    def test_authority_expansion_rejected(self) -> None:
        self.assert_invalid(
            "authority-expansion.yaml",
            "effective authority expands parent organization: approve",
        )

    def test_cross_domain_transfer_rejected(self) -> None:
        self.assert_invalid("cross-domain.yaml", "cross-domain authority")

    def test_unknown_node_fails_closed(self) -> None:
        graph = self.load("valid.yaml")
        with self.assertRaises(AuthorityValidationError):
            graph.resolve("unknown")

    def test_serialization_is_deterministic_and_round_trips(self) -> None:
        graph = self.load("valid.yaml")
        json_one = graph.to_json()
        json_two = graph.to_json()
        self.assertEqual(json_one, json_two)
        restored = AuthorityGraph.from_mapping(json.loads(json_one))
        restored.validate()
        self.assertEqual(restored.to_mapping(), graph.to_mapping())
        yaml_restored = AuthorityGraph.from_mapping(yaml.safe_load(graph.to_yaml()))
        yaml_restored.validate()
        self.assertEqual(yaml_restored.to_mapping(), graph.to_mapping())

    def test_cli_validate_and_resolve(self) -> None:
        valid = FIXTURES / "valid.yaml"
        validation = subprocess.run(
            [sys.executable, str(CLI), "validate", str(valid)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("PASS: authority graph", validation.stdout)
        resolution = subprocess.run(
            [sys.executable, str(CLI), "resolve", str(valid), "session"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(resolution.stdout)["root_id"], "organization")

    def test_cli_rejects_invalid_graph(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "validate",
                str(FIXTURES / "cycle.yaml"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("authority cycle detected", result.stderr)


if __name__ == "__main__":
    unittest.main()
