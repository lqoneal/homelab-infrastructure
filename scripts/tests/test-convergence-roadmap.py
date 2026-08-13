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

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.convergence_roadmap import (  # noqa: E402
    ConvergenceRoadmap,
    EXPECTED_GATE_IDS,
    ROADMAP_RELATIVE_ROOT,
    RoadmapError,
)


def _make_test_tree_removable(root: Path) -> None:
    """Restore write/search bits on test-owned immutable-style artifacts."""
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        try:
            path.chmod(path.stat().st_mode | 0o700)
        except FileNotFoundError:
            pass
    try:
        root.chmod(root.stat().st_mode | 0o700)
    except FileNotFoundError:
        pass


_original_copytree = shutil.copytree


def _ignore_repository_evidence(path, names):
    """Keep bound top-level evidence, omit unrelated historical bulk."""
    ignored = {".git", "__pycache__", "runtime", "tmp", "*.pyc"}
    path_text = str(Path(path))
    manifest_bound = set()
    manifest_path = ROOT / "engineering/convergence/engineering-system-convergence/binding-manifest.yaml"
    if manifest_path.is_file():
        manifest = yaml.safe_load(manifest_path.read_text()) or {}
        manifest_bound = {
            str(item["path"])
            for item in manifest.get("sources", [])
            if isinstance(item, dict) and item.get("path")
        }
    if Path(path).name == "evidence":
        if Path(path).parent.name == "engineering-system-convergence":
            return [name for name in names if name.endswith(".pyc")]
        if "/gates/C00-" in path_text or "/gates/C01-" in path_text:
            return [name for name in names if name.endswith(".pyc")]
        ignored_evidence = [
            name for name in names
            if name != "EVIDENCE-MANIFEST.yaml"
            and not name.endswith(".pyc")
        ]
        relative_bound = {
            str((Path(path) / name).resolve().relative_to(ROOT))
            for name in names
            if (Path(path) / name).is_file()
            and str((Path(path) / name).resolve().relative_to(ROOT)) in manifest_bound
        }
        return [name for name in ignored_evidence if str((Path(path) / name).resolve().relative_to(ROOT)) not in relative_bound]
    keep_evidence = (
        Path(path).name == "engineering-system-convergence"
        or "/gates/C00-" in path_text
        or "/gates/C01-" in path_text
    )
    if not keep_evidence and "evidence" not in names:
        ignored.add("evidence")
    return [name for name in names if name in ignored or name.endswith(".pyc")]


def _copytree_for_tests(src, dst, *args, **kwargs):
    if Path(src).resolve() == ROOT:
        kwargs["ignore"] = _ignore_repository_evidence
    return _original_copytree(src, dst, *args, **kwargs)


# The historical CR23 tests intentionally copy the repository. Bound inputs
# remain available, while unrelated evidence is excluded to keep qualification
# within the repository-local temporary-storage budget.
shutil.copytree = _copytree_for_tests


@pytest.fixture(autouse=True)
def _remove_test_tree_immutability(tmp_path):
    yield
    _make_test_tree_removable(tmp_path)


class ConvergenceRoadmapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ConvergenceRoadmap(ROOT)

    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory(
            ignore_cleanup_errors=False,
        )
        self.addCleanup(
            lambda: (
                _make_test_tree_removable(Path(temporary.name)),
                temporary.cleanup(),
            )[-1]
        )
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
        expected_state = __import__("yaml").safe_load(
            (
                ROOT
                / "engineering/convergence/"
                "engineering-system-convergence/STATE.yaml"
            ).read_text()
        )
        self.assertEqual(
            expected_state["next_authorized_action"],
            "OPERATOR_REVIEW_C02_ASSESSMENT",
        )
        self.assertEqual(
            value["next_authorized_action"],
            "OPERATOR_REVIEW_C02_ASSESSMENT",
        )
        state = self.load(ROOT / ROADMAP_RELATIVE_ROOT / "STATE.yaml")
        corrective_state = self.load(
            ROOT
            / "engineering/convergence/engineering-system-convergence/gates/"
            / "C02-controlled-documentation-and-authority/corrective/"
            / "ESC-C02-CORRECTIVE-001/STATE.yaml"
        )
        retirement = self.load(
            ROOT
            / "engineering/convergence/engineering-system-convergence/gates/"
            / "C02-controlled-documentation-and-authority/corrective/"
            / "ESC-C02-CORRECTIVE-001/evidence/"
            / "CR48-CR55-RETIREMENT-SUPERSESSION-ASSESSMENT-001.yaml"
        )
        c03 = self.load(
            ROOT
            / "engineering/convergence/engineering-system-convergence/gates/"
            / "C03-eos-and-engineering-state/GATE.yaml"
        )
        self.assertEqual(state["current_gate"], "C02")
        self.assertEqual(state["next_authorized_action"], "OPERATOR_REVIEW_C02_ASSESSMENT")
        self.assertEqual(corrective_state["state"], "COMPLETE")
        self.assertTrue(retirement["retirement_transition_performed"])
        self.assertFalse(retirement["execution_performed"])
        self.assertTrue(
            all(
                item["determination"] == "RETIRED_SUPERSEDED"
                for item in retirement["independent_retirement_test"].values()
            )
        )
        self.assertEqual(c03["status"], "PENDING")
        self.assertFalse((ROOT / c03["result_location"]).exists())
        self.assertTrue(Path(value["gate_definition"]).is_file())
        self.assertTrue(Path(value["last_result"]).is_file())
        self.assertEqual(value["roadmap_version"], "2.3.0")
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



def test_cr17_status_projection_awaiting_operator_review():
    from pathlib import Path
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    v = ConvergenceRoadmap(Path.cwd()).projection()

    assert v["lifecycle_state"] == "AWAITING_OPERATOR_REVIEW"
    assert v["execution_result_state"] == "VALID_FINAL"
    assert v["review_required"] is True
    assert v["review_state"] == "AWAITING_OPERATOR_REVIEW"
    assert v["operator_decision"] == "NONE"
    assert v["completion_state"] == "INCOMPLETE"
    assert v["read_only"] is True


def test_cr17_status_projection_current_without_result(tmp_path):
    from pathlib import Path
    import yaml
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    repo = _build_test_repository(tmp_path)
    root = repo / "engineering/convergence/engineering-system-convergence"

    state = yaml.safe_load((root / "STATE.yaml").read_text())
    roadmap = yaml.safe_load((root / "roadmap.yaml").read_text())

    current = state["current_gate"]

    definition = next(
        x["definition"]
        for x in roadmap["gates"]
        if x["gate_id"] == current
    )

    gate = yaml.safe_load((repo / definition).read_text())
    result = repo / gate["result_location"]

    if result.exists():
        result.unlink()

    state["next_authorized_action"] = (
        gate["resume_instructions"]["next_authorized_action"]
    )
    (root / "STATE.yaml").write_text(
        yaml.safe_dump(state, sort_keys=False)
    )

    project_state_path = repo / "docs/project/PROJ-0001-PROJECT_STATE.md"
    project_text = project_state_path.read_text()
    parts = project_text.split("---", 2)
    assert len(parts) == 3

    project_front = yaml.safe_load(parts[1])
    project_front["convergence_program"]["next_authorized_action"] = (
        state["next_authorized_action"]
    )

    project_state_path.write_text(
        "---\n"
        + yaml.safe_dump(project_front, sort_keys=False, width=110)
        + "---"
        + parts[2]
    )

    import hashlib

    manifest_path = root / "binding-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())

    rebound = {
        "engineering/convergence/engineering-system-convergence/STATE.yaml",
        "docs/project/PROJ-0001-PROJECT_STATE.md",
    }

    for source in manifest["sources"]:
        if source["path"] in rebound:
            source["sha256"] = hashlib.sha256(
                (repo / source["path"]).read_bytes()
            ).hexdigest()

    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False)
    )

    v = ConvergenceRoadmap(repo).projection()

    assert v["lifecycle_state"] == "CURRENT"
    assert v["execution_result_state"] == "ABSENT"
    assert v["review_required"] is False
    assert v["review_state"] == "NOT_REQUIRED"
    assert v["operator_decision"] == "NONE"
    assert v["completion_state"] == "INCOMPLETE"
    assert v["read_only"] is True


def test_cr18_evaluate_pending_review_is_not_corruption():
    from pathlib import Path
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    value = ConvergenceRoadmap(Path.cwd()).evaluate(
        compare_persisted=False
    )

    assert value["overall_result"] == "PASS"
    assert value["executable"] is True
    assert value["lifecycle_state"] == "AWAITING_OPERATOR_REVIEW"
    assert value["blockers"] == []
    assert value["next_authorized_action"] == (
        "REVIEW_REBASED_C06_WOP_EENS_FOUNDATIONAL_DEVELOPMENT_BOUNDARY"
    )


def test_cr18_historical_c00_c02_provenance_remains_not_applicable():
    from pathlib import Path
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    value = ConvergenceRoadmap(Path.cwd()).evaluate(
        compare_persisted=False
    )

    gates = {
        item["gate_id"]: item
        for item in value["gate_results"]
    }

    for gate_id in ("C00", "C01", "C02"):
        assert gates[gate_id]["result"] == "NOT_APPLICABLE"
        assert gates[gate_id]["standard_applicability"] == "NOT_APPLICABLE"


def test_cr18_prospective_c03_plus_qualification_remains_pass():
    from pathlib import Path
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    value = ConvergenceRoadmap(Path.cwd()).evaluate(
        compare_persisted=False
    )

    gates = {
        item["gate_id"]: item
        for item in value["gate_results"]
    }

    for number in range(3, 21):
        gate_id = f"C{number:02d}"
        assert gates[gate_id]["result"] == "PASS"
        assert gates[gate_id]["standard_applicability"] != "NOT_APPLICABLE"


def test_cr18_evaluation_is_read_only():
    from pathlib import Path
    import hashlib
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    root = Path(
        "engineering/convergence/engineering-system-convergence"
    )

    files = [
        path for path in root.rglob("*")
        if path.is_file()
    ]

    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }

    resolver = ConvergenceRoadmap(Path.cwd())

    first = resolver.evaluate(compare_persisted=False)
    second = resolver.evaluate(compare_persisted=False)

    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }

    assert before == after
    assert first == second


def test_cr19_resume_projection_exposes_pending_review_read_only():
    from pathlib import Path
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    resolver = ConvergenceRoadmap(Path.cwd())
    value = resolver.projection()

    assert value["result"] == "PASS"
    assert value["current_gate"] == "C02"
    assert value["lifecycle_state"] == "AWAITING_OPERATOR_REVIEW"
    assert value["execution_result_state"] == "VALID_FINAL"
    assert value["review_required"] is True
    assert value["review_state"] == "AWAITING_OPERATOR_REVIEW"
    assert value["operator_decision"] == "NONE"
    assert value["completion_state"] == "INCOMPLETE"
    assert value["next_authorized_action"] == (
        "REVIEW_REBASED_C06_WOP_EENS_FOUNDATIONAL_DEVELOPMENT_BOUNDARY"
    )
    assert value["read_only"] is True




def _cr20_fixture_emm_rebind(repo):
    import hashlib
    import yaml

    manifest_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "binding-manifest.yaml"
    )

    source_rel = "scripts/lib/eos/convergence_roadmap.py"
    source_path = repo / source_rel

    manifest = yaml.safe_load(
        manifest_path.read_text()
    )

    matches = [
        item
        for item in manifest.get("sources", [])
        if (
            isinstance(item, dict)
            and item.get("path") == source_rel
        )
    ]

    if len(matches) != 1:
        raise AssertionError(
            "expected exactly one convergence_roadmap.py EMM binding"
        )

    matches[0]["sha256"] = hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest()

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
            width=100,
        )
    )


def _cr20_review_inputs(repo):
    from pathlib import Path
    import hashlib
    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    _cr20_fixture_emm_rebind(repo)

    value = ConvergenceRoadmap(repo).projection()

    gate_path = Path(value["gate_definition"])
    result_path = Path(value["gate_result"])

    return {
        "roadmap_id": value["roadmap_id"],
        "roadmap_version": str(value["roadmap_version"]),
        "gate_id": value["current_gate"],
        "gate_definition_digest": hashlib.sha256(
            gate_path.read_bytes()
        ).hexdigest(),
        "result_digest": hashlib.sha256(
            result_path.read_bytes()
        ).hexdigest(),
        "operator_identity": "test-operator",
    }


