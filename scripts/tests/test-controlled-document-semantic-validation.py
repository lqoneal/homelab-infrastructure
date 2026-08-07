#!/usr/bin/env python3
"""Regression tests for additive controlled-document semantic validation."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
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
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ROADMAP.md"
            path.write_text("# Roadmap\n\nObjective only.\n", encoding="utf-8")
            validation = validator.Validation()
            output = io.StringIO()
            with redirect_stdout(output):
                result = validator.semantic_validate_path(
                    validation,
                    path,
                    validator.load_semantic_catalog(),
                )
            self.assertEqual("Roadmap", result["profile"])
            self.assertEqual("FAIL", result["status"])
            self.assertTrue(validation.errors)
            expected = [
                error for error in validation.errors
                if "required semantic concept" in error
            ]
            self.assertEqual(
                {
                    "sequencing", "dependencies", "completion", "traceability"
                },
                {error.rsplit(" ", 1)[-1] for error in expected},
            )
            # The negative fixture is intentionally invalid. Keep the
            # validator fail-closed, but classify its captured diagnostics so
            # they cannot be mistaken for repository-level failures.
            self.assertIn("FAIL:", output.getvalue())
            for error in expected:
                print(f"EXPECTED_NEGATIVE_FIXTURE_FINDING: {error}")
            self.assertEqual(4, len(expected))

    def test_valid_roadmap_fixture_passes(self) -> None:
        validation = validator.Validation()
        result = validator.semantic_validate_path(
            validation,
            ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/ROADMAP.md",
            validator.load_semantic_catalog(),
        )
        self.assertEqual("Roadmap", result["profile"])
        self.assertIn(result["status"], {"PASS", "PASS_WITH_MANUAL_CRITERIA"})
        self.assertEqual([], validation.errors)

    def test_canonical_zeus_development_roadmap_resolves_to_roadmap_profile(self) -> None:
        path = ROOT / "engineering/docs/architecture/ZEUS-CANONICAL-DEVELOPMENT-ROADMAP.md"
        self.assertEqual("Roadmap", validator.semantic_profile_for(path))
        validation = validator.Validation()
        result = validator.semantic_validate_path(
            validation, path, validator.load_semantic_catalog()
        )
        self.assertEqual("Roadmap", result["profile"])
        self.assertIn(result["status"], {"PASS", "PASS_WITH_MANUAL_CRITERIA"})
        self.assertEqual([], validation.errors)

    def test_cli_propagates_real_semantic_failure_exit_code(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "ROADMAP.md"
            path.write_text("# Roadmap\n\nObjective only.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", "scripts/validate_controlled_documents.py",
                 "--semantic-path", str(path.relative_to(ROOT))],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Controlled-document checks failed:", result.stdout)

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
