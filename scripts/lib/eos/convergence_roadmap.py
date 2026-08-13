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
import json
import sys
from pathlib import Path
try:
    from scripts.lib.eos.roadmap_lifecycle import (
        LifecycleError,
        LifecycleState,
        ResultClass,
        ResultFacts,
        classify_result,
        pending_review_transition,
        result_recorded_transition,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise

    from roadmap_lifecycle import (
        LifecycleError,
        LifecycleState,
        ResultClass,
        ResultFacts,
        classify_result,
        pending_review_transition,
        result_recorded_transition,
    )
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


def _canonical_next_authorized_action(
    repository_root: Path,
    state_action: str,
) -> str:
    """Consume a satisfied C18 review boundary without mutating EOS state."""
    if state_action != "REVIEW_C18_INTEGRATION_AUTHORITY_BOUNDARY":
        return state_action
    try:
        try:
            from scripts.lib.eos.maturity_recognition import resolve as resolve_maturity
        except ModuleNotFoundError as error:
            if error.name != "scripts":
                raise
            from maturity_recognition import resolve as resolve_maturity
        maturity = resolve_maturity(repository_root)
    except Exception:
        return state_action
    if maturity.get("result") == "PASS" and maturity.get("integration", {}).get("accepted") is True:
        action = maturity.get("next_authorized_action")
        if isinstance(action, str) and action.strip():
            return action.strip()
    return state_action


def project_bounded_implementation_authority(
    repository_root: Path | str,
    transaction: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one explicit bounded implementation transaction generically.

    Gate-specific requirements are supplied by ``policy``.  The generic
    resolver never assumes a particular gate or roadmap successor.
    """
    repository_root = Path(repository_root).resolve()
    resolver = ConvergenceRoadmap(repository_root)
    resolved = resolver.validate()
    blockers: list[str] = []
    if not isinstance(transaction, dict):
        transaction = {}
    policy = policy or {}

    required = {
        "transaction_id", "gate_id", "scope", "authorized_scope",
        "prerequisites", "qualification", "blockers", "authority",
        "successor_gate_execution_requested", "publication_requested",
    }
    missing = sorted(required - set(transaction))
    if missing:
        blockers.append("MISSING_TRANSACTION_FIELDS:" + ",".join(missing))

    gate_id = transaction.get("gate_id")
    required_gate_id = policy.get("required_gate_id")
    if required_gate_id is not None and gate_id != required_gate_id:
        blockers.append("GATE_POLICY_MISMATCH")

    transaction_id = transaction.get("transaction_id")
    if not isinstance(transaction_id, str) or not transaction_id.strip():
        blockers.append("TRANSACTION_ID_REQUIRED")

    if transaction.get("state") is not None and transaction.get("state") != "AUTHORIZED_FOR_IMPLEMENTATION":
        blockers.append("TRANSACTION_NOT_CURRENTLY_AUTHORIZED")
    if transaction.get("roadmap_id") is not None and transaction.get("roadmap_id") != resolved["roadmap"]["roadmap_id"]:
        blockers.append("ROADMAP_ID_MISMATCH")
    if transaction.get("roadmap_version") is not None and str(transaction.get("roadmap_version")) != str(resolved["roadmap"]["roadmap_version"]):
        blockers.append("ROADMAP_VERSION_MISMATCH")
    authority = transaction.get("authority")
    provenance = policy.get("provenance_reference")
    if provenance is not None and (
        not isinstance(authority, dict) or authority.get("provenance_reference") != provenance
    ):
        blockers.append("AUTHORITY_PROVENANCE_INVALID")

    scope = transaction.get("scope")
    authorized_scope = transaction.get("authorized_scope")
    if not isinstance(scope, list) or not scope or not all(isinstance(item, str) and item.strip() for item in scope):
        blockers.append("IMPLEMENTATION_SCOPE_REQUIRED")
        scope = []
    if not isinstance(authorized_scope, list) or not authorized_scope or not all(
        isinstance(item, str) and item.strip() for item in authorized_scope
    ):
        blockers.append("AUTHORIZED_SCOPE_REQUIRED")
        authorized_scope = []
    if not set(scope).issubset(set(authorized_scope)):
        blockers.append("IMPLEMENTATION_SCOPE_EXCEEDS_TRANSACTION_BOUNDARY")

    prerequisites = transaction.get("prerequisites")
    if not isinstance(prerequisites, dict) or not prerequisites or not all(
        value is True for value in prerequisites.values()
    ):
        blockers.append("PREREQUISITES_NOT_SATISFIED")

    qualification = transaction.get("qualification")
    if not isinstance(qualification, dict) or not (
        qualification.get("valid") is True or qualification.get("required") is True
    ):
        blockers.append("QUALIFICATION_ARTIFACT_INVALID_OR_MISSING")

    declared_blockers = transaction.get("blockers")
    if not isinstance(declared_blockers, list):
        blockers.append("BLOCKER_LIST_INVALID")
    elif declared_blockers:
        blockers.extend("EXPLICIT_BLOCKER:" + str(item) for item in declared_blockers)

    authority = transaction.get("authority")
    if not isinstance(authority, dict) or authority.get("bounded_implementation") is not True:
        blockers.append("BOUNDED_IMPLEMENTATION_AUTHORITY_ABSENT")
    if isinstance(authority, dict) and authority.get("publication_owner") != "ZEUS":
        blockers.append("PUBLICATION_AUTHORITY_MUST_BE_ZEUS")

    if transaction.get("successor_gate_execution_requested") is not False:
        blockers.append("SUCCESSOR_GATE_EXECUTION_NOT_AUTHORIZED")
    if transaction.get("publication_requested") is not False:
        blockers.append("PUBLICATION_NOT_AUTHORIZED_IN_IMPLEMENTATION_TRANSACTION")

    roadmap_executable = (
        resolved["state"].get("executable_qualification", {}).get("executable") is True
    )
    if not roadmap_executable:
        blockers.append("CANONICAL_ROADMAP_NOT_EXECUTABLE")

    authorized = not blockers
    return {
        "result": "PASS",
        "projection": "ZEUS_BOUNDED_IMPLEMENTATION_AUTHORITY",
        "transaction_recognized": not any(
            item.startswith(("MISSING_TRANSACTION_FIELDS", "TRANSACTION_ID_REQUIRED"))
            for item in blockers
        ),
        "transaction_id": transaction_id,
        "gate_id": gate_id,
        "roadmap_executable": roadmap_executable,
        "bounded_implementation_authorized": authorized,
        "authorized_scope": list(authorized_scope),
        "resolved_scope": list(scope),
        "qualification_required": True,
        "publication_authority_owner": "ZEUS",
        "codex_publication_authority": False,
        "successor_gate_execution_authorized": False,
        "blockers": blockers,
        "next_authorized_action": (
            "EXECUTE_BOUNDED_IMPLEMENTATION_INCREMENT"
            if authorized else "RESOLVE_BOUNDED_IMPLEMENTATION_SCOPE"
        ),
        "read_only": True,
    }


def project_c06_bounded_implementation_authority(
    repository_root: Path | str,
    transaction: dict[str, Any] | None = None,
    *,
    transaction_id: str = "C06-WOP-01-ROADMAP-AUTHORITY-001",
) -> dict[str, Any]:
    """Resolve the C06 transaction through the generic resolver and C06 policy."""
    repository_root = Path(repository_root).resolve()
    if transaction is None:
        transaction = _load_bounded_implementation_transaction(
            repository_root, transaction_id
        )
    result = project_bounded_implementation_authority(
        repository_root,
        transaction=transaction,
        policy={
            "required_gate_id": "C06",
            "provenance_reference": (
                "C06-BOUNDED-IMPLEMENTATION-CONTROLLED-AUTHORITY-AND-FIRST-INCREMENT-001"
            ),
        },
    )
    result["projection"] = "ZEUS_C06_BOUNDED_IMPLEMENTATION_AUTHORITY"
    return result


def _load_bounded_implementation_transaction(
    repository_root: Path,
    transaction_id: str,
) -> dict[str, Any]:
    """Load and integrity-check the single C06 persisted transaction record."""
    path = repository_root / ROADMAP_RELATIVE_ROOT / (
        "gates/C06-wop-and-execution-contract/evidence/"
        "C06-BOUNDED-IMPLEMENTATION-TRANSACTION-001.yaml"
    )
    value = _load_yaml(path, "C06 bounded implementation transaction")
    schema_path = repository_root / ROADMAP_RELATIVE_ROOT / (
        "schemas/bounded-implementation-transaction.schema.yaml"
    )
    _schema_validate(value, schema_path, "C06 bounded implementation transaction")
    if value.get("transaction_id") != transaction_id:
        raise RoadmapError("bounded implementation transaction is unknown")
    expected = _sha256_canonical_mapping(
        {key: item for key, item in value.items() if key != "transaction_digest"}
    )
    if value.get("transaction_digest") != expected:
        raise RoadmapError("bounded implementation transaction digest mismatch")
    return value


def _sha256_canonical_mapping(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


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
                result = _load_yaml(result_path, f"{gate_id} result")

                _reject_runtime_identifiers(
                    result,
                    f"result.{gate_id}",
                )

                if result.get("gate_id") != gate_id:
                    raise RoadmapError(
                        f"{gate_id} result identity mismatch"
                    )

                result_value = result.get("result")

                result_class = classify_result(
                    ResultFacts(
                        exists=True,
                        identity_valid=True,
                        schema_valid=(
                            isinstance(result_value, str)
                            and bool(result_value)
                        ),
                        evidence_valid=(
                            isinstance(result.get("evidence"), list)
                            and bool(result["evidence"])
                            and all(
                                isinstance(item, dict)
                                and bool(item.get("path"))
                                for item in result["evidence"]
                            )
                        ),
                        final=(
                            result_value in TERMINAL_RESULTS
                        ),
                    )
                )

                if result_class is not ResultClass.VALID_FINAL:
                    raise RoadmapError(
                        f"{gate_id} current result is not "
                        f"reviewable: {result_class.value}"
                    )

                try:
                    recorded_state = result_recorded_transition(
                        LifecycleState.CURRENT,
                        result_class,
                    )

                    review_state = pending_review_transition(
                        recorded_state,
                        result_class,
                    )
                except LifecycleError as exc:
                    raise RoadmapError(str(exc)) from exc

                if review_state is not                         LifecycleState.AWAITING_OPERATOR_REVIEW:
                    raise RoadmapError(
                        f"{gate_id} failed to derive "
                        "AWAITING_OPERATOR_REVIEW"
                    )

                results[gate_id] = result

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

        # The frozen gate resume instruction describes the execution-time
        # action for a CURRENT gate that has not yet produced a result.
        #
        # Once validation has accepted a terminal result for the current
        # gate, the lifecycle is RESULT_RECORDED /
        # AWAITING_OPERATOR_REVIEW.  At that point the execution-time
        # resume instruction is no longer the applicable next-action
        # invariant.  CR16 validates that lifecycle condition read-only;
        # later lifecycle/CLI gates own review-action projection and
        # mutating operator decisions.
        if current not in results:
            if (
                state["next_authorized_action"]
                != current_gate["resume_instructions"][
                    "next_authorized_action"
                ]
            ):
                raise RoadmapError(
                    "state and current gate next authorized action disagree"
                )
        elif not isinstance(
            state.get("next_authorized_action"),
            str,
        ) or not state["next_authorized_action"].strip():
            raise RoadmapError(
                "pending-review state requires a durable "
                "next authorized action"
            )

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

        current_result = resolved["results"].get(
            resolved["state"]["current_gate"]
        )

        lifecycle_state = (
            "AWAITING_OPERATOR_REVIEW"
            if current_result is not None
            else "CURRENT"
        )

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
            "lifecycle_state": lifecycle_state,
            "next_authorized_action": _canonical_next_authorized_action(
                self.repository_root,
                resolved["state"]["next_authorized_action"],
            ),
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
        current_result = resolved["results"].get(state["current_gate"])

        if current_result is None:
            lifecycle_state = "CURRENT"
            execution_result_state = "ABSENT"
            review_required = False
            review_state = "NOT_REQUIRED"
            operator_decision = "NONE"
            completion_state = "INCOMPLETE"
        else:
            gate_definition_path = _safe_repository_path(
                self.repository_root,
                next(
                    item["definition"]
                    for item in roadmap["gates"]
                    if item["gate_id"] == state["current_gate"]
                ),
                "current gate definition",
            )

            result_path = _safe_repository_path(
                self.repository_root,
                gate["result_location"],
                "current gate result",
            )

            receipt = _resolve_operator_review_receipt(
                self.repository_root,
                roadmap_id=roadmap["roadmap_id"],
                roadmap_version=str(roadmap["roadmap_version"]),
                gate_id=state["current_gate"],
                gate_definition_path=gate_definition_path,
                result_path=result_path,
            )

            execution_result_state = "VALID_FINAL"
            completion_state = "INCOMPLETE"

            if receipt is None:
                lifecycle_state = "AWAITING_OPERATOR_REVIEW"
                review_required = True
                review_state = "AWAITING_OPERATOR_REVIEW"
                operator_decision = "NONE"
            else:
                operator_decision = receipt["decision"]
                lifecycle_state = (
                    "ACCEPTED"
                    if operator_decision == "ACCEPT"
                    else "REJECTED"
                )
                review_required = False
                review_state = lifecycle_state

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
            "lifecycle_state": lifecycle_state,
            "execution_result_state": execution_result_state,
            "review_required": review_required,
            "review_state": review_state,
            "operator_decision": operator_decision,
            "completion_state": completion_state,
            "last_completed_gate": state["last_completed_gate"],
            "completed_gates": state["completed_gates"],
            "blocked_gates": state["blocked_gates"],
            "pending_gates": state["pending_gates"],
            "next_authorized_action": _canonical_next_authorized_action(
                self.repository_root,
                state["next_authorized_action"],
            ),
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


def _active_gate_projection_context(
    repository_root: Path | str,
) -> dict[str, Any]:
    """Resolve the minimum canonical authority needed by CR47 projections."""
    repository_root = Path(repository_root).resolve()
    roadmap_root = repository_root / ROADMAP_RELATIVE_ROOT
    roadmap = _load_yaml(roadmap_root / ROADMAP_FILE, "roadmap definition")
    state = _load_yaml(roadmap_root / STATE_FILE, "roadmap state")
    gate_id = state.get("current_gate")
    if not isinstance(gate_id, str) or not gate_id:
        raise RoadmapError("active gate authority is missing")
    references = [
        item for item in roadmap.get("gates", [])
        if isinstance(item, dict) and item.get("gate_id") == gate_id
    ]
    if len(references) != 1:
        raise RoadmapError("active gate authority cannot be uniquely resolved")
    reference = references[0]
    definition_path = _safe_repository_path(
        repository_root, reference.get("definition"), "active gate definition",
    )
    gate = _load_yaml(definition_path, "active gate definition")
    if gate.get("gate_id") != gate_id:
        raise RoadmapError("active gate definition identity mismatch")
    if gate.get("result_location") != reference.get("result"):
        raise RoadmapError("active gate result authority is ambiguous")
    result_path = _safe_repository_path(
        repository_root, gate.get("result_location"), "active gate result",
    )
    return {
        "repository_root": repository_root,
        "roadmap_root": roadmap_root,
        "roadmap": roadmap,
        "state": state,
        "gate_id": gate_id,
        "reference": reference,
        "gate": gate,
        "definition_path": definition_path,
        "result_path": result_path,
    }


def project_authority_surface_contract(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    field: str = "result_location",
) -> dict[str, Any]:
    """Identify which canonical surface owns an active-gate field."""
    context = _active_gate_projection_context(repository_root)
    owners = {
        "current_gate": (context["roadmap_root"] / STATE_FILE, "ROADMAP_STATE"),
        "result_location": (context["definition_path"], "GATE_DEFINITION"),
        "evidence_location": (context["definition_path"], "GATE_DEFINITION"),
        "next_gate": (context["definition_path"], "GATE_DEFINITION"),
        "status": (context["definition_path"], "GATE_DEFINITION"),
    }
    if field not in owners:
        raise RoadmapError(f"no canonical authority surface for field: {field}")
    source, kind = owners[field]
    value = (
        context["state"][field]
        if field == "current_gate"
        else context["gate"].get(field)
    )
    if value is None:
        raise RoadmapError(f"canonical authority field is missing: {field}")
    return {
        "result": "PASS",
        "projection": "AUTHORITY_SURFACE_CONTRACT",
        "gate_id": context["gate_id"],
        "field": field,
        "value": value,
        "authority_surface": str(source),
        "authority_kind": kind,
        "roadmap_reference_role": "LOCATOR_PROVENANCE",
        "ownership": "AUTHORITATIVE",
        "read_only": True,
    }


def project_result_authority_identity(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    result_path: Path | str | None = None,
) -> dict[str, Any]:
    """Project the canonical active-gate/result identity relationship."""
    context = _active_gate_projection_context(repository_root)
    path = context["result_path"] if result_path is None else Path(result_path)
    if not path.is_absolute():
        path = _safe_repository_path(
            context["repository_root"], str(path), "inspected result",
        )
    else:
        path = path.resolve()
        if context["repository_root"] not in path.parents:
            raise RoadmapError("inspected result escapes repository root")
    declared_gate = None
    if path.is_file():
        declared_gate = _load_yaml(path, "inspected result").get("gate_id")
        if not isinstance(declared_gate, str) or not declared_gate:
            raise RoadmapError("result-declared gate identity is missing")
    return {
        "result": "PASS",
        "projection": "RESULT_AUTHORITY_IDENTITY",
        "active_gate_id": context["gate_id"],
        "result_declared_gate_id": declared_gate,
        "identity_state": (
            "RESULT_ABSENT" if declared_gate is None else
            "MATCH" if declared_gate == context["gate_id"] else "MISMATCH"
        ),
        "identity_matches": (
            None if declared_gate is None else declared_gate == context["gate_id"]
        ),
        "canonical_result_path": str(context["result_path"]),
        "inspected_result_path": str(path),
        "authority_surface": str(context["definition_path"]),
        "authority_kind": "GATE_DEFINITION",
        "read_only": True,
    }


def project_result_lifecycle_diagnostic(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    result_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return a bounded canonical lifecycle diagnostic for the active gate."""
    context = _active_gate_projection_context(repository_root)
    identity = project_result_authority_identity(
        repository_root, result_path=result_path,
    )
    path = Path(identity["inspected_result_path"])
    value = _load_yaml(path, "inspected result") if path.is_file() else {}
    declared_digest = value.get("starting_state", {}).get("gate_contract_sha256")
    stale = (
        isinstance(declared_digest, str)
        and declared_digest != _sha256(context["definition_path"])
    )
    facts = ResultFacts(
        exists=path.is_file(),
        identity_valid=identity["identity_state"] == "MATCH",
        schema_valid=isinstance(value.get("result"), str) and bool(value.get("result")),
        evidence_valid=(
            isinstance(value.get("evidence"), list)
            and bool(value.get("evidence"))
            and all(isinstance(item, dict) and bool(item.get("path")) for item in value["evidence"])
        ),
        final=value.get("result") in TERMINAL_RESULTS,
        stale=stale,
    )
    result_class = classify_result(facts)
    classification = (
        "WRONG_GATE_RESULT" if result_class is ResultClass.INVALID
        and identity["identity_state"] == "MISMATCH" else result_class.value
    )
    actions = {
        "ABSENT": context["state"].get("next_authorized_action"),
        "WRONG_GATE_RESULT": "REMOVE_OR_REPLACE_WRONG_GATE_RESULT",
        "STALE": "REGENERATE_RESULT_AGAINST_CURRENT_GATE_AUTHORITY",
        "INVALID": "CORRECT_RESULT_TO_CANONICAL_CONTRACT",
        "NONFINAL": "COMPLETE_ACTIVE_GATE_RESULT",
        "VALID_FINAL": "REQUEST_OPERATOR_REVIEW",
        "CONFLICTING": "RESOLVE_CONFLICTING_RESULT_AUTHORITY",
    }
    return {
        "result": "PASS",
        "projection": "RESULT_LIFECYCLE_DIAGNOSTIC",
        "active_gate_id": context["gate_id"],
        "classification": classification,
        "canonical_result_class": result_class.value,
        "blocking_dependency": None if classification == "VALID_FINAL" else "ACTIVE_GATE_RESULT",
        "recommended_action": actions[classification],
        "identity": identity,
        "stale_authority": (
            None if not stale else {
                "declared_gate_definition_digest": declared_digest,
                "current_gate_definition_digest": _sha256(context["definition_path"]),
            }
        ),
        "diagnostic_scope": "ACTIVE_GATE_ONLY",
        "read_only": True,
        "state_advanced": False,
        "successor_executed": False,
    }


def project_acceptance_target_authority(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    target_gate_id: str | None = None,
) -> dict[str, Any]:
    """Project whether an acceptance request targets the active gate."""
    context = _active_gate_projection_context(repository_root)
    target = context["gate_id"] if target_gate_id is None else target_gate_id
    if not isinstance(target, str) or not target:
        raise RoadmapError("acceptance target identity is missing")
    matches = target == context["gate_id"]
    return {
        "result": "PASS",
        "projection": "ACCEPTANCE_TARGET_AUTHORITY",
        "active_gate_id": context["gate_id"],
        "target_gate_id": target,
        "target_matches_active_gate": matches,
        "classification": "AUTHORIZED_TARGET" if matches else "WRONG_CURRENT_GATE",
        "authority_surface": str(context["roadmap_root"] / STATE_FILE),
        "authority_kind": "ROADMAP_STATE",
        "read_only": True,
    }


def project_acceptance_prerequisites(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    target_gate_id: str | None = None,
    result_path: Path | str | None = None,
) -> dict[str, Any]:
    """Project canonical preconditions without creating acceptance authority."""
    context = _active_gate_projection_context(repository_root)
    target = project_acceptance_target_authority(
        repository_root, target_gate_id=target_gate_id,
    )
    diagnostic = project_result_lifecycle_diagnostic(
        repository_root, result_path=result_path,
    )
    transition_valid = False
    if diagnostic["canonical_result_class"] == ResultClass.VALID_FINAL.value:
        try:
            recorded = result_recorded_transition(LifecycleState.CURRENT, ResultClass.VALID_FINAL)
            transition_valid = pending_review_transition(recorded, ResultClass.VALID_FINAL) is LifecycleState.AWAITING_OPERATOR_REVIEW
        except LifecycleError:
            transition_valid = False
    checks = [
        {"prerequisite": "TARGET_IS_ACTIVE_GATE", "satisfied": target["target_matches_active_gate"]},
        {"prerequisite": "RESULT_IS_VALID_FINAL", "satisfied": diagnostic["classification"] == "VALID_FINAL"},
        {"prerequisite": "AWAITING_OPERATOR_REVIEW", "satisfied": transition_valid},
    ]
    missing = [item["prerequisite"] for item in checks if not item["satisfied"]]
    return {
        "result": "PASS",
        "projection": "ACCEPTANCE_PREREQUISITES",
        "target_gate_id": target["target_gate_id"],
        "prerequisites": checks,
        "missing_prerequisites": missing,
        "all_satisfied": not missing,
        "acceptance_receipt_created": False,
        "read_only": True,
    }


def project_acceptance_readiness(
    repository_root: Path | str = DEFAULT_REPOSITORY_ROOT,
    *,
    target_gate_id: str | None = None,
    result_path: Path | str | None = None,
) -> dict[str, Any]:
    """Compose acceptance boundary and prerequisite projections."""
    prerequisites = project_acceptance_prerequisites(
        repository_root,
        target_gate_id=target_gate_id,
        result_path=result_path,
    )
    blockers = list(prerequisites["missing_prerequisites"])
    return {
        "result": "PASS",
        "projection": "ACCEPTANCE_READINESS",
        "target_gate_id": prerequisites["target_gate_id"],
        "ready": not blockers,
        "classification": "READY_FOR_EXPLICIT_ACCEPTANCE" if not blockers else "NOT_READY",
        "blockers": blockers,
        "next_authorized_action": (
            "REQUEST_EXPLICIT_OPERATOR_ACCEPTANCE" if not blockers
            else project_result_lifecycle_diagnostic(
                repository_root, result_path=result_path,
            )["recommended_action"]
        ),
        "prerequisites": prerequisites,
        "acceptance_executed": False,
        "acceptance_receipt_created": False,
        "state_advanced": False,
        "successor_executed": False,
        "read_only": True,
    }






def inspect_emm_binding_scope(
    repository_root: Path | str,
    *,
    source_path: str,
) -> dict[str, Any]:
    """Return read-only EMM binding and drift status for one path."""

    repository_root = Path(repository_root).resolve()

    if (
        not isinstance(source_path, str)
        or not source_path.strip()
    ):
        raise RoadmapError("missing EMM source path")

    candidate = _safe_repository_path(
        repository_root,
        source_path,
        "EMM inspection source",
    )

    roadmap_root = (
        repository_root
        / ROADMAP_RELATIVE_ROOT
    )

    manifest_path = roadmap_root / MANIFEST_FILE

    manifest = _load_yaml(
        manifest_path,
        "EMM binding manifest",
    )

    sources = manifest.get("sources")

    if not isinstance(sources, list):
        raise RoadmapError(
            "EMM binding manifest sources are malformed"
        )

    matches = [
        entry
        for entry in sources
        if (
            isinstance(entry, dict)
            and entry.get("path") == source_path
        )
    ]

    if len(matches) > 1:
        raise RoadmapError(
            "duplicate EMM binding source: "
            + source_path
        )

    source_exists = candidate.is_file()

    if not matches:
        return {
            "result": "PASS",
            "classification": "UNBOUND_BY_POLICY",
            "source_path": source_path,
            "bound": False,
            "source_exists": source_exists,
            "expected_sha256": None,
            "actual_sha256": (
                _sha256(candidate)
                if source_exists
                else None
            ),
            "drifted": False,
            "rebind_eligible": False,
            "read_only": True,
        }

    entry = matches[0]

    if set(entry) != {"path", "sha256"}:
        raise RoadmapError(
            "EMM binding entry is malformed"
        )

    expected = entry["sha256"]

    if not source_exists:
        return {
            "result": "PASS",
            "classification": "MISSING_SOURCE",
            "source_path": source_path,
            "bound": True,
            "source_exists": False,
            "expected_sha256": expected,
            "actual_sha256": None,
            "drifted": False,
            "rebind_eligible": False,
            "read_only": True,
        }

    actual = _sha256(candidate)

    drifted = actual != expected

    return {
        "result": "PASS",
        "classification": (
            "BOUND_DRIFTED"
            if drifted
            else "BOUND_CLEAN"
        ),
        "source_path": source_path,
        "bound": True,
        "source_exists": True,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "drifted": drifted,
        "rebind_eligible": drifted,
        "read_only": True,
    }









def project_composite_execution_preflight(
    repository_root: Path | str,
    *,
    parent_gate_id: str,
    corrective_root_path: str,
    manual_gate_id: str,
    manual_contract_path: str,
    source_path: str,
    temporary_workspace: str | None = None,
) -> dict[str, Any]:
    """Compose qualified Zeus projections without re-deriving authority."""

    repository_root = Path(repository_root).resolve()

    successor = project_successor_action_contract(
        repository_root,
        gate_id=parent_gate_id,
    )

    maturity = project_executable_roadmap_maturity(
        repository_root,
        gate_id=parent_gate_id,
    )

    emm_scope = inspect_emm_binding_scope(
        repository_root,
        source_path=source_path,
    )

    emm_awareness = project_emm_reconciliation_awareness(
        repository_root,
        source_path=source_path,
    )

    resource = project_qualification_resource_preflight(
        repository_root,
        temporary_workspace=temporary_workspace,
        fixture_copy_multiplier=8,
        minimum_extra_bytes=2 * 1024**3,
    )

    nested = project_nested_corrective_reconciliation(
        repository_root,
        parent_gate_id=parent_gate_id,
        corrective_root_path=corrective_root_path,
        manual_gate_id=manual_gate_id,
        manual_contract_path=manual_contract_path,
    )

    manual = project_manual_gate_execution_preflight(
        repository_root,
        parent_gate_id=parent_gate_id,
        manual_gate_id=manual_gate_id,
        manual_contract_path=manual_contract_path,
        temporary_workspace=temporary_workspace,
    )

    components = {
        "ZO-005": emm_awareness,
        "ZO-006": maturity,
        "ZO-007": manual,
        "ZO-008": nested,
        "ZO-009": successor,
        "ZO-010": emm_scope,
        "ZO-011": resource,
    }

    blockers = []

    if emm_scope.get("classification") == "MISSING_SOURCE":
        blockers.append({
            "dependency": "ZO-010",
            "classification":
                emm_scope.get("classification"),
        })

    if emm_awareness.get("reconciliation_required") is True:
        blockers.append({
            "dependency": "ZO-005",
            "classification":
                emm_awareness.get("classification"),
        })

    if resource.get("classification") != "READY":
        blockers.append({
            "dependency": "ZO-011",
            "classification":
                resource.get("classification"),
        })

    if nested.get("consistent") is not True:
        blockers.append({
            "dependency": "ZO-008",
            "classification":
                nested.get("classification"),
        })

    if maturity.get("classification") != "CURRENT_EXECUTABLE":
        blockers.append({
            "dependency": "ZO-006",
            "classification":
                maturity.get("classification"),
        })

    if manual.get("ready") is not True:
        blockers.append({
            "dependency": "ZO-007",
            "classification":
                manual.get("classification"),
        })

    if (
        successor.get("classification")
        != "EXECUTABLE_SUCCESSOR_ACTION_RESOLVED"
    ):
        blockers.append({
            "dependency": "ZO-009",
            "classification":
                successor.get("classification"),
        })

    if blockers:
        first = blockers[0]

        classification = "BLOCKED"
        ready = False
        blocking_dependency = first["dependency"]
        blocking_classification = first["classification"]
        recommended_action = (
            "RESOLVE_" + blocking_dependency.replace("-", "_")
        )

    else:
        classification = "READY"
        ready = True
        blocking_dependency = None
        blocking_classification = None
        recommended_action = (
            manual.get("classification")
        )

    return {
        "result": "PASS",
        "projection":
            "ZEUS_COMPOSITE_EXECUTION_PREFLIGHT",
        "classification":
            classification,
        "ready":
            ready,
        "blocking_dependency":
            blocking_dependency,
        "blocking_classification":
            blocking_classification,
        "blocking_dependencies":
            blockers,
        "component_order": [
            "ZO-010",
            "ZO-005",
            "ZO-011",
            "ZO-008",
            "ZO-006",
            "ZO-007",
            "ZO-009",
        ],
        "components":
            components,
        "parent_gate_id":
            parent_gate_id,
        "manual_gate_id":
            manual_gate_id,
        "nested_current_item":
            nested.get("nested_current_item"),
        "next_nested_item":
            nested.get("next_item"),
        "successor_gate":
            successor.get("successor_gate"),
        "next_authorized_action":
            successor.get("next_authorized_action"),
        "recommended_action":
            recommended_action,
        "execution_performed":
            False,
        "state_advanced":
            False,
        "parent_gate_advanced":
            False,
        "successor_executed":
            False,
        "automatic_reconciliation":
            False,
        "read_only":
            True,
    }


def project_nested_corrective_reconciliation(
    repository_root: Path | str,
    *,
    parent_gate_id: str,
    corrective_root_path: str,
    manual_gate_id: str,
    manual_contract_path: str,
) -> dict[str, Any]:
    """Project consistency between parent and nested corrective state."""

    repository_root = Path(repository_root).resolve()

    if not isinstance(parent_gate_id, str) or not parent_gate_id.strip():
        raise RoadmapError("missing parent_gate_id")

    if not isinstance(corrective_root_path, str) or not corrective_root_path.strip():
        raise RoadmapError("missing corrective_root_path")

    if not isinstance(manual_gate_id, str) or not manual_gate_id.strip():
        raise RoadmapError("missing manual_gate_id")

    if not isinstance(manual_contract_path, str) or not manual_contract_path.strip():
        raise RoadmapError("missing manual_contract_path")

    resolver = ConvergenceRoadmap(repository_root)

    validated = resolver.validate()

    parent_state = validated.get("state")

    if not isinstance(parent_state, dict):
        raise RoadmapError(
            "validated parent roadmap state unavailable"
        )

    parent_current_gate = parent_state.get(
        "current_gate"
    )

    if parent_current_gate != parent_gate_id:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
            "classification":
                "PARENT_GATE_MISMATCH",
            "consistent": False,
            "blocking_dependency":
                "PARENT_ROADMAP_STATE",
            "parent_gate_id":
                parent_gate_id,
            "parent_current_gate":
                parent_current_gate,
            "nested_current_item":
                None,
            "execution_performed":
                False,
            "state_advanced":
                False,
            "parent_gate_advanced":
                False,
            "successor_executed":
                False,
            "read_only":
                True,
        }

    corrective_root = _safe_repository_path(
        repository_root,
        corrective_root_path,
        "corrective root",
    )

    corrective_state_path = (
        corrective_root
        / "STATE.yaml"
    )

    corrective_roadmap_path = (
        corrective_root
        / "ROADMAP.yaml"
    )

    if not corrective_state_path.is_file():
        raise RoadmapError(
            "nested corrective STATE.yaml missing"
        )

    if not corrective_roadmap_path.is_file():
        raise RoadmapError(
            "nested corrective ROADMAP.yaml missing"
        )

    corrective_state = _load_yaml(
        corrective_state_path,
        "nested corrective state",
    )

    corrective_roadmap = _load_yaml(
        corrective_roadmap_path,
        "nested corrective roadmap",
    )

    corrective_roadmap_id = corrective_roadmap.get(
        "roadmap_id"
    )

    if not corrective_roadmap_id:
        raise RoadmapError(
            "nested corrective roadmap identity missing"
        )

    manual_contract_abs = _safe_repository_path(
        repository_root,
        manual_contract_path,
        "manual execution contract",
    )

    manual_contract = _load_yaml(
        manual_contract_abs,
        "manual execution contract",
    )

    if manual_contract.get("gate_id") != manual_gate_id:
        raise RoadmapError(
            "manual gate identity mismatch"
        )

    authority = manual_contract.get(
        "authority"
    )

    if not isinstance(authority, dict):
        raise RoadmapError(
            "manual execution authority missing"
        )

    required_parent = authority.get(
        "parent_gate"
    )

    if required_parent != parent_gate_id:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
            "classification":
                "NESTED_PARENT_AUTHORITY_MISMATCH",
            "consistent": False,
            "blocking_dependency":
                "MANUAL_CONTRACT_AUTHORITY",
            "parent_gate_id":
                parent_gate_id,
            "manual_parent_gate":
                required_parent,
            "nested_current_item":
                corrective_state.get("current_item"),
            "execution_performed":
                False,
            "state_advanced":
                False,
            "parent_gate_advanced":
                False,
            "successor_executed":
                False,
            "read_only":
                True,
        }

    required_current_item = authority.get(
        "current_item_required"
    )

    current_item = corrective_state.get(
        "current_item"
    )

    if current_item != required_current_item:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
            "classification":
                "NESTED_CURRENT_ITEM_MISMATCH",
            "consistent": False,
            "blocking_dependency":
                "NESTED_CORRECTIVE_STATE",
            "parent_gate_id":
                parent_gate_id,
            "parent_current_gate":
                parent_current_gate,
            "nested_current_item":
                current_item,
            "required_current_item":
                required_current_item,
            "execution_performed":
                False,
            "state_advanced":
                False,
            "parent_gate_advanced":
                False,
            "successor_executed":
                False,
            "read_only":
                True,
        }

    dependency_gate = authority.get(
        "dependency_required"
    )

    if not isinstance(dependency_gate, str) or not dependency_gate.strip():
        raise RoadmapError(
            "nested dependency authority missing"
        )

    dependency_result_path = (
        corrective_root
        / "gates"
        / dependency_gate
        / "RESULT.yaml"
    )

    if not dependency_result_path.is_file():
        return {
            "result": "PASS",
            "projection":
                "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
            "classification":
                "NESTED_DEPENDENCY_NOT_COMPLETE",
            "consistent": False,
            "blocking_dependency":
                "NESTED_DEPENDENCY_RESULT",
            "dependency_gate":
                dependency_gate,
            "dependency_result":
                "MISSING",
            "nested_current_item":
                current_item,
            "execution_performed":
                False,
            "state_advanced":
                False,
            "parent_gate_advanced":
                False,
            "successor_executed":
                False,
            "read_only":
                True,
        }

    dependency_result = _load_yaml(
        dependency_result_path,
        "nested dependency result",
    )

    dependency_complete = (
        dependency_result.get("status") == "COMPLETE"
        and dependency_result.get("result") == "PASS"
    )

    if not dependency_complete:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
            "classification":
                "NESTED_DEPENDENCY_NOT_COMPLETE",
            "consistent": False,
            "blocking_dependency":
                "NESTED_DEPENDENCY_RESULT",
            "dependency_gate":
                dependency_gate,
            "dependency_result":
                "NOT_COMPLETE_PASS",
            "nested_current_item":
                current_item,
            "execution_performed":
                False,
            "state_advanced":
                False,
            "parent_gate_advanced":
                False,
            "successor_executed":
                False,
            "read_only":
                True,
        }

    next_item = authority.get(
        "next_item"
    )

    transition = manual_contract.get(
        "state_transition"
    )

    if not isinstance(transition, dict):
        raise RoadmapError(
            "manual state transition missing"
        )

    if transition.get("from") != current_item:
        raise RoadmapError(
            "nested transition source mismatch"
        )

    if transition.get("to") != next_item:
        raise RoadmapError(
            "nested transition target mismatch"
        )

    if transition.get("execute_successor") is not False:
        raise RoadmapError(
            "nested contract permits successor execution"
        )

    parent_result_path = (
        repository_root
        / "engineering/convergence/"
          "engineering-system-convergence"
        / "gates"
        / "C02-controlled-documentation-and-authority"
        / "RESULT.yaml"
    )

    parent_result = (
        _load_yaml(
            parent_result_path,
            "parent gate result",
        )
        if parent_result_path.is_file()
        else None
    )

    parent_completed = False

    if isinstance(parent_result, dict):
        parent_completed = (
            parent_result.get("status") == "COMPLETE"
            and parent_result.get("result") == "PASS"
        )

    # A nested corrective may be active under a parent gate that has
    # assessment/result evidence, but nested readiness must never be
    # interpreted as parent advancement.
    return {
        "result": "PASS",
        "projection":
            "ZEUS_NESTED_CORRECTIVE_RECONCILIATION",
        "classification":
            "NESTED_CORRECTIVE_CONSISTENT",
        "consistent": True,
        "blocking_dependency": None,
        "parent_gate_id":
            parent_gate_id,
        "parent_current_gate":
            parent_current_gate,
        "parent_result_present":
            parent_result is not None,
        "parent_result_complete_pass":
            parent_completed,
        "corrective_roadmap_id":
            corrective_roadmap_id,
        "corrective_root_path":
            corrective_root_path,
        "manual_gate_id":
            manual_gate_id,
        "manual_contract_path":
            manual_contract_path,
        "nested_current_item":
            current_item,
        "dependency_gate":
            dependency_gate,
        "dependency_result":
            "COMPLETE_PASS",
        "next_item":
            next_item,
        "state_transition":
            transition,
        "nested_ready_implies_parent_advance":
            False,
        "execution_performed":
            False,
        "state_advanced":
            False,
        "parent_gate_advanced":
            False,
        "successor_executed":
            False,
        "read_only":
            True,
    }


