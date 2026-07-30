"""Fail-closed semantic governance for Progressive Runtime capabilities."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_dependencies import (
    CLASSIFICATION_PATH,
)
from scripts.lib.authority_pipeline.progressive_runtime_registration import (
    INTERFACE_LAYERS,
    REGISTRY_PATH as CONSUMER_REGISTRY_PATH,
    validate as validate_consumers,
)


class RuntimeCapabilityError(ValueError):
    """The Progressive Runtime capability contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-capabilities.json"


def _load(root: Path, relative: str, label: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimeCapabilityError(
            f"runtime-capability input is incomplete: {relative}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeCapabilityError(
            f"runtime-capability input is invalid: {relative}"
        ) from error
    if not isinstance(value, dict):
        raise RuntimeCapabilityError(f"{label} must be an object")
    return value


def _strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def validate(repository: Path | str) -> dict[str, object]:
    """Prove bidirectional capability/layer/interface/consumer traceability."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH, "runtime capability registry")
    classification = _load(root, CLASSIFICATION_PATH, "runtime classification")
    consumers = _load(root, CONSUMER_REGISTRY_PATH, "runtime consumer registry")
    try:
        consumer_analysis = validate_consumers(root)
    except ValueError as error:
        raise RuntimeCapabilityError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimeCapabilityError("unsupported runtime capability registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeCapabilityError("invalid runtime capability registry model")
    entries = registry.get("capabilities")
    if not isinstance(entries, list) or not entries:
        raise RuntimeCapabilityError("runtime capabilities must be a nonempty list")

    layer_owners: dict[int, set[str]] = {}
    for item in classification.get("runtime_layers", []):
        if isinstance(item, dict) and isinstance(item.get("layer"), int):
            modules = item.get("modules")
            if isinstance(modules, list):
                layer_owners[item["layer"]] = set(modules)

    consumer_entries = consumers.get("consumers")
    if not isinstance(consumer_entries, list):
        raise RuntimeCapabilityError("runtime consumer registry is invalid")
    declared_consumers = {
        item["consumer"]: item
        for item in consumer_entries
        if isinstance(item, dict) and isinstance(item.get("consumer"), str)
    }
    declarations = consumers.get("capability_declarations")
    if not isinstance(declarations, dict):
        raise RuntimeCapabilityError(
            "runtime consumer capability declarations are missing"
        )
    if set(declarations) != set(declared_consumers):
        raise RuntimeCapabilityError(
            "runtime consumer capability declarations are stale or incomplete"
        )
    for consumer, declared in declarations.items():
        if not _strings(declared) or declared != sorted(declared):
            raise RuntimeCapabilityError(
                f"invalid capability declaration for {consumer}"
            )

    capabilities: dict[str, dict[str, object]] = {}
    consumer_capabilities = {consumer: [] for consumer in declared_consumers}
    for raw in entries:
        if not isinstance(raw, dict):
            raise RuntimeCapabilityError("invalid runtime capability entry")
        identifier = raw.get("capability")
        layers = raw.get("runtime_layers")
        owners = raw.get("runtime_owners")
        interfaces = raw.get("interfaces")
        registered = raw.get("consumers")
        if (
            not isinstance(identifier, str)
            or not identifier
            or not isinstance(layers, list)
            or not layers
            or any(not isinstance(layer, int) for layer in layers)
            or len(layers) != len(set(layers))
            or not _strings(owners)
            or not _strings(interfaces)
            or not _strings(registered)
        ):
            raise RuntimeCapabilityError("invalid runtime capability entry")
        if identifier in capabilities:
            raise RuntimeCapabilityError(
                f"duplicate capability identifier: {identifier}"
            )
        unknown_layers = set(layers) - layer_owners.keys()
        if unknown_layers:
            raise RuntimeCapabilityError(
                f"undefined runtime layer for capability {identifier}"
            )
        expected_owners = set().union(*(layer_owners[layer] for layer in layers))
        if set(owners) != expected_owners:
            raise RuntimeCapabilityError(
                f"orphaned capability or runtime owner mismatch: {identifier}"
            )
        unknown_interfaces = set(interfaces) - INTERFACE_LAYERS.keys()
        if unknown_interfaces:
            raise RuntimeCapabilityError(
                f"undefined capability interface for {identifier}: "
                + ", ".join(sorted(unknown_interfaces))
            )
        interface_layers = set().union(
            *(INTERFACE_LAYERS[interface] for interface in interfaces)
        )
        if not set(layers) <= interface_layers:
            raise RuntimeCapabilityError(
                f"capability/interface mismatch: {identifier}"
            )
        unknown_consumers = set(registered) - declared_consumers.keys()
        if unknown_consumers:
            raise RuntimeCapabilityError(
                f"stale capability registration: {identifier}: "
                + ", ".join(sorted(unknown_consumers))
            )
        for consumer in registered:
            declaration = declared_consumers[consumer]
            if not set(layers) <= set(declaration["runtime_layers"]):
                raise RuntimeCapabilityError(
                    f"consumer capability mismatch: {consumer}: {identifier}"
                )
            if not set(declaration["interfaces"]) & set(interfaces):
                raise RuntimeCapabilityError(
                    f"capability/interface mismatch: {consumer}: {identifier}"
                )
            consumer_capabilities[consumer].append(identifier)
        capabilities[identifier] = raw

    if [item.get("capability") for item in entries] != sorted(capabilities):
        raise RuntimeCapabilityError(
            "runtime capability registry is not deterministically ordered"
        )
    for raw in entries:
        for field in ("runtime_layers", "runtime_owners", "interfaces", "consumers"):
            if raw[field] != sorted(raw[field]):
                raise RuntimeCapabilityError(
                    f"runtime capability {field} are not deterministically ordered"
                )
    for consumer, declared in declarations.items():
        unknown = set(declared) - capabilities.keys()
        if unknown:
            raise RuntimeCapabilityError(
                f"consumer references nonexistent capabilities: {consumer}: "
                + ", ".join(sorted(unknown))
            )
        registered = set(consumer_capabilities[consumer])
        if set(declared) != registered:
            raise RuntimeCapabilityError(
                f"consumer capability declaration is not synchronized: {consumer}"
            )
    missing = [
        consumer
        for consumer, declared in consumer_capabilities.items()
        if not declared
    ]
    if missing:
        raise RuntimeCapabilityError(
            "consumer references no registered capability: "
            + ", ".join(sorted(missing))
        )

    return {
        "status": "PASS",
        "capability_count": len(capabilities),
        "consumer_count": consumer_analysis["consumer_count"],
        "capabilities": [
            {
                "capability": identifier,
                "runtime_layers": capabilities[identifier]["runtime_layers"],
                "runtime_owners": capabilities[identifier]["runtime_owners"],
                "interfaces": capabilities[identifier]["interfaces"],
                "consumers": capabilities[identifier]["consumers"],
            }
            for identifier in sorted(capabilities)
        ],
        "consumer_capabilities": {
            consumer: sorted(declared)
            for consumer, declared in sorted(consumer_capabilities.items())
        },
    }
