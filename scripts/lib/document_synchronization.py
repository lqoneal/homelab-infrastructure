"""Repository-independent implementation/document synchronization analysis."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml


DRIFT_STATES = {
    "PASS",
    "OUT_OF_SYNC",
    "IMPLEMENTATION_CHANGED",
    "DOCUMENT_CHANGED",
    "MISSING_ARTIFACT",
    "SUPERSEDED",
    "UNKNOWN",
}
OBJECT_TYPES = {
    "file",
    "directory",
    "executable",
    "script",
    "library",
    "service",
    "configuration",
    "generated_artifact",
}
FINGERPRINT_STRATEGIES = {
    "sha256",
    "repository_inventory",
    "git_object",
    "repository_commit",
    "immutable_locator",
}
QUALIFICATION_IMPACTS = {
    "qualification_still_valid",
    "manual_review_required",
    "automatic_revalidation_sufficient",
    "independent_qualification_required",
    "publication_required",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_path(path: Path) -> str:
    """Hash a file or a directory's sorted relative names, kinds, and contents."""
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    if not path.is_dir():
        raise FileNotFoundError(path)
    for child in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        relative = child.relative_to(path).as_posix()
        kind = "directory" if child.is_dir() else "file"
        digest.update(canonical_json([relative, kind]))
        if child.is_file():
            digest.update(child.read_bytes())
    return digest.hexdigest()


def git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def fingerprint(
    repository: Path,
    locator: str,
    strategy: str,
) -> str:
    if strategy not in FINGERPRINT_STRATEGIES:
        raise ValueError(f"unsupported fingerprint strategy: {strategy}")
    if strategy == "repository_commit":
        return git_output(repository, "rev-parse", "HEAD")
    if strategy == "immutable_locator":
        return hashlib.sha256(locator.encode("utf-8")).hexdigest()
    path = (repository / locator).resolve()
    path.relative_to(repository.resolve())
    if not path.exists():
        raise FileNotFoundError(locator)
    if strategy == "sha256":
        return sha256_path(path)
    if strategy == "repository_inventory":
        inventory = git_output(
            repository,
            "ls-files",
            "-co",
            "--exclude-standard",
            "--",
            locator,
        ).splitlines()
        digest = hashlib.sha256()
        for repository_locator in sorted(set(filter(None, inventory))):
            artifact = repository / repository_locator
            if artifact.is_file():
                digest.update(canonical_json(repository_locator))
                digest.update(artifact.read_bytes())
        return digest.hexdigest()
    return git_output(repository, "hash-object", str(path))


