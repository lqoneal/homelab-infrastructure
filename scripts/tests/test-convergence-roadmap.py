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

    def test_current_gate_and_completed_dependency_order_are_valid(self):
        value = self.resolver.validate()
        self.assertEqual(value["state"]["current_gate"], "C02")
        self.assertEqual(value["state"]["completed_gates"], ["C00", "C01"])
        self.assertTrue(set(value["gates"]["C02"]["dependencies"]).issubset(value["state"]["completed_gates"]))

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

    def test_unrelated_engctl_version_surface_still_works(self):
        result = subprocess.run(
            [str(ROOT / "scripts/engctl"), "version"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "engctl version 0.9.0")


if __name__ == "__main__":
    unittest.main()
