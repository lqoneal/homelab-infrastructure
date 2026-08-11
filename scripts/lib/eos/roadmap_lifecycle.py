"""Generic fail-closed executable-roadmap lifecycle model.

This module contains lifecycle semantics only. It performs no filesystem
mutation, EOS synchronization, publication, git operation, or successor work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LifecycleError(RuntimeError):
    """Fail-closed lifecycle contract violation."""


class LifecycleState(str, Enum):
    PENDING = "PENDING"
    CURRENT = "CURRENT"
    RESULT_RECORDED = "RESULT_RECORDED"
    AWAITING_OPERATOR_REVIEW = "AWAITING_OPERATOR_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class ResultClass(str, Enum):
    ABSENT = "ABSENT"
    INVALID = "INVALID"
    NONFINAL = "NONFINAL"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    VALID_FINAL = "VALID_FINAL"


class OperatorDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ResultFacts:
    exists: bool
    identity_valid: bool = False
    schema_valid: bool = False
    evidence_valid: bool = False
    final: bool = False
    stale: bool = False
    conflicting: bool = False


@dataclass(frozen=True)
class ReviewBinding:
    roadmap_id: str
    roadmap_version: str
    gate_id: str
    gate_definition_digest: str
    result_digest: str
    operator_identity: str
    transaction_id: str


@dataclass(frozen=True)
class AdvancementBinding:
    roadmap_id: str
    roadmap_version: str
    gate_id: str
    gate_definition_digest: str
    result_digest: str
    acceptance_receipt_id: str
    acceptance_receipt_digest: str
    transaction_id: str


ALLOWED_TRANSITIONS = frozenset({
    (LifecycleState.PENDING, LifecycleState.CURRENT),
    (LifecycleState.CURRENT, LifecycleState.RESULT_RECORDED),
    (
        LifecycleState.RESULT_RECORDED,
        LifecycleState.AWAITING_OPERATOR_REVIEW,
    ),
    (
        LifecycleState.AWAITING_OPERATOR_REVIEW,
        LifecycleState.ACCEPTED,
    ),
    (
        LifecycleState.AWAITING_OPERATOR_REVIEW,
        LifecycleState.REJECTED,
    ),
    (LifecycleState.ACCEPTED, LifecycleState.COMPLETED),
})


def classify_result(facts: ResultFacts) -> ResultClass:
    if not facts.exists:
        return ResultClass.ABSENT

    if facts.conflicting:
        return ResultClass.CONFLICTING

    if facts.stale:
        return ResultClass.STALE

    if not (
        facts.identity_valid
        and facts.schema_valid
        and facts.evidence_valid
    ):
        return ResultClass.INVALID

    if not facts.final:
        return ResultClass.NONFINAL

    return ResultClass.VALID_FINAL


def require_transition(
    current: LifecycleState,
    target: LifecycleState,
) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise LifecycleError(
            f"forbidden lifecycle transition: {current.value}->{target.value}"
        )


def result_recorded_transition(
    current: LifecycleState,
    result_class: ResultClass,
) -> LifecycleState:
    if current is not LifecycleState.CURRENT:
        raise LifecycleError(
            "result may be recorded only for CURRENT gate"
        )

    if result_class is not ResultClass.VALID_FINAL:
        raise LifecycleError(
            f"result not reviewable: {result_class.value}"
        )

    require_transition(
        current,
        LifecycleState.RESULT_RECORDED,
    )

    return LifecycleState.RESULT_RECORDED


def pending_review_transition(
    current: LifecycleState,
    result_class: ResultClass,
) -> LifecycleState:
    if result_class is not ResultClass.VALID_FINAL:
        raise LifecycleError(
            "only VALID_FINAL result may enter operator review"
        )

    require_transition(
        current,
        LifecycleState.AWAITING_OPERATOR_REVIEW,
    )

    return LifecycleState.AWAITING_OPERATOR_REVIEW


def apply_operator_decision(
    current: LifecycleState,
    result_class: ResultClass,
    decision: OperatorDecision,
    binding: ReviewBinding,
) -> LifecycleState:
    if current is not LifecycleState.AWAITING_OPERATOR_REVIEW:
        raise LifecycleError(
            "operator decision requires AWAITING_OPERATOR_REVIEW"
        )

    if result_class is not ResultClass.VALID_FINAL:
        raise LifecycleError(
            "operator decision requires VALID_FINAL result"
        )

    _require_review_binding(binding)

    target = (
        LifecycleState.ACCEPTED
        if decision is OperatorDecision.ACCEPT
        else LifecycleState.REJECTED
    )

    require_transition(current, target)

    return target


def complete_accepted_gate(
    current: LifecycleState,
    binding: AdvancementBinding,
    *,
    successor_gate: Optional[str],
    terminal: bool,
) -> tuple[LifecycleState, Optional[str]]:
    if current is not LifecycleState.ACCEPTED:
        raise LifecycleError(
            "only ACCEPTED gate may advance to COMPLETED"
        )

    _require_advancement_binding(binding)

    if terminal and successor_gate is not None:
        raise LifecycleError(
            "terminal advancement cannot fabricate successor"
        )

    if not terminal and not successor_gate:
        raise LifecycleError(
            "nonterminal advancement requires deterministic successor"
        )

    require_transition(
        current,
        LifecycleState.COMPLETED,
    )

    return LifecycleState.COMPLETED, successor_gate


def classify_replay(
    *,
    transaction_id_matches: bool,
    gate_matches: bool,
    result_matches: bool,
    receipt_matches: bool,
    pre_state_matches: bool,
    committed: bool,
) -> str:
    if not transaction_id_matches:
        return "NEW_TRANSACTION"

    if not all((
        gate_matches,
        result_matches,
        receipt_matches,
        pre_state_matches,
    )):
        raise LifecycleError(
            "conflicting replay identity"
        )

    return (
        "ALREADY_APPLIED"
        if committed
        else "RESUME_EXACT_TRANSACTION"
    )


def _require_nonempty(
    name: str,
    value: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LifecycleError(
            f"missing required binding: {name}"
        )


def _require_review_binding(
    binding: ReviewBinding,
) -> None:
    for name in (
        "roadmap_id",
        "roadmap_version",
        "gate_id",
        "gate_definition_digest",
        "result_digest",
        "operator_identity",
        "transaction_id",
    ):
        _require_nonempty(
            name,
            getattr(binding, name),
        )


def _require_advancement_binding(
    binding: AdvancementBinding,
) -> None:
    for name in (
        "roadmap_id",
        "roadmap_version",
        "gate_id",
        "gate_definition_digest",
        "result_digest",
        "acceptance_receipt_id",
        "acceptance_receipt_digest",
        "transaction_id",
    ):
        _require_nonempty(
            name,
            getattr(binding, name),
        )
