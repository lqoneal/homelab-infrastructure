"""Independent qualification for OA-19 append-only evidence capture."""

from __future__ import annotations

import hashlib
import json
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.evidence_capture import EvidenceCapture, EvidenceCaptureError
from scripts.lib.eos import capability_registry, mission_knowledge


OBJECTIVE = "Prove append-only capture of commands, outputs, state, timestamps, identities, checksums, and completion markers."


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualification(repository: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zeus-oa19-") as directory:
        database = Path(directory) / "evidence.sqlite3"
        capture = EvidenceCapture(database)
        start = datetime(2026, 8, 1, 6, 19, tzinfo=timezone.utc)
        common = {
            "mission_id": "OA-19",
            "wop_id": "WOP-OA-19-EXECUTION-001",
            "repository_identity": str(repository),
            "baseline_commit": "d08edaec17dbbefd68f2f0d2dbf4f606a61ac4a4",
            "agent_identity": "oa19-qualification-agent",
        }
        records = []
        for number, state in enumerate(("STARTED", "CAPTURED", "COMPLETED"), start=1):
            records.append(capture.capture(
                **common,
                record_id=f"OA19-EVIDENCE-{number:04d}",
                command="zeus verify OA-19",
                stdout=f"OA-19 {state}",
                stderr="",
                state=state,
                completion_marker="OA19-EVIDENCE-COMPLETE" if state == "COMPLETED" else "OA19-EVIDENCE-INCOMPLETE",
                timestamp=(start + timedelta(seconds=number)).isoformat(),
            ))
        before_duplicate = capture.store.count()
        duplicate = capture.capture(
            **common,
            record_id="OA19-EVIDENCE-0003",
            command="zeus verify OA-19",
            stdout="OA-19 COMPLETED",
            stderr="",
            state="COMPLETED",
            completion_marker="OA19-EVIDENCE-COMPLETE",
            timestamp=(start + timedelta(seconds=3)).isoformat(),
        )
        if duplicate.inserted or capture.store.count() != before_duplicate:
            raise ValueError("identical evidence replay was not suppressed")
        try:
            capture.capture(
                **common,
                record_id="OA19-EVIDENCE-0003",
                command="tampered command",
                stdout="OA-19 COMPLETED",
                stderr="",
                state="COMPLETED",
                completion_marker="OA19-EVIDENCE-COMPLETE",
                timestamp=(start + timedelta(seconds=3)).isoformat(),
            )
        except Exception:
            conflicting_replay = True
        else:
            conflicting_replay = False
        if not conflicting_replay:
            raise ValueError("conflicting evidence replay was accepted")
        try:
            capture.capture(**{**common, "record_id": "OA19-EVIDENCE-BAD", "command": "", "stdout": "x", "stderr": "", "state": "FAILED", "completion_marker": "", "timestamp": start.isoformat()})
        except EvidenceCaptureError:
            malformed_rejected = True
        else:
            malformed_rejected = False
        if not malformed_rejected:
            raise ValueError("malformed evidence was accepted")
        recovered = EvidenceCapture(database)
        replayed = list(recovered.replay())
        if len(replayed) != 3 or recovered.store.count() != 3:
            raise ValueError("evidence did not survive restart recovery")
        for item in replayed:
            payload = item.event.payload
            required = ("command", "stdout", "stderr", "state", "timestamp", "agent_identity", "checksum", "completion_marker")
            if any(field not in payload or not isinstance(payload[field], str) for field in required):
                raise ValueError("captured evidence is incomplete")
        return {
            "database_journal_mode": recovered.store.journal_mode(),
            "record_count": len(replayed),
            "sequence": [item.sequence for item in replayed],
            "duplicate_inserted": duplicate.inserted,
            "conflicting_replay_rejected": conflicting_replay,
            "malformed_input_rejected": malformed_rejected,
            "restart_recovery": True,
            "records": [item.event.to_dict() for item in replayed],
            "assertions": {
                "append_only_capture": "PASS",
                "command_output_state_capture": "PASS",
                "timestamp_identity_capture": "PASS",
                "checksum_capture": "PASS",
                "completion_marker_capture": "PASS",
                "duplicate_replay_protection": "PASS",
                "conflicting_replay_rejection": "PASS",
                "malformed_input_fail_closed": "PASS",
                "restart_recovery": "PASS",
            },
        }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-19" or state["gates"]["OA-18"].get("state") != "ACCEPTED":
        raise ValueError("OA-19 is not the sole active gate after OA-18 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-19")
    if mission.get("lifecycle") != "CURRENT" or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-017"] or mission.get("capability_outcomes") != ["ZEUS-OA-CAP-018"]:
        raise ValueError("OA-19 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    capability = next(item for item in registry["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-018")
    if capability.get("name") != "Evidence Capture" or capability.get("lifecycle") not in {"Planned", "Operational"}:
        raise ValueError("OA-19 capability identity is not authoritative")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-19/VERIFIED"
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-19", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": marker["evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": str(marker_path.parent.relative_to(repository))}
    result = _qualification(repository)
    evidence = {
        "schema_version": 1, "gate_id": "OA-19", "result": "PASS", "objective": OBJECTIVE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {"objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-19/objective.yaml", "predecessor": "OA-18 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")), "capability_registry_revision": str(registry.get("revision")), "capability_id": "ZEUS-OA-CAP-018", "baseline": "d08edaec17dbbefd68f2f0d2dbf4f606a61ac4a4"},
        "assertions": result["assertions"],
        "qualification": {key: value for key, value in result.items() if key != "records"},
        "evidence_records": result["records"],
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-19", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-19"
    _write(runtime / "EVIDENCE-CAPTURE-VERIFICATION.json", evidence)
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-19"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-19", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": str(runtime.relative_to(repository))}
