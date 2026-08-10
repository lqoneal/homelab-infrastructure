#!/usr/bin/env python3
"""Regression coverage for durable convergence roadmap persistence and resume."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.convergence_roadmap import (  # noqa: E402
    ConvergenceRoadmap,
    EXPECTED_GATE_IDS,
    ROADMAP_RELATIVE_ROOT,
    RoadmapError,
)


class ConvergenceRoadmapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ConvergenceRoadmap(ROOT)

    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture_root = Path(temporary.name) / "repository"
        roadmap_source = ROOT / ROADMAP_RELATIVE_ROOT
        roadmap_target = fixture_root / ROADMAP_RELATIVE_ROOT
        roadmap_target.parent.mkdir(parents=True)
        shutil.copytree(roadmap_source, roadmap_target)
        project_target = fixture_root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        project_target.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "docs/project/PROJ-0001-PROJECT_STATE.md", project_target)
        manifest = self.load(roadmap_target / "binding-manifest.yaml")
        for source in manifest["sources"]:
            source_path = ROOT / source["path"]
            target_path = fixture_root / source["path"]
            if target_path.exists():
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        catalog = self.load(roadmap_target / "execution-playbooks.yaml")
        for playbook in catalog["playbooks"].values():
            for surface in playbook["discovery_surfaces"]:
                if surface["existence"] != "REQUIRED" or surface["kind"] != "PATH":
                    continue
                target_path = fixture_root / surface["location"]
                if target_path.exists():
                    continue
                source_path = ROOT / surface["location"]
                if source_path.is_file():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                else:
                    target_path.mkdir(parents=True, exist_ok=True)
        return fixture_root

    @staticmethod
    def load(path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    @staticmethod
    def write(path: Path, value: dict) -> None:
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def rebind(self, fixture_root: Path) -> None:
        manifest_path = fixture_root / ROADMAP_RELATIVE_ROOT / "binding-manifest.yaml"
        manifest = self.load(manifest_path)
        for source in manifest["sources"]:
            path = fixture_root / source["path"]
            source["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write(manifest_path, manifest)

    def test_roadmap_parses_and_schema_validates(self):
        value = self.resolver.validate()
        self.assertEqual(value["result"], "PASS")
        for schema in (ROOT / ROADMAP_RELATIVE_ROOT / "schemas").glob("*.yaml"):
            self.assertIsInstance(self.load(schema), dict)

    def test_gate_ids_are_unique_and_c00_through_c20_are_present(self):
        value = self.resolver.validate()
        self.assertEqual(list(value["gates"]), EXPECTED_GATE_IDS)
        self.assertEqual(len(value["gates"]), len(set(value["gates"])))

    def test_dependency_references_resolve(self):
        value = self.resolver.validate()
        for gate in value["gates"].values():
            self.assertTrue(set(gate["dependencies"]).issubset(value["gates"]))

    def test_unknown_dependency_fails_closed(self):
        fixture_root = self.fixture()
        gate_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C03-eos-and-engineering-state/GATE.yaml"
        gate = self.load(gate_path)
        gate["dependencies"].append("C99")
        self.write(gate_path, gate)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "dependency does not resolve"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_current_gate_and_completed_dependency_order_are_valid(self):
        value = self.resolver.validate()
        self.assertEqual(value["state"]["current_gate"], "C02")
        self.assertEqual(value["state"]["completed_gates"], ["C00", "C01"])
        self.assertTrue(set(value["gates"]["C02"]["dependencies"]).issubset(value["state"]["completed_gates"]))

    def test_mixed_generation_provenance_keeps_frozen_gates_out_of_new_standard(self):
        value = self.resolver.validate()
        references = {item["gate_id"]: item for item in value["roadmap"]["gates"]}
        self.assertEqual(references["C00"]["contract_provenance"]["contract_generation"], "HISTORICAL_FROZEN")
        self.assertEqual(references["C01"]["contract_provenance"]["contract_generation"], "HISTORICAL_FROZEN")
        self.assertEqual(references["C02"]["contract_provenance"]["contract_generation"], "ACTIVATION_FROZEN")
        for gate_id in ("C00", "C01", "C02"):
            self.assertEqual(references[gate_id]["contract_provenance"]["standard_applicability"], "NOT_APPLICABLE")
        self.assertEqual(references["C03"]["contract_provenance"]["standard_applicability"], "STD-0006@1.0")
        result = self.resolver.evaluate(value)
        gate_results = {item["gate_id"]: item for item in result["gate_results"]}
        for gate_id in ("C00", "C01", "C02"):
            self.assertEqual(gate_results[gate_id]["result"], "NOT_APPLICABLE")
        self.assertEqual(gate_results["C03"]["result"], "PASS")

    def test_gate_identity_is_separate_from_roadmap_order(self):
        fixture_root = self.fixture()
        roadmap_path = fixture_root / ROADMAP_RELATIVE_ROOT / "roadmap.yaml"
        roadmap = self.load(roadmap_path)
        c03 = next(item for item in roadmap["gates"] if item["gate_id"] == "C03")
        c03["roadmap_order"] = 25
        self.write(roadmap_path, roadmap)
        self.rebind(fixture_root)
        value = ConvergenceRoadmap(fixture_root).validate()
        self.assertEqual(next(item for item in value["roadmap"]["gates"] if item["gate_id"] == "C03")["gate_identity"], "ESC-GATE-C03")

    def test_historical_gate_without_prospective_fields_remains_valid(self):
        value = self.resolver.validate()
        self.assertNotIn("gate_type", value["gates"]["C00"])
        self.assertNotIn("execution_playbook", value["gates"]["C02"])

    def test_result_paths_are_deterministic(self):
        value = self.resolver.validate()
        for reference in value["roadmap"]["gates"]:
            gate = value["gates"][reference["gate_id"]]
            self.assertEqual(reference["result"], gate["result_location"])
            self.assertTrue(reference["result"].endswith("/RESULT.yaml"))

    def test_missing_gate_definition_fails_closed(self):
        fixture_root = self.fixture()
        (fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C02-controlled-documentation-and-authority/GATE.yaml").unlink()
        with self.assertRaisesRegex(RoadmapError, "definition missing"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_malformed_roadmap_state_fails_closed(self):
        fixture_root = self.fixture()
        (fixture_root / ROADMAP_RELATIVE_ROOT / "STATE.yaml").write_text("- malformed\n", encoding="utf-8")
        with self.assertRaisesRegex(RoadmapError, "root must be a mapping"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_unknown_completed_gate_fails_closed(self):
        fixture_root = self.fixture()
        state_path = fixture_root / ROADMAP_RELATIVE_ROOT / "STATE.yaml"
        state = self.load(state_path)
        state["completed_gates"].append("C99")
        self.write(state_path, state)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "unknown completed gate"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_state_evidence_contradiction_fails_closed(self):
        fixture_root = self.fixture()
        result_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C01-repository-and-infrastructure-baseline/RESULT.yaml"
        result = self.load(result_path)
        result["result"] = "COMPLETE"
        self.write(result_path, result)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "state/evidence contradiction"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_manifested_evidence_drift_fails_closed(self):
        fixture_root = self.fixture()
        evidence = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C01-repository-and-infrastructure-baseline/evidence/discovery/C01-SUMMARY.md"
        evidence.write_text(evidence.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        with self.assertRaisesRegex(RoadmapError, "evidence digest mismatch"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_incomplete_dependency_cannot_be_current(self):
        fixture_root = self.fixture()
        state_path = fixture_root / ROADMAP_RELATIVE_ROOT / "STATE.yaml"
        state = self.load(state_path)
        state["current_gate"] = "C03"
        state["next_authorized_action"] = "BEGIN_C03_EOS_AND_ENGINEERING_STATE_ASSESSMENT"
        self.write(state_path, state)
        c02_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C02-controlled-documentation-and-authority/GATE.yaml"
        c03_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C03-eos-and-engineering-state/GATE.yaml"
        c02, c03 = self.load(c02_path), self.load(c03_path)
        c02["status"], c03["status"] = "PENDING", "CURRENT"
        self.write(c02_path, c02)
        self.write(c03_path, c03)
        roadmap_path = fixture_root / ROADMAP_RELATIVE_ROOT / "roadmap.yaml"
        roadmap = self.load(roadmap_path)
        for reference in roadmap["gates"]:
            if reference["gate_id"] == "C02":
                reference["contract_provenance"]["lifecycle"] = "PENDING"
            elif reference["gate_id"] == "C03":
                reference["contract_provenance"]["lifecycle"] = "CURRENT"
        self.write(roadmap_path, roadmap)
        project_path = fixture_root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        project_text = project_path.read_text(encoding="utf-8")
        project_text = project_text.replace("phase: C02 Controlled Documentation and Authority Assessment", "phase: C03 EOS and Engineering State Assessment")
        project_text = project_text.replace("  current_gate: C02", "  current_gate: C03")
        project_text = project_text.replace("BEGIN_C02_CONTROLLED_DOCUMENTATION_AND_AUTHORITY_ASSESSMENT", "BEGIN_C03_EOS_AND_ENGINEERING_STATE_ASSESSMENT")
        project_path.write_text(project_text, encoding="utf-8")
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "incomplete dependencies"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_resume_projection_exposes_program_gate_and_next_action(self):
        value = self.resolver.projection()
        self.assertEqual(value["program"], "Engineering System Convergence")
        self.assertEqual(value["current_gate"], "C02")
        self.assertEqual(value["next_authorized_action"], "BEGIN_C02_CONTROLLED_DOCUMENTATION_AND_AUTHORITY_ASSESSMENT")
        self.assertTrue(Path(value["gate_definition"]).is_file())
        self.assertTrue(Path(value["last_result"]).is_file())
        self.assertEqual(value["roadmap_version"], "2.0.0")
        self.assertEqual(value["execution_sufficiency"], "PASS")
        self.assertTrue(value["executable"])

    def test_live_evaluator_qualifies_esc_and_all_required_gates(self):
        value = self.resolver.evaluate()
        self.assertEqual(value["structural_result"], "PASS")
        self.assertEqual(value["overall_result"], "PASS")
        self.assertTrue(value["executable"])
        gate_results = {item["gate_id"]: item for item in value["gate_results"]}
        self.assertEqual(gate_results["C02"]["result"], "NOT_APPLICABLE")
        for gate_id in [f"C{number:02d}" for number in range(3, 21)]:
            self.assertEqual(gate_results[gate_id]["result"], "PASS")
        self.assertEqual(gate_results["C20"]["criteria"]["terminal_semantics"], "PASS")

    def test_missing_execution_playbook_fails_executable_qualification(self):
        fixture_root = self.fixture()
        gate_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C03-eos-and-engineering-state/GATE.yaml"
        gate = self.load(gate_path)
        gate["execution_playbook"]["playbook_id"] = "MISSING-PLAYBOOK"
        self.write(gate_path, gate)
        self.rebind(fixture_root)
        result = ConvergenceRoadmap(fixture_root).evaluate(compare_persisted=False)
        self.assertFalse(result["executable"])
        self.assertIn("execution playbook does not resolve", " ".join(result["blockers"]))

    def test_missing_classification_contract_fails_executable_qualification(self):
        fixture_root = self.fixture()
        catalog_path = fixture_root / ROADMAP_RELATIVE_ROOT / "execution-playbooks.yaml"
        catalog = self.load(catalog_path)
        catalog["playbooks"]["ESC-C03"]["classification_vocabulary"]["finding_classes"] = []
        self.write(catalog_path, catalog)
        self.rebind(fixture_root)
        result = ConvergenceRoadmap(fixture_root).evaluate(compare_persisted=False)
        self.assertFalse(result["executable"])
        self.assertIn("classification vocabulary", " ".join(result["blockers"]))

    def test_missing_artifact_schema_fails_closed(self):
        fixture_root = self.fixture()
        catalog_path = fixture_root / ROADMAP_RELATIVE_ROOT / "execution-playbooks.yaml"
        catalog = self.load(catalog_path)
        catalog["playbooks"]["ESC-C03"]["artifact_contracts"][0]["minimum_record_fields"] = []
        self.write(catalog_path, catalog)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "execution playbook catalog invalid"):
            ConvergenceRoadmap(fixture_root).evaluate(compare_persisted=False)

    def test_missing_completeness_test_fails_closed(self):
        fixture_root = self.fixture()
        catalog_path = fixture_root / ROADMAP_RELATIVE_ROOT / "execution-playbooks.yaml"
        catalog = self.load(catalog_path)
        catalog["playbooks"]["ESC-C03"]["completeness_tests"] = []
        self.write(catalog_path, catalog)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "execution playbook catalog invalid"):
            ConvergenceRoadmap(fixture_root).evaluate(compare_persisted=False)

    def test_ambiguous_terminal_continuation_fails_closed(self):
        fixture_root = self.fixture()
        gate_path = fixture_root / ROADMAP_RELATIVE_ROOT / "gates/C20-controlled-convergence-implementation/GATE.yaml"
        gate = self.load(gate_path)
        gate["terminal"]["continuation_authority"] = None
        self.write(gate_path, gate)
        self.rebind(fixture_root)
        with self.assertRaisesRegex(RoadmapError, "terminal continuation is ambiguous"):
            ConvergenceRoadmap(fixture_root).validate()

    def test_planning_only_can_be_structurally_valid_but_not_executable(self):
        fixture_root = self.fixture()
        roadmap_path = fixture_root / ROADMAP_RELATIVE_ROOT / "roadmap.yaml"
        roadmap = self.load(roadmap_path)
        roadmap["classification"] = "AUTHORITATIVE_PLANNING_ROADMAP"
        roadmap["roadmap_class"] = "PLANNING_ONLY"
        self.write(roadmap_path, roadmap)
        self.rebind(fixture_root)
        resolver = ConvergenceRoadmap(fixture_root)
        self.assertEqual(resolver.validate()["result"], "PASS")
        result = resolver.evaluate(compare_persisted=False)
        self.assertFalse(result["executable"])
        self.assertEqual(result["overall_result"], "NOT_EXECUTABLE")
        self.assertIn("PLANNING_ONLY", " ".join(result["warnings"]))

    def test_fresh_shell_cli_needs_no_conversation_or_runtime_identity(self):
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        result = subprocess.run(
            [str(ROOT / "scripts/engctl"), "roadmap", "status"],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Program: Engineering System Convergence", result.stdout)
        self.assertIn("Current Gate: C02", result.stdout)

    def test_preservation_branch_is_reference_only(self):
        value = self.resolver.validate()
        preservation = value["roadmap"]["repository"]["preservation"]
        self.assertEqual(preservation["mode"], "REFERENCE_ONLY")
        self.assertEqual(preservation["commit"], "4f5626d39f0924d3551cdabfcb61788153706774")

    def test_durable_records_do_not_require_provider_or_session_identifiers(self):
        value = self.resolver.validate()
        serialized = yaml.safe_dump({"roadmap": value["roadmap"], "state": value["state"], "gates": value["gates"]})
        for key in ("provider_session_id", "session_id", "thread_id", "transport_id"):
            self.assertNotIn(key, serialized)

    def test_validation_is_read_only(self):
        paths = [path for path in (ROOT / ROADMAP_RELATIVE_ROOT).rglob("*") if path.is_file()]
        before = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}
        result = subprocess.run(
            [str(ROOT / "scripts/engctl"), "roadmap", "validate"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}
        self.assertEqual(before, after)
        self.assertIn("Read-only: YES", result.stdout)

    def test_cli_evaluate_reports_machine_readable_pass(self):
        result = subprocess.run(
            [str(ROOT / "scripts/engctl"), "roadmap", "evaluate"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = yaml.safe_load(result.stdout)
        self.assertEqual(value["overall_result"], "PASS")
        self.assertTrue(value["executable"])

    def test_unrelated_engctl_version_surface_still_works(self):
        result = subprocess.run(
            [str(ROOT / "scripts/engctl"), "version"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "engctl version 0.9.0")


if __name__ == "__main__":
    unittest.main()