def test_cr20_operator_review_accept_reject_replay_and_fail_closed(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_operator_review_transaction,
    )

    source = Path.cwd()
    repo = tmp_path / "repo"

    shutil.copytree(
        source,
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    corr = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "gates/C02-controlled-documentation-and-authority"
        / "corrective/ESC-C02-CORRECTIVE-001"
    )

    cr20_result_path = corr / "gates/CR20/RESULT.yaml"

    assert cr20_result_path.is_file()

    cr20_result_before = cr20_result_path.read_bytes()

    cr21_result_path = corr / "gates/CR21/RESULT.yaml"

    assert cr21_result_path.is_file()

    cr21_result_before = cr21_result_path.read_bytes()

    inputs = _cr20_review_inputs(repo)

    accepted = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-accept",
    )

    assert accepted["result"] == "PASS"
    assert accepted["decision"] == "ACCEPT"
    assert accepted["lifecycle_state"] == "ACCEPTED"
    assert accepted["already_applied"] is False

    replay = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-accept",
    )

    assert replay["result"] == "PASS"
    assert replay["already_applied"] is True
    assert replay["decision_receipt_id"] == \
        accepted["decision_receipt_id"]

    try:
        apply_operator_review_transaction(
            repo,
            **inputs,
            decision="REJECT",
            transaction_id="tx-cr20-accept",
        )
    except RoadmapError as exc:
        assert "conflicting transaction replay" in str(exc)
    else:
        raise AssertionError("conflicting replay did not fail closed")

    try:
        apply_operator_review_transaction(
            repo,
            **inputs,
            decision="REJECT",
            transaction_id="tx-cr20-reject",
        )
    except RoadmapError as exc:
        assert "conflicting prior operator decision" in str(exc)
    else:
        raise AssertionError(
            "cross-transaction ACCEPT/REJECT conflict did not fail closed"
        )

    duplicate_accept = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-duplicate-accept",
    )

    assert duplicate_accept["result"] == "PASS"
    assert duplicate_accept["decision"] == "ACCEPT"
    assert duplicate_accept["already_applied"] is True
    assert duplicate_accept["decision_receipt_id"] ==         accepted["decision_receipt_id"]

    bad_authority = dict(inputs)
    bad_authority["operator_identity"] = ""

    try:
        apply_operator_review_transaction(
            repo,
            **bad_authority,
            decision="ACCEPT",
            transaction_id="tx-cr20-missing-authority",
        )
    except RoadmapError as exc:
        assert "missing operator_identity" in str(exc)
    else:
        raise AssertionError("missing authority did not fail closed")

    bad_result = dict(inputs)
    bad_result["result_digest"] = "0" * 64

    try:
        apply_operator_review_transaction(
            repo,
            **bad_result,
            decision="ACCEPT",
            transaction_id="tx-cr20-bad-result",
        )
    except RoadmapError as exc:
        assert "result digest mismatch" in str(exc)
    else:
        raise AssertionError("bad result digest did not fail closed")

    bad_gate = dict(inputs)
    bad_gate["gate_definition_digest"] = "0" * 64

    try:
        apply_operator_review_transaction(
            repo,
            **bad_gate,
            decision="ACCEPT",
            transaction_id="tx-cr20-bad-gate",
        )
    except RoadmapError as exc:
        assert "gate definition digest mismatch" in str(exc)
    else:
        raise AssertionError("bad gate digest did not fail closed")

    # CR20 is already complete in the current authoritative baseline.
    # Operator-review replay must preserve that historical RESULT exactly;
    # it must neither delete nor rewrite it.
    cr20_result_after = cr20_result_path.read_bytes()

    assert cr20_result_after == cr20_result_before
    # CR21 is also already complete in the current authoritative baseline.
    # CR20 review replay must not mutate its successor's historical result.
    cr21_result_after = cr21_result_path.read_bytes()

    assert cr21_result_after == cr21_result_before


def test_cr20_review_receipt_does_not_advance_live_roadmap(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = repo / "engineering/convergence/engineering-system-convergence"
    before = yaml.safe_load((root / "STATE.yaml").read_text())

    inputs = _cr20_review_inputs(repo)

    value = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-no-advance",
    )

    after = yaml.safe_load((root / "STATE.yaml").read_text())

    assert value["lifecycle_state"] == "ACCEPTED"
    assert before == after
    assert after["current_gate"] == "C02"
    assert "C02" not in after["completed_gates"]





def _cr21_fixture_emm_rebind(repo):
    import hashlib
    import yaml

    manifest_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "binding-manifest.yaml"
    )

    source_rel = "scripts/lib/eos/convergence_roadmap.py"
    source_path = repo / source_rel

    manifest = yaml.safe_load(
        manifest_path.read_text()
    )

    matches = [
        item
        for item in manifest.get("sources", [])
        if item.get("path") == source_rel
    ]

    assert len(matches) == 1

    matches[0]["sha256"] = hashlib.sha256(
        source_path.read_bytes()
    ).hexdigest()

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
            width=100,
        )
    )


def _cr21_fixture(repo):
    from pathlib import Path
    import hashlib

    _cr21_fixture_emm_rebind(repo)

    from scripts.lib.eos.convergence_roadmap import (
        ConvergenceRoadmap,
        apply_operator_review_transaction,
    )

    projection = ConvergenceRoadmap(repo).projection()

    gate_path = Path(projection["gate_definition"])
    result_path = Path(projection["gate_result"])

    review_inputs = {
        "roadmap_id": projection["roadmap_id"],
        "roadmap_version": str(projection["roadmap_version"]),
        "gate_id": projection["current_gate"],
        "gate_definition_digest": hashlib.sha256(
            gate_path.read_bytes()
        ).hexdigest(),
        "result_digest": hashlib.sha256(
            result_path.read_bytes()
        ).hexdigest(),
        "operator_identity": "cr21-test-operator",
    }

    accepted = apply_operator_review_transaction(
        repo,
        **review_inputs,
        decision="ACCEPT",
        transaction_id="tx-cr21-review-accept",
    )

    receipt_dir = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
    )

    receipt_path = next(
        path
        for path in receipt_dir.glob("*.json")
        if accepted["decision_receipt_id"]
        in path.read_text()
    )

    state_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "STATE.yaml"
    )

    advancement_inputs = {
        key: value
        for key, value in review_inputs.items()
        if key != "operator_identity"
    }

    return {
        **advancement_inputs,
        "acceptance_receipt_id":
            accepted["decision_receipt_id"],
        "acceptance_receipt_digest": hashlib.sha256(
            receipt_path.read_bytes()
        ).hexdigest(),
        "pre_state_digest": hashlib.sha256(
            state_path.read_bytes()
        ).hexdigest(),
    }


def test_cr21_advancement_success_and_replay(tmp_path):
    from pathlib import Path
    import json
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    inputs = _cr21_fixture(repo)

    before = yaml.safe_load(
        (root / "STATE.yaml").read_text()
    )

    result = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-advance",
    )

    after = yaml.safe_load(
        (root / "STATE.yaml").read_text()
    )

    assert result["result"] == "PASS"
    assert result["lifecycle_state"] == "COMPLETED"
    assert result["successor_gate"] == "C03"
    assert result["already_applied"] is False

    assert before["current_gate"] == "C02"
    assert after["current_gate"] == "C03"
    assert "C02" in after["completed_gates"]
    assert after["completed_gates"].count("C02") == 1

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr21-advance.json"
    )

    assert tx_path.is_file()

    tx = json.loads(tx_path.read_text())

    assert tx["status"] == "ADVANCEMENT_COMPLETE"
    assert tx["gate_id"] == "C02"
    assert tx["successor_gate"] == "C03"
    assert tx["pre_state_digest"] == inputs["pre_state_digest"]

    replay = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-advance",
    )

    assert replay["result"] == "PASS"
    assert replay["already_applied"] is True

    replay_state = yaml.safe_load(
        (root / "STATE.yaml").read_text()
    )

    assert replay_state["completed_gates"].count("C02") == 1
    assert replay_state["current_gate"] == "C03"


