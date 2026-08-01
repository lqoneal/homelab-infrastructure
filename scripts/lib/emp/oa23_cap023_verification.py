"""Independent qualification for OA-23 Safe Interruption."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .safe_interruption import PauseStore, SafeInterruptionError, authorize_pause, observe

OBJECTIVE = "Prove durable pause behavior without inferred completion or duplicated effects."
CAPABILITY_ID = "ZEUS-OA-CAP-023"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def qualify(repository: Path) -> dict:
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-23-CAP-023"
    store = PauseStore(evidence_dir / "pauses")
    record = authorize_pause(
        request_id="PAUSE-OA23-CAP023-QUAL-001", mission_id="OA-23",
        target="bounded-operation-001", repository=str(repository),
        baseline="b740920d7f472f2d213b3b9c10c515dc25f605e2",
        authority="OA-23/SUPERVISED-PAUSE", operator="OPERATOR", authorized=True,
        requested_at="2026-08-01T13:00:00Z", expires_at="2026-08-01T14:00:00Z",
        at="2026-08-01T13:01:00Z")
    saved, created = store.save(record)
    replay, replay_created = store.save(record)
    observation = observe(saved, at="2026-08-01T13:02:00Z")
    assertions = {
        "durable_pause": "PASS" if saved["state"] == "PAUSED" else "FAIL",
        "no_inferred_completion": "PASS" if not saved["completion_inferred"] else "FAIL",
        "no_duplicate_effects": "PASS" if not saved["effects_applied"] and not saved["duplicate_effects"] else "FAIL",
        "explicit_authorization": "PASS" if saved["authority"] and saved["operator"] else "FAIL",
        "replay_idempotency": "PASS" if created and not replay_created and replay == saved else "FAIL",
        "durable_recovery": "PASS" if store.load(saved["request_id"]) == saved else "FAIL",
        "bounded_observation": "PASS" if observation["telemetry_only"] and not observation["completion_inferred"] else "FAIL",
    }
    negative = {}
    cases = {
        "unauthorized": {"authorized": False},
        "stale": {"at": "2026-08-01T15:00:00Z"},
        "mismatched_mission": {"mission_id": "OA-24"},
    }
    for name, overrides in cases.items():
        values = dict(request_id="NEGATIVE-" + name, mission_id="OA-23", target="bounded-operation-001",
                      repository=str(repository), baseline="b740920d7f472f2d213b3b9c10c515dc25f605e2",
                      authority="OA-23/SUPERVISED-PAUSE", operator="OPERATOR", authorized=True,
                      requested_at="2026-08-01T13:00:00Z", expires_at="2026-08-01T14:00:00Z",
                      at="2026-08-01T13:01:00Z")
        values.update(overrides)
        try:
            authorize_pause(**values)
        except SafeInterruptionError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    assertions["negative_fail_closed"] = "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL"
    result = {"schema_version": 1, "capability_id": CAPABILITY_ID, "mission_id": "OA-23",
              "objective": OBJECTIVE, "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
              "assertions": assertions, "negative_cases": negative, "record_digest": saved["record_digest"],
              "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL"}
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-023-QUALIFICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
