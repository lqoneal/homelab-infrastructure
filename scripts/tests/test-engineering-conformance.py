#!/usr/bin/env python3
"""Regression tests for engineering contract conformance validation."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/lib/engineering_conformance.py"
SPEC = importlib.util.spec_from_file_location("engineering_conformance", MODULE_PATH)
conformance = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(conformance)


def contract(identifier: str, locator: str, arguments: list[str]) -> dict:
    return {
        "contract_id": identifier,
        "category": "API",
        "source": {"document_id": "SPEC-TEST", "locator": "docs/spec.md"},
        "discovery": {
            "mechanism": "api_signature",
            "locator": locator,
            "symbol": "interface",
        },
        "expectations": {"arguments": arguments, "file_locations": [locator]},
    }


class EngineeringConformanceTests(unittest.TestCase):
    def test_repository_catalog_is_conformant_and_deterministic(self) -> None:
        catalog = conformance.load_contracts(
            ROOT / "engineering/validation/engineering-contracts.yaml"
        )
        first = conformance.analyze(ROOT, catalog)
        second = conformance.analyze(ROOT, catalog)
        self.assertEqual(first, second)
        self.assertEqual(
            conformance.canonical_report(first),
            conformance.canonical_report(second),
        )
        self.assertEqual([], first["invariant_failures"])
        self.assertEqual(10, first["summary"]["conformant"])
        self.assertEqual("derived_engineering_evidence", first["evidence_classification"])
        self.assertTrue(all(value == "not_inferred" for value in first["authority_boundaries"].values()))

    def test_missing_partial_incompatible_and_obsolete_are_evidenced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/partial.py").write_text(
                "def interface(first):\n    return first\n", encoding="utf-8"
            )
            (root / "src/incompatible.py").write_text(
                "def interface(actual):\n    return actual\n", encoding="utf-8"
            )
            catalog = {
                "authority": "SPEC-0001",
                "contracts": [
                    {
                        **contract("PARTIAL", "src/partial.py", ["first"]),
                        "expectations": {
                            "arguments": ["first"],
                            "return_values": ["documented"],
                            "file_locations": ["src/partial.py"],
                        },
                    },
                    contract("INCOMPATIBLE", "src/incompatible.py", ["expected"]),
                    contract("MISSING", "src/missing.py", ["value"]),
                    {
                        **contract("OBSOLETE", "src/obsolete.py", ["value"]),
                        "lifecycle": "deprecated",
                    },
                ],
            }
            report = conformance.analyze(root, catalog)
            results = {
                item["contract_id"]: item["determination"]
                for item in report["validated_contracts"]
            }
            self.assertEqual("partially_conformant", results["PARTIAL"])
            self.assertEqual("incompatible_implementation", results["INCOMPATIBLE"])
            self.assertEqual("missing_implementation", results["MISSING"])
            self.assertEqual("obsolete_contract", results["OBSOLETE"])
            self.assertTrue(report["invariant_failures"])
            self.assertTrue(report["compatibility_findings"])
            self.assertTrue(all(item["evidence"] for item in report["validated_contracts"]))

    def test_contract_extraction_rejects_ambiguous_or_unknown_elements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contracts.yaml"
            path.write_text(
                yaml.safe_dump(
                    {
                        "contracts": [
                            {
                                **contract("BAD", "src/a.py", []),
                                "expectations": {"invented_contract": True},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                conformance.load_contracts(path)

    def test_canonical_json_is_sorted_and_reproducible(self) -> None:
        rendered = conformance.canonical_report({"z": 1, "a": {"d": 2, "b": 1}})
        self.assertEqual({"a": {"b": 1, "d": 2}, "z": 1}, json.loads(rendered))
        self.assertLess(rendered.index('"a"'), rendered.index('"z"'))

    def test_undocumented_discovered_behavior_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tool.py").write_text(
                "def interface(expected, undocumented):\n    return None\n",
                encoding="utf-8",
            )
            report = conformance.analyze(
                root,
                {
                    "contracts": [
                        contract("EXTRA", "tool.py", ["expected"])
                    ]
                },
            )
            self.assertEqual(1, report["summary"]["undocumented_behavior"])
            self.assertEqual(
                "undocumented",
                report["undocumented_implementation_behavior"][0]["observed"],
            )


if __name__ == "__main__":
    unittest.main()
