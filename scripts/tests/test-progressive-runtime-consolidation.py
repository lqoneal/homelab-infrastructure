#!/usr/bin/env python3
"""T15 qualification for the consolidated Progressive Runtime baseline."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_consolidation import (
    INDEX_PATH,
    REGISTRIES,
    SPEC_PATH,
    RuntimeConsolidationError,
    validate,
)


ROOT = Path(__file__).resolve().parents[2]


class ProgressiveRuntimeConsolidationTests(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in (
            "scripts/lib/emp/progressive_gate.py",
            "scripts/lib/emp/progressive_lifecycle.py",
            "scripts/lib/emp/progressive_runtime_support.py",
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        shutil.copytree(
            ROOT / "scripts/lib/authority_pipeline",
            root / "scripts/lib/authority_pipeline",
        )
        for relative in (*REGISTRIES, SPEC_PATH, INDEX_PATH):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return root

    def test_complete_runtime_baseline_passes(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["baseline"], "Progressive Runtime Governance Baseline v1.0"
        )
        self.assertEqual(len(result["chain"]), 9)
        self.assertEqual(len(result["registry_sha256"]), 8)
        self.assertEqual(
            result["analyses"]["registration"]["implementation_synchronization"],
            "DEFERRED_TO_CONSUMER_PUBLICATION",
        )

    def test_complete_runtime_baseline_requires_no_consumer_implementation(
        self,
    ) -> None:
        result = validate(self.fixture())
        self.assertEqual(result["status"], "PASS")

    def test_repeated_qualification_is_byte_deterministic(self) -> None:
        first = json.dumps(validate(ROOT), sort_keys=True, separators=(",", ":"))
        second = json.dumps(validate(ROOT), sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)

    def test_missing_registry_fails_closed(self) -> None:
        root = self.fixture()
        (root / REGISTRIES[-1]).unlink()
        with self.assertRaisesRegex(RuntimeConsolidationError, "incomplete"):
            validate(root)

    def test_stale_registry_fails_closed(self) -> None:
        root = self.fixture()
        path = root / REGISTRIES[-2]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["execution_contracts"][0]["completion_criteria"].append("stale")
        value["execution_contracts"][0]["completion_criteria"].sort()
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeConsolidationError, "stale"):
            validate(root)

    def test_duplicate_ownership_fails_closed(self) -> None:
        root = self.fixture()
        path = root / REGISTRIES[-2]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["execution_contracts"].append(value["execution_contracts"][0])
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeConsolidationError, "duplicate"):
            validate(root)

    def test_broken_traceability_fails_closed(self) -> None:
        root = self.fixture()
        path = root / REGISTRIES[-1]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["outcomes"][0]["owning_runtime_execution_contract"] = "absent"
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeConsolidationError, "nonexistent"):
            validate(root)

    def test_nondeterministic_order_fails_closed(self) -> None:
        root = self.fixture()
        path = root / REGISTRIES[-1]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["outcomes"].reverse()
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeConsolidationError, "ordered"):
            validate(root)

    def test_missing_document_reference_fails_closed(self) -> None:
        root = self.fixture()
        path = root / INDEX_PATH
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Progressive Runtime Governance Baseline v1.0", "missing-baseline"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            RuntimeConsolidationError, "missing documentation reference"
        ):
            validate(root)

    def test_inconsistent_documentation_fails_closed(self) -> None:
        root = self.fixture()
        path = root / SPEC_PATH
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Runtime Outcomes are architecture metadata only",
                "Runtime Outcomes execute production behavior",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            RuntimeConsolidationError, "inconsistent documentation"
        ):
            validate(root)


if __name__ == "__main__":
    unittest.main()
