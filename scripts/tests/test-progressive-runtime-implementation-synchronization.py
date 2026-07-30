#!/usr/bin/env python3
"""Downstream synchronization tests for Progressive Runtime consumers."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    REGISTRY_PATH,
    RuntimeRegistrationError,
    validate_implementation,
)
from scripts.lib.authority_pipeline.progressive_runtime_dependencies import (
    validate_implementation as validate_compatibility_implementation,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeImplementationSynchronizationTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        registry = root / REGISTRY_PATH
        registry.parent.mkdir(parents=True)
        shutil.copy2(ROOT / REGISTRY_PATH, registry)
        return root

    def test_repository_implementation_synchronization_passes(self) -> None:
        result = validate_implementation(ROOT)
        self.assertEqual(result["implementation_synchronization"], "PASS")

    def test_repository_compatibility_synchronization_passes(self) -> None:
        result = validate_compatibility_implementation(ROOT)
        self.assertEqual(result["compatibility_synchronization"], "PASS")

    def test_interface_bypass_is_rejected(self) -> None:
        root = self.fixture()
        consumer = root / "scripts/lib/emp/controlled_mission_authority.py"
        consumer.write_text(
            consumer.read_text(encoding="utf-8")
            + "\nfrom scripts.lib.emp import progressive_lifecycle\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            RuntimeRegistrationError, "bypasses registered runtime interfaces"
        ):
            validate_implementation(root)

    def test_stale_registry_entry_is_rejected(self) -> None:
        root = self.fixture()
        path = root / REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["consumers"].append(
            {
                "consumer": "scripts.lib.emp.agent_qualification",
                "consumer_type": "production",
                "runtime_layers": [1, 2],
                "interfaces": ["scripts.lib.emp.progressive_oa"],
            }
        )
        value["consumers"].sort(key=lambda item: item["consumer"])
        path.write_text(
            json.dumps(value, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeRegistrationError, "without runtime"):
            validate_implementation(root)


if __name__ == "__main__":
    unittest.main()