def test_cr21_advancement_rejects_bad_bindings(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    bad = dict(inputs)
    bad["pre_state_digest"] = "0" * 64

    try:
        apply_gate_advancement_transaction(
            repo,
            **bad,
            transaction_id="tx-cr21-bad-prestate",
        )
    except RoadmapError as exc:
        assert "pre-state digest mismatch" in str(exc)
    else:
        raise AssertionError(
            "bad pre-state digest did not fail closed"
        )

    bad = dict(inputs)
    bad["acceptance_receipt_digest"] = "0" * 64

    try:
        apply_gate_advancement_transaction(
            repo,
            **bad,
            transaction_id="tx-cr21-bad-receipt",
        )
    except RoadmapError as exc:
        assert "acceptance receipt digest mismatch" in str(exc)
    else:
        raise AssertionError(
            "bad receipt digest did not fail closed"
        )

    bad = dict(inputs)
    bad["result_digest"] = "0" * 64

    try:
        apply_gate_advancement_transaction(
            repo,
            **bad,
            transaction_id="tx-cr21-bad-result",
        )
    except RoadmapError as exc:
        assert "result digest mismatch" in str(exc)
    else:
        raise AssertionError(
            "bad result digest did not fail closed"
        )

    bad = dict(inputs)
    bad["gate_definition_digest"] = "0" * 64

    try:
        apply_gate_advancement_transaction(
            repo,
            **bad,
            transaction_id="tx-cr21-bad-gate",
        )
    except RoadmapError as exc:
        assert "gate definition digest mismatch" in str(exc)
    else:
        raise AssertionError(
            "bad gate digest did not fail closed"
        )



def test_cr21_conflicting_committed_replay_fails_closed(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-conflict",
    )

    conflicting = dict(inputs)
    conflicting["result_digest"] = "0" * 64

    try:
        apply_gate_advancement_transaction(
            repo,
            **conflicting,
            transaction_id="tx-cr21-conflict",
        )
    except RoadmapError as exc:
        assert (
            "conflicting advancement transaction replay"
            in str(exc)
        )
    else:
        raise AssertionError(
            "conflicting committed replay did not fail closed"
        )


def test_cr21_interrupted_transaction_recovers_exactly(tmp_path):
    from pathlib import Path
    import hashlib
    import json
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    state_path = root / "STATE.yaml"

    inputs = _cr21_fixture(repo)

    pre_state_bytes = state_path.read_bytes()

    first = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-interrupted",
    )

    assert first["result"] == "PASS"

    post_state_bytes = state_path.read_bytes()

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr21-interrupted.json"
    )

    tx = json.loads(tx_path.read_text())

    assert tx["status"] == "ADVANCEMENT_COMPLETE"
    assert tx["post_state_digest"] == hashlib.sha256(
        post_state_bytes
    ).hexdigest()

    # Simulate interruption after transaction provenance was durably
    # written but before authoritative STATE.yaml promotion.
    state_path.write_bytes(pre_state_bytes)

    tx["status"] = "PENDING_RECONCILIATION"

    tx_path.write_text(
        json.dumps(
            tx,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    recovered = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-interrupted",
    )

    assert recovered["result"] == "PASS"
    assert recovered["lifecycle_state"] == "COMPLETED"
    assert recovered["successor_gate"] == "C03"

    final_state = yaml.safe_load(
        state_path.read_text()
    )

    assert final_state["current_gate"] == "C03"
    assert final_state["completed_gates"].count("C02") == 1

    final_tx = json.loads(tx_path.read_text())

    assert final_tx["status"] == "ADVANCEMENT_COMPLETE"



def test_cr21_interrupted_after_state_promotion_finalizes_receipt(tmp_path):
    from pathlib import Path
    import json
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    state_path = root / "STATE.yaml"

    inputs = _cr21_fixture(repo)

    first = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-poststate-interrupted",
    )

    assert first["result"] == "PASS"

    state_before_recovery = state_path.read_bytes()

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr21-poststate-interrupted.json"
    )

    tx = json.loads(tx_path.read_text())

    tx["status"] = "PENDING_RECONCILIATION"

    tx_path.write_text(
        json.dumps(
            tx,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    recovered = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-poststate-interrupted",
    )

    assert recovered["result"] == "PASS"
    assert recovered["already_applied"] is True
    assert recovered["recovered"] is True
    assert recovered["recovery_mode"] == (
        "FINALIZED_POST_STATE_TRANSACTION"
    )

    assert state_path.read_bytes() == state_before_recovery

    state = yaml.safe_load(
        state_path.read_text()
    )

    assert state["current_gate"] == "C03"
    assert state["completed_gates"].count("C02") == 1

    finalized = json.loads(
        tx_path.read_text()
    )

    assert finalized["status"] == "ADVANCEMENT_COMPLETE"



def test_cr21_missing_authoritative_successor_fails_closed(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    roadmap_path = root / "roadmap.yaml"

    roadmap = yaml.safe_load(
        roadmap_path.read_text()
    )

    current = next(
        item
        for item in roadmap["gates"]
        if item["gate_id"] == "C02"
    )

    gate_path = repo / current["definition"]
    gate = yaml.safe_load(gate_path.read_text())

    gate["next_gate"] = None

    gate_path.write_text(
        yaml.safe_dump(
            gate,
            sort_keys=False,
            width=100,
        )
    )

    _cr21_fixture_emm_rebind(repo)

    try:
        apply_gate_advancement_transaction(
            repo,
            **inputs,
            transaction_id="tx-cr21-missing-successor",
        )
    except RoadmapError as exc:
        assert (
            "C02 historical next_gate is not deterministic"
            in str(exc)
        )
    else:
        raise AssertionError(
            "missing authoritative successor did not fail closed"
        )


def test_cr21_conflicting_successor_dependency_fails_closed(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    roadmap = yaml.safe_load(
        (root / "roadmap.yaml").read_text()
    )

    successor_ref = next(
        item
        for item in roadmap["gates"]
        if item["gate_id"] == "C03"
    )

    successor_path = repo / successor_ref["definition"]
    successor = yaml.safe_load(
        successor_path.read_text()
    )

    successor["dependencies"] = [
        "C02",
        "C20",
    ]

    successor_path.write_text(
        yaml.safe_dump(
            successor,
            sort_keys=False,
            width=100,
        )
    )

    _cr21_fixture_emm_rebind(repo)

    try:
        apply_gate_advancement_transaction(
            repo,
            **inputs,
            transaction_id="tx-cr21-unsatisfied-successor",
        )
    except RoadmapError as exc:
        assert (
            "C03 dependency is not a predecessor: C20"
            in str(exc)
        )
    else:
        raise AssertionError(
            "unsatisfied successor dependency did not fail closed"
        )



def test_cr21_advancement_never_mutates_live_repository(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    live = Path.cwd()

    live_state = (
        live
        / "engineering/convergence/engineering-system-convergence"
        / "STATE.yaml"
    )

    before = hashlib.sha256(
        live_state.read_bytes()
    ).hexdigest()

    repo = tmp_path / "repo"

    shutil.copytree(
        live,
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr21-isolated-only",
    )

    after = hashlib.sha256(
        live_state.read_bytes()
    ).hexdigest()

    assert before == after



def test_cr22_machine_classification_contract(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    # CR21 fixture creates an isolated EMM-rebound repository and
    # produces one valid ACCEPT receipt.
    inputs = _cr21_fixture(repo)

    first_advance = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr22-classification-advance",
    )

    assert first_advance["classification"] == "APPLIED"
    assert first_advance["already_applied"] is False

    replay_advance = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr22-classification-advance",
    )

    assert replay_advance["classification"] == "ALREADY_APPLIED"
    assert replay_advance["already_applied"] is True

    # Use a separate isolated copy for operator-review classification.
    review_repo = tmp_path / "review-repo"

    shutil.copytree(
        Path.cwd(),
        review_repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    _cr21_fixture_emm_rebind(review_repo)

    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap
    import hashlib

    projection = ConvergenceRoadmap(review_repo).projection()

    gate_path = Path(projection["gate_definition"])
    result_path = Path(projection["gate_result"])

    review_inputs = {
        "roadmap_id": projection["roadmap_id"],
        "roadmap_version": str(projection["roadmap_version"]),
        "gate_id": projection["current_gate"],
        "gate_definition_digest":
            hashlib.sha256(gate_path.read_bytes()).hexdigest(),
        "result_digest":
            hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "operator_identity": "cr22-classification-test",
        "decision": "ACCEPT",
    }

    first_review = apply_operator_review_transaction(
        review_repo,
        **review_inputs,
        transaction_id="tx-cr22-classification-review",
    )

    assert first_review["classification"] == "APPLIED"
    assert first_review["already_applied"] is False

    replay_review = apply_operator_review_transaction(
        review_repo,
        **review_inputs,
        transaction_id="tx-cr22-classification-review",
    )

    assert replay_review["classification"] == "ALREADY_APPLIED"
    assert replay_review["already_applied"] is True


def test_cr22_unrecoverable_partial_state_fails_closed(tmp_path):
    from pathlib import Path
    import json
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    state_path = root / "STATE.yaml"

    inputs = _cr21_fixture(repo)

    # Produce a legitimate complete transaction first so all provenance
    # fields and post-state digest are canonical.
    first = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr22-unrecoverable",
    )

    assert first["result"] == "PASS"

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr22-unrecoverable.json"
    )

    tx = json.loads(tx_path.read_text())

    # Convert it to the interrupted durable state.
    tx["status"] = "PENDING_RECONCILIATION"

    tx_path.write_text(
        json.dumps(
            tx,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    # Construct state that is intentionally neither the transaction's
    # recorded pre-state nor its recorded post-state.
    state = yaml.safe_load(
        state_path.read_text()
    )

    state["next_authorized_action"] = (
        "CR22_SYNTHETIC_UNRECOVERABLE_STATE"
    )

    state_path.write_text(
        yaml.safe_dump(
            state,
            sort_keys=False,
        )
    )

    before = state_path.read_bytes()

    try:
        apply_gate_advancement_transaction(
            repo,
            **inputs,
            transaction_id="tx-cr22-unrecoverable",
        )
    except RoadmapError as exc:
        assert (
            "pending advancement state matches neither "
            "recorded pre-state nor post-state"
            in str(exc)
        )
    else:
        raise AssertionError(
            "unrecoverable partial state did not fail closed"
        )

    # Fail-closed means no attempted repair/mutation.
    assert state_path.read_bytes() == before


def test_cr22_recovery_classification_contract(tmp_path):
    from pathlib import Path
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    state_path = root / "STATE.yaml"

    inputs = _cr21_fixture(repo)

    pre_state = state_path.read_bytes()

    apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr22-classification-recover",
    )

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr22-classification-recover.json"
    )

    tx = json.loads(tx_path.read_text())

    # Recreate transaction-recorded-before-state-promotion interruption.
    state_path.write_bytes(pre_state)
    tx["status"] = "PENDING_RECONCILIATION"

    tx_path.write_text(
        json.dumps(
            tx,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    recovered = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr22-classification-recover",
    )

    assert recovered["classification"] == "RECOVERED"
    assert recovered["result"] == "PASS"



def test_cr23_advancement_provenance_contract(tmp_path):
    from pathlib import Path
    import hashlib
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    inputs = _cr21_fixture(repo)

    result = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr23-advancement-provenance",
    )

    assert result["result"] == "PASS"

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr23-advancement-provenance.json"
    )

    assert tx_path.is_file()

    tx = json.loads(tx_path.read_text())

    required = {
        "roadmap_id": inputs["roadmap_id"],
        "roadmap_version": str(inputs["roadmap_version"]),
        "gate_id": inputs["gate_id"],
        "gate_definition_digest":
            inputs["gate_definition_digest"],
        "result_digest":
            inputs["result_digest"],
        "acceptance_receipt_id":
            inputs["acceptance_receipt_id"],
        "acceptance_receipt_digest":
            inputs["acceptance_receipt_digest"],
        "pre_state_digest":
            inputs["pre_state_digest"],
        "transaction_id":
            "tx-cr23-advancement-provenance",
    }

    for key, expected in required.items():
        assert key in tx
        assert str(tx[key]) == str(expected)

    # Advancement provenance must include qualified post-state identity.
    assert tx.get("post_state_digest")

    # Lifecycle/disposition must be independently reconstructable
    # from the durable transaction itself, not merely the API return.
    assert tx.get("lifecycle_state") == "COMPLETED"
    assert isinstance(tx.get("terminal_state"), bool)

    if tx["terminal_state"]:
        assert tx.get("successor_gate") is None
        assert tx.get("next_authorized_action") == "NONE"
    else:
        assert tx.get("successor_gate") is not None
        assert tx.get("next_authorized_action")

    # Persisted state must match the transaction's post-state identity.
    state_path = root / "STATE.yaml"

    actual_post = hashlib.sha256(
        state_path.read_bytes()
    ).hexdigest()

    assert tx["post_state_digest"] == actual_post


def test_cr23_operator_review_provenance_contract(tmp_path):
    from pathlib import Path
    import hashlib
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr20_review_inputs(repo)

    result = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr23-review-provenance",
    )

    assert result["result"] == "PASS"

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    tx_path = (
        root
        / "receipts/operator-review"
        / "tx-cr23-review-provenance.json"
    )

    assert tx_path.is_file()

    tx = json.loads(tx_path.read_text())

    required = {
        "roadmap_id": inputs["roadmap_id"],
        "roadmap_version": str(inputs["roadmap_version"]),
        "gate_id": inputs["gate_id"],
        "gate_definition_digest":
            inputs["gate_definition_digest"],
        "result_digest":
            inputs["result_digest"],
        "operator_identity":
            inputs["operator_identity"],
        "transaction_id":
            "tx-cr23-review-provenance",
        "decision": "ACCEPT",
    }

    for key, expected in required.items():
        assert key in tx
        assert str(tx[key]) == str(expected)

    assert tx.get("receipt_type") == "OPERATOR_REVIEW_DECISION"
    assert tx.get("receipt_id")
    assert (
        result["decision_receipt_id"]
        == tx["receipt_id"]
    )

    receipt_digest = hashlib.sha256(
        tx_path.read_bytes()
    ).hexdigest()

    assert len(receipt_digest) == 64
    assert tx.get("lifecycle_state") == "ACCEPTED"
    assert tx.get("next_authorized_action")


def test_cr23_provenance_replay_is_identity_stable(tmp_path):
    from pathlib import Path
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    inputs = _cr21_fixture(repo)

    first = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr23-provenance-replay",
    )

    tx_path = (
        root
        / "runtime/advancement-transactions"
        / "tx-cr23-provenance-replay.json"
    )

    before = tx_path.read_bytes()

    replay = apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr23-provenance-replay",
    )

    after = tx_path.read_bytes()

    assert first["classification"] == "APPLIED"
    assert replay["classification"] == "ALREADY_APPLIED"

    # Exact replay may not rewrite provenance.
    assert after == before


def test_cr23_review_replay_is_identity_stable(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    inputs = _cr20_review_inputs(repo)

    first = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr23-review-replay",
    )

    tx_path = (
        root
        / "receipts/operator-review"
        / "tx-cr23-review-replay.json"
    )

    before = tx_path.read_bytes()

    replay = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr23-review-replay",
    )

    after = tx_path.read_bytes()

    assert first["classification"] == "APPLIED"
    assert replay["classification"] == "ALREADY_APPLIED"

    assert after == before