def project_manual_gate_execution_preflight(
    repository_root: Path | str,
    *,
    parent_gate_id: str,
    manual_gate_id: str,
    manual_contract_path: str,
    temporary_workspace: str | None = None,
) -> dict[str, Any]:
    """Project read-only readiness for one bounded manual gate."""

    repository_root = Path(repository_root).resolve()

    if not isinstance(parent_gate_id, str) or not parent_gate_id.strip():
        raise RoadmapError("missing parent_gate_id")

    if not isinstance(manual_gate_id, str) or not manual_gate_id.strip():
        raise RoadmapError("missing manual_gate_id")

    if not isinstance(manual_contract_path, str) or not manual_contract_path.strip():
        raise RoadmapError("missing manual_contract_path")

    maturity = project_executable_roadmap_maturity(
        repository_root,
        gate_id=parent_gate_id,
    )

    if maturity.get("classification") != "CURRENT_EXECUTABLE":
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "PARENT_NOT_EXECUTABLE",
            "ready": False,
            "blocking_dependency":
                "ZO-006",
            "blocking_classification":
                maturity.get("classification"),
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    contract_path = _safe_repository_path(
        repository_root,
        manual_contract_path,
        "manual execution contract",
    )

    contract = _load_yaml(
        contract_path,
        "manual execution contract",
    )

    if not isinstance(contract, dict):
        raise RoadmapError(
            "manual execution contract must be structured"
        )

    if contract.get("gate_id") != manual_gate_id:
        raise RoadmapError(
            "manual execution contract gate identity mismatch"
        )

    if contract.get("execution_mode") != "MANUAL_BOUNDED":
        raise RoadmapError(
            "manual execution contract is not MANUAL_BOUNDED"
        )

    authority = contract.get("authority")

    if not isinstance(authority, dict):
        raise RoadmapError(
            "manual execution authority is unavailable"
        )

    required_authority = {
        "gate_contract",
        "corrective_roadmap",
        "corrective_state",
        "parent_gate",
        "current_item_required",
        "dependency_required",
        "next_item",
    }

    missing_authority = sorted(
        key
        for key in required_authority
        if not authority.get(key)
    )

    if missing_authority:
        raise RoadmapError(
            "manual execution authority incomplete: "
            + ", ".join(missing_authority)
        )

    if authority["parent_gate"] != parent_gate_id:
        raise RoadmapError(
            "manual execution parent authority mismatch"
        )

    corrective_root = contract_path.parent.parent.parent

    state_path = (
        corrective_root
        / authority["corrective_state"]
    )

    corrective_state = _load_yaml(
        state_path,
        "corrective state",
    )

    current_item = corrective_state.get(
        "current_item"
    )

    required_current_item = authority[
        "current_item_required"
    ]

    if current_item != required_current_item:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "WRONG_CURRENT_ITEM",
            "ready": False,
            "blocking_dependency":
                "MANUAL_CONTRACT_STATE",
            "blocking_classification":
                "WRONG_CURRENT_ITEM",
            "current_item": current_item,
            "required_current_item":
                required_current_item,
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    dependency_id = authority[
        "dependency_required"
    ]

    dependency_result_path = (
        corrective_root
        / "gates"
        / dependency_id
        / "RESULT.yaml"
    )

    if not dependency_result_path.is_file():
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "DEPENDENCY_NOT_COMPLETE",
            "ready": False,
            "blocking_dependency":
                "MANUAL_GATE_DEPENDENCY",
            "blocking_classification":
                "RESULT_MISSING",
            "dependency_gate":
                dependency_id,
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    dependency_result = _load_yaml(
        dependency_result_path,
        "manual gate dependency result",
    )

    if not (
        dependency_result.get("status") == "COMPLETE"
        and dependency_result.get("result") == "PASS"
    ):
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "DEPENDENCY_NOT_COMPLETE",
            "ready": False,
            "blocking_dependency":
                "MANUAL_GATE_DEPENDENCY",
            "blocking_classification":
                "RESULT_NOT_COMPLETE_PASS",
            "dependency_gate":
                dependency_id,
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    emm = project_emm_reconciliation_awareness(
        repository_root,
        source_path="scripts/lib/eos/convergence_roadmap.py",
    )

    # Global EMM integrity must be checked separately from one source's
    # local binding scope.
    resolver = ConvergenceRoadmap(repository_root)
    resolver.validate()

    if emm.get("reconciliation_required") is True:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "EMM_RECONCILIATION_REQUIRED",
            "ready": False,
            "blocking_dependency":
                "ZO-005",
            "blocking_classification":
                emm.get("classification"),
            "emm_awareness": emm,
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    if temporary_workspace is None:
        temporary_workspace = str(
            repository_root.parent
            / "tmp/zeus-manual-preflight"
        )

    resource = project_qualification_resource_preflight(
        repository_root,
        temporary_workspace=temporary_workspace,
        fixture_copy_multiplier=8,
        minimum_extra_bytes=2 * 1024**3,
    )

    if resource.get("classification") != "READY":
        return {
            "result": "PASS",
            "projection":
                "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
            "classification":
                "RESOURCE_BLOCKED",
            "ready": False,
            "blocking_dependency":
                "ZO-011",
            "blocking_classification":
                resource.get("classification"),
            "resource_preflight": resource,
            "parent_maturity": maturity,
            "manual_gate_id": manual_gate_id,
            "manual_contract_path":
                manual_contract_path,
            "execution_performed": False,
            "state_advanced": False,
            "successor_executed": False,
            "read_only": True,
        }

    state_transition = contract.get(
        "state_transition"
    )

    if not isinstance(state_transition, dict):
        raise RoadmapError(
            "manual execution state transition missing"
        )

    if state_transition.get("from") != manual_gate_id:
        raise RoadmapError(
            "manual execution transition source mismatch"
        )

    if state_transition.get("execute_successor") is not False:
        raise RoadmapError(
            "manual execution contract must prohibit successor execution"
        )

    next_item = authority.get("next_item")

    if state_transition.get("to") != next_item:
        raise RoadmapError(
            "manual execution transition target mismatch"
        )

    return {
        "result": "PASS",
        "projection":
            "ZEUS_MANUAL_GATE_EXECUTION_PREFLIGHT",
        "classification":
            "READY_FOR_MANUAL_EXECUTION",
        "ready": True,
        "blocking_dependency": None,
        "blocking_classification": None,
        "parent_gate": parent_gate_id,
        "parent_maturity": maturity,
        "manual_gate_id": manual_gate_id,
        "manual_contract_path":
            manual_contract_path,
        "manual_contract_id":
            contract.get("contract_id"),
        "execution_mode":
            contract.get("execution_mode"),
        "current_item":
            current_item,
        "dependency_gate":
            dependency_id,
        "dependency_result":
            "COMPLETE_PASS",
        "emm_awareness": emm,
        "resource_preflight": resource,
        "next_item": next_item,
        "state_transition":
            state_transition,
        "execution_performed": False,
        "state_advanced": False,
        "successor_executed": False,
        "read_only": True,
    }


