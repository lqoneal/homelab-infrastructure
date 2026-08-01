"""Canonical verification for human dispatch authorization receipts."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.dispatch_authorization import authorize, reject, request, validate
from scripts.lib.eos import capability_registry, mission_knowledge

EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-14-execution-001"


def _digest(value: dict[str, Any], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-14", {})
    if state.get("active_gate") != "OA-14" or gate.get("state") not in {"PENDING", "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}:
        raise ValueError("OA-14 is not the sole active verifiable gate")
    if state.get("gates", {}).get("OA-13", {}).get("state") != "ACCEPTED":
        raise ValueError("OA-13 acceptance is not current")
    capabilities = capability_registry.load(repository)
    cap = next((item for item in capabilities["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-013"), None)
    if not cap or cap.get("runtime_availability") != "AVAILABLE" or cap.get("lifecycle") != "Operational":
        raise ValueError("ZEUS-OA-CAP-013 is not operational in the Capability Registry")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-14")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-14 qualification requires its current pre-acceptance lifecycle")

    authorization_request = request(repository)
    replay = request(repository)
    if authorization_request != replay:
        raise ValueError("authorization request replay is not deterministic")
    expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    receipt = authorize(authorization_request, "loneal", expiry)
    validate(repository, authorization_request, receipt)
    rejected = reject(authorization_request, "operator denied authorization")
    if rejected.get("protected_effect_authorized") or rejected.get("execution_started"):
        raise ValueError("rejection produced an effect")
    negative = {}
    for name, altered in {
        "malformed_request": {**authorization_request, "request_digest": "invalid"},
        "expired_receipt": {**receipt, "expires_at": "2000-01-01T00:00:00+00:00"},
        "replayed_receipt": {**receipt, "request_digest": "different"},
    }.items():
        try:
            validate(repository, authorization_request, altered)
        except ValueError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    if set(negative.values()) != {"PASS"}:
        raise ValueError("authorization negative cases did not fail closed")
    later_evidence = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-15"
    later_decisions = repository / progressive_oa.PACKAGE_PATH / "runtime/decisions/OA-15"
    if later_evidence.exists() or later_decisions.exists():
        raise ValueError("OA-15 runtime artifacts exist")
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-14",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-14/objective.yaml",
            "predecessor": "OA-13 ACCEPTED",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(capabilities.get("revision")),
            "request_digest": authorization_request["request_digest"],
            "receipt_digest": receipt["receipt_digest"],
        },
        "assertions": {
            "explicit_authorization": "PASS",
            "explicit_rejection": "PASS",
            "expiration_rejected": negative["expired_receipt"],
            "replay_safe": negative["replayed_receipt"],
            "negative_fail_closed": negative,
            "execution_started": "PASS_FALSE",
            "later_gate_artifacts_absent": True,
        },
    }
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-14", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker, "marker_digest")
    runtime_dir = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-14"
    _write(runtime_dir / "AUTHORIZATION-REQUEST.json", authorization_request)
    _write(runtime_dir / "AUTHORIZATION-RECEIPT.json", receipt)
    _write(runtime_dir / "VERIFICATION.json", evidence)
    _write(runtime_dir / "VERIFIED", marker)
    state["gates"]["OA-14"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-14", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "request_digest": authorization_request["request_digest"], "receipt_digest": receipt["receipt_digest"], "evidence_directory": EVIDENCE_DIR}