def test_cr23_real_parent_state_never_mutated_by_isolated_provenance(
    tmp_path,
):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        apply_gate_advancement_transaction,
    )

    live = Path.cwd()

    live_parent = (
        live
        / "engineering/convergence/engineering-system-convergence"
        / "STATE.yaml"
    )

    before = hashlib.sha256(
        live_parent.read_bytes()
    ).hexdigest()

    repo = tmp_path / "repo"

    shutil.copytree(
        live,
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr21_fixture(repo)

    apply_gate_advancement_transaction(
        repo,
        **inputs,
        transaction_id="tx-cr23-isolation-proof",
    )

    after = hashlib.sha256(
        live_parent.read_bytes()
    ).hexdigest()

    assert after == before



def test_cr23_zo005_emm_awareness_bound_clean(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_emm_reconciliation_awareness,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    _cr21_fixture_emm_rebind(repo)

    result = project_emm_reconciliation_awareness(
        repo,
        source_path=(
            "engineering/convergence/"
            "engineering-system-convergence/STATE.yaml"
        ),
    )

    assert result["classification"] == "BOUND_CLEAN"
    assert result["reconciliation_required"] is False
    assert result["recommended_action"] == "NONE_REQUIRED"
    assert result["automatic_reconciliation"] is False
    assert result["read_only"] is True


def test_cr23_zo005_emm_awareness_bound_drifted(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_emm_reconciliation_awareness,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    _cr21_fixture_emm_rebind(repo)

    target = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence/STATE.yaml"
    )

    target.write_text(
        target.read_text()
        + "\n# ZO005 isolated drift\n"
    )

    result = project_emm_reconciliation_awareness(
        repo,
        source_path=(
            "engineering/convergence/"
            "engineering-system-convergence/STATE.yaml"
        ),
    )

    assert result["classification"] == "BOUND_DRIFTED"
    assert result["reconciliation_required"] is True
    assert result["rebind_eligible"] is True
    assert (
        result["recommended_action"]
        == "EMM_RECONCILIATION_REQUIRED"
    )
    assert result["automatic_reconciliation"] is False


def test_cr23_zo005_emm_awareness_unbound(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_emm_reconciliation_awareness,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    result = project_emm_reconciliation_awareness(
        repo,
        source_path="scripts/tests/test-convergence-roadmap.py",
    )

    assert result["classification"] == "UNBOUND_BY_POLICY"
    assert result["reconciliation_required"] is False
    assert result["rebind_eligible"] is False
    assert (
        result["recommended_action"]
        == "NONE_UNBOUND_BY_POLICY"
    )
    assert result["automatic_reconciliation"] is False


def test_cr23_zo005_emm_awareness_missing_bound_source(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        project_emm_reconciliation_awareness,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    _cr21_fixture_emm_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    manifest = yaml.safe_load(
        (root / "binding-manifest.yaml").read_text()
    )

    target_rel = None

    for item in manifest.get("sources", []):
        if not isinstance(item, dict):
            continue

        rel = item.get("path")

        if rel and (repo / rel).is_file():
            target_rel = rel
            break

    assert target_rel is not None

    (repo / target_rel).unlink()

    result = project_emm_reconciliation_awareness(
        repo,
        source_path=target_rel,
    )

    assert result["classification"] == "MISSING_SOURCE"
    assert result["reconciliation_required"] is False
    assert result["rebind_eligible"] is False
    assert (
        result["recommended_action"]
        == "FAIL_CLOSED_MISSING_SOURCE"
    )
    assert result["automatic_reconciliation"] is False


def test_cr23_zo005_emm_awareness_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_emm_reconciliation_awareness,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    _cr21_fixture_emm_rebind(repo)

    manifest = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence/"
          "binding-manifest.yaml"
    )

    before = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()

    project_emm_reconciliation_awareness(
        repo,
        source_path=(
            "engineering/convergence/"
            "engineering-system-convergence/STATE.yaml"
        ),
    )

    after = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()

    assert before == after


def test_cr23_zo005_does_not_call_rebind(tmp_path, monkeypatch):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    called = {"value": False}

    def forbidden(*args, **kwargs):
        called["value"] = True
        raise AssertionError(
            "read-only awareness invoked EMM rebind"
        )

    monkeypatch.setattr(
        roadmap,
        "apply_emm_rebind_transaction",
        forbidden,
    )

    roadmap.project_emm_reconciliation_awareness(
        repo,
        source_path="scripts/tests/test-convergence-roadmap.py",
    )

    assert called["value"] is False


def test_cr20_operator_review_cli_accept_replay_and_conflict(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil
    import subprocess
    import yaml

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    _cr20_fixture_emm_rebind(repo)

    value = ConvergenceRoadmap(repo).projection()

    gate_path = Path(value["gate_definition"])
    result_path = Path(value["gate_result"])

    common = [
        "python3",
        str(repo / "scripts/lib/eos/convergence_roadmap.py"),
        "--repository-root",
        str(repo),
        "operator-review",
        "--roadmap-id",
        value["roadmap_id"],
        "--roadmap-version",
        str(value["roadmap_version"]),
        "--gate-id",
        value["current_gate"],
        "--gate-definition-digest",
        hashlib.sha256(gate_path.read_bytes()).hexdigest(),
        "--result-digest",
        hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "--operator-identity",
        "test-operator",
    ]

    accepted = subprocess.run(
        common + [
            "--decision",
            "ACCEPT",
            "--transaction-id",
            "tx-cli-accept",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert accepted.returncode == 0, accepted.stderr

    accepted_value = yaml.safe_load(accepted.stdout)

    assert accepted_value["result"] == "PASS"
    assert accepted_value["decision"] == "ACCEPT"
    assert accepted_value["lifecycle_state"] == "ACCEPTED"
    assert accepted_value["read_only"] is False

    replay = subprocess.run(
        common + [
            "--decision",
            "ACCEPT",
            "--transaction-id",
            "tx-cli-accept",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert replay.returncode == 0, replay.stderr

    replay_value = yaml.safe_load(replay.stdout)

    assert replay_value["already_applied"] is True
    assert replay_value["decision_receipt_id"] == \
        accepted_value["decision_receipt_id"]

    conflict = subprocess.run(
        common + [
            "--decision",
            "REJECT",
            "--transaction-id",
            "tx-cli-reject",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert conflict.returncode != 0
    assert "conflicting prior operator decision" in conflict.stderr

    state = yaml.safe_load(
        (
            repo
            / "engineering/convergence/engineering-system-convergence/STATE.yaml"
        ).read_text()
    )

    assert state["current_gate"] == "C02"
    assert "C02" not in state["completed_gates"]



def test_cr20_fresh_projection_recovers_persisted_operator_decision(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        ConvergenceRoadmap,
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr20_review_inputs(repo)

    accepted = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-persisted-accept",
    )

    assert accepted["lifecycle_state"] == "ACCEPTED"

    fresh = ConvergenceRoadmap(repo).projection()

    assert fresh["current_gate"] == "C02"
    assert fresh["lifecycle_state"] == "ACCEPTED"
    assert fresh["execution_result_state"] == "VALID_FINAL"
    assert fresh["review_required"] is False
    assert fresh["review_state"] == "ACCEPTED"
    assert fresh["operator_decision"] == "ACCEPT"
    assert fresh["completion_state"] == "INCOMPLETE"
    assert fresh["read_only"] is True



def test_cr20_fresh_projection_recovers_rejected_decision(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        ConvergenceRoadmap,
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr20_review_inputs(repo)

    rejected = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="REJECT",
        transaction_id="tx-cr20-persisted-reject",
    )

    assert rejected["lifecycle_state"] == "REJECTED"

    fresh = ConvergenceRoadmap(repo).projection()

    assert fresh["current_gate"] == "C02"
    assert fresh["lifecycle_state"] == "REJECTED"
    assert fresh["execution_result_state"] == "VALID_FINAL"
    assert fresh["review_required"] is False
    assert fresh["review_state"] == "REJECTED"
    assert fresh["operator_decision"] == "REJECT"
    assert fresh["completion_state"] == "INCOMPLETE"
    assert fresh["read_only"] is True


def test_cr20_tampered_persisted_receipt_fails_closed(tmp_path):
    from pathlib import Path
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        ConvergenceRoadmap,
        RoadmapError,
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr20_review_inputs(repo)

    result = apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-tamper",
    )

    receipt = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
        / "tx-cr20-tamper.json"
    )

    value = json.loads(receipt.read_text())
    value["result_digest"] = "0" * 64
    receipt.write_text(json.dumps(value, indent=2) + "\n")

    try:
        ConvergenceRoadmap(repo).projection()
    except RoadmapError as exc:
        assert "persisted operator review result digest mismatch" in str(exc)
    else:
        raise AssertionError("tampered persisted receipt did not fail closed")


def test_cr20_conflicting_persisted_receipts_fail_closed(tmp_path):
    from pathlib import Path
    import json
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        ConvergenceRoadmap,
        RoadmapError,
        apply_operator_review_transaction,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
        ),
    )

    inputs = _cr20_review_inputs(repo)

    apply_operator_review_transaction(
        repo,
        **inputs,
        decision="ACCEPT",
        transaction_id="tx-cr20-conflict-a",
    )

    receipt_dir = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
    )

    source = receipt_dir / "tx-cr20-conflict-a.json"
    conflicting = receipt_dir / "tx-cr20-conflict-b.json"

    value = json.loads(source.read_text())
    value["transaction_id"] = "tx-cr20-conflict-b"
    value["receipt_id"] = "ORR-CONFLICT"
    value["decision"] = "REJECT"
    value["lifecycle_state"] = "REJECTED"

    conflicting.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    )

    try:
        ConvergenceRoadmap(repo).projection()
    except RoadmapError as exc:
        assert "conflicting persisted operator review decisions" in str(exc)
    else:
        raise AssertionError(
            "conflicting persisted receipts did not fail closed"
        )


if __name__ == "__main__":
    unittest.main()




def _build_test_repository(tmp_path):
    """Create an isolated repository copy for mutation-oriented tests."""
    source = ROOT
    destination = tmp_path / "repository"

    def ignore(directory, names):
        ignored = set()

        for name in (".git", "__pycache__", ".pytest_cache"):
            if name in names:
                ignored.add(name)

        return ignored

    shutil.copytree(
        source,
        destination,
        ignore=ignore,
        symlinks=True,
    )

    return destination

def test_current_gate_valid_result_derives_pending_review(tmp_path):
    """A valid current-gate result is reviewable, not completed."""

    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    repo = _build_test_repository(tmp_path)

    state_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "STATE.yaml"
    )

    result_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "gates/C02-test/RESULT.yaml"
    )

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_path.write_text(
        """
schema_version: 1
gate_id: C02
result: PASS
evidence:
  - path: engineering/convergence/engineering-system-convergence/gates/C02-test/evidence/EVIDENCE-MANIFEST.yaml
""".lstrip()
    )

    evidence = result_path.parent / "evidence/EVIDENCE-MANIFEST.yaml"
    evidence.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    evidence.write_text(
        """
schema_version: 1
gate_id: C02
evidence: []
""".lstrip()
    )

    controller = ConvergenceRoadmap(repo)

    # Validation must accept the current+valid-result state.
    controller.validate()

    state = __import__("yaml").safe_load(
        state_path.read_text()
    )

    assert state["current_gate"] == "C02"
    assert "C02" not in state["completed_gates"]


def test_current_gate_result_does_not_imply_acceptance_or_completion(tmp_path):
    """Result existence alone never supplies operator authority."""

    from scripts.lib.eos.convergence_roadmap import ConvergenceRoadmap

    repo = _build_test_repository(tmp_path)

    result_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "gates/C02-test/RESULT.yaml"
    )

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_path.write_text(
        """
schema_version: 1
gate_id: C02
result: PASS
evidence:
  - path: engineering/convergence/engineering-system-convergence/gates/C02-test/evidence/EVIDENCE-MANIFEST.yaml
""".lstrip()
    )

    evidence = result_path.parent / "evidence/EVIDENCE-MANIFEST.yaml"
    evidence.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    evidence.write_text(
        """
schema_version: 1
gate_id: C02
evidence: []
""".lstrip()
    )

    controller = ConvergenceRoadmap(repo)
    controller.validate()

    state_path = (
        repo
        / "engineering/convergence/engineering-system-convergence"
        / "STATE.yaml"
    )

    state = __import__("yaml").safe_load(
        state_path.read_text()
    )

    assert "C02" not in state["completed_gates"]
    assert state["current_gate"] == "C02"


def _cr23_emm_fixture(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil
    import yaml

    source = Path.cwd()
    repo = tmp_path / "repo"

    shutil.copytree(
        source,
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    manifest_path = root / "binding-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())

    target = "scripts/lib/eos/convergence_roadmap.py"
    target_path = repo / target

    old_digest = hashlib.sha256(
        target_path.read_bytes()
    ).hexdigest()

    found = [
        item
        for item in manifest["sources"]
        if item["path"] == target
    ]

    assert len(found) == 1

    # Fixture must begin clean.
    found[0]["sha256"] = old_digest

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
        )
    )

    target_path.write_bytes(
        target_path.read_bytes()
        + b"\n# CR23 EMM fixture mutation\n"
    )

    new_digest = hashlib.sha256(
        target_path.read_bytes()
    ).hexdigest()

    return (
        repo,
        manifest_path,
        target,
        old_digest,
        new_digest,
    )


def test_cr23_emm_rebind_exact_authorized_mutation(tmp_path):
    import hashlib
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        apply_emm_rebind_transaction,
    )

    (
        repo,
        manifest_path,
        target,
        old_digest,
        new_digest,
    ) = _cr23_emm_fixture(tmp_path)

    before = yaml.safe_load(manifest_path.read_text())
    before_map = {
        item["path"]: item["sha256"]
        for item in before["sources"]
    }

    result = apply_emm_rebind_transaction(
        repo,
        authorized_mutations={
            target: old_digest,
        },
        transaction_id="tx-cr23-emm-exact",
    )

    assert result["result"] == "PASS"

    after = yaml.safe_load(manifest_path.read_text())
    after_map = {
        item["path"]: item["sha256"]
        for item in after["sources"]
    }

    assert after_map[target] == new_digest

    for path, digest in before_map.items():
        if path != target:
            assert after_map[path] == digest

    assert result["sources"] == [
        {
            "path": target,
            "old_sha256": old_digest,
            "new_sha256": new_digest,
        }
    ]

    assert (
        hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        == result["post_manifest_sha256"]
    )


def test_cr23_emm_rebind_exact_replay(tmp_path):
    from scripts.lib.eos.convergence_roadmap import (
        apply_emm_rebind_transaction,
    )

    (
        repo,
        manifest_path,
        target,
        old_digest,
        _,
    ) = _cr23_emm_fixture(tmp_path)

    first = apply_emm_rebind_transaction(
        repo,
        authorized_mutations={
            target: old_digest,
        },
        transaction_id="tx-cr23-emm-replay",
    )

    manifest_after_first = manifest_path.read_bytes()

    replay = apply_emm_rebind_transaction(
        repo,
        authorized_mutations={
            target: old_digest,
        },
        transaction_id="tx-cr23-emm-replay",
    )

    assert first["result"] == "PASS"
    assert replay["result"] == "ALREADY_RECONCILED"
    assert manifest_path.read_bytes() == manifest_after_first
    assert (
        replay["post_manifest_sha256"]
        == first["post_manifest_sha256"]
    )