def load_metadata(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("synchronization metadata is not a mapping")
    return loaded


def validate_metadata(metadata: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    declarations = metadata.get("synchronizations")
    if not isinstance(declarations, list):
        return ["synchronizations must be a list"]
    seen: set[str] = set()
    for index, declaration in enumerate(declarations):
        label = f"synchronizations[{index}]"
        if not isinstance(declaration, dict):
            errors.append(f"{label} must be a mapping")
            continue
        identifier = declaration.get("synchronization_id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{label}.synchronization_id is required")
        elif identifier in seen:
            errors.append(f"{label}.synchronization_id is duplicated")
        else:
            seen.add(identifier)
        for key in (
            "documentation",
            "implementation",
            "ownership",
            "validation_scope",
            "synchronization_strategy",
        ):
            if not declaration.get(key):
                errors.append(f"{label}.{key} is required")
        if not isinstance(declaration.get("qualification_policy"), dict):
            errors.append(f"{label}.qualification_policy is required")
        implementation = declaration.get("implementation", {})
        if isinstance(implementation, dict):
            if implementation.get("object_type") not in OBJECT_TYPES:
                errors.append(f"{label}.implementation.object_type is invalid")
            strategies = implementation.get("fingerprints")
            if not isinstance(strategies, list) or not strategies:
                errors.append(f"{label}.implementation.fingerprints is required")
            else:
                for item in strategies:
                    if (
                        not isinstance(item, dict)
                        or item.get("strategy") not in FINGERPRINT_STRATEGIES
                    ):
                        errors.append(f"{label}.implementation fingerprint is invalid")
        else:
            errors.append(f"{label}.implementation must be a mapping")
    return errors


def _changed(fingerprints: list[dict[str, Any]]) -> bool | None:
    comparable = [
        item for item in fingerprints
        if item.get("expected") is not None and item.get("actual") is not None
    ]
    if not comparable:
        return None
    return any(
        not item.get("matches", item["expected"] == item["actual"])
        for item in comparable
    )


def fingerprint_matches(
    repository: Path,
    strategy: str,
    expected: str | None,
    actual: str | None,
) -> bool | None:
    """Compare fingerprints without creating a commit-publication fixed point."""
    if expected is None or actual is None:
        return None
    if strategy != "repository_commit":
        return expected == actual
    completed = subprocess.run(
        [
            "git", "-C", str(repository), "merge-base", "--is-ancestor",
            expected, actual,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.returncode == 0


def classify(
    *,
    exists: bool,
    superseded: bool,
    implementation_changed: bool | None,
    documentation_changed: bool | None,
) -> str:
    if superseded:
        return "SUPERSEDED"
    if not exists:
        return "MISSING_ARTIFACT"
    if implementation_changed is None or documentation_changed is None:
        return "UNKNOWN"
    if implementation_changed and documentation_changed:
        return "OUT_OF_SYNC"
    if implementation_changed:
        return "IMPLEMENTATION_CHANGED"
    if documentation_changed:
        return "DOCUMENT_CHANGED"
    return "PASS"


def qualification_impact(status: str, policy: dict[str, Any]) -> dict[str, Any]:
    configured = policy.get(status)
    if not isinstance(configured, list) or not configured:
        defaults = {
            "PASS": ["qualification_still_valid"],
            "DOCUMENT_CHANGED": ["manual_review_required", "publication_required"],
            "IMPLEMENTATION_CHANGED": ["manual_review_required"],
            "OUT_OF_SYNC": ["independent_qualification_required", "publication_required"],
            "MISSING_ARTIFACT": ["independent_qualification_required"],
            "SUPERSEDED": ["manual_review_required", "publication_required"],
            "UNKNOWN": ["manual_review_required"],
        }
        configured = defaults[status]
    actions = sorted(set(configured))
    invalid = sorted(set(actions) - QUALIFICATION_IMPACTS)
    if invalid:
        raise ValueError(f"invalid qualification impact: {', '.join(invalid)}")
    return {
        "assessment": actions,
        "approval_decision": None,
        "automatic_decision_prohibited": True,
    }


def build_graph(declarations: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, str]] = {}
    edges: set[tuple[str, str, str]] = set()
    for declaration in declarations:
        document = declaration["documentation"]["document_id"]
        artifact = declaration["implementation"]["repository_locator"]
        nodes[document] = {"id": document, "kind": "documentation"}
        nodes[artifact] = {"id": artifact, "kind": "implementation"}
        edges.add((document, artifact, "synchronizes_with"))
        for dependent in declaration.get("downstream_documentation", []):
            nodes[dependent] = {"id": dependent, "kind": "documentation"}
            edges.add((dependent, document, "depends_on"))
    return {
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": [
            {"source": source, "target": target, "relationship": relationship}
            for source, target, relationship in sorted(edges)
        ],
    }


def affected_documentation(
    graph: dict[str, Any], changed_artifacts: set[str]
) -> list[str]:
    reverse: dict[str, set[str]] = defaultdict(set)
    node_kinds = {node["id"]: node["kind"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        reverse[edge["target"]].add(edge["source"])
    found: set[str] = set()
    queue = deque(sorted(changed_artifacts))
    visited = set(queue)
    while queue:
        node = queue.popleft()
        for dependent in sorted(reverse[node]):
            if dependent in visited:
                continue
            visited.add(dependent)
            queue.append(dependent)
            if node_kinds.get(dependent) == "documentation":
                found.add(dependent)
    return sorted(found)


def analyze(repository: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    errors = validate_metadata(metadata)
    if errors:
        raise ValueError("; ".join(errors))
    declarations = sorted(
        metadata["synchronizations"], key=lambda item: item["synchronization_id"]
    )
    graph = build_graph(declarations)
    results: list[dict[str, Any]] = []
    changed_artifacts: set[str] = set()
    for declaration in declarations:
        implementation = declaration["implementation"]
        documentation = declaration["documentation"]
        locator = implementation["repository_locator"]
        implementation_path = repository / locator
        document_locator = documentation["repository_locator"]
        document_path = repository / document_locator
        implementation_fingerprints: list[dict[str, Any]] = []
        for item in implementation["fingerprints"]:
            strategy = item["strategy"]
            try:
                actual = fingerprint(repository, locator, strategy)
            except (FileNotFoundError, OSError, subprocess.SubprocessError, ValueError):
                actual = None
            implementation_fingerprints.append(
                {
                    "strategy": strategy,
                    "expected": item.get("value"),
                    "actual": actual,
                    "matches": fingerprint_matches(
                        repository, strategy, item.get("value"), actual
                    ),
                }
            )
        document_strategy = documentation.get("fingerprint", {}).get(
            "strategy", "sha256"
        )
        try:
            document_actual = fingerprint(repository, document_locator, document_strategy)
        except (FileNotFoundError, OSError, subprocess.SubprocessError, ValueError):
            document_actual = None
        document_fingerprints = [{
            "strategy": document_strategy,
            "expected": documentation.get("fingerprint", {}).get("value"),
            "actual": document_actual,
            "matches": fingerprint_matches(
                repository,
                document_strategy,
                documentation.get("fingerprint", {}).get("value"),
                document_actual,
            ),
        }]
        implementation_changed = _changed(implementation_fingerprints)
        documentation_changed = _changed(document_fingerprints)
        status = classify(
            exists=implementation_path.exists() and document_path.exists(),
            superseded=bool(declaration.get("superseded_by")),
            implementation_changed=implementation_changed,
            documentation_changed=documentation_changed,
        )
        if status in {"OUT_OF_SYNC", "IMPLEMENTATION_CHANGED", "MISSING_ARTIFACT"}:
            changed_artifacts.add(locator)
        results.append({
            "synchronization_id": declaration["synchronization_id"],
            "documentation": documentation,
            "implementation": {
                "repository_locator": locator,
                "object_type": implementation["object_type"],
            },
            "ownership": declaration["ownership"],
            "validation_scope": declaration["validation_scope"],
            "synchronization_strategy": declaration["synchronization_strategy"],
            "implementation_fingerprints": implementation_fingerprints,
            "documentation_fingerprints": document_fingerprints,
            "implementation_changed": implementation_changed,
            "documentation_changed": documentation_changed,
            "synchronization_required": status not in {"PASS", "SUPERSEDED"},
            "requalification_required": status
            in {"OUT_OF_SYNC", "MISSING_ARTIFACT"},
            "drift_status": status,
            "qualification_impact": qualification_impact(
                status, declaration["qualification_policy"]
            ),
            "required_actions": qualification_impact(
                status, declaration["qualification_policy"]
            )["assessment"],
        })
    return {
        "schema_version": 1,
        "repository": metadata.get("repository", {}),
        "synchronized_artifacts": results,
        "dependency_graph": graph,
        "affected_documentation": affected_documentation(graph, changed_artifacts),
        "summary": {
            state: sum(item["drift_status"] == state for item in results)
            for state in sorted(DRIFT_STATES)
        },
    }
