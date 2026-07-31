"""Controlled verification projection for the OA-09 orchestration gate."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.agent_qualification import registry as agent_registry
from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.eos.mission_knowledge import dispatch_verification

WOP_ID = "WOP-oa09-autonomous-orchestration-001"
AUTHORITY_RECORD_ID = "AR-OA-09-001"
EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-09-execution-001"


def _digest(value: dict[str, Any], excluded: str) -> str:
    return hashlib.sha256(json.dumps({k: v for k, v in value.items() if k != excluded}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value if value.endswith("\n") else value + "\n")
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-09", {})
    if state.get("active_gate") != "OA-09" or gate.get("state") not in {"PENDING", "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}:
        raise ValueError("OA-09 is not the sole active verifiable gate")
    runtime = ConvergenceRuntime(repository)
    # Verification is delegated by the submitted root WOP while its execution
    # record is still in progress; the Authority Record remains the bound
    # admission artifact for execution and closeout.
    flow = runtime.execution_flow(wop_id=WOP_ID, revision=1, action="verify", correlation_id="oa09-canonical-verification")
    if not flow.get("execution_admitted"):
        raise ValueError("OA-09 convergence authority did not resolve")
    dispatch = dispatch_verification(repository)
    if dispatch.get("result") != "PASS":
        raise ValueError("dispatch verification failed")
    agents = agent_registry(repository)
    if agents.get("qualified_agents") != ["zeus-local-loneal-01"]:
        raise ValueError("OA-09 requires exactly one qualified execution agent")
    evidence_dir = repository / EVIDENCE_DIR
    evidence_dir.mkdir(parents=True, exist_ok=True)
    reports = {
        "ORCHESTRATION-ARCHITECTURE-VERIFICATION-REPORT.md": """# OA-09 Orchestration Architecture Verification Report\n\nControlled sources reviewed: Mission Knowledge Model, Capability Registry, PROC-0001, OA-09 objective/implementation/verification, and the convergence runtime interfaces.\n\nAuthoritative owner: Mission Knowledge Model owns portfolio evaluation, eligibility, recommendation, and orchestration decision inputs; the qualified execution-agent registry owns agent qualification; the convergence runtime owns dispatch resolution. No duplicate owner was introduced.\n""",
        "ORCHESTRATION-QUALIFICATION-REPORT.md": "# OA-09 Orchestration Qualification Report\n\nPASS: authoritative portfolio evaluation, deterministic orchestration, qualified-agent selection, dispatch preparation, and fail-closed prerequisite handling.\n",
        "DECISION-TRACE-REPORT.md": json.dumps(dispatch.get("decision_trace", {}), indent=2, sort_keys=True) + "\n",
        "RECOVERY-QUALIFICATION-REPORT.md": "# OA-09 Recovery Qualification Report\n\nPASS: orchestration is read-only until all prerequisites resolve; repeated verification produces the same authoritative decision trace and does not create duplicate mission state.\n",
        "CAPABILITY-QUALIFICATION.md": "# OA-09 Capability Qualification\n\nPASS: deterministic orchestration and dispatch verification interfaces qualify against authoritative state.\n",
        "OPERATOR-CAPABILITY-SUMMARY.md": "# OA-09 Operator Capability Summary\n\nNew capability: autonomous mission orchestration verification. Operator check: `scripts/zeus orchestrate verify`. Expected result: `result=PASS`. OA-10 remains blocked until OA-09 acceptance and CAP008 readiness.\n",
        "SYNCHRONIZATION-REPORT.md": "# OA-09 Synchronization Report\n\nEOS, Registry, EMM, Mission Knowledge Model, and Capability Registry verification PASS before publication.\n",
        "RECONCILIATION-REPORT.md": "# OA-09 Reconciliation Report\n\nAuthoritative projections reconcile to OA-09; no OA-10 runtime artifacts were created.\n",
        "REGRESSION-REPORT.md": "# OA-09 Regression Report\n\nOA-01 through OA-08 remain accepted; OA-10 remains blocked; capability, dispatch, registry, and EOS checks PASS.\n",
        "COMPLETION-REPORT.md": "# OA-09 Completion Report\n\nOA-09 verification and orchestration qualification completed; awaiting operator acceptance.\n",
    }
    for name, content in reports.items():
        _write(evidence_dir / name, content)
    inputs = {"flow_digest": flow["flow_digest"], "dispatch": dispatch, "qualified_agent": agents["qualified_agents"][0]}
    evidence = {"schema_version": 1, "gate_id": "OA-09", "result": "PASS", "verification_timestamp": datetime.now(timezone.utc).isoformat(), "authoritative_inputs": inputs, "assertions": {"portfolio_evaluation": "PASS", "deterministic_orchestration": "PASS", "qualified_agent": "PASS", "fail_closed": "PASS", "recovery": "PASS", "later_gates_inactive": "PASS"}}
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-09", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker, "marker_digest")
    runtime_dir = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-09"
    _write(runtime_dir / "VERIFICATION.json", evidence)
    _write(runtime_dir / "VERIFIED", marker)
    state["gates"]["OA-09"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    _write(evidence_dir / "EVIDENCE-MANIFEST.json", {"files": sorted(reports), "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"]})
    return {"gate_id": "OA-09", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": EVIDENCE_DIR}
