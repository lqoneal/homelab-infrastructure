#!/usr/bin/env python3
"""T09 qualification for Progressive Runtime policy governance."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_capabilities import (
    REGISTRY_PATH as CAPABILITY_REGISTRY_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_dependencies import (
    CLASSIFICATION_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_policies import (
    REGISTRY_PATH,
    RuntimePolicyError,
    validate,
)
from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    REGISTRY_PATH as CONSUMER_REGISTRY_PATH,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimePolicyTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (
            REGISTRY_PATH,
            CAPABILITY_REGISTRY_PATH,
            CLASSIFICATION_PATH,
            CONSUMER_REGISTRY_PATH,
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return root

    def registry(self, root: Path) -> tuple[Path, dict]:
        path = root / REGISTRY_PATH
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write(self, path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_repository_policy_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["policy_count"], 3)
        self.assertEqual(result["capability_count"], 3)
        self.assertEqual(len(result["capability_policies"]), 3)

    def test_repeated_policy_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_undefined_policy_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["policy_identifier"] = ""
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "undefined"):
            validate(root)

    def test_duplicate_policy_identifier_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        duplicate = dict(value["policies"][1])
        duplicate["governed_capability"] = value["policies"][0][
            "governed_capability"
        ]
        value["policies"].append(duplicate)
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "duplicate"):
            validate(root)

    def test_capability_without_policy_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "without governing"):
            validate(root)

    def test_conflicting_policy_assignment_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][2]["governed_capability"] = value["policies"][1][
            "governed_capability"
        ]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "conflicting"):
            validate(root)

    def test_nonexistent_capability_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["governed_capability"] = "absent-capability"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "nonexistent"):
            validate(root)

    def test_invalid_authority_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["required_authority_level"] = "UNDEFINED"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "authority"):
            validate(root)

    def test_invalid_approval_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["approval_requirements"]["state"] = "PENDING"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "approval"):
            validate(root)

    def test_invalid_approval_authority_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][1]["approval_requirements"]["authority_level"] = (
            "CONTROLLED_MISSION_AUTHORITY"
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "approval"):
            validate(root)

    def test_invalid_lifecycle_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["lifecycle_state"] = "STALE"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "lifecycle"):
            validate(root)

    def test_inconsistent_eligibility_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0]["eligibility_requirements"][
            "capability_registered"
        ] = False
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "eligibility"):
            validate(root)

    def test_stale_policy_registration_is_rejected(self) -> None:
        root = self.fixture()
        capability_path = root / CAPABILITY_REGISTRY_PATH
        capability = json.loads(capability_path.read_text(encoding="utf-8"))
        capability["capabilities"][0]["interfaces"].reverse()
        self.write(capability_path, capability)
        with self.assertRaisesRegex(RuntimePolicyError, "stale"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimePolicyError, "incomplete"):
            validate(root)

    def test_policy_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["policies"][0], value["policies"][1] = (
            value["policies"][1],
            value["policies"][0],
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimePolicyError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
