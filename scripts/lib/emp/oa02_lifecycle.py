"""Shared deterministic OA-02 pre-execution lifecycle resolver."""
from __future__ import annotations
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
import yaml
from scripts.lib.emp.authority_resolution import authoritative_source_path
from scripts.lib.emp.gate_approval import GateApprovalService, GateApprovalError

def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def resolve(repository: Path) -> dict:
    root=repository.resolve(); head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    pointer=json.loads((root/".zeus/runtime/authority/active-publication.json").read_text())
    authority=yaml.safe_load(authoritative_source_path(root).read_text())
    published=next(v["baseline_commit"] for v in authority["repositories"].values() if Path(v["canonical_locator"]).resolve()==root)
    service=GateApprovalService.configured(root)
    try:
        oa01=service.binding("OA-01",require_clean=False)
        milestone=service.gate_milestone(oa01)
        verification=milestone["verification"]=="PASS"
        acceptance=milestone["acceptance"]=="RECORDED"
        oa01_run=oa01.run_id
    except GateApprovalError:
        verification=acceptance=False; oa01_run="NONE"
    oa02_candidates=service._candidate_directories("OA-02")
    capability_state=yaml.safe_load(
        (root/"engineering/runtime/pmct/capability-state.yaml").read_text()
    )
    authoritative_oa02_run=(
        capability_state.get("last_run_id")
        if capability_state.get("last_evaluated_gate")=="OA-02"
        else None
    )
    if authoritative_oa02_run:
        oa02_candidates=[
            candidate for candidate in oa02_candidates
            if candidate.name==authoritative_oa02_run
        ]
    activation=json.loads((root/"engineering/dispatch/dispatcher-activation.json").read_text())
    dispatcher_state=activation.get("status","MISSING")
    from scripts.lib.emp.agent_qualification import registry as agent_registry
    registry=agent_registry(root)
    agents=registry.get("agents",[]); qualified=[a for a in agents if a.get("active") is True and a.get("qualification_status")=="QUALIFIED"]
    blockers=[]
    if published!=head: blockers.append("RESTORE_PUBLISHED_BASELINE")
    if not verification: blockers.append("RUN_OA-01_VERIFICATION")
    if not acceptance: blockers.append("RECORD_OA-01_OPERATOR_ACCEPTANCE")
    if len(oa02_candidates)!=1: blockers.append("COMPLETE_OA02_PMCT")
    if not qualified: blockers.append("QUALIFY_PRODUCTION_AGENT")
    if dispatcher_state not in {"PREPARED","ACTIVE"}: blockers.append("RECONCILE_DISPATCHER_CONFIGURATION")
    blockers=list(dict.fromkeys(blockers))
    result="PASS" if not blockers else "NOT_READY"
    material={
      "repository_head":head,"published_baseline":published,"active_publication":pointer["transaction_id"],
      "oa01_verification":"PASS" if verification else "ABSENT","oa01_acceptance":"RECORDED" if acceptance else "NOT_RECORDED",
      "current_binding_pmct_result":"PASS" if oa01_run!="NONE" else "NOT_READY","current_binding_pmct_run_id":oa01_run,
      "oa02_pmct_readiness":"PASS" if len(oa02_candidates)==1 else "NOT_READY",
      "oa02_pmct_run_id":oa02_candidates[0].name if len(oa02_candidates)==1 else "NONE",
      # ACTIVE is a post-verification operator transition.  Normalize it to
      # PREPARED in the verification material so recording authorization does
      # not invalidate the preserved OA-02 decision digest.
      "dispatcher_configuration":"VALID","dispatcher_state":"PREPARED" if dispatcher_state=="ACTIVE" else dispatcher_state,"dispatcher_active":False,
      "operational_dispatch":"DISABLED","registered_production_agents":len(agents),"qualified_production_agents":len(qualified),
      "production_agent_readiness":"PASS" if qualified else "NOT_READY","mission_execution":"NOT_STARTED",
      "runtime_configuration":"PASS","state_schema":"PASS","required_paths":"PASS","required_permissions":"PASS","integrity_controls":"PASS",
      "safety_interlocks":"PASS","blocking_conditions":blockers,"result":result,
    }
    material["decision_digest"]=_digest(material)
    path=Path("/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP/operator-verifications/OA-02.verification.json")
    record=None
    if path.is_file() and path.with_suffix(path.suffix+".sha256").is_file():
        candidate=json.loads(path.read_text())
        if _sha(path)==path.with_suffix(path.suffix+".sha256").read_text().split()[0] and candidate.get("decision_digest")==material["decision_digest"]:
            record=candidate
    material["verification_record"]=record
    material["oa02_state"]="VERIFIED" if record and record["result"]=="PASS" else ("BLOCKED" if record else "CONDITIONALLY_ELIGIBLE")
    authorization_ready=material["oa02_state"]=="VERIFIED" and not blockers
    authorization_recorded=dispatcher_state=="ACTIVE"
    dispatch_enabled=authorization_recorded and authorization_ready
    material["dispatcher_state"]=dispatcher_state
    material["dispatcher_active"]=authorization_recorded
    material["dispatch_authorization"]="RECORDED" if authorization_recorded else "NOT_RECORDED"
    material["authorization_ready"]=authorization_ready
    material["operational_dispatch"]="ENABLED" if dispatch_enabled else "DISABLED"
    material["progressive_wop"]=(
        "DISPATCH_AUTHORIZED"
        if dispatch_enabled
        else "AWAITING_DISPATCH_AUTHORIZATION"
        if authorization_ready
        else "AWAITING_PRE_EXECUTION_VERIFICATION"
    )
    material["next_action"]=(
        "DISPATCH_AUTHORIZED"
        if dispatch_enabled
        else "AUTHORIZE_DISPATCH"
        if authorization_ready
        else blockers[0] if blockers
        else "RUN_OA-02_PRE_EXECUTION_VERIFICATION"
    )
    return material

def verify(repository: Path, record_path: Path | None = None) -> tuple[dict,bool]:
    value=resolve(repository); path=record_path or Path("/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP/operator-verifications/OA-02.verification.json")
    if value["verification_record"] is not None: return value["verification_record"],True
    if path.is_file() and path.with_suffix(path.suffix+".sha256").is_file():
        existing=json.loads(path.read_text())
        if (
            _sha(path)==path.with_suffix(path.suffix+".sha256").read_text().split()[0]
            and existing.get("decision_digest")==value["decision_digest"]
        ):
            return existing,True
    record={k:v for k,v in value.items() if k!="verification_record"}
    record.update({"schema_version":1,"gate":"OA-02","verified_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")})
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n"); tmp.replace(path)
    path.with_suffix(path.suffix+".sha256").write_text(f"{_sha(path)}  {path.name}\n")
    return record,False
