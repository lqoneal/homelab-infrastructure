"""Repository-independent implementation/document coverage analysis."""

from __future__ import annotations

import fnmatch
import json
import stat
import subprocess
from pathlib import Path
from typing import Any

import yaml


REQUIREMENTS = {"mandatory", "optional", "prohibited"}
COVERAGE_STATES = {
    "synchronized",
    "undocumented",
    "orphaned_declaration",
    "obsolete_declaration",
    "excluded_by_policy",
    "external_dependency",
    "unknown_classification",
}
DOCUMENT_KINDS = {
    "SPEC": "Specification",
    "PROC": "Procedure",
    "STD": "Standard",
    "EWO": "WOP",
    "ROADMAP": "Roadmap",
    "GATE": "Gate Specification",
    "VERIFICATION": "Verification Guide",
    "COMPLETION": "Completion Report",
}


def load_policy(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("coverage policy is not a mapping")
    return value


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    categories = policy.get("categories")
    rules = policy.get("classification_rules")
    roots = policy.get("discovery", {}).get("roots")
    if not isinstance(categories, dict) or not categories:
        errors.append("categories must be a non-empty mapping")
        categories = {}
    for name, definition in categories.items():
        if not isinstance(definition, dict):
            errors.append(f"category {name} must be a mapping")
        elif definition.get("documentation") not in REQUIREMENTS:
            errors.append(f"category {name} documentation policy is invalid")
    if not isinstance(rules, list) or not rules:
        errors.append("classification_rules must be a non-empty list")
    else:
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict) or rule.get("category") not in categories:
                errors.append(f"classification_rules[{index}] category is invalid")
            if not isinstance(rule, dict) or not isinstance(rule.get("patterns"), list):
                errors.append(f"classification_rules[{index}] patterns are required")
    if not isinstance(roots, list) or not roots:
        errors.append("discovery.roots must be a non-empty list")
    return errors