def test_cr23_emm_rebind_conflicting_replay_fails_closed(tmp_path):
    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_emm_rebind_transaction,
    )

    (
        repo,
        _,
        target,
        old_digest,
        _,
    ) = _cr23_emm_fixture(tmp_path)

    apply_emm_rebind_transaction(
        repo,
        authorized_mutations={
            target: old_digest,
        },
        transaction_id="tx-cr23-emm-conflict",
    )

    try:
        apply_emm_rebind_transaction(
            repo,
            authorized_mutations={
                target: "0" * 64,
            },
            transaction_id="tx-cr23-emm-conflict",
        )
    except RoadmapError as exc:
        assert (
            "conflicting EMM transaction replay" in str(exc)
            or "authorized prior digest mismatch" in str(exc)
        )
    else:
        raise AssertionError(
            "conflicting EMM replay did not fail closed"
        )


def test_cr23_emm_rebind_unauthorized_drift_fails_closed(tmp_path):
    import hashlib
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_emm_rebind_transaction,
    )

    (
        repo,
        manifest_path,
        target,
        old_digest,
        _,
    ) = _cr23_emm_fixture(tmp_path)

    manifest = yaml.safe_load(manifest_path.read_text())

    other = next(
        item["path"]
        for item in manifest["sources"]
        if item["path"] != target
        and (repo / item["path"]).is_file()
    )

    other_path = repo / other

    other_path.write_bytes(
        other_path.read_bytes()
        + b"\n# unauthorized fixture drift\n"
    )

    before = manifest_path.read_bytes()

    try:
        apply_emm_rebind_transaction(
            repo,
            authorized_mutations={
                target: old_digest,
            },
            transaction_id="tx-cr23-emm-unauthorized",
        )
    except RoadmapError as exc:
        assert (
            "unauthorized or unexplained EMM source drift"
            in str(exc)
        )
    else:
        raise AssertionError(
            "unauthorized EMM drift did not fail closed"
        )

    assert manifest_path.read_bytes() == before


def test_cr23_emm_rebind_unbound_source_fails_closed(tmp_path):
    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_emm_rebind_transaction,
    )

    (
        repo,
        manifest_path,
        _,
        _,
        _,
    ) = _cr23_emm_fixture(tmp_path)

    unbound = "CR23-UNBOUND-FIXTURE.txt"
    unbound_path = repo / unbound
    unbound_path.write_text("fixture\n")

    import hashlib

    digest = hashlib.sha256(
        unbound_path.read_bytes()
    ).hexdigest()

    before = manifest_path.read_bytes()

    try:
        apply_emm_rebind_transaction(
            repo,
            authorized_mutations={
                unbound: digest,
            },
            transaction_id="tx-cr23-emm-unbound",
        )
    except RoadmapError as exc:
        assert "not EMM-bound" in str(exc)
    else:
        raise AssertionError(
            "unbound EMM mutation did not fail closed"
        )

    assert manifest_path.read_bytes() == before


def test_cr23_emm_rebind_requires_exact_drift_set(tmp_path):
    import hashlib
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        apply_emm_rebind_transaction,
    )

    (
        repo,
        manifest_path,
        target,
        old_digest,
        _,
    ) = _cr23_emm_fixture(tmp_path)

    manifest = yaml.safe_load(manifest_path.read_text())

    clean = next(
        item
        for item in manifest["sources"]
        if item["path"] != target
        and (repo / item["path"]).is_file()
    )

    clean_path = repo / clean["path"]
    clean_digest = hashlib.sha256(
        clean_path.read_bytes()
    ).hexdigest()

    before = manifest_path.read_bytes()

    try:
        apply_emm_rebind_transaction(
            repo,
            authorized_mutations={
                target: old_digest,
                clean["path"]: clean_digest,
            },
            transaction_id="tx-cr23-emm-overbroad",
        )
    except RoadmapError as exc:
        assert (
            "does not exactly match drift"
            in str(exc)
        )
    else:
        raise AssertionError(
            "overbroad authorized mutation set did not fail closed"
        )

    assert manifest_path.read_bytes() == before




def test_cr23_zo010_bound_clean(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    manifest_path = root / "binding-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())

    target = "scripts/lib/eos/convergence_roadmap.py"

    import hashlib

    actual = hashlib.sha256(
        (repo / target).read_bytes()
    ).hexdigest()

    entry = next(
        item
        for item in manifest["sources"]
        if item["path"] == target
    )

    entry["sha256"] = actual

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
        )
    )

    result = inspect_emm_binding_scope(
        repo,
        source_path=target,
    )

    assert result["result"] == "PASS"
    assert result["classification"] == "BOUND_CLEAN"
    assert result["bound"] is True
    assert result["source_exists"] is True
    assert result["expected_sha256"] == actual
    assert result["actual_sha256"] == actual
    assert result["drifted"] is False
    assert result["rebind_eligible"] is False
    assert result["read_only"] is True


def test_cr23_zo010_bound_drifted(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    manifest_path = root / "binding-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())

    target = "scripts/lib/eos/convergence_roadmap.py"
    target_path = repo / target

    actual_before = hashlib.sha256(
        target_path.read_bytes()
    ).hexdigest()

    entry = next(
        item
        for item in manifest["sources"]
        if item["path"] == target
    )

    entry["sha256"] = actual_before

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
        )
    )

    target_path.write_bytes(
        target_path.read_bytes()
        + b"\n# ZO-010 drift fixture\n"
    )

    actual_after = hashlib.sha256(
        target_path.read_bytes()
    ).hexdigest()

    result = inspect_emm_binding_scope(
        repo,
        source_path=target,
    )

    assert result["classification"] == "BOUND_DRIFTED"
    assert result["bound"] is True
    assert result["source_exists"] is True
    assert result["expected_sha256"] == actual_before
    assert result["actual_sha256"] == actual_after
    assert result["drifted"] is True
    assert result["rebind_eligible"] is True
    assert result["read_only"] is True


def test_cr23_zo010_unbound_existing_source(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    target = "ZO010-UNBOUND.txt"

    (repo / target).write_text("fixture\n")

    result = inspect_emm_binding_scope(
        repo,
        source_path=target,
    )

    assert result["classification"] == "UNBOUND_BY_POLICY"
    assert result["bound"] is False
    assert result["source_exists"] is True
    assert result["actual_sha256"]
    assert result["expected_sha256"] is None
    assert result["drifted"] is False
    assert result["rebind_eligible"] is False
    assert result["read_only"] is True


def test_cr23_zo010_unbound_missing_source(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    result = inspect_emm_binding_scope(
        repo,
        source_path="ZO010-NOT-PRESENT.txt",
    )

    assert result["classification"] == "UNBOUND_BY_POLICY"
    assert result["bound"] is False
    assert result["source_exists"] is False
    assert result["expected_sha256"] is None
    assert result["actual_sha256"] is None
    assert result["drifted"] is False
    assert result["rebind_eligible"] is False
    assert result["read_only"] is True


def test_cr23_zo010_bound_missing_source(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    manifest_path = root / "binding-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())

    target = "scripts/lib/eos/convergence_roadmap.py"

    assert (repo / target).is_file()

    (repo / target).unlink()

    result = inspect_emm_binding_scope(
        repo,
        source_path=target,
    )

    assert result["classification"] == "MISSING_SOURCE"
    assert result["bound"] is True
    assert result["source_exists"] is False
    assert result["expected_sha256"]
    assert result["actual_sha256"] is None
    assert result["drifted"] is False
    assert result["rebind_eligible"] is False
    assert result["read_only"] is True


def test_cr23_zo010_introspection_is_byte_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        inspect_emm_binding_scope,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    root = (
        repo
        / "engineering/convergence/engineering-system-convergence"
    )

    manifest = root / "binding-manifest.yaml"

    target = "scripts/lib/eos/convergence_roadmap.py"

    before_manifest = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()

    before_source = hashlib.sha256(
        (repo / target).read_bytes()
    ).hexdigest()

    inspect_emm_binding_scope(
        repo,
        source_path=target,
    )

    after_manifest = hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()

    after_source = hashlib.sha256(
        (repo / target).read_bytes()
    ).hexdigest()

    assert after_manifest == before_manifest
    assert after_source == before_source



def test_cr23_zo011_resource_preflight_ready(tmp_path, monkeypatch):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap

    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "file.txt").write_text("fixture\n")

    class Usage:
        total = 10_000_000_000
        used = 1_000_000_000
        free = 9_000_000_000

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda path: Usage(),
    )

    class Process:
        returncode = 0
        stdout = "1000000\tfixture\n"

    monkeypatch.setattr(
        roadmap.subprocess if hasattr(roadmap, "subprocess") else __import__("subprocess"),
        "run",
        lambda *args, **kwargs: Process(),
        raising=False,
    )

    result = roadmap.project_qualification_resource_preflight(
        repo,
        temporary_workspace=tmp_path / "workspace",
        fixture_copy_multiplier=8,
        minimum_extra_bytes=2_000_000_000,
    )

    assert result["classification"] == "READY"
    assert result["ready"] is True
    assert result["resource"] is None
    assert result["semantic_test_failure"] is False
    assert result["qualification_executed"] is False
    assert (
        result["recommended_action"]
        == "USE_SELECTED_WORKSPACE"
    )
    assert result["read_only"] is True


def test_cr23_zo011_resource_preflight_blocked(tmp_path, monkeypatch):
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap

    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "file.txt").write_text("fixture\n")

    class Usage:
        total = 2_000_000_000
        used = 1_900_000_000
        free = 100_000_000

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda path: Usage(),
    )

    import subprocess

    class Process:
        returncode = 0
        stdout = "100000000\tfixture\n"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Process(),
    )

    result = roadmap.project_qualification_resource_preflight(
        repo,
        temporary_workspace=tmp_path / "workspace",
        fixture_copy_multiplier=8,
        minimum_extra_bytes=2_000_000_000,
    )

    assert result["classification"] == "RESOURCE_BLOCKED"
    assert result["resource"] == "TEMPORARY_STORAGE"
    assert result["ready"] is False
    assert result["semantic_test_failure"] is False
    assert result["qualification_executed"] is False
    assert (
        result["recommended_action"]
        == "SELECT_ALTERNATE_AUTHORIZED_WORKSPACE"
    )


def test_cr23_zo011_missing_workspace_parent_resolves_existing_ancestor(
    tmp_path,
):
    from scripts.lib.eos.convergence_roadmap import (
        project_qualification_resource_preflight,
    )

    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "file.txt").write_text("fixture\n")

    requested = (
        tmp_path
        / "not-yet-created"
        / "nested"
        / "pytest"
    )

    result = project_qualification_resource_preflight(
        repo,
        temporary_workspace=requested,
        fixture_copy_multiplier=1,
        minimum_extra_bytes=0,
    )

    assert result["temporary_workspace"] == str(
        requested.resolve()
    )
    assert result["filesystem_probe"] == str(
        tmp_path.resolve()
    )
    assert result["qualification_executed"] is False
    assert result["read_only"] is True


def test_cr23_zo011_required_reserve_is_conservative(tmp_path, monkeypatch):
    import shutil
    import subprocess

    from scripts.lib.eos.convergence_roadmap import (
        project_qualification_resource_preflight,
    )

    repo = tmp_path / "repo"
    repo.mkdir()

    class Usage:
        total = 100_000_000_000
        used = 1
        free = 99_999_999_999

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda path: Usage(),
    )

    class Process:
        returncode = 0
        stdout = "100000000\tfixture\n"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Process(),
    )

    result = project_qualification_resource_preflight(
        repo,
        temporary_workspace=tmp_path,
        fixture_copy_multiplier=8,
        minimum_extra_bytes=2_000_000_000,
    )

    assert (
        result["required_reserve_bytes"]
        == 2_100_000_000
    )


def test_cr23_zo011_resource_preflight_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib

    from scripts.lib.eos.convergence_roadmap import (
        project_qualification_resource_preflight,
    )

    repo = tmp_path / "repo"
    repo.mkdir()

    target = repo / "file.txt"
    target.write_text("fixture\n")

    requested = (
        tmp_path
        / "does-not-exist"
        / "qualification"
    )

    before = hashlib.sha256(
        target.read_bytes()
    ).hexdigest()

    assert not requested.exists()

    project_qualification_resource_preflight(
        repo,
        temporary_workspace=requested,
        fixture_copy_multiplier=1,
        minimum_extra_bytes=0,
    )

    after = hashlib.sha256(
        target.read_bytes()
    ).hexdigest()

    assert before == after
    assert not requested.exists()


