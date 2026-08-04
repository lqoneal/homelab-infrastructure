"""Canonical resolution of receipt-backed Stage 1 submissions for execution.

Stage 1 is the authority for Development submissions.  Admission and
execution files are projections used by the older runtime controllers; they
must not become a second source of identity or authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime


class Stage1ExecutionResolutionError(ValueError):
    """Stage 1 cannot be consumed as an unambiguous execution source."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _find_execution(execution_store: Path, admission_id: str, execution_id: str | None):
    matches = []
    for path in sorted(execution_store.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise Stage1ExecutionResolutionError(f"invalid execution projection: {path.name}: {error}") from error
        supplied_digest = value.get("state_digest")
        if supplied_digest is not None:
            material = dict(value)
            material.pop("state_digest", None)
            if supplied_digest != _digest(material):
                raise Stage1ExecutionResolutionError(f"execution projection digest mismatch: {path.name}")
        if execution_id and value.get("execution_id") != execution_id:
            continue
        if value.get("admission_id") == admission_id:
            matches.append(value)
    if len(matches) > 1:
        raise Stage1ExecutionResolutionError("conflicting execution projections for Stage 1 admission")
    return matches[0] if matches else None


def _derived_admission(record: Mapping[str, Any], admission_id: str) -> dict[str, Any]:
    """Return an in-memory admission projection, never a fabricated receipt."""
    receipts = record.get("receipts") or {}
    admission = receipts.get("admission") or {}
    dispatch = receipts.get("dispatch") or {}
    if admission.get("admission_id") != admission_id:
        raise Stage1ExecutionResolutionError("admission identity is not receipt-backed")
    if record.get("execution_mode") != "DEVELOPMENT":
        raise Stage1ExecutionResolutionError("Stage 1 execution resolution only supports Development")
    package = Path(str(record.get("package", ""))).resolve()
    metadata_path = package / "mission.yaml"
    try:
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise Stage1ExecutionResolutionError(f"authoritative WOP metadata unavailable: {error}") from error
    if not isinstance(metadata, Mapping):
        raise Stage1ExecutionResolutionError("authoritative WOP metadata is not a mapping")
    if metadata.get("mission_id") != record.get("mission_id") or metadata.get("wop_id") != record.get("wop_id"):
        raise Stage1ExecutionResolutionError("Stage 1 and WOP identities conflict")
    submission = {
        "schema_version": 1, "document_type": "EngineeringWorkOrder",
        "wop_id": record["wop_id"], "mission_id": record["mission_id"],
        "phase_id": metadata.get("phase_id", "DEVELOPMENT"),
        "revision": metadata.get("revision", 1), "status": metadata.get("status", "Active"),
        "title": metadata.get("title", record["mission_id"]),
        "repository_identity": record["repository"],
        "submitter_identity": record.get("operator", "stage1"),
        "approval": {"authority": "Engineering Governance", "reference": "STAGE1-RECEIPT-BACKED"},
        "execution_package_references": {"immutable_wop": str(metadata_path)},
        "authoritative_references": ["Stage 1 receipt-backed transaction"],
        "sections": {"purpose_and_expected_outcome": metadata.get("objective", "")},
    }
    submission["submission_digest"] = _digest(submission)
    wop = deepcopy(submission)
    wop["submission_digest"] = submission["submission_digest"]
    return {
        "schema_version": 1, "status": "DECIDED", "admission_state": "ADMITTED",
        "admission_id": admission_id, "runtime_source": "STAGE1_RECEIPT_BACKED",
        "request": {"mode": "qualification", "mission_id": record["mission_id"],
                    "repository": record["repository"], "repository_baseline": record.get("repository_baseline"),
                    "submission_id": record["instance_id"], "principal_id": record.get("operator", "stage1"),
                    "submitter_identity": record.get("operator", "stage1")},
        "artifacts": {
            "repository_baseline": record.get("repository_baseline"),
            "wop_result": {"wop": wop, "published": True},
            "admission_decision": {"admission_decision": "QUALIFICATION_ONLY"},
            "authority_context": {"admission": {"wop_revision": metadata.get("revision", 1), "authority": {"source": "Stage 1"}}},
        },
        "stage1_identity": record["instance_id"],
        "stage1_package_digest": record.get("package_digest"),
        "stage1_authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest"),
        "stage1_dispatch_receipt_id": dispatch.get("receipt_id"),
        "stage1_execution_id": (receipts.get("execution") or {}).get("execution_id"),
    }


def _derived_execution(admission: Mapping[str, Any], record: Mapping[str, Any], execution_id: str) -> dict[str, Any]:
    """Build the legacy execution projection from the canonical Stage 1 binding."""
    wop = admission["artifacts"]["wop_result"]["wop"]
    state = {
        "schema_version": 1,
        "runtime_version": "zeus-mission-execution/1",
        "execution_id": execution_id,
        "admission_id": admission["admission_id"],
        "mode": "qualification",
        "mission_id": wop["mission_id"],
        "wop_id": wop["wop_id"],
        "wop_submission_digest": wop["submission_digest"],
        "repository": admission["request"]["repository"],
        "repository_baseline": admission["request"].get("repository_baseline"),
        "state": "Pending",
        "current_gate": "VALIDATE_WOP",
        "completed_gates": [], "checkpoints": [], "evidence": [],
        "failure": None, "wait_reason": None,
        "stage1_transaction_id": record["instance_id"],
        "stage1_package_digest": record.get("package_digest"),
        "stage1_source_digest": record.get("source_digest"),
        "stage1_authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest"),
        "stage1_dispatch_receipt_id": (record.get("receipts") or {}).get("dispatch", {}).get("receipt_id"),
        "stage1_provider_selection": (record.get("receipts") or {}).get("provider_selection"),
    }
    state["state_digest"] = _digest(state)
    return state


