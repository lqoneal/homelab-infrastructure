"""Read-only discovery projection for canonical P4 runtime missions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.lib.emp.bootstrap_boundary import _transaction_digest
from scripts.lib.emp.mission_admission_boundary import _canonical, _digest, _load
from scripts.lib.emp.repository_identity import resolve
from scripts.lib.emp.runtime_paths import runtime_root


class CanonicalRuntimeMissionError(ValueError):
    """Canonical runtime mission state is absent or inconsistent."""


def _one(directory: Path, mission_id: str, label: str) -> tuple[Path, dict[str, Any]]:
    matches = []
    for path in sorted(directory.glob("*.json")):
        value = _load(path)
        if value.get("mission_id") == mission_id:
            matches.append((path, value))
    if len(matches) != 1:
        raise CanonicalRuntimeMissionError(f"{label} cardinality is {len(matches)} for {mission_id}")
    return matches[0]


def _artifact(runtime: Path, directory: str, descriptor: dict[str, Any], label: str) -> tuple[Path, dict[str, Any]]:
    raw = descriptor.get("path")
    if not isinstance(raw, str):
        raise CanonicalRuntimeMissionError(f"{label} path is missing")
    path = Path(raw).resolve()
    try:
        path.relative_to(runtime)
    except ValueError as error:
        raise CanonicalRuntimeMissionError(f"{label} path escapes runtime") from error
    if path.parent.name != directory or not path.is_file():
        raise CanonicalRuntimeMissionError(f"{label} path is invalid")
    value = _load(path)
    expected = descriptor.get("digest")
    if directory == "bootstraps":
        if expected != value.get("transaction_digest") or expected != _transaction_digest(value):
            raise CanonicalRuntimeMissionError(f"{label} digest mismatch")
    elif expected != value.get("artifact_digest") or expected != _digest({k: v for k, v in value.items() if k != "artifact_digest"}):
        raise CanonicalRuntimeMissionError(f"{label} digest mismatch")
    return path, value


def discover(repository: Path | str, mission_id: str) -> dict[str, Any]:
    root = Path(repository).resolve()
    runtime = runtime_root(root).resolve()
    mission_id = str(mission_id).upper()
    submission_path, submission = _one(runtime / "submissions" / "receipts", mission_id, "submission")
    admission_path, admission = _one(runtime / "admissions", mission_id, "admission")
    bootstrap_path, bootstrap = _one(runtime / "bootstraps", mission_id, "bootstrap")
    if submission.get("submission_state") != "ADMISSION_REQUESTED" or submission.get("submission_result") != "PASS":
        raise CanonicalRuntimeMissionError("submission is not ADMISSION_REQUESTED/PASS")
    if admission.get("admission_state") != "ADMISSION_COMPLETE" or admission.get("admission_result") != "PASS":
        raise CanonicalRuntimeMissionError("admission is not ADMISSION_COMPLETE/PASS")
    if bootstrap.get("bootstrap_state") != "READY_FOR_EXECUTION_PROVIDER" or bootstrap.get("bootstrap_result") != "PASS":
        raise CanonicalRuntimeMissionError("bootstrap is not provider-ready")
    if bootstrap.get("provider_ready") is not True or any(bootstrap.get(k) is not False for k in ("provider_selected", "dispatch_created", "execution_started")):
        raise CanonicalRuntimeMissionError("bootstrap crosses the provider boundary")
    if admission.get("admission_id") != bootstrap.get("admission_id") or submission.get("submission_id") != admission.get("submission_id"):
        raise CanonicalRuntimeMissionError("canonical identity chain is inconsistent")
    identity = resolve(root)
    if admission.get("operation") != "BETA" or bootstrap.get("repository_baseline") != admission.get("repository_baseline"):
        raise CanonicalRuntimeMissionError("Operation Beta or baseline binding is invalid")
    artifacts = {"bootstrap_transaction": (bootstrap_path, bootstrap)}
    for directory, field in (("execution-records", "execution_record"), ("bootstrap-receipts", "bootstrap_receipt"), ("bootstrap-journals", "bootstrap_journal"), ("provider-readiness", "provider_readiness")):
        path, value = _artifact(runtime, directory, bootstrap[field], field)
        artifacts[field] = (path, value)
        if value.get("mission_id") != mission_id:
            raise CanonicalRuntimeMissionError(f"{field} mission identity mismatch")
    return {
        "result": "PASS", "mission": "DISCOVERABLE", "mission_id": mission_id,
        "wop_id": submission.get("wop_id"), "operation": "BETA",
        "submission_id": submission["submission_id"], "submission_state": submission["submission_state"],
        "admission_id": admission["admission_id"], "admission_state": admission["admission_state"],
        "bootstrap_id": bootstrap["bootstrap_id"], "bootstrap_state": bootstrap["bootstrap_state"],
        "bootstrap_result": bootstrap["bootstrap_result"], "provider_ready": True,
        "provider_selected": False, "dispatch_created": False, "execution_started": False,
        "next_action": bootstrap["next_action"], "next_authorized_action": bootstrap["next_action"],
        "repository": identity, "repository_baseline": bootstrap["repository_baseline"],
        "authority": "Operation Beta", "blockers": [],
        "artifacts": {name: {"path": str(path), "digest": (value.get("transaction_digest") if name == "bootstrap_transaction" else value.get("artifact_digest"))} for name, (path, value) in artifacts.items()},
    }


def view(repository: Path | str, action: str, mission_id: str) -> dict[str, Any]:
    value = discover(repository, mission_id)
    value["view"] = action
    if action == "blockers":
        value["blockers"] = []
    return value
