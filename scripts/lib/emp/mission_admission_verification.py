"""Read-only Zeus P3-G1 admission replay verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest as _canonical_digest
from scripts.lib.emp.mission_admission_boundary import _load as _canonical_load
from scripts.lib.emp.repository_identity import resolve
from scripts.lib.emp.wop_verification import verify_artifact


class MissionAdmissionVerificationError(ValueError):
    """The canonical admission replay evidence is incomplete or inconsistent."""


def _load(path: Path) -> dict[str, Any]:
    try:
        return _canonical_load(path)
    except ValueError as error:
        raise MissionAdmissionVerificationError(str(error)) from error


def _check_artifact(path: Path, expected: str) -> dict[str, Any]:
    value = _load(path)
    supplied = value.get("artifact_digest")
    if supplied != expected or supplied != _canonical_digest(
            {key: item for key, item in value.items() if key != "artifact_digest"}):
        raise MissionAdmissionVerificationError(f"artifact digest mismatch: {path}")
    return value


def _canonical_artifact_path(raw: Any, runtime: Path, class_name: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise MissionAdmissionVerificationError(f"{class_name} path is missing")
    path = Path(raw).resolve()
    try:
        path.relative_to(runtime)
    except ValueError as error:
        raise MissionAdmissionVerificationError(
            f"{class_name} path escapes the authorized runtime: {path}"
        ) from error
    if path.parent.name != class_name:
        raise MissionAdmissionVerificationError(
            f"{class_name} path is not in the canonical storage directory: {path}"
        )
    return path


def verify_admission_replay(first: Mapping[str, Any], replay: Mapping[str, Any], *,
                            runtime_root: Path | str, wop: Path | str,
                            repository: Path | str) -> dict[str, Any]:
    """Verify two outputs from the canonical ``zeus admit`` command."""
    required = ("admission_id", "transaction_type", "transaction_digest",
                "admission_state", "admission_result", "package",
                "mission_contract", "execution_authority", "admission_receipt",
                "admission_journal", "bootstrap_eligible", "execution_created")
    if any(key not in first for key in required):
        raise MissionAdmissionVerificationError("first admission response is incomplete")
    if first.get("admission_state") != "ADMISSION_COMPLETE" or first.get("admission_result") != "PASS":
        raise MissionAdmissionVerificationError("admission did not reach ADMISSION_COMPLETE/PASS")
    if first.get("transaction_type") != "mission-admission":
        raise MissionAdmissionVerificationError("Mission Admission transaction type is invalid")
    if first.get("bootstrap_eligible") is not True or first.get("execution_created") is not False:
        raise MissionAdmissionVerificationError("bootstrap or execution boundary is invalid")
    transaction_digest = first.get("transaction_digest")
    if (not isinstance(transaction_digest, str) or
            transaction_digest != _canonical_digest({key: value for key, value in first.items()
                                                     if key != "transaction_digest"})):
        raise MissionAdmissionVerificationError("Mission Admission transaction digest mismatch")
    if replay.get("duplicate_admission") != "IDEMPOTENT":
        raise MissionAdmissionVerificationError("replay is not IDEMPOTENT")
    stable = ("admission_id", "transaction_type", "mission_id", "wop_id", "submission_id", "package_digest",
              "mission_contract_digest", "execution_authority_digest", "repository_baseline",
              "transaction_digest")
    for key in stable:
        if first.get(key) != replay.get(key):
            raise MissionAdmissionVerificationError(f"replay identity or digest changed: {key}")
    for field in ("package", "mission_contract", "execution_authority", "admission_receipt", "admission_journal"):
        if first.get(field) != replay.get(field):
            raise MissionAdmissionVerificationError(f"replay artifact descriptor changed: {field}")
    runtime = Path(runtime_root).resolve()
    descriptors = {
        "packages": "package",
        "mission-contracts": "mission_contract",
        "execution-authority": "execution_authority",
        "receipts": "admission_receipt",
        "journals": "admission_journal",
    }
    if any(not isinstance(first.get(field), Mapping) for field in descriptors.values()):
        raise MissionAdmissionVerificationError("admission artifact descriptor is invalid")
    paths = {
        key: _canonical_artifact_path(first[field].get("path"), runtime, key)
        for key, field in descriptors.items()
    }
    for field in descriptors.values():
        if not isinstance(first.get(field), Mapping) or not first[field].get("digest"):
            raise MissionAdmissionVerificationError(f"{field} digest is missing")
    receipt_path = paths["receipts"]
    if not receipt_path.is_file():
        raise MissionAdmissionVerificationError("admission receipt is missing")
    receipt = _check_artifact(receipt_path, first["admission_receipt"]["digest"])
    if receipt.get("receipt_type") != "admission" or receipt.get("admission_state") != "ADMISSION_COMPLETE":
        raise MissionAdmissionVerificationError("admission receipt content is invalid")
    if receipt.get("admission_id") != first["admission_id"]:
        raise MissionAdmissionVerificationError("admission receipt identity mismatch")
    artifact_values = {}
    for key in ("package", "mission_contract", "execution_authority", "admission_journal"):
        descriptor = first[key]
        artifact_values[key] = _check_artifact(paths[{
            "package": "packages",
            "mission_contract": "mission-contracts",
            "execution_authority": "execution-authority",
            "admission_journal": "journals",
        }[key]], descriptor["digest"])
    if artifact_values["package"].get("artifact_type") != "immutable-execution-package":
        raise MissionAdmissionVerificationError("immutable execution package class is invalid")
    if artifact_values["mission_contract"].get("artifact_type") != "mission-contract":
        raise MissionAdmissionVerificationError("Mission Contract class is invalid")
    if artifact_values["execution_authority"].get("artifact_type") != "execution-authority":
        raise MissionAdmissionVerificationError("execution-authority class is invalid")
    if artifact_values["admission_journal"].get("journal_type") != "admission":
        raise MissionAdmissionVerificationError("admission journal class is invalid")
    for key in ("mission_id", "wop_id", "submission_id", "admission_id"):
        values = [receipt.get(key)] + [value.get(key) for value in artifact_values.values() if key in value]
        if any(value != first.get(key) for value in values):
            raise MissionAdmissionVerificationError(f"artifact identity mismatch: {key}")
    if (receipt.get("operation") != "BETA" or
            any(value.get("operation") != "BETA" for value in artifact_values.values()
                if "operation" in value)):
        raise MissionAdmissionVerificationError("Operation Beta evidence is missing")
    identity = resolve(repository)
    if artifact_values["package"].get("repository", {}).get("canonical_repository_identity") != identity["canonical_repository_identity"]:
        raise MissionAdmissionVerificationError("canonical repository identity mismatch")
    if artifact_values["package"].get("repository_baseline") != first.get("repository_baseline"):
        raise MissionAdmissionVerificationError("repository baseline evidence mismatch")
    provenance = artifact_values["package"].get("immutable_provenance")
    if not isinstance(provenance, Mapping) or not provenance.get("traceability_digest"):
        raise MissionAdmissionVerificationError("immutable provenance is missing")
    wop_result = verify_artifact(Path(wop))
    if wop_result.get("result") != "PASS":
        raise MissionAdmissionVerificationError("authored-WOP integrity verification failed")
    if wop_result["traceability"].get("mission_id") != first.get("mission_id") or wop_result["traceability"].get("wop_id") != first.get("wop_id"):
        raise MissionAdmissionVerificationError("authored WOP and admission identities disagree")
    classes = {
        "immutable_execution_package": runtime / "packages",
        "mission_contract": runtime / "mission-contracts",
        "execution_authority": runtime / "execution-authority",
        "admission_receipt": runtime / "receipts",
        "admission_journal": runtime / "journals",
    }
    counts = {name: len(list(path.glob("*.json"))) for name, path in classes.items()}
    if any(count != 1 for count in counts.values()):
        raise MissionAdmissionVerificationError(f"required artifact cardinality is not exactly one: {counts}")
    if any(paths[key].name != f"{first['admission_id']}.json" for key in paths):
        raise MissionAdmissionVerificationError("canonical artifact filename does not match admission identity")
    if not all(paths[key].is_file() for key in paths):
        raise MissionAdmissionVerificationError("canonical admission artifact is missing")
    journal = artifact_values["admission_journal"]
    provisioned = journal.get("provisioned")
    expected_provisioned = [first[field]["digest"] for field in
                            ("package", "mission_contract", "execution_authority", "admission_receipt")]
    if provisioned != expected_provisioned:
        raise MissionAdmissionVerificationError("admission journal artifact provenance is incomplete")
    # mission-executions is a pre-existing legacy lifecycle store and is not a
    # canonical P3/P4 downstream artifact.  Canonical bootstrap artifacts use
    # bootstraps/, execution-records/, and provider-readiness/.
    prohibited = {"executions", "bootstrap", "providers", "dispatch", "provider-selection"}
    downstream = [str(path) for path in runtime.rglob("*.json") if any(part in prohibited for part in path.parts)]
    if downstream:
        raise MissionAdmissionVerificationError(f"downstream artifacts exist: {downstream}")
    return {
        "result": "PASS",
        "transaction": {
            "transaction_type": "mission-admission",
            "transaction_digest": first["transaction_digest"],
            "admission_id": first["admission_id"],
        },
        "bootstrap_boundary": {
            "bootstrap_eligible": True,
            "next_action": "EVALUATE_BOOTSTRAP_ELIGIBILITY",
            "execution_created": False,
            "bootstrap_performed": False,
        },
        "checks": {
            "receipt_integrity": "PASS", "authored_wop_integrity": "PASS",
            "mission_admission_transaction": "PASS",
            "submission_admission_identity_parity": "PASS", "operation_beta": "PASS",
            "repository_identity": "PASS", "immutable_provenance": "PASS",
            "no_operational_alpha_fallback": "PASS", "artifact_counts": counts,
            "downstream_artifacts": "NONE",
        },
    }