def project_executable_roadmap_maturity(
    repository_root: Path | str,
    *,
    gate_id: str,
) -> dict[str, Any]:
    """Project read-only executable maturity for one validated gate."""

    repository_root = Path(repository_root).resolve()

    resolver = ConvergenceRoadmap(repository_root)
    resolved = resolver.validate()

    state = resolved.get("state")

    if not isinstance(state, dict):
        raise RoadmapError(
            "validated roadmap state unavailable"
        )

    current_gate = state.get("current_gate")

    completed = set(
        state.get("completed_gates", [])
    )

    blocked = set(
        state.get("blocked_gates", [])
    )

    successor_projection = project_successor_action_contract(
        repository_root,
        gate_id=gate_id,
    )

    terminal = bool(
        successor_projection["terminal"]
    )

    is_current = gate_id == current_gate
    is_completed = gate_id in completed
    is_blocked = gate_id in blocked

    if is_blocked:
        classification = "BLOCKED"
        executable = False
        recommended_action = "RESOLVE_BLOCKERS"

    elif is_completed:
        classification = "COMPLETE"
        executable = False
        recommended_action = "NONE_GATE_COMPLETE"

    elif not is_current:
        classification = "NOT_CURRENT"
        executable = False
        recommended_action = "WAIT_FOR_GATE_ACTIVATION"

    elif terminal:
        classification = "TERMINAL_CURRENT"
        executable = False
        recommended_action = (
            successor_projection.get(
                "terminal_resume_action"
            )
            or "NONE_TERMINAL"
        )

    elif (
        successor_projection.get(
            "classification"
        )
        == "EXECUTABLE_SUCCESSOR_ACTION_RESOLVED"
    ):
        classification = "CURRENT_EXECUTABLE"
        executable = True
        recommended_action = (
            successor_projection[
                "next_authorized_action"
            ]
        )

    else:
        raise RoadmapError(
            "validated gate has unresolved maturity projection"
        )

    return {
        "result": "PASS",
        "projection":
            "ZEUS_EXECUTABLE_ROADMAP_MATURITY",
        "gate_id": gate_id,
        "current_gate": current_gate,
        "is_current": is_current,
        "is_completed": is_completed,
        "is_blocked": is_blocked,
        "terminal": terminal,
        "classification": classification,
        "executable": executable,
        "successor_gate":
            successor_projection.get(
                "successor_gate"
            ),
        "next_authorized_action":
            successor_projection.get(
                "next_authorized_action"
            ),
        "recommended_action":
            recommended_action,
        "authority_surface":
            successor_projection.get(
                "authority_surface"
            ),
        "authority_kind":
            successor_projection.get(
                "authority_kind"
            ),
        "action_surface":
            successor_projection.get(
                "action_surface"
            ),
        "successor_executed": False,
        "read_only": True,
    }


