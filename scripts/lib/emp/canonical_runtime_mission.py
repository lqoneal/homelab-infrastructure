"""Read-only discovery projection for canonical P4 runtime missions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from scripts.lib.emp.bootstrap_boundary import _transaction_digest
from scripts.lib.emp.mission_admission_boundary import _canonical, _digest, _load
from scripts.lib.emp.repository_identity import resolve
from scripts.lib.emp.runtime_paths import runtime_root
from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.emp.provider_selection import _mission_artifacts, _verify_set
from scripts.lib.emp import provider_session
from scripts.lib.emp import provider_invocation
from scripts.lib.emp import execution_start
from scripts.lib.emp import codex_adapter


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
    baseline = resolve_baseline(
        root, Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")),
        mission_provenance_baseline=bootstrap.get("repository_baseline"),
        runtime_identity=_load(runtime / "runtime-identity.json"),
    )
    if baseline["result"] != "PASS":
        first = baseline["errors"][0] if baseline["errors"] else {"code": "PUBLICATION_PARITY_FAILURE", "message": "canonical baseline resolution failed"}
        raise CanonicalRuntimeMissionError(f"{first['code']}: {first['message']}")
    if admission.get("operation") != "BETA" or bootstrap.get("repository_baseline") != admission.get("repository_baseline"):
        raise CanonicalRuntimeMissionError("Operation Beta or baseline binding is invalid")
    artifacts = {"bootstrap_transaction": (bootstrap_path, bootstrap)}
    for directory, field in (("execution-records", "execution_record"), ("bootstrap-receipts", "bootstrap_receipt"), ("bootstrap-journals", "bootstrap_journal"), ("provider-readiness", "provider_readiness")):
        path, value = _artifact(runtime, directory, bootstrap[field], field)
        artifacts[field] = (path, value)
        if value.get("mission_id") != mission_id:
            raise CanonicalRuntimeMissionError(f"{field} mission identity mismatch")
    provider_stage = _verify_set(runtime, _mission_artifacts(runtime, mission_id))
    dispatch_stage = None
    try:
        from scripts.lib.emp.dispatch_foundation import _found, _verify_set as verify_dispatch_set
        dispatch_stage = verify_dispatch_set(runtime, _found(runtime, mission_id))
    except Exception as error:
        raise CanonicalRuntimeMissionError(str(error)) from error
    if provider_stage:
        for key, descriptor in provider_stage["artifacts"].items():
            artifacts[key] = (Path(descriptor["path"]), _load(Path(descriptor["path"])))
        provider_selected = True
        provider_qualified = bool(provider_stage.get("provider_qualified"))
        dispatch_eligible = bool(provider_stage.get("dispatch_eligible"))
        next_action = "EVALUATE_PROVIDER_DISPATCH"
    else:
        provider_selected = False
        provider_qualified = False
        dispatch_eligible = False
        next_action = bootstrap["next_action"]
    if dispatch_stage:
        for key, descriptor in dispatch_stage["artifacts"].items():
            artifacts[key] = (Path(descriptor["path"]), _load(Path(descriptor["path"])))
        session_stage = provider_session.verify(root, mission_id, runtime_root=runtime)
        if session_stage.get("result") != "PASS":
            blocker = session_stage.get("blockers", [{"message": "provider-session verification failed"}])[0]
            raise CanonicalRuntimeMissionError(f"{blocker.get('code', 'PROVIDER_SESSION_INVALID')}: {blocker.get('message')}")
        for key, descriptor in session_stage.get("artifacts", {}).items():
            artifacts[key] = (Path(descriptor["path"]), _load(Path(descriptor["path"])))
        invocation_stage = provider_invocation.verify(root, mission_id, runtime_root=runtime)
        if invocation_stage.get("result") != "PASS":
            blocker = invocation_stage.get("blockers", [{"message": "provider-invocation verification failed"}])[0]
            raise CanonicalRuntimeMissionError(f"{blocker.get('code', 'PROVIDER_INVOCATION_INVALID')}: {blocker.get('message')}")
        for key, descriptor in invocation_stage.get("artifacts", {}).items():
            artifacts[key] = (Path(descriptor["path"]), _load(Path(descriptor["path"])))
        execution_stage = execution_start.verify(root, mission_id, runtime_root=runtime)
        if execution_stage.get("result") != "PASS":
            blocker = execution_stage.get("blockers", [{"message": "execution-start verification failed"}])[0]
            raise CanonicalRuntimeMissionError(f"{blocker.get('code', 'EXECUTION_START_INVALID')}: {blocker.get('message')}")
        for key, descriptor in execution_stage.get("artifacts", {}).items():
            artifacts[key] = (Path(descriptor["path"]), _load(Path(descriptor["path"])))
        next_action = execution_stage.get("next_authorized_action") if execution_stage.get("execution_started") else invocation_stage.get("next_authorized_action", session_stage.get("next_authorized_action", "ESTABLISH_PROVIDER_SESSION"))
    else:
        session_stage = {}
        invocation_stage = {}
        execution_stage = {}
    codex_stage = codex_adapter.status(root, mission_id, runtime_root=runtime) if execution_stage.get("result") == "PASS" else {}
    if codex_stage.get("state") == "NOT_STARTED":
        codex_stage = {}
    elif codex_stage.get("state") == "RECONCILED_HISTORICAL":
        next_action = codex_stage.get("next_authorized_action", "FOLLOW_CURRENT_OPERATION_BETA_AUTHORITY")
    mission_work_started = bool(codex_stage.get("mission_work_started", execution_stage.get("mission_work_started", False)))
    repository_work_started = bool(codex_stage.get("repository_work_started", execution_stage.get("repository_work_started", False)))
    execution_monitoring_active = codex_stage.get("execution_monitoring") == "ACTIVE"
    return {
        "result": "PASS", "mission": "DISCOVERABLE", "mission_id": mission_id,
        "wop_id": submission.get("wop_id"), "operation": "BETA",
        "submission_id": submission["submission_id"], "submission_state": submission["submission_state"],
        "admission_id": admission["admission_id"], "admission_state": admission["admission_state"],
        "bootstrap_id": bootstrap["bootstrap_id"], "bootstrap_state": bootstrap["bootstrap_state"],
        "bootstrap_result": bootstrap["bootstrap_result"], "provider_ready": True,
        "provider_selected": provider_selected, "provider_qualified": provider_qualified,
        "dispatch_eligible": dispatch_eligible, "dispatch_created": bool(dispatch_stage), "provider_session_created": bool(session_stage.get("provider_session_created")), "provider_session_authorized": bool(session_stage.get("provider_session_authorized")), "provider_session_id": session_stage.get("provider_session_id"), "provider_session_state": session_stage.get("session_state"), "provider_invoked": bool(invocation_stage.get("provider_invoked", session_stage.get("provider_invoked", False))), "provider_acknowledged": bool(invocation_stage.get("provider_acknowledged", False)), "provider_invocation_id": invocation_stage.get("provider_invocation_id"), "provider_invocation_state": invocation_stage.get("provider_invocation_state"), "invocation_provenance_baseline": invocation_stage.get("invocation_provenance_baseline"), "execution_start_eligible": bool(invocation_stage.get("execution_start_eligible", False)), "execution_start_verification": execution_stage.get("result", "NOT_STARTED"), "execution_id": execution_stage.get("execution_id"), "execution_session_id": execution_stage.get("execution_session_id"), "execution_start_state": execution_stage.get("execution_start_state"), "execution_start_authorized": bool(execution_stage.get("execution_start_authorized", False)), "execution_session_created": bool(execution_stage.get("execution_session_created", False)), "provider_process_bound": bool(execution_stage.get("provider_process_bound", False)), "execution_adapter_mode": execution_stage.get("execution_adapter_mode"), "execution_started": bool(execution_stage.get("execution_started", False)), "mission_work_started": mission_work_started, "repository_work_started": repository_work_started, "execution_monitoring_active": execution_monitoring_active, "completion_reported": bool(execution_stage.get("completion_reported", False)), "codex_session_id": codex_stage.get("session_id"), "codex_session_state": codex_stage.get("state"), "codex_process_alive": codex_stage.get("process_alive", False),
        "execution_start_provenance_baseline": execution_stage.get("execution_start_provenance_baseline"),
        "execution_start_baseline_relationship": execution_stage.get("execution_start_baseline_relationship", execution_stage.get("baseline_relationship")),
        "execution_start_integrity": execution_stage.get("execution_start_integrity", "FAIL" if execution_stage else "NOT_STARTED"),
        "current_published_baseline": execution_stage.get("current_published_baseline", invocation_stage.get("current_published_baseline", baseline.get("published_head"))),
        "next_action": next_action, "next_authorized_action": next_action,
        "repository": {**identity, "current_baseline": baseline["current_head"], "published_baseline": baseline["published_head"], "eos_baseline": baseline["eos_baseline"], "mission_provenance_baseline": baseline["mission_provenance_baseline"], "mission_baseline_relationship": baseline["mission_baseline_relationship"]},
        "repository_baseline": bootstrap["repository_baseline"], "baseline_resolution": baseline,
        "authority": "Operation Beta", "blockers": [],
        "provider_id": provider_stage.get("provider_id") if provider_stage else None,
        "provider_selection_id": provider_stage.get("provider_selection_id") if provider_stage else None,
        "provider_selection": provider_stage or {},
        "dispatch": dispatch_stage or {},
        "provider_session": session_stage,
        "provider_invocation": invocation_stage,
        "execution_start": execution_stage, "codex": codex_stage,
        "artifacts": {name: {"path": str(path), "digest": (value.get("transaction_digest") if name == "bootstrap_transaction" else value.get("artifact_digest"))} for name, (path, value) in artifacts.items()},
    }


def view(repository: Path | str, action: str, mission_id: str) -> dict[str, Any]:
    value = discover(repository, mission_id)
    value["view"] = action
    if action == "blockers":
        value["blockers"] = []
    return value
