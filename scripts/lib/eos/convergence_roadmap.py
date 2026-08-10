#!/usr/bin/env python3
"""Read-only resolver for the Engineering System Convergence roadmap.

The roadmap files own planning and gate-position facts.  This resolver performs
the EMM-owned binding, digest, provenance, and drift checks before projecting
those facts to engctl.  It never changes roadmap, project, registry, or EOS
state.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from yaml.constructor import ConstructorError


DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ROADMAP_RELATIVE_ROOT = Path("engineering/convergence/engineering-system-convergence")
ROADMAP_FILE = "roadmap.yaml"
STATE_FILE = "STATE.yaml"
MANIFEST_FILE = "binding-manifest.yaml"
PROJECT_STATE = Path("docs/project/PROJ-0001-PROJECT_STATE.md")
EXPECTED_GATE_IDS = [f"C{number:02d}" for number in range(21)]
TERMINAL_RESULTS = {"COMPLETE", "COMPLETE_WITH_FINDINGS"}
GATE_STATUSES = {"COMPLETE", "COMPLETE_WITH_FINDINGS", "CURRENT", "PENDING", "BLOCKED"}
PROHIBITED_DURABLE_KEYS = {"provider_session_id", "session_id", "thread_id", "transport_id"}
EXECUTABLE_CLASSES = {"EXECUTABLE", "IMPLEMENTATION", "RECOVERY_RESUME"}
HISTORICAL_GATE_IDS = {"C00", "C01"}
ACTIVATION_GATE_IDS = {"C02"}
PROSPECTIVE_GATE_IDS = set(EXPECTED_GATE_IDS) - HISTORICAL_GATE_IDS - ACTIVATION_GATE_IDS
EVALUATION_CRITERIA = (
    "procedural_sufficiency", "discovery_sufficiency", "coverage_determinism",
    "classification_determinism", "artifact_determinism", "evidence_sufficiency",
    "result_determinism", "authority_boundaries", "fail_closed_behavior",
    "review_boundary", "state_transition_determinism", "persistence",
    "cold_resume", "terminal_semantics",
)


class RoadmapError(ValueError):
    """Raised when authoritative roadmap inputs cannot be resolved uniquely."""


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key: {key}", key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RoadmapError(f"{label} missing: {path}")
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as error:
        raise RoadmapError(f"{label} malformed: {error}") from error
    if not isinstance(value, dict):
        raise RoadmapError(f"{label} root must be a mapping: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise RoadmapError(f"cannot read bound source {path}: {error}") from error
    return digest.hexdigest()


def _safe_repository_path(repository_root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise RoadmapError(f"{label} must be a non-empty repository-relative path")
    path = (repository_root / value).resolve()
    if path != repository_root and repository_root not in path.parents:
        raise RoadmapError(f"{label} escapes repository root: {value}")
    return path


def _schema_validate(instance: dict[str, Any], schema_path: Path, label: str) -> None:
    schema = _load_yaml(schema_path, f"{label} schema")
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.SchemaError as error:
        raise RoadmapError(f"{label} schema invalid: {error.message}") from error
    except jsonschema.ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise RoadmapError(f"{label} invalid at {location}: {error.message}") from error


def _reject_runtime_identifiers(value: Any, location: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in PROHIBITED_DURABLE_KEYS:
                raise RoadmapError(f"durable roadmap contains prohibited runtime identifier at {location}.{key}")
            _reject_runtime_identifiers(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_runtime_identifiers(child, f"{location}[{index}]")


def _frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RoadmapError(f"Project State unavailable: {error}") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise RoadmapError("Project State frontmatter missing")
    try:
        end = lines.index("---", 1)
        value = yaml.load("\n".join(lines[1:end]), Loader=UniqueKeyLoader)
    except (ValueError, yaml.YAMLError) as error:
        raise RoadmapError(f"Project State frontmatter malformed: {error}") from error
    if not isinstance(value, dict):
        raise RoadmapError("Project State frontmatter must be a mapping")
    return value


class ConvergenceRoadmap:
    """Resolve and validate one repository-authoritative convergence roadmap."""

    def __init__(self, repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
                 roadmap_root: Path | str | None = None) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.roadmap_root = (
            Path(roadmap_root).resolve() if roadmap_root is not None
            else (self.repository_root / ROADMAP_RELATIVE_ROOT).resolve()
        )
        if self.roadmap_root != self.repository_root and self.repository_root not in self.roadmap_root.parents:
            raise RoadmapError("roadmap root must be inside the repository")
        self.roadmap_path = self.roadmap_root / ROADMAP_FILE
        self.state_path = self.roadmap_root / STATE_FILE
        self.manifest_path = self.roadmap_root / MANIFEST_FILE

    def validate(self) -> dict[str, Any]:
        roadmap = _load_yaml(self.roadmap_path, "roadmap definition")
        state = _load_yaml(self.state_path, "roadmap state")
        _schema_validate(roadmap, self.roadmap_root / "schemas/roadmap.schema.yaml", "roadmap definition")
        _schema_validate(state, self.roadmap_root / "schemas/state.schema.yaml", "roadmap state")
        _reject_runtime_identifiers(roadmap, "roadmap")
        _reject_runtime_identifiers(state, "state")

        if roadmap["roadmap_id"] != state["roadmap_id"]:
            raise RoadmapError("roadmap definition and state roadmap_id disagree")
        if str(roadmap["roadmap_version"]) != str(state["roadmap_version"]):
            raise RoadmapError("roadmap definition and state roadmap_version disagree")
        if roadmap["state_path"] != str(ROADMAP_RELATIVE_ROOT / STATE_FILE):
            raise RoadmapError("roadmap state path is not canonical")
        if roadmap["binding_manifest"] != str(ROADMAP_RELATIVE_ROOT / MANIFEST_FILE):
            raise RoadmapError("roadmap binding manifest path is not canonical")
        if roadmap["program_id"] != "ENGINEERING-SYSTEM-CONVERGENCE":
            raise RoadmapError("unexpected convergence program identity")
        if state["repository_baseline"] != roadmap["repository"]["baseline"]:
            raise RoadmapError("roadmap definition and state repository baseline disagree")

        gate_refs = roadmap["gates"]
        gate_ids = [item.get("gate_id") for item in gate_refs]
        if not set(EXPECTED_GATE_IDS).issubset(gate_ids) or len(set(gate_ids)) != len(gate_ids):
            raise RoadmapError("gate sequence must contain unique required C00 through C20 identities")
        gate_orders = {item["gate_id"]: item["roadmap_order"] for item in gate_refs}
        if len(gate_orders) != len(gate_refs) or gate_orders != dict(sorted(gate_orders.items(), key=lambda pair: pair[1])):
            raise RoadmapError("roadmap gate ordering must be unique and monotonically recorded")
        gate_identities = [item["gate_identity"] for item in gate_refs]
        if len(set(gate_identities)) != len(gate_identities):
            raise RoadmapError("roadmap gate identities must be unique")

        gates: dict[str, dict[str, Any]] = {}
        for item in gate_refs:
            gate_id = item["gate_id"]
            gate_path = _safe_repository_path(self.repository_root, item["definition"], f"{gate_id} definition")
            expected_parent = self.roadmap_root / "gates"
            if expected_parent not in gate_path.parents:
                raise RoadmapError(f"{gate_id} definition is outside canonical gate tree")
            gate = _load_yaml(gate_path, f"{gate_id} definition")
            provenance = item["contract_provenance"]
            schema_path = _safe_repository_path(
                self.repository_root, provenance["validation_schema"],
                f"{gate_id} validation schema",
            )
            if schema_path.parent != self.roadmap_root / "schemas":
                raise RoadmapError(f"{gate_id} validation schema is outside canonical schema tree")
            _schema_validate(gate, schema_path, f"{gate_id} definition")
            _reject_runtime_identifiers(gate, f"gate.{gate_id}")
            if gate["gate_id"] != gate_id:
                raise RoadmapError(f"{gate_id} definition identity mismatch")
            if gate["status"] not in GATE_STATUSES:
                raise RoadmapError(f"{gate_id} has unsupported status")
            if gate["result_location"] != item["result"]:
                raise RoadmapError(f"{gate_id} result location disagrees with roadmap index")
            gates[gate_id] = gate

        for gate_id, gate in gates.items():
            for dependency in gate["dependencies"]:
                if dependency not in gates:
                    raise RoadmapError(f"{gate_id} dependency does not resolve: {dependency}")
                if gate_orders[dependency] >= gate_orders[gate_id]:
                    raise RoadmapError(f"{gate_id} dependency is not a predecessor: {dependency}")
            if gate_id not in HISTORICAL_GATE_IDS and gate_id not in ACTIVATION_GATE_IDS:
                terminal = gate["terminal"]
                if terminal["is_terminal"]:
                    if gate["next_gate"] is not None:
                        raise RoadmapError(f"{gate_id} terminal gate must set next_gate to null")
                    if not terminal["continuation_authority"] or not terminal["continuation_action"]:
                        raise RoadmapError(f"{gate_id} terminal continuation is ambiguous")
                else:
                    if gate["next_gate"] not in gates:
                        raise RoadmapError(f"{gate_id} next_gate does not resolve")
                    if gate_orders[gate["next_gate"]] <= gate_orders[gate_id]:
                        raise RoadmapError(f"{gate_id} next_gate does not advance roadmap order")
                    if gate_id == EXPECTED_GATE_IDS[-1] and gate["next_gate"] is None:
                        raise RoadmapError(f"{gate_id} final gate must declare terminal semantics")
                    if terminal["continuation_authority"] is not None or terminal["continuation_action"] is not None:
                        raise RoadmapError(f"{gate_id} non-terminal gate declares external continuation")
            else:
                if gate["next_gate"] not in gates or gate_orders[gate["next_gate"]] <= gate_orders[gate_id]:
                    raise RoadmapError(f"{gate_id} historical next_gate is not deterministic")

        completed = state["completed_gates"]
        blocked = state["blocked_gates"]
        pending = state["pending_gates"]
        current = state["current_gate"]
        for label, values in (("completed", completed), ("blocked", blocked), ("pending", pending)):
            if len(values) != len(set(values)):
                raise RoadmapError(f"duplicate {label} gate")
            unknown = sorted(set(values) - set(gates))
            if unknown:
                raise RoadmapError(f"unknown {label} gate(s): {', '.join(unknown)}")
        if current not in gates:
            raise RoadmapError(f"current gate does not resolve: {current}")
        if current in completed or current in blocked or current not in pending:
            raise RoadmapError("current gate classification is inconsistent")
        if set(completed) & set(blocked) or set(completed) & set(pending) or set(blocked) & set(pending):
            raise RoadmapError("gate state sets overlap")
        if set(completed + blocked + pending) != set(gates):
            raise RoadmapError("gate state sets do not cover the roadmap")

        for item in gate_refs:
            gate_id = item["gate_id"]
            provenance = item["contract_provenance"]
            expected_lifecycle = (
                "COMPLETE" if gate_id in completed else
                "BLOCKED" if gate_id in blocked else
                "CURRENT" if gate_id == current else
                "PENDING"
            )
            if provenance["lifecycle"] != expected_lifecycle:
                raise RoadmapError(f"{gate_id} roadmap provenance lifecycle disagrees with state")
            expected_generation = (
                "HISTORICAL_FROZEN" if gate_id in HISTORICAL_GATE_IDS else
                "ACTIVATION_FROZEN" if gate_id in ACTIVATION_GATE_IDS else
                "PROSPECTIVE_EXECUTABLE"
            )
            if provenance["contract_generation"] != expected_generation:
                raise RoadmapError(f"{gate_id} roadmap provenance generation is not canonical")
            expected_applicability = "STD-0006@1.0" if gate_id in PROSPECTIVE_GATE_IDS else "NOT_APPLICABLE"
            if provenance["standard_applicability"] != expected_applicability:
                raise RoadmapError(f"{gate_id} STD-0006 applicability is not canonical")
            expected_schema = (
                self.roadmap_root / "schemas/gate.schema.yaml"
                if gate_id not in HISTORICAL_GATE_IDS and gate_id not in ACTIVATION_GATE_IDS
                else self.roadmap_root / "schemas/gate-historical-v1.schema.yaml"
            )
            if _safe_repository_path(self.repository_root, provenance["validation_schema"], f"{gate_id} validation schema") != expected_schema:
                raise RoadmapError(f"{gate_id} selects the wrong generation validation schema")

        results: dict[str, dict[str, Any]] = {}
        for gate_id, gate in gates.items():
            expected_status = (
                "CURRENT" if gate_id == current else
                "BLOCKED" if gate_id in blocked else
                gate["status"] if gate_id in completed else "PENDING"
            )
            if gate["status"] != expected_status:
                raise RoadmapError(f"{gate_id} definition and state status disagree")
            unmet = [dependency for dependency in gate["dependencies"] if dependency not in completed]
            if gate_id == current and unmet:
                raise RoadmapError(f"current gate has incomplete dependencies: {', '.join(unmet)}")

            result_path = _safe_repository_path(self.repository_root, gate["result_location"], f"{gate_id} result")
            if gate_id in completed:
                result = _load_yaml(result_path, f"{gate_id} result")
                _schema_validate(result, self.roadmap_root / "schemas/result.schema.yaml", f"{gate_id} result")
                _reject_runtime_identifiers(result, f"result.{gate_id}")
                if result["gate_id"] != gate_id or result["result"] != gate["status"]:
                    raise RoadmapError(f"{gate_id} state/evidence contradiction")
                if result["result"] not in TERMINAL_RESULTS:
                    raise RoadmapError(f"{gate_id} is completed without a terminal result")
                if not result["evidence"] or not all(item.get("path") for item in result["evidence"]):
                    raise RoadmapError(f"{gate_id} completion lacks evidence")
                for evidence in result["evidence"]:
                    evidence_path = _safe_repository_path(
                        self.repository_root, evidence["path"], f"{gate_id} evidence"
                    )
                    if not evidence_path.exists():
                        raise RoadmapError(f"{gate_id} evidence missing: {evidence['path']}")
                    supplied_digest = evidence.get("sha256")
                    if supplied_digest and (not evidence_path.is_file() or _sha256(evidence_path) != supplied_digest):
                        raise RoadmapError(f"{gate_id} evidence digest mismatch: {evidence['path']}")
                    if evidence_path.suffix in {".yaml", ".yml"}:
                        self._validate_evidence_manifest(gate_id, evidence_path)
                results[gate_id] = result
            elif result_path.exists():
                raise RoadmapError(f"{gate_id} has a result but is not completed")

        if state["last_completed_gate"] != (completed[-1] if completed else None):
            raise RoadmapError("last_completed_gate disagrees with completed_gates")
        last_result = gates[state["last_completed_gate"]]["result_location"] if completed else None
        if state["last_result"] != last_result:
            raise RoadmapError("last_result does not identify the last completed gate result")
        if completed:
            last_evidence = state["last_evidence"]
            if not isinstance(last_evidence, str) or not last_evidence:
                raise RoadmapError("last_evidence is required after completion")
            _safe_repository_path(self.repository_root, last_evidence, "last evidence").is_file() or (
                _raise("last_evidence does not exist")
            )

        current_gate = gates[current]
        if state["next_authorized_action"] != current_gate["resume_instructions"]["next_authorized_action"]:
            raise RoadmapError("state and current gate next authorized action disagree")

        self._validate_project_state(roadmap, state)
        self._validate_manifest(roadmap, state, gates)
        return {
            "result": "PASS",
            "roadmap": roadmap,
            "state": state,
            "gates": gates,
            "results": results,
            "roadmap_path": self.roadmap_path,
            "state_path": self.state_path,
            "manifest_path": self.manifest_path,
            "drift_owner": "EMM",
            "read_only": True,
        }

    def evaluate(self, resolved: dict[str, Any] | None = None, *, compare_persisted: bool = True) -> dict[str, Any]:
        """Evaluate execution sufficiency without adding roadmap-specific methodology."""
        resolved = resolved or self.validate()
        roadmap = resolved["roadmap"]
        gates = resolved["gates"]
        contract = roadmap["evaluation_contract"]
        catalog_path = _safe_repository_path(
            self.repository_root, contract["playbook_catalog"], "execution playbook catalog"
        )
        schema_path = _safe_repository_path(
            self.repository_root, contract["playbook_schema"], "execution playbook schema"
        )
        evaluation_schema_path = _safe_repository_path(
            self.repository_root, contract["evaluation_schema"], "roadmap evaluation schema"
        )
        catalog = _load_yaml(catalog_path, "execution playbook catalog")
        _schema_validate(catalog, schema_path, "execution playbook catalog")
        _reject_runtime_identifiers(catalog, "execution_playbook_catalog")
        shared = catalog["shared_contracts"]
        shared_ids = {
            name: definition["contract_id"] for name, definition in shared.items()
        }

        gate_results: list[dict[str, Any]] = []
        all_blockers: list[str] = []
        all_warnings: list[str] = []
        for gate_id, gate in gates.items():
            provenance = next(item["contract_provenance"] for item in roadmap["gates"] if item["gate_id"] == gate_id)
            if provenance["standard_applicability"] == "NOT_APPLICABLE":
                gate_results.append({
                    "gate_id": gate_id,
                    "result": "NOT_APPLICABLE",
                    "contract_generation": provenance["contract_generation"],
                    "standard_applicability": provenance["standard_applicability"],
                    "criteria": {name: "NOT_APPLICABLE" for name in EVALUATION_CRITERIA},
                    "warnings": [],
                    "blockers": [],
                })
                continue
            criteria = {name: "PASS" for name in EVALUATION_CRITERIA}
            blockers: list[str] = []
            warnings: list[str] = []

            reference = gate.get("execution_playbook") or {}
            if reference.get("catalog") != contract["playbook_catalog"]:
                blockers.append("execution playbook catalog does not match roadmap evaluation contract")
            playbook = catalog["playbooks"].get(reference.get("playbook_id"))
            if not isinstance(playbook, dict):
                blockers.append("execution playbook does not resolve")
                for criterion in EVALUATION_CRITERIA:
                    criteria[criterion] = "FAIL"
            else:
                if playbook.get("gate_id") != gate_id:
                    blockers.append("execution playbook gate identity mismatch")

                procedure = gate.get("assessment_or_execution_procedure")
                if not isinstance(procedure, list) or not procedure or not playbook.get("inventory_method"):
                    criteria["procedural_sufficiency"] = "FAIL"
                    blockers.append("procedure or inventory method is missing")

                surfaces = playbook.get("discovery_surfaces") or []
                if not surfaces:
                    criteria["discovery_sufficiency"] = "FAIL"
                    blockers.append("discovery surfaces are missing")
                for surface in surfaces:
                    if surface.get("existence") != "REQUIRED" or surface.get("kind") not in {"PATH", "GLOB"}:
                        continue
                    location = surface.get("location")
                    try:
                        path = _safe_repository_path(
                            self.repository_root, location, f"{gate_id} discovery surface"
                        )
                    except RoadmapError as error:
                        criteria["discovery_sufficiency"] = "FAIL"
                        blockers.append(str(error))
                        continue
                    if surface.get("kind") == "PATH" and not path.exists():
                        criteria["discovery_sufficiency"] = "FAIL"
                        blockers.append(f"required discovery surface missing: {location}")

                coverage = playbook.get("coverage_rules") or []
                if not coverage or any(not rule.get("requirement") or not rule.get("evidence") for rule in coverage):
                    criteria["coverage_determinism"] = "FAIL"
                    blockers.append("coverage rules are missing or incomplete")

                vocabulary = playbook.get("classification_vocabulary") or {}
                if playbook.get("classification_required") and (
                    not vocabulary.get("finding_classes") or not vocabulary.get("severity")
                ):
                    criteria["classification_determinism"] = "FAIL"
                    blockers.append("required classification vocabulary is missing")

                artifacts = playbook.get("artifact_contracts") or []
                artifact_ids = [artifact.get("artifact_id") for artifact in artifacts]
                if (
                    not artifacts or len(artifact_ids) != len(set(artifact_ids))
                    or any(
                        not artifact.get("minimum_record_fields")
                        or not artifact.get("completeness_key")
                        or not artifact.get("purpose")
                        for artifact in artifacts
                    )
                ):
                    criteria["artifact_determinism"] = "FAIL"
                    blockers.append("artifact contracts are missing, duplicate, or incomplete")

                if not gate.get("required_evidence") or not gate.get("evidence_location"):
                    criteria["evidence_sufficiency"] = "FAIL"
                    blockers.append("required evidence contract or location is missing")

                required_results = {"COMPLETE", "COMPLETE_WITH_FINDINGS", "BLOCKED", "FAILED"}
                if set((playbook.get("result_rules") or {}).keys()) != required_results:
                    criteria["result_determinism"] = "FAIL"
                    blockers.append("result rules are incomplete or ambiguous")
                if playbook.get("result_contract") != shared_ids["result_contract"]:
                    criteria["result_determinism"] = "FAIL"
                    blockers.append("result contract does not resolve")

                if not gate.get("scope_out") or not playbook.get("prohibited_operations"):
                    criteria["authority_boundaries"] = "FAIL"
                    blockers.append("scope-out or prohibited-operation boundary is missing")
                if not gate.get("fail_closed_conditions") or not gate.get("stop_boundary"):
                    criteria["fail_closed_behavior"] = "FAIL"
                    blockers.append("fail-closed or stop boundary is missing")

                shared_references = {
                    "review_boundary": ("review_contract", "review_contract"),
                    "state_transition_determinism": ("state_transition_contract", "state_transition_contract"),
                    "persistence": ("persistence_contract", "persistence_contract"),
                    "cold_resume": ("cold_resume_contract", "cold_resume_contract"),
                }
                for criterion, (field, shared_name) in shared_references.items():
                    if playbook.get(field) != shared_ids[shared_name]:
                        criteria[criterion] = "FAIL"
                        blockers.append(f"{field.replace('_', ' ')} does not resolve")

                if not playbook.get("cross_checks") or not playbook.get("completeness_tests"):
                    criteria["coverage_determinism"] = "FAIL"
                    blockers.append("cross-checks or completeness tests are missing")

                terminal = gate.get("terminal") or {}
                if terminal.get("is_terminal"):
                    if gate.get("next_gate") is not None or not terminal.get("continuation_authority") or not terminal.get("continuation_action"):
                        criteria["terminal_semantics"] = "FAIL"
                        blockers.append("terminal continuation is ambiguous")
                elif gate.get("next_gate") is None:
                    criteria["terminal_semantics"] = "FAIL"
                    blockers.append("non-terminal gate has no successor")

            result = "FAIL" if blockers else "PASS"
            all_blockers.extend(f"{gate_id}: {blocker}" for blocker in blockers)
            all_warnings.extend(f"{gate_id}: {warning}" for warning in warnings)
            gate_results.append({
                "gate_id": gate_id,
                "result": result,
                "contract_generation": provenance["contract_generation"],
                "standard_applicability": provenance["standard_applicability"],
                "criteria": criteria,
                "warnings": warnings,
                "blockers": blockers,
            })

        criterion_dimensions = {
            "procedural_result": "procedural_sufficiency",
            "discovery_result": "discovery_sufficiency",
            "coverage_result": "coverage_determinism",
            "classification_result": "classification_determinism",
            "artifact_contract_result": "artifact_determinism",
            "evidence_result": "evidence_sufficiency",
            "result_determinism_result": "result_determinism",
            "authority_boundary_result": "authority_boundaries",
            "fail_closed_result": "fail_closed_behavior",
            "review_boundary_result": "review_boundary",
            "state_transition_result": "state_transition_determinism",
            "persistence_result": "persistence",
            "cold_resume_result": "cold_resume",
        }
        evaluated_gate_results = [item for item in gate_results if item["standard_applicability"] != "NOT_APPLICABLE"]
        dimension_results = {
            dimension: "PASS" if all(
                gate_result["criteria"][criterion] == "PASS" for gate_result in evaluated_gate_results
            ) else "FAIL"
            for dimension, criterion in criterion_dimensions.items()
        }

        persisted_path = _safe_repository_path(
            self.repository_root, contract["persisted_evaluation"], "persisted roadmap evaluation"
        )
        persisted = _load_yaml(persisted_path, "persisted roadmap evaluation") if persisted_path.is_file() else None
        evaluated_at = (
            persisted.get("evaluated_at") if persisted else resolved["state"]["updated_at"]
        )
        executable_claim = roadmap["roadmap_class"] in EXECUTABLE_CLASSES
        if roadmap["roadmap_class"] == "PLANNING_ONLY":
            all_warnings.append("Roadmap class PLANNING_ONLY is structurally valid but cannot be executable.")
        executable = executable_claim and not all_blockers
        result: dict[str, Any] = {
            "schema_version": 1,
            "roadmap_id": roadmap["roadmap_id"],
            "roadmap_version": str(roadmap["roadmap_version"]),
            "evaluation_standard": {
                "standard": contract["standard"],
                "procedure": contract["procedure"],
                "playbook_contract": f"{catalog['contract_id']}@{catalog['contract_version']}",
            },
            "evaluated_at": evaluated_at,
            "structural_result": "PASS",
            **dimension_results,
            "gate_results": gate_results,
            "warnings": all_warnings,
            "blockers": all_blockers,
            "overall_result": "PASS" if executable else "NOT_EXECUTABLE",
            "executable": executable,
        }

        if persisted and compare_persisted:
            comparable_keys = [
                "roadmap_id", "roadmap_version", "evaluation_standard", "structural_result",
                *dimension_results.keys(), "gate_results", "warnings", "blockers",
                "overall_result", "executable",
            ]
            if any(persisted.get(key) != result.get(key) for key in comparable_keys):
                result["blockers"].append("Persisted evaluation does not match live execution-sufficiency result.")
                result["overall_result"] = "NOT_EXECUTABLE"
                result["executable"] = False

        _schema_validate(result, evaluation_schema_path, "live roadmap evaluation")
        return result

    def _validate_project_state(self, roadmap: dict[str, Any], state: dict[str, Any]) -> None:
        project_state_path = _safe_repository_path(
            self.repository_root, roadmap["project_state_path"], "Project State path"
        )
        value = _frontmatter(project_state_path)
        if value.get("mission") != roadmap["program_title"]:
            raise RoadmapError("Project State mission and convergence program disagree")
        if not str(value.get("phase", "")).startswith(state["current_gate"]):
            raise RoadmapError("Project State phase and convergence current gate disagree")
        binding = value.get("convergence_program")
        expected = {
            "program_id": roadmap["program_id"],
            "roadmap_id": roadmap["roadmap_id"],
            "roadmap_version": roadmap["roadmap_version"],
            "roadmap_path": str(ROADMAP_RELATIVE_ROOT / ROADMAP_FILE),
            "state_path": str(ROADMAP_RELATIVE_ROOT / STATE_FILE),
            "current_gate": state["current_gate"],
            "next_authorized_action": state["next_authorized_action"],
            "executable_qualification": state["executable_qualification"]["result"],
            "evaluation_standard": state["executable_qualification"]["standard"],
            "evaluation_procedure": state["executable_qualification"]["procedure"],
            "evaluation_result": state["executable_qualification"]["evaluation_result"],
        }
        if binding != expected:
            raise RoadmapError("Project State and convergence roadmap state disagree")

    def _validate_manifest(self, roadmap: dict[str, Any], state: dict[str, Any],
                           gates: dict[str, dict[str, Any]]) -> None:
        manifest = _load_yaml(self.manifest_path, "EMM binding manifest")
        if manifest.get("schema_version") != 1 or manifest.get("roadmap_id") != roadmap["roadmap_id"]:
            raise RoadmapError("EMM binding manifest identity mismatch")
        entries = manifest.get("sources")
        if not isinstance(entries, list) or not entries:
            raise RoadmapError("EMM binding manifest has no sources")
        by_path: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                raise RoadmapError("EMM binding manifest source is malformed")
            path = entry["path"]
            digest = entry["sha256"]
            if path in by_path:
                raise RoadmapError(f"duplicate EMM binding source: {path}")
            if not isinstance(digest, str) or len(digest) != 64:
                raise RoadmapError(f"invalid EMM binding digest: {path}")
            by_path[path] = digest

        required = {
            str(ROADMAP_RELATIVE_ROOT / ROADMAP_FILE),
            str(ROADMAP_RELATIVE_ROOT / STATE_FILE),
            roadmap["project_state_path"],
        }
        required.update(item["definition"] for item in roadmap["gates"])
        required.update(gates[gate_id]["result_location"] for gate_id in state["completed_gates"])
        required.update((
            roadmap["evaluation_contract"]["playbook_catalog"],
            roadmap["evaluation_contract"]["playbook_schema"],
            roadmap["evaluation_contract"]["evaluation_schema"],
            roadmap["evaluation_contract"]["persisted_evaluation"],
        ))
        missing = sorted(required - set(by_path))
        if missing:
            raise RoadmapError(f"EMM binding manifest missing required source(s): {', '.join(missing)}")
        for relative, expected in by_path.items():
            path = _safe_repository_path(self.repository_root, relative, "EMM binding source")
            if not path.is_file():
                raise RoadmapError(f"EMM binding source missing: {relative}")
            actual = _sha256(path)
            if actual != expected:
                raise RoadmapError(f"EMM source drift: {relative}")

    def _validate_evidence_manifest(self, gate_id: str, path: Path) -> None:
        value = _load_yaml(path, f"{gate_id} evidence manifest")
        files = value.get("files")
        if files is None:
            return
        if value.get("gate_id") != gate_id or not isinstance(files, list) or not files:
            raise RoadmapError(f"{gate_id} evidence manifest is malformed")
        canonical = _safe_repository_path(
            self.repository_root, value.get("canonical_location"), f"{gate_id} canonical evidence location"
        )
        seen: set[str] = set()
        for item in files:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                raise RoadmapError(f"{gate_id} evidence manifest entry is malformed")
            relative, expected = item["path"], item["sha256"]
            if relative in seen or not isinstance(relative, str) or Path(relative).is_absolute():
                raise RoadmapError(f"{gate_id} evidence manifest path is invalid: {relative}")
            seen.add(relative)
            evidence_file = (canonical / relative).resolve()
            if canonical not in evidence_file.parents or not evidence_file.is_file():
                raise RoadmapError(f"{gate_id} manifested evidence missing: {relative}")
            if not isinstance(expected, str) or _sha256(evidence_file) != expected:
                raise RoadmapError(f"{gate_id} manifested evidence digest mismatch: {relative}")

    def projection(self) -> dict[str, Any]:
        resolved = self.validate()
        state = resolved["state"]
        roadmap = resolved["roadmap"]
        gate = resolved["gates"][state["current_gate"]]
        return {
            "result": "PASS",
            "program_id": roadmap["program_id"],
            "program": roadmap["program_title"],
            "roadmap_id": roadmap["roadmap_id"],
            "roadmap_version": roadmap["roadmap_version"],
            "roadmap": str(resolved["roadmap_path"]),
            "roadmap_state": str(resolved["state_path"]),
            "program_state": state["program_state"],
            "current_gate": state["current_gate"],
            "current_gate_title": gate["title"],
            "last_completed_gate": state["last_completed_gate"],
            "completed_gates": state["completed_gates"],
            "blocked_gates": state["blocked_gates"],
            "pending_gates": state["pending_gates"],
            "next_authorized_action": state["next_authorized_action"],
            "execution_sufficiency": state["executable_qualification"]["result"],
            "executable": state["executable_qualification"]["executable"],
            "gate_definition": str(_safe_repository_path(
                self.repository_root,
                next(item["definition"] for item in roadmap["gates"] if item["gate_id"] == state["current_gate"]),
                "current gate definition",
            )),
            "gate_result": str(_safe_repository_path(
                self.repository_root, gate["result_location"], "current gate result"
            )),
            "gate_evidence": str(_safe_repository_path(
                self.repository_root, gate["evidence_location"], "current gate evidence"
            )),
            "last_result": str(_safe_repository_path(
                self.repository_root, state["last_result"], "last result"
            )) if state["last_result"] else None,
            "last_evidence": str(_safe_repository_path(
                self.repository_root, state["last_evidence"], "last evidence"
            )) if state["last_evidence"] else None,
            "repository_baseline": state["repository_baseline"],
            "queue_authority": roadmap["authority_model"]["queue_model"]["current_authority"],
            "queue_role": roadmap["authority_model"]["queue_model"]["current_role"],
            "future_queue_authority": roadmap["authority_model"]["queue_model"]["future_authority"],
            "future_queue_role": "NOT_YET_ACTIVE",
            "history_model": roadmap["authority_model"]["mutation_policy"]["historical_model"],
            "maturity_model": roadmap["authority_model"]["mutation_policy"]["maturity_model"],
            "read_only": True,
        }


def _raise(message: str) -> bool:
    raise RoadmapError(message)


def _format_status(value: dict[str, Any], heading: str = "ENGINEERING SYSTEM CONVERGENCE ROADMAP") -> str:
    completed = ", ".join(value["completed_gates"]) or "none"
    blocked = ", ".join(value["blocked_gates"]) or "none"
    result_display = value["gate_result"] if Path(value["gate_result"]).is_file() else "not recorded"
    return "\n".join((
        heading,
        "-" * len(heading),
        "Result: PASS",
        f"Program: {value['program']}",
        f"Program ID: {value['program_id']}",
        f"Program State: {value['program_state']}",
        f"Roadmap ID: {value['roadmap_id']}",
        f"Roadmap Version: {value['roadmap_version']}",
        f"Execution Sufficiency: {value['execution_sufficiency']}",
        f"Executable: {'YES' if value['executable'] else 'NO'}",
        f"Roadmap: {value['roadmap']}",
        f"Roadmap State: {value['roadmap_state']}",
        f"Current Gate: {value['current_gate']} — {value['current_gate_title']}",
        f"Last Completed Gate: {value['last_completed_gate'] or 'none'}",
        f"Completed: {completed}",
        f"Blockers: {blocked}",
        f"Next Authorized Action: {value['next_authorized_action']}",
        f"Queue Authority: {value['queue_authority']} ({value['queue_role']})",
        f"Future Queue Authority: {value['future_queue_authority']} ({value['future_queue_role']})",
        f"History Model: {value['history_model']}",
        f"Maturity Model: {value['maturity_model']}",
        f"Gate Definition: {value['gate_definition']}",
        f"Gate Result: {result_display}",
        f"Gate Evidence: {value['gate_evidence']}",
        f"Last Result: {value['last_result'] or 'none'}",
        f"Last Evidence: {value['last_evidence'] or 'none'}",
        "Read-only: YES",
    ))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="engctl roadmap")
    parser.add_argument("--repository-root", default=str(DEFAULT_REPOSITORY_ROOT))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("show")
    subparsers.add_parser("results")
    subparsers.add_parser("validate")
    subparsers.add_parser("evaluate")
    subparsers.add_parser("resume")
    gate_parser = subparsers.add_parser("gate")
    gate_parser.add_argument("gate_id")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    resolver = ConvergenceRoadmap(args.repository_root)
    try:
        resolved = resolver.validate()
        if args.command in {"status", "resume"}:
            heading = "ENGINEERING SYSTEM CONVERGENCE" if args.command == "resume" else "ENGINEERING SYSTEM CONVERGENCE ROADMAP"
            print(_format_status(resolver.projection(), heading))
        elif args.command == "validate":
            evaluation = resolver.evaluate(resolved)
            print(f"PASS: {resolved['roadmap']['roadmap_id']} roadmap, state, gates, results, evidence, Project State, and EMM bindings are consistent")
            print("STRUCTURAL_VALIDITY=PASS")
            print(f"EXECUTION_SUFFICIENCY={evaluation['overall_result']}")
            print(f"EXECUTABLE={'YES' if evaluation['executable'] else 'NO'}")
            print("Read-only: YES")
            if resolved["roadmap"]["roadmap_class"] in EXECUTABLE_CLASSES and not evaluation["executable"]:
                return 1
        elif args.command == "evaluate":
            evaluation = resolver.evaluate(resolved)
            print(yaml.safe_dump(evaluation, sort_keys=False).rstrip())
            if resolved["roadmap"]["roadmap_class"] in EXECUTABLE_CLASSES and not evaluation["executable"]:
                return 1
        elif args.command == "show":
            print(yaml.safe_dump(resolved["roadmap"], sort_keys=False).rstrip())
        elif args.command == "gate":
            gate_id = args.gate_id.upper()
            if gate_id not in resolved["gates"]:
                raise RoadmapError(f"unknown gate: {args.gate_id}")
            print(yaml.safe_dump(resolved["gates"][gate_id], sort_keys=False).rstrip())
        elif args.command == "results":
            if not resolved["results"]:
                print("No completed gate results.")
            for gate_id in resolved["state"]["completed_gates"]:
                result = resolved["results"][gate_id]
                path = resolved["gates"][gate_id]["result_location"]
                print(f"{gate_id}: {result['result']} — {resolver.repository_root / path}")
            print("Read-only: YES")
    except RoadmapError as error:
        print(f"FAIL CLOSED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
