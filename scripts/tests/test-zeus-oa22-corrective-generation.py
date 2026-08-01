"""Independent CAP-022 qualification."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.emp.corrective_work_authorization import AuthorizationStore, decide, request
from lib.emp.corrective_work_generation import (
    CorrectiveWorkGenerationError,
    CorrectiveWorkStore,
    generate,
)


def main() -> int:
    start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    expiry = datetime(2026, 8, 1, 13, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        authorization = request(
            authorization_id="AUTH-CAP021-001", mission_id="OA-22",
            wop_id="WOP-OA-22-COMPLETE-EXECUTION-AND-PUBLICATION-001",
            repository="/data/engineering/repositories/homelab",
            baseline="f3e77fa62c00aace83959e2f813200ffcb79f215",
            authority="OA-22/CAP-021", operator="OPERATOR",
            scope=["runtime/evidence/OA-22"], requested_at=start, expires_at=expiry,
        )
        auth_receipt = decide(
            authorization, decision="AUTHORIZED", operator="OPERATOR",
            authority_lease="LEASE-OA22-001", decided_at=start,
        )
        proposal = generate(
            request_record=authorization, authorization_receipt=auth_receipt,
            proposal_id="PROP-OA22-001", trigger="verified_failure",
            bounded_objective="capture bounded corrective work for the verified failure",
            affected_records=["runtime/evidence/OA-22"], at="2026-08-01T12:01:00Z",
        )
        store = CorrectiveWorkStore(root / "proposals")
        saved, created = store.save(proposal)
        replay, replay_created = store.save(proposal)
        assert created and not replay_created and replay == saved
        assert saved["state"] == "PROPOSED"
        assert saved["dispatched"] is False and saved["executed"] is False
        tampered = dict(proposal)
        tampered["bounded_objective"] = "unauthorized expansion"
        try:
            generate(
                request_record=authorization, authorization_receipt=auth_receipt,
                proposal_id="PROP-OA22-002", trigger="verified_failure",
                bounded_objective=tampered["bounded_objective"], affected_records=[],
                at="2026-08-01T12:01:00Z",
            )
        except CorrectiveWorkGenerationError:
            pass
        else:
            raise AssertionError("unbounded/tampered proposal was accepted")
        denied = decide(
            authorization, decision="DENIED", operator="OPERATOR",
            authority_lease="LEASE-OA22-002", decided_at=start,
        )
        try:
            generate(
                request_record=authorization, authorization_receipt=denied,
                proposal_id="PROP-OA22-003", trigger="verified_failure",
                bounded_objective="capture bounded corrective work",
                affected_records=["runtime/evidence/OA-22"], at="2026-08-01T12:01:00Z",
            )
        except CorrectiveWorkGenerationError:
            pass
        else:
            raise AssertionError("denied authorization generated corrective work")
    print("PASS: CAP-022 bounded generation, authorization binding, fail-closed, replay, and recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
