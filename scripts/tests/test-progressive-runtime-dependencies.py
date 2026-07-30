#!/usr/bin/env python3
"""Qualification for the Progressive Runtime Layer dependency contract."""

from __future__ import annotations

import shutil
import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_dependencies import (
    DependencyContractError,
    validate,
    validate_implementation,
)


ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "engineering/architecture/progressive-runtime-classification.json",
    "scripts/lib/emp/progressive_gate.py",
    "scripts/lib/emp/progressive_lifecycle.py",
    "scripts/lib/emp/progressive_runtime_support.py",
)


class ProgressiveRuntimeDependencyTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        for relative in FILES:
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return directory

    def test_repository_dependency_contract_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runtime_layer_count"], 3)
        self.assertEqual(
            [item["name"] for item in result["runtime_layers"]],
            [
                "Progressive Authority Primitives",
                "Progressive Decision Authority",
                "Progressive Lifecycle Projection",
            ],
        )
        self.assertEqual(
            result["runtime_edges"],
            {
                "scripts.lib.emp.progressive_gate": [],
                "scripts.lib.emp.progressive_lifecycle": [
                    "scripts.lib.emp.progressive_gate"
                ],
            },
        )

    def test_runtime_compatibility_leakage_fails_closed(self) -> None:
        root = self.fixture()
        path = root / "scripts/lib/emp/progressive_gate.py"
        path.write_text(
            path.read_text()
            + "\nfrom scripts.lib.emp import progressive_oa\n"
        )
        with self.assertRaisesRegex(
            DependencyContractError, "consumes compatibility"
        ):
            validate(root)

    def test_upward_dependency_fails_closed(self) -> None:
        root = self.fixture()
        path = root / "scripts/lib/emp/progressive_gate.py"
        path.write_text(
            path.read_text()
            + "\nfrom scripts.lib.emp import progressive_lifecycle\n"
        )
        with self.assertRaisesRegex(DependencyContractError, "upward"):
            validate(root)

    def test_runtime_cycle_fails_closed(self) -> None:
        root = self.fixture()
        gate = root / "scripts/lib/emp/progressive_gate.py"
        gate.write_text(
            gate.read_text()
            + "\nfrom scripts.lib.emp import progressive_lifecycle\n"
        )
        with self.assertRaises(DependencyContractError):
            validate(root)

    def test_foundation_cannot_consume_runtime_or_compatibility(self) -> None:
        root = self.fixture()
        path = root / "scripts/lib/emp/progressive_runtime_support.py"
        path.write_text(
            path.read_text()
            + "\nfrom scripts.lib.emp import progressive_gate\n"
        )
        with self.assertRaisesRegex(DependencyContractError, "foundational"):
            validate(root)

    def test_projection_cannot_duplicate_authority(self) -> None:
        root = self.fixture()
        path = root / "scripts/lib/emp/progressive_lifecycle.py"
        path.write_text(path.read_text() + "\ndef decide():\n    pass\n")
        with self.assertRaisesRegex(
            DependencyContractError, "duplicates authority ownership"
        ):
            validate(root)

    def test_missing_validation_input_fails_closed(self) -> None:
        root = self.fixture()
        (root / "scripts/lib/emp/progressive_lifecycle.py").unlink()
        with self.assertRaisesRegex(DependencyContractError, "incomplete"):
            validate(root)

    def test_governance_qualification_requires_no_compatibility_sources(self) -> None:
        root = self.fixture()
        result = validate(root)
        self.assertEqual(
            result["compatibility_synchronization"],
            "DEFERRED_TO_CONSUMER_PUBLICATION",
        )
        with self.assertRaisesRegex(
            DependencyContractError, "compatibility validation input is incomplete"
        ):
            validate_implementation(root)

    def classification(self, root: Path) -> tuple[Path, dict]:
        path = (
            root
            / "engineering/architecture/progressive-runtime-classification.json"
        )
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write_classification(self, path: Path, value: dict) -> None:
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_fourth_runtime_layer_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.classification(root)
        value["runtime_layers"].append(
            {
                "layer": 4,
                "name": "Unauthorized Runtime Layer",
                "modules": ["scripts.lib.emp.progressive_runtime_support"],
            }
        )
        self.write_classification(path, value)
        with self.assertRaisesRegex(
            DependencyContractError, "exactly the three canonical"
        ):
            validate(root)

    def test_runtime_layer_reclassification_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.classification(root)
        value["runtime_layers"][2]["name"] = "Progressive Decision Authority"
        self.write_classification(path, value)
        with self.assertRaisesRegex(
            DependencyContractError, "exactly the three canonical"
        ):
            validate(root)

    def test_compatibility_misclassification_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.classification(root)
        value["compatibility_adapters"].remove(
            "scripts.lib.emp.progressive_oa"
        )
        value["foundational_shared_utilities"].append(
            "scripts.lib.emp.progressive_oa"
        )
        self.write_classification(path, value)
        with self.assertRaisesRegex(
            DependencyContractError, "foundational_shared_utilities"
        ):
            validate(root)

    def test_foundational_utility_misclassification_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.classification(root)
        value["foundational_shared_utilities"].clear()
        value["compatibility_adapters"].append(
            "scripts.lib.emp.progressive_runtime_support"
        )
        self.write_classification(path, value)
        with self.assertRaisesRegex(
            DependencyContractError, "foundational_shared_utilities"
        ):
            validate(root)

    def test_qualification_infrastructure_cannot_be_runtime(self) -> None:
        root = self.fixture()
        path, value = self.classification(root)
        value["runtime_layers"][2]["modules"].append(
            "scripts.lib.authority_pipeline.progressive_runtime_dependencies"
        )
        self.write_classification(path, value)
        with self.assertRaisesRegex(
            DependencyContractError, "exactly the three canonical"
        ):
            validate(root)

    def test_invalid_classification_fails_closed(self) -> None:
        root = self.fixture()
        path, _ = self.classification(root)
        path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(DependencyContractError, "invalid"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
