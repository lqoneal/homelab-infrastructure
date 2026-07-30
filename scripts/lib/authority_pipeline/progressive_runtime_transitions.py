"""Fail-closed transition governance for Progressive Runtime states."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_states import (
    REGISTRY_PATH as STATE_REGISTRY_PATH,
    RuntimeStateError,
    validate as validate_states,
)


class RuntimeTransitionError(ValueError):
    """The Progressive Runtime transition contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-transitions.json"
EXPECTED_APPROVAL_STATES = ["NOT_REQUIRED", "REQUIRED"]
EXPECTED_ROLLBACK_MODES = ["RETURN_TO_SOURCE_STATE"]


def _load(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimeTransitionError(
            f"runtime-transition input is incomplete: {relative}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeTransitionError(
            f"runtime-transition input is invalid: {relative}"
        ) from error
    if not isinstance(value, dict):
        raise RuntimeTransitionError("runtime transition registry must be an object")
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
    """Prove canonical edge ownership and transition-to-consumer traceability."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH)
    state_path = root / STATE_REGISTRY_PATH
    if not state_path.is_file():
        raise RuntimeTransitionError(
            f"runtime-transition input is incomplete: {STATE_REGISTRY_PATH}"
        )
    digest = hashlib.sha256(state_path.read_bytes()).hexdigest()
    if registry.get("state_registry_sha256") != digest:
        raise RuntimeTransitionError("stale runtime transition registry metadata")
    try:
        state_analysis = validate_states(root)
    except RuntimeStateError as error:
        raise RuntimeTransitionError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimeTransitionError("unsupported runtime transition registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeTransitionError("invalid runtime transition registry model")
    raw_transitions = registry.get("transitions")
    if not isinstance(raw_transitions, list) or not raw_transitions:
        raise RuntimeTransitionError("runtime transitions must be a nonempty list")

    states = {
        state["state_identifier"]: state for state in state_analysis["states"]
    }
    policies = {
        policy["policy_identifier"]: policy
        for state in state_analysis["states"]
        for policy in state["policies"]
    }
    graph_edges = {
        (edge["predecessor"], edge["successor"])
        for edge in state_analysis["transitions"]
    }
    transitions: dict[str, dict[str, object]] = {}
    owned_edges: dict[tuple[str, str], list[str]] = {}

    for raw in raw_transitions:
        if not isinstance(raw, dict):
            raise RuntimeTransitionError("undefined or invalid runtime transition")
        identifier = raw.get("transition_identifier")
        if not isinstance(identifier, str) or not identifier:
            raise RuntimeTransitionError("undefined or invalid runtime transition")
        if identifier in transitions:
            raise RuntimeTransitionError(
                f"duplicate transition identifier: {identifier}"
            )
        source = raw.get("source_runtime_state")
        destination = raw.get("destination_runtime_state")
        if source not in states or destination not in states:
            raise RuntimeTransitionError(
                f"transition references nonexistent runtime state: {identifier}"
            )
        edge = (source, destination)
        if edge not in graph_edges:
            raise RuntimeTransitionError(
                f"transition violates runtime state graph: {identifier}"
            )
        for field, label in (
            ("governing_runtime_policies", "governing runtime policies"),
            ("guard_conditions", "guard conditions"),
            ("required_evidence", "required evidence"),
            ("transition_invariants", "transition invariants"),
        ):
            if not _ordered_unique_strings(raw.get(field)):
                raise RuntimeTransitionError(f"missing or invalid {label}: {identifier}")

        governing = raw["governing_runtime_policies"]
        if set(governing) != {
            policy["policy_identifier"] for policy in states[destination]["policies"]
        }:
            raise RuntimeTransitionError(
                f"transition/state policy ownership mismatch: {identifier}"
            )
        if set(governing) - policies.keys():
            raise RuntimeTransitionError(
                f"transition references nonexistent runtime policy: {identifier}"
            )
        required_guards = set(states[source]["exit_conditions"]) | set(
            states[destination]["entry_conditions"]
        )
        if not required_guards.issubset(raw["guard_conditions"]):
            raise RuntimeTransitionError(
                f"transition guard conditions violate state contract: {identifier}"
            )

        approval = raw.get("approval_requirements")
        if not isinstance(approval, dict):
            raise RuntimeTransitionError(
                f"missing or invalid approval requirements: {identifier}"
            )
        approval_state = approval.get("state")
        approval_authority = approval.get("authority_level")
        required_authorities = sorted(
            {
                policy["approval_requirements"]["authority_level"]
                for policy in (policies[item] for item in governing)
                if policy["approval_requirements"]["state"] == "REQUIRED"
            }
        )
        expected_state = "REQUIRED" if required_authorities else "NOT_REQUIRED"
        expected_authority = (
            required_authorities[0] if len(required_authorities) == 1 else None
        )
        if (
            approval_state not in EXPECTED_APPROVAL_STATES
            or approval_state != expected_state
            or approval_authority != expected_authority
        ):
            raise RuntimeTransitionError(
                f"invalid approval requirements: {identifier}"
            )

        rollback = raw.get("rollback_behavior")
        if (
            not isinstance(rollback, dict)
            or rollback.get("mode") not in EXPECTED_ROLLBACK_MODES
            or not _ordered_unique_strings(rollback.get("conditions"))
        ):
            raise RuntimeTransitionError(
                f"missing or invalid rollback definition: {identifier}"
            )
        expected_invariants = sorted(
            set(states[source]["required_invariants"])
            & set(states[destination]["required_invariants"])
        )
        if raw["transition_invariants"] != expected_invariants:
            raise RuntimeTransitionError(
                f"transition invariant violation: {identifier}"
            )
        transitions[identifier] = raw
        owned_edges.setdefault(edge, []).append(identifier)

    if [
        item.get("transition_identifier") for item in raw_transitions
    ] != sorted(transitions):
        raise RuntimeTransitionError(
            "runtime transition registry is not deterministically ordered"
        )
    missing = graph_edges - owned_edges.keys()
    duplicate_edges = {
        edge: owners for edge, owners in owned_edges.items() if len(owners) != 1
    }
    if missing:
        raise RuntimeTransitionError("undefined runtime state transition")
    if duplicate_edges:
        raise RuntimeTransitionError("runtime state transition has multiple owners")

    state_transitions = {
        state: sorted(
            identifier
            for identifier, transition in transitions.items()
            if state
            in (
                transition["source_runtime_state"],
                transition["destination_runtime_state"],
            )
        )
        for state in sorted(states)
    }
    policy_transitions = {
        policy: sorted(
            identifier
            for identifier, transition in transitions.items()
            if policy in transition["governing_runtime_policies"]
        )
        for policy in sorted(policies)
    }
    return {
        "status": "PASS",
        "transition_count": len(transitions),
        "state_count": len(states),
        "policy_count": len(policies),
        "transitions": [
            {
                **transitions[identifier],
                "destination_policies": states[
                    transitions[identifier]["destination_runtime_state"]
                ]["policies"],
            }
            for identifier in sorted(transitions)
        ],
        "state_transitions": state_transitions,
        "policy_transitions": policy_transitions,
    }
