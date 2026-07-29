#!/usr/bin/env python3
"""Regression tests for additive controlled-document semantic validation."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/validate_controlled_documents.py"
SPEC = importlib.util.spec_from_file_location("controlled_document_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class SemanticValidationTests(unittest.TestCase):
    def test_catalog_has_required_profiles_and_resolved_criteria(self) -> None:
        catalog = validator.load_semantic_catalog()
        expected = {
            "Standard",
            "Specification",
            "Procedure",
            "Policy",
            "Template",
            "WOP",
            "Roadmap",
            "Gate Specification",
            "Operator Verification Guide",
            "Completion Report",
        }
        self.assertEqual(expected, set(catalog["profiles"]))
        criteria = catalog["criteria"]
        for profile in catalog["profiles"].values():
            self.assertTrue(profile["criteria"])
            self.assertTrue(all(item in criteria for item in profile["criteria"]))
            self.assertTrue(
                {
                    "required_engineering_content",
                    "required_traceability",
                    "required_evidence",
                    "required_command_documentation",
                    "required_validation_criteria",
                    "required_acceptance_criteria",
                }.issubset(profile)
            )
        for definition in criteria.values():
            self.assertTrue(
                {
                    "identifier",
                    "description",
                    "applicability",
                    "validation_method",
                    "automation",
                    "required_evidence",
                    "fail_condition",
                    "remediation_guidance",
                }.issubset(definition)
            )

    def test_coverage_report_is_machine_readable_and_complete(self) -> None:
        report = validator.coverage_report(validator.load_semantic_catalog())
        serialized = json.loads(json.dumps(report))
        self.assertEqual(1, serialized["schema_version"])
        self.assertEqual("SPEC-0001", serialized["authority"])
        self.assertEqual(
            set(validator.load_semantic_catalog()["criteria"]),
            {row["criterion"] for row in serialized["criteria"]},
        )
        self.assertTrue(
            all(
                row["coverage"]
                in {"automated", "manual", "partially_automated", "not_automated"}
                for row in serialized["criteria"]
            )
        )

    def test_profile_resolution_and_fail_closed_missing_content(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "ROADMAP.md"
            path.write_text("# Roadmap\n\nObjective only.\n", encoding="utf-8")
            validation = validator.Validation()
            result = validator.semantic_validate_path(
                validation,
                path,
                validator.load_semantic_catalog(),
            )
            self.assertEqual("Roadmap", result["profile"])
            self.assertEqual("FAIL", result["status"])
            self.assertTrue(validation.errors)

    def test_gate_commands_are_inspected_without_execution(self) -> None:
        self.assertTrue(validator.command_exists("python3 --help"))
        self.assertTrue(validator.command_exists("zeus --help"))
        self.assertFalse(validator.command_exists("definitely-not-a-repository-command --help"))
        valid, evidence = validator.command_interface_check(
            "zeus approve OA-01 --operator OPERATOR",
            "PASS returns exit status 0; validation failure is nonzero.",
        )
        self.assertTrue(valid, evidence)
        self.assertEqual("interface_only", evidence["execution_mode"])
        undocumented, _ = validator.command_interface_check(
            "zeus approve OA-01 --operator OPERATOR",
            "Approve the gate.",
        )
        self.assertFalse(undocumented)


if __name__ == "__main__":
    unittest.main()
