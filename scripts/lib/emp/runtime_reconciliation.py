#!/usr/bin/env python3
"""Canonical, receipt-backed reconciliation of Stage 1 runtime projections.

Stage 1 is immutable authority.  Admission, execution, and reconciliation
receipts are derived projections and are installed as one guarded transaction.
This module deliberately does not create authority, alter Stage 1 receipts, or
start execution.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.stage1_execution_resolution import (
    Stage1ExecutionResolutionError,
    _derived_admission,
    _derived_execution,
    _digest,
    _find_execution,
    _canonical_execution_identity,
    _read_projection,
    resolve as resolve_stage1,
)


class RuntimeReconciliationError(Stage1ExecutionResolutionError):
    """The runtime cannot be reconciled to one lawful Stage 1 projection."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _receipt_id(material: Mapping[str, Any]) -> str:
    return "ZEUS-RECONCILIATION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, _canonical(material)))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _valid_projection(value: Mapping[str, Any], identity: str, label: str) -> bool:
    supplied = value.get("state_digest")
    material = dict(value)
    material.pop("state_digest", None)
    return bool(supplied and supplied == _digest(material) and value.get(label) == identity)


@contextmanager
def _lock(root: Path, transaction_id: str):
    directory = root / "reconciliation-locks"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{transaction_id}.lock"
    stream = path.open("a+")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def _write_temp(path: Path, value: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(raw)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(dict(value), stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return temporary


def _atomic_install(values: list[tuple[Path, Mapping[str, Any]]]) -> None:
    """Install all prepared files, restoring the exact pre-state on failure."""
    temporary: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path | None]] = []
    installed: list[Path] = []
    try:
        for target, value in values:
            temporary.append((target, _write_temp(target, value)))
        for target, _ in temporary:
            backup = None
            if target.exists():
                descriptor, raw = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.backup.")
                os.close(descriptor)
                backup = Path(raw)
                os.replace(target, backup)
            backups.append((target, backup))
        for target, temp in temporary:
            os.replace(temp, target)
            installed.append(target)
    except (OSError, ValueError) as error:
        for target in installed:
            target.unlink(missing_ok=True)
        for target, backup in reversed(backups):
            if backup is not None and backup.exists():
                os.replace(backup, target)
        raise RuntimeReconciliationError(f"atomic reconciliation persistence failed: {error}") from error
    finally:
        for _, temp in temporary:
            temp.unlink(missing_ok=True)
        for _, backup in backups:
            if backup is not None:
                backup.unlink(missing_ok=True)


def _discover(runtime_root: Path, transaction_id: str, admission_id: str, execution_id: str) -> dict[str, Any]:
    result: dict[str, Any] = {"admissions": [], "executions": [], "sessions": [], "receipts": []}
    for kind, directory in (("admissions", "mission-admissions"), ("executions", "mission-executions"), ("sessions", "native-sessions")):
        path = runtime_root / directory
        for candidate in sorted(path.glob("*.json")) if path.exists() else []:
            try:
                value = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RuntimeReconciliationError(f"CORRUPTED_RECORD: {candidate.name}: {error}") from error
            if not isinstance(value, dict):
                raise RuntimeReconciliationError(f"CORRUPTED_RECORD: {candidate.name} is not an object")
            if (value.get("stage1_transaction_id") == transaction_id
                    or value.get("stage1_identity") == transaction_id
                    or value.get("admission_id") == admission_id
                    or value.get("execution_id") == execution_id
                    or value.get("execution_id") and value.get("execution_id") == transaction_id):
                result[kind].append({"path": str(candidate), "identity": value.get("admission_id") or value.get("execution_id") or value.get("session_id"), "value": value})
    return result


