"""Fail-closed behavioral governance for Progressive Runtime capabilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_capabilities import (
    REGISTRY_PATH as CAPABILITY_REGISTRY_PATH,
    RuntimeCapabilityError,
    validate as validate_capabilities,
)


class RuntimePolicyError(ValueError):
    """The Progressive Runtime policy contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-policies.json"
EXPECTED_AUTHORITY_LEVELS = [
    "CONTROLLED_MISSION_AUTHORITY",
    "GATE_DECISION_AUTHORITY",
    "READ_ONLY_RUNTIME_AUTHORITY",
]
EXPECTED_APPROVAL_STATES = ["NOT_REQUIRED", "REQUIRED"]
EXPECTED_LIFECYCLE_STATES = ["ACTIVE"]
EXPECTED_FAILURE_BEHAVIORS = ["FAIL_CLOSED"]
EXPECTED_ELIGIBILITY = {
    "capability_registered": True,
    "canonical_interface_required": True,
    "registered_consumer_required": True,
}


def _load(root: Path, relative: str, label: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimePolicyError(f"runtime-policy input is incomplete: {relative}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimePolicyError(f"runtime-policy input is invalid: {relative}") from error
    if not isinstance(value, dict):
        raise RuntimePolicyError(f"{label} must be an object")
    return value


def _ordered_unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
        and value == sorted(value)
        and len(value) == len(set(value))
    )


def validate(repository: Path | str) -> dict[str, object]:
    """Prove one-policy ownership and full policy-to-consumer traceability."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH, "runtime policy registry")
    capability_path = root / CAPABILITY_REGISTRY_PATH
    if not capability_path.is_file():
        raise RuntimePolicyError(
            f"runtime-policy input is incomplete: {CAPABILITY_REGISTRY_PATH}"
        )
    digest = hashlib.sha256(capability_path.read_bytes()).hexdigest()
    if registry.get("capability_registry_sha256") != digest:
        raise RuntimePolicyError("stale runtime policy registration metadata")
    try:
        capability_analysis = validate_capabilities(root)
    except RuntimeCapabilityError as error:
        raise RuntimePolicyError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimePolicyError("unsupported runtime policy registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimePolicyError("invalid runtime policy registry model")
    vocabularies = (
        ("authority_levels", EXPECTED_AUTHORITY_LEVELS),
        ("approval_states", EXPECTED_APPROVAL_STATES),
        ("lifecycle_states", EXPECTED_LIFECYCLE_STATES),
        ("failure_behaviors", EXPECTED_FAILURE_BEHAVIORS),
    )
    for field, expected in vocabularies:
        if registry.get(field) != expected:
            raise RuntimePolicyError(f"invalid runtime policy {field}")

    capability_entries = capability_analysis["capabilities"]
    capabilities = {entry["capability"]: entry for entry in capability_entries}
    raw_policies = registry.get("policies")
    if not isinstance(raw_policies, list) or not raw_policies:
        raise RuntimePolicyError("runtime policies must be a nonempty list")

    policies: dict[str, dict[str, object]] = {}
    capability_policies: dict[str, list[str]] = {
        capability: [] for capability in capabilities
    }
    for raw in raw_policies:
        if not isinstance(raw, dict):
            raise RuntimePolicyError("undefined or invalid runtime policy")
        identifier = raw.get("policy_identifier")
        capability = raw.get("governed_capability")
        authority = raw.get("required_authority_level")
        approval = raw.get("approval_requirements")
        constraints = raw.get("execution_constraints")
        lifecycle = raw.get("lifecycle_state")
        eligibility = raw.get("eligibility_requirements")
        failure = raw.get("failure_behavior")
        runtime_states = raw.get("runtime_states")
        if not isinstance(identifier, str) or not identifier:
            raise RuntimePolicyError("undefined or invalid runtime policy")
        if identifier in policies:
            raise RuntimePolicyError(f"duplicate policy identifier: {identifier}")
        if not isinstance(capability, str) or capability not in capabilities:
            raise RuntimePolicyError(
                f"policy references nonexistent capability: {identifier}"
            )
        if authority not in EXPECTED_AUTHORITY_LEVELS:
            raise RuntimePolicyError(f"invalid policy authority: {identifier}")
        if not isinstance(approval, dict):
            raise RuntimePolicyError(f"invalid approval requirements: {identifier}")
        approval_state = approval.get("state")
        approval_authority = approval.get("authority_level")
        if approval_state not in EXPECTED_APPROVAL_STATES:
            raise RuntimePolicyError(f"invalid approval requirements: {identifier}")
        if (
            approval_state == "REQUIRED"
            and approval_authority != authority
        ) or (
            approval_state == "NOT_REQUIRED"
            and approval_authority is not None
        ):
            raise RuntimePolicyError(f"invalid approval requirements: {identifier}")
        if not _ordered_unique_strings(constraints):
            raise RuntimePolicyError(f"invalid execution constraints: {identifier}")
        if lifecycle not in EXPECTED_LIFECYCLE_STATES:
            raise RuntimePolicyError(f"invalid lifecycle state: {identifier}")
        if eligibility != EXPECTED_ELIGIBILITY:
            raise RuntimePolicyError(
                f"inconsistent policy eligibility requirements: {identifier}"
            )
        if failure not in EXPECTED_FAILURE_BEHAVIORS:
            raise RuntimePolicyError(f"invalid failure behavior: {identifier}")
        if not _ordered_unique_strings(runtime_states):
            raise RuntimePolicyError(f"invalid runtime states: {identifier}")
        policies[identifier] = raw
        capability_policies[capability].append(identifier)

    if [item.get("policy_identifier") for item in raw_policies] != sorted(policies):
        raise RuntimePolicyError("runtime policy registry is not deterministically ordered")
    conflicts = {
        capability: assigned
        for capability, assigned in capability_policies.items()
        if len(assigned) > 1
    }
    if conflicts:
        raise RuntimePolicyError(
            "conflicting policy assignments: " + ", ".join(sorted(conflicts))
        )
    orphaned = [
        capability
        for capability, assigned in capability_policies.items()
        if not assigned
    ]
    if orphaned:
        raise RuntimePolicyError(
            "capabilities without governing policies: " + ", ".join(orphaned)
        )

    return {
        "status": "PASS",
        "policy_count": len(policies),
        "capability_count": len(capabilities),
        "policies": [
            {
                **policies[identifier],
                "runtime_layers": capabilities[
                    policies[identifier]["governed_capability"]
                ]["runtime_layers"],
                "interfaces": capabilities[
                    policies[identifier]["governed_capability"]
                ]["interfaces"],
                "consumers": capabilities[
                    policies[identifier]["governed_capability"]
                ]["consumers"],
            }
            for identifier in sorted(policies)
        ],
        "capability_policies": {
            capability: assigned[0]
            for capability, assigned in sorted(capability_policies.items())
        },
    }