def test_cr23_zo011_never_classifies_resource_block_as_semantic_failure(
    tmp_path,
    monkeypatch,
):
    import shutil
    import subprocess

    from scripts.lib.eos.convergence_roadmap import (
        project_qualification_resource_preflight,
    )

    repo = tmp_path / "repo"
    repo.mkdir()

    class Usage:
        total = 1000
        used = 999
        free = 1

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda path: Usage(),
    )

    class Process:
        returncode = 0
        stdout = "1000\tfixture\n"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Process(),
    )

    result = project_qualification_resource_preflight(
        repo,
        temporary_workspace=tmp_path,
        fixture_copy_multiplier=8,
        minimum_extra_bytes=1000,
    )

    assert result["classification"] == "RESOURCE_BLOCKED"
    assert result["semantic_test_failure"] is False
    assert result["qualification_executed"] is False





def _zo009_fixture_rebind(repo):
    from pathlib import Path
    import hashlib
    import yaml

    root = (
        Path(repo)
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    manifest_path = root / "binding-manifest.yaml"

    manifest = yaml.safe_load(
        manifest_path.read_text()
    )

    for item in manifest.get("sources", []):
        if not isinstance(item, dict):
            continue

        rel = item.get("path")

        if not rel:
            continue

        path = Path(repo) / rel

        if path.is_file():
            item["sha256"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            sort_keys=False,
        )
    )

    # ZO-007/008/013 are historical CR23 contracts.  A copy of the current
    # repository is not that historical state: the corrective has since
    # progressed to CR48.  Project only the historical facts these read-only
    # qualifications require, leaving the live repository and production
    # semantics untouched.
    corrective_root = (
        Path(repo)
        / "engineering/convergence/engineering-system-convergence/"
          "gates/C02-controlled-documentation-and-authority/"
          "corrective/ESC-C02-CORRECTIVE-001"
    )
    state_path = corrective_root / "STATE.yaml"
    state = yaml.safe_load(state_path.read_text())
    completed_items = state.get("completed_items", [])
    if state.get("current_item") == "CR48":
        state["completed_items"] = completed_items[:completed_items.index("CR23")]
        state["current_item"] = "CR23"
        state["blockers"] = []
        state["last_completed_item"] = "CR22"
        state["next_authorized_action"] = (
            "EXECUTE_CR23_IMPLEMENT_LIFECYCLE_PROVENANCE"
        )
    state_path.write_text(yaml.safe_dump(state, sort_keys=False))

    historical_result = corrective_root / "gates/CR23/RESULT.yaml"
    if historical_result.exists():
        historical_result.unlink()

    # Rebind after the explicit projection so the copied fixture remains a
    # coherent repository for the resolver's digest checks.
    manifest = yaml.safe_load(manifest_path.read_text())
    for item in manifest.get("sources", []):
        if not isinstance(item, dict) or not item.get("path"):
            continue
        path = Path(repo) / item["path"]
        if path.is_file():
            item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))


