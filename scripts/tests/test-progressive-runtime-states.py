#!/usr/bin/env python3
"""T10 qualification for Progressive Runtime operational-state governance."""

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
    REGISTRY_PATH,
    RuntimeStateError,
    validate,
    validate_execution_eligibility,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeStateTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (
            REGISTRY_PATH,
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

    def synchronize_policy_digest(self, root: Path) -> None:
        path, value = self.registry(root)
        value["policy_registry_sha256"] = hashlib.sha256(
            (root / POLICY_REGISTRY_PATH).read_bytes()
        ).hexdigest()
        self.write(path, value)

    def test_repository_state_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["state_count"], 3)
        self.assertEqual(result["policy_count"], 3)
        self.assertEqual(result["initial_state"], "AUTHORITY_CONTEXT_VALIDATED")
        self.assertEqual(len(result["transitions"]), 2)

    def test_repeated_state_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_authorized_execution_is_accepted(self) -> None:
        result = validate_execution_eligibility(
            ROOT,
            "policy-progressive-decision-authority",
            "DECISION_AUTHORIZED",
        )
        self.assertEqual(result["status"], "AUTHORIZED")

    def test_execution_outside_authorized_state_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeStateError, "outside authorized"):
            validate_execution_eligibility(
                ROOT,
                "policy-progressive-decision-authority",
                "AUTHORITY_CONTEXT_VALIDATED",
            )

    def test_undefined_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0]["state_identifier"] = ""
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "undefined"):
            validate(root)

    def test_duplicate_state_identifier_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"].append(value["states"][0])
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "duplicate"):
            validate(root)

    def test_invalid_predecessor_reference_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][1]["permitted_predecessor_states"] = ["ABSENT"]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "predecessor"):
            validate(root)

    def test_invalid_successor_reference_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0]["permitted_successor_states"] = ["ABSENT"]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "successor"):
            validate(root)

    def test_transition_reciprocity_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0]["permitted_successor_states"] = []
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "reciprocity"):
            validate(root)

    def test_unreachable_state_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"].append(
            {
                "state_identifier": "UNREACHABLE",
                "permitted_predecessor_states": [],
                "permitted_successor_states": [],
                "entry_conditions": ["never"],
                "exit_conditions": ["never"],
                "required_invariants": ["runtime-integrity-preserved"],
                "permitted_runtime_policies": [
                    "policy-progressive-lifecycle-projection"
                ],
            }
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "unreachable"):
            validate(root)

    def test_illegal_transition_cycle_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0]["permitted_predecessor_states"] = [
            "LIFECYCLE_PROJECTION_ELIGIBLE"
        ]
        value["states"][2]["permitted_successor_states"] = [
            "AUTHORITY_CONTEXT_VALIDATED"
        ]
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "cycle"):
            validate(root)

    def test_policy_nonexistent_state_is_rejected(self) -> None:
        root = self.fixture()
        policy_path = root / POLICY_REGISTRY_PATH
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["policies"][1]["runtime_states"] = ["ABSENT"]
        self.write(policy_path, policy)
        self.synchronize_policy_digest(root)
        with self.assertRaisesRegex(RuntimeStateError, "nonexistent states"):
            validate(root)

    def test_policy_state_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        policy_path = root / POLICY_REGISTRY_PATH
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["policies"][0]["runtime_states"] = ["AUTHORITY_CONTEXT_VALIDATED"]
        self.write(policy_path, policy)
        self.synchronize_policy_digest(root)
        with self.assertRaisesRegex(RuntimeStateError, "policy/state mismatch"):
            validate(root)

    def test_invalid_invariant_metadata_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0]["required_invariants"] = []
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "invariants"):
            validate(root)

    def test_stale_registry_is_rejected(self) -> None:
        root = self.fixture()
        policy_path = root / POLICY_REGISTRY_PATH
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["policies"][0]["execution_constraints"].append(
            "state-governance-required"
        )
        policy["policies"][0]["execution_constraints"].sort()
        self.write(policy_path, policy)
        with self.assertRaisesRegex(RuntimeStateError, "stale"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeStateError, "incomplete"):
            validate(root)

    def test_state_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["states"][0], value["states"][1] = (
            value["states"][1],
            value["states"][0],
        )
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeStateError, "ordered"):
            validate(root)

    def test_undefined_execution_policy_and_state_fail_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeStateError, "undefined runtime policy"):
            validate_execution_eligibility(ROOT, "ABSENT", "DECISION_AUTHORIZED")
        with self.assertRaisesRegex(RuntimeStateError, "undefined runtime state"):
            validate_execution_eligibility(
                ROOT, "policy-progressive-decision-authority", "ABSENT"
            )


if __name__ == "__main__":
    unittest.main()
