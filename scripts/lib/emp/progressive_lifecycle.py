"""Read-only lifecycle projections over canonical Progressive authority."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib.emp.progressive_gate import (
    ProgressiveGateError,
    ProgressiveGateService,
)


class ProgressiveLifecycleError(ValueError):
    """Canonical Progressive state cannot produce a coherent projection."""


@dataclass(frozen=True)
class LifecycleProjection:
    package_id: str
    repository: str
    gate_id: str
    current_gate: str | None
    gate_state: str
    verification_state: str
    predecessor_state: str
    receipt_state: str
    receipt: str | None
    lifecycle_state: str
    next_action: str

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _lifecycle_state(gate_state: str, verification_state: str) -> str:
    if gate_state == "ACCEPTED":
        return "ACCEPTED"
    if gate_state == "REJECTED":
        return "REJECTED"
    if verification_state == "VERIFIED":
        return "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE"
    if gate_state in {"FAILED", "INTERRUPTED"}:
        return "BLOCKED"
    return "AWAITING_VERIFICATION"


def _next_action(gate_id: str, lifecycle_state: str) -> str:
    if lifecycle_state == "ACCEPTED":
        return "COMPLETE"
    if lifecycle_state == "REJECTED":
        return f"CORRECT_OR_RECOVER_{gate_id}"
    if lifecycle_state == "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE":
        return f"DECIDE_{gate_id}"
    if lifecycle_state == "BLOCKED":
        return f"CORRECT_OR_RECOVER_{gate_id}"
    return f"VERIFY_{gate_id}"


class ProgressiveLifecycleProjector:
    """Project lifecycle state without owning verification or decisions."""

    def __init__(
        self,
        root: Path | str,
        service: ProgressiveGateService | None = None,
    ):
        self.service = service or ProgressiveGateService(root)

    def project(self, gate_id: str) -> dict[str, Any]:
        try:
            state = self.service.gate_state(gate_id)
        except ProgressiveGateError as error:
            raise ProgressiveLifecycleError(str(error)) from error

        gate_state = state["gate_state"]
        verification_state = state["verification_state"]
        receipt_state = state["receipt_state"]
        receipt = state["receipt"]
        if gate_state == "ACCEPTED":
            if receipt_state != "VALID" or not receipt:
                raise ProgressiveLifecycleError(
                    "accepted lifecycle has no canonical valid receipt"
                )
        elif receipt_state != "ABSENT" or receipt is not None:
            raise ProgressiveLifecycleError(
                "non-accepted lifecycle selects an acceptance receipt"
            )

        lifecycle_state = _lifecycle_state(gate_state, verification_state)
        return LifecycleProjection(
            package_id=state["package_id"],
            repository=state["repository"],
            gate_id=state["gate_id"],
            current_gate=state["current_gate"],
            gate_state=gate_state,
            verification_state=verification_state,
            predecessor_state=state["predecessor_state"],
            receipt_state=receipt_state,
            receipt=receipt,
            lifecycle_state=lifecycle_state,
            next_action=_next_action(state["gate_id"], lifecycle_state),
        ).as_dict()


def project(root: Path | str, gate_id: str) -> dict[str, Any]:
    """Convenience projection entry point for compatibility consumers."""
    return ProgressiveLifecycleProjector(root).project(gate_id)