def project_successor_action_contract(
    repository_root: Path | str,
    *,
    gate_id: str,
) -> dict[str, Any]:
    """Project successor authority from a canonically valid roadmap."""

    repository_root = Path(repository_root).resolve()

    if not isinstance(gate_id, str) or not gate_id.strip():
        raise RoadmapError("missing gate_id")

    resolver = ConvergenceRoadmap(repository_root)

    # Structural/schema/lifecycle contract validity belongs to the
    # canonical resolver. ZO-009 never attempts to reinterpret an
    # invalid gate graph.
    resolver.validate()

    roadmap = _load_yaml(
        resolver.roadmap_path,
        "roadmap definition",
    )

    entries = [
        item
        for item in roadmap.get("gates", [])
        if (
            isinstance(item, dict)
            and item.get("gate_id") == gate_id
        )
    ]

    if len(entries) != 1:
        raise RoadmapError(
            "gate locator is not uniquely resolvable: "
            + gate_id
        )

    entry = entries[0]

    definition = entry.get("definition")

    if not isinstance(definition, str) or not definition.strip():
        raise RoadmapError(
            "gate definition locator unavailable"
        )

    gate_path = _safe_repository_path(
        repository_root,
        definition,
        "gate definition",
    )

    gate = _load_yaml(
        gate_path,
        "gate definition",
    )

    if gate.get("gate_id") != gate_id:
        raise RoadmapError(
            "gate definition identity mismatch"
        )

    successor = gate.get("next_gate")

    terminal_value = gate.get("terminal")

    # Historical/activation contracts do not necessarily expose the
    # version-2 terminal object. Canonical validation has already
    # established their next_gate legality.
    terminal = (
        isinstance(terminal_value, dict)
        and bool(terminal_value.get("is_terminal"))
    )

    resume = gate.get("resume_instructions") or {}

    if not isinstance(resume, dict):
        raise RoadmapError(
            "gate resume_instructions must be structured"
        )

    gate_resume_action = resume.get(
        "next_authorized_action"
    )

    if terminal:
        return {
            "result": "PASS",
            "projection":
                "ZEUS_SUCCESSOR_ACTION_CONTRACT",
            "authority_surface": definition,
            "authority_kind": "GATE_DEFINITION",
            "action_surface":
                "resume_instructions.next_authorized_action",
            "gate_id": gate_id,
            "terminal": True,
            "successor_gate": None,
            "next_authorized_action": None,
            "terminal_resume_action":
                gate_resume_action,
            "continuation_authority":
                terminal_value.get(
                    "continuation_authority"
                ),
            "continuation_action":
                terminal_value.get(
                    "continuation_action"
                ),
            "action_count": 0,
            "classification":
                "TERMINAL_NO_ROADMAP_SUCCESSOR",
            "executable_successor": False,
            "successor_executed": False,
            "read_only": True,
        }

    if not isinstance(successor, str) or not successor.strip():
        # This should normally be unreachable because canonical
        # validation owns this invariant, but preserve local
        # defensive failure.
        raise RoadmapError(
            "canonically valid nonterminal gate has no successor"
        )

    successor_entries = [
        item
        for item in roadmap.get("gates", [])
        if (
            isinstance(item, dict)
            and item.get("gate_id") == successor
        )
    ]

    if len(successor_entries) != 1:
        raise RoadmapError(
            "successor locator is not uniquely resolvable"
        )

    successor_definition = successor_entries[0].get(
        "definition"
    )

    if (
        not isinstance(successor_definition, str)
        or not successor_definition.strip()
    ):
        raise RoadmapError(
            "successor definition locator unavailable"
        )

    successor_path = _safe_repository_path(
        repository_root,
        successor_definition,
        "successor gate definition",
    )

    successor_gate = _load_yaml(
        successor_path,
        "successor gate definition",
    )

    if successor_gate.get("gate_id") != successor:
        raise RoadmapError(
            "successor gate identity mismatch"
        )

    successor_resume = successor_gate.get(
        "resume_instructions"
    )

    if not isinstance(successor_resume, dict):
        raise RoadmapError(
            "successor resume_instructions must be structured"
        )

    action = successor_resume.get(
        "next_authorized_action"
    )

    if not isinstance(action, str) or not action.strip():
        raise RoadmapError(
            "successor has no structured "
            "resume_instructions.next_authorized_action"
        )

    return {
        "result": "PASS",
        "projection":
            "ZEUS_SUCCESSOR_ACTION_CONTRACT",
        "authority_surface":
            successor_definition,
        "authority_kind":
            "GATE_DEFINITION",
        "action_surface":
            "resume_instructions.next_authorized_action",
        "gate_id": gate_id,
        "terminal": False,
        "successor_gate": successor,
        "next_authorized_action": action.strip(),
        "terminal_resume_action": None,
        "continuation_authority": None,
        "continuation_action": None,
        "action_count": 1,
        "classification":
            "EXECUTABLE_SUCCESSOR_ACTION_RESOLVED",
        "executable_successor": True,
        "successor_executed": False,
        "read_only": True,
    }


