#!/usr/bin/env python3
"""Repository-independent, read-only engineering property assurance analysis."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


PROPERTY_CATEGORIES = {
    "Safety Invariant", "Authorization Boundary", "Approval Boundary",
    "State-Transition Rule", "Idempotence Requirement", "Recovery Guarantee",
    "Failure-Containment Rule", "Dependency Requirement", "Evidence Requirement",
    "Lifecycle Constraint", "Integrity Requirement", "Availability Requirement",
    "Determinism Requirement", "Auditability Requirement",
    "Mission Correctness Requirement",
}
STRATEGIES = {
    "Static Inspection", "State-Machine Analysis", "Dependency-Graph Analysis",
    "Policy Evaluation", "Manifest Validation", "Schema Validation",
    "Control-Flow Inspection", "Read-Only Command Inspection",
    "Deterministic Simulation", "Non-Mutating Test Harness",
    "Existing Regression Evidence Evaluation", "Evidence Traceability Analysis",
}
DETERMINATIONS = {
    "ASSURED", "PARTIALLY_ASSURED", "NOT_ASSURED", "VIOLATED",
    "INSUFFICIENT_EVIDENCE", "AMBIGUOUS_PROPERTY", "OBSOLETE_PROPERTY",
    "NOT_APPLICABLE",
}
IMPACTS = {
    "engineering review required", "implementation correction required",
    "documentation correction required", "contract correction required",
    "synchronization update required", "revalidation required",
    "independent qualification required", "publication review required",
    "operational hold recommended", "no action required",
}
REQUIRED_FIELDS = {
    "property_id", "authoritative_source", "category", "engineering_objective",
    "subject", "preconditions", "required_invariant", "prohibited_condition",
    "applicable_states", "applicable_transitions", "dependency_assumptions",
    "validation_strategy", "required_evidence", "failure_classification",
    "assurance_impact", "review_owner", "authority_boundary",
}


def _stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def canonical_report(report: dict[str, Any]) -> str:
    return json.dumps(_stable(report), indent=2, sort_keys=True) + "\n"


def load_catalog(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("properties"), list):
        raise ValueError("engineering assurance catalog requires a properties list")
    identifiers: set[str] = set()
    for item in payload["properties"]:
        if not isinstance(item, dict):
            raise ValueError("engineering property is not a mapping")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"engineering property missing fields: {sorted(missing)}")
        identifier = item["property_id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"EP-[A-Z0-9-]+", identifier):
            raise ValueError(f"invalid permanent property identifier: {identifier!r}")
        if identifier in identifiers:
            raise ValueError(f"duplicate engineering property: {identifier}")
        identifiers.add(identifier)
        if item["category"] not in PROPERTY_CATEGORIES:
            raise ValueError(f"{identifier}: unsupported property category")
        strategies = item["validation_strategy"]
        if isinstance(strategies, str):
            strategies = [strategies]
        if not strategies or set(strategies) - STRATEGIES:
            raise ValueError(f"{identifier}: unsupported validation strategy")
        impacts = item["assurance_impact"]
        if isinstance(impacts, str):
            impacts = [impacts]
        if not impacts or set(impacts) - IMPACTS:
            raise ValueError(f"{identifier}: unsupported assurance impact")
        if not isinstance(item["authoritative_source"], dict):
            raise ValueError(f"{identifier}: authoritative source is required")
    return payload


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inspect(root: Path, check: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a declaration-selected, non-mutating inspection."""
    kind = str(check.get("kind", "file_exists"))
    locator = str(check.get("locator", ""))
    path = root / locator
    evidence: dict[str, Any] = {"kind": kind, "locator": locator}
    if kind == "file_exists":
        passed = path.is_file() if check.get("object", "file") == "file" else path.exists()
        if path.is_file():
            evidence["sha256"] = _digest(path)
    elif kind in {"contains", "not_contains", "regex"}:
        if not path.is_file():
            return {**evidence, "status": "INSUFFICIENT", "reason": "locator does not resolve"}
        text = path.read_text(encoding="utf-8")
        pattern = str(check.get("pattern", ""))
        matched = bool(re.search(pattern, text, re.MULTILINE))
        passed = (not matched) if kind == "not_contains" else matched
        evidence.update({"sha256": _digest(path), "pattern": pattern, "matched": matched})
    elif kind == "python_symbol":
        if not path.is_file():
            return {**evidence, "status": "INSUFFICIENT", "reason": "locator does not resolve"}
        tree = ast.parse(path.read_text(encoding="utf-8"))
        symbol = str(check.get("symbol", ""))
        passed = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == symbol for node in ast.walk(tree)
        )
        evidence.update({"sha256": _digest(path), "symbol": symbol})
    elif kind == "state_machine":
        states = set(map(str, check.get("states", [])))
        terminal = set(map(str, check.get("terminal_states", [])))
        transitions = [tuple(map(str, value)) for value in check.get("transitions", [])]
        prohibited = [tuple(map(str, value)) for value in check.get("prohibited_transitions", [])]
        illegal_terminal = sorted([list(t) for t in transitions if t[0] in terminal and t[0] != t[1]])
        present_prohibited = sorted([list(t) for t in transitions if t in prohibited])
        unknown = sorted([list(t) for t in transitions if t[0] not in states or t[1] not in states])
        passed = not illegal_terminal and not present_prohibited and not unknown
        evidence.update({
            "states": sorted(states), "transitions": sorted([list(t) for t in transitions]),
            "illegal_terminal_transitions": illegal_terminal,
            "present_prohibited_transitions": present_prohibited,
            "unknown_state_transitions": unknown,
        })
    elif kind == "declaration":
        passed = bool(check.get("value"))
        evidence["declared_value"] = check.get("value")
    else:
        return {**evidence, "status": "INSUFFICIENT", "reason": "unsupported inspection kind"}
    return {**evidence, "status": "PASS" if passed else "FAIL"}


