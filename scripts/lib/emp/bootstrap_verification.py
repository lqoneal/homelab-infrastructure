"""Read-only P4-G1 bootstrap replay verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.bootstrap_boundary import (
    BOOTSTRAP_CLASSES,
    _artifact,
    _descriptor_path,
    _verify_admission,
    _load,
    _transaction_digest,
)
from scripts.lib.emp.repository_identity import resolve


class BootstrapVerificationError(ValueError):
    """Bootstrap evidence is incomplete, altered, or out of scope."""


def verify_bootstrap_replay(first: Mapping[str, Any], replay: Mapping[str, Any], *,
                            runtime_root: Path | str, repository: Path | str) -> dict[str, Any]:
    required = ("bootstrap_id", "transaction_type", "transaction_digest", "bootstrap_state",
                "bootstrap_result", "execution_record", "bootstrap_receipt",
                "bootstrap_journal", "provider_readiness")
    if any(key not in first for key in required):
        raise BootstrapVerificationError("bootstrap response is incomplete")
    if first.get("transaction_type") != "bootstrap":
        raise BootstrapVerificationError("bootstrap transaction type is invalid")
    if first.get("bootstrap_state") != "READY_FOR_EXECUTION_PROVIDER" or first.get("bootstrap_result") != "PASS":
        raise BootstrapVerificationError("bootstrap did not reach provider readiness")
    if first.get("provider_ready") is not True or any(first.get(key) is not False for key in
                                                     ("provider_selected", "dispatch_created", "execution_started")):
        raise BootstrapVerificationError("provider or execution boundary is invalid")
    if first.get("next_action") != "EVALUATE_EXECUTION_PROVIDER":
        raise BootstrapVerificationError("bootstrap next action is invalid")
    if first.get("transaction_digest") != _transaction_digest(first):
        raise BootstrapVerificationError("bootstrap transaction digest mismatch")
    if replay.get("duplicate_bootstrap") != "IDEMPOTENT":
        raise BootstrapVerificationError("bootstrap replay is not IDEMPOTENT")
    stable = ("bootstrap_id", "transaction_type", "transaction_digest", "admission_id", "submission_id",
              "mission_id", "wop_id", "repository_baseline", "admission_transaction_digest")
    for key in stable:
        if first.get(key) != replay.get(key):
            raise BootstrapVerificationError(f"bootstrap replay changed {key}")
    for field in BOOTSTRAP_CLASSES.values():
        if first.get(field) != replay.get(field):
            raise BootstrapVerificationError(f"bootstrap replay changed {field}")
    runtime = Path(runtime_root).resolve()
    admission = _verify_admission(runtime / "admissions" / f"{first['admission_id']}.json", runtime, Path(repository).resolve())
    if admission["transaction"].get("transaction_digest") != first.get("admission_transaction_digest"):
        raise BootstrapVerificationError("bootstrap and admission transaction identities disagree")
    values = {}
    for directory, field in BOOTSTRAP_CLASSES.items():
        descriptor = first[field]
        path = _descriptor_path(descriptor, runtime, directory)
        if directory == "bootstraps":
            transaction = _load(path)
            if descriptor.get("digest") != transaction.get("transaction_digest") or transaction.get("transaction_digest") != _transaction_digest(transaction):
                raise BootstrapVerificationError("bootstrap transaction digest mismatch")
            values[field] = transaction
        else:
            values[field] = _artifact(path, descriptor.get("digest"), directory)
        if path.name != f"{first['bootstrap_id']}.json":
            raise BootstrapVerificationError(f"{field} filename identity mismatch")
    counts = {directory: len(list((runtime / directory).glob("*.json"))) for directory in BOOTSTRAP_CLASSES}
    if any(count != 1 for count in counts.values()):
        raise BootstrapVerificationError(f"bootstrap artifact cardinality is invalid: {counts}")
    record = values["execution_record"]
    if record.get("artifact_type") != "canonical-execution-record" or record.get("provider_ready") is not True:
        raise BootstrapVerificationError("execution record is invalid")
    if record.get("provider_selected") or record.get("dispatch_created") or record.get("execution_started"):
        raise BootstrapVerificationError("execution record crosses provider boundary")
    if values["bootstrap_receipt"].get("receipt_type") != "bootstrap":
        raise BootstrapVerificationError("bootstrap receipt is invalid")
    if values["bootstrap_journal"].get("journal_type") != "bootstrap":
        raise BootstrapVerificationError("bootstrap journal is invalid")
    if values["provider_readiness"].get("artifact_type") != "provider-readiness":
        raise BootstrapVerificationError("provider-readiness projection is invalid")
    for field in ("admission_id", "submission_id", "mission_id", "wop_id", "bootstrap_id"):
        if any(value.get(field) != first.get(field) for value in values.values()):
            raise BootstrapVerificationError(f"bootstrap artifact identity mismatch: {field}")
    if record.get("operation") != "BETA" or any(value.get("operation") != "BETA" for value in values.values()):
        raise BootstrapVerificationError("Operation Beta evidence is missing")
    if record.get("repository", {}).get("canonical_repository_identity") != resolve(repository)["canonical_repository_identity"]:
        raise BootstrapVerificationError("canonical repository identity mismatch")
    if record.get("repository_baseline") != first.get("repository_baseline"):
        raise BootstrapVerificationError("repository baseline mismatch")
    if record.get("bootstrap_transaction_digest") != first.get("transaction_digest"):
        raise BootstrapVerificationError("execution record transaction binding is invalid")
    expected_bindings = {
        "execution_package_digest": admission["transaction"]["package"]["digest"],
        "mission_contract_digest": admission["transaction"]["mission_contract"]["digest"],
        "execution_authority_digest": admission["transaction"]["execution_authority"]["digest"],
    }
    if record.get("bindings") != expected_bindings:
        raise BootstrapVerificationError("execution record admission artifact bindings are invalid")
    # mission-executions is a pre-existing legacy lifecycle store.  It is
    # deliberately excluded from canonical P4 downstream-effect checks; the
    # canonical P4 execution boundary is represented by execution-records,
    # while provider/session/dispatch/execution stores remain prohibited.
    prohibited = {"providers", "provider-sessions", "dispatch", "dispatches", "executions", "bootstrap-sessions"}
    downstream = [str(path) for path in runtime.rglob("*.json") if any(part in prohibited for part in path.parts)]
    if downstream:
        raise BootstrapVerificationError(f"downstream artifacts exist: {downstream}")
    return {"result": "PASS", "bootstrap_state": first["bootstrap_state"],
            "bootstrap_result": first["bootstrap_result"], "provider_ready": True,
            "provider_selected": False, "dispatch_created": False, "execution_started": False,
            "next_action": first["next_action"], "duplicate_bootstrap": "IDEMPOTENT",
            "artifact_counts": counts, "downstream_artifacts": "NONE"}
