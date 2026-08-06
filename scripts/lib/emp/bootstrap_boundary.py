"""Canonical P4-G1 bootstrap boundary.

Consumes one verified P3-G1 admission transaction and provisions bootstrap
evidence only.  Provider selection, dispatch, and execution are deliberately
outside this boundary.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import (
    _canonical,
    _digest,
    _load,
    _write_immutable,
)
from scripts.lib.emp.repository_identity import resolve


class BootstrapBoundaryError(ValueError):
    """Bootstrap cannot safely consume the supplied admission evidence."""


ADMISSION_CLASSES = {
    "packages": ("package", "immutable-execution-package"),
    "mission-contracts": ("mission_contract", "mission-contract"),
    "execution-authority": ("execution_authority", "execution-authority"),
    "receipts": ("admission_receipt", "admission"),
    "journals": ("admission_journal", "admission"),
}

BOOTSTRAP_CLASSES = {
    "bootstraps": "bootstrap_transaction",
    "execution-records": "execution_record",
    "bootstrap-receipts": "bootstrap_receipt",
    "bootstrap-journals": "bootstrap_journal",
    "provider-readiness": "provider_readiness",
}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, check=False)
    if result.returncode:
        raise BootstrapBoundaryError(f"repository verification failed: {' '.join(args)}")
    return result.stdout.strip()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _descriptor_path(descriptor: Any, runtime: Path, directory: str) -> Path:
    if not isinstance(descriptor, Mapping):
        raise BootstrapBoundaryError(f"missing {directory} descriptor")
    raw = descriptor.get("path")
    if not isinstance(raw, str) or not raw:
        raise BootstrapBoundaryError(f"missing {directory} path")
    path = Path(raw).resolve()
    if not _inside(path, runtime) or path.parent.name != directory:
        raise BootstrapBoundaryError(f"{directory} path is outside canonical runtime")
    if not path.is_file():
        raise BootstrapBoundaryError(f"missing {directory} artifact")
    return path


def _artifact(path: Path, expected: str, directory: str) -> dict[str, Any]:
    value = _load(path)
    supplied = value.get("artifact_digest")
    if not isinstance(supplied, str) or supplied != expected:
        raise BootstrapBoundaryError(f"{directory} digest mismatch")
    if supplied != _digest({key: item for key, item in value.items()
                            if key != "artifact_digest"}):
        raise BootstrapBoundaryError(f"{directory} canonical digest mismatch")
    return value


def _verify_admission(path: Path, runtime: Path, repository: Path) -> dict[str, Any]:
    value = _load(path)
    if path.parent.name == "receipts":
        admission_id = value.get("admission_id")
        if not isinstance(admission_id, str):
            raise BootstrapBoundaryError("admission receipt lacks admission_id")
        transaction_path = runtime / "admissions" / f"{admission_id}.json"
        value = _load(transaction_path)
    transaction_digest = value.get("transaction_digest")
    unsigned = {key: item for key, item in value.items() if key != "transaction_digest"}
    if (value.get("transaction_type") != "mission-admission" or
            value.get("admission_state") != "ADMISSION_COMPLETE" or
            value.get("admission_result") != "PASS" or
            value.get("bootstrap_eligible") is not True or
            not isinstance(transaction_digest, str) or
            transaction_digest != _digest(unsigned)):
        raise BootstrapBoundaryError("admission transaction is not valid for bootstrap")
    identity = resolve(repository)
    if value.get("operation") != "BETA" or value.get("repository_baseline") != _git(repository, "rev-parse", "HEAD"):
        raise BootstrapBoundaryError("admission Operation or repository baseline is invalid")
    if _git(repository, "rev-parse", "HEAD") != _git(repository, "rev-parse", "origin/main"):
        raise BootstrapBoundaryError("repository is not at published origin/main")
    artifacts: dict[str, dict[str, Any]] = {}
    for directory, (field, artifact_class) in ADMISSION_CLASSES.items():
        descriptor = value.get(field)
        path = _descriptor_path(descriptor, runtime, directory)
        expected = descriptor.get("digest") if isinstance(descriptor, Mapping) else None
        if not isinstance(expected, str):
            raise BootstrapBoundaryError(f"{field} digest is missing")
        artifact = _artifact(path, expected, directory)
        actual_class = artifact.get("artifact_type", artifact.get("receipt_type", artifact.get("journal_type")))
        if actual_class != artifact_class:
            raise BootstrapBoundaryError(f"{field} artifact type is invalid")
        artifacts[field] = artifact
    package = artifacts["package"]
    if package.get("repository", {}).get("canonical_repository_identity") != identity["canonical_repository_identity"]:
        raise BootstrapBoundaryError("canonical repository identity mismatch")
    for key in ("admission_id", "mission_id", "wop_id"):
        values = [value.get(key)] + [item.get(key) for item in artifacts.values()]
        if any(item != values[0] for item in values):
            raise BootstrapBoundaryError(f"admission artifact identity mismatch: {key}")
    if artifacts["admission_receipt"].get("submission_id") != value.get("submission_id"):
        raise BootstrapBoundaryError("submission identity mismatch")
    if artifacts["admission_journal"].get("provisioned") != [
        value[field]["digest"] for field in ("package", "mission_contract", "execution_authority", "admission_receipt")
    ]:
        raise BootstrapBoundaryError("admission journal provenance is invalid")
    counts = {directory: len(list((runtime / directory).glob("*.json"))) for directory in ADMISSION_CLASSES}
    if any(count != 1 for count in counts.values()):
        raise BootstrapBoundaryError(f"admission artifact cardinality is invalid: {counts}")
    return {"transaction": value, "artifacts": artifacts}


def _transaction_digest(value: Mapping[str, Any]) -> str:
    # The execution record binds this digest, so its descriptor digest is
    # excluded from the transaction's digest material to avoid a circular hash.
    material = dict(value)
    material.pop("transaction_digest", None)
    for field in BOOTSTRAP_CLASSES.values():
        descriptor = material.get(field)
        if isinstance(descriptor, Mapping):
            material[field] = {key: item for key, item in descriptor.items() if key != "digest"}
    return _digest(material)


def _validate_bootstrap_artifacts(runtime: Path, bootstrap_id: str, response: Mapping[str, Any]) -> None:
    for directory, field in BOOTSTRAP_CLASSES.items():
        descriptor = response.get(field)
        path = _descriptor_path(descriptor, runtime, directory)
        if path.name != f"{bootstrap_id}.json":
            raise BootstrapBoundaryError(f"{field} identity filename mismatch")
        if directory == "bootstraps":
            value = _load(path)
            if not isinstance(descriptor, Mapping) or descriptor.get("digest") != value.get("transaction_digest"):
                raise BootstrapBoundaryError("bootstrap transaction digest descriptor mismatch")
            if value.get("transaction_digest") != _transaction_digest(value):
                raise BootstrapBoundaryError("bootstrap transaction digest mismatch")
        else:
            if not isinstance(descriptor, Mapping) or descriptor.get("digest") != _load(path).get("artifact_digest"):
                raise BootstrapBoundaryError(f"{field} digest descriptor mismatch")
            _artifact(path, descriptor["digest"], directory)
    counts = {directory: len(list((runtime / directory).glob("*.json"))) for directory in BOOTSTRAP_CLASSES}
    if any(count != 1 for count in counts.values()):
        raise BootstrapBoundaryError(f"bootstrap artifact cardinality is invalid: {counts}")


def bootstrap(admission: Path | str, *, repository: Path | str, runtime_root: Path | str,
              at: str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    runtime = Path(runtime_root).resolve()
    admission_facts = _verify_admission(Path(admission).resolve(), runtime, root)
    admission_tx = admission_facts["transaction"]
    admission_id = admission_tx["admission_id"]
    identity = {"admission_id": admission_id, "transaction_digest": admission_tx["transaction_digest"],
                "mission_id": admission_tx["mission_id"], "wop_id": admission_tx["wop_id"],
                "repository_baseline": admission_tx["repository_baseline"]}
    bootstrap_id = "BOOTSTRAP-" + str(uuid.uuid5(uuid.NAMESPACE_URL, _canonical(identity)))
    transaction_path = runtime / "bootstraps" / f"{bootstrap_id}.json"
    if transaction_path.exists():
        existing = _load(transaction_path)
        if existing.get("transaction_digest") != _transaction_digest(existing):
            raise BootstrapBoundaryError("bootstrap transaction digest mismatch")
        _validate_bootstrap_artifacts(runtime, bootstrap_id, existing)
        existing["duplicate_bootstrap"] = "IDEMPOTENT"
        return existing
    baseline = _git(root, "rev-parse", "HEAD")
    common = {"schema_version": 1, "bootstrap_id": bootstrap_id, "admission_id": admission_id,
              "submission_id": admission_tx["submission_id"], "mission_id": admission_tx["mission_id"],
              "wop_id": admission_tx["wop_id"], "operation": "BETA", "repository_baseline": baseline,
              "provider_selected": False, "dispatch_created": False, "execution_started": False}
    package = admission_facts["artifacts"]["package"]
    bindings = {"execution_package_digest": admission_tx["package"]["digest"],
                "mission_contract_digest": admission_tx["mission_contract"]["digest"],
                "execution_authority_digest": admission_tx["execution_authority"]["digest"]}
    record = dict(common, artifact_type="canonical-execution-record", lifecycle_state="READY_FOR_EXECUTION_PROVIDER",
                  provider_ready=True, admission_transaction_digest=admission_tx["transaction_digest"], bindings=bindings,
                  repository=package["repository"])
    # Establish the deterministic transaction identity before the record digest.
    transaction = dict(common, transaction_type="bootstrap", bootstrap_state="READY_FOR_EXECUTION_PROVIDER",
                       bootstrap_result="PASS", provider_ready=True, next_action="EVALUATE_EXECUTION_PROVIDER",
                       admission_transaction_digest=admission_tx["transaction_digest"],
                       bootstrap_transaction={"path": str(transaction_path.resolve())},
                       execution_record={"path": str((runtime / "execution-records" / f"{bootstrap_id}.json").resolve())},
                       bootstrap_receipt={"path": str((runtime / "bootstrap-receipts" / f"{bootstrap_id}.json").resolve())},
                       bootstrap_journal={"path": str((runtime / "bootstrap-journals" / f"{bootstrap_id}.json").resolve())},
                       provider_readiness={"path": str((runtime / "provider-readiness" / f"{bootstrap_id}.json").resolve())})
    transaction["transaction_digest"] = _transaction_digest(transaction)
    record["bootstrap_transaction_digest"] = transaction["transaction_digest"]
    record["artifact_digest"] = _digest(record)
    _write_immutable(runtime / "execution-records" / f"{bootstrap_id}.json", record)
    receipt = dict(common, artifact_type="bootstrap-receipt", receipt_type="bootstrap",
                   bootstrap_state="READY_FOR_EXECUTION_PROVIDER", bootstrap_result="PASS",
                   provider_ready=True, bootstrap_transaction_digest=transaction["transaction_digest"],
                   execution_record_digest=record["artifact_digest"])
    receipt["artifact_digest"] = _digest(receipt)
    _write_immutable(runtime / "bootstrap-receipts" / f"{bootstrap_id}.json", receipt)
    journal = dict(common, artifact_type="bootstrap-journal", journal_type="bootstrap",
                   states=["BOOTSTRAP_EVALUATING", "BOOTSTRAP_QUALIFIED", "EXECUTION_RECORD_PROVISIONED", "READY_FOR_EXECUTION_PROVIDER"],
                   provisioned=[record["artifact_digest"], receipt["artifact_digest"]],
                   bootstrap_transaction_digest=transaction["transaction_digest"])
    journal["artifact_digest"] = _digest(journal)
    _write_immutable(runtime / "bootstrap-journals" / f"{bootstrap_id}.json", journal)
    readiness = dict(common, artifact_type="provider-readiness", readiness_state="READY_FOR_EXECUTION_PROVIDER",
                     provider_ready=True, provider_selected=False, bootstrap_transaction_digest=transaction["transaction_digest"],
                     execution_record_digest=record["artifact_digest"])
    readiness["artifact_digest"] = _digest(readiness)
    _write_immutable(runtime / "provider-readiness" / f"{bootstrap_id}.json", readiness)
    transaction["execution_record"]["digest"] = record["artifact_digest"]
    transaction["bootstrap_transaction"]["digest"] = transaction["transaction_digest"]
    transaction["bootstrap_receipt"]["digest"] = receipt["artifact_digest"]
    transaction["bootstrap_journal"]["digest"] = journal["artifact_digest"]
    transaction["provider_readiness"]["digest"] = readiness["artifact_digest"]
    _write_immutable(transaction_path, transaction)
    return transaction
