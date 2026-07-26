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

from scripts.lib.emp.authority_publication import commissioning_status
from scripts.lib.emp.authority_resolution import (
    AuthorityResolutionRuntime,
    canonical_json,
    digest,
    load_authority_state,
)
from scripts.lib.emp.owner_enrollment import enrollment_status
from scripts.lib.emp.production_execution import dispatch_readiness
from scripts.lib.emp.reasoning import WopGenerator
from scripts.lib.emp.wop_admission import AdmissionController
from scripts.lib.emp.wop_service import OperationalWopService


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
        self.authority_state_path = (
            Path(authority_state_path)
            if authority_state_path is not None
            else self.root / "engineering/authority/operational-authority-state.yaml"
        )
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
        required = {"mode", "intent", "mission_id", "repository"}
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
        if request["mode"] == "qualification":
            context = {
                "mode": "qualification",
                "approval_authority": "PLACEHOLDER-APPROVAL-AUTHORITY",
                "approval_reference": "PLACEHOLDER-APPROVAL-REFERENCE",
                "approval_date": "1970-01-01",
                "authority_node_id": "PLACEHOLDER-AUTHORITY-NODE",
                "adr_reference": "PLACEHOLDER-ADR",
                "immutable_wop_reference": "PLACEHOLDER-IMMUTABLE-WOP",
            }
            state["artifacts"]["authority_context"] = context
            return {
                "authority_mode": "qualification-placeholder",
                "operational_authority_allocated": False,
            }
        commissioning = self.commissioning_probe(self.root)
        owners = self.enrollment_probe(self.root)
        if commissioning["commissioning_state"] != "READY":
            raise StageBlocked(
                "OPERATIONAL_READINESS_BLOCKER",
                "operational authority infrastructure is not commissioned",
                {"commissioning": commissioning, "owner_enrollment": owners},
            )
        try:
            bundle = AuthorityResolutionRuntime(
                self.root, load_authority_state(self.authority_state_path)
            ).resolve(
                mission_id=request["mission_id"],
                work_item_id=request["work_item_id"],
                principal_id=request["principal_id"],
                issued_at=at,
            )
        except ValueError as error:
            raise StageBlocked(
                "AUTHORITY_FAILURE", str(error), {"source": str(self.authority_state_path)}
            ) from error
        state["artifacts"]["authority_context"] = bundle
        return {
            "authority_mode": "operational",
            "resolution_id": bundle["resolution_id"],
            "bundle_digest": bundle["bundle_digest"],
        }

    def _stage_wop_generation(self, state, at):
        request = state["request"]
        authority = state["artifacts"]["authority_context"]
        if request["mode"] == "qualification":
            result = WopGenerator().generate(
                intent=request["intent"],
                mission_id=request["mission_id"],
                phase_id=request.get("phase_id") or "QUALIFICATION-PHASE",
                repository_identity=str(self.root),
                submitter_identity=request.get("submitter_identity")
                or "qualification-operator",
                approval_authority=authority["approval_authority"],
                approval_reference=authority["approval_reference"],
                approval_date=authority["approval_date"],
                authority_node_id=authority["authority_node_id"],
                adr_reference=authority["adr_reference"],
                immutable_wop_reference=authority["immutable_wop_reference"],
            )
        else:
            result = OperationalWopService().generate(
                intent=request["intent"],
                bundle=authority,
                repository_root=self.root,
                at=at,
            )
        state["artifacts"]["wop_result"] = result
        return {
            "wop_id": result["wop"]["wop_id"],
            "submission_digest": result["wop"]["submission_digest"],
            "review_required": result["review_required"],
            "automatically_submitted": result["automatically_submitted"],
        }

    def _stage_submission_eligibility(self, state, at):
        request = state["request"]
        wop = state["artifacts"]["wop_result"]["wop"]
        failures = AdmissionController().validate(wop, str(self.root))
        if failures:
            raise StageBlocked(
                "ADMISSION_VALIDATION_FAILURE",
                "generated WOP failed admission validation",
                {"failures": [failure.to_mapping() for failure in failures]},
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
        if request["mode"] == "qualification":
            decision = {
                "admission_decision": "QUALIFICATION_ONLY",
                "submission_eligible": False,
                "review_required": True,
                "automatically_submitted": False,
                "dispatch_permitted": False,
            }
        else:
            decision = AdmissionController().decide(
                wop, expected_repository=str(self.root), evaluated_at=at
            ).data
            decision["submission_eligible"] = (
                decision["admission_decision"] == "ACCEPTED"
            )
            decision["automatically_submitted"] = False
            readiness = self.dispatch_probe(
                repository=str(self.root),
                baseline=state["artifacts"]["repository_baseline"],
                mission_class=str(wop.get("mission_class", "engineering")),
            )
            decision["dispatch_permitted"] = readiness["dispatch_permitted"]
            decision["dispatch_readiness"] = readiness
        state["artifacts"]["admission_decision"] = decision
        return decision

    def _production_dispatch_readiness(self, *, repository, baseline, mission_class):
        runtime = self.root / ".zeus/runtime"
        return dispatch_readiness(
            repository=repository,
            baseline=baseline,
            activation_path=self.root / "engineering/dispatch/dispatcher-activation.json",
            registry_path=self.root / "engineering/dispatch/execution-agent-registry.json",
            mission_class=mission_class,
            required_paths=(
                self.root / "engineering/dispatch/dispatcher-policy.yaml",
                self.root / "engineering/eens/production-eens-policy.yaml",
                self.root / "engineering/evidence/production-evidence-policy.yaml",
                self.root / "engineering/reconciliation/production-reconciliation-policy.yaml",
                runtime,
            ),
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
        }
        if value["mode"] not in {"qualification", "operational"}:
            raise MissionAdmissionError("mode must be qualification or operational")
        return value

    @staticmethod
    def _time(value):
        if value.tzinfo is None:
            raise MissionAdmissionError("timestamp must include timezone")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
