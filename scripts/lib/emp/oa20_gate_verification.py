"""Independent qualification for OA-20 evidence integrity and provenance."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.evidence_capture import EvidenceCapture
from scripts.lib.emp.evidence_provenance import EvidenceProvenance, EvidenceProvenanceError
from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove evidence binding to repository commit, authority, mission, WOP, execution, gate, and agent."
BASELINE = "7bc52fc7eab77a9f637264adae621adf3ba6c774"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualification(repository: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zeus-oa20-") as directory:
        root = Path(directory)
        timestamp = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc).isoformat()
        capture = EvidenceCapture(root / "capture.sqlite3")
        capture.capture(record_id="OA20-EVIDENCE-0001", mission_id="OA-20", wop_id="WOP-OA-20-EXECUTION-001", repository_identity=str(repository), baseline_commit=BASELINE, agent_identity="oa20-qualification-agent", command="zeus verify OA-20", stdout="PASS", stderr="", state="COMPLETED", completion_marker="OA20-EVIDENCE-COMPLETE", timestamp=timestamp)
        record = list(capture.replay())[0].event.payload
        binder = EvidenceProvenance(root / "provenance.sqlite3")
        bindings = dict(evidence_record=record, repository_identity=str(repository), repository_commit=BASELINE, authority_identity="MANUAL_GOVERNANCE_WOP:WOP-OA-20-WORKTREE-RECONCILIATION-AND-EXECUTION-001", mission_id="OA-20", wop_id="WOP-OA-20-EXECUTION-001", execution_id="OA20-EXECUTION-001", gate_id="OA-20", agent_identity="oa20-qualification-agent", timestamp=timestamp)
        first = binder.bind(**bindings)
        duplicate = binder.bind(**bindings)
        if not first.inserted or duplicate.inserted or binder.store.count() != 1:
            raise ValueError("provenance binding replay semantics failed")
        try:
            binder.bind(**{**bindings, "mission_id": "OA-19"})
        except EvidenceProvenanceError:
            mismatch_rejected = True
        else:
            mismatch_rejected = False
        tampered = {**record, "stdout": "tampered"}
        try:
            binder.bind(**{**bindings, "evidence_record": tampered})
        except EvidenceProvenanceError:
            tamper_rejected = True
        else:
            tamper_rejected = False
        try:
            binder.bind(**{**bindings, "authority_identity": ""})
        except EvidenceProvenanceError:
            missing_rejected = True
        else:
            missing_rejected = False
        recovered = EvidenceProvenance(root / "provenance.sqlite3")
        replayed = list(recovered.replay())
        if len(replayed) != 1 or not all((mismatch_rejected, tamper_rejected, missing_rejected)):
            raise ValueError("provenance negative or recovery qualification failed")
        manifest = replayed[0].event.payload
        required = EvidenceProvenance.REQUIRED_BINDINGS
        if any(manifest["bindings"].get(key) != bindings[key] for key in required):
            raise ValueError("provenance manifest omitted an authoritative binding")
        return {
            "manifest": manifest,
            "database_journal_mode": recovered.store.journal_mode(),
            "assertions": {
                "repository_commit_binding": "PASS", "authority_binding": "PASS",
                "mission_wop_binding": "PASS", "execution_gate_binding": "PASS",
                "agent_binding": "PASS", "checksum_integrity": "PASS",
                "mismatch_fail_closed": "PASS", "tamper_fail_closed": "PASS",
                "missing_binding_fail_closed": "PASS", "replay_idempotency": "PASS",
                "restart_recovery": "PASS",
            },
        }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-20" or state["gates"]["OA-19"].get("state") != "ACCEPTED":
        raise ValueError("OA-20 is not the sole active gate after OA-19 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-20")
    if mission.get("lifecycle") != "CURRENT" or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-018"] or mission.get("capability_outcomes") != ["ZEUS-OA-CAP-019"]:
        raise ValueError("OA-20 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    capability = next(item for item in registry["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-019")
    if capability.get("name") != "Evidence Integrity and Provenance" or capability.get("lifecycle") not in {"Planned", "Operational"}:
        raise ValueError("OA-20 capability identity is not authoritative")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-20/VERIFIED"
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-20", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": marker["evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": str(marker_path.parent.relative_to(repository))}
    result = _qualification(repository)
    evidence = {
        "schema_version": 1, "gate_id": "OA-20", "result": "PASS", "objective": OBJECTIVE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {"objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-20/objective.yaml", "predecessor": "OA-19 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")), "capability_registry_revision": str(registry.get("revision")), "capability_id": "ZEUS-OA-CAP-019", "baseline": BASELINE},
        "assertions": result["assertions"], "bound_manifest": result["manifest"],
        "qualification": {"database_journal_mode": result["database_journal_mode"]},
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-20", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-20"
    _write(runtime / "EVIDENCE-PROVENANCE-VERIFICATION.json", evidence)
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-20"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-20", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": str(runtime.relative_to(repository))}
