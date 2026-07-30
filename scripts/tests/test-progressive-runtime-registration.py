#!/usr/bin/env python3
"""Qualification for the Progressive Runtime consumer registration contract."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    REGISTRY_PATH,
    RuntimeRegistrationError,
    validate,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeRegistrationTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        registry = root / REGISTRY_PATH
        registry.parent.mkdir(parents=True)
        shutil.copy2(ROOT / REGISTRY_PATH, registry)
        return root

    def registry(self, root: Path) -> tuple[Path, dict]:
        path = root / REGISTRY_PATH
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write_registry(self, path: Path, value: dict) -> None:
        path.write_text(
            json.dumps(value, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )

    def test_repository_runtime_registration_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["consumer_count"], 17)
        self.assertEqual(len(result["production_consumers"]), 15)
        self.assertEqual(
            result["compatibility_consumers"],
            [
                "scripts.lib.emp.oa02_lifecycle",
                "scripts.lib.emp.progressive_oa",
            ],
        )

    def test_repeated_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_governance_qualification_requires_no_consumer_sources(self) -> None:
        root = self.fixture()
        self.assertFalse((root / "scripts/lib").exists())
        result = validate(root)
        self.assertEqual(
            result["implementation_synchronization"],
            "DEFERRED_TO_CONSUMER_PUBLICATION",
        )

    def test_unregistered_interface_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["consumers"][0]["interfaces"] = ["scripts.lib.emp.unregistered"]
        self.write_registry(path, value)
        with self.assertRaisesRegex(
            RuntimeRegistrationError, "unregistered runtime interface"
        ):
            validate(root)

    def test_duplicate_registration_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["consumers"].append(value["consumers"][0])
        self.write_registry(path, value)
        with self.assertRaisesRegex(RuntimeRegistrationError, "duplicate"):
            validate(root)

    def test_nonexistent_layer_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["consumers"][0]["runtime_layers"] = [4]
        self.write_registry(path, value)
        with self.assertRaisesRegex(RuntimeRegistrationError, "nonexistent"):
            validate(root)

    def test_invalid_registry_entry_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["consumers"][0]["consumer_type"] = "foundation"
        self.write_registry(path, value)
        with self.assertRaisesRegex(RuntimeRegistrationError, "invalid"):
            validate(root)

    def test_invalid_registry_is_rejected(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeRegistrationError, "invalid"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeRegistrationError, "incomplete"):
            validate(root)

    def test_registry_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["consumers"][0], value["consumers"][1] = (
            value["consumers"][1],
            value["consumers"][0],
        )
        self.write_registry(path, value)
        with self.assertRaisesRegex(RuntimeRegistrationError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