def _repository_files(repository: Path) -> list[str]:
    """Reuse Git's repository inventory; fall back to a deterministic walk."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), "ls-files", "-co", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return sorted(set(filter(None, completed.stdout.splitlines())))
    except (OSError, subprocess.SubprocessError):
        return sorted(
            path.relative_to(repository).as_posix()
            for path in repository.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )


def discover(repository: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    roots = tuple(root.rstrip("/") for root in policy["discovery"]["roots"])
    files = [
        locator
        for locator in _repository_files(repository)
        if any(locator == root or locator.startswith(root + "/") for root in roots)
    ]
    artifacts: list[dict[str, Any]] = []
    for locator in files:
        path = repository / locator
        mode = path.stat().st_mode if path.exists() else 0
        artifacts.append(
            {
                "repository_locator": locator,
                "artifact_kind": (
                    "executable"
                    if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    else "file"
                ),
                "discovery_evidence": {
                    "mechanism": "git_repository_inventory",
                    "root": next(
                        root
                        for root in roots
                        if locator == root or locator.startswith(root + "/")
                    ),
                },
            }
        )
    return artifacts


def classify_artifact(locator: str, policy: dict[str, Any]) -> dict[str, str]:
    for rule in policy["classification_rules"]:
        if any(fnmatch.fnmatchcase(locator, pattern) for pattern in rule["patterns"]):
            category = rule["category"]
            definition = policy["categories"][category]
            return {
                "category": category,
                "documentation_requirement": definition["documentation"],
                "classification_evidence": rule.get("evidence", f"matched {rule['patterns']}"),
            }
    return {
        "category": "Unknown",
        "documentation_requirement": "mandatory",
        "classification_evidence": "no ordered classification rule matched",
    }


def _covers(declaration: dict[str, Any], locator: str) -> bool:
    implementation = declaration.get("implementation", {})
    declared = implementation.get("repository_locator")
    if not isinstance(declared, str):
        return False
    if declared == locator:
        return True
    return (
        implementation.get("coverage_scope") == "recursive"
        and locator.startswith(declared.rstrip("/") + "/")
    )


def _document_kind(document: dict[str, Any]) -> str:
    document_id = str(document.get("document_id", "")).upper()
    locator = str(document.get("repository_locator", "")).upper()
    for marker, kind in DOCUMENT_KINDS.items():
        if marker in document_id or marker in locator:
            return kind
    return "Other Authoritative Documentation"


def analyze(
    repository: Path,
    synchronization_metadata: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    declarations = sorted(
        synchronization_metadata.get("synchronizations", []),
        key=lambda item: item.get("synchronization_id", ""),
    )
    discovered = discover(repository, policy)
    results: list[dict[str, Any]] = []
    declared_ids: set[str] = set()
    graph_edges: set[tuple[str, str, str]] = set()
    graph_nodes: dict[str, dict[str, str]] = {}

    for artifact in discovered:
        locator = artifact["repository_locator"]
        classification = classify_artifact(locator, policy)
        matches = [item for item in declarations if _covers(item, locator)]
        for match in matches:
            declared_ids.add(match["synchronization_id"])
        documents = []
        for match in matches:
            document = match["documentation"]
            document_exists = (repository / document["repository_locator"]).is_file()
            documents.append(
                {
                    "synchronization_id": match["synchronization_id"],
                    "document_id": document["document_id"],
                    "repository_locator": document["repository_locator"],
                    "document_kind": _document_kind(document),
                    "exists": document_exists,
                }
            )
            graph_nodes[locator] = {"id": locator, "kind": "implementation"}
            graph_nodes[document["document_id"]] = {
                "id": document["document_id"],
                "kind": "documentation",
            }
            graph_edges.add((document["document_id"], locator, "covers"))

        requirement = classification["documentation_requirement"]
        if classification["category"] == "External Dependency":
            state = "external_dependency"
        elif classification["category"] == "Unknown":
            state = "unknown_classification"
        elif requirement in {"optional", "prohibited"}:
            state = "excluded_by_policy"
        elif not matches:
            state = "undocumented"
        elif any(item.get("superseded_by") for item in matches):
            state = "obsolete_declaration"
        elif all(item["exists"] for item in documents):
            state = "synchronized"
        else:
            state = "orphaned_declaration"
        results.append(
            {
                **artifact,
                **classification,
                "coverage_state": state,
                "documentation": documents,
                "evidence": {
                    "matched_declarations": [
                        item["synchronization_id"] for item in matches
                    ],
                    "artifact_exists": (repository / locator).exists(),
                },
            }
        )

    orphan_declarations: list[dict[str, Any]] = []
    obsolete_declarations: list[dict[str, Any]] = []
    for declaration in declarations:
        locator = declaration["implementation"]["repository_locator"]
        implementation_exists = (repository / locator).exists()
        document = declaration["documentation"]
        documentation_exists = (repository / document["repository_locator"]).is_file()
        matched = declaration["synchronization_id"] in declared_ids
        if declaration.get("superseded_by"):
            obsolete_declarations.append(
                {
                    "synchronization_id": declaration["synchronization_id"],
                    "superseded_by": declaration["superseded_by"],
                    "implementation_locator": locator,
                    "evidence": "declaration contains an explicit supersedence locator",
                }
            )
        if not implementation_exists or not documentation_exists or not matched:
            orphan_declarations.append(
                {
                    "synchronization_id": declaration["synchronization_id"],
                    "implementation_locator": locator,
                    "documentation_locator": document["repository_locator"],
                    "implementation_exists": implementation_exists,
                    "documentation_exists": documentation_exists,
                    "matched_discovered_artifact": matched,
                    "obsolete": bool(declaration.get("superseded_by")),
                    "evidence": "declaration endpoint or discovered implementation is unreachable",
                }
            )

    total = len(results)
    mandatory = [item for item in results if item["documentation_requirement"] == "mandatory"]
    synchronized = [item for item in results if item["coverage_state"] == "synchronized"]
    undocumented = [item for item in results if item["coverage_state"] == "undocumented"]
    excluded = [
        item
        for item in results
        if item["coverage_state"] in {"excluded_by_policy", "external_dependency"}
    ]
    documented_mandatory = [
        item for item in mandatory if item["coverage_state"] == "synchronized"
    ]
    synchronization_covered = [
        item for item in results if bool(item["documentation"])
    ]
    metrics = {
        "total_implementation_artifacts": total,
        "synchronized_artifacts": len(synchronized),
        "undocumented_artifacts": len(undocumented),
        "orphan_declarations": len(orphan_declarations),
        "excluded_artifacts": len(excluded),
        "documentation_coverage_percentage": round(
            100.0 * len(documented_mandatory) / len(mandatory), 2
        )
        if mandatory
        else 100.0,
        "synchronization_coverage_percentage": round(
            100.0 * len(synchronization_covered) / total, 2
        )
        if total
        else 100.0,
        "documentation_debt": len(undocumented)
        + sum(not item["documentation_exists"] for item in orphan_declarations),
    }
    gaps = [
        {
            "repository_locator": item["repository_locator"],
            "finding": item["coverage_state"],
            "evidence": item["evidence"],
        }
        for item in results
        if item["coverage_state"]
        in {"undocumented", "orphaned_declaration", "unknown_classification"}
    ]
    return {
        "schema_version": 1,
        "authority": policy.get("authority"),
        "repository": synchronization_metadata.get("repository", {}),
        "discovered_implementation_artifacts": results,
        "synchronized_artifacts": synchronized,
        "undocumented_artifacts": undocumented,
        "orphan_declarations": orphan_declarations,
        "obsolete_declarations": obsolete_declarations,
        "excluded_artifacts": excluded,
        "coverage_graph": {
            "nodes": [graph_nodes[key] for key in sorted(graph_nodes)],
            "edges": [
                {"source": source, "target": target, "relationship": relationship}
                for source, target, relationship in sorted(graph_edges)
            ],
        },
        "synchronization_gaps": gaps,
        "documentation_debt": {
            "count": metrics["documentation_debt"],
            "artifacts": [item["repository_locator"] for item in undocumented],
        },
        "orphan_findings": {
            "undocumented_implementation": [
                item["repository_locator"] for item in undocumented
            ],
            "documentation_without_implementation": [
                item["documentation_locator"]
                for item in orphan_declarations
                if not item["implementation_exists"]
            ],
            "obsolete_synchronization_declarations": [
                item["synchronization_id"]
                for item in obsolete_declarations
            ],
            "unreachable_implementation": [
                item["implementation_locator"]
                for item in orphan_declarations
                if not item["implementation_exists"]
            ],
            "unreachable_documentation": [
                item["documentation_locator"]
                for item in orphan_declarations
                if not item["documentation_exists"]
            ],
            "stale_dependency_declarations": [
                item["synchronization_id"]
                for item in orphan_declarations
                if not item["implementation_exists"] or not item["documentation_exists"]
            ],
        },
        "coverage_metrics": metrics,
        "recommended_review_actions": [
            {
                "action": "declare_or_exclude_implementation",
                "repository_locator": item["repository_locator"],
            }
            for item in undocumented
        ]
        + [
            {
                "action": "repair_or_retire_declaration",
                "synchronization_id": item["synchronization_id"],
            }
            for item in orphan_declarations
        ],
    }


def canonical_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
