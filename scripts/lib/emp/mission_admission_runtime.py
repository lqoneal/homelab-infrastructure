#!/usr/bin/env python3
"""Restartable supervised Mission Admission Runtime."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.authority_publication import commissioning_status
from scripts.lib.emp.authority_resolution import (
    canonical_json,
    digest,
)
from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.emp.owner_enrollment import enrollment_status
from scripts.lib.emp.production_execution import dispatch_readiness
from scripts.lib.emp.reasoning import WopGenerator
from scripts.lib.emp.wop_admission import AdmissionController, CONTRACT
from scripts.lib.emp.wop_service import OperationalWopService
from scripts.lib.emp.stage1_runtime import Stage1Runtime, validate_package
from scripts.lib.eos.mission_contract import load as load_mission_contract, validate as validate_mission_contract


class MissionAdmissionError(ValueError):
    """Mission admission state or request is invalid."""


class StageBlocked(MissionAdmissionError):
    def __init__(self, category: str, message: str, diagnostics: Any = None):
        self.category = category
        self.diagnostics = diagnostics
        super().__init__(message)


STAGES = (
    "MISSION_VALIDATION",
    "REPOSITORY_VERIFICATION",
    "MISSION_QUALIFICATION",
    "AUTHORITY_RESOLUTION",
    "WOP_GENERATION",
    "SUBMISSION_ELIGIBILITY",
    "ADMISSION_DECISION",
)


def admission_identifier(request: Mapping[str, Any]) -> str:
    return "MISSION-ADMISSION-" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(request))
    )


class AdmissionStateStore:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def path(self, admission_id: str) -> Path:
        return self.directory / f"{admission_id}.json"

    def load(self, admission_id: str) -> dict[str, Any]:
        try:
            value = json.loads(self.path(admission_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MissionAdmissionError(f"invalid admission state: {error}") from error
        if not isinstance(value, dict):
            raise MissionAdmissionError("admission state must be an object")
        supplied = value.pop("state_digest", None)
        if supplied != digest(value):
            raise MissionAdmissionError("admission state digest mismatch")
        value["state_digest"] = supplied
        return value

    def save(self, value: Mapping[str, Any]) -> Path:
        data = deepcopy(dict(value))
        data.pop("state_digest", None)
        data["state_digest"] = digest(data)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.path(str(data["admission_id"]))
        descriptor, temporary = tempfile.mkstemp(dir=self.directory, prefix=".admission.")
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(data, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return path


class MissionAdmissionRuntime:
    """One state machine for qualification and operational admission."""

    VERSION = "zeus-mission-admission/1"

    def __init__(
        self,
        repository_root: Path | str,
        store: AdmissionStateStore,
        *,
        authority_state_path: Path | str | None = None,
        commissioning_probe=None,
        enrollment_probe=None,
        dispatch_probe=None,
    ):
        self.root = Path(repository_root).resolve()
        self.store = store
        self.authority_state_path = None
        self.commissioning_probe = commissioning_probe or commissioning_status
        self.enrollment_probe = enrollment_probe or enrollment_status
        self.dispatch_probe = dispatch_probe or self._production_dispatch_readiness

    def start(
        self,
        request: Mapping[str, Any],
        *,
        at: datetime,
        max_stages: int | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_request(request)
        admission_id = admission_identifier(normalized)
        path = self.store.path(admission_id)
        if path.exists():
            state = self.store.load(admission_id)
            if state["request"] != normalized:
                raise MissionAdmissionError("admission identity collision")
            return self.run(admission_id, at=at, max_stages=max_stages)
        state = {
            "schema_version": 1,
            "runtime_version": self.VERSION,
            "admission_id": admission_id,
            "request": normalized,
            "request_digest": digest(normalized),
            "status": "REQUESTED",
            "current_stage": STAGES[0],
            "completed_stages": [],
            "evidence": [],
            "artifacts": {},
            "failure": None,
            "created_at": self._time(at),
            "updated_at": self._time(at),
        }
        self.store.save(state)
        return self.run(admission_id, at=at, max_stages=max_stages)

    def run(
        self, admission_id: str, *, at: datetime, max_stages: int | None = None
    ) -> dict[str, Any]:
        state = self.store.load(admission_id)
        if state["status"] == "DECIDED":
            return state
        state["status"] = "RUNNING"
        state["failure"] = None
        executed = 0
        while state["current_stage"] is not None:
            if max_stages is not None and executed >= max_stages:
                state["status"] = "INTERRUPTED"
                state["updated_at"] = self._time(at)
                self.store.save(state)
                return self.store.load(admission_id)
            stage = state["current_stage"]
            try:
                payload = self._execute(stage, state, at)
            except StageBlocked as error:
                state["status"] = "BLOCKED"
                state["failure"] = {
                    "stage": stage,
                    "category": error.category,
                    "message": str(error),
                    "diagnostics": error.diagnostics,
                    "retryable": True,
                }
                self._record_evidence(state, stage, "BLOCKED", state["failure"], at)
                state["updated_at"] = self._time(at)
                self.store.save(state)
                return self.store.load(admission_id)
            self._record_evidence(state, stage, "COMPLETED", payload, at)
            state["completed_stages"].append(stage)
            state["current_stage"] = (
                STAGES[STAGES.index(stage) + 1] if stage != STAGES[-1] else None
            )
            state["updated_at"] = self._time(at)
            state["status"] = "DECIDED" if state["current_stage"] is None else "RUNNING"
            self.store.save(state)
            executed += 1
        return self.store.load(admission_id)

    def _execute(
        self, stage: str, state: dict[str, Any], at: datetime
    ) -> dict[str, Any]:
        method = getattr(self, f"_stage_{stage.lower()}")
        return method(state, at)

    def _stage_mission_validation(self, state, at):
        request = state["request"]
        required = {"mode", "mission_id", "repository"}
        missing = sorted(field for field in required if not request.get(field))
        if missing:
            raise StageBlocked(
                "VALIDATION_FAILURE",
                "mission request is incomplete",
                {"missing_fields": missing},
            )
        if request["mode"] == "operational" and (
            not request.get("work_item_id") or not request.get("principal_id")
        ):
            raise StageBlocked(
                "VALIDATION_FAILURE",
                "operational request requires work item and principal",
                {"missing_fields": ["work_item_id", "principal_id"]},
            )
        return {"request_digest": state["request_digest"], "validation": "PASS"}

    def _stage_repository_verification(self, state, at):
        requested = Path(state["request"]["repository"]).resolve()
        discovered = self._git("rev-parse", "--show-toplevel")
        baseline = self._git("rev-parse", "HEAD")
        if requested != self.root or Path(discovered).resolve() != self.root:
            raise StageBlocked(
                "REPOSITORY_FAILURE",
                "repository identity mismatch",
                {"requested": str(requested), "discovered": discovered},
            )
        state["artifacts"]["repository_baseline"] = baseline
        return {
            "repository": str(self.root),
            "baseline_commit": baseline,
            "verification": "PASS",
        }

    def _stage_mission_qualification(self, state, at):
        mode = state["request"]["mode"]
        result = (
            "QUALIFIED_NON_OPERATIONAL"
            if mode == "qualification"
            else "DELEGATED_TO_AUTHORITATIVE_MISSION_RECORD"
        )
        state["artifacts"]["qualification"] = result
        return {"qualification": result, "mode": mode}

    def _stage_authority_resolution(self, state, at):
        request = state["request"]
        # Retain the historical non-authoritative qualification fixture and the
        # explicit convergence compatibility path. Published mission contracts
        # always take the canonical branch below.
        if request["mode"] == "operational" and request.get("implementation_wop_id"):
            flow = ConvergenceRuntime(self.root).execution_flow(
                wop_id=request["implementation_wop_id"], revision=request["implementation_wop_revision"],
                action="admit_mission", correlation_id=request["correlation_id"],
                authority_record_id=request.get("authority_record_id"),
            )
            if not flow["execution_admitted"]:
                raise StageBlocked("AUTHORITY_FAILURE", "convergence authority is not resolved", flow["authority_receipt"])
            state["artifacts"]["authority_context"] = flow
            return {"authority_mode": "operational-compatibility", "resolution_id": flow["authority_receipt"]["receipt_digest"], "bundle_digest": flow["flow_digest"]}
        if request["mode"] == "operational" and not (self.root / "engineering/mission-contracts/contracts" / f"{request['mission_id']}.yaml").is_file():
            raise StageBlocked("AUTHORITY_FAILURE", "convergence Implementation WOP is required")
        if request["mode"] == "qualification" and request["mission_id"].startswith("ZEUS-") and not (self.root / "engineering/mission-contracts/contracts" / f"{request['mission_id']}.yaml").is_file():
            context = {"mode": "qualification", "approval_authority": "PLACEHOLDER-APPROVAL-AUTHORITY", "approval_reference": "PLACEHOLDER-APPROVAL-REFERENCE", "approval_date": "1970-01-01", "authority_node_id": "PLACEHOLDER-AUTHORITY-NODE", "adr_reference": "PLACEHOLDER-ADR", "immutable_wop_reference": "PLACEHOLDER-IMMUTABLE-WOP"}
            state["artifacts"]["authority_context"] = context
            return {"authority_mode": "qualification-placeholder", "operational_authority_allocated": False}
        binding = self._resolve_published_binding(state)
        state["artifacts"]["authority_context"] = binding
        return {
            "authority_mode": state["request"]["mode"],
            "authority_source": binding["authority"]["source"],
            "contract_id": binding["mission_contract"]["contract_id"],
            "wop_id": binding["wop"]["wop_id"],
            "package_digest": binding["wop"]["package_digest"],
            "operational_authority_allocated": state["request"]["mode"] == "operational",
        }

    def _stage_wop_generation(self, state, at):
        request = state["request"]
        binding = state["artifacts"]["authority_context"]
        if "admission" not in binding:
            if request["mode"] == "qualification":
                result = WopGenerator().generate(
                    intent=request["intent"], mission_id=request["mission_id"],
                    phase_id=request.get("phase_id") or "QUALIFICATION-PHASE",
                    repository_identity=str(self.root),
                    submitter_identity=request.get("submitter_identity") or "qualification-operator",
                    approval_authority="PLACEHOLDER-APPROVAL-AUTHORITY",
                    approval_reference="PLACEHOLDER-APPROVAL-REFERENCE",
                    approval_date="1970-01-01", authority_node_id="PLACEHOLDER-AUTHORITY-NODE",
                    adr_reference="PLACEHOLDER-ADR", immutable_wop_reference="PLACEHOLDER-IMMUTABLE-WOP",
                )
                state["artifacts"]["wop_result"] = result
                return {"wop_id": result["wop"]["wop_id"], "submission_digest": result["wop"]["submission_digest"], "review_required": True, "automatically_submitted": False}
            result = ConvergenceRuntime(self.root).operational_wop(intent=request["intent"], flow=binding)
            state["artifacts"]["wop_result"] = result
            return {"wop_id": result["wop"]["wop_id"], "submission_digest": result["wop"]["submission_digest"], "review_required": result["review_required"], "automatically_submitted": result["automatically_submitted"]}
        state["artifacts"]["wop_result"] = {"wop": binding["submission"], "published": True}
        return {
            "wop_id": binding["wop"]["wop_id"],
            "submission_digest": binding["submission"]["submission_digest"],
            "package_digest": binding["wop"]["package_digest"],
            "published_package_reused": True,
            "review_required": True,
            "automatically_submitted": False,
        }

    def _stage_submission_eligibility(self, state, at):
        request = state["request"]
        wop = state["artifacts"]["wop_result"]["wop"]
        failures = (
            self._canonical_binding_failures(state)
            if "admission" in state["artifacts"]["authority_context"]
            else AdmissionController().validate(wop, str(self.root))
        )
        if failures:
            raise StageBlocked(
                "ADMISSION_VALIDATION_FAILURE",
                "canonical mission binding failed admission validation",
                {"failures": [failure.to_mapping() for failure in failures] if failures and hasattr(failures[0], "to_mapping") else failures},
            )
        eligible = request["mode"] == "operational"
        result = {
            "schema_valid": True,
            "submission_eligible": eligible,
            "ineligibility_reason": None if eligible else "QUALIFICATION_MODE",
            "explicit_operator_submission_required": True,
        }
        state["artifacts"]["submission_eligibility"] = result
        return result

    def _stage_admission_decision(self, state, at):
        request = state["request"]
        wop = state["artifacts"]["wop_result"]["wop"]
        authority = state["artifacts"]["authority_context"]
        validation = (
            self._canonical_binding_failures(state)
            if "admission" in authority
            else AdmissionController().validate(wop, str(self.root))
        )
        if validation:
            raise StageBlocked("ADMISSION_VALIDATION_FAILURE", "canonical mission binding failed admission validation", {
                "failures": [failure.to_mapping() for failure in validation] if hasattr(validation[0], "to_mapping") else validation})
        if "admission" not in authority:
            if request["mode"] == "qualification":
                decision = {"admission_decision": "QUALIFICATION_ONLY", "submission_eligible": False, "review_required": True, "automatically_submitted": False, "dispatch_permitted": False}
            else:
                decision = AdmissionController().decide(wop, expected_repository=str(self.root), evaluated_at=at).data
                decision["submission_eligible"] = decision["admission_decision"] == "ACCEPTED"
                decision["automatically_submitted"] = False
                decision["dispatch_permitted"] = bool(authority.get("execution_admitted"))
                decision["dispatch_readiness"] = {"model": "CONVERGENCE_AUTHORITY", "dispatch_permitted": decision["dispatch_permitted"]}
            state["artifacts"]["admission_decision"] = decision
            return decision
        binding = authority["admission"]
        if request["mode"] == "qualification":
            decision = {
                "admission_decision": "QUALIFICATION_ONLY",
                "validation_failures": [],
                "validation_summary": {"failure_count": 0, "reason_codes": []},
                "submission_eligible": False,
                "review_required": True,
                "automatically_submitted": False,
                "dispatch_permitted": False,
            }
        else:
            decision = {
                "admission_decision": "ACCEPTED",
                "validation_failures": [],
                "validation_summary": {"failure_count": 0, "reason_codes": []},
                "submission_digest": wop["submission_digest"],
                "wop_id": wop["wop_id"],
                "mission_id": wop["mission_id"],
                "repository_identity": str(self.root),
                "evaluation_timestamp": self._time(at),
                "validator_version": "published-mission-contract/1",
            }
            decision["submission_eligible"] = (
                decision["admission_decision"] == "ACCEPTED"
            )
            decision["automatically_submitted"] = False
            # Operational Alpha admission is governed by the convergence flow
            # resolved above.  The Progressive PMCT/production-agent dispatcher
            # is a retained compatibility capability, not an OA authority input.
            decision["dispatch_permitted"] = binding["dispatch_permission"]
            decision["dispatch_readiness"] = {
                "model": "PUBLISHED_MISSION_CONTRACT",
                "dispatch_permitted": binding["dispatch_permission"],
                "baseline": binding["repository"]["development_baseline"],
            }
        decision["mission_binding"] = binding
        decision["next_authorized_action"] = (
            "Run independent qualification; do not dispatch."
            if request["mode"] == "qualification"
            else "Proceed to bounded execution only after operational approval."
        )
        state["artifacts"]["admission_decision"] = decision
        return decision

    def _canonical_binding_failures(self, state) -> list[dict[str, str]]:
        binding = state["artifacts"]["authority_context"]
        admission = binding["admission"]
        required = {
            "mission_id": admission.get("mission_id"),
            "wop_id": admission.get("wop_id"),
            "package_digest": admission.get("package_digest"),
            "immutable_manifest_reference": admission.get("immutable_manifest_reference"),
            "authority.source": admission.get("authority", {}).get("source"),
            "approval.authority": admission.get("approval", {}).get("authority"),
            "approval.reference": admission.get("approval", {}).get("reference"),
            "repository.identity": admission.get("repository", {}).get("identity"),
            "repository.development_baseline": admission.get("repository", {}).get("development_baseline"),
        }
        failures: list[dict[str, str]] = []
        for field, value in required.items():
            if value in (None, "", [], {}):
                failures.append({"field": field, "reason_code": "REQUIRED_FIELD_MISSING", "message": f"{field} is unresolved"})
        serialized = json.dumps(binding, sort_keys=True)
        if "PLACEHOLDER-" in serialized or "None" in serialized:
            failures.append({"field": "binding", "reason_code": "PLACEHOLDER_OR_UNRESOLVED_VALUE", "message": "canonical admission binding contains a placeholder or unresolved value"})
        if admission.get("repository", {}).get("identity") != str(self.root):
            failures.append({"field": "repository.identity", "reason_code": "REPOSITORY_IDENTITY_MISMATCH", "message": "repository binding does not match admission target"})
        if admission.get("mission_id") != state["request"]["mission_id"]:
            failures.append({"field": "mission_id", "reason_code": "MISSION_ID_MISMATCH", "message": "submission and contract mission IDs differ"})
        return failures

    def _resolve_published_binding(self, state) -> dict[str, Any]:
        """Resolve one mission contract and its published WOP package.

        This is the shared resolver for qualification and operational admission;
        mode changes only the dispatch boundary.
        """
        request = state["request"]
        mission = request["mission_id"]
        contract_path = self.root / "engineering/mission-contracts/contracts" / f"{mission}.yaml"
        if not contract_path.is_file():
            raise StageBlocked("AUTHORITY_FAILURE", "mission contract is missing", {"mission_id": mission})
        contract = load_mission_contract(contract_path)
        errors = validate_mission_contract(contract, self.root)
        if errors:
            raise StageBlocked("AUTHORITY_FAILURE", "mission contract is invalid", {"errors": errors})
        if contract.get("mission_id") != mission:
            raise StageBlocked("AUTHORITY_FAILURE", "mission contract mission mismatch")
        package_path = self.root / str(contract["wop"]["locator"])
        package_root = package_path.parent
        try:
            metadata, package_evidence = validate_package(package_root)
        except Exception as error:
            raise StageBlocked("PACKAGE_FAILURE", "published WOP package is invalid", {"error": str(error)}) from error
        if metadata.get("mission_id") != mission or metadata.get("wop_id") != contract["wop"]["id"]:
            raise StageBlocked("AUTHORITY_FAILURE", "mission contract and WOP identity disagree", {
                "contract_mission": contract.get("mission_id"), "wop_mission": metadata.get("mission_id"),
                "contract_wop": contract["wop"]["id"], "wop_id": metadata.get("wop_id")})
        package_digest = Stage1Runtime._tree_digest(package_root)
        manifest_path = package_root / "manifests/immutable-manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, Mapping) or manifest.get("wop_id") != metadata["wop_id"]:
            raise StageBlocked("AUTHORITY_FAILURE", "immutable manifest is unresolved or mismatched")
        submitter = request.get("submitter_identity") or request.get("principal_id") or "qualification-operator"
        principal = request.get("principal_id") or submitter
        approval_authority = contract["roles"]["human_authorizer"]
        approval_reference = contract["approvals"].get("authority_reference") or contract["activation"]["record"]
        section_values = {
            "purpose_and_expected_outcome": contract["scope"]["objective"],
            "mission_classification": "Operation Beta / ZDCL development mission",
            "governing_references": "; ".join([str(contract_path.relative_to(self.root)), str(contract["wop"]["locator"])]),
            "scope": "\n".join(f"- {item}" for item in metadata["scope"]),
            "explicit_authority": f"Authorized by {approval_authority}; source {contract_path.relative_to(self.root)}",
            "prohibited_activities": "\n".join(f"- {item}" for item in contract["scope"]["prohibited"]),
            "dependencies_and_entry_criteria": "\n".join(f"- {item}" for item in metadata["dependencies"]),
            "deliverables": "Bounded ZDCL-01 native session foundation and its evidence.",
            "execution_sequence": "Verify identity and baseline; execute the published WOP gates; qualify; reconcile; close out.",
            "success_and_acceptance_criteria": "The published WOP gates and mission contract completion criteria pass.",
            "validation_profile": "Published package validation, mission-contract validation, and independent qualification.",
            "publication_and_synchronization": "Publish only within the authorized Development Engineering Platform workflow.",
            "stop_resume_and_escalation": "Stop on authority, package, repository, baseline, or digest mismatch; resume from the persisted checkpoint.",
            "completion_report_requirement": "Produce the ZDCL-01 completion report and immutable evidence receipt.",
        }
        submission = {
            "schema_version": 1,
            "document_type": "EngineeringWorkOrder",
            "wop_id": metadata["wop_id"],
            "mission_id": mission,
            "phase_id": metadata.get("phase_id") or request.get("phase_id") or "UNSPECIFIED_BY_CONTRACT",
            "revision": metadata.get("revision", 1),
            "status": metadata.get("status", "Active"),
            "title": metadata["title"],
            "repository_identity": str(self.root),
            "submitter_identity": submitter,
            "approval": {
                "authority": approval_authority,
                "reference": approval_reference,
                "status": "approved",
                "authorized_lifecycle_state": "Active",
                "source": f"{contract_path.relative_to(self.root)}:roles.human_authorizer",
            },
            "execution_package_references": {
                "authority_node_id": manifest["authority_source"],
                "authorization_decision_record": approval_reference,
                "immutable_wop": str(manifest_path.relative_to(self.root)),
            },
            "authoritative_references": [CONTRACT["procedure"], CONTRACT["template"], *CONTRACT["standards"], str(contract_path.relative_to(self.root)), str(contract["wop"]["locator"]), *manifest.get("authority_documents", [])],
            "sections": {name: section_values[name] for name in CONTRACT["required_sections"]},
        }
        # The admission controller's schema is for standalone WOP submissions;
        # admission additionally carries the complete canonical binding below.
        submission["submission_digest"] = digest(submission)
        admission = {
            "operation": "BETA",
            "mission_id": mission,
            "mission_family": mission.split("-", 1)[0],
            "title": metadata["title"],
            "purpose": contract["scope"]["objective"],
            "expected_outcome": contract["scope"]["objective"],
            "scope": metadata["scope"],
            "explicit_exclusions": contract["scope"]["prohibited"],
            "dependencies": metadata["dependencies"],
            "prerequisites": metadata["dependencies"],
            "wop_id": metadata["wop_id"],
            "wop_revision": metadata.get("revision", 1),
            "package_path": str(package_root),
            "package_digest": package_digest,
            "immutable_manifest_reference": str(manifest_path.relative_to(self.root)),
            "repository": {"identity": str(self.root), "development_baseline": contract["repository"]["baseline"], "production_baseline": "OA-v1.0.0"},
            "submission_id": self._submission_id(mission, request),
            "work_item": {"state": "NOT_DECLARED_BY_MISSION_CONTRACT", "source": str(contract_path.relative_to(self.root))},
            "submitter": submitter,
            "principal": principal,
            "authority": {"source": str(contract_path.relative_to(self.root)), "owner": approval_authority},
            "approval": {"authority": approval_authority, "reference": approval_reference, "status": "approved", "source": str(contract_path.relative_to(self.root)) + ":approvals"},
            "lifecycle_authorization": contract["lifecycle"],
            "qualification_mode": request["mode"],
            "dispatch_permission": request["mode"] == "operational" and bool(contract["permissions"].get("modify")),
            "correlation_id": request["correlation_id"],
            "package_validation": package_evidence,
        }
        return {"mission_contract": {"contract_id": contract["contract_id"], "path": str(contract_path.relative_to(self.root)), "digest": digest(contract)},
                "wop": {"wop_id": metadata["wop_id"], "package_digest": package_digest, "path": str(package_root)},
                "repository": admission["repository"], "authority": admission["authority"], "admission": admission,
                "submission": submission}

    def _submission_id(self, mission: str, request: Mapping[str, Any]) -> str:
        if request.get("submission_id"):
            return str(request["submission_id"])
        stage_root = self.root / ".zeus/runtime/stage1"
        try:
            record = Stage1Runtime(self.root, stage_root).show(mission)
        except Exception as error:
            raise StageBlocked("SUBMISSION_FAILURE", "authoritative mission submission is unavailable", {
                "mission_id": mission, "error": str(error)}) from error
        if record.get("state") not in {"STAGED", "ADMITTED"}:
            raise StageBlocked("SUBMISSION_FAILURE", "mission submission is not active", {
                "mission_id": mission, "state": record.get("state")})
        return str(record["instance_id"])

    def _effective_agent_registry(self):
        from scripts.lib.emp.agent_qualification import runtime_registry_path
        return runtime_registry_path(self.root)

    def _production_dispatch_readiness(self, *, repository, baseline, mission_class):
        runtime = self.root / ".zeus/runtime"
        return dispatch_readiness(
            repository=repository,
            baseline=baseline,
            activation_path=self.root / "engineering/dispatch/dispatcher-activation.json",
            registry_path=self._effective_agent_registry(),
            mission_class=mission_class,
            required_paths=(
                self.root / "engineering/dispatch/dispatcher-policy.yaml",
                self.root / "engineering/eens/production-eens-policy.yaml",
                self.root / "engineering/evidence/production-evidence-policy.yaml",
                self.root / "engineering/reconciliation/production-reconciliation-policy.yaml",
                runtime,
            ),
            allowed_signers=self.root / "engineering/authority/allowed-signers",
        )

    @staticmethod
    def _record_evidence(state, stage, outcome, payload, at):
        material = {
            "sequence": len(state["evidence"]) + 1,
            "stage": stage,
            "outcome": outcome,
            "observed_at": MissionAdmissionRuntime._time(at),
            "payload": deepcopy(payload),
        }
        material["evidence_digest"] = digest(material)
        state["evidence"].append(material)

    def _git(self, *arguments):
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise StageBlocked(
                "REPOSITORY_FAILURE",
                "repository verification command failed",
                {"stderr": result.stderr.strip()},
            )
        return result.stdout.strip()

    @staticmethod
    def _normalize_request(request):
        value = {
            "mode": request.get("mode"),
            "intent": str(request.get("intent", "")).strip(),
            "mission_id": request.get("mission_id"),
            "phase_id": request.get("phase_id"),
            "work_item_id": request.get("work_item_id"),
            "principal_id": request.get("principal_id"),
            "submitter_identity": request.get("submitter_identity"),
            "repository": str(Path(str(request.get("repository", ""))).resolve())
            if request.get("repository")
            else "",
            "implementation_wop_id": request.get("implementation_wop_id"),
            "implementation_wop_revision": str(request.get("implementation_wop_revision", "1")),
            "authority_record_id": request.get("authority_record_id"),
            "correlation_id": request.get("correlation_id", "mission-admission"),
            "submission_id": request.get("submission_id"),
        }
        if value["mode"] not in {"qualification", "operational"}:
            raise MissionAdmissionError("mode must be qualification or operational")
        return value

    @staticmethod
    def _time(value):
        if value.tzinfo is None:
            raise MissionAdmissionError("timestamp must include timezone")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
