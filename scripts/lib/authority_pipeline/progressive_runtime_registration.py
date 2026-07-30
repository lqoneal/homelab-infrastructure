"""Fail-closed validation of Progressive Runtime consumer registrations."""

from __future__ import annotations

import ast
import json
from pathlib import Path


class RuntimeRegistrationError(ValueError):
    """The Progressive Runtime consumer registration contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-consumers.json"
CANONICAL_LAYERS = frozenset({1, 2, 3})
INTERFACE_LAYERS = {
    "scripts.lib.emp.progressive_gate": frozenset({1, 2}),
    "scripts.lib.emp.progressive_lifecycle": frozenset({3}),
    "scripts.lib.emp.progressive_oa": frozenset({1, 2}),
    "scripts.lib.emp.oa02_lifecycle": frozenset({3}),
}
RUNTIME_INTERNAL = frozenset(
    {
        "scripts.lib.emp.progressive_gate",
        "scripts.lib.emp.progressive_lifecycle",
    }
)
COMPATIBILITY_CONSUMERS = frozenset(
    {
        "scripts.lib.emp.progressive_oa",
        "scripts.lib.emp.oa02_lifecycle",
    }
)


def _module_path(root: Path, module: str) -> Path:
    return root / (module.replace(".", "/") + ".py")


def _imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        raise RuntimeRegistrationError(
            f"runtime-registration input is invalid: {path}"
        ) from error
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            imports.update(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return imports


def _load_registry(root: Path) -> dict[str, object]:
    path = root / REGISTRY_PATH
    if not path.is_file():
        raise RuntimeRegistrationError(
            f"runtime-registration input is incomplete: {REGISTRY_PATH}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeRegistrationError(
            f"runtime-registration input is invalid: {REGISTRY_PATH}"
        ) from error
    if not isinstance(value, dict):
        raise RuntimeRegistrationError("runtime consumer registry must be an object")
    return value


def _discover(root: Path) -> dict[str, set[str]]:
    base = root / "scripts/lib"
    if not base.is_dir():
        raise RuntimeRegistrationError(
            "runtime-registration input is incomplete: scripts/lib"
        )
    discovered: dict[str, set[str]] = {}
    for path in sorted(base.rglob("*.py")):
        module = ".".join(path.relative_to(root).with_suffix("").parts)
        if module in RUNTIME_INTERNAL:
            continue
        consumed = _imports(path) & INTERFACE_LAYERS.keys()
        if consumed:
            discovered[module] = consumed
    return discovered


def validate(repository: Path | str) -> dict[str, object]:
    """Prove the governance registry contract without loading consumers."""
    root = Path(repository).resolve()
    registry = _load_registry(root)
    if registry.get("schema_version") != 1:
        raise RuntimeRegistrationError("unsupported runtime consumer registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeRegistrationError("invalid runtime consumer registry model")
    raw_entries = registry.get("consumers")
    if not isinstance(raw_entries, list):
        raise RuntimeRegistrationError("runtime consumer registrations must be a list")

    registrations: dict[str, dict[str, object]] = {}
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise RuntimeRegistrationError("invalid runtime consumer registry entry")
        consumer = raw.get("consumer")
        consumer_type = raw.get("consumer_type")
        layers = raw.get("runtime_layers")
        interfaces = raw.get("interfaces")
        if (
            not isinstance(consumer, str)
            or not consumer
            or consumer_type not in {"production", "compatibility"}
            or not isinstance(layers, list)
            or not layers
            or any(not isinstance(layer, int) for layer in layers)
            or len(layers) != len(set(layers))
            or not isinstance(interfaces, list)
            or not interfaces
            or any(not isinstance(interface, str) for interface in interfaces)
            or len(interfaces) != len(set(interfaces))
        ):
            raise RuntimeRegistrationError("invalid runtime consumer registry entry")
        if consumer in registrations:
            raise RuntimeRegistrationError(
                f"duplicate runtime consumer registration: {consumer}"
            )
        if not set(layers) <= CANONICAL_LAYERS:
            raise RuntimeRegistrationError(
                f"nonexistent runtime layer registered by {consumer}"
            )
        unknown = set(interfaces) - INTERFACE_LAYERS.keys()
        if unknown:
            raise RuntimeRegistrationError(
                f"unregistered runtime interface for {consumer}: "
                + ", ".join(sorted(unknown))
            )
        expected_layers = set().union(
            *(INTERFACE_LAYERS[interface] for interface in interfaces)
        )
        if set(layers) != expected_layers:
            raise RuntimeRegistrationError(
                f"runtime layers do not match registered interfaces for {consumer}"
            )
        expected_type = (
            "compatibility"
            if consumer in COMPATIBILITY_CONSUMERS
            else "production"
        )
        if consumer_type != expected_type:
            raise RuntimeRegistrationError(
                f"invalid consumer type for {consumer}: {consumer_type}"
            )
        registrations[consumer] = raw

    ordered = sorted(registrations)
    if [entry["consumer"] for entry in raw_entries] != ordered:
        raise RuntimeRegistrationError(
            "runtime consumer registry is not deterministically ordered"
        )
    return {
        "status": "PASS",
        "qualification_scope": "GOVERNANCE_DECLARATIONS",
        "implementation_synchronization": "DEFERRED_TO_CONSUMER_PUBLICATION",
        "consumer_count": len(ordered),
        "production_consumers": [
            consumer
            for consumer in ordered
            if registrations[consumer]["consumer_type"] == "production"
        ],
        "compatibility_consumers": [
            consumer
            for consumer in ordered
            if registrations[consumer]["consumer_type"] == "compatibility"
        ],
        "registrations": [
            {
                "consumer": consumer,
                "runtime_layers": registrations[consumer]["runtime_layers"],
                "interfaces": registrations[consumer]["interfaces"],
            }
            for consumer in ordered
        ],
    }


def validate_implementation(repository: Path | str) -> dict[str, object]:
    """Synchronize declared consumers with implementation at its publication."""
    root = Path(repository).resolve()
    governance = validate(root)
    registrations = {
        item["consumer"]: item for item in governance["registrations"]
    }
    for consumer in registrations:
        if not _module_path(root, consumer).is_file():
            raise RuntimeRegistrationError(
                f"registered runtime consumer is missing: {consumer}"
            )

    discovered = _discover(root)
    missing = set(discovered) - registrations.keys()
    if missing:
        raise RuntimeRegistrationError(
            "unregistered runtime consumer(s): " + ", ".join(sorted(missing))
        )
    stale = registrations.keys() - discovered.keys()
    if stale:
        raise RuntimeRegistrationError(
            "invalid registry entries without runtime consumption: "
            + ", ".join(sorted(stale))
        )
    for consumer, consumed in discovered.items():
        declared = set(registrations[consumer]["interfaces"])
        if consumed != declared:
            raise RuntimeRegistrationError(
                f"consumer bypasses registered runtime interfaces: {consumer}"
            )

    return {
        **governance,
        "qualification_scope": "IMPLEMENTATION_SYNCHRONIZATION",
        "implementation_synchronization": "PASS",
    }
