"""Fail-closed execution-contract governance for Progressive Runtime transitions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.lib.authority_pipeline.progressive_runtime_transitions import (
    REGISTRY_PATH as TRANSITION_REGISTRY_PATH,
    RuntimeTransitionError,
    validate as validate_transitions,
)


class RuntimeExecutionContractError(ValueError):
    """The Progressive Runtime execution contract is violated."""


REGISTRY_PATH = (
    "engineering/architecture/progressive-runtime-execution-contracts.json"
)
CANONICAL_PHASES = [
    "PREPARE",
    "VERIFY_PRECONDITIONS",
    "EXECUTE",
    "COLLECT_EVIDENCE",
    "VERIFY_COMPLETION",
    "FINALIZE",
]


def _load(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    if not path.is_file():
        raise RuntimeExecutionContractError(
            f"runtime-execution-contract input is incomplete: {relative}"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeExecutionContractError(
            f"runtime-execution-contract input is invalid: {relative}"
        ) from error
    if not isinstance(value, dict):
        raise RuntimeExecutionContractError(
            "runtime execution contract registry must be an object"
        )
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
    """Prove execution-contract ownership and downstream traceability."""
    root = Path(repository).resolve()
    registry = _load(root, REGISTRY_PATH)
    transition_path = root / TRANSITION_REGISTRY_PATH
    if not transition_path.is_file():
        raise RuntimeExecutionContractError(
            f"runtime-execution-contract input is incomplete: {TRANSITION_REGISTRY_PATH}"
        )
    digest = hashlib.sha256(transition_path.read_bytes()).hexdigest()
    if registry.get("transition_registry_sha256") != digest:
        raise RuntimeExecutionContractError(
            "stale runtime execution contract registry metadata"
        )
    try:
        transition_analysis = validate_transitions(root)
    except RuntimeTransitionError as error:
        raise RuntimeExecutionContractError(str(error)) from error

    if registry.get("schema_version") != 1:
        raise RuntimeExecutionContractError(
            "unsupported runtime execution contract registry schema"
        )
    if registry.get("runtime_model") != "Progressive Runtime Layer":
        raise RuntimeExecutionContractError(
            "invalid runtime execution contract registry model"
        )
    raw_contracts = registry.get("execution_contracts")
    if not isinstance(raw_contracts, list) or not raw_contracts:
        raise RuntimeExecutionContractError(
            "runtime execution contracts must be a nonempty list"
        )

    transitions = {
        item["transition_identifier"]: item
        for item in transition_analysis["transitions"]
    }
    contracts: dict[str, dict[str, object]] = {}
    transition_owners: dict[str, list[str]] = {}

    for raw in raw_contracts:
        if not isinstance(raw, dict):
            raise RuntimeExecutionContractError(
                "undefined or invalid runtime execution contract"
            )
        identifier = raw.get("execution_contract_identifier")
        if not isinstance(identifier, str) or not identifier:
            raise RuntimeExecutionContractError(
                "undefined or invalid runtime execution contract"
            )
        if identifier in contracts:
            raise RuntimeExecutionContractError(
                f"duplicate execution contract identifier: {identifier}"
            )
        transition_id = raw.get("owning_runtime_transition")
        if transition_id not in transitions:
            raise RuntimeExecutionContractError(
                f"contract references nonexistent runtime transition: {identifier}"
            )
        if transitions[transition_id].get("execution_contract_identifier") != identifier:
            raise RuntimeExecutionContractError(
                f"transition/execution-contract ownership mismatch: {identifier}"
            )
        if raw.get("execution_phases") != CANONICAL_PHASES:
            raise RuntimeExecutionContractError(
                f"missing or invalid execution phases: {identifier}"
            )
        if not _ordered_unique_strings(raw.get("execution_preconditions")):
            raise RuntimeExecutionContractError(
                f"missing or invalid execution preconditions: {identifier}"
            )

        checkpoints = raw.get("execution_checkpoints")
        if not isinstance(checkpoints, list) or not checkpoints:
            raise RuntimeExecutionContractError(
                f"missing execution checkpoints: {identifier}"
            )
        checkpoint_ids: list[str] = []
        checkpoint_evidence: set[str] = set()
        for order, checkpoint in enumerate(checkpoints, start=1):
            if not isinstance(checkpoint, dict):
                raise RuntimeExecutionContractError(
                    f"invalid execution checkpoint: {identifier}"
                )
            checkpoint_id = checkpoint.get("checkpoint_identifier")
            if (
                not isinstance(checkpoint_id, str)
                or not checkpoint_id
                or checkpoint_id in checkpoint_ids
                or checkpoint.get("order") != order
                or checkpoint.get("phase") not in CANONICAL_PHASES
                or not _ordered_unique_strings(checkpoint.get("required_evidence"))
            ):
                raise RuntimeExecutionContractError(
                    f"invalid execution checkpoint: {identifier}"
                )
            checkpoint_ids.append(checkpoint_id)
            checkpoint_evidence.update(checkpoint["required_evidence"])
        if checkpoint_ids != sorted(checkpoint_ids):
            raise RuntimeExecutionContractError(
                f"execution checkpoints are not deterministic: {identifier}"
            )

        evidence = raw.get("required_evidence")
        if not _ordered_unique_strings(evidence) or set(evidence) != checkpoint_evidence:
            raise RuntimeExecutionContractError(
                f"missing or invalid required evidence: {identifier}"
            )
        if set(evidence) != set(transitions[transition_id]["required_evidence"]):
            raise RuntimeExecutionContractError(
                f"transition/execution-contract evidence mismatch: {identifier}"
            )

        interruption = raw.get("interruption_behavior")
        if not isinstance(interruption, dict):
            raise RuntimeExecutionContractError(
                f"missing interruption behavior: {identifier}"
            )
        interruptible = interruption.get("interruptible_phases")
        if (
            not isinstance(interruptible, list)
            or not interruptible
            or len(interruptible) != len(set(interruptible))
            or any(phase not in CANONICAL_PHASES for phase in interruptible)
            or interruptible
            != sorted(interruptible, key=CANONICAL_PHASES.index)
            or interruption.get("restart_phase") not in CANONICAL_PHASES
            or not _ordered_unique_strings(interruption.get("interruption_evidence"))
        ):
            raise RuntimeExecutionContractError(
                f"missing or invalid interruption behavior: {identifier}"
            )

        resume = raw.get("resume_behavior")
        if (
            not isinstance(resume, dict)
            or resume.get("resume_phase") != interruption.get("restart_phase")
            or not _ordered_unique_strings(resume.get("resume_prerequisites"))
        ):
            raise RuntimeExecutionContractError(
                f"missing or invalid resume behavior: {identifier}"
            )
        for field, label in (
            ("completion_criteria", "completion criteria"),
            ("failure_criteria", "failure criteria"),
        ):
            if not _ordered_unique_strings(raw.get(field)):
                raise RuntimeExecutionContractError(
                    f"missing or invalid {label}: {identifier}"
                )

        rollback_triggers = raw.get("rollback_triggers")
        if not isinstance(rollback_triggers, list) or not rollback_triggers:
            raise RuntimeExecutionContractError(
                f"missing rollback triggers: {identifier}"
            )
        trigger_names: list[str] = []
        for trigger in rollback_triggers:
            if (
                not isinstance(trigger, dict)
                or not isinstance(trigger.get("trigger"), str)
                or not trigger.get("trigger")
                or trigger.get("trigger") in trigger_names
                or trigger.get("rollback_checkpoint") not in checkpoint_ids
                or not _ordered_unique_strings(
                    trigger.get("rollback_completion_criteria")
                )
            ):
                raise RuntimeExecutionContractError(
                    f"missing or invalid rollback triggers: {identifier}"
                )
            trigger_names.append(trigger["trigger"])
        if trigger_names != sorted(trigger_names):
            raise RuntimeExecutionContractError(
                f"rollback triggers are not deterministic: {identifier}"
            )
        expected_triggers = transitions[transition_id]["rollback_behavior"]["conditions"]
        if trigger_names != expected_triggers:
            raise RuntimeExecutionContractError(
                f"transition/execution-contract rollback mismatch: {identifier}"
            )

        contracts[identifier] = raw
        transition_owners.setdefault(transition_id, []).append(identifier)

    if [
        item.get("execution_contract_identifier") for item in raw_contracts
    ] != sorted(contracts):
        raise RuntimeExecutionContractError(
            "runtime execution contract registry is not deterministically ordered"
        )
    if set(transition_owners) != set(transitions):
        raise RuntimeExecutionContractError("runtime transition without execution contract")
    if any(len(owners) != 1 for owners in transition_owners.values()):
        raise RuntimeExecutionContractError(
            "runtime transition has multiple execution contracts"
        )

    return {
        "status": "PASS",
        "execution_contract_count": len(contracts),
        "transition_count": len(transitions),
        "contracts": [contracts[item] for item in sorted(contracts)],
        "transition_contracts": {
            item: transition_owners[item][0] for item in sorted(transition_owners)
        },
        "contract_transitions": {
            item: contracts[item]["owning_runtime_transition"]
            for item in sorted(contracts)
        },
        "transitions": transition_analysis["transitions"],
        "state_transitions": transition_analysis["state_transitions"],
        "policy_transitions": transition_analysis["policy_transitions"],
    }
