"""Static enforcement for the frozen Progressive Runtime Layer dependency graph."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path


class DependencyContractError(ValueError):
    """The Progressive Runtime Layer dependency contract is violated."""


@dataclass(frozen=True)
class ModuleRule:
    layer: int | None
    path: str


CLASSIFICATION_PATH = (
    "engineering/architecture/progressive-runtime-classification.json"
)
EXPECTED_RUNTIME_LAYERS = (
    (1, "Progressive Authority Primitives", ("scripts.lib.emp.progressive_gate",)),
    (2, "Progressive Decision Authority", ("scripts.lib.emp.progressive_gate",)),
    (
        3,
        "Progressive Lifecycle Projection",
        ("scripts.lib.emp.progressive_lifecycle",),
    ),
)
RUNTIME_MODULES = {
    "scripts.lib.emp.progressive_gate": ModuleRule(
        layer=1, path="scripts/lib/emp/progressive_gate.py"
    ),
    "scripts.lib.emp.progressive_lifecycle": ModuleRule(
        layer=3, path="scripts/lib/emp/progressive_lifecycle.py"
    ),
}

# Layer 1 and Layer 2 are intentionally co-located in progressive_gate.py.
DECISION_AUTHORITY = "scripts.lib.emp.progressive_gate"
FOUNDATION_MODULES = {
    "scripts.lib.emp.progressive_runtime_support": ModuleRule(
        layer=None, path="scripts/lib/emp/progressive_runtime_support.py"
    )
}
COMPATIBILITY_MODULES = {
    "scripts.lib.emp.progressive_oa": ModuleRule(
        layer=None, path="scripts/lib/emp/progressive_oa.py"
    ),
    "scripts.lib.emp.oa02_lifecycle": ModuleRule(
        layer=None, path="scripts/lib/emp/oa02_lifecycle.py"
    ),
}
PROJECTION_FORBIDDEN_DEFINITIONS = {
    "approve",
    "decide",
    "decline",
    "record_acceptance",
    "validate_receipt",
    "verify",
    "_persist_receipt",
    "_write_state",
}
EXPECTED_FOUNDATION_MODULES = frozenset(FOUNDATION_MODULES)
EXPECTED_COMPATIBILITY_MODULES = frozenset(COMPATIBILITY_MODULES)
EXPECTED_QUALIFICATION_INFRASTRUCTURE = frozenset(
    {
        "scripts.lib.authority_pipeline.progressive_runtime_capabilities",
        "scripts.lib.authority_pipeline.progressive_runtime_consolidation",
        "scripts.lib.authority_pipeline.progressive_runtime_dependencies",
        "scripts.lib.authority_pipeline.progressive_runtime_execution_contracts",
        "scripts.lib.authority_pipeline.progressive_runtime_outcomes",
        "scripts.lib.authority_pipeline.progressive_runtime_policies",
        "scripts.lib.authority_pipeline.progressive_runtime_registration",
        "scripts.lib.authority_pipeline.progressive_runtime_states",
        "scripts.lib.authority_pipeline.progressive_runtime_transitions",
        "scripts.tests.test-progressive-runtime-capabilities",
        "scripts.tests.test-progressive-runtime-consolidation",
        "scripts.tests.test-progressive-runtime-dependencies",
        "scripts.tests.test-progressive-runtime-execution-contracts",
        "scripts.tests.test-progressive-runtime-implementation-synchronization",
        "scripts.tests.test-progressive-runtime-outcomes",
        "scripts.tests.test-progressive-runtime-policies",
        "scripts.tests.test-progressive-runtime-registration",
        "scripts.tests.test-progressive-runtime-states",
        "scripts.tests.test-progressive-runtime-transitions",
    }
)


def _classification(repository: Path) -> dict[str, object]:
    path = repository / CLASSIFICATION_PATH
    if not path.is_file():
        raise DependencyContractError(
            f"runtime classification input is incomplete: {CLASSIFICATION_PATH}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DependencyContractError(
            f"runtime classification input is invalid: {CLASSIFICATION_PATH}"
        ) from error
    if not isinstance(value, dict):
        raise DependencyContractError("runtime classification must be an object")
    return value


def _require_exact_classification(value: dict[str, object]) -> None:
    layers = value.get("runtime_layers")
    if not isinstance(layers, list):
        raise DependencyContractError("runtime_layers must be a list")
    actual_layers: list[tuple[int, str, tuple[str, ...]]] = []
    for entry in layers:
        if not isinstance(entry, dict):
            raise DependencyContractError("runtime layer classification is invalid")
        layer = entry.get("layer")
        name = entry.get("name")
        modules = entry.get("modules")
        if (
            not isinstance(layer, int)
            or not isinstance(name, str)
            or not isinstance(modules, list)
            or not modules
            or any(not isinstance(module, str) for module in modules)
        ):
            raise DependencyContractError("runtime layer classification is invalid")
        actual_layers.append((layer, name, tuple(modules)))
    if tuple(actual_layers) != EXPECTED_RUNTIME_LAYERS:
        raise DependencyContractError(
            "runtime model must contain exactly the three canonical runtime layers"
        )

    expected_categories = {
        "foundational_shared_utilities": EXPECTED_FOUNDATION_MODULES,
        "compatibility_adapters": EXPECTED_COMPATIBILITY_MODULES,
        "qualification_infrastructure": EXPECTED_QUALIFICATION_INFRASTRUCTURE,
    }
    runtime_modules = {
        module for _, _, modules in actual_layers for module in modules
    }
    categories: dict[str, frozenset[str]] = {}
    for category, expected in expected_categories.items():
        entries = value.get(category)
        if (
            not isinstance(entries, list)
            or any(not isinstance(entry, str) for entry in entries)
            or len(entries) != len(set(entries))
        ):
            raise DependencyContractError(f"{category} classification is invalid")
        categories[category] = frozenset(entries)
        if categories[category] != expected:
            raise DependencyContractError(
                f"{category} classification does not match the frozen runtime model"
            )

    classified_sets = [runtime_modules, *categories.values()]
    for index, left in enumerate(classified_sets):
        for right in classified_sets[index + 1 :]:
            if left & right:
                raise DependencyContractError(
                    "a module is assigned to conflicting runtime classifications"
                )


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
            result.update(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return result


def _definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _runtime_edges(repository: Path) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {}
    for module, rule in RUNTIME_MODULES.items():
        edges[module] = _imports(repository / rule.path) & RUNTIME_MODULES.keys()
    return edges


def _require_acyclic(edges: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module: str) -> None:
        if module in visiting:
            raise DependencyContractError(
                f"runtime circular dependency includes {module}"
            )
        if module in visited:
            return
        visiting.add(module)
        for dependency in edges[module]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in edges:
        visit(module)


def validate(repository: Path | str) -> dict[str, object]:
    """Validate the governance-owned runtime and foundational dependency graph."""
    root = Path(repository).resolve()
    classification = _classification(root)
    _require_exact_classification(classification)
    all_rules = {
        **RUNTIME_MODULES,
        **FOUNDATION_MODULES,
    }
    missing = [rule.path for rule in all_rules.values() if not (root / rule.path).is_file()]
    if missing:
        raise DependencyContractError(
            "dependency validation input is incomplete: " + ", ".join(missing)
        )

    compatibility = set(COMPATIBILITY_MODULES)
    foundation = set(FOUNDATION_MODULES)
    runtime = set(RUNTIME_MODULES)
    imports = {
        module: _imports(root / rule.path) for module, rule in all_rules.items()
    }

    for module in runtime:
        leakage = imports[module] & compatibility
        if leakage:
            raise DependencyContractError(
                f"runtime module {module} consumes compatibility module(s): "
                + ", ".join(sorted(leakage))
            )
        if module == DECISION_AUTHORITY:
            allowed_runtime: set[str] = set()
        else:
            allowed_runtime = {DECISION_AUTHORITY}
        upward = (imports[module] & runtime) - allowed_runtime
        if upward:
            raise DependencyContractError(
                f"upward runtime dependency from {module}: "
                + ", ".join(sorted(upward))
            )

    for module in foundation:
        forbidden = imports[module] & (runtime | compatibility)
        if forbidden:
            raise DependencyContractError(
                f"foundational utility {module} consumes runtime/compatibility: "
                + ", ".join(sorted(forbidden))
            )

    projection_path = root / RUNTIME_MODULES[
        "scripts.lib.emp.progressive_lifecycle"
    ].path
    forbidden_owners = _definitions(projection_path) & PROJECTION_FORBIDDEN_DEFINITIONS
    if forbidden_owners:
        raise DependencyContractError(
            "lifecycle projection duplicates authority ownership: "
            + ", ".join(sorted(forbidden_owners))
        )

    edges = _runtime_edges(root)
    _require_acyclic(edges)
    return {
        "status": "PASS",
        "qualification_scope": "GOVERNANCE_IMPLEMENTATION",
        "runtime_layer_count": len(EXPECTED_RUNTIME_LAYERS),
        "runtime_layers": [
            {"layer": layer, "name": name, "modules": list(modules)}
            for layer, name, modules in EXPECTED_RUNTIME_LAYERS
        ],
        "runtime_modules": sorted(runtime),
        "foundation_modules": sorted(foundation),
        "compatibility_modules": sorted(compatibility),
        "qualification_infrastructure": sorted(
            EXPECTED_QUALIFICATION_INFRASTRUCTURE
        ),
        "runtime_edges": {
            module: sorted(dependencies)
            for module, dependencies in sorted(edges.items())
        },
        "compatibility_synchronization": "DEFERRED_TO_CONSUMER_PUBLICATION",
    }


def validate_implementation(repository: Path | str) -> dict[str, object]:
    """Validate downstream compatibility adapters when their unit publishes."""
    root = Path(repository).resolve()
    governance = validate(root)
    missing = [
        rule.path
        for rule in COMPATIBILITY_MODULES.values()
        if not (root / rule.path).is_file()
    ]
    if missing:
        raise DependencyContractError(
            "compatibility validation input is incomplete: " + ", ".join(missing)
        )
    runtime = set(RUNTIME_MODULES)
    imports = {
        module: _imports(root / rule.path)
        for module, rule in COMPATIBILITY_MODULES.items()
    }
    return {
        **governance,
        "qualification_scope": "IMPLEMENTATION_SYNCHRONIZATION",
        "compatibility_synchronization": "PASS",
        "compatibility_consumes_runtime": {
            module: sorted(imports[module] & runtime)
            for module in sorted(COMPATIBILITY_MODULES)
        },
    }
