#!/usr/bin/env python3
"""Supervised deterministic conversation, WOP guidance, and generation."""
from __future__ import annotations
import json, os, tempfile, uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
import yaml
from scripts.lib.emp.wop_admission import (
    AUTHORITATIVE_SCHEMA, CONTRACT, AdmissionController, REQUIRED_SUBMISSION_FORMAT,
    canonical_json, submission_digest,
)

class ReasoningError(ValueError): pass

def _id(prefix, material):
    return prefix+"-"+str(uuid.uuid5(uuid.NAMESPACE_URL,canonical_json(material)))
def _time(value):
    if value.tzinfo is None: raise ReasoningError("timestamp must include timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

class WopGuidanceService:
    """Every response derives from the one admission schema."""
    def template(self): return deepcopy(REQUIRED_SUBMISSION_FORMAT)
    def requirements(self):
        return {"schema_required":deepcopy(AUTHORITATIVE_SCHEMA["required"]),
                "required_sections":deepcopy(CONTRACT["required_sections"]),
                "execution_package_references":deepcopy(CONTRACT["execution_package_references"]),
                "authoritative_references":[CONTRACT["procedure"],CONTRACT["template"],*CONTRACT["standards"]],
                "operator_review_required":CONTRACT["operator_review_required"]}
    def example(self):
        v=WopGenerator().generate(intent="Demonstrate supervised WOP preparation",
          mission_id=CONTRACT["example_values"]["mission_id"],phase_id=CONTRACT["example_values"]["phase_id"],
          repository_identity=CONTRACT["example_values"]["repository_identity"],submitter_identity=CONTRACT["example_values"]["submitter_identity"],
          approval_authority="operator",approval_reference="EXAMPLE-APPROVAL",approval_date="2026-07-25",
          authority_node_id="work-package",adr_reference="ADR-example",immutable_wop_reference="WOP-example")
        return v["wop"]
    def validate(self,wop,repository):
        failures=AdmissionController().validate(wop,repository)
        return {"admission_decision":"ACCEPTED" if not failures else "RESUBMISSION_REQUIRED",
                "validation_failures":[x.to_mapping() for x in failures],
                "authoritative_references":[CONTRACT["procedure"],CONTRACT["template"],*CONTRACT["standards"]],
                "operator_review_required":True}
    def explain_rejection(self,record):
        value=json.loads(Path(record).read_text())
        if value.get("admission_decision")!="RESUBMISSION_REQUIRED": raise ReasoningError("record is not a rejection")
        return {"admission_id":value["admission_id"],"status":"RESUBMISSION_REQUIRED",
          "explanations":[{"reason_code":x["reason_code"],"field":x["field"],"why":x["message"],"correction":x["required_correction"]} for x in value["validation_failures"]],
          "authoritative_references":value["authoritative_references"],
          "execution_status":"No engineering work has begun."}

class WopGenerator:
    def generate(self,*,intent,mission_id,phase_id,repository_identity,submitter_identity,
                 approval_authority,approval_reference,approval_date,authority_node_id,
                 adr_reference,immutable_wop_reference):
        material={"intent":intent.strip(),"mission_id":mission_id,"phase_id":phase_id,
                  "repository_identity":repository_identity,"submitter_identity":submitter_identity}
        wop_id=_id("WOP",material)
        sections={name:self._section(name,intent) for name in CONTRACT["required_sections"]}
        value={"schema_version":1,"document_type":"EngineeringWorkOrder","wop_id":wop_id,
          "mission_id":mission_id,"phase_id":phase_id,"revision":1,"status":"Active",
          "title":intent.strip(),"repository_identity":repository_identity,
          "submitter_identity":submitter_identity,
          "approval":{"authority":approval_authority,"reference":approval_reference,
                      "date":approval_date,"authorized_lifecycle_state":"Active"},
          "execution_package_references":{"authority_node_id":authority_node_id,
              "authorization_decision_record":adr_reference,"immutable_wop":immutable_wop_reference},
          "authoritative_references":[CONTRACT["procedure"],CONTRACT["template"],*CONTRACT["standards"]],
          "sections":sections}
        value["submission_digest"]=submission_digest(value)
        return {"wop":value,"review_required":True,"automatically_submitted":False,
                "recommendation":"Review and explicitly submit through Mission N0."}
    @staticmethod
    def _section(name,intent):
        statements={
          "purpose_and_expected_outcome":f"Purpose: {intent}. Expected outcome: a verified bounded result.",
          "mission_classification":"Category A — Repository Engineering Work; apply PROC-0001 gates.",
          "governing_references":"Conform to the authoritative references in this package.",
          "scope":f"In scope: {intent}. Out of scope: all unlisted effects.",
          "explicit_authority":"Only the reviewed package scope is proposed; this draft grants no authority.",
          "prohibited_activities":"No autonomous approval, dispatch, execution, or authority expansion.",
          "dependencies_and_entry_criteria":"Admission, authorization, prerequisites, and clean baseline are required.",
          "deliverables":"Produce the bounded implementation, tests, evidence, and completion report.",
          "execution_sequence":"Verify first; implement bounded work; qualify; stop at the approved boundary.",
          "success_and_acceptance_criteria":"All declared outcomes and canonical validators must pass.",
          "validation_profile":"Use canonical repository validators and transaction-specific tests.",
          "publication_and_synchronization":"Perform only publication and synchronization explicitly authorized.",
          "stop_resume_and_escalation":"Stop on mismatch, ambiguity, failed gate, or authority expansion.",
          "completion_report_requirement":"Produce the repository-standard Completion Report.",
        }; return statements[name]

class ContextManager:
    def __init__(self,path): self.path=Path(path)
    def load(self):
        if not self.path.exists(): return {"schema_version":1,"conversation":[],"referenced_missions":[],"referenced_wops":[],"pending_approvals":[],"active_execution_sessions":[],"recent_engineering_actions":[],"non_authoritative":True}
        return json.loads(self.path.read_text())
    def record(self,request,response):
        data=self.load(); data["conversation"].append({"request":request,"response":response})
        data["recent_engineering_actions"]=(data["recent_engineering_actions"]+[response["intent"]])[-10:]
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix=".context.")
        try:
            with os.fdopen(fd,"w") as f: json.dump(data,f,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        return data

class EngineeringExplanationEngine:
    """Read-only explanations over records produced by existing EMP services."""
    SUPPORTED = {
        "mission_selection": ("selected_mission", "policy_evaluations"),
        "eligibility": ("mission_id", "eligibility_reasons"),
        "approval": ("approval_request_id", "status"),
        "qualification": ("qualification_id", "qualification_decision"),
        "reconciliation": ("plan_id", "targets"),
        "validation": ("admission_decision", "validation_failures"),
    }
    def explain(self,kind,record):
        if kind not in self.SUPPORTED: raise ReasoningError("unsupported explanation kind")
        missing=[x for x in self.SUPPORTED[kind] if x not in record]
        if missing: raise ReasoningError("explanation record is incomplete: "+",".join(missing))
        return {"kind":kind,"facts":{x:deepcopy(record[x]) for x in self.SUPPORTED[kind]},
                "authoritative_record_digest":submission_digest(record),
                "authoritative_references":[CONTRACT["procedure"],CONTRACT["template"]],
                "recommendation_only":True}

class ConversationEngine:
    def __init__(self,guidance=None): self.guidance=guidance or WopGuidanceService()
    def respond(self,request,*,repository=None,package=None,rejection=None,status=None):
        normalized=" ".join(request.lower().strip().rstrip(".?").split())
        if normalized in {"show me the wop template","show wop template"}:
            payload=self.guidance.template(); intent="WOP_TEMPLATE"
        elif normalized in {"what is required in a wop","show wop requirements"}:
            payload=self.guidance.requirements(); intent="WOP_REQUIREMENTS"
        elif normalized in {"show me a wop example","show wop example"}:
            payload=self.guidance.example(); intent="WOP_EXAMPLE"
        elif normalized.startswith("validate this wop"):
            if package is None or repository is None: raise ReasoningError("package and repository are required")
            payload=self.guidance.validate(package,repository); intent="WOP_VALIDATE"
        elif normalized.startswith("explain why this wop was rejected"):
            if rejection is None: raise ReasoningError("rejection record is required")
            payload=self.guidance.explain_rejection(rejection); intent="REJECTION_EXPLAIN"
        elif "status" in normalized:
            payload=status or {}; intent="ENGINEERING_STATUS"
        elif any(word in normalized for word in ("plan","prepare","guidance","question","repository")):
            payload={"recommendation":"Prepare bounded, reviewable work; validate through admission before orchestration.",
                     "authoritative_references":[CONTRACT["procedure"],CONTRACT["template"]],
                     "no_engineering_action_performed":True}; intent="SUPERVISED_GUIDANCE"
        else: raise ReasoningError("request is outside deterministic supervised conversation intents")
        return {"intent":intent,"request":request,"response":payload,"recommendation_only":True}
