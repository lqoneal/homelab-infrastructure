#!/usr/bin/env python3
"""Independent CAP-021 authorization-boundary qualification."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.corrective_work_authorization import (  # noqa: E402
    AuthorizationStore,
    CorrectiveAuthorizationError,
    decide,
    request,
    validate,
)


def main():
    start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    req = request(
        authorization_id="OA22-CAP021-AUTH-0001",
        mission_id="OA-22",
        wop_id="WOP-OA-22-EXECUTION-001",
        repository="/data/engineering/repositories/homelab",
        baseline="f3e77fa62c00aace83959e2f813200ffcb79f215",
        authority="OA-22/CAP-021",
        operator="OA22-QUALIFICATION-OPERATOR",
        scope=["record-corrective-proposal:OA22-001"],
        requested_at=start,
        expires_at=start + timedelta(minutes=10),
    )
    receipt = decide(req, decision="AUTHORIZED", operator="OA22-QUALIFICATION-OPERATOR", authority_lease="OA22-LEASE-0001", decided_at=start + timedelta(seconds=1))
    validate(req, receipt, at=start + timedelta(seconds=2))

    with tempfile.TemporaryDirectory(prefix="zeus-oa22-cap021-") as directory:
        store = AuthorizationStore(directory)
        first, inserted = store.save(receipt)
        replay, duplicate = store.save(receipt)
        assert inserted and not duplicate and replay == first
        recovered = store.load(req["authorization_id"])
        assert recovered == first

    for bad in (
        {**req, "scope": []},
        {**req, "request_digest": "0" * 64},
        {**receipt, "receipt_digest": "0" * 64},
    ):
        try:
            if bad is req or bad.get("scope") == []:
                request(**{key: bad[key] for key in ("authorization_id", "mission_id", "wop_id", "repository", "baseline", "authority", "operator", "scope", "requested_at", "expires_at")})
            elif "request_digest" in bad and bad.get("authorization_type", "").endswith("RECEIPT"):
                validate(req, bad, at=start + timedelta(seconds=2))
            else:
                validate(bad, receipt, at=start + timedelta(seconds=2))
        except CorrectiveAuthorizationError:
            pass
        else:
            raise AssertionError("malformed or replayed authorization was accepted")

    try:
        validate(req, receipt, at=start + timedelta(minutes=11))
    except CorrectiveAuthorizationError:
        expired = True
    else:
        expired = False
    assert expired
    assert receipt["corrective_work_generated"] is False
    print("PASS: CAP-021 authorization boundary, bounded scope, fail-closed, replay, expiry, and recovery")


if __name__ == "__main__":
    main()
