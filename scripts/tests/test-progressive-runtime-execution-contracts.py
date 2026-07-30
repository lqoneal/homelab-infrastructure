#!/usr/bin/env python3
"""T12 qualification for Progressive Runtime execution-contract governance."""

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
    REGISTRY_PATH,
    RuntimeExecutionContractError,
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


class ProgressiveRuntimeExecutionContractTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / "scripts/lib", root / "scripts/lib")
        for relative in (
            REGISTRY_PATH,
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

    def synchronize_transition_digest(self, root: Path) -> None:
        path, value = self.registry(root)
        value["transition_registry_sha256"] = hashlib.sha256(
            (root / TRANSITION_REGISTRY_PATH).read_bytes()
        ).hexdigest()
        self.write(path, value)

    def mutate_contract(self, field: str, value: object = None) -> Path:
        root = self.fixture()
        path, registry = self.registry(root)
        if value is None:
            registry["execution_contracts"][0].pop(field)
        else:
            registry["execution_contracts"][0][field] = value
        self.write(path, registry)
        return root

    def test_repository_execution_contract_governance_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["execution_contract_count"], 2)
        self.assertEqual(result["transition_count"], 2)
        self.assertEqual(len(result["transition_contracts"]), 2)
        self.assertEqual(len(result["contract_transitions"]), 2)

    def test_repeated_analysis_is_deterministic(self) -> None:
        self.assertEqual(validate(ROOT), validate(ROOT))

    def test_undefined_contract_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"].pop()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "without"):
            validate(root)

    def test_duplicate_contract_identifier_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"].append(value["execution_contracts"][0])
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "duplicate"):
            validate(root)

    def test_nonexistent_transition_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["owning_runtime_transition"] = "ABSENT"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "nonexistent"):
            validate(root)

    def test_transition_reference_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path = root / TRANSITION_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["transitions"][0]["execution_contract_identifier"] = "ABSENT"
        self.write(path, value)
        self.synchronize_transition_digest(root)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "ownership"):
            validate(root)

    def test_missing_execution_phases_is_rejected(self) -> None:
        root = self.mutate_contract("execution_phases", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "phases"):
            validate(root)

    def test_noncanonical_phase_order_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["execution_phases"].reverse()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "phases"):
            validate(root)

    def test_missing_preconditions_is_rejected(self) -> None:
        root = self.mutate_contract("execution_preconditions", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "preconditions"):
            validate(root)

    def test_missing_checkpoints_is_rejected(self) -> None:
        root = self.mutate_contract("execution_checkpoints", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "checkpoints"):
            validate(root)

    def test_checkpoint_order_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["execution_checkpoints"][0]["order"] = 2
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "checkpoint"):
            validate(root)

    def test_checkpoint_without_evidence_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["execution_checkpoints"][0][
            "required_evidence"
        ] = []
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "checkpoint"):
            validate(root)

    def test_missing_required_evidence_is_rejected(self) -> None:
        root = self.mutate_contract("required_evidence", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "evidence"):
            validate(root)

    def test_missing_interruption_behavior_is_rejected(self) -> None:
        root = self.mutate_contract("interruption_behavior")
        with self.assertRaisesRegex(RuntimeExecutionContractError, "interruption"):
            validate(root)

    def test_invalid_interruptible_phase_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["interruption_behavior"][
            "interruptible_phases"
        ].append("UNKNOWN")
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "interruption"):
            validate(root)

    def test_missing_resume_behavior_is_rejected(self) -> None:
        root = self.mutate_contract("resume_behavior")
        with self.assertRaisesRegex(RuntimeExecutionContractError, "resume"):
            validate(root)

    def test_resume_restart_mismatch_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["resume_behavior"]["resume_phase"] = "PREPARE"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "resume"):
            validate(root)

    def test_missing_completion_criteria_is_rejected(self) -> None:
        root = self.mutate_contract("completion_criteria", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "completion"):
            validate(root)

    def test_missing_failure_criteria_is_rejected(self) -> None:
        root = self.mutate_contract("failure_criteria", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "failure"):
            validate(root)

    def test_missing_rollback_triggers_is_rejected(self) -> None:
        root = self.mutate_contract("rollback_triggers", [])
        with self.assertRaisesRegex(RuntimeExecutionContractError, "rollback"):
            validate(root)

    def test_invalid_rollback_checkpoint_is_rejected(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"][0]["rollback_triggers"][0][
            "rollback_checkpoint"
        ] = "ABSENT"
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "rollback"):
            validate(root)

    def test_stale_registry_is_rejected(self) -> None:
        root = self.fixture()
        path = root / TRANSITION_REGISTRY_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        value["transitions"][0]["guard_conditions"].append("new-condition")
        value["transitions"][0]["guard_conditions"].sort()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "stale"):
            validate(root)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRY_PATH).unlink()
        with self.assertRaisesRegex(RuntimeExecutionContractError, "incomplete"):
            validate(root)

    def test_contract_order_is_enforced(self) -> None:
        root = self.fixture()
        path, value = self.registry(root)
        value["execution_contracts"].reverse()
        self.write(path, value)
        with self.assertRaisesRegex(RuntimeExecutionContractError, "ordered"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
