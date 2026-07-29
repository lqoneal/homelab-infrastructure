#!/usr/bin/env python3
"""Repository-independent engineering contract conformance analysis."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml


CONTRACT_CATEGORIES = {
    "Command Interface",
    "API",
    "Configuration",
    "Data Schema",
    "File Format",
    "Service Interface",
    "Workflow",
    "State Transition",
    "Exit Behavior",
    "Observable Output",
}
CONTRACT_ELEMENTS = {
    "command_names",
    "arguments",
    "options",
    "environment_variables",
    "configuration_keys",
    "file_locations",
    "schemas",
    "return_values",
    "exit_codes",
    "generated_artifacts",
    "expected_side_effects",
    "invariants",
    "preconditions",
    "postconditions",
}
DETERMINATIONS = {
    "conformant",
    "partially_conformant",
    "undocumented_capability",
    "undocumented_behavior",
    "missing_implementation",
    "obsolete_contract",
    "incompatible_implementation",
    "ambiguous_contract",
}


def load_contracts(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("engineering contract catalog is not a mapping")
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise ValueError("engineering contract catalog requires a contracts list")
    identifiers: set[str] = set()
    for contract in contracts:
        if not isinstance(contract, dict):
            raise ValueError("engineering contract is not a mapping")
        identifier = contract.get("contract_id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("engineering contract requires contract_id")
        if identifier in identifiers:
            raise ValueError(f"duplicate engineering contract: {identifier}")
        identifiers.add(identifier)
        if contract.get("category") not in CONTRACT_CATEGORIES:
            raise ValueError(f"{identifier}: unsupported contract category")
        if not isinstance(contract.get("source"), dict):
            raise ValueError(f"{identifier}: documented source is required")
        if not isinstance(contract.get("discovery"), dict):
            raise ValueError(f"{identifier}: discovery declaration is required")
        expectations = contract.get("expectations")
        if not isinstance(expectations, dict) or not expectations:
            raise ValueError(f"{identifier}: expectations are required")
        unknown = set(expectations) - CONTRACT_ELEMENTS
        if unknown:
            raise ValueError(f"{identifier}: unsupported contract elements: {sorted(unknown)}")
    return payload


def _stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def canonical_report(report: dict[str, Any]) -> str:
    return json.dumps(_stable(report), indent=2, sort_keys=True) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tokens(help_text: str, prefix: str) -> list[str]:
    values: set[str] = set()
    for token in help_text.replace(",", " ").replace("[", " ").replace("]", " ").split():
        cleaned = token.strip("(){}:;")
        if cleaned.startswith(prefix):
            values.add(cleaned.split("=", 1)[0])
    return sorted(values)


def _discover_cli(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    locator = str(declaration["locator"])
    executable = root / locator
    command_path = [str(item) for item in declaration.get("command_path", [])]
    evidence = {
        "mechanism": "help_interface",
        "locator": locator,
        "command_path": command_path,
    }
    if not executable.is_file():
        return {"status": "missing", "evidence": evidence}
    try:
        completed = subprocess.run(
            [str(executable), *command_path, "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={"PATH": "/usr/bin:/bin"},
        )
    except (OSError, subprocess.SubprocessError) as error:
        evidence["error"] = str(error)
        return {"status": "unavailable", "evidence": evidence}
    help_text = completed.stdout + completed.stderr
    evidence.update(
        {
            "inspection_only": True,
            "return_code": completed.returncode,
            "content_sha256": hashlib.sha256(help_text.encode()).hexdigest(),
        }
    )
    return {
        "status": "discovered" if help_text else "unavailable",
        "command_names": sorted(
            set(command_path)
            | set(str(item) for item in declaration.get("known_command_names", []))
        ),
        "options": _tokens(help_text, "-"),
        "observable_output": help_text,
        "evidence": evidence,
    }


def _discover_python_ast(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    locator = str(declaration["locator"])
    path = root / locator
    symbol = declaration.get("symbol")
    evidence = {"mechanism": "python_ast", "locator": locator, "symbol": symbol}
    if not path.is_file():
        return {"status": "missing", "evidence": evidence}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as error:
        evidence["error"] = str(error)
        return {"status": "unavailable", "evidence": evidence}
    signatures: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if symbol and node.name != symbol:
                continue
            signatures.append(
                {
                    "name": node.name,
                    "arguments": [
                        argument.arg
                        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                    ],
                    "return_annotation": ast.unparse(node.returns) if node.returns else None,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                }
            )
    evidence["content_sha256"] = _sha256(path)
    return {
        "status": "discovered" if signatures else "missing",
        "api_signatures": sorted(signatures, key=lambda item: item["name"]),
        "evidence": evidence,
    }


def _flatten_keys(value: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value):
            dotted = f"{prefix}.{key}" if prefix else str(key)
            keys.append(dotted)
            keys.extend(_flatten_keys(value[key], dotted))
    return keys


def _discover_structured(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    locator = str(declaration["locator"])
    path = root / locator
    mechanism = str(declaration.get("mechanism", "configuration_inspection"))
    evidence = {"mechanism": mechanism, "locator": locator}
    if not path.is_file():
        return {"status": "missing", "evidence": evidence}
    try:
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as error:
        evidence["error"] = str(error)
        return {"status": "unavailable", "evidence": evidence}
    evidence["content_sha256"] = _sha256(path)
    return {
        "status": "discovered",
        "configuration_keys": _flatten_keys(payload),
        "schemas": payload if mechanism == "schema_parsing" else None,
        "evidence": evidence,
    }


def discover_contract(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    declaration = contract["discovery"]
    mechanism = declaration.get("mechanism")
    if mechanism == "help_interface":
        return _discover_cli(root, declaration)
    if mechanism in {"api_signature", "metadata_extraction"}:
        return _discover_python_ast(root, declaration)
    if mechanism in {
        "schema_parsing",
        "configuration_inspection",
        "manifest_inspection",
        "service_descriptor",
    }:
        return _discover_structured(root, declaration)
    if mechanism == "file_inspection":
        locator = str(declaration["locator"])
        path = root / locator
        evidence = {"mechanism": mechanism, "locator": locator}
        if not path.is_file():
            return {"status": "missing", "evidence": evidence}
        evidence["content_sha256"] = _sha256(path)
        return {"status": "discovered", "evidence": evidence}
    return {
        "status": "unavailable",
        "evidence": {"mechanism": mechanism, "error": "unsupported discovery mechanism"},
    }


def _observed_values(element: str, discovered: dict[str, Any]) -> list[Any]:
    mapping = {
        "command_names": "command_names",
        "arguments": "arguments",
        "options": "options",
        "configuration_keys": "configuration_keys",
        "schemas": "schemas",
        "return_values": "return_values",
        "exit_codes": "exit_codes",
        "generated_artifacts": "generated_artifacts",
        "expected_side_effects": "expected_side_effects",
        "invariants": "invariants",
        "preconditions": "preconditions",
        "postconditions": "postconditions",
    }
    if element == "file_locations":
        return [discovered.get("evidence", {}).get("locator")]
    if element == "observable_output":
        return [discovered.get("observable_output", "")]
    if element == "environment_variables":
        return discovered.get("environment_variables", [])
    if element == "arguments":
        return sorted(
            {
                argument
                for signature in discovered.get("api_signatures", [])
                for argument in signature.get("arguments", [])
            }
        )
    value = discovered.get(mapping.get(element, element), [])
    return value if isinstance(value, list) else [value]


def _matches(expected: Any, observed: list[Any]) -> bool:
    if isinstance(expected, dict):
        return all(item in observed for item in expected)
    expected_values = expected if isinstance(expected, list) else [expected]
    for value in expected_values:
        if isinstance(value, str) and any(
            isinstance(item, str) and value in item for item in observed
        ):
            continue
        if value not in observed:
            return False
    return True


def analyze(root: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    validated: list[dict[str, Any]] = []
    discovered_contracts: list[dict[str, Any]] = []
    invariant_failures: list[dict[str, Any]] = []
    compatibility_findings: list[dict[str, Any]] = []
    undocumented: list[dict[str, Any]] = []
    for contract in sorted(catalog["contracts"], key=lambda item: item["contract_id"]):
        discovered = discover_contract(root, contract)
        discovered_contracts.append(
            {"contract_id": contract["contract_id"], **discovered}
        )
        expectations = contract["expectations"]
        checks: list[dict[str, Any]] = []
        if discovered["status"] == "missing":
            determination = (
                "obsolete_contract" if contract.get("lifecycle") == "deprecated"
                else "missing_implementation"
            )
        elif discovered["status"] != "discovered":
            determination = "ambiguous_contract"
        else:
            for element in sorted(expectations):
                observed = _observed_values(element, discovered)
                passed = _matches(expectations[element], observed)
                check = {
                    "element": element,
                    "status": "PASS" if passed else "FAIL",
                    "expected": expectations[element],
                    "observed": observed,
                }
                checks.append(check)
                if not passed:
                    invariant_failures.append(
                        {
                            "contract_id": contract["contract_id"],
                            "invariant": f"documented {element} exists or agrees",
                            "evidence": check,
                        }
                    )
            failures = [item for item in checks if item["status"] == "FAIL"]
            if not failures:
                determination = "conformant"
            elif all(
                item["status"] == "FAIL"
                for item in checks
                if item["element"] != "file_locations"
            ):
                determination = "incompatible_implementation"
            else:
                determination = "partially_conformant"
            if determination in {"incompatible_implementation", "partially_conformant"}:
                compatibility_findings.append(
                    {
                        "contract_id": contract["contract_id"],
                        "risk": "documented interface missing or changed",
                        "advisory": True,
                        "evidence": failures,
                    }
                )
        if discovered["status"] == "discovered":
            for element in sorted(expectations):
                expected = expectations[element]
                if not isinstance(expected, list):
                    continue
                observed = _observed_values(element, discovered)
                extras = sorted(
                    (item for item in observed if item not in expected),
                    key=str,
                )
                for extra in extras:
                    undocumented.append(
                        {
                            "contract_id": contract["contract_id"],
                            "determination": (
                                "undocumented_capability"
                                if element == "command_names"
                                else "undocumented_behavior"
                            ),
                            "element": element,
                            "observed": extra,
                            "evidence": discovered["evidence"],
                        }
                    )
        validated.append(
            {
                "contract_id": contract["contract_id"],
                "category": contract["category"],
                "source": contract["source"],
                "determination": determination,
                "checks": checks,
                "evidence": discovered["evidence"],
            }
        )
    counts = {
        determination: sum(
            item["determination"] == determination for item in validated
        )
        for determination in sorted(DETERMINATIONS)
    }
    counts["undocumented_capability"] = sum(
        item["determination"] == "undocumented_capability" for item in undocumented
    )
    counts["undocumented_behavior"] = sum(
        item["determination"] == "undocumented_behavior" for item in undocumented
    )
    actions = sorted(
        {
            "Reconcile documented and discovered interface evidence."
            for item in validated
            if item["determination"] != "conformant"
        }
        | (
            {"Review undocumented capabilities and document or explicitly exclude them."}
            if undocumented
            else set()
        )
    )
    return {
        "schema_version": 1,
        "authority": catalog.get("authority"),
        "evidence_classification": "derived_engineering_evidence",
        "authority_boundaries": catalog.get("authority_boundaries", {}),
        "validated_contracts": validated,
        "discovered_contracts": discovered_contracts,
        "conformant_interfaces": [
            item["contract_id"]
            for item in validated
            if item["determination"] == "conformant"
        ],
        "partial_conformance": [
            item for item in validated if item["determination"] == "partially_conformant"
        ],
        "undocumented_implementation_behavior": undocumented,
        "incompatible_implementation": [
            item for item in validated if item["determination"] == "incompatible_implementation"
        ],
        "invariant_failures": invariant_failures,
        "compatibility_findings": compatibility_findings,
        "recommended_engineering_actions": actions,
        "summary": counts,
    }
