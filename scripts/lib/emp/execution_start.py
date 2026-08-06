"""Bounded P5-G5 execution-start foundation.

This controller starts only the qualification execution boundary.  It creates
an immutable, provider-bound execution session projection and acknowledgement;
it never launches ``engctl codex``, delivers mission work, or monitors a
process.  The mode is intentionally explicit so this state cannot be
mistaken for a real Codex execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.provider_invocation import verify as verify_provider_invocation
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos import operational_beta


CONTRACT = "ZEUS-P5-G5-EXECUTION-START-FOUNDATION"
VERSION = "1"
MODE = "QUALIFICATION_ADAPTER"
ADAPTER_ID = "zeus-bounded-execution-session-v1"
STAGE_DIRS = {
    "execution_start_transaction": "execution-start-transactions",
    "execution_start_authorization": "execution-start-authorizations",
    "execution_start_package": "execution-start-packages",
    "execution_session": "execution-sessions",
    "execution_start_acknowledgement": "execution-start-acknowledgements",
    "execution_start_receipt": "execution-start-receipts",
    "execution_start_journal": "execution-start-journals",
    "controlled_execution_readiness": "controlled-execution-readiness",
}
ARTIFACT_TYPES = {key: key.replace("_", "-") for key in STAGE_DIRS}


class ExecutionStartError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code, self.message, self.next_action = code, message, next_action
        super().__init__(message)


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root:
        return Path(runtime_root).resolve()
    return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception as error:
        raise ExecutionStartError("EXECUTION_ARTIFACT_INVALID", f"{path}: {error}") from error
    return value


def _found(runtime: Path, mission_id: str) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    found = {key: [] for key in STAGE_DIRS}
    for key, directory in STAGE_DIRS.items():
        location = runtime / directory
        for path in sorted(location.glob("*.json")) if location.is_dir() else ():
            value = _load(path)
            if value.get("mission_id") == mission_id:
                found[key].append((path, value))
    return found


def _path(runtime: Path, key: str, descriptor: Mapping[str, Any]) -> Path:
    raw = descriptor.get("path")
    if not isinstance(raw, str):
        raise ExecutionStartError("EXECUTION_PATH_INVALID", f"{key} path is missing")
    path = Path(raw).resolve()
    try:
        path.relative_to(runtime)
    except ValueError as error:
        raise ExecutionStartError("EXECUTION_PATH_ESCAPE", f"{key} path escapes authoritative runtime") from error
    if path.parent != runtime / STAGE_DIRS[key] or not path.is_file():
        raise ExecutionStartError("EXECUTION_PATH_INVALID", f"{key} path is not canonical")
    return path


def _verify_set(runtime: Path, found: dict[str, list[tuple[Path, dict[str, Any]]]]) -> dict[str, Any] | None:
    if not any(found.values()):
        return None
    if any(len(items) != 1 for items in found.values()):
        raise ExecutionStartError("EXECUTION_CARDINALITY_CONFLICT", "execution-start artifact cardinality is not exactly one per class")
    values = {key: items[0][1] for key, items in found.items()}
    anchor = values["execution_start_transaction"]
    execution_id = anchor.get("execution_id")
    if not execution_id or anchor.get("execution_start_state") != "READY_FOR_CONTROLLED_EXECUTION":
        raise ExecutionStartError("EXECUTION_STATE_INVALID", "execution start is not controlled-execution-ready")
    binding_fields = ("mission_id", "provider_invocation_id", "provider_session_id", "provider_id",
                      "dispatch_id", "repository_identity", "current_published_baseline",
                      "invocation_provenance_baseline", "execution_package_digest",
                      "execution_authority_digest", "mission_contract_digest")
    for key, value in values.items():
        if value.get("artifact_type") != ARTIFACT_TYPES[key]:
            raise ExecutionStartError("EXECUTION_ARTIFACT_MISMATCH", f"{key} artifact type mismatch")
        if value.get("artifact_digest") != digest({k: v for k, v in value.items() if k != "artifact_digest"}):
            raise ExecutionStartError("EXECUTION_DIGEST_MISMATCH", f"{key} digest mismatch")
        if value.get("execution_id") != execution_id:
            raise ExecutionStartError("EXECUTION_IDENTITY_MISMATCH", f"{key} execution identity mismatch")
        if any(value.get(field) != anchor.get(field) for field in binding_fields):
            raise ExecutionStartError("EXECUTION_BINDING_MISMATCH", f"{key} execution binding mismatch")
        if values[key] and found[key][0][0].name != f"{execution_id}.json":
            raise ExecutionStartError("EXECUTION_PATH_INVALID", f"{key} filename is not canonical")
    for key, descriptor in (anchor.get("artifacts") or {}).items():
        if key not in values or descriptor.get("digest") != values[key].get("artifact_digest"):
            raise ExecutionStartError("EXECUTION_ARTIFACT_MISMATCH", f"{key} descriptor digest mismatch")
        if _path(runtime, key, descriptor) != found[key][0][0].resolve():
            raise ExecutionStartError("EXECUTION_PATH_INVALID", f"{key} descriptor path mismatch")
    required = {"execution_start_authorized": True, "execution_session_created": True,
                "execution_started": True, "provider_process_bound": True,
                "mission_work_started": False, "repository_work_started": False,
                "execution_monitoring_active": False, "completion_reported": False}
    if any(anchor.get(key) != expected for key, expected in required.items()):
        raise ExecutionStartError("EXECUTION_BOUNDARY_FAILURE", "execution start crosses the controlled-work boundary")
    if anchor.get("execution_adapter_mode") != MODE:
        raise ExecutionStartError("EXECUTION_MODE_INVALID", "unsupported execution adapter mode")
    if values["execution_start_acknowledgement"].get("acknowledged") is not True:
        raise ExecutionStartError("EXECUTION_ACKNOWLEDGEMENT_MISSING", "execution acknowledgement is absent")
    return {"result": "PASS", "mission_id": anchor["mission_id"], "execution_id": execution_id,
            "execution_session_id": anchor["execution_session_id"], "execution_start_state": anchor["execution_start_state"],
            "execution_start_result": "PASS", "execution_start_authorized": True,
            "execution_session_created": True, "execution_started": True,
            "provider_process_bound": True, "provider_id": anchor["provider_id"],
            "provider_invocation_id": anchor["provider_invocation_id"], "provider_session_id": anchor["provider_session_id"],
            "execution_adapter_mode": MODE, "mission_work_started": False, "repository_work_started": False,
            "execution_monitoring_active": False, "completion_reported": False,
            "execution_start_replay": "IDEMPOTENT", "invocation_provenance_baseline": anchor["invocation_provenance_baseline"],
            "current_published_baseline": anchor["current_published_baseline"], "artifacts": {
                key: {"path": str(items[0][0]), "digest": items[0][1]["artifact_digest"]} for key, items in found.items()},
            "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK", "blockers": [], "read_only": True}


def _resolve(root: Path, mission_id: str, runtime: Path, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    authority = operational_beta.authority(root)
    if not (authority.get("result") == "PASS" and authority.get("authority_framework") == "OPERATION_BETA"
            and authority.get("authority_integrity") == "PASS" and authority.get("authority_resolution") == "PASS"
            and authority.get("oa_authority") == "SUPERSEDED"):
        raise ExecutionStartError("AUTHORITY_FAILURE", "published Operation Beta authority chain failed")
    invocation = verify_provider_invocation(root, mission_id, runtime_root=runtime)
    if invocation.get("result") != "PASS":
        raise ExecutionStartError("PROVIDER_INVOCATION_FAILURE", "provider invocation verification failed")
    if invocation.get("provider_invocation_state") != "READY_FOR_EXECUTION_START" or not invocation.get("execution_start_eligible"):
        raise ExecutionStartError("INVOCATION_NOT_READY", "provider invocation is not execution-start eligible")
    if invocation.get("execution_started") or invocation.get("mission_work_started"):
        raise ExecutionStartError("EXECUTION_ALREADY_STARTED", "execution or mission work already started")
    from scripts.lib.emp.mission_verification_controller import verify as verify_mission
    mission = verify_mission(root, mission_id, runtime_root=runtime, include_provider_invocation=False)
    if mission.get("result") != "PASS":
        raise ExecutionStartError("MISSION_VERIFICATION_FAILURE", "earlier mission stages failed verification")
    refs = invocation.get("artifacts", {})
    package = refs.get("provider_invocation_package")
    if not package:
        raise ExecutionStartError("INVOCATION_PACKAGE_MISSING", "provider invocation package is missing")
    mission_refs = mission.get("artifacts", {})
    required = ("mission_contract", "execution_authority", "execution_package")
    if any(name not in mission_refs for name in required):
        raise ExecutionStartError("EXECUTION_PACKAGE_INCOMPLETE", "execution-start bindings are incomplete")
    existing_provenance = (existing or {}).get("invocation_provenance_baseline")
    invocation_id = invocation["provider_invocation_id"]
    inputs = {
        "mission_id": mission_id, "wop_id": mission.get("wop_id"), "submission_id": mission.get("submission_id"),
        "admission_id": mission.get("admission_id"), "bootstrap_id": mission.get("bootstrap_id"),
        "provider_selection_id": mission.get("provider_selection_id"), "dispatch_id": invocation["dispatch_id"],
        "provider_session_id": invocation["provider_session_id"], "provider_invocation_id": invocation_id,
        "provider_id": invocation["provider_id"], "mission_contract_digest": mission_refs["mission_contract"]["digest"],
        "execution_authority_digest": mission_refs["execution_authority"]["digest"],
        "execution_package_digest": mission_refs["execution_package"]["digest"],
        "provider_invocation_package_digest": package["digest"],
        "repository_identity": (mission.get("repository") or {}).get("repository_identity"),
        "current_published_baseline": invocation["current_published_baseline"],
        "invocation_provenance_baseline": invocation["invocation_provenance_baseline"],
        "execution_start_contract": [CONTRACT, VERSION],
    }
    if existing_provenance and existing_provenance != inputs["invocation_provenance_baseline"]:
        raise ExecutionStartError("EXECUTION_INPUT_MISMATCH", "immutable invocation provenance changed")
    execution_id = identifier("EXECUTION-START", inputs)
    session_id = identifier("EXECUTION-SESSION", {"execution_id": execution_id, "provider_invocation_id": invocation_id})
    return {"invocation": invocation, "mission": mission, "inputs": inputs, "execution_id": execution_id,
            "execution_session_id": session_id, "provider_invocation_package": package}


def _expected(resolved: Mapping[str, Any], runtime: Path) -> dict[str, dict[str, Any]]:
    i = dict(resolved["inputs"]); execution_id = resolved["execution_id"]; session_id = resolved["execution_session_id"]
    common = {"schema_version": 1, "mission_id": i["mission_id"], **i, "execution_id": execution_id,
              "execution_session_id": session_id, "execution_adapter_mode": MODE,
              "adapter_id": ADAPTER_ID, "execution_started": True, "execution_session_created": True,
              "provider_process_bound": True, "mission_work_started": False, "repository_work_started": False,
              "execution_monitoring_active": False, "completion_reported": False,
              "execution_start_contract": {"id": CONTRACT, "version": VERSION}}
    refs = {key: {"path": str((runtime / STAGE_DIRS[key] / f"{execution_id}.json").resolve())} for key in STAGE_DIRS if key != "execution_start_transaction"}
    values = {
        "execution_start_authorization": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_authorization"], authorization_result="PASS", execution_start_authorized=True, next_authorized_action="BEGIN_CONTROLLED_MISSION_WORK"),
        "execution_start_package": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_package"], package_state="EXECUTION_START_ACCEPTED", provider_invocation_package=dict(resolved["provider_invocation_package"]), prohibited_actions=["MISSION_WORK", "REPOSITORY_MUTATION", "EXECUTION_MONITORING", "COMPLETION"], stop_condition="STOP_BEFORE_CONTROLLED_MISSION_WORK"),
        "execution_session": dict(common, artifact_type=ARTIFACT_TYPES["execution_session"], session_state="READY_FOR_CONTROLLED_EXECUTION", process_identity=f"QUALIFICATION-PROCESS-{execution_id}", session_binding="QUALIFICATION_IDLE_BOUNDARY"),
        "execution_start_acknowledgement": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_acknowledgement"], acknowledged=True, acknowledgement_result="PASS", provider_bound_context_digest=digest({"provider_id": i["provider_id"], "provider_invocation_id": i["provider_invocation_id"], "execution_id": execution_id})),
        "execution_start_receipt": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_receipt"], receipt_type="execution-start", result="PASS", replay="IDEMPOTENT"),
        "execution_start_journal": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_journal"], states=["EXECUTION_START_EVALUATING", "EXECUTION_START_AUTHORIZED", "EXECUTION_SESSION_CREATED", "EXECUTION_STARTED", "READY_FOR_CONTROLLED_EXECUTION"], process_contacted=False, process_bound=True, mission_work_started=False),
        "controlled_execution_readiness": dict(common, artifact_type=ARTIFACT_TYPES["controlled_execution_readiness"], readiness_state="READY_FOR_CONTROLLED_EXECUTION", next_action="BEGIN_CONTROLLED_MISSION_WORK"),
    }
    for value in values.values(): value["artifact_digest"] = digest(value)
    transaction = dict(common, artifact_type=ARTIFACT_TYPES["execution_start_transaction"], execution_start_state="READY_FOR_CONTROLLED_EXECUTION", execution_start_result="PASS", execution_start_authorized=True, artifacts=refs)
    transaction["artifacts"] = {key: refs[key] | {"digest": values[key]["artifact_digest"]} for key in refs}
    transaction["artifact_digest"] = digest(transaction)
    values["execution_start_transaction"] = transaction
    return values


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id = Path(repository).resolve(), str(mission_id).upper(); runtime = _runtime(root, runtime_root)
    try:
        found = _found(runtime, mission_id); existing = _verify_set(runtime, found)
        anchor = _load(existing["artifacts"]["execution_start_transaction"]["path"]) if existing else None
        resolved = _resolve(root, mission_id, runtime, existing=anchor)
        if existing and existing.get("execution_id") != resolved["execution_id"]:
            raise ExecutionStartError("EXECUTION_INPUT_MISMATCH", "execution-critical input differs from immutable execution binding")
        if existing:
            existing.update({"current_published_baseline": resolved["inputs"]["current_published_baseline"], "read_only": True})
            return existing
        return {"result": "PASS", "mission_id": mission_id, "execution_start_created": False,
                "execution_started": False, "mission_work_started": False, "read_only": True,
                "blockers": [], "next_authorized_action": "START_EXECUTION"}
    except ExecutionStartError as error:
        return {"result": "FAIL", "mission_id": mission_id, "execution_start_created": False,
                "execution_started": False, "mission_work_started": False, "read_only": True,
                "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def create(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id = Path(repository).resolve(), str(mission_id).upper(); runtime = _runtime(root, runtime_root)
    try:
        found = _found(runtime, mission_id); existing = _verify_set(runtime, found)
        if existing:
            return {**existing, "read_only": False, "duplicate_execution_start": "IDEMPOTENT"}
        resolved = _resolve(root, mission_id, runtime)
        values = _expected(resolved, runtime)
        for key, value in values.items():
            path = runtime / STAGE_DIRS[key] / f"{resolved['execution_id']}.json"
            if path.exists():
                raise ExecutionStartError("EXECUTION_CONFLICT", f"existing execution-start path conflicts: {path}")
            atomic_write(path, value)
        result = verify(root, mission_id, runtime_root=runtime)
        if result.get("result") != "PASS":
            raise ExecutionStartError("EXECUTION_PARTIAL_STATE", "execution-start artifact chain failed post-write verification")
        return {**result, "read_only": False, "duplicate_execution_start": "NO"}
    except ExecutionStartError as error:
        return {"result": "FAIL", "mission_id": mission_id, "execution_start_created": False,
                "execution_started": False, "mission_work_started": False, "read_only": False,
                "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def render(value: Mapping[str, Any]) -> str:
    blockers = value.get("blockers", [])
    return "\n".join(("Zeus Execution Start", "--------------------", f"Result                    : {value.get('result')}", f"Execution ID             : {value.get('execution_id', 'NONE')}", f"Session ID               : {value.get('execution_session_id', 'NONE')}", f"Adapter mode             : {value.get('execution_adapter_mode', 'NOT_STARTED')}", f"Execution started        : {'YES' if value.get('execution_started') else 'NO'}", f"Provider process bound   : {'YES' if value.get('provider_process_bound') else 'NO'}", f"Mission work started     : {'YES' if value.get('mission_work_started') else 'NO'}", f"Replay                   : {value.get('execution_start_replay', 'NOT_RUN')}", f"Blockers                 : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}", f"Next action              : {value.get('next_authorized_action')}", "Read-only                : YES" if value.get('read_only') else "Read-only                : NO (execution start materialized)"))
