#!/usr/bin/env python3
import json
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.assurance_language import AssuranceLanguage, AssuranceLanguageError
from scripts.lib.eos.execution_interface import ExecutionInterface, ExecutionInterfaceError
from scripts.lib.eos.mission_assurance import MissionAssurance, MissionAssuranceError


ZEUS = ROOT / "scripts/zeus"
MISSION = "P2-038-CORRECTIVE"


class ZeusMissionAssuranceTests(unittest.TestCase):
    def run_zeus(self, *arguments, expected=0):
        result = subprocess.run(
            [str(ZEUS), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={"PATH": "/usr/bin:/bin", "ZEUS_NO_INTRO": "1"},
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def test_capabilities_are_explicitly_read_only(self):
        result = self.run_zeus("assurance", "capabilities")
        self.assertEqual(result["mode"], "READ_ONLY_INDEPENDENT_VERIFICATION")
        self.assertEqual(result["lifecycle_ownership"], "PRESERVED")
        self.assertEqual(
            result["phases"],
            ["preflight", "execution", "synchronization", "closeout"],
        )
        self.assertEqual(result["language"]["id"], "CONTROLLED-MISSION-ASSURANCE-LANGUAGE")
        self.assertEqual(result["language"]["version"], "1.0")
        self.assertEqual(result["language"]["authoritative_source"]["document_id"], "SPEC-0013")

    def test_requirements_and_qualification_use_derived_cardinality(self):
        requirements = self.run_zeus("mission", "requirements", MISSION)
        qualification = self.run_zeus("mission", "qualify", MISSION)
        self.assertEqual(requirements["discovery"]["mission_contract_count"], 1)
        self.assertTrue(requirements["discovery"]["satisfied"])
        self.assertEqual(
            qualification["mission_contract_count"],
            len(qualification["mission_contract_discovery"]["candidate_paths"]),
        )

    def test_phase_results_fail_closed_and_are_deterministic(self):
        preflight = self.run_zeus("mission", "preflight", MISSION)
        synchronization = self.run_zeus("mission", "synchronization", MISSION)
        first = self.run_zeus("mission", "verify", MISSION, expected=78)
        second = self.run_zeus("mission", "verify", MISSION, expected=78)
        self.assertEqual(first, second)
        self.assertEqual(preflight["result"], "PASS")
        self.assertEqual(synchronization["result"], "PASS")
        self.assertEqual(first["execution_eligibility"]["result"], "FAIL")
        self.assertEqual(first["closeout_eligibility"]["result"], "FAIL")
        self.assertIn(
            "MA-ACCEPTANCE-001",
            first["closeout_eligibility"]["unsatisfied_requirements"],
        )

    def test_zero_and_duplicate_contract_discovery_fail_closed(self):
        missing = subprocess.run(
            [str(ZEUS), "mission", "qualify", "NO-SUCH-MISSION"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={"PATH": "/usr/bin:/bin", "ZEUS_NO_INTRO": "1"},
        )
        self.assertEqual(missing.returncode, 78)
        self.assertIn("derived 0 Mission Contracts", missing.stderr)

        interface = ExecutionInterface(ROOT)
        original = ROOT / "engineering/execution/missions/P2-038-CORRECTIVE.yaml"
        with tempfile.TemporaryDirectory(
            dir=ROOT / "engineering/execution/missions"
        ) as directory:
            duplicate = Path(directory) / "duplicate.yaml"
            duplicate.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
            interface._contract_paths = lambda: [original, duplicate]
            with self.assertRaisesRegex(
                ExecutionInterfaceError, "derived 2 from discovery"
            ):
                interface.mission(MISSION)

    def test_controlled_requirement_change_affects_result_without_logic_change(self):
        assurance = MissionAssurance(ROOT)
        declarations = assurance.interface.assurance_requirements()
        revised = copy.deepcopy(declarations)
        contract = next(item for item in revised if item["id"] == "MA-CONTRACT-001")
        contract["assertion"]["value"] = 2
        with mock.patch.object(
            assurance.interface, "assurance_requirements", return_value=revised
        ):
            result = assurance.evaluate(MISSION, "preflight")
        self.assertEqual(result["result"], "FAIL")
        self.assertIn("MA-CONTRACT-001", result["unsatisfied_requirements"])

    def test_conflicting_and_ambiguous_controlled_requirements_fail_closed(self):
        interface = ExecutionInterface(ROOT)
        documents = interface._controlled_documents()
        spec = next(
            item for item in documents["SPEC-0005"]
            if str(item.get("version")) == "1.2"
        )
        duplicate = copy.deepcopy(spec["mission_assurance_requirements"][0])
        procedure = next(
            item for item in documents["PROC-0001"]
            if str(item.get("version")) == "1.16"
        )
        procedure["mission_assurance_requirements"].append(duplicate)
        with mock.patch.object(
            interface, "_controlled_documents", return_value=documents
        ), self.assertRaisesRegex(
            ExecutionInterfaceError, "conflicting assurance requirement"
        ):
            interface.assurance_requirements()

        assurance = MissionAssurance(ROOT)
        declarations = assurance.interface.assurance_requirements()
        declarations[0]["assertion"] = {
            "selector": "state.no_such_fact",
            "operator": "equals",
            "value": True,
        }
        with mock.patch.object(
            assurance.interface, "assurance_requirements", return_value=declarations
        ), self.assertRaisesRegex(
            MissionAssuranceError, "selector unresolved"
        ):
            assurance.requirements(MISSION)

    def test_invalid_operator_selector_and_expression_fail_closed(self):
        definition = ExecutionInterface(ROOT).assurance_language_definition()
        language = AssuranceLanguage(ROOT, definition)
        base = {
            "id": "MA-TEST-001",
            "language_version": "1.0",
            "phase": "preflight",
            "description": "Test declaration.",
            "assertion": {
                "selector": "state.mission.status",
                "operator": "equals",
                "value": "ACTIVE",
            },
        }
        invalid_operator = copy.deepcopy(base)
        invalid_operator["assertion"]["operator"] = "approximately_equals"
        with self.assertRaisesRegex(AssuranceLanguageError, "unsupported assurance operator"):
            language.validate_declaration(invalid_operator)

        invalid_selector = copy.deepcopy(base)
        invalid_selector["assertion"]["selector"] = "environment.secret"
        with self.assertRaisesRegex(AssuranceLanguageError, "unsupported assurance selector"):
            language.validate_declaration(invalid_selector)

        ambiguous = copy.deepcopy(base)
        ambiguous["assertion"] = {
            "all": [base["assertion"]],
            "selector": "state.mission.status",
        }
        with self.assertRaisesRegex(AssuranceLanguageError, "ambiguous compound"):
            language.validate_declaration(ambiguous)

    def test_language_version_incompatibility_fails_closed(self):
        definition = ExecutionInterface(ROOT).assurance_language_definition()
        language = AssuranceLanguage(ROOT, definition)
        declaration = {
            "id": "MA-TEST-001",
            "language_version": "2.0",
            "phase": "preflight",
            "description": "Incompatible declaration.",
            "assertion": {
                "selector": "state.mission.status",
                "operator": "equals",
                "value": "ACTIVE",
            },
        }
        with self.assertRaisesRegex(AssuranceLanguageError, "version incompatible"):
            language.validate_declaration(declaration)

    def test_controlled_language_revision_changes_semantics_without_zeus_change(self):
        definition = ExecutionInterface(ROOT).assurance_language_definition()
        revised = copy.deepcopy(definition)
        revised["language_version"] = "1.1"
        revised["operators"]["equals"]["implementation"] = "strict_not_equals"
        language = AssuranceLanguage(ROOT, revised)
        expression = {
            "selector": "state.value",
            "operator": "equals",
            "value": "expected",
        }
        original = AssuranceLanguage(ROOT, definition)
        context = {"state": {"value": "expected"}}
        self.assertTrue(original.evaluate(expression, context)[0])
        self.assertFalse(language.evaluate(expression, context)[0])

    def test_repository_path_operators_reject_escape(self):
        definition = ExecutionInterface(ROOT).assurance_language_definition()
        language = AssuranceLanguage(ROOT, definition)
        expression = {
            "selector": "state.path",
            "operator": "path_exists",
        }
        with self.assertRaisesRegex(AssuranceLanguageError, "escapes repository"):
            language.evaluate(expression, {"state": {"path": "../outside"}})


if __name__ == "__main__":
    unittest.main()