def _zo009_gate_path(repo, gate_id):
    from pathlib import Path
    import yaml

    root = (
        Path(repo)
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    roadmap = yaml.safe_load(
        (root / "roadmap.yaml").read_text()
    )

    entry = next(
        item
        for item in roadmap["gates"]
        if item["gate_id"] == gate_id
    )

    return Path(repo) / entry["definition"]


def _zo009_gate(repo, gate_id):
    import yaml

    path = _zo009_gate_path(
        repo,
        gate_id,
    )

    return path, yaml.safe_load(
        path.read_text()
    )


def _zo009_find_nonterminal(repo):
    import yaml

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    roadmap = yaml.safe_load(
        (root / "roadmap.yaml").read_text()
    )

    for entry in roadmap["gates"]:
        path, gate = _zo009_gate(
            repo,
            entry["gate_id"],
        )

        terminal = gate.get("terminal") or {}

        if (
            not bool(terminal.get("is_terminal"))
            and isinstance(
                gate.get("next_gate"),
                str,
            )
            and gate.get("next_gate")
        ):
            return entry["gate_id"], path, gate

    raise AssertionError(
        "no authoritative nonterminal gate found"
    )


def _zo009_find_terminal(repo):
    import yaml

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    roadmap = yaml.safe_load(
        (root / "roadmap.yaml").read_text()
    )

    for entry in roadmap["gates"]:
        path, gate = _zo009_gate(
            repo,
            entry["gate_id"],
        )

        terminal = gate.get("terminal") or {}

        if bool(terminal.get("is_terminal")):
            return entry["gate_id"], path, gate

    raise AssertionError(
        "no authoritative terminal gate found"
    )


def test_cr23_zo009_successor_action_resolves_exactly_one(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, _, gate = _zo009_find_nonterminal(repo)

    successor = gate["next_gate"]

    successor_path, successor_gate = _zo009_gate(
        repo,
        successor,
    )

    action = successor_gate.get(
        "next_authorized_action"
    )

    resume = successor_gate.get(
        "resume_instructions"
    )

    if not action and isinstance(resume, dict):
        action = resume.get(
            "next_authorized_action"
        )

    assert action

    _zo009_fixture_rebind(repo)

    result = project_successor_action_contract(
        repo,
        gate_id=gate_id,
    )

    assert result["result"] == "PASS"
    assert result["successor_gate"] == successor
    assert result["next_authorized_action"] == action
    assert result["action_count"] == 1
    assert result["authority_kind"] == "GATE_DEFINITION"
    assert result["successor_executed"] is False
    assert result["read_only"] is True


def test_cr23_zo009_missing_successor_action_fails_closed(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, _, gate = _zo009_find_nonterminal(repo)

    successor = gate["next_gate"]

    path, value = _zo009_gate(
        repo,
        successor,
    )

    value.pop(
        "next_authorized_action",
        None,
    )

    resume = value.get(
        "resume_instructions"
    )

    if isinstance(resume, dict):
        resume.pop(
            "next_authorized_action",
            None,
        )

    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    try:
        project_successor_action_contract(
            repo,
            gate_id=gate_id,
        )
    except RoadmapError as exc:
        assert "next_authorized_action" in str(exc)
    else:
        raise AssertionError(
            "missing successor action did not fail closed"
        )


def test_cr23_zo009_action_surface_is_structured_resume_only(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, _, gate = _zo009_find_nonterminal(repo)

    successor = gate["next_gate"]

    _, successor_gate = _zo009_gate(
        repo,
        successor,
    )

    expected = successor_gate[
        "resume_instructions"
    ]["next_authorized_action"]

    _zo009_fixture_rebind(repo)

    result = project_successor_action_contract(
        repo,
        gate_id=gate_id,
    )

    assert result["next_authorized_action"] == expected
    assert (
        result["action_surface"]
        == "resume_instructions.next_authorized_action"
    )
    assert result["action_count"] == 1
    assert result["successor_executed"] is False

def test_cr23_zo009_missing_successor_is_canonically_rejected(
    tmp_path,
):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, path, value = _zo009_find_nonterminal(repo)

    value["next_gate"] = None

    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    try:
        project_successor_action_contract(
            repo,
            gate_id=gate_id,
        )
    except RoadmapError as exc:
        message = str(exc)

        assert (
            "next_gate"
            in message
            or "successor"
            in message
        )
    else:
        raise AssertionError(
            "canonical missing successor did not fail closed"
        )

def test_cr23_zo009_terminal_gate_exposes_no_successor_action(
    tmp_path,
):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, _, gate = _zo009_find_terminal(repo)

    assert gate["next_gate"] is None

    resume_action = (
        gate.get("resume_instructions") or {}
    ).get("next_authorized_action")

    # Terminal gates may retain a resume/authority action.
    # It must not be projected as a roadmap successor action.
    assert resume_action

    _zo009_fixture_rebind(repo)

    result = project_successor_action_contract(
        repo,
        gate_id=gate_id,
    )

    assert result["terminal"] is True
    assert result["successor_gate"] is None
    assert result["next_authorized_action"] is None
    assert result["terminal_resume_action"] == (
        gate["resume_instructions"]["next_authorized_action"]
    )
    assert result["action_count"] == 0
    assert result["executable_successor"] is False
    assert result["successor_executed"] is False
    assert result["classification"] == "TERMINAL_NO_ROADMAP_SUCCESSOR"

def test_cr23_zo009_terminal_successor_is_canonically_rejected(
    tmp_path,
):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, path, value = _zo009_find_terminal(repo)

    assert value["next_gate"] is None

    value["next_gate"] = "C19"

    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    try:
        project_successor_action_contract(
            repo,
            gate_id=gate_id,
        )
    except RoadmapError as exc:
        message = str(exc)

        assert (
            "terminal"
            in message
            and "next_gate"
            in message
        )
    else:
        raise AssertionError(
            "canonical terminal successor did not fail closed"
        )

def test_cr23_zo009_projection_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    gate_id, _, _ = _zo009_find_nonterminal(repo)

    _zo009_fixture_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    roadmap_path = root / "roadmap.yaml"
    state_path = root / "STATE.yaml"
    manifest_path = root / "binding-manifest.yaml"

    before = {
        "roadmap": hashlib.sha256(
            roadmap_path.read_bytes()
        ).hexdigest(),
        "state": hashlib.sha256(
            state_path.read_bytes()
        ).hexdigest(),
        "manifest": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
    }

    project_successor_action_contract(
        repo,
        gate_id=gate_id,
    )

    after = {
        "roadmap": hashlib.sha256(
            roadmap_path.read_bytes()
        ).hexdigest(),
        "state": hashlib.sha256(
            state_path.read_bytes()
        ).hexdigest(),
        "manifest": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
    }

    assert before == after




def test_cr23_zo006_current_gate_projects_executable(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_executable_roadmap_maturity(
        repo,
        gate_id="C02",
    )

    assert result["classification"] == "CURRENT_EXECUTABLE"
    assert result["executable"] is True
    assert result["is_current"] is True
    assert result["successor_gate"] == "C03"
    assert result["next_authorized_action"]
    assert result["recommended_action"] == \
        result["next_authorized_action"]
    assert result["successor_executed"] is False
    assert result["read_only"] is True


def test_cr23_zo006_completed_gate_is_not_executable(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_executable_roadmap_maturity(
        repo,
        gate_id="C01",
    )

    assert result["classification"] == "COMPLETE"
    assert result["executable"] is False
    assert result["is_completed"] is True
    assert result["recommended_action"] == "NONE_GATE_COMPLETE"


def test_cr23_zo006_future_gate_is_not_current(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_executable_roadmap_maturity(
        repo,
        gate_id="C03",
    )

    assert result["classification"] == "NOT_CURRENT"
    assert result["executable"] is False
    assert result["is_current"] is False
    assert (
        result["recommended_action"]
        == "WAIT_FOR_GATE_ACTIVATION"
    )


def test_cr23_zo006_blocked_gate_projects_blocked(tmp_path, monkeypatch):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module
    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original_validate = roadmap_module.ConvergenceRoadmap.validate

    def validated_with_block(self):
        value = original_validate(self)

        value = dict(value)
        state = dict(value["state"])
        state["blocked_gates"] = ["C02"]
        value["state"] = state

        return value

    monkeypatch.setattr(
        roadmap_module.ConvergenceRoadmap,
        "validate",
        validated_with_block,
    )

    result = project_executable_roadmap_maturity(
        repo,
        gate_id="C02",
    )

    assert result["classification"] == "BLOCKED"
    assert result["executable"] is False
    assert result["is_blocked"] is True
    assert result["recommended_action"] == "RESOLVE_BLOCKERS"


def test_cr23_zo006_consumes_zo009_successor_authority(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
        project_successor_action_contract,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    successor = project_successor_action_contract(
        repo,
        gate_id="C02",
    )

    maturity = project_executable_roadmap_maturity(
        repo,
        gate_id="C02",
    )

    assert (
        maturity["authority_surface"]
        == successor["authority_surface"]
    )

    assert (
        maturity["next_authorized_action"]
        == successor["next_authorized_action"]
    )

    assert (
        maturity["action_surface"]
        == "resume_instructions.next_authorized_action"
    )


def test_cr23_zo006_projection_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_executable_roadmap_maturity,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    paths = [
        root / "roadmap.yaml",
        root / "STATE.yaml",
        root / "binding-manifest.yaml",
    ]

    before = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    project_executable_roadmap_maturity(
        repo,
        gate_id="C02",
    )

    after = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    assert before == after


def test_cr23_zo006_never_executes_successor(tmp_path, monkeypatch):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    called = {"value": False}

    original = getattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
    )

    def forbidden(*args, **kwargs):
        called["value"] = True
        raise AssertionError(
            "maturity projection executed advancement"
        )

    monkeypatch.setattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
        forbidden,
    )

    result = roadmap_module.project_executable_roadmap_maturity(
        repo,
        gate_id="C02",
    )

    assert result["result"] == "PASS"
    assert result["successor_executed"] is False
    assert called["value"] is False

    monkeypatch.setattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
        original,
    )




def _zo007_contract_path():
    return (
        "engineering/convergence/engineering-system-convergence/"
        "gates/C02-controlled-documentation-and-authority/"
        "corrective/ESC-C02-CORRECTIVE-001/"
        "gates/CR23/MANUAL-EXECUTION.yaml"
    )


def test_cr23_zo007_ready_for_manual_execution(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_manual_gate_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_manual_gate_execution_preflight(
        repo,
        parent_gate_id="C02",
        manual_gate_id="CR23",
        manual_contract_path=_zo007_contract_path(),
        temporary_workspace=str(
            tmp_path / "qualification"
        ),
    )

    assert result["result"] == "PASS"
    assert (
        result["classification"]
        == "READY_FOR_MANUAL_EXECUTION"
    )
    assert result["ready"] is True
    assert result["current_item"] == "CR23"
    assert result["dependency_gate"] == "CR22"
    assert result["dependency_result"] == "COMPLETE_PASS"
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["successor_executed"] is False
    assert result["read_only"] is True


def test_cr23_zo007_wrong_current_item_blocks(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        project_manual_gate_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    corr = (
        repo
        / "engineering/convergence/engineering-system-convergence/"
          "gates/C02-controlled-documentation-and-authority/"
          "corrective/ESC-C02-CORRECTIVE-001"
    )

    state_path = corr / "STATE.yaml"

    state = yaml.safe_load(
        state_path.read_text()
    )

    state["current_item"] = "CR22"

    state_path.write_text(
        yaml.safe_dump(
            state,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    result = project_manual_gate_execution_preflight(
        repo,
        parent_gate_id="C02",
        manual_gate_id="CR23",
        manual_contract_path=_zo007_contract_path(),
        temporary_workspace=str(
            tmp_path / "qualification"
        ),
    )

    assert result["classification"] == "WRONG_CURRENT_ITEM"
    assert result["ready"] is False
    assert (
        result["blocking_dependency"]
        == "MANUAL_CONTRACT_STATE"
    )


def test_cr23_zo007_missing_dependency_blocks(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_manual_gate_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    corr = (
        repo
        / "engineering/convergence/engineering-system-convergence/"
          "gates/C02-controlled-documentation-and-authority/"
          "corrective/ESC-C02-CORRECTIVE-001"
    )

    (corr / "gates/CR22/RESULT.yaml").unlink()

    _zo009_fixture_rebind(repo)

    result = project_manual_gate_execution_preflight(
        repo,
        parent_gate_id="C02",
        manual_gate_id="CR23",
        manual_contract_path=_zo007_contract_path(),
        temporary_workspace=str(
            tmp_path / "qualification"
        ),
    )

    assert (
        result["classification"]
        == "DEPENDENCY_NOT_COMPLETE"
    )
    assert result["ready"] is False
    assert result["dependency_gate"] == "CR22"


def test_cr23_zo007_parent_not_executable_blocks(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original = (
        roadmap_module.project_executable_roadmap_maturity
    )

    def blocked(*args, **kwargs):
        value = original(*args, **kwargs)
        value = dict(value)
        value["classification"] = "BLOCKED"
        value["executable"] = False
        return value

    monkeypatch.setattr(
        roadmap_module,
        "project_executable_roadmap_maturity",
        blocked,
    )

    result = (
        roadmap_module.project_manual_gate_execution_preflight(
            repo,
            parent_gate_id="C02",
            manual_gate_id="CR23",
            manual_contract_path=_zo007_contract_path(),
            temporary_workspace=str(
                tmp_path / "qualification"
            ),
        )
    )

    assert (
        result["classification"]
        == "PARENT_NOT_EXECUTABLE"
    )
    assert result["blocking_dependency"] == "ZO-006"
    assert result["ready"] is False


def test_cr23_zo007_resource_blocked_is_distinct(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    def resource_blocked(*args, **kwargs):
        return {
            "result": "PASS",
            "projection":
                "ZEUS_QUALIFICATION_RESOURCE_PREFLIGHT",
            "classification":
                "RESOURCE_BLOCKED",
            "ready": False,
            "qualification_executed": False,
            "semantic_test_failure": False,
            "read_only": True,
        }

    monkeypatch.setattr(
        roadmap_module,
        "project_qualification_resource_preflight",
        resource_blocked,
    )

    result = (
        roadmap_module.project_manual_gate_execution_preflight(
            repo,
            parent_gate_id="C02",
            manual_gate_id="CR23",
            manual_contract_path=_zo007_contract_path(),
            temporary_workspace=str(
                tmp_path / "qualification"
            ),
        )
    )

    assert result["classification"] == "RESOURCE_BLOCKED"
    assert result["blocking_dependency"] == "ZO-011"
    assert result["ready"] is False


def test_cr23_zo007_contract_identity_mismatch_fails_closed(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        project_manual_gate_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    contract_path = repo / _zo007_contract_path()

    contract = yaml.safe_load(
        contract_path.read_text()
    )

    contract["gate_id"] = "CR22"

    contract_path.write_text(
        yaml.safe_dump(
            contract,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    try:
        project_manual_gate_execution_preflight(
            repo,
            parent_gate_id="C02",
            manual_gate_id="CR23",
            manual_contract_path=_zo007_contract_path(),
            temporary_workspace=str(
                tmp_path / "qualification"
            ),
        )
    except RoadmapError as exc:
        assert "identity mismatch" in str(exc)
    else:
        raise AssertionError(
            "manual contract identity mismatch did not fail closed"
        )


def test_cr23_zo007_projection_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_manual_gate_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    corr = (
        root
        / "gates/C02-controlled-documentation-and-authority/"
          "corrective/ESC-C02-CORRECTIVE-001"
    )

    paths = [
        root / "STATE.yaml",
        root / "binding-manifest.yaml",
        corr / "STATE.yaml",
        corr / "gates/CR22/RESULT.yaml",
        corr / "gates/CR23/MANUAL-EXECUTION.yaml",
    ]

    before = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    result = project_manual_gate_execution_preflight(
        repo,
        parent_gate_id="C02",
        manual_gate_id="CR23",
        manual_contract_path=_zo007_contract_path(),
        temporary_workspace=str(
            tmp_path / "qualification"
        ),
    )

    after = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    assert before == after
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["successor_executed"] is False


def test_cr23_zo007_never_executes_or_advances(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    called = {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }

    def forbidden_advance(*args, **kwargs):
        called["advance"] = True
        raise AssertionError("advancement executed")

    def forbidden_review(*args, **kwargs):
        called["review"] = True
        raise AssertionError("review transaction executed")

    def forbidden_rebind(*args, **kwargs):
        called["emm_rebind"] = True
        raise AssertionError("EMM rebind executed")

    monkeypatch.setattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
        forbidden_advance,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_operator_review_transaction",
        forbidden_review,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_emm_rebind_transaction",
        forbidden_rebind,
    )

    result = (
        roadmap_module.project_manual_gate_execution_preflight(
            repo,
            parent_gate_id="C02",
            manual_gate_id="CR23",
            manual_contract_path=_zo007_contract_path(),
            temporary_workspace=str(
                tmp_path / "qualification"
            ),
        )
    )

    assert result["ready"] is True
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["successor_executed"] is False
    assert called == {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }




def _zo008_corrective_root():
    return (
        "engineering/convergence/engineering-system-convergence/"
        "gates/C02-controlled-documentation-and-authority/"
        "corrective/ESC-C02-CORRECTIVE-001"
    )


def _zo008_manual_contract():
    return (
        _zo008_corrective_root()
        + "/gates/CR23/MANUAL-EXECUTION.yaml"
    )


def test_cr23_zo008_live_shape_is_consistent(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C02",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    assert result["result"] == "PASS"
    assert (
        result["classification"]
        == "NESTED_CORRECTIVE_CONSISTENT"
    )
    assert result["consistent"] is True
    assert result["parent_current_gate"] == "C02"
    assert result["nested_current_item"] == "CR23"
    assert result["dependency_gate"] == "CR22"
    assert result["dependency_result"] == "COMPLETE_PASS"
    assert result["next_item"] == "CR24"
    assert (
        result["nested_ready_implies_parent_advance"]
        is False
    )
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False
    assert result["read_only"] is True


def test_cr23_zo008_parent_gate_mismatch_is_distinct(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C03",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    assert result["classification"] == "PARENT_GATE_MISMATCH"
    assert result["consistent"] is False
    assert (
        result["blocking_dependency"]
        == "PARENT_ROADMAP_STATE"
    )


def test_cr23_zo008_nested_current_item_mismatch_blocks(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    corr = repo / _zo008_corrective_root()

    state_path = corr / "STATE.yaml"

    state = yaml.safe_load(
        state_path.read_text()
    )

    state["current_item"] = "CR22"

    state_path.write_text(
        yaml.safe_dump(
            state,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C02",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    assert (
        result["classification"]
        == "NESTED_CURRENT_ITEM_MISMATCH"
    )
    assert result["consistent"] is False
    assert (
        result["blocking_dependency"]
        == "NESTED_CORRECTIVE_STATE"
    )


def test_cr23_zo008_missing_dependency_is_distinct(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    corr = repo / _zo008_corrective_root()

    (corr / "gates/CR22/RESULT.yaml").unlink()

    _zo009_fixture_rebind(repo)

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C02",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    assert (
        result["classification"]
        == "NESTED_DEPENDENCY_NOT_COMPLETE"
    )
    assert result["consistent"] is False
    assert result["dependency_gate"] == "CR22"
    assert result["dependency_result"] == "MISSING"


def test_cr23_zo008_parent_authority_mismatch_is_distinct(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    path = repo / _zo008_manual_contract()

    value = yaml.safe_load(
        path.read_text()
    )

    value["authority"]["parent_gate"] = "C03"

    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C02",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    assert (
        result["classification"]
        == "NESTED_PARENT_AUTHORITY_MISMATCH"
    )
    assert result["consistent"] is False
    assert (
        result["blocking_dependency"]
        == "MANUAL_CONTRACT_AUTHORITY"
    )


def test_cr23_zo008_successor_execution_must_be_prohibited(tmp_path):
    from pathlib import Path
    import shutil
    import yaml

    from scripts.lib.eos.convergence_roadmap import (
        RoadmapError,
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    path = repo / _zo008_manual_contract()

    value = yaml.safe_load(
        path.read_text()
    )

    value["state_transition"]["execute_successor"] = True

    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
        )
    )

    _zo009_fixture_rebind(repo)

    try:
        project_nested_corrective_reconciliation(
            repo,
            parent_gate_id="C02",
            corrective_root_path=_zo008_corrective_root(),
            manual_gate_id="CR23",
            manual_contract_path=_zo008_manual_contract(),
        )
    except RoadmapError as exc:
        assert "successor execution" in str(exc)
    else:
        raise AssertionError(
            "successor-executing nested contract did not fail closed"
        )


def test_cr23_zo008_projection_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_nested_corrective_reconciliation,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    corr = repo / _zo008_corrective_root()

    paths = [
        root / "STATE.yaml",
        root / "binding-manifest.yaml",
        corr / "STATE.yaml",
        corr / "ROADMAP.yaml",
        corr / "gates/CR22/RESULT.yaml",
        corr / "gates/CR23/MANUAL-EXECUTION.yaml",
    ]

    before = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    result = project_nested_corrective_reconciliation(
        repo,
        parent_gate_id="C02",
        corrective_root_path=_zo008_corrective_root(),
        manual_gate_id="CR23",
        manual_contract_path=_zo008_manual_contract(),
    )

    after = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    assert before == after
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False


def test_cr23_zo008_never_executes_or_advances(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    called = {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }

    def forbidden_advance(*args, **kwargs):
        called["advance"] = True
        raise AssertionError("advancement executed")

    def forbidden_review(*args, **kwargs):
        called["review"] = True
        raise AssertionError("review transaction executed")

    def forbidden_rebind(*args, **kwargs):
        called["emm_rebind"] = True
        raise AssertionError("EMM rebind executed")

    monkeypatch.setattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
        forbidden_advance,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_operator_review_transaction",
        forbidden_review,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_emm_rebind_transaction",
        forbidden_rebind,
    )

    result = (
        roadmap_module.project_nested_corrective_reconciliation(
            repo,
            parent_gate_id="C02",
            corrective_root_path=_zo008_corrective_root(),
            manual_gate_id="CR23",
            manual_contract_path=_zo008_manual_contract(),
        )
    )

    assert result["consistent"] is True
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False

    assert called == {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }




def _zo013_corrective_root():
    return (
        "engineering/convergence/engineering-system-convergence/"
        "gates/C02-controlled-documentation-and-authority/"
        "corrective/ESC-C02-CORRECTIVE-001"
    )


def _zo013_manual_contract():
    return (
        _zo013_corrective_root()
        + "/gates/CR23/MANUAL-EXECUTION.yaml"
    )


def _zo013_kwargs(tmp_path):
    return {
        "parent_gate_id": "C02",
        "corrective_root_path":
            _zo013_corrective_root(),
        "manual_gate_id": "CR23",
        "manual_contract_path":
            _zo013_manual_contract(),
        "source_path":
            "scripts/lib/eos/convergence_roadmap.py",
        "temporary_workspace":
            str(tmp_path / "qualification"),
    }


def test_cr23_zo013_live_composite_is_ready(tmp_path):
    from pathlib import Path
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_composite_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    result = project_composite_execution_preflight(
        repo,
        **_zo013_kwargs(tmp_path),
    )

    assert result["result"] == "PASS"
    assert result["classification"] == "READY"
    assert result["ready"] is True
    assert result["blocking_dependency"] is None
    assert result["blocking_dependencies"] == []
    assert result["nested_current_item"] == "CR23"
    assert result["next_nested_item"] == "CR24"
    assert result["successor_gate"] == "C03"
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False
    assert result["automatic_reconciliation"] is False
    assert result["read_only"] is True


def test_cr23_zo013_reports_exact_emm_blocker(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original = (
        roadmap_module.project_emm_reconciliation_awareness
    )

    def blocked(*args, **kwargs):
        value = original(*args, **kwargs)
        value = dict(value)
        value["classification"] = "BOUND_DRIFTED"
        value["reconciliation_required"] = True
        return value

    monkeypatch.setattr(
        roadmap_module,
        "project_emm_reconciliation_awareness",
        blocked,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    assert result["classification"] == "BLOCKED"
    assert result["ready"] is False
    assert result["blocking_dependency"] == "ZO-005"
    assert (
        result["blocking_classification"]
        == "BOUND_DRIFTED"
    )


def test_cr23_zo013_reports_exact_resource_blocker(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    def blocked(*args, **kwargs):
        return {
            "result": "PASS",
            "projection":
                "ZEUS_QUALIFICATION_RESOURCE_PREFLIGHT",
            "classification":
                "RESOURCE_BLOCKED",
            "ready": False,
            "qualification_executed": False,
            "semantic_test_failure": False,
            "read_only": True,
        }

    monkeypatch.setattr(
        roadmap_module,
        "project_qualification_resource_preflight",
        blocked,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    assert result["classification"] == "BLOCKED"
    assert result["blocking_dependency"] == "ZO-011"
    assert (
        result["blocking_classification"]
        == "RESOURCE_BLOCKED"
    )


def test_cr23_zo013_reports_nested_blocker(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original = (
        roadmap_module.project_nested_corrective_reconciliation
    )

    def blocked(*args, **kwargs):
        value = original(*args, **kwargs)
        value = dict(value)
        value["classification"] = (
            "NESTED_CURRENT_ITEM_MISMATCH"
        )
        value["consistent"] = False
        return value

    monkeypatch.setattr(
        roadmap_module,
        "project_nested_corrective_reconciliation",
        blocked,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    assert result["classification"] == "BLOCKED"
    assert result["blocking_dependency"] == "ZO-008"
    assert (
        result["blocking_classification"]
        == "NESTED_CURRENT_ITEM_MISMATCH"
    )


def test_cr23_zo013_reports_manual_blocker(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original = (
        roadmap_module.project_manual_gate_execution_preflight
    )

    def blocked(*args, **kwargs):
        value = original(*args, **kwargs)
        value = dict(value)
        value["classification"] = (
            "DEPENDENCY_NOT_COMPLETE"
        )
        value["ready"] = False
        return value

    monkeypatch.setattr(
        roadmap_module,
        "project_manual_gate_execution_preflight",
        blocked,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    assert result["classification"] == "BLOCKED"
    assert result["blocking_dependency"] == "ZO-007"
    assert (
        result["blocking_classification"]
        == "DEPENDENCY_NOT_COMPLETE"
    )


def test_cr23_zo013_preserves_multiple_distinct_blockers(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    original_emm = (
        roadmap_module.project_emm_reconciliation_awareness
    )

    def emm_blocked(*args, **kwargs):
        value = original_emm(*args, **kwargs)
        value = dict(value)
        value["classification"] = "BOUND_DRIFTED"
        value["reconciliation_required"] = True
        return value

    def resource_blocked(*args, **kwargs):
        return {
            "result": "PASS",
            "projection":
                "ZEUS_QUALIFICATION_RESOURCE_PREFLIGHT",
            "classification":
                "RESOURCE_BLOCKED",
            "ready": False,
            "qualification_executed": False,
            "semantic_test_failure": False,
            "read_only": True,
        }

    monkeypatch.setattr(
        roadmap_module,
        "project_emm_reconciliation_awareness",
        emm_blocked,
    )

    monkeypatch.setattr(
        roadmap_module,
        "project_qualification_resource_preflight",
        resource_blocked,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    dependencies = [
        item["dependency"]
        for item in result["blocking_dependencies"]
    ]

    assert dependencies[:2] == [
        "ZO-005",
        "ZO-011",
    ]


def test_cr23_zo013_projection_is_read_only(tmp_path):
    from pathlib import Path
    import hashlib
    import shutil

    from scripts.lib.eos.convergence_roadmap import (
        project_composite_execution_preflight,
    )

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    root = (
        repo
        / "engineering/convergence/"
          "engineering-system-convergence"
    )

    corr = repo / _zo013_corrective_root()

    paths = [
        root / "STATE.yaml",
        root / "binding-manifest.yaml",
        corr / "STATE.yaml",
        corr / "ROADMAP.yaml",
        corr / "gates/CR22/RESULT.yaml",
        corr / "gates/CR23/MANUAL-EXECUTION.yaml",
    ]

    before = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    result = project_composite_execution_preflight(
        repo,
        **_zo013_kwargs(tmp_path),
    )

    after = {
        str(path):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for path in paths
    }

    assert before == after
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False
    assert result["automatic_reconciliation"] is False


def test_cr23_zo013_never_executes_or_reconciles(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    import shutil

    import scripts.lib.eos.convergence_roadmap as roadmap_module

    repo = tmp_path / "repo"

    shutil.copytree(
        Path.cwd(),
        repo,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            "runtime",
        ),
    )

    _zo009_fixture_rebind(repo)

    called = {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }

    def forbidden_advance(*args, **kwargs):
        called["advance"] = True
        raise AssertionError("advancement executed")

    def forbidden_review(*args, **kwargs):
        called["review"] = True
        raise AssertionError("review transaction executed")

    def forbidden_rebind(*args, **kwargs):
        called["emm_rebind"] = True
        raise AssertionError("EMM rebind executed")

    monkeypatch.setattr(
        roadmap_module,
        "apply_gate_advancement_transaction",
        forbidden_advance,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_operator_review_transaction",
        forbidden_review,
    )

    monkeypatch.setattr(
        roadmap_module,
        "apply_emm_rebind_transaction",
        forbidden_rebind,
    )

    result = (
        roadmap_module.project_composite_execution_preflight(
            repo,
            **_zo013_kwargs(tmp_path),
        )
    )

    assert result["ready"] is True
    assert result["execution_performed"] is False
    assert result["state_advanced"] is False
    assert result["parent_gate_advanced"] is False
    assert result["successor_executed"] is False
    assert result["automatic_reconciliation"] is False

    assert called == {
        "advance": False,
        "review": False,
        "emm_rebind": False,
    }


def _cr47_repository(tmp_path):
    return _build_test_repository(tmp_path)


def _cr47_result_path(repo):
    return (
        repo / ROADMAP_RELATIVE_ROOT
        / "gates/C02-controlled-documentation-and-authority/RESULT.yaml"
    )


def test_cr47_zo012_authority_surface_contract(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_authority_surface_contract

    value = project_authority_surface_contract(_cr47_repository(tmp_path))
    assert value["field"] == "result_location"
    assert value["authority_kind"] == "GATE_DEFINITION"
    assert value["roadmap_reference_role"] == "LOCATOR_PROVENANCE"
    assert value["read_only"] is True


def test_cr47_zo018_missing_result_diagnostic(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_result_lifecycle_diagnostic

    repo = _cr47_repository(tmp_path)
    _cr47_result_path(repo).unlink()
    value = project_result_lifecycle_diagnostic(repo)
    assert value["classification"] == "ABSENT"
    assert value["blocking_dependency"] == "ACTIVE_GATE_RESULT"
    assert value["state_advanced"] is False


def test_cr47_zo019_result_diagnostic_is_bounded_to_active_gate(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_result_lifecycle_diagnostic

    value = project_result_lifecycle_diagnostic(_cr47_repository(tmp_path))
    assert value["active_gate_id"] == "C02"
    assert value["diagnostic_scope"] == "ACTIVE_GATE_ONLY"
    assert "gate_results" not in value


def test_cr47_zo020_wrong_gate_result_diagnostic(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_result_lifecycle_diagnostic

    repo = _cr47_repository(tmp_path)
    path = _cr47_result_path(repo)
    result = yaml.safe_load(path.read_text())
    result["gate_id"] = "C03"
    path.write_text(yaml.safe_dump(result, sort_keys=False))
    value = project_result_lifecycle_diagnostic(repo)
    assert value["classification"] == "WRONG_GATE_RESULT"
    assert value["identity"]["active_gate_id"] == "C02"
    assert value["identity"]["result_declared_gate_id"] == "C03"


def test_cr47_zo021_result_authority_identity_projection(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_result_authority_identity

    value = project_result_authority_identity(_cr47_repository(tmp_path))
    assert value["identity_state"] == "MATCH"
    assert value["active_gate_id"] == value["result_declared_gate_id"] == "C02"
    assert value["authority_kind"] == "GATE_DEFINITION"


def test_cr47_zo023_stale_result_diagnostic(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_result_lifecycle_diagnostic

    repo = _cr47_repository(tmp_path)
    path = _cr47_result_path(repo)
    result = yaml.safe_load(path.read_text())
    result["starting_state"]["gate_contract_sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(result, sort_keys=False))
    value = project_result_lifecycle_diagnostic(repo)
    assert value["classification"] == "STALE"
    assert value["stale_authority"]["declared_gate_definition_digest"] == "0" * 64


def test_cr47_zo028_acceptance_target_authority_projection(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_acceptance_target_authority

    repo = _cr47_repository(tmp_path)
    valid = project_acceptance_target_authority(repo, target_gate_id="C02")
    wrong = project_acceptance_target_authority(repo, target_gate_id="C03")
    assert valid["classification"] == "AUTHORIZED_TARGET"
    assert wrong["classification"] == "WRONG_CURRENT_GATE"
    assert wrong["authority_kind"] == "ROADMAP_STATE"


def test_cr47_zo029_acceptance_boundary_diagnostic_projection(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_acceptance_readiness

    value = project_acceptance_readiness(
        _cr47_repository(tmp_path), target_gate_id="C03",
    )
    assert value["ready"] is False
    assert "TARGET_IS_ACTIVE_GATE" in value["blockers"]
    assert value["acceptance_executed"] is False


def test_cr47_zo031_acceptance_prerequisite_projection(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_acceptance_prerequisites

    value = project_acceptance_prerequisites(_cr47_repository(tmp_path))
    assert value["all_satisfied"] is True
    assert [item["prerequisite"] for item in value["prerequisites"]] == [
        "TARGET_IS_ACTIVE_GATE", "RESULT_IS_VALID_FINAL", "AWAITING_OPERATOR_REVIEW",
    ]
    assert value["acceptance_receipt_created"] is False


def test_cr47_zo032_acceptance_readiness_diagnostic_projection(tmp_path):
    from scripts.lib.eos.convergence_roadmap import project_acceptance_readiness

    repo = _cr47_repository(tmp_path)
    before = _cr47_result_path(repo).read_bytes()
    value = project_acceptance_readiness(repo)
    assert value["classification"] == "READY_FOR_EXPLICIT_ACCEPTANCE"
    assert value["next_authorized_action"] == "REQUEST_EXPLICIT_OPERATOR_ACCEPTANCE"
    assert value["acceptance_receipt_created"] is False
    assert value["state_advanced"] is False
    assert value["successor_executed"] is False
    assert _cr47_result_path(repo).read_bytes() == before