def project_qualification_resource_preflight(
    repository_root: Path | str,
    *,
    temporary_workspace: Path | str,
    fixture_copy_multiplier: int = 8,
    minimum_extra_bytes: int = 2 * 1024**3,
) -> dict[str, Any]:
    """Project read-only qualification resource readiness."""

    import shutil
    import subprocess

    repository_root = Path(repository_root).resolve()
    temporary_workspace = Path(temporary_workspace).resolve()

    if fixture_copy_multiplier < 1:
        raise RoadmapError(
            "fixture_copy_multiplier must be positive"
        )

    if minimum_extra_bytes < 0:
        raise RoadmapError(
            "minimum_extra_bytes cannot be negative"
        )

    if not repository_root.is_dir():
        raise RoadmapError(
            "qualification repository root is unavailable"
        )

    # The selected workspace itself need not exist yet.
    # Resource inspection uses the nearest existing parent.
    probe = temporary_workspace

    while not probe.exists():
        parent = probe.parent

        if parent == probe:
            raise RoadmapError(
                "qualification temporary filesystem cannot be resolved"
            )

        probe = parent

    if not probe.is_dir():
        raise RoadmapError(
            "qualification temporary filesystem probe is not a directory"
        )

    size = subprocess.run(
        [
            "du",
            "-sb",
            str(repository_root),
        ],
        capture_output=True,
        text=True,
    )

    if size.returncode != 0:
        raise RoadmapError(
            "qualification repository size inspection failed"
        )

    try:
        repository_bytes = int(
            size.stdout.split()[0]
        )
    except (IndexError, ValueError) as error:
        raise RoadmapError(
            "qualification repository size is invalid"
        ) from error

    usage = shutil.disk_usage(probe)

    required_reserve_bytes = max(
        repository_bytes * fixture_copy_multiplier,
        repository_bytes + minimum_extra_bytes,
    )

    ready = usage.free >= required_reserve_bytes

    return {
        "result": "PASS",
        "projection":
            "ZEUS_QUALIFICATION_RESOURCE_PREFLIGHT",
        "classification":
            "READY" if ready else "RESOURCE_BLOCKED",
        "resource":
            None if ready else "TEMPORARY_STORAGE",
        "repository_root": str(repository_root),
        "repository_bytes": repository_bytes,
        "temporary_workspace": str(temporary_workspace),
        "filesystem_probe": str(probe),
        "filesystem_total_bytes": usage.total,
        "filesystem_used_bytes": usage.used,
        "filesystem_free_bytes": usage.free,
        "fixture_copy_multiplier":
            fixture_copy_multiplier,
        "minimum_extra_bytes":
            minimum_extra_bytes,
        "required_reserve_bytes":
            required_reserve_bytes,
        "ready": ready,
        "semantic_test_failure": False,
        "qualification_executed": False,
        "recommended_action": (
            "USE_SELECTED_WORKSPACE"
            if ready
            else "SELECT_ALTERNATE_AUTHORIZED_WORKSPACE"
        ),
        "read_only": True,
    }


