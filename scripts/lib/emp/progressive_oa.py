"""Temporary compatibility interface for Progressive Operational Alpha.

Canonical runtime layers may not import this module.  Existing consumers keep
their public interface while authority operations delegate downward to the
Progressive Runtime Layer.
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.emp.progressive_runtime_support import (
    PACKAGE,
    PACKAGE_PATH,
    ProgressiveOAError,
    _advance_after_acceptance,
    _is_superseded,
    _load_yaml,
    _marker_binding,
    _package,
    _persist_receipt,
    _receipt_digest,
    _resolve_receipt_path,
    _root,
    _validate_receipt_bindings,
    _validate_replay_lifecycle,
    _write_state,
    evidence,
    explain,
    gate,
    gates,
    load_state,
    next_action,
    objective,
    show,
    state_path,
    status,
)


def decide(
    root: Path, gate_id: str, decision: str, operator: str | None, at: str | None
) -> tuple[dict, bool]:
    """Delegate a legacy decision call to canonical Layer 2 authority."""
    from scripts.lib.emp.progressive_gate import (
        ProgressiveGateError,
        ProgressiveGateService,
    )

    try:
        return ProgressiveGateService(root).decide(
            gate_id, decision, operator, at
        )
    except ProgressiveGateError as error:
        raise ProgressiveOAError(str(error)) from error


def verify_receipt(root: Path, gate_id: str) -> dict:
    """Delegate legacy receipt verification to canonical Layer 1 authority."""
    from scripts.lib.emp.progressive_gate import (
        ProgressiveGateError,
        validate_receipt,
    )

    try:
        result = validate_receipt(root, gate_id)
    except ProgressiveGateError as error:
        raise ProgressiveOAError(str(error)) from error
    return {
        "gate_id": result["gate_id"],
        "receipt": result["receipt"],
        "integrity": "PASS",
    }


def controller(root: Path) -> dict:
    """Preserve the legacy controller without making it runtime authority."""
    value = load_state(root)
    active = value["active_gate"]
    if active is None:
        return next_action(root)
    current = value["gates"][active]
    if current["state"] == "PENDING":
        current["state"] = "IMPLEMENTATION_REQUIRED"
        value["status"] = "ACTIVE"
        _write_state(root, value)
    return next_action(root)
