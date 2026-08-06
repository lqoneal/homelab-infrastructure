"""Canonical P3-G1 Mission Admission boundary.

Consumes one immutable P2 submission receipt and its authored WOP, then
provisions the admission package only.  This boundary never bootstraps,
dispatches, or creates an execution record.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve, resolve_declared
from scripts.lib.emp.wop_verification import verify_artifact


class MissionAdmissionBoundaryError(ValueError):
    """Admission cannot safely provision its complete immutable package."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_text(encoding="utf-8") != serialized:
            raise MissionAdmissionBoundaryError(
                f"immutable artifact identity collision: {path.name}"
            )


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MissionAdmissionBoundaryError(f"artifact is unreadable: {path}: {error}") from error
    if not isinstance(value, dict):
        raise MissionAdmissionBoundaryError(f"artifact must be an object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise MissionAdmissionBoundaryError(f"git verification failed: {' '.join(args)}")
    return result.stdout.strip()


def _submission_facts(receipt_path: Path, wop_path: Path, repository: Path) -> dict[str, Any]:
    receipt = _load(receipt_path)
    if receipt.get("receipt_type") != "submission":
        raise MissionAdmissionBoundaryError("invalid submission receipt type")
    supplied = receipt.get("receipt_digest")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if not isinstance(supplied, str) or supplied != _digest(unsigned):
        raise MissionAdmissionBoundaryError("submission receipt digest mismatch")
    required = ("submission_id", "submission_state", "submission_result", "admission_request_id",
                "mission_id", "wop_id", "operation", "repository_identity", "wop_output_digest",
                "immutable_provenance")
    if any(not receipt.get(key) for key in required):
        raise MissionAdmissionBoundaryError("submission receipt is incomplete")
    if receipt["submission_state"] != "ADMISSION_REQUESTED" or receipt["submission_result"] != "PASS":
        raise MissionAdmissionBoundaryError("submission is not ADMISSION_REQUESTED/PASS")
    if receipt["operation"] != "BETA":
        raise MissionAdmissionBoundaryError("Operation Beta is required")
    try:
        declared = resolve_declared(receipt["repository_identity"].get("canonical_repository_identity"), repository)
    except (AttributeError, TypeError, ValueError) as error:
        raise MissionAdmissionBoundaryError(f"repository identity mismatch: {error}") from error
    if declared["canonical_repository_identity"] != resolve(repository)["canonical_repository_identity"]:
        raise MissionAdmissionBoundaryError("repository identity mismatch")
    if not wop_path.is_file() or _sha(wop_path) != receipt["wop_output_digest"]:
        raise MissionAdmissionBoundaryError("authored WOP digest does not match submission")
    verified = verify_artifact(wop_path)
    if verified.get("result") != "PASS":
        raise MissionAdmissionBoundaryError("authored WOP verification failed")
    trace = verified.get("traceability") or verified.get("trace")
    if not isinstance(trace, Mapping):
        raise MissionAdmissionBoundaryError("authored WOP traceability is missing")
    if trace.get("operation") != "BETA" or trace.get("mission_id") != receipt["mission_id"] or trace.get("wop_id") != receipt["wop_id"]:
        raise MissionAdmissionBoundaryError("submission and authored WOP identities disagree")
    provenance = receipt["immutable_provenance"]
    if not isinstance(provenance, Mapping) or not provenance.get("traceability_digest"):
        raise MissionAdmissionBoundaryError("immutable provenance is missing")
    if _digest({key: value for key, value in trace.items() if key not in {"output_digest"}}) != provenance["traceability_digest"]:
        # P2 uses canonical replay content; accept the canonical verifier's
        # normalized digest when available, but never an unbound receipt.
        from scripts.lib.emp.wop_verification import canonical_replay_content
        if _digest(canonical_replay_content(trace)) != provenance["traceability_digest"]:
            raise MissionAdmissionBoundaryError("immutable provenance digest mismatch")
    request_path = receipt_path.parent.parent / "requests" / f"{receipt['admission_request_id']}.json"
    request = _load(request_path)
    if request.get("submission_id") != receipt["submission_id"] or request.get("mission_admission_executed") is not False:
        raise MissionAdmissionBoundaryError("admission request projection is invalid")
    return {"receipt": receipt, "receipt_path": str(receipt_path.resolve()), "wop_path": str(wop_path.resolve()),
            "trace": dict(trace), "repository": declared, "request": request}


def _artifact(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(value)
    data["artifact_digest"] = _digest(data)
    _write_immutable(path, data)
    return data


def admit(submission: Path | str, *, wop: Path | str, repository: Path | str,
          runtime_root: Path | str, at: str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    receipt_path = Path(submission).resolve()
    wop_path = Path(wop).resolve()
    facts = _submission_facts(receipt_path, wop_path, root)
    receipt = facts["receipt"]
    identity = {"submission_id": receipt["submission_id"], "mission_id": receipt["mission_id"],
                "wop_id": receipt["wop_id"], "submission_digest": receipt["submission_digest"],
                "repository": facts["repository"]["canonical_repository_identity"]}
    admission_id = "ADMISSION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, _canonical(identity)))
    runtime = Path(runtime_root).resolve()
    transaction_path = runtime / "admissions" / f"{admission_id}.json"
    if transaction_path.exists():
        existing = _load(transaction_path)
        if existing.get("transaction_digest") != _digest({k: v for k, v in existing.items() if k != "transaction_digest"}):
            raise MissionAdmissionBoundaryError("admission transaction digest mismatch")
        existing["duplicate_admission"] = "IDEMPOTENT"
        return existing
    baseline = _git(root, "rev-parse", "HEAD")
    package_digest = _digest({"wop_digest": receipt["wop_output_digest"], "provenance": receipt["immutable_provenance"], "repository_baseline": baseline})
    package = _artifact(runtime / "packages" / f"{admission_id}.json", {
        "schema_version": 1, "artifact_type": "immutable-execution-package", "admission_id": admission_id,
        "mission_id": receipt["mission_id"], "wop_id": receipt["wop_id"], "operation": "BETA",
        "repository": facts["repository"], "repository_baseline": baseline,
        "wop_output_digest": receipt["wop_output_digest"], "immutable_provenance": receipt["immutable_provenance"],
        "execution_created": False,
    })
    contract = _artifact(runtime / "mission-contracts" / f"{admission_id}.json", {
        "schema_version": 1, "artifact_type": "mission-contract", "mission_contract_id": "MISSION-CONTRACT-" + admission_id.removeprefix("ADMISSION-"),
        "admission_id": admission_id, "mission_id": receipt["mission_id"], "wop_id": receipt["wop_id"],
        "operation": "BETA", "lifecycle": "PROVISIONED", "execution_permitted": False,
    })
    authority = _artifact(runtime / "execution-authority" / f"{admission_id}.json", {
        "schema_version": 1, "artifact_type": "execution-authority", "authority_id": "EXECUTION-AUTHORITY-" + admission_id.removeprefix("ADMISSION-"),
        "admission_id": admission_id, "mission_id": receipt["mission_id"], "wop_id": receipt["wop_id"],
        "operation": "BETA", "state": "PROVISIONED", "bootstrap_eligible": True,
        "execution_permitted": False,
    })
    common = {"schema_version": 1, "admission_id": admission_id, "submission_id": receipt["submission_id"],
              "mission_id": receipt["mission_id"], "wop_id": receipt["wop_id"], "package_digest": package["artifact_digest"],
              "mission_contract_digest": contract["artifact_digest"], "execution_authority_digest": authority["artifact_digest"],
              "repository_baseline": baseline, "operation": "BETA"}
    admission_receipt = _artifact(runtime / "receipts" / f"{admission_id}.json", {
        **common, "receipt_type": "admission", "admission_state": "ADMISSION_COMPLETE", "admission_result": "PASS",
        "bootstrap_eligible": True, "execution_created": False, "bootstrap_performed": False,
    })
    journal = _artifact(runtime / "journals" / f"{admission_id}.json", {
        **common, "journal_type": "admission", "states": ["ADMISSION_REQUESTED", "ADMISSION_EVALUATING", "PACKAGE_PROVISIONED", "MISSION_CONTRACT_PROVISIONED", "EXECUTION_AUTHORITY_PROVISIONED", "ADMISSION_COMPLETE"],
        "provisioned": [package["artifact_digest"], contract["artifact_digest"], authority["artifact_digest"], admission_receipt["artifact_digest"]],
        "execution_created": False,
    })
    transaction = {"schema_version": 1, "transaction_type": "mission-admission", **common,
                   "admission_state": "ADMISSION_COMPLETE", "admission_result": "PASS", "duplicate_admission": "NEW",
                   "package": {"path": str((runtime / "packages" / f"{admission_id}.json").resolve()), "digest": package["artifact_digest"]},
                   "mission_contract": {"path": str((runtime / "mission-contracts" / f"{admission_id}.json").resolve()), "digest": contract["artifact_digest"]},
                   "execution_authority": {"path": str((runtime / "execution-authority" / f"{admission_id}.json").resolve()), "digest": authority["artifact_digest"]},
                   "admission_receipt": {"path": str((runtime / "receipts" / f"{admission_id}.json").resolve()), "digest": admission_receipt["artifact_digest"]},
                   "admission_journal": {"path": str((runtime / "journals" / f"{admission_id}.json").resolve()), "digest": journal["artifact_digest"]},
                   "bootstrap_eligible": True, "execution_created": False, "bootstrap_performed": False,
                   "next_action": "EVALUATE_BOOTSTRAP_ELIGIBILITY", "provenance": receipt["immutable_provenance"]}
    transaction["transaction_digest"] = _digest(transaction)
    _write_immutable(transaction_path, transaction)
    return transaction