def project_emm_reconciliation_awareness(
    repository_root: Path,
    *,
    source_path: str,
) -> dict[str, Any]:
    """Project read-only Zeus EMM reconciliation awareness.

    This projection consumes canonical EMM binding-scope
    introspection. It never performs reconciliation.
    """

    inspection = inspect_emm_binding_scope(
        repository_root,
        source_path=source_path,
    )

    classification = inspection["classification"]

    action_map = {
        "BOUND_CLEAN": "NONE_REQUIRED",
        "BOUND_DRIFTED": "EMM_RECONCILIATION_REQUIRED",
        "MISSING_SOURCE": "FAIL_CLOSED_MISSING_SOURCE",
        "UNBOUND_BY_POLICY": "NONE_UNBOUND_BY_POLICY",
    }

    if classification not in action_map:
        raise RoadmapError(
            "unsupported EMM binding classification: "
            + str(classification)
        )

    reconciliation_required = (
        classification == "BOUND_DRIFTED"
    )

    return {
        "result": "PASS",
        "projection": "ZEUS_EMM_RECONCILIATION_AWARENESS",
        "source_path": inspection["source_path"],
        "classification": classification,
        "bound": inspection["bound"],
        "source_exists": inspection["source_exists"],
        "expected_sha256": inspection["expected_sha256"],
        "actual_sha256": inspection["actual_sha256"],
        "drifted": inspection["drifted"],
        "rebind_eligible": inspection["rebind_eligible"],
        "reconciliation_required":
            reconciliation_required,
        "recommended_action": action_map[classification],
        "canonical_reconciliation_primitive":
            "apply_emm_rebind_transaction",
        "automatic_reconciliation": False,
        "read_only": True,
    }


