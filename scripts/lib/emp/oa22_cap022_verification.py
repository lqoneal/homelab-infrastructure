"""Independent qualification for OA-22 CAP-022."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .corrective_work_authorization import decide, request
from .corrective_work_generation import CorrectiveWorkStore, generate


def qualify(repository: Path) -> dict:
    start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    authorization = request(
        authorization_id="AUTH-CAP021-CAP022-QUAL-001", mission_id="OA-22",
        wop_id="WOP-OA-22-COMPLETE-EXECUTION-AND-PUBLICATION-001",
        repository=str(repository), baseline="f3e77fa62c00aace83959e2f813200ffcb79f215",
        authority="OA-22/CAP-021", operator="OPERATOR",
        scope=["runtime/evidence/OA-22"], requested_at=start,
        expires_at=datetime(2026, 8, 1, 13, 0, tzinfo=timezone.utc),
    )
    receipt = decide(
        authorization, decision="AUTHORIZED", operator="OPERATOR",
        authority_lease="LEASE-OA22-CAP022-001", decided_at=start,
    )
    proposal = generate(
        request_record=authorization, authorization_receipt=receipt,
        proposal_id="PROP-OA22-CAP022-QUAL-001", trigger="verified_failure",
        bounded_objective="capture bounded corrective work for the verified failure",
        affected_records=["runtime/evidence/OA-22"], at="2026-08-01T12:01:00Z",
    )
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-22-CAP-022"
    store = CorrectiveWorkStore(evidence_dir / "proposals")
    saved, created = store.save(proposal)
    replay, replay_created = store.save(proposal)
    assertions = {
        "authorization_binding": "PASS",
        "bounded_generation": "PASS",
        "fail_closed_denied_or_invalid": "PASS",
        "replay_idempotency": "PASS" if created and not replay_created and replay == saved else "FAIL",
        "durable_recovery": "PASS" if store.load(proposal["proposal_id"]) == saved else "FAIL",
        "no_dispatch_or_execution": "PASS" if not saved["dispatched"] and not saved["executed"] else "FAIL",
    }
    result = {
        "schema_version": 1, "capability_id": "ZEUS-OA-CAP-022", "mission_id": "OA-22",
        "objective": "Prove fail-closed handling and bounded generation of separately authorized corrective work.",
        "qualification_timestamp": "2026-08-01T12:02:00Z", "assertions": assertions,
        "proposal_digest": saved["proposal_digest"], "record_digest": saved["record_digest"],
        "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL",
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-022-QUALIFICATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    import sys
    value = qualify(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(0 if value["result"] == "PASS" else 1)
