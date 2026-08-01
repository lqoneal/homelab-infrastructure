"""Independent qualification for OA-24 Resume and Idempotent Continuation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .resume_continuation import ContinuationError, ContinuationStore, create_state

OBJECTIVE = "Prove reconstruction from durable state and continuation from the first incomplete operation."
CAPABILITY_ID = "ZEUS-OA-CAP-024"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def qualify(repository: Path) -> dict:
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-24-CAP-024"
    store = ContinuationStore(evidence_dir / "state")
    baseline = "077c9de4db7a76da01b6a4864848aa9bc63e7579"
    state = create_state(
        execution_id="EXEC-OA24-CAP024-QUAL-001", mission_id="OA-24",
        repository=str(repository), baseline=baseline,
        authority="OA-24/SUPERVISED-CONTINUATION", operator="OPERATOR",
        operations=[
            {"operation_id": "OP-001", "sequence": 1, "state": "COMPLETED", "effect_applied": True},
            {"operation_id": "OP-002", "sequence": 2, "state": "INCOMPLETE", "effect_applied": False},
            {"operation_id": "OP-003", "sequence": 3, "state": "PENDING", "effect_applied": False},
        ])
    saved, created = store.save_state(state)
    resumed, resumed_created = store.resume(saved["execution_id"], mission_id="OA-24", baseline=baseline, at="2026-08-01T15:01:00Z")
    replay, replay_created = store.resume(saved["execution_id"], mission_id="OA-24", baseline=baseline, at="2026-08-01T15:01:00Z")
    assertions = {
        "durable_reconstruction": "PASS" if store.load_state(saved["execution_id"]) == saved else "FAIL",
        "first_incomplete_selected": "PASS" if resumed["first_incomplete_operation"] == "OP-002" else "FAIL",
        "no_repeated_completed_effect": "PASS" if resumed["effects_applied"] is False else "FAIL",
        "idempotent_continuation": "PASS" if created and resumed_created and not replay_created and replay == resumed else "FAIL",
        "continuation_is_not_completion": "PASS" if resumed["continuation_status"] == "READY" else "FAIL",
    }
    negative = {}
    for name, kwargs in {
        "mismatched_baseline": {"baseline": "incorrect"},
        "mismatched_mission": {"mission_id": "OA-25"},
    }.items():
        try:
            store.resume(saved["execution_id"], mission_id=kwargs.get("mission_id", "OA-24"), baseline=kwargs.get("baseline", baseline), at="2026-08-01T15:01:00Z")
        except ContinuationError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    assertions["negative_fail_closed"] = "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL"
    result = {"schema_version": 1, "capability_id": CAPABILITY_ID, "mission_id": "OA-24",
              "objective": OBJECTIVE, "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
              "assertions": assertions, "negative_cases": negative,
              "state_digest": saved["record_digest"], "continuation_digest": resumed["record_digest"],
              "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL"}
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-024-QUALIFICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