def reconcile(root: Path | str, stage1_directory: Path | str, admission_store: Path | str,
              execution_store: Path | str, *, command: str, identifier: str | None = None,
              execution_id: str | None = None, admission_id: str | None = None,
              require_lineage_environment: bool = False) -> dict[str, Any]:
    """Resolve, plan, atomically install, and report one runtime projection."""
    root = Path(root).resolve()
    runtime_root = Path(admission_store).resolve().parent
    with _lock(runtime_root, identifier or execution_id or "stage1-resolution"):
        try:
            base = resolve_stage1(root, stage1_directory, admission_store, execution_store,
                                  identifier=identifier, execution_id=execution_id,
                                  admission_id=None, hydrate=False,
                                  require_lineage_environment=False,
                                  resolve_admission_lineage=False)
        except Stage1ExecutionResolutionError as error:
            raise RuntimeReconciliationError(f"UNVERIFIABLE_RECORD: {error}") from error
        transaction = base["transaction"]
        transaction_id = transaction["instance_id"]
        canonical_execution_id, identity_operands = _canonical_execution_identity(transaction)
        if execution_id and execution_id != canonical_execution_id:
            raise RuntimeReconciliationError(
                "UNVERIFIABLE_RECORD: requested execution conflicts with Stage 1 receipt: "
                f"requested={execution_id} canonical_stage1_instance_id={canonical_execution_id} "
                f"operands={json.dumps(identity_operands, sort_keys=True)}")
        receipt_admission = (transaction.get("receipts") or {}).get("admission", {}).get("admission_id")
        requested = admission_id or receipt_admission
        if not requested:
            raise RuntimeReconciliationError("authoritative Stage 1 admission identity is absent")

        # Existing supersession is resolved by the established admission-chain
        # resolver.  New first-generation projections are derived directly from
        # the immutable Stage 1 receipt and never fabricated as new admissions.
        existing_admission = _read_projection(Path(admission_store) / f"{requested}.json")
        lineage = existing_admission and (existing_admission.get("superseded_by") or existing_admission.get("supersedes"))
        if lineage or admission_id:
            from scripts.lib.emp.admission_supersession import resolve_for_start, resolve_for_resume
            published = None
            if require_lineage_environment:
                import subprocess
                published = subprocess.run(["git", "-C", str(root), "rev-parse", "origin/main"], capture_output=True, text=True, check=True).stdout.strip()
            resolved_lineage = resolve_for_start(root, admission_store, execution_store, requested,
                                                 stage1_transaction=transaction,
                                                 published_baseline=published)
            chain = resolve_for_resume(root, admission_store, resolved_lineage["admission_id"],
                                       stage1_transaction=transaction,
                                       enforce_environment=require_lineage_environment)
            admission = deepcopy(chain["admission"])
            resolved_admission = chain["admission_id"]
            chain_ids = [item["admission_id"] for item in chain["lineage"]]
        else:
            resolved_admission = receipt_admission
            admission = _derived_admission(transaction, resolved_admission)
            chain_ids = [resolved_admission]
        execution = _find_execution(Path(execution_store), resolved_admission, None,
                                    transaction.get("source_digest"),
                                    (transaction.get("receipts") or {}).get("authorization", {}).get("authority_snapshot_digest"))
        resolved_execution = canonical_execution_id
        stale_execution = execution is not None and execution.get("execution_id") != resolved_execution
        if stale_execution:
            if execution.get("stage1_transaction_id") != transaction_id:
                raise RuntimeReconciliationError(
                    "DIVERGENT_EXECUTION_TRANSACTION_IDENTITY: derived projection belongs to another Stage 1 transaction")
            execution = None
        if execution is None:
            execution = _derived_execution(admission, transaction, resolved_execution)
        admission["stage1_execution_id"] = resolved_execution
        admission_material = dict(admission)
        admission_material.pop("state_digest", None)
        admission_value = {**admission_material, "state_digest": _digest(admission_material)}
        execution_value = dict(execution)
        execution_material = dict(execution_value)
        execution_material.pop("state_digest", None)
        execution_value = {**execution_material, "state_digest": _digest(execution_material)}
        admission_path = Path(admission_store) / f"{resolved_admission}.json"
        execution_path = Path(execution_store) / f"{resolved_execution}.json"
        discovered = _discover(runtime_root, transaction_id, resolved_admission, resolved_execution)
        old_admission = _read_projection(admission_path)
        old_execution = _read_projection(execution_path)
        if old_admission is not None and not _valid_projection(old_admission, resolved_admission, "admission_id"):
            raise RuntimeReconciliationError("CORRUPTED_RECORD: canonical admission projection is invalid")
        if old_execution is not None and not _valid_projection(old_execution, resolved_execution, "execution_id"):
            if (old_execution.get("execution_id") != resolved_execution
                    and old_execution.get("stage1_transaction_id") == transaction_id
                    and old_execution.get("state_digest") == _digest({k: v for k, v in old_execution.items() if k != "state_digest"})):
                stale_execution = True
            else:
                raise RuntimeReconciliationError("CORRUPTED_RECORD: canonical execution projection is invalid")
        immutable_fields = {
            "stage1_identity": transaction_id,
            "stage1_transaction_id": transaction_id,
            "stage1_package_digest": transaction.get("package_digest"),
            "stage1_source_digest": transaction.get("source_digest"),
            "stage1_authority_snapshot_digest": (transaction.get("receipts") or {}).get("authorization", {}).get("authority_snapshot_digest"),
        }
        for existing, label in ((old_admission, "admission"), (old_execution, "execution")):
            if existing is None:
                continue
            for field, expected in immutable_fields.items():
                if field in existing and expected is not None and existing[field] != expected:
                    raise RuntimeReconciliationError(f"DIVERGENT_{label.upper()}_IDENTITY: {field} differs from Stage 1")
        classifications = []
        if old_admission is None: classifications.append("MISSING_PROJECTION")
        if old_execution is None: classifications.append("MISSING_PROJECTION")
        admission_required = ("stage1_transaction_id", "stage1_source_digest", "stage1_provider_selection")
        execution_required = ("stage1_transaction_id", "stage1_source_digest", "stage1_provider_selection")
        admission_partial = old_admission is not None and any(field not in old_admission for field in admission_required)
        execution_partial = old_execution is not None and any(field not in old_execution for field in execution_required)
        if admission_partial or execution_partial: classifications.append("PARTIAL_PROJECTION")
        if stale_execution: classifications.append("STALE_EXECUTION_PROJECTION")
        if old_admission is not None and old_execution is not None and not admission_partial and not execution_partial:
            classifications.append("ALREADY_CANONICAL")
        pre_state = _digest({"admission": old_admission, "execution": old_execution})
        post_state = _digest({"admission": admission_value, "execution": execution_value})
        receipt_material = {"transaction_id": transaction_id, "command": command,
                            "admission_id": resolved_admission, "execution_id": resolved_execution,
                            "post_state_digest": post_state}
        reconciliation_id = _receipt_id(receipt_material)
        receipt_path = runtime_root / "evidence" / "reconciliation-receipts" / f"{reconciliation_id}.json"
        receipt = {"schema_version": 1, "reconciliation_id": reconciliation_id,
                   "transaction_id": transaction_id, "requested_command": command,
                   "repository_identity": str(root), "runtime_identity": str(runtime_root),
                   "discovered_representations": discovered, "conflict_classifications": sorted(set(classifications)),
                   "authority_precedence": ["stage1_instance_id", "dispatch_receipt", "provider_selection_transaction", "execution_projection", "native_session", "operator_argument"],
                   "selected_authoritative_records": {"stage1_transaction": transaction_id, "admission_id": resolved_admission, "execution_id": resolved_execution},
                   "records_created": [str(p) for p, old in ((admission_path, old_admission), (execution_path, old_execution)) if old is None],
                   "records_repaired": ([str(execution_path)] if stale_execution else []), "records_superseded": [], "records_rebound": [],
                   "records_preserved": [transaction_id, resolved_admission, resolved_execution], "records_rejected": [],
                   "pre_state_digest": pre_state, "post_state_digest": post_state, "rollback_result": "NOT_REQUIRED",
                   "final_admission_id": resolved_admission, "final_execution_id": resolved_execution,
                   "final_session_id": execution_value.get("session_id"), "final_lifecycle_state": execution_value.get("state"),
                   "next_authorized_action": "Continue the existing receipt-backed execution without resubmission.",
                   "timestamp": _now(),
                   "execution_identity_operands": identity_operands}
        receipt["receipt_digest"] = _digest(receipt)
        if (not receipt_path.exists() or old_admission is None or old_execution is None
                or admission_partial or execution_partial or stale_execution):
            _atomic_install([(admission_path, admission_value), (execution_path, execution_value), (receipt_path, receipt)])
        result = {**base, "source": "STAGE1_RECONCILIATION", "admission_id": resolved_admission,
                "admission": admission_value, "execution": execution_value, "execution_id": resolved_execution,
                "hydrated": bool(old_admission is None or old_execution is None or admission_partial or execution_partial),
                "reconciliation": {"reconciliation_id": reconciliation_id, "classification": sorted(set(classifications)),
                                    "replayed": old_admission is not None and old_execution is not None and not admission_partial and not execution_partial,
                                    "admission_chain": chain_ids, "receipt_path": str(receipt_path)},
                "identities": {**base["identities"], "admission_id": resolved_admission, "execution_id": resolved_execution,
                               "execution_identity_operands": identity_operands}}
        result["admission_lineage"] = {"requested_admission_id": requested,
                                        "receipt_admission_id": receipt_admission,
                                        "resolved_admission_id": resolved_admission,
                                        "lineage": chain_ids,
                                        "replayed": bool(old_admission is not None and old_execution is not None and not admission_partial and not execution_partial)}
        return result
