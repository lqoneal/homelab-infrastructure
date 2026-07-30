#!/usr/bin/env python3
"""T11 qualification for Progressive Runtime transition governance."""

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
    REGISTRY_PATH as POLICY_REGISTRY_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    REGISTRY_PATH as CONSUMER_REGISTRY_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_states import (
    REGISTRY_PATH as STATE_REGISTRY_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_transitions import (
    REGISTRY_PATH,
    RuntimeTransitionError,
    validate,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeTransitionTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (
            REGISTRY_PATH,
            STATE_REGISTRY_PATH,
            POLICY_REGISTRY_PATH,
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

    def synchronize_state_digest(self, root: Path) -> None:
        path, value = self.registry(root)
        value["state_registry_sha256"] = hashlib.sha256(
            (root / STATE_REGISTRY_PATH).read_bytes()
        ).hexdigest()
        self.write(path, value)

    def test_repository_transition_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["transition_count"], 2)
        self.assertEqual(result["state_count"], 3)
        self.assertEqual(result["policy_count"], 3)
        self.assertEqual(len(result["state_transitions"]), 3)

    def test_repeated_transition_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_undefined_transition_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "undefined"):
            validate(root)

    def test_duplicate_transition_identifier_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"].append(value["transitions"][0])
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "duplicate"):
            validate(root)

    def test_nonexistent_source_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["source_runtime_state"] = "ABSENT"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "nonexistent"):
            validate(root)

    def test_nonexistent_destination_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["destination_runtime_state"] = "ABSENT"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "nonexistent"):
            validate(root)

    def test_invalid_source_destination_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["destination_runtime_state"] = (
            "LIFECYCLE_PROJECTION_ELIGIBLE"
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "state graph"):
            validate(root)

    def test_duplicate_edge_ownership_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        duplicate = json.loads(json.dumps(value["transitions"][0]))
        duplicate["transition_identifier"] = "transition-duplicate-owner"
        value["transitions"].append(duplicate)
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "multiple owners"):
            validate(root)

    def test_missing_guard_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["guard_conditions"] = []
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "guard"):
            validate(root)

    def test_incomplete_state_guard_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["guard_conditions"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "guard"):
            validate(root)

    def test_missing_evidence_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["required_evidence"] = []
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "evidence"):
            validate(root)

    def test_missing_approval_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0].pop("approval_requirements")
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "approval"):
            validate(root)

    def test_invalid_approval_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["approval_requirements"]["state"] = "NOT_REQUIRED"
        value["transitions"][0]["approval_requirements"]["authority_level"] = None
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "approval"):
            validate(root)

    def test_missing_rollback_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0].pop("rollback_behavior")
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "rollback"):
            validate(root)

    def test_invalid_rollback_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["rollback_behavior"]["mode"] = "CONTINUE"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "rollback"):
            validate(root)

    def test_transition_invariant_violation_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["transition_invariants"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "invariant"):
            validate(root)

    def test_transition_state_policy_ownership_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"][0]["governing_runtime_policies"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "ownership"):
            validate(root)

    def test_stale_registry_is_rejected(self) -> None:
        root = self.fixture()
        state_path = root / STATE_REGISTRY_PATH
        value = json.loads(state_path.read_text(encoding="utf-8"))
        value["states"][0]["exit_conditions"].append("new-condition")
        value["states"][0]["exit_conditions"].sort()
        self.write(state_path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "stale"):
            validate(root)

    def test_state_graph_change_without_transition_is_rejected(self) -> None:
        root = self.fixture()
        state_path = root / STATE_REGISTRY_PATH
        value = json.loads(state_path.read_text(encoding="utf-8"))
        value["states"][0]["permitted_successor_states"].append(
            "LIFECYCLE_PROJECTION_ELIGIBLE"
        )
        value["states"][0]["permitted_successor_states"].sort()
        value["states"][2]["permitted_predecessor_states"].append(
            "AUTHORITY_CONTEXT_VALIDATED"
        )
        value["states"][2]["permitted_predecessor_states"].sort()
        self.write(state_path, value)
        self.synchronize_state_digest(root)
        with self.assertRaisesRegex(RuntimeTransitionError, "undefined"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeTransitionError, "incomplete"):
            validate(root)

    def test_transition_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["transitions"].reverse()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeTransitionError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