def _read_projection(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Stage1ExecutionResolutionError(f"invalid runtime projection: {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise Stage1ExecutionResolutionError(f"runtime projection is not an object: {path.name}")
    return value


def _atomic_write_projections(admission_path: Path, admission: Mapping[str, Any], execution_path: Path,
                              execution: Mapping[str, Any]) -> None:
    """Install both projections or leave both stores unchanged."""
    existing_admission = _read_projection(admission_path)
    existing_execution = _read_projection(execution_path)
    if existing_admission is not None and existing_execution is not None:
        for value, expected, label in ((existing_admission, admission["admission_id"], "admission_id"),
                                       (existing_execution, execution["execution_id"], "execution_id")):
            supplied = value.get("state_digest")
            material = dict(value)
            material.pop("state_digest", None)
            if not supplied or supplied != _digest(material) or value.get(label) != expected:
                raise Stage1ExecutionResolutionError(f"existing {label} projection conflicts with Stage 1")
        return
    if existing_admission is not None or existing_execution is not None:
        raise Stage1ExecutionResolutionError("partial Stage 1 runtime hydration would be non-atomic")
    admission_path.parent.mkdir(parents=True, exist_ok=True)
    execution_path.parent.mkdir(parents=True, exist_ok=True)
    temp_paths: list[Path] = []
    installed: list[Path] = []
    try:
        for target, value in ((admission_path, admission), (execution_path, execution)):
            descriptor, raw = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
            temp = Path(raw)
            temp_paths.append(temp)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(value), indent=2, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        for temp, target in zip(temp_paths, (admission_path, execution_path)):
            os.replace(temp, target)
            installed.append(target)
    except OSError as error:
        for path in installed:
            path.unlink(missing_ok=True)
        raise Stage1ExecutionResolutionError(f"atomic Stage 1 runtime hydration failed: {error}") from error
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)


def resolve(root: Path | str, stage1_directory: Path | str, admission_store: Path | str,
            execution_store: Path | str, identifier: str | None = None,
            execution_id: str | None = None, admission_id: str | None = None,
            hydrate: bool = False) -> dict[str, Any]:
    runtime = Stage1Runtime(root, stage1_directory)
    try:
        records = runtime.store.all()
        receipt_backed = [item for item in records
                          if item.get("lifecycle_integrity") == "RECEIPT_BACKED_V1"]
        if not receipt_backed and not identifier:
            raise Stage1ExecutionResolutionError("no receipt-backed Stage 1 transaction exists")
        record = runtime.resolve_transaction(identifier) if identifier else runtime.resolve_transaction(
            next(item["instance_id"] for item in receipt_backed
                 if item.get("state") not in {"REJECTED", "CLOSED"})
        )
    except (Stage1Error, StopIteration) as error:
        raise Stage1ExecutionResolutionError(str(error)) from error
    receipts = record.get("receipts")
    if record.get("lifecycle_integrity") != "RECEIPT_BACKED_V1" or not isinstance(receipts, Mapping):
        raise Stage1ExecutionResolutionError("Stage 1 record is not receipt-backed")
    requested_admission_id = admission_id
    resolved_admission_id = (receipts.get("admission") or {}).get("admission_id")
    if not resolved_admission_id:
        raise Stage1ExecutionResolutionError("Stage 1 admission identity is missing")
    if requested_admission_id and requested_admission_id != resolved_admission_id:
        raise Stage1ExecutionResolutionError("requested admission conflicts with Stage 1 receipt")
    execution = _find_execution(Path(execution_store), resolved_admission_id, execution_id)
    admission = _derived_admission(record, resolved_admission_id)
    resolved_execution_id = execution.get("execution_id") if execution else (receipts.get("execution") or {}).get("execution_id") or record["instance_id"]
    if execution_id and execution_id != resolved_execution_id:
        raise Stage1ExecutionResolutionError("requested execution conflicts with Stage 1 receipt")
    admission["stage1_execution_id"] = resolved_execution_id
    if not execution:
        execution = _derived_execution(admission, record, resolved_execution_id)
    result = {"source": "STAGE1", "transaction": record, "admission_id": resolved_admission_id,
            "admission": admission,
            "execution": execution,
            "execution_id": resolved_execution_id,
            "identities": {"transaction_id": record["instance_id"], "admission_id": resolved_admission_id,
                            "package_digest": record.get("package_digest"),
                            "authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest"),
                            "dispatch_receipt_id": (receipts.get("dispatch") or {}).get("receipt_id"),
                            "execution_id": resolved_execution_id}}
    if hydrate:
        admission_path = Path(admission_store) / f"{resolved_admission_id}.json"
        execution_path = Path(execution_store) / f"{resolved_execution_id}.json"
        already_present = admission_path.exists() and execution_path.exists()
        _atomic_write_projections(admission_path, {**admission, "state_digest": _digest(admission)}, execution_path, execution)
        result["hydrated"] = not already_present
    return result
