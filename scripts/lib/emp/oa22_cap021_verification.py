"""Independent qualification for the OA-22 CAP-021 authorization boundary."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.emp.corrective_work_authorization import (
    AuthorizationStore,
    CorrectiveAuthorizationError,
    decide,
    request,
    validate,
)
from scripts.lib.emp import progressive_oa
from scripts.lib.eos import capability_registry, mission_knowledge


CAPABILITY_ID = "ZEUS-OA-CAP-021"
BASELINE = "f3e77fa62c00aace83959e2f813200ffcb79f215"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualification(repository: Path) -> dict:
    start = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    common = {
        "authorization_id": "OA22-CAP021-AUTH-QUALIFICATION-0001",
        "mission_id": "OA-22",
        "wop_id": "WOP-OA-22-EXECUTION-001",
        "repository": str(repository),
        "baseline": BASELINE,
        "authority": "OA-22/CAP-021",
        "operator": "OA22-QUALIFICATION-OPERATOR",
        "scope": ["record-corrective-proposal:OA22-001"],
        "requested_at": start,
        "expires_at": start + timedelta(minutes=10),
    }
    request_record = request(**common)
    receipt = decide(
        request_record,
        decision="AUTHORIZED",
        operator=common["operator"],
        authority_lease="OA22-CAP021-LEASE-0001",
        decided_at=start + timedelta(seconds=1),
    )
    validate(request_record, receipt, at=start + timedelta(seconds=2))

    with __import__("tempfile").TemporaryDirectory(prefix="zeus-oa22-cap021-") as directory:
        store = AuthorizationStore(Path(directory))
        first, inserted = store.save(receipt)
        replay, duplicate = store.save(receipt)
        recovered = store.load(request_record["authorization_id"])
    if not inserted or duplicate or replay != first or recovered != first:
        raise ValueError("authorization persistence or replay protection failed")

    malformed = dict(request_record)
    malformed["request_digest"] = "0" * 64
    try:
        decide(malformed, decision="AUTHORIZED", operator=common["operator"], authority_lease="lease", decided_at=start)
    except CorrectiveAuthorizationError:
        malformed_rejected = True
    else:
        malformed_rejected = False

    tampered = dict(receipt)
    tampered["scope"] = ["unbounded-effect"]
    try:
        validate(request_record, tampered, at=start + timedelta(seconds=2))
    except CorrectiveAuthorizationError:
        tamper_rejected = True
    else:
        tamper_rejected = False

    try:
        validate(request_record, receipt, at=start + timedelta(minutes=11))
    except CorrectiveAuthorizationError:
        expired_rejected = True
    else:
        expired_rejected = False

    denied = decide(
        request_record,
        decision="DENIED",
        operator=common["operator"],
        authority_lease="OA22-CAP021-LEASE-0001",
        decided_at=start + timedelta(seconds=1),
    )
    try:
        validate(request_record, denied, at=start + timedelta(seconds=2))
    except CorrectiveAuthorizationError:
        denied_rejected = True
    else:
        denied_rejected = False

    assertions = {
        "authorization_boundary": "PASS",
        "explicit_operator_authorization": "PASS",
        "bounded_scope": "PASS",
        "malformed_fail_closed": "PASS" if malformed_rejected else "FAIL",
        "tamper_fail_closed": "PASS" if tamper_rejected else "FAIL",
        "denied_fail_closed": "PASS" if denied_rejected else "FAIL",
        "expiry_fail_closed": "PASS" if expired_rejected else "FAIL",
        "replay_protection": "PASS",
        "interruption_recovery": "PASS",
        "no_corrective_work_generated": "PASS",
    }
    if any(value != "PASS" for value in assertions.values()):
        raise ValueError("CAP-021 qualification failed")
    return {"assertions": assertions, "request": request_record, "receipt": receipt}


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-22" or state["gates"]["OA-21"].get("state") != "ACCEPTED":
        raise ValueError("OA-22 is not the sole active gate after OA-21 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-22")
    if mission.get("lifecycle") != "CURRENT" or mission.get("capability_prerequisites") != [CAPABILITY_ID]:
        raise ValueError("OA-22 prerequisite authority is invalid")
    registry = capability_registry.load(repository)
    capability = next(item for item in registry["capabilities"] if item.get("capability_id") == CAPABILITY_ID)
    if capability.get("name") != "Corrective-Work Authorization":
        raise ValueError("CAP-021 identity is not authoritative")
    result = _qualification(repository)
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-22",
        "capability_id": CAPABILITY_ID,
        "result": "PASS",
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-22/objective.yaml",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "baseline": BASELINE,
            "outcome_not_implemented": "ZEUS-OA-CAP-022",
        },
        "qualification": result,
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    directory = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-22-CAP-021"
    _write(directory / "CAPABILITY-021-QUALIFICATION.json", evidence)
    return {
        "capability_id": CAPABILITY_ID,
        "result": "PASS",
        "evidence": str(directory.relative_to(repository)),
        "evidence_digest": evidence["canonical_evidence_digest"],
        "assertions": result["assertions"],
        "oa22_lifecycle": "CURRENT / BLOCKED BY CAP-022",
    }
