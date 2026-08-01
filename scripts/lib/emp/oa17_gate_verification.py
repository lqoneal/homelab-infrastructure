"""Independent qualification for controlled execution authorization."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.execution_authorization import (
    ExecutionAuthorizationError,
    ExecutionAuthorizationStore,
    decide,
    request,
    transition,
    validate,
)
from scripts.lib.eos import capability_registry, mission_knowledge


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualify(repository: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zeus-oa17-") as directory:
        store = ExecutionAuthorizationStore(Path(directory) / "authorization")
        execution_id = "MISSION-EXECUTION-OA17-QUALIFICATION-001"
        at = datetime(2026, 7, 31, 9, 17, tzinfo=timezone.utc)
        req = request(
            execution_id=execution_id,
            mission_id="OA-17",
            wop_id="WOP-OA-17-EXECUTION-001",
            repository=str(repository),
            authority="Mission Knowledge Model + EMM + Capability Registry",
            operator="OA-17-QUALIFICATION-OPERATOR",
            expires_at=at + timedelta(minutes=10),
        )
        state = {**req, "state": "PENDING", "updated_at": req["requested_at"]}
        store.save(state)
        loaded = store.load(execution_id)
        if loaded["state"] != "PENDING":
            raise ValueError("authorization pending state was not durable")
        receipt = decide(req, decision="AUTHORIZED", authority_lease="OA17-AUTHORITY-LEASE-001",
                         operator="OA-17-QUALIFICATION-OPERATOR", at=at)
        validate(req, receipt, at=at)
        authorized = transition(loaded, "AUTHORIZED", at=at, reason="VALIDATED_AUTHORIZATION")
        authorized.update({"receipt": receipt})
        store.save(authorized)
        recovered = store.load(execution_id)
        if recovered["state"] != "AUTHORIZED":
            raise ValueError("authorized state did not survive restart recovery")
        denied_request = request(
            execution_id="MISSION-EXECUTION-OA17-DENIED-001", mission_id="OA-17",
            wop_id=req["wop_id"], repository=str(repository), authority=req["authority"],
            operator=req["operator"], expires_at=at + timedelta(minutes=10),
        )
        denied_state = {**denied_request, "state": "PENDING", "updated_at": denied_request["requested_at"]}
        denied_state = transition(denied_state, "DENIED", at=at, reason="AUTHORITY_DENIED")
        store.save(denied_state)
        if store.load(denied_state["execution_id"])["state"] != "DENIED":
            raise ValueError("denied authorization state was not durable")
        try:
            validate(req, {**receipt, "receipt_digest": "replayed"}, at=at)
        except ExecutionAuthorizationError:
            replay_rejected = True
        else:
            replay_rejected = False
        if not replay_rejected:
            raise ValueError("authorization receipt replay was accepted")
        expired_request = request(
            execution_id="MISSION-EXECUTION-OA17-EXPIRY-001", mission_id="OA-17",
            wop_id=req["wop_id"], repository=str(repository), authority=req["authority"],
            operator=req["operator"], expires_at=at + timedelta(seconds=1),
        )
        expired_receipt = decide(expired_request, decision="AUTHORIZED", authority_lease="OA17-AUTHORITY-LEASE-002",
                                 operator=req["operator"], at=at)
        try:
            validate(expired_request, expired_receipt, at=at + timedelta(seconds=2))
        except ExecutionAuthorizationError:
            timeout_rejected = True
        else:
            timeout_rejected = False
        if not timeout_rejected:
            raise ValueError("expired authorization was accepted")
        revoked = transition(recovered, "REVOKED", at=at + timedelta(seconds=3), reason="AUTHORITY_REVOKED")
        store.save(revoked)
        if store.load(execution_id)["state"] != "REVOKED":
            raise ValueError("revoked authorization state was not durable")
        return {
            "request": req, "receipt": receipt, "state": store.load(execution_id),
            "assertions": {
                "pending_authorization": "PASS", "authorized": "PASS", "denied": "PASS",
                "expired": "PASS", "revoked": "PASS", "authorization_identity": "PASS",
                "authority_lease_verification": "PASS", "receipt_binding": "PASS",
                "replay_protection": "PASS", "timeout_handling": "PASS",
                "interrupted_authorization_recovery": "PASS", "fail_closed": "PASS",
            },
        }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-17" or state["gates"]["OA-16"].get("state") != "ACCEPTED":
        raise ValueError("OA-17 is not the sole active gate after OA-16 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-17")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-17 is not CURRENT in the Mission Knowledge Model")
    registry = capability_registry.load(repository)
    marker_candidate = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-17/VERIFIED"
    if any(item.get("capability_id") == "ZEUS-OA-CAP-016" for item in registry["capabilities"]) and marker_candidate.is_file():
        marker_path, marker = progressive_oa._marker_binding(repository, "OA-17")
        return {"gate_id": "OA-17", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
                "evidence_digest": marker["evidence_digest"], "marker_digest": marker["marker_digest"],
                "execution_id": "BOUND_BY_VERIFICATION_EVIDENCE",
                "evidence_directory": "engineering/evidence/2026-07-31-wop-oa-17-execution-001"}
    result = _qualify(repository)
    evidence = {
        "schema_version": 1, "gate_id": "OA-17", "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {"objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-17/objective.yaml",
                                  "predecessor": "OA-16 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
                                  "capability_registry_revision": str(registry.get("revision"))},
        "assertions": result["assertions"],
        "qualification": {"execution_id": result["request"]["execution_id"], "authorization_state": result["state"]["state"],
                           "request_digest": result["request"]["request_digest"], "receipt_digest": result["receipt"]["receipt_digest"]},
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-17",
              "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"],
              "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-17"
    _write(runtime / "AUTHORIZATION-REQUEST.json", result["request"])
    _write(runtime / "AUTHORIZATION-RECEIPT.json", result["receipt"])
    _write(runtime / "AUTHORIZATION-STATE.json", result["state"])
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-17"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-17", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"],
            "execution_id": result["request"]["execution_id"],
            "evidence_directory": "engineering/evidence/2026-07-31-wop-oa-17-execution-001"}