def _group(check: dict[str, Any]) -> str:
    return str(check.get("result_group", "invariant_results"))


def _determination(prop: dict[str, Any], results: list[dict[str, Any]]) -> str:
    status = prop.get("property_status", "applicable")
    if status == "obsolete":
        return "OBSOLETE_PROPERTY"
    if status == "ambiguous":
        return "AMBIGUOUS_PROPERTY"
    if status == "not_applicable":
        return "NOT_APPLICABLE"
    if not results or any(item["status"] == "INSUFFICIENT" for item in results):
        return "INSUFFICIENT_EVIDENCE"
    evaluated = [
        item for item in results if item["kind"] != "authoritative_source_traceability"
    ]
    if not evaluated:
        return "NOT_ASSURED"
    failures = [item for item in evaluated if item["status"] == "FAIL"]
    if failures and len(failures) == len(evaluated):
        return "VIOLATED"
    if failures:
        return "PARTIALLY_ASSURED"
    return "ASSURED"


def analyze(root: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    properties: list[dict[str, Any]] = []
    for prop in sorted(catalog["properties"], key=lambda value: value["property_id"]):
        checks = prop.get("checks", [])
        results = [_inspect(root, check) for check in checks]
        source = prop["authoritative_source"]
        source_path = root / str(source.get("locator", ""))
        source_result = {
            "status": "PASS" if source_path.is_file() else "INSUFFICIENT",
            "kind": "authoritative_source_traceability",
            "locator": str(source.get("locator", "")),
        }
        results_for_determination = [*results, source_result]
        grouped = {
            name: [result for check, result in zip(checks, results) if _group(check) == name]
            for name in (
                "invariant_results", "transition_results", "authority_boundary_results",
                "idempotence_results", "failure_path_results",
                "evidence_sufficiency_results",
            )
        }
        determination = _determination(prop, results_for_determination)
        idempotence_checks = grouped["idempotence_results"]
        if prop["category"] != "Idempotence Requirement" and not idempotence_checks:
            idempotence_classification = "not applicable"
        elif any(item["status"] == "INSUFFICIENT" for item in idempotence_checks):
            idempotence_classification = "insufficient evidence"
        elif any(item["status"] == "FAIL" for item in idempotence_checks):
            idempotence_classification = "replay risk"
        elif idempotence_checks:
            idempotence_classification = "proven idempotent"
        else:
            idempotence_classification = "conditionally idempotent"
        unresolved = [
            result.get("reason", f"{result['kind']} inspection failed")
            for result in results_for_determination if result["status"] != "PASS"
        ]
        observed = []
        if source_path.is_file():
            observed.append({"locator": str(source["locator"]), "sha256": _digest(source_path)})
        properties.append({
            "property_id": prop["property_id"],
            "authoritative_source": source,
            "property_category": prop["category"],
            "engineering_objective": prop["engineering_objective"],
            "evaluated_subject": prop["subject"],
            "validation_strategy": prop["validation_strategy"],
            "observed_evidence": observed,
            **grouped,
            "idempotence_classification": idempotence_classification,
            "evidence_sufficiency_results": grouped["evidence_sufficiency_results"] + [source_result],
            "assurance_determination": determination,
            "assurance_impact": prop["assurance_impact"],
            "unresolved_conditions": sorted(set(unresolved)),
            "recommended_engineering_actions": (
                ["no action required"] if determination == "ASSURED"
                else list(prop.get("recommended_engineering_actions", prop["assurance_impact"]))
            ),
            "review_owner": prop["review_owner"],
            "authority_boundary": prop["authority_boundary"],
        })
    unresolved = [p["property_id"] for p in properties if p["assurance_determination"] != "ASSURED"]
    return {
        "schema_version": 1,
        "evidence_classification": "derived engineering evidence",
        "authority_boundary_statement": (
            "This report grants no approval, qualification, publication, lifecycle, "
            "operational, implementation, ownership, or decision authority."
        ),
        "evaluated_systems": sorted({str(p["subject"]) for p in catalog["properties"]}),
        "assurance_strategies": sorted({
            strategy for p in catalog["properties"]
            for strategy in ([p["validation_strategy"]] if isinstance(p["validation_strategy"], str) else p["validation_strategy"])
        }),
        "declared_engineering_properties": properties,
        "assurance_determinations": [
            {"property_id": p["property_id"], "determination": p["assurance_determination"]}
            for p in properties
        ],
        "unresolved_properties": unresolved,
        "recommended_engineering_actions": sorted({
            action for p in properties for action in p["recommended_engineering_actions"]
        }),
    }
