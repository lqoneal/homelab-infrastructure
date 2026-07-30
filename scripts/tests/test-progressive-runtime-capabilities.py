#!/usr/bin/env python3
"""T08 qualification for Progressive Runtime capability governance."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_capabilities import (
    REGISTRY_PATH,
    RuntimeCapabilityError,
    validate,
)
from scripts.lib.authority_pipeline.progressive_runtime_dependencies import (
    CLASSIFICATION_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    REGISTRY_PATH as CONSUMER_REGISTRY_PATH,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeCapabilityTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (REGISTRY_PATH, CLASSIFICATION_PATH, CONSUMER_REGISTRY_PATH):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return root

    def registry(self, root: Path) -> tuple[Path, dict]:
        path = root / REGISTRY_PATH
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write(self, path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_repository_capability_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["capability_count"], 3)
        self.assertEqual(result["consumer_count"], 17)
        self.assertTrue(all(result["consumer_capabilities"].values()))

    def test_repeated_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_undefined_capability_shape_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][0]["capability"] = ""
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "invalid"):
            validate(root)

    def test_duplicate_capability_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"].append(value["capabilities"][0])
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "duplicate"):
            validate(root)

    def test_consumer_nonexistent_capability_is_rejected(self) -> None:
        root = self.fixture()
        path = root / CONSUMER_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["capability_declarations"][
            "scripts.lib.emp.next_action"
        ] = ["undefined-capability"]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "nonexistent"):
            validate(root)

    def test_orphaned_capability_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][0]["runtime_owners"] = [
            "scripts.lib.emp.progressive_lifecycle"
        ]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "owner mismatch"):
            validate(root)

    def test_capability_to_layer_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][0]["runtime_layers"] = [3]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "owner mismatch"):
            validate(root)

    def test_consumer_capability_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][2]["consumers"].append(
            "scripts.lib.emp.controlled_mission_authority"
        )
        value["capabilities"][2]["consumers"].sort()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "consumer capability"):
            validate(root)

    def test_interface_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][2]["interfaces"] = [
            "scripts.lib.emp.progressive_gate"
        ]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "interface mismatch"):
            validate(root)

    def test_stale_capability_registration_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][0]["consumers"].append("scripts.lib.emp.absent")
        value["capabilities"][0]["consumers"].sort()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "stale"):
            validate(root)

    def test_consumer_without_capability_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        consumer = "scripts.lib.emp.controlled_mission_authority"
        for capability in value["capabilities"]:
            capability["consumers"] = [
                item for item in capability["consumers"] if item != consumer
            ]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "not synchronized"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeCapabilityError, "incomplete"):
            validate(root)

    def test_registry_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["capabilities"][0], value["capabilities"][1] = (
            value["capabilities"][1],
            value["capabilities"][0],
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeCapabilityError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
