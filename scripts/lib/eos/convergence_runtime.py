"""Fail-closed Operational Alpha convergence runtime services.

This module is deliberately storage-neutral.  It resolves authoritative facts
from their controlled locations, produces only derived receipts/projections,
and never advances a WOP or writes an authoritative record.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Mapping

import yaml


class ConvergenceRuntimeError(ValueError):
    """The convergence authority chain cannot be resolved safely."""


OUTCOMES = {
    "RESOLVED", "NOT_FOUND", "AMBIGUOUS_RESOLUTION", "INTEGRITY_FAILURE",
    "INCOMPATIBLE_VERSION", "PRECONDITION_FAILED",
}
WOP_STATES = {
    "DRAFT", "READY", "ACTIVE", "EXECUTING", "VERIFIED", "QUALIFIED",
    "ACCEPTED", "CLOSED", "BLOCKED", "SUPERSEDED", "ARCHIVED",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ConvergenceRuntimeError(f"cannot read {path}: {error}") from error
    if not isinstance(value, Mapping):
        raise ConvergenceRuntimeError(f"{path} must be a mapping")
    return dict(value)


class ConvergenceRuntime:
    """Read-only EMM resolver and deterministic integration facade."""

    VERSION = "zeus-convergence-runtime/1"

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.emm_path = self.root / "engineering/metadata/operational-alpha-emm.yaml"

    def _path(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if self.root not in path.parents and path != self.root:
            raise ConvergenceRuntimeError("metadata source escapes repository")
        return path

    def emm(self) -> dict[str, Any]:
        value = load_mapping(self.emm_path)
        if value.get("schema_version") != 1:
            raise ConvergenceRuntimeError("unsupported EMM schema")
        if value.get("baseline_id") != "OA-IMPLEMENTATION-BASELINE-1.0":
            raise ConvergenceRuntimeError("EMM baseline binding is invalid")
        if not isinstance(value.get("entities"), list):
            raise ConvergenceRuntimeError("EMM entities are missing")
        return value

    def _entity(self, entity_type: str, entity_id: str, revision: str | int | None = None) -> dict[str, Any]:
        matches = [
            dict(item) for item in self.emm()["entities"]
            if isinstance(item, Mapping)
            and item.get("entity_type") == entity_type
            and item.get("entity_id") == entity_id
            and (revision is None or str(item.get("revision")) == str(revision))
        ]
        if not matches:
            raise ConvergenceRuntimeError(f"EMM entity not found: {entity_type}/{entity_id}")
        if len(matches) != 1:
            raise ConvergenceRuntimeError(f"EMM entity is ambiguous: {entity_type}/{entity_id}")
        entity = matches[0]
        for required in ("revision", "authoritative_owner", "source", "classification"):
            if not entity.get(required):
                raise ConvergenceRuntimeError(f"EMM entity lacks {required}")
        return entity

    def _source(self, entity: Mapping[str, Any]) -> tuple[Path, str]:
        path = self._path(str(entity["source"]))
        if not path.is_file() or path.is_symlink():
            raise ConvergenceRuntimeError(f"authoritative source unavailable: {entity['source']}")
        source_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_digest = entity.get("source_digest")
        if expected_digest is not None and expected_digest != source_digest:
            raise ConvergenceRuntimeError(
                f"authoritative source digest differs: {entity['source']}"
            )
        return path, source_digest

    def execution_contract(self) -> tuple[dict[str, Any], dict[str, Any], str]:
        """Resolve the authoritative contract that selects a WOP gate plan."""
        entity = self._entity(
            "OperationalExecutionContract", "OPERATIONAL-ALPHA-EXECUTION-CONTRACT", "1.0"
        )
        if not entity.get("source_digest"):
            raise ConvergenceRuntimeError("execution contract lacks EMM source digest")
        path, source_digest = self._source(entity)
        contract = load_mapping(path)
        required = {
            "contract_id": "OPERATIONAL-ALPHA-EXECUTION-CONTRACT",
            "revision": "1.0",
            "classification": "Authoritative",
            "baseline_id": self.emm()["baseline_id"],
            "lifecycle_state": "READY",
        }
        for field, expected in required.items():
            if str(contract.get(field)) != expected:
                raise ConvergenceRuntimeError(f"execution contract {field} is invalid")
        resolution = contract.get("gate_plan_resolution")
        if not isinstance(resolution, Mapping) or resolution.get("entity_type") != "OperationalGatePlan":
            raise ConvergenceRuntimeError("execution contract gate-plan resolution is invalid")
        return entity, contract, source_digest

    def operational_gate_plan(
        self, *, wop_id: str, revision: str | int
    ) -> tuple[dict[str, Any], dict[str, Any], str]:
        """Resolve a published, exact, handler-compatible plan without deriving it."""
        self.execution_contract()
        entity = self._entity("OperationalGatePlan", wop_id, revision)
        if entity.get("classification") != "Authoritative" or not entity.get("source_digest"):
            raise ConvergenceRuntimeError("Operational Gate Plan lacks authoritative source identity")
        path, source_digest = self._source(entity)
        plan_record = load_mapping(path)
        binding = plan_record.get("implementation_wop")
        if (
            plan_record.get("baseline_id") != self.emm()["baseline_id"]
            or not isinstance(binding, Mapping)
            or binding.get("wop_id") != wop_id
            or str(binding.get("revision")) != str(revision)
            or str(plan_record.get("lifecycle_state", "")).upper() != "ACTIVE"
            or not isinstance(plan_record.get("gate_plan"), Mapping)
        ):
            raise ConvergenceRuntimeError("Operational Gate Plan binding or lifecycle is invalid")
        return entity, plan_record, source_digest

    def _wop(self, wop_id: str, revision: str | int) -> tuple[dict[str, Any], dict[str, Any], str]:
        entity = self._entity("ImplementationWOP", wop_id, revision)
        path, source_digest = self._source(entity)
        wop = load_mapping(path)
        if wop.get("wop_id") != wop_id or str(wop.get("revision")) != str(revision):
            raise ConvergenceRuntimeError("Implementation WOP identity differs from EMM")
        status = str(wop.get("status", "")).upper()
        if status not in WOP_STATES:
            raise ConvergenceRuntimeError("Implementation WOP lifecycle state is invalid")
        context = wop.get("execution_context")
        if not isinstance(context, Mapping) or context.get("baseline_id") != self.emm()["baseline_id"]:
            raise ConvergenceRuntimeError("Implementation WOP baseline binding is invalid")
        return entity, wop, source_digest

    def _authority(self, authority_id: str | None) -> tuple[dict[str, Any], str] | None:
        if authority_id is None:
            return None
        entity = self._entity("AuthorityRecord", authority_id)
        path, source_digest = self._source(entity)
        record = load_mapping(path)
        if record.get("authority_record_id") != authority_id:
            raise ConvergenceRuntimeError("Authority Record identity differs from EMM")
        return record, source_digest

    def resolve(self, *, wop_id: str, revision: str | int, action: str,
                correlation_id: str, authority_record_id: str | None = None) -> dict[str, Any]:
        """Resolve the exact governed chain without causing any lifecycle effect."""
        receipt: dict[str, Any] = {
            "schema_version": 1, "resolver_version": self.VERSION,
            "correlation_id": correlation_id, "requested_action": action,
            "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0",
            "inputs": {"implementation_wop": {"id": wop_id, "revision": str(revision)}},
            "outcome": "PRECONDITION_FAILED", "reasons": [],
        }
        try:
            wop_entity, wop, wop_digest = self._wop(wop_id, revision)
            receipt["inputs"]["implementation_wop"].update({
                "owner": wop_entity["authoritative_owner"], "source_digest": wop_digest,
                "status": wop["status"],
            })
            authority = self._authority(authority_record_id)
            if authority is None:
                receipt["reasons"].append("AUTHORITY_RECORD_REQUIRED")
            else:
                record, authority_digest = authority
                receipt["inputs"]["authority_record"] = {
                    "id": authority_record_id, "source_digest": authority_digest,
                    "owner": "Governance",
                }
                permitted = record.get("permitted_actions", [])
                binding = record.get("implementation_wop", {})
                if (record.get("baseline_id") != receipt["baseline_id"]
                        or str(binding.get("wop_id")) != wop_id
                        or str(binding.get("revision")) != str(revision)
                        or action not in permitted):
                    receipt["reasons"].append("AUTHORITY_RECORD_NOT_APPLICABLE")
                elif str(record.get("lifecycle_state", "")).upper() != "ACTIVE":
                    receipt["reasons"].append("AUTHORITY_RECORD_NOT_ACTIVE")
                elif str(wop.get("status", "")).upper() != "ACTIVE":
                    receipt["reasons"].append("WOP_NOT_ACTIVE")
                else:
                    receipt["outcome"] = "RESOLVED"
            receipt["emm_digest"] = digest(self.emm())
        except ConvergenceRuntimeError as error:
            receipt["outcome"] = "NOT_FOUND" if "not found" in str(error) else "INTEGRITY_FAILURE"
            receipt["reasons"].append(str(error))
        receipt["receipt_digest"] = digest({k: v for k, v in receipt.items() if k != "receipt_digest"})
        return receipt

    def capabilities(self) -> dict[str, Any]:
        return {
            "authority_resolution": "READY", "emm_resolution": "READY",
            "implementation_wop_resolution": "READY", "generated_artifacts": "READY",
            "eos_synchronization": "READY", "eens_event_contract": "READY",
            "emp_receipts": "READY", "qualification_interface": "READY",
            "lifecycle_management": "READ_ONLY_READY",
        }

    def generated_artifact(self, *, artifact_id: str, source_entities: list[dict[str, str]]) -> dict[str, Any]:
        """Build a reproducible, non-authoritative artifact manifest."""
        for source in source_entities:
            self._entity(source["entity_type"], source["entity_id"], source.get("revision"))
        artifact = {
            "schema_version": 1, "artifact_id": artifact_id, "classification": "Derived",
            "generator_version": self.VERSION, "metadata_version": self.emm()["version"],
            "source_entities": source_entities, "synchronization_status": "CURRENT",
            "qualification_status": "NOT_READY",
        }
        artifact["artifact_digest"] = digest(artifact)
        return artifact

    def synchronization_plan(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Return an idempotent projection plan; this does not mutate EOS or EENS."""
        if receipt.get("outcome") not in OUTCOMES:
            raise ConvergenceRuntimeError("receipt outcome is invalid")
        plan = {
            "schema_version": 1, "source": "Metadata Engine", "direction": "authoritative_to_derived",
            "trigger": "resolved_receipt", "eos": "idempotent_projection",
            "eens": "append_by_event_identity", "receipt_digest": receipt.get("receipt_digest"),
        }
        plan["plan_digest"] = digest(plan)
        return plan

    def eens_event(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Create the EENS append contract without appending an event itself."""
        value = {
            "schema_version": "1.0", "event_type": "convergence.resolution",
            "source": "Zeus", "subject": str(receipt["inputs"]["implementation_wop"]["id"]),
            "idempotency_key": f"convergence:{receipt['receipt_digest']}",
            "payload": {"receipt_digest": receipt["receipt_digest"], "outcome": receipt["outcome"],
                        "baseline_id": receipt["baseline_id"]},
        }
        value["event_digest"] = digest(value)
        return value

    def emp_receipt(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Produce the read-only EMP planning projection required by SPEC-0014."""
        value = {"schema_version": 1, "producer": "Metadata Engine", "consumer": "EMP",
                 "direction": "metadata_to_plan_projection", "receipt_digest": receipt["receipt_digest"],
                 "outcome": receipt["outcome"], "baseline_id": receipt["baseline_id"]}
        value["projection_digest"] = digest(value)
        return value

    def qualify(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        result = "PASS" if receipt.get("outcome") == "RESOLVED" else "NOT_READY"
        value = {"schema_version": 1, "engine": "Qualification Engine", "result": result,
                 "subject_receipt": receipt.get("receipt_digest"), "criteria": [
                     "identity", "lineage", "ownership", "compatibility", "lifecycle", "synchronization"]}
        value["qualification_digest"] = digest(value)
        return value

    def execution_flow(self, *, wop_id: str, revision: str | int, action: str,
                       correlation_id: str, authority_record_id: str | None = None) -> dict[str, Any]:
        """Resolve the complete non-mutating runtime flow used by Zeus dispatch.

        The returned envelope is the only admission input for an execution
        runtime.  Its construction has no lifecycle or transport side effect.
        """
        receipt = self.resolve(wop_id=wop_id, revision=revision, action=action,
                               correlation_id=correlation_id,
                               authority_record_id=authority_record_id)
        artifact = self.generated_artifact(
            artifact_id=f"EXECUTION-PLAN-{wop_id}-{revision}",
            source_entities=[{"entity_type": "ImplementationWOP", "entity_id": wop_id,
                              "revision": str(revision)}],
        )
        flow = {"schema_version": 1, "authority_receipt": receipt,
                "generated_artifact": artifact,
                "synchronization": self.synchronization_plan(receipt),
                "eens_event": self.eens_event(receipt),
                "emp_projection": self.emp_receipt(receipt),
                "qualification": self.qualify(receipt),
                "execution_admitted": receipt["outcome"] == "RESOLVED"}
        flow["flow_digest"] = digest(flow)
        return flow

    def operational_execution_context(
        self,
        *,
        flow: Mapping[str, Any],
        execution_id: str,
        mission_id: str,
        repository: Path | str,
        repository_baseline: str,
        wop_submission_digest: str,
        workspace: Path | str,
    ) -> dict[str, Any]:
        """Assemble a derived handler context from a resolved flow and plan.

        This method is intentionally incapable of constructing a plan.  A
        missing or malformed EMM-registered plan leaves the execution path
        blocked before a handler receives a context.
        """
        if not flow.get("execution_admitted"):
            raise ConvergenceRuntimeError("resolved convergence authority is required")
        receipt = flow.get("authority_receipt")
        if not isinstance(receipt, Mapping) or receipt.get("outcome") != "RESOLVED":
            raise ConvergenceRuntimeError("execution flow receipt is not resolved")
        wop_input = receipt.get("inputs", {}).get("implementation_wop", {})
        if not isinstance(wop_input, Mapping):
            raise ConvergenceRuntimeError("execution flow lacks Implementation WOP input")
        _, plan_record, plan_digest = self.operational_gate_plan(
            wop_id=str(wop_input.get("id", "")), revision=str(wop_input.get("revision", ""))
        )
        from scripts.lib.emp.operational_gate_handler import OperationalExecutionContextService

        return OperationalExecutionContextService.create(
            execution_id=execution_id,
            mission_id=mission_id,
            repository=repository,
            repository_baseline=repository_baseline,
            wop_submission_digest=wop_submission_digest,
            workspace=workspace,
            gate_plan=plan_record["gate_plan"],
            authorization={
                "decision": "AUTHORIZED",
                "execution_id": execution_id,
                "reference": receipt["receipt_digest"],
                "operational_gate_plan_digest": plan_digest,
            },
        )

    def operational_wop(self, *, intent: str, flow: Mapping[str, Any]) -> dict[str, Any]:
        """Render an admission-compatible WOP only from a resolved flow."""
        if not flow.get("execution_admitted"):
            raise ConvergenceRuntimeError("resolved convergence authority is required")
        from scripts.lib.emp.wop_admission import CONTRACT, submission_digest
        receipt = flow["authority_receipt"]
        source = self._wop(receipt["inputs"]["implementation_wop"]["id"],
                           receipt["inputs"]["implementation_wop"]["revision"])[1]
        wop_id = "WOP-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json({
            "flow": flow["flow_digest"], "intent": intent.strip()})))
        sections = {name: f"Convergence-derived: {intent.strip()}" for name in CONTRACT["required_sections"]}
        value = {"schema_version": 1, "document_type": "EngineeringWorkOrder", "wop_id": wop_id,
                 "mission_id": source["mission_id"], "phase_id": source["phase_id"], "revision": 1,
                 "status": "Active", "title": intent.strip(), "repository_identity": str(self.root),
                 "submitter_identity": "convergence-runtime", "approval": {
                     "authority": "Governance", "reference": receipt["inputs"]["authority_record"]["id"],
                     "date": "1970-01-01T00:00:00+00:00", "authorized_lifecycle_state": "Active"},
                 "execution_package_references": {
                     "authority_node_id": receipt["receipt_digest"],
                     "authorization_decision_record": flow["qualification"]["qualification_digest"],
                     "immutable_wop": source["wop_id"]},
                 "authoritative_references": [CONTRACT["procedure"], CONTRACT["template"], *CONTRACT["standards"]],
                 "sections": sections, "convergence_flow_digest": flow["flow_digest"]}
        value["submission_digest"] = submission_digest(value)
        return {"wop": value, "authority_resolved": True, "review_required": True,
                "automatically_submitted": False, "convergence_flow": dict(flow)}
