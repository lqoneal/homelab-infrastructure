"""Fail-closed outcome governance for Progressive Runtime execution contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_execution_contracts import (
    REGISTRY_PATH as CONTRACT_REGISTRY_PATH,
    RuntimeExecutionContractError,
    validate as validate_contracts,
)
from scripts.lib.authority_pipeline.progressive_runtime_states import (
    REGISTRY_PATH as STATE_REGISTRY_PATH,
)


class RuntimeOutcomeError(ValueError):
    """The Progressive Runtime outcome contract is violated."""


REGISTRY_PATH = "engineering/architecture/progressive-runtime-outcomes.json"
CLASSIFICATIONS = frozenset({"SUCCESS", "FAILURE", "PARTIAL", "CANCELLED"})
AUTHORIZATION_EFFECTS = frozenset({"ELIGIBLE", "BLOCKED", "TERMINAL"})
LIFECYCLE_EFFECTS = frozenset(
    {
        "NO_PROJECTION_CHANGE",
        "DECISION_AUTHORIZATION_RECORDED",
        "PROJECTION_ELIGIBILITY_RECORDED",
    }
)


def _load(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimeOutcomeError(f"runtime-outcome input is incomplete: {relative}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeOutcomeError(
            f"runtime-outcome input is invalid: {relative}"
        ) from error
    if not isinstance(value, dict):
        raise RuntimeOutcomeError("runtime outcome registry must be an object")
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
    """Prove outcome ownership, state mapping, and downstream traceability."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH)
    contract_path = root / CONTRACT_REGISTRY_PATH
    if not contract_path.is_file():
        raise RuntimeOutcomeError(
            f"runtime-outcome input is incomplete: {CONTRACT_REGISTRY_PATH}"
        )
    digest = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    if registry.get("execution_contract_registry_sha256") != digest:
        raise RuntimeOutcomeError("stale runtime outcome registry metadata")
    try:
        contract_analysis = validate_contracts(root)
    except RuntimeExecutionContractError as error:
        raise RuntimeOutcomeError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimeOutcomeError("unsupported runtime outcome registry schema")
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeOutcomeError("invalid runtime outcome registry model")
    raw_outcomes = registry.get("outcomes")
    if not isinstance(raw_outcomes, list) or not raw_outcomes:
        raise RuntimeOutcomeError("runtime outcomes must be a nonempty list")

    state_registry = _load(root, STATE_REGISTRY_PATH)
    raw_states = state_registry.get("states")
    if not isinstance(raw_states, list):
        raise RuntimeOutcomeError("runtime outcome state input is invalid")
    contracts = {
        item["execution_contract_identifier"]: item
        for item in contract_analysis["contracts"]
    }
    for contract_id, contract in contracts.items():
        if not _ordered_unique_strings(contract.get("runtime_outcome_identifiers")):
            raise RuntimeOutcomeError(
                f"execution contract without runtime outcome: {contract_id}"
            )
    states = {item["state_identifier"]: item for item in raw_states}
    outcomes: dict[str, dict[str, object]] = {}
    contract_outcomes: dict[str, list[str]] = {}

    for raw in raw_outcomes:
        if not isinstance(raw, dict):
            raise RuntimeOutcomeError("undefined or invalid runtime outcome")
        identifier = raw.get("outcome_identifier")
        if not isinstance(identifier, str) or not identifier:
            raise RuntimeOutcomeError("undefined or invalid runtime outcome")
        if identifier in outcomes:
            raise RuntimeOutcomeError(f"duplicate outcome identifier: {identifier}")
        contract_id = raw.get("owning_runtime_execution_contract")
        if contract_id not in contracts:
            raise RuntimeOutcomeError(
                f"outcome references nonexistent execution contract: {identifier}"
            )
        if identifier not in contracts[contract_id].get(
            "runtime_outcome_identifiers", []
        ):
            raise RuntimeOutcomeError(
                f"contract/outcome ownership mismatch: {identifier}"
            )
        if raw.get("outcome_classification") not in CLASSIFICATIONS:
            raise RuntimeOutcomeError(f"invalid outcome classification: {identifier}")
        state_id = raw.get("resulting_runtime_state")
        if not isinstance(state_id, str) or state_id not in states:
            raise RuntimeOutcomeError(
                f"missing or invalid resulting runtime state: {identifier}"
            )
        for field, label in (
            ("required_evidence", "required evidence"),
            ("completion_criteria", "completion criteria"),
            ("invariant_requirements", "invariant requirements"),
        ):
            if not _ordered_unique_strings(raw.get(field)):
                raise RuntimeOutcomeError(f"missing or invalid {label}: {identifier}")
        if raw["invariant_requirements"] != states[state_id]["required_invariants"]:
            raise RuntimeOutcomeError(f"outcome invariant mismatch: {identifier}")
        if raw.get("downstream_authorization_effect") not in AUTHORIZATION_EFFECTS:
            raise RuntimeOutcomeError(
                f"invalid downstream authorization effect: {identifier}"
            )
        if raw.get("lifecycle_projection_effect") not in LIFECYCLE_EFFECTS:
            raise RuntimeOutcomeError(
                f"invalid lifecycle projection effect: {identifier}"
            )

        outcomes[identifier] = raw
        contract_outcomes.setdefault(contract_id, []).append(identifier)

    if [item.get("outcome_identifier") for item in raw_outcomes] != sorted(outcomes):
        raise RuntimeOutcomeError(
            "runtime outcome registry is not deterministically ordered"
        )
    if set(contract_outcomes) != set(contracts):
        raise RuntimeOutcomeError("execution contract without runtime outcome")
    for contract_id, contract in contracts.items():
        declared = contract.get("runtime_outcome_identifiers")
        if declared != contract_outcomes[contract_id]:
            raise RuntimeOutcomeError(
                f"contract/outcome ownership mismatch: {contract_id}"
            )

    return {
        "status": "PASS",
        "outcome_count": len(outcomes),
        "execution_contract_count": len(contracts),
        "outcomes": [outcomes[item] for item in sorted(outcomes)],
        "contract_outcomes": {
            item: contract_outcomes[item] for item in sorted(contract_outcomes)
        },
        "outcome_contracts": {
            item: outcomes[item]["owning_runtime_execution_contract"]
            for item in sorted(outcomes)
        },
        "contracts": contract_analysis["contracts"],
        "contract_transitions": contract_analysis["contract_transitions"],
        "transitions": contract_analysis["transitions"],
        "state_transitions": contract_analysis["state_transitions"],
        "policy_transitions": contract_analysis["policy_transitions"],
    }
