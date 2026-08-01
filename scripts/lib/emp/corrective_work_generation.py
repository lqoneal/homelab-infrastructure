"""CAP-022 bounded corrective-work generation.

Generation is deliberately downstream of the CAP-021 authorization boundary.
This module creates an auditable proposal only; it never dispatches, applies,
or executes corrective work.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from .corrective_work_authorization import CorrectiveAuthorizationError, digest, validate


class CorrectiveWorkGenerationError(ValueError):
    """The corrective-work proposal is invalid or replay-inconsistent."""


MAX_OBJECTIVE_BYTES = 2048
MAX_RECORDS = 32


def generate(*, request_record: dict[str, Any], authorization_receipt: dict[str, Any],
             proposal_id: str, trigger: str, bounded_objective: str,
             affected_records: list[str], at: str) -> dict[str, Any]:
    """Create a deterministic, bounded proposal after CAP-021 authorization."""
    if not proposal_id or not trigger or not bounded_objective:
        raise CorrectiveWorkGenerationError("proposal identity and objective are required")
    if len(bounded_objective.encode("utf-8")) > MAX_OBJECTIVE_BYTES:
        raise CorrectiveWorkGenerationError("bounded corrective objective is too large")
    if not isinstance(affected_records, list) or not affected_records:
        raise CorrectiveWorkGenerationError("affected records are required")
    if len(affected_records) > MAX_RECORDS or len(set(affected_records)) != len(affected_records):
        raise CorrectiveWorkGenerationError("affected records exceed bounded contract")
    try:
        authorization = validate(request_record, authorization_receipt, at=at)
    except CorrectiveAuthorizationError as error:
        raise CorrectiveWorkGenerationError(str(error)) from error
    unsigned = {
        "schema_version": 1,
        "proposal_type": "ZEUS_CORRECTIVE_WORK_PROPOSAL",
        "proposal_id": proposal_id,
        "mission_id": authorization["mission_id"],
        "wop_id": authorization["wop_id"],
        "repository": authorization["repository"],
        "baseline": authorization["baseline"],
        "authority": authorization["authority"],
        "authorization_id": authorization["authorization_id"],
        "authorization_receipt_digest": authorization["receipt_digest"],
        "trigger": trigger,
        "bounded_objective": bounded_objective,
        "affected_records": list(affected_records),
        "created_at": at,
        "state": "PROPOSED",
        "corrective_work_generated": True,
        "dispatched": False,
        "executed": False,
        "prohibited_effects": ["dispatch", "execution", "acceptance_inference", "later_gate_execution"],
    }
    return {**unsigned, "proposal_digest": digest(unsigned)}


class CorrectiveWorkStore:
    """Atomic durable proposal store with identical replay acceptance."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self, proposal_id: str) -> dict[str, Any]:
        try:
            value = json.loads((self.path / f"{proposal_id}.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CorrectiveWorkGenerationError("proposal record is unavailable") from error
        supplied = value.pop("record_digest", None)
        if supplied != digest(value):
            raise CorrectiveWorkGenerationError("proposal record digest mismatch")
        value["record_digest"] = supplied
        return value

    def save(self, proposal: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        data = deepcopy(proposal)
        data.pop("record_digest", None)
        data["record_digest"] = digest(data)
        self.path.mkdir(parents=True, exist_ok=True)
        target = self.path / f"{data['proposal_id']}.json"
        if target.is_file():
            existing = self.load(data["proposal_id"])
            if existing != data:
                raise CorrectiveWorkGenerationError("proposal replay diverged")
            return existing, False
        temporary = target.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return data, True
