#!/usr/bin/env python3
"""T13 qualification for Progressive Runtime outcome governance."""

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
from scripts.lib.authority_pipeline.progressive_runtime_execution_contracts import (
    REGISTRY_PATH as CONTRACT_REGISTRY_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_outcomes import (
    REGISTRY_PATH,
    RuntimeOutcomeError,
    validate,
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
    REGISTRY_PATH as TRANSITION_REGISTRY_PATH,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeOutcomeTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (
            REGISTRY_PATH,
            CONTRACT_REGISTRY_PATH,
            TRANSITION_REGISTRY_PATH,
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

    def synchronize_contract_digest(self, root: Path) -> None:
        path, value = self.registry(root)
        value["execution_contract_registry_sha256"] = hashlib.sha256(
            (root / CONTRACT_REGISTRY_PATH).read_bytes()
        ).hexdigest()
        self.write(path, value)

    def mutate_outcome(self, field: str, value: object = None) -> Path:
        root = self.fixture()
        path, registry = self.registry(root)
        if value is None:
            registry["outcomes"][0].pop(field)
        else:
            registry["outcomes"][0][field] = value
        self.write(path, registry)
        return root

    def test_repository_outcome_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome_count"], 4)
        self.assertEqual(result["execution_contract_count"], 2)
        self.assertEqual(len(result["contract_outcomes"]), 2)
        self.assertEqual(len(result["outcome_contracts"]), 4)

    def test_repeated_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_undefined_outcome_is_rejected(self) -> None:
        root = self.mutate_outcome("outcome_identifier")
        with self.assertRaisesRegex(RuntimeOutcomeError, "undefined"):
            validate(root)

    def test_duplicate_outcome_identifier_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["outcomes"].append(value["outcomes"][0])
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeOutcomeError, "duplicate"):
            validate(root)

    def test_contract_without_outcome_is_rejected(self) -> None:
        root = self.fixture()
        path = root / CONTRACT_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["execution_contracts"][0]["runtime_outcome_identifiers"] = []
        self.write(path, value)
        self.synchronize_contract_digest(root)
        with self.assertRaisesRegex(RuntimeOutcomeError, "without"):
            validate(root)

    def test_nonexistent_execution_contract_is_rejected(self) -> None:
        root = self.mutate_outcome(
            "owning_runtime_execution_contract", "execution-contract-absent"
        )
        with self.assertRaisesRegex(RuntimeOutcomeError, "nonexistent"):
            validate(root)

    def test_contract_reference_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path = root / CONTRACT_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["execution_contracts"][0]["runtime_outcome_identifiers"].pop()
        self.write(path, value)
        self.synchronize_contract_digest(root)
        with self.assertRaisesRegex(RuntimeOutcomeError, "ownership"):
            validate(root)

    def test_invalid_classification_is_rejected(self) -> None:
        root = self.mutate_outcome("outcome_classification", "IMPLEMENTED")
        with self.assertRaisesRegex(RuntimeOutcomeError, "classification"):
            validate(root)

    def test_missing_resulting_state_is_rejected(self) -> None:
        root = self.mutate_outcome("resulting_runtime_state")
        with self.assertRaisesRegex(RuntimeOutcomeError, "resulting"):
            validate(root)

    def test_nonexistent_resulting_state_is_rejected(self) -> None:
        root = self.mutate_outcome("resulting_runtime_state", "ABSENT")
        with self.assertRaisesRegex(RuntimeOutcomeError, "resulting"):
            validate(root)

    def test_missing_evidence_is_rejected(self) -> None:
        root = self.mutate_outcome("required_evidence", [])
        with self.assertRaisesRegex(RuntimeOutcomeError, "evidence"):
            validate(root)

    def test_nondeterministic_evidence_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["outcomes"][0]["required_evidence"].reverse()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeOutcomeError, "evidence"):
            validate(root)

    def test_missing_completion_criteria_is_rejected(self) -> None:
        root = self.mutate_outcome("completion_criteria", [])
        with self.assertRaisesRegex(RuntimeOutcomeError, "completion"):
            validate(root)

    def test_missing_invariants_is_rejected(self) -> None:
        root = self.mutate_outcome("invariant_requirements", [])
        with self.assertRaisesRegex(RuntimeOutcomeError, "invariant"):
            validate(root)

    def test_state_invariant_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["outcomes"][0]["invariant_requirements"].append("unknown-invariant")
        value["outcomes"][0]["invariant_requirements"].sort()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeOutcomeError, "mismatch"):
            validate(root)

    def test_invalid_authorization_effect_is_rejected(self) -> None:
        root = self.mutate_outcome("downstream_authorization_effect", "DEFERRED")
        with self.assertRaisesRegex(RuntimeOutcomeError, "authorization"):
            validate(root)

    def test_invalid_lifecycle_effect_is_rejected(self) -> None:
        root = self.mutate_outcome("lifecycle_projection_effect", "PROJECT")
        with self.assertRaisesRegex(RuntimeOutcomeError, "lifecycle"):
            validate(root)

    def test_stale_registry_is_rejected(self) -> None:
        root = self.fixture()
        path = root / CONTRACT_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["execution_contracts"][0]["completion_criteria"].append(
            "new-completion-criterion"
        )
        value["execution_contracts"][0]["completion_criteria"].sort()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeOutcomeError, "stale"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeOutcomeError, "incomplete"):
            validate(root)

    def test_outcome_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["outcomes"].reverse()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeOutcomeError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