def apply_emm_rebind_transaction(
    repository_root: Path | str,
    *,
    authorized_mutations: dict[str, str],
    transaction_id: str,
) -> dict[str, Any]:
    """Atomically reconcile exactly authorized EMM source mutations."""

    import json
    import os
    from datetime import datetime, timezone

    repository_root = Path(repository_root).resolve()

    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise RoadmapError("missing transaction_id")

    if (
        not isinstance(authorized_mutations, dict)
        or not authorized_mutations
    ):
        raise RoadmapError("authorized mutation set must be non-empty")

    normalized: dict[str, str] = {}

    for relative, old_digest in authorized_mutations.items():
        path = _safe_repository_path(
            repository_root,
            relative,
            "authorized EMM mutation",
        )

        if not path.is_file():
            raise RoadmapError(
                f"authorized EMM source missing: {relative}"
            )

        if (
            not isinstance(old_digest, str)
            or len(old_digest) != 64
        ):
            raise RoadmapError(
                f"invalid authorized prior digest: {relative}"
            )

        normalized[relative] = old_digest

    roadmap_root = repository_root / ROADMAP_RELATIVE_ROOT
    manifest_path = roadmap_root / MANIFEST_FILE

    manifest = _load_yaml(
        manifest_path,
        "EMM binding manifest",
    )

    entries = manifest.get("sources")

    if not isinstance(entries, list) or not entries:
        raise RoadmapError("EMM binding manifest has no sources")

    by_path: dict[str, str] = {}

    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256"}
        ):
            raise RoadmapError(
                "EMM binding manifest source is malformed"
            )

        relative = entry["path"]
        digest = entry["sha256"]

        if relative in by_path:
            raise RoadmapError(
                f"duplicate EMM binding source: {relative}"
            )

        by_path[relative] = digest

    unknown = sorted(set(normalized) - set(by_path))

    if unknown:
        raise RoadmapError(
            "authorized mutation is not EMM-bound: "
            + ", ".join(unknown)
        )

    actual: dict[str, str] = {}
    drift: dict[str, tuple[str, str]] = {}

    for relative, expected in by_path.items():
        path = _safe_repository_path(
            repository_root,
            relative,
            "EMM binding source",
        )

        if not path.is_file():
            raise RoadmapError(
                f"EMM binding source missing: {relative}"
            )

        digest = _sha256(path)
        actual[relative] = digest

        if digest != expected:
            drift[relative] = (expected, digest)

    unauthorized = sorted(set(drift) - set(normalized))

    if unauthorized:
        raise RoadmapError(
            "unauthorized or unexplained EMM source drift: "
            + ", ".join(unauthorized)
        )

    for relative, prior in normalized.items():
        bound = by_path[relative]

        if bound != prior and bound != actual[relative]:
            raise RoadmapError(
                f"authorized prior digest mismatch: {relative}"
            )

    transaction_dir = (
        roadmap_root
        / "runtime/emm-rebind-transactions"
    )

    transaction_path = (
        transaction_dir
        / f"{transaction_id}.json"
    )

    requested_identity = {
        "transaction_type": "EMM_REBIND",
        "transaction_id": transaction_id,
        "authorized_mutations": dict(sorted(normalized.items())),
    }

    if transaction_path.is_file():
        try:
            committed = json.loads(
                transaction_path.read_text()
            )
        except (OSError, ValueError) as error:
            raise RoadmapError(
                "existing EMM transaction is malformed"
            ) from error

        for key, expected in requested_identity.items():
            if committed.get(key) != expected:
                raise RoadmapError(
                    "conflicting EMM transaction replay"
                )

        post_digest = committed.get(
            "post_manifest_sha256"
        )

        if (
            not isinstance(post_digest, str)
            or _sha256(manifest_path) != post_digest
        ):
            raise RoadmapError(
                "committed EMM transaction post-manifest mismatch"
            )

        for item in committed.get("sources", []):
            relative = item.get("path")
            new_digest = item.get("new_sha256")

            if (
                relative not in actual
                or actual[relative] != new_digest
            ):
                raise RoadmapError(
                    "committed EMM transaction source mismatch"
                )

        return {
            "result": "ALREADY_RECONCILED",
            "transaction_id": transaction_id,
            "post_manifest_sha256": post_digest,
            "sources": committed.get("sources", []),
        }

    if not drift:
        raise RoadmapError(
            "authorized mutation set contains no pending EMM drift"
        )

    missing_authorized_drift = sorted(
        relative
        for relative in normalized
        if relative not in drift
    )

    if missing_authorized_drift:
        raise RoadmapError(
            "authorized mutation set does not exactly match drift: "
            + ", ".join(missing_authorized_drift)
        )

    pre_manifest_bytes = manifest_path.read_bytes()
    pre_manifest_digest = hashlib.sha256(
        pre_manifest_bytes
    ).hexdigest()

    updated_sources = []

    source_records = []

    for entry in entries:
        relative = entry["path"]

        if relative in normalized:
            old_digest = entry["sha256"]
            new_digest = actual[relative]

            updated_sources.append(
                {
                    "path": relative,
                    "sha256": new_digest,
                }
            )

            source_records.append(
                {
                    "path": relative,
                    "old_sha256": old_digest,
                    "new_sha256": new_digest,
                }
            )
        else:
            updated_sources.append(dict(entry))

    updated_manifest = dict(manifest)
    updated_manifest["sources"] = updated_sources

    post_manifest_bytes = yaml.safe_dump(
        updated_manifest,
        sort_keys=False,
    ).encode("utf-8")

    post_manifest_digest = hashlib.sha256(
        post_manifest_bytes
    ).hexdigest()

    transaction_record = {
        "schema_version": 1,
        **requested_identity,
        "status": "PENDING_RECONCILIATION",
        "pre_manifest_sha256": pre_manifest_digest,
        "post_manifest_sha256": post_manifest_digest,
        "sources": source_records,
        "recorded_at": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
    }

    transaction_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    transaction_tmp = transaction_path.with_suffix(".tmp")
    manifest_tmp = manifest_path.with_suffix(".tmp")

    if transaction_tmp.exists():
        transaction_tmp.unlink()

    if manifest_tmp.exists():
        manifest_tmp.unlink()

    transaction_tmp.write_text(
        json.dumps(
            transaction_record,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    manifest_tmp.write_bytes(post_manifest_bytes)

    try:
        os.replace(manifest_tmp, manifest_path)

        transaction_record["status"] = "RECONCILIATION_COMPLETE"

        transaction_tmp.write_text(
            json.dumps(
                transaction_record,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        os.replace(
            transaction_tmp,
            transaction_path,
        )
    finally:
        if manifest_tmp.exists():
            manifest_tmp.unlink()

        if transaction_tmp.exists():
            transaction_tmp.unlink()

    if _sha256(manifest_path) != post_manifest_digest:
        raise RoadmapError(
            "EMM post-manifest identity mismatch"
        )

    for item in source_records:
        relative = item["path"]

        if _sha256(repository_root / relative) != item["new_sha256"]:
            raise RoadmapError(
                f"EMM post-rebind source mismatch: {relative}"
            )

    return {
        "result": "PASS",
        "transaction_id": transaction_id,
        "pre_manifest_sha256": pre_manifest_digest,
        "post_manifest_sha256": post_manifest_digest,
        "sources": source_records,
    }


def _resolve_operator_review_receipt(
    repository_root: Path,
    *,
    roadmap_id: str,
    roadmap_version: str,
    gate_id: str,
    gate_definition_path: Path,
    result_path: Path,
) -> dict[str, Any] | None:
    import hashlib
    import json

    receipt_dir = (
        repository_root
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
    )

    if not receipt_dir.is_dir():
        return None

    gate_digest = hashlib.sha256(
        gate_definition_path.read_bytes()
    ).hexdigest()

    result_digest = hashlib.sha256(
        result_path.read_bytes()
    ).hexdigest()

    matching = []

    for receipt_path in sorted(receipt_dir.glob("*.json")):
        try:
            receipt = json.loads(receipt_path.read_text())
        except (OSError, ValueError) as error:
            raise RoadmapError(
                f"invalid operator review receipt: {receipt_path}"
            ) from error

        if receipt.get("receipt_type") != "OPERATOR_REVIEW_DECISION":
            continue

        same_target = (
            receipt.get("roadmap_id") == roadmap_id
            and str(receipt.get("roadmap_version")) == str(roadmap_version)
            and receipt.get("gate_id") == gate_id
        )

        if not same_target:
            continue

        if receipt.get("gate_definition_digest") != gate_digest:
            raise RoadmapError(
                "persisted operator review gate digest mismatch"
            )

        if receipt.get("result_digest") != result_digest:
            raise RoadmapError(
                "persisted operator review result digest mismatch"
            )

        if receipt.get("result_class") != "VALID_FINAL":
            raise RoadmapError(
                "persisted operator review result class invalid"
            )

        decision = receipt.get("decision")

        if decision not in {"ACCEPT", "REJECT"}:
            raise RoadmapError(
                "persisted operator review decision invalid"
            )

        if not receipt.get("operator_identity"):
            raise RoadmapError(
                "persisted operator review authority missing"
            )

        if not receipt.get("transaction_id"):
            raise RoadmapError(
                "persisted operator review transaction missing"
            )

        if not receipt.get("receipt_id"):
            raise RoadmapError(
                "persisted operator review receipt identity missing"
            )

        matching.append(receipt)

    if not matching:
        return None

    decisions = {x["decision"] for x in matching}

    if len(decisions) != 1:
        raise RoadmapError(
            "conflicting persisted operator review decisions"
        )

    receipt_ids = {x["receipt_id"] for x in matching}

    if len(receipt_ids) != 1:
        raise RoadmapError(
            "duplicate persisted operator review authority"
        )

    return matching[0]




def apply_gate_advancement_transaction(
    repository_root: Path,
    *,
    roadmap_id: str,
    roadmap_version: str,
    gate_id: str,
    gate_definition_digest: str,
    result_digest: str,
    acceptance_receipt_id: str,
    acceptance_receipt_digest: str,
    pre_state_digest: str,
    transaction_id: str,
) -> dict[str, Any]:
    """Apply one explicit, receipt-backed atomic gate advancement."""

    from datetime import datetime, timezone
    import hashlib
    import json
    import os
    import tempfile

    try:
        from scripts.lib.eos.roadmap_lifecycle import (
            AdvancementBinding,
            LifecycleState,
            complete_accepted_gate,
        )
    except ModuleNotFoundError as error:
        if error.name != "scripts":
            raise

        from roadmap_lifecycle import (
            AdvancementBinding,
            LifecycleState,
            complete_accepted_gate,
        )

    # Exact committed replay must be recognized before current-state
    # roadmap validation. A successful advancement intentionally changes
    # current_gate, so validating the old gate as current would reject a
    # legitimate replay before its immutable transaction can be checked.
    root = Path(repository_root).resolve()

    roadmap_root = (
        root
        / "engineering/convergence/engineering-system-convergence"
    )

    transaction_dir = (
        roadmap_root
        / "runtime/advancement-transactions"
    )

    transaction_path = (
        transaction_dir
        / f"{transaction_id}.json"
    )

    recovering_pre_state_transaction = False

    if transaction_path.is_file():
        try:
            committed = json.loads(
                transaction_path.read_text()
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RoadmapError(
                "existing advancement transaction is unreadable"
            ) from exc

        expected_replay = {
            "transaction_id": transaction_id,
            "roadmap_id": roadmap_id,
            "roadmap_version": str(roadmap_version),
            "gate_id": gate_id,
            "gate_definition_digest":
                gate_definition_digest,
            "result_digest": result_digest,
            "acceptance_receipt_id":
                acceptance_receipt_id,
            "acceptance_receipt_digest":
                acceptance_receipt_digest,
            "pre_state_digest": pre_state_digest,
        }

        conflicts = [
            key
            for key, expected in expected_replay.items()
            if str(committed.get(key)) != str(expected)
        ]

        if conflicts:
            raise RoadmapError(
                "conflicting advancement transaction replay: "
                + ", ".join(sorted(conflicts))
            )

        transaction_status = committed.get("status")

        if transaction_status not in {
            "PENDING_RECONCILIATION",
            "ADVANCEMENT_COMPLETE",
        }:
            raise RoadmapError(
                "existing advancement transaction status is invalid"
            )

        state_path = roadmap_root / "STATE.yaml"

        if not state_path.is_file():
            raise RoadmapError(
                "authoritative state missing during advancement recovery"
            )

        current_state_bytes = state_path.read_bytes()
        current_state_digest = hashlib.sha256(
            current_state_bytes
        ).hexdigest()

        recorded_pre_digest = committed.get(
            "pre_state_digest"
        )
        recorded_post_digest = committed.get(
            "post_state_digest"
        )

        if transaction_status == "ADVANCEMENT_COMPLETE":
            if current_state_digest != recorded_post_digest:
                raise RoadmapError(
                    "committed advancement post-state does not match"
                )

            return {
                "result": "PASS",
                "lifecycle_state": "COMPLETED",
                "completed_gate": gate_id,
                "successor_gate": committed.get(
                    "successor_gate"
                ),
                "transaction_id": transaction_id,
                "classification": "ALREADY_APPLIED",
                "already_applied": True,
                "recovered": False,
            }

        # PENDING_RECONCILIATION has exactly two recoverable states:
        #
        # 1. STATE.yaml still equals the recorded pre-state. Fall through
        #    and deterministically execute the exact recorded transaction.
        #
        # 2. STATE.yaml already equals the recorded post-state. The state
        #    promotion succeeded and only transaction finalization was
        #    interrupted; finalize the receipt without applying state again.
        if current_state_digest == recorded_post_digest:
            committed["status"] = "ADVANCEMENT_COMPLETE"

            fd, temporary_name = tempfile.mkstemp(
                prefix="." + transaction_path.name + ".",
                dir=str(transaction_path.parent),
            )

            temporary = Path(temporary_name)

            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(
                        (
                            json.dumps(
                                committed,
                                indent=2,
                                sort_keys=True,
                            )
                            + "\n"
                        ).encode("utf-8")
                    )
                    handle.flush()
                    os.fsync(handle.fileno())

                os.replace(
                    temporary,
                    transaction_path,
                )
            finally:
                if temporary.exists():
                    temporary.unlink()

            return {
                "result": "PASS",
                "lifecycle_state": "COMPLETED",
                "completed_gate": gate_id,
                "successor_gate": committed.get(
                    "successor_gate"
                ),
                "transaction_id": transaction_id,
                "classification": "RECOVERED",
                "already_applied": True,
                "recovered": True,
                "recovery_mode":
                    "FINALIZED_POST_STATE_TRANSACTION",
            }

        if current_state_digest != recorded_pre_digest:
            raise RoadmapError(
                "pending advancement state matches neither "
                "recorded pre-state nor post-state"
            )

        recovering_pre_state_transaction = True

        # Exact pre-state remains authoritative. Continue through the normal
        # advancement path below using the already-validated immutable
        # transaction identity.
    resolver = ConvergenceRoadmap(repository_root)
    projection = resolver.projection()

    if projection["roadmap_id"] != roadmap_id:
        raise RoadmapError("roadmap identity mismatch")

    if str(projection["roadmap_version"]) != str(roadmap_version):
        raise RoadmapError("roadmap version mismatch")

    if projection["current_gate"] != gate_id:
        raise RoadmapError("gate identity mismatch")

    gate_path = Path(projection["gate_definition"])
    result_path = Path(projection["gate_result"])

    if not gate_path.is_file():
        raise RoadmapError("gate definition unavailable")

    if not result_path.is_file():
        raise RoadmapError("gate result unavailable")

    actual_gate_digest = hashlib.sha256(
        gate_path.read_bytes()
    ).hexdigest()

    actual_result_digest = hashlib.sha256(
        result_path.read_bytes()
    ).hexdigest()

    if actual_gate_digest != gate_definition_digest:
        raise RoadmapError("gate definition digest mismatch")

    if actual_result_digest != result_digest:
        raise RoadmapError("result digest mismatch")

    review_receipt = _resolve_operator_review_receipt(
        repository_root,
        roadmap_id=roadmap_id,
        roadmap_version=str(roadmap_version),
        gate_id=gate_id,
        gate_definition_path=gate_path,
        result_path=result_path,
    )

    if review_receipt is None:
        raise RoadmapError("valid ACCEPT receipt is missing")

    if review_receipt.get("decision") != "ACCEPT":
        raise RoadmapError("gate is not accepted")

    if review_receipt.get("lifecycle_state") != "ACCEPTED":
        raise RoadmapError("acceptance receipt lifecycle state invalid")

    if review_receipt.get("receipt_id") != acceptance_receipt_id:
        raise RoadmapError("acceptance receipt identity mismatch")

    receipt_dir = (
        repository_root
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
    )

    matching_receipts = [
        path
        for path in sorted(receipt_dir.glob("*.json"))
        if json.loads(path.read_text()).get("receipt_id")
        == acceptance_receipt_id
    ]

    if len(matching_receipts) != 1:
        raise RoadmapError(
            "acceptance receipt cannot be uniquely resolved"
        )

    actual_receipt_digest = hashlib.sha256(
        matching_receipts[0].read_bytes()
    ).hexdigest()

    if actual_receipt_digest != acceptance_receipt_digest:
        raise RoadmapError("acceptance receipt digest mismatch")

    for label, value in (
        ("acceptance_receipt_id", acceptance_receipt_id),
        ("acceptance_receipt_digest", acceptance_receipt_digest),
        ("pre_state_digest", pre_state_digest),
        ("transaction_id", transaction_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise RoadmapError(f"missing {label}")

    roadmap = resolver.validate()

    completed = set(roadmap["state"]["completed_gates"])
    blocked = set(roadmap["state"].get("blocked_gates", []))

    current_definition = roadmap["gates"].get(gate_id)

    if current_definition is None:
        raise RoadmapError(
            "current gate absent from authoritative roadmap"
        )

    terminal_contract = current_definition.get("terminal") or {}
    terminal = bool(terminal_contract.get("is_terminal"))
    successor = current_definition.get("next_gate")

    if terminal:
        if successor is not None:
            raise RoadmapError(
                "terminal gate cannot define successor"
            )
    else:
        if not successor:
            raise RoadmapError(
                "nonterminal gate has no authoritative successor"
            )

        successor_definition = roadmap["gates"].get(successor)

        if successor_definition is None:
            raise RoadmapError(
                "authoritative successor gate is unavailable"
            )

        if successor in completed:
            raise RoadmapError(
                "authoritative successor is already complete"
            )

        if successor in blocked:
            raise RoadmapError(
                "authoritative successor is blocked"
            )

        dependencies = successor_definition.get(
            "dependencies",
            [],
        )

        unsatisfied = [
            dependency
            for dependency in dependencies
            if (
                dependency not in completed
                and dependency != gate_id
            )
        ]

        if unsatisfied:
            raise RoadmapError(
                "authoritative successor dependencies "
                "are unsatisfied"
            )

    binding = AdvancementBinding(
        roadmap_id=roadmap_id,
        roadmap_version=str(roadmap_version),
        gate_id=gate_id,
        gate_definition_digest=gate_definition_digest,
        result_digest=result_digest,
        acceptance_receipt_id=acceptance_receipt_id,
        acceptance_receipt_digest=acceptance_receipt_digest,
        transaction_id=transaction_id,
    )

    target, resolved_successor = complete_accepted_gate(
        LifecycleState.ACCEPTED,
        binding,
        successor_gate=successor,
        terminal=terminal,
    )

    # Persist the qualified advancement as one recoverable transaction.
    #
    # The transaction receipt is written first. The authoritative roadmap
    # state is then promoted atomically. A fresh resolver must therefore
    # either observe the old state plus a recoverable transaction receipt,
    # or the complete new state. Successor execution is intentionally
    # outside this transaction.
    root = Path(repository_root).resolve()

    roadmap_root = (
        root
        / "engineering/convergence/engineering-system-convergence"
    )
    state_path = roadmap_root / "STATE.yaml"

    transaction_dir = (
        roadmap_root
        / "runtime/advancement-transactions"
    )
    transaction_dir.mkdir(parents=True, exist_ok=True)

    transaction_path = (
        transaction_dir
        / f"{transaction_id}.json"
    )

    pre_state_bytes = state_path.read_bytes()
    actual_pre_state_digest = hashlib.sha256(
        pre_state_bytes
    ).hexdigest()

    if actual_pre_state_digest != pre_state_digest:
        raise RoadmapError("pre-state digest mismatch")

    completed_gate = gate_id
    successor_gate = resolved_successor

    state_value = yaml.safe_load(
        pre_state_bytes.decode("utf-8")
    )

    if completed_gate in state_value["completed_gates"]:
        raise RoadmapError(
            "gate already completed without matching transaction replay"
        )

    if state_value["current_gate"] != completed_gate:
        raise RoadmapError("current gate mismatch before commit")

    pending = list(state_value["pending_gates"])

    if completed_gate not in pending:
        raise RoadmapError(
            "completed gate missing from pending gate set"
        )

    if not terminal and successor_gate not in pending:
        raise RoadmapError(
            "successor missing from pending gate set"
        )

    state_value["completed_gates"] = (
        list(state_value["completed_gates"])
        + [completed_gate]
    )

    state_value["pending_gates"] = [
        item for item in pending
        if item != completed_gate
    ]

    state_value["current_gate"] = (
        None if terminal else successor_gate
    )
    state_value["last_completed_gate"] = completed_gate

    completed_definition = resolver.validate()["gates"][
        completed_gate
    ]

    state_value["last_result"] = (
        completed_definition["result_location"]
    )

    evidence_root = Path(
        completed_definition["evidence_location"]
    )

    evidence_manifest = (
        evidence_root / "EVIDENCE-MANIFEST.yaml"
    )

    if not (
        root / evidence_manifest
    ).is_file():
        raise RoadmapError(
            "completed gate evidence manifest missing"
        )

    state_value["last_evidence"] = str(evidence_manifest)

    if terminal:
        state_value["next_authorized_action"] = "NONE"
    else:
        successor_definition = roadmap["gates"][
            successor_gate
        ]

        resume = successor_definition.get(
            "resume_instructions"
        )

        if isinstance(resume, dict):
            next_action = resume.get(
                "next_authorized_action"
            )
        else:
            next_action = None

        if not next_action:
            next_action = successor_definition.get(
                "next_authorized_action"
            )

        if not next_action:
            raise RoadmapError(
                "authoritative successor next action unavailable"
            )

        state_value["next_authorized_action"] = next_action

    from datetime import datetime, timezone

    state_value["updated_at"] = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    post_state_bytes = yaml.safe_dump(
        state_value,
        sort_keys=False,
    ).encode("utf-8")

    post_state_digest = hashlib.sha256(
        post_state_bytes
    ).hexdigest()

    transaction_record = {
        "schema_version": 1,
        "transaction_type": "GATE_ADVANCEMENT",
        "transaction_id": transaction_id,
        "roadmap_id": roadmap_id,
        "roadmap_version": str(roadmap_version),
        "gate_id": gate_id,
        "gate_definition_digest": gate_definition_digest,
        "result_digest": result_digest,
        "acceptance_receipt_id":
            acceptance_receipt_id,
        "acceptance_receipt_digest":
            acceptance_receipt_digest,
        "pre_state_digest": pre_state_digest,
        "post_state_digest": post_state_digest,
        "lifecycle_state": target.value,
        "successor_gate": successor_gate,
        "terminal_state": terminal,
        "next_authorized_action":
            state_value["next_authorized_action"],
        "status": "PENDING_RECONCILIATION",
    }

    transaction_bytes = (
        json.dumps(
            transaction_record,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    def atomic_write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, temporary_name = tempfile.mkstemp(
            prefix="." + path.name + ".",
            dir=str(path.parent),
        )

        temporary = Path(temporary_name)

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temporary, path)

        finally:
            if temporary.exists():
                temporary.unlink()

    # Record transaction provenance before authoritative mutation.
    atomic_write(
        transaction_path,
        transaction_bytes,
    )

    # Commit the complete parent-roadmap transition atomically.
    atomic_write(
        state_path,
        post_state_bytes,
    )

    transaction_record["status"] = "ADVANCEMENT_COMPLETE"

    atomic_write(
        transaction_path,
        (
            json.dumps(
                transaction_record,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )

    return {
        "result": "PASS",
        "transaction_id": transaction_id,
        "gate_id": gate_id,
        "lifecycle_state": target.value,
        "acceptance_receipt_id": acceptance_receipt_id,
        "successor_gate": resolved_successor,
        "terminal_state": terminal,
        "classification": (
            "RECOVERED"
            if recovering_pre_state_transaction
            else "APPLIED"
        ),
        "already_applied": False,
        "recovered": recovering_pre_state_transaction,
        "durable_state_written": False,
        "read_only": False,
    }


def apply_operator_review_transaction(
    repository_root: Path,
    *,
    roadmap_id: str,
    roadmap_version: str,
    gate_id: str,
    gate_definition_digest: str,
    result_digest: str,
    operator_identity: str,
    decision: str,
    transaction_id: str,
) -> dict[str, Any]:
    """Apply one explicit, receipt-backed operator review decision."""

    from datetime import datetime, timezone
    import hashlib
    import json

    try:
        from scripts.lib.eos.roadmap_lifecycle import (
            LifecycleState,
            OperatorDecision,
            ResultClass,
            ReviewBinding,
            apply_operator_decision,
        )
    except ModuleNotFoundError as error:
        if error.name != "scripts":
            raise

        from roadmap_lifecycle import (
            LifecycleState,
            OperatorDecision,
            ResultClass,
            ReviewBinding,
            apply_operator_decision,
        )

    resolver = ConvergenceRoadmap(repository_root)
    projection = resolver.projection()

    if projection["roadmap_id"] != roadmap_id:
        raise RoadmapError("roadmap identity mismatch")

    if str(projection["roadmap_version"]) != str(roadmap_version):
        raise RoadmapError("roadmap version mismatch")

    if projection["current_gate"] != gate_id:
        raise RoadmapError("gate identity mismatch")

    if projection["execution_result_state"] != "VALID_FINAL":
        raise RoadmapError("operator review requires VALID_FINAL result")

    if decision not in {"ACCEPT", "REJECT"}:
        raise RoadmapError("unsupported operator decision")

    for label, value in (
        ("operator_identity", operator_identity),
        ("transaction_id", transaction_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise RoadmapError(f"missing {label}")

    gate_path = Path(projection["gate_definition"])
    result_path = Path(projection["gate_result"])

    if not gate_path.is_file():
        raise RoadmapError("gate definition unavailable")

    if not result_path.is_file():
        raise RoadmapError("review result unavailable")

    actual_gate_digest = hashlib.sha256(
        gate_path.read_bytes()
    ).hexdigest()

    actual_result_digest = hashlib.sha256(
        result_path.read_bytes()
    ).hexdigest()

    if actual_gate_digest != gate_definition_digest:
        raise RoadmapError("gate definition digest mismatch")

    if actual_result_digest != result_digest:
        raise RoadmapError("result digest mismatch")

    receipt_dir = (
        repository_root
        / "engineering/convergence/engineering-system-convergence"
        / "receipts/operator-review"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = receipt_dir / f"{transaction_id}.json"

    requested_identity = {
        "transaction_id": transaction_id,
        "roadmap_id": roadmap_id,
        "roadmap_version": str(roadmap_version),
        "gate_id": gate_id,
        "gate_definition_digest": gate_definition_digest,
        "result_path": str(result_path),
        "result_digest": result_digest,
        "result_class": "VALID_FINAL",
        "decision": decision,
        "operator_identity": operator_identity,
    }

    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text())

        comparable = {
            key: prior.get(key)
            for key in requested_identity
        }

        if comparable != requested_identity:
            raise RoadmapError("conflicting transaction replay")

        return {
            "result": "PASS",
            "decision_receipt_id": prior["receipt_id"],
            "transaction_id": transaction_id,
            "decision": decision,
            "lifecycle_state": prior["lifecycle_state"],
            "classification": "ALREADY_APPLIED",
            "already_applied": True,
            "next_authorized_action":
                prior["next_authorized_action"],
        }

    for existing_path in sorted(receipt_dir.glob("*.json")):
        existing = json.loads(existing_path.read_text())

        same_review_target = (
            existing.get("roadmap_id") == roadmap_id
            and str(existing.get("roadmap_version")) == str(roadmap_version)
            and existing.get("gate_id") == gate_id
            and existing.get("gate_definition_digest")
                == gate_definition_digest
            and existing.get("result_digest") == result_digest
        )

        if not same_review_target:
            continue

        existing_decision = existing.get("decision")

        if existing_decision != decision:
            raise RoadmapError(
                "conflicting prior operator decision"
            )

        return {
            "result": "PASS",
            "decision_receipt_id": existing["receipt_id"],
            "transaction_id": existing["transaction_id"],
            "decision": existing_decision,
            "lifecycle_state": existing["lifecycle_state"],
            "classification": "ALREADY_APPLIED",
            "already_applied": True,
            "next_authorized_action":
                existing["next_authorized_action"],
        }

    if projection["lifecycle_state"] != "AWAITING_OPERATOR_REVIEW":
        raise RoadmapError(
            "operator review requires AWAITING_OPERATOR_REVIEW"
        )

    binding = ReviewBinding(
        roadmap_id=roadmap_id,
        roadmap_version=str(roadmap_version),
        gate_id=gate_id,
        gate_definition_digest=gate_definition_digest,
        result_digest=result_digest,
        operator_identity=operator_identity,
        transaction_id=transaction_id,
    )

    target = apply_operator_decision(
        LifecycleState.AWAITING_OPERATOR_REVIEW,
        ResultClass.VALID_FINAL,
        OperatorDecision[decision],
        binding,
    )

    decided_at = datetime.now(timezone.utc).isoformat()

    receipt_seed = {
        **requested_identity,
        "decided_at": decided_at,
        "lifecycle_state": target.value,
    }

    receipt_digest = hashlib.sha256(
        json.dumps(
            receipt_seed,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    receipt_id = "ORR-" + receipt_digest[:24].upper()

    receipt = {
        "receipt_type": "OPERATOR_REVIEW_DECISION",
        "receipt_id": receipt_id,
        **receipt_seed,
        "next_authorized_action":
            "EXECUTE_CR21_IMPLEMENT_ATOMIC_ADVANCEMENT"
            if decision == "ACCEPT"
            else "RECONCILE_REJECTED_GATE_RESULT",
    }

    tmp = receipt_path.with_suffix(".tmp")

    if tmp.exists():
        tmp.unlink()

    tmp.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    tmp.replace(receipt_path)

    return {
        "result": "PASS",
        "decision_receipt_id": receipt_id,
        "transaction_id": transaction_id,
        "decision": decision,
        "lifecycle_state": target.value,
        "classification": "APPLIED",
        "already_applied": False,
        "next_authorized_action":
            receipt["next_authorized_action"],
    }



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
        f"Lifecycle State: {value['lifecycle_state']}",
        f"Execution Result State: {value['execution_result_state']}",
        f"Review Required: {'YES' if value['review_required'] else 'NO'}",
        f"Review State: {value['review_state']}",
        f"Operator Decision: {value['operator_decision']}",
        f"Completion State: {value['completion_state']}",
        f"Last Completed Gate: {value['last_completed_gate'] or 'none'}",
        f"Completed: {completed}",
        f"Blocked Gates: {blocked}",
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

    review_parser = subparsers.add_parser("operator-review")
    review_parser.add_argument("--roadmap-id", required=True)
    review_parser.add_argument("--roadmap-version", required=True)
    review_parser.add_argument("--gate-id", required=True)
    review_parser.add_argument("--gate-definition-digest", required=True)
    review_parser.add_argument("--result-digest", required=True)
    review_parser.add_argument("--operator-identity", required=True)
    review_parser.add_argument(
        "--decision",
        required=True,
        choices=("ACCEPT", "REJECT"),
    )
    review_parser.add_argument("--transaction-id", required=True)

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
        elif args.command == "operator-review":
            result = apply_operator_review_transaction(
                resolver.repository_root,
                roadmap_id=args.roadmap_id,
                roadmap_version=args.roadmap_version,
                gate_id=args.gate_id,
                gate_definition_digest=args.gate_definition_digest,
                result_digest=args.result_digest,
                operator_identity=args.operator_identity,
                decision=args.decision,
                transaction_id=args.transaction_id,
            )
            print(
                yaml.safe_dump(
                    {
                        **result,
                        "command": "operator-review",
                        "roadmap_id": args.roadmap_id,
                        "read_only": False,
                    },
                    sort_keys=False,
                ).rstrip()
            )
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
