"""Fail-closed operational-state governance for Progressive Runtime policies."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_policies import (
    REGISTRY_PATH as POLICY_REGISTRY_PATH,
    RuntimePolicyError,
    validate as validate_policies,
)


class RuntimeStateError(ValueError):
    """The Progressive Runtime operational-state contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-states.json"


def _load(root: Path, relative: str, label: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimeStateError(f"runtime-state input is incomplete: {relative}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeStateError(f"runtime-state input is invalid: {relative}") from error
    if not isinstance(value, dict):
        raise RuntimeStateError(f"{label} must be an object")
    return value


def _ordered_unique_strings(value: object, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item) for item in value)
        and value == sorted(value)
        and len(value) == len(set(value))
    )


def _reject_cycles(
    states: dict[str, dict[str, object]],
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise RuntimeStateError("illegal runtime-state transition cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for successor in states[identifier]["permitted_successor_states"]:
            visit(successor)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(states):
        visit(identifier)


def validate(repository: Path | str) -> dict[str, object]:
    """Prove state reachability, transitions, invariants, and policy ownership."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH, "runtime state registry")
    policy_path = root / POLICY_REGISTRY_PATH
    if not policy_path.is_file():
        raise RuntimeStateError(
            f"runtime-state input is incomplete: {POLICY_REGISTRY_PATH}"
        )
    digest = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    if registry.get("policy_registry_sha256") != digest:
        raise RuntimeStateError("stale runtime-state registry metadata")
    try:
        policy_analysis = validate_policies(root)
    except RuntimePolicyError as error:
        raise RuntimeStateError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimeStateError("unsupported runtime state registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeStateError("invalid runtime state registry model")
    raw_states = registry.get("states")
    if not isinstance(raw_states, list) or not raw_states:
        raise RuntimeStateError("runtime states must be a nonempty list")

    policies = {
        policy["policy_identifier"]: policy for policy in policy_analysis["policies"]
    }
    states: dict[str, dict[str, object]] = {}
    state_policies: dict[str, list[str]] = {}
    for raw in raw_states:
        if not isinstance(raw, dict):
            raise RuntimeStateError("undefined or invalid runtime state")
        identifier = raw.get("state_identifier")
        if not isinstance(identifier, str) or not identifier:
            raise RuntimeStateError("undefined or invalid runtime state")
        if identifier in states:
            raise RuntimeStateError(f"duplicate state identifier: {identifier}")
        for field in (
            "permitted_predecessor_states",
            "permitted_successor_states",
        ):
            if not _ordered_unique_strings(raw.get(field), allow_empty=True):
                raise RuntimeStateError(f"invalid {field}: {identifier}")
        for field in ("entry_conditions", "exit_conditions", "required_invariants"):
            if not _ordered_unique_strings(raw.get(field)):
                raise RuntimeStateError(f"invalid state invariants: {identifier}")
        permitted = raw.get("permitted_runtime_policies")
        if not _ordered_unique_strings(permitted):
            raise RuntimeStateError(f"invalid permitted runtime policies: {identifier}")
        states[identifier] = raw
        state_policies[identifier] = permitted

    if [item.get("state_identifier") for item in raw_states] != sorted(states):
        raise RuntimeStateError("runtime state registry is not deterministically ordered")

    for identifier, state in states.items():
        predecessors = state["permitted_predecessor_states"]
        successors = state["permitted_successor_states"]
        invalid_predecessors = set(predecessors) - states.keys()
        if invalid_predecessors:
            raise RuntimeStateError(
                f"invalid predecessor reference: {identifier}: "
                + ", ".join(sorted(invalid_predecessors))
            )
        invalid_successors = set(successors) - states.keys()
        if invalid_successors:
            raise RuntimeStateError(
                f"invalid successor reference: {identifier}: "
                + ", ".join(sorted(invalid_successors))
            )
    for identifier, state in states.items():
        predecessors = state["permitted_predecessor_states"]
        successors = state["permitted_successor_states"]
        for predecessor in predecessors:
            if identifier not in states[predecessor]["permitted_successor_states"]:
                raise RuntimeStateError(
                    f"invalid transition reciprocity: {predecessor} -> {identifier}"
                )
        for successor in successors:
            if identifier not in states[successor]["permitted_predecessor_states"]:
                raise RuntimeStateError(
                    f"invalid transition reciprocity: {identifier} -> {successor}"
                )
        nonexistent = set(state_policies[identifier]) - policies.keys()
        if nonexistent:
            raise RuntimeStateError(
                f"state references nonexistent policies: {identifier}: "
                + ", ".join(sorted(nonexistent))
            )

    _reject_cycles(states)
    roots = sorted(
        identifier
        for identifier, state in states.items()
        if not state["permitted_predecessor_states"]
    )
    initial_state = registry.get("initial_state")
    if not isinstance(initial_state, str) or initial_state not in states:
        raise RuntimeStateError("undefined runtime initial state")
    if states[initial_state]["permitted_predecessor_states"]:
        raise RuntimeStateError("runtime initial state has predecessors")
    reachable: set[str] = set()
    pending = [initial_state]
    while pending:
        identifier = pending.pop()
        if identifier in reachable:
            continue
        reachable.add(identifier)
        pending.extend(reversed(states[identifier]["permitted_successor_states"]))
    unreachable = set(states) - reachable
    if unreachable:
        raise RuntimeStateError(
            "unreachable runtime states: " + ", ".join(sorted(unreachable))
        )

    policy_states: dict[str, list[str]] = {}
    for identifier, policy in policies.items():
        declared = policy.get("runtime_states")
        if not _ordered_unique_strings(declared):
            raise RuntimeStateError(f"invalid runtime states: {identifier}")
        nonexistent = set(declared) - states.keys()
        if nonexistent:
            raise RuntimeStateError(
                f"policy references nonexistent states: {identifier}: "
                + ", ".join(sorted(nonexistent))
            )
        reciprocal = sorted(
            state
            for state, permitted in state_policies.items()
            if identifier in permitted
        )
        if declared != reciprocal:
            raise RuntimeStateError(f"policy/state mismatch: {identifier}")
        policy_states[identifier] = declared

    return {
        "status": "PASS",
        "state_count": len(states),
        "policy_count": len(policies),
        "initial_state": initial_state,
        "states": [
            {
                **states[identifier],
                "policies": [
                    policies[policy] for policy in state_policies[identifier]
                ],
            }
            for identifier in sorted(states)
        ],
        "policy_states": {
            policy: states_for_policy
            for policy, states_for_policy in sorted(policy_states.items())
        },
        "transitions": [
            {"predecessor": identifier, "successor": successor}
            for identifier in sorted(states)
            for successor in states[identifier]["permitted_successor_states"]
        ],
    }


def validate_execution_eligibility(
    repository: Path | str, policy_identifier: str, state_identifier: str
) -> dict[str, str]:
    """Fail closed unless the policy is authorized in the supplied state."""
    analysis = validate(repository)
    if policy_identifier not in analysis["policy_states"]:
        raise RuntimeStateError(f"undefined runtime policy: {policy_identifier}")
    if state_identifier not in {
        state["state_identifier"] for state in analysis["states"]
    }:
        raise RuntimeStateError(f"undefined runtime state: {state_identifier}")
    if state_identifier not in analysis["policy_states"][policy_identifier]:
        raise RuntimeStateError(
            f"execution outside authorized states: {policy_identifier}: "
            f"{state_identifier}"
        )
    return {
        "status": "AUTHORIZED",
        "policy_identifier": policy_identifier,
        "state_identifier": state_identifier,
    }
