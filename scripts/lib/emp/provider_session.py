"""P5-G3 canonical provider-session foundation.

This controller materializes a provider session record from the immutable
published dispatch.  It deliberately contains no provider adapter or
execution path: the terminal state is READY_FOR_PROVIDER_INVOCATION.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.dispatch_foundation import _found as _dispatch_found, _verify_set as _verify_dispatch_set
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.provider_selection import _mission_artifacts, _verify_set as _verify_provider_set
from scripts.lib.emp.runtime_paths import resolve_runtime


SESSION_CONTRACT = "ZEUS-P5-G3-PROVIDER-SESSION-FOUNDATION"
SESSION_VERSION = "1"
STAGE_DIRS = {
    "provider_session": "provider-sessions",
    "provider_session_receipt": "provider-session-receipts",
    "provider_session_journal": "provider-session-journals",
    "provider_session_authorization": "provider-session-authorizations",
    "provider_session_readiness": "provider-session-readiness-records",
}
ARTIFACT_TYPES = {
    "provider_session": "provider-session",
    "provider_session_receipt": "provider-session-receipt",
    "provider_session_journal": "provider-session-journal",
    "provider_session_authorization": "provider-session-authorization",
    "provider_session_readiness": "provider-session-readiness",
}


class ProviderSessionError(ValueError):
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
        raise ProviderSessionError("PROVIDER_SESSION_ARTIFACT_INVALID", f"{path}: {error}") from error
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


def _dispatch_snapshot(runtime: Path, value: Mapping[str, Any]) -> dict[str, str]:
    return {key: descriptor["digest"] for key, descriptor in (value.get("artifacts") or {}).items()}


def _provider_snapshot(value: Mapping[str, Any]) -> dict[str, str]:
    return {key: descriptor["digest"] for key, descriptor in (value.get("artifacts") or {}).items()}


def _verify_set(runtime: Path, found: dict[str, list[tuple[Path, dict[str, Any]]]]) -> dict[str, Any] | None:
    if not any(found.values()):
        return None
    if any(len(items) != 1 for items in found.values()):
        raise ProviderSessionError("PROVIDER_SESSION_CARDINALITY_CONFLICT", "provider-session artifact cardinality is not exactly one per class")
    values = {key: items[0][1] for key, items in found.items()}
    anchor = values["provider_session"]
    session_id = anchor.get("provider_session_id")
    if not session_id or anchor.get("session_state") != "READY_FOR_PROVIDER_INVOCATION":
        raise ProviderSessionError("PROVIDER_SESSION_STATE_INVALID", "provider session is not invocation-ready")
    for key, value in values.items():
        if value.get("artifact_type") != ARTIFACT_TYPES[key]:
            raise ProviderSessionError("PROVIDER_SESSION_ARTIFACT_MISMATCH", f"{key} artifact type mismatch")
        if value.get("artifact_digest") != digest({k: v for k, v in value.items() if k != "artifact_digest"}):
            raise ProviderSessionError("PROVIDER_SESSION_DIGEST_MISMATCH", f"{key} digest mismatch")
        if values[key] and values[key].get("provider_session_id") != session_id:
            raise ProviderSessionError("PROVIDER_SESSION_IDENTITY_MISMATCH", f"{key} session identity mismatch")
        if values[key] and values[key].get("mission_id") != anchor.get("mission_id"):
            raise ProviderSessionError("PROVIDER_SESSION_CROSS_MISSION", f"{key} mission identity mismatch")
        if values[key] and values[key].get("dispatch_id") != anchor.get("dispatch_id"):
            raise ProviderSessionError("PROVIDER_SESSION_DISPATCH_MISMATCH", f"{key} dispatch identity mismatch")
        if values[key] and values[key].get("provider_id") != anchor.get("provider_id"):
            raise ProviderSessionError("PROVIDER_SUBSTITUTION", f"{key} provider identity mismatch")
        if found[key][0][0].name != f"{session_id}.json" or found[key][0][0].parent.name != STAGE_DIRS[key]:
            raise ProviderSessionError("PROVIDER_SESSION_PATH_INVALID", f"{key} path is not canonical")
    for key, descriptor in (anchor.get("artifacts") or {}).items():
        if key not in values or descriptor.get("digest") != values[key].get("artifact_digest"):
            raise ProviderSessionError("PROVIDER_SESSION_ARTIFACT_MISMATCH", f"{key} descriptor digest mismatch")
        if Path(str(descriptor.get("path"))).resolve() != found[key][0][0].resolve():
            raise ProviderSessionError("PROVIDER_SESSION_PATH_INVALID", f"{key} descriptor path mismatch")
    if anchor.get("provider_session_authorized") is not True or anchor.get("provider_invoked") or anchor.get("execution_started"):
        raise ProviderSessionError("PROVIDER_SESSION_BOUNDARY_FAILURE", "provider session crosses the invocation boundary")
    return {
        "result": "PASS", "replay": "IDEMPOTENT", "provider_session_id": session_id,
        "dispatch_id": anchor["dispatch_id"], "provider_id": anchor["provider_id"],
        "session_state": anchor["session_state"], "provider_session_authorized": True,
        "provider_session_created": True, "provider_invoked": False, "invocation_started": False,
        "execution_started": False, "artifacts": {key: {"path": str(items[0][0]), "digest": items[0][1]["artifact_digest"]} for key, items in found.items()},
        "dispatch_artifacts": anchor.get("dispatch_artifacts", {}),
        "provider_selection_artifacts": anchor.get("provider_selection_artifacts", {}),
        "next_authorized_action": "INVOKE_PROVIDER",
    }


def _validate_inputs(root: Path, mission_id: str, runtime: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    dispatch = _verify_dispatch_set(runtime, _dispatch_found(runtime, mission_id))
    if not dispatch or dispatch.get("result") != "PASS" or not dispatch.get("dispatch_id"):
        # Dispatch discovery is mission-scoped.  Preserved dispatches for
        # other missions are historical/subordinate evidence and cannot make
        # this target mission invalid.  A target mission with session records
        # but no valid dispatch is different: it is an orphaned current
        # projection and must fail closed.
        if any(_found(runtime, mission_id).values()):
            raise ProviderSessionError("PROVIDER_SESSION_ORPHANED", "target mission has provider-session artifacts without a valid dispatch")
        raise ProviderSessionError("DISPATCH_NOT_READY", "published dispatch is not valid for provider-session creation")
    provider = _verify_provider_set(runtime, _mission_artifacts(runtime, mission_id))
    if not provider or provider.get("result") != "PASS":
        raise ProviderSessionError("PROVIDER_SELECTION_INVALID", "provider selection is not valid")
    if provider.get("provider_id") != dispatch.get("provider_id") or provider.get("provider_selection_id") != load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("provider_selection_id"):
        raise ProviderSessionError("PROVIDER_SUBSTITUTION", "provider selection differs from published dispatch")
    return dispatch, provider


def _expected(runtime: Path, dispatch: Mapping[str, Any], provider: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    inputs = {"mission_id": dispatch["mission_id"], "dispatch_id": dispatch["dispatch_id"], "provider_id": dispatch["provider_id"],
              "provider_selection_id": provider["provider_selection_id"], "dispatch_artifacts": _dispatch_snapshot(runtime, dispatch),
              "provider_selection_artifacts": _provider_snapshot(provider), "contract": [SESSION_CONTRACT, SESSION_VERSION]}
    session_id = identifier("PROVIDER-SESSION", inputs)
    common = {"schema_version": 1, "mission_id": dispatch["mission_id"], "wop_id": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("wop_id"),
              "submission_id": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("submission_id"), "admission_id": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("admission_id"),
              "bootstrap_id": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("bootstrap_id"), "operation": "BETA",
              "authority_framework": "OPERATION_BETA", "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED", "dispatch_id": dispatch["dispatch_id"],
              "provider_selection_id": provider["provider_selection_id"], "provider_id": dispatch["provider_id"], "provider_type": dispatch.get("provider_type"),
              "current_published_baseline": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("current_published_baseline"),
              "mission_provenance_baseline": load_json(Path(dispatch["artifacts"]["dispatch_transaction"]["path"])).get("mission_provenance_baseline"),
              "dispatch_artifacts": inputs["dispatch_artifacts"], "provider_selection_artifacts": inputs["provider_selection_artifacts"],
              "session_contract": {"id": SESSION_CONTRACT, "version": SESSION_VERSION}, "provider_session_id": session_id,
              "provider_session_created": True, "provider_invoked": False, "invocation_started": False, "execution_started": False}
    refs = {key: {"path": str((runtime / STAGE_DIRS[key] / f"{session_id}.json").resolve())} for key in STAGE_DIRS if key != "provider_session"}
    values = {
        "provider_session": dict(common, artifact_type=ARTIFACT_TYPES["provider_session"], session_state="READY_FOR_PROVIDER_INVOCATION", provider_session_authorized=True, next_authorized_action="INVOKE_PROVIDER", artifacts=refs),
        "provider_session_receipt": dict(common, artifact_type=ARTIFACT_TYPES["provider_session_receipt"], receipt_type="provider-session", result="PASS", replay="IDEMPOTENT"),
        "provider_session_journal": dict(common, artifact_type=ARTIFACT_TYPES["provider_session_journal"], states=["PROVIDER_SESSION_EVALUATING", "PROVIDER_SESSION_AUTHORIZED", "PROVIDER_SESSION_CREATED", "READY_FOR_PROVIDER_INVOCATION"], provisioned=[]),
        "provider_session_authorization": dict(common, artifact_type=ARTIFACT_TYPES["provider_session_authorization"], authorization_result="PASS", provider_session_authorized=True, invocation_authorized=False, execution_authorized=False),
        "provider_session_readiness": dict(common, artifact_type=ARTIFACT_TYPES["provider_session_readiness"], readiness_state="READY_FOR_PROVIDER_INVOCATION", next_action="INVOKE_PROVIDER", provider_invoked=False, execution_started=False),
    }
    for key, value in values.items():
        value["artifact_digest"] = digest(value)
    values["provider_session_journal"]["provisioned"] = [values[key]["artifact_digest"] for key in values if key != "provider_session_journal"]
    values["provider_session_journal"]["artifact_digest"] = digest({k: v for k, v in values["provider_session_journal"].items() if k != "artifact_digest"})
    values["provider_session"]["artifacts"] = {key: refs[key] | {"digest": values[key]["artifact_digest"]} for key in refs}
    values["provider_session"]["artifact_digest"] = digest({k: v for k, v in values["provider_session"].items() if k != "artifact_digest"})
    return values


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id, runtime = Path(repository).resolve(), str(mission_id).upper(), _runtime(Path(repository).resolve(), runtime_root)
    try:
        dispatch, provider = _validate_inputs(root, mission_id, runtime)
        existing = _verify_set(runtime, _found(runtime, mission_id))
        if existing:
            if existing["dispatch_artifacts"] != _dispatch_snapshot(runtime, dispatch) or existing["provider_selection_artifacts"] != _provider_snapshot(provider):
                raise ProviderSessionError("PROVIDER_SESSION_STALE", "dispatch or provider selection changed after session creation")
            return {**existing, "mission_id": mission_id, "read_only": True, "blockers": [], "next_authorized_action": "INVOKE_PROVIDER"}
        return {"result": "PASS", "mission_id": mission_id, "dispatch_id": dispatch["dispatch_id"], "provider_id": provider["provider_id"], "provider_session_created": False, "provider_invoked": False, "execution_started": False, "read_only": True, "blockers": [], "next_authorized_action": "MATERIALIZE_PROVIDER_SESSION"}
    except ProviderSessionError as error:
        return {"result": "FAIL", "mission_id": mission_id, "provider_session_created": False, "provider_invoked": False, "execution_started": False, "read_only": True, "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def create(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id, runtime = Path(repository).resolve(), str(mission_id).upper(), _runtime(Path(repository).resolve(), runtime_root)
    preview = verify(root, mission_id, runtime_root=runtime)
    if preview.get("result") != "PASS":
        return preview
    dispatch, provider = _validate_inputs(root, mission_id, runtime)
    found = _found(runtime, mission_id)
    existing = _verify_set(runtime, found)
    if existing:
        return {**existing, "mission_id": mission_id, "read_only": False, "duplicate_session": "IDEMPOTENT", "next_authorized_action": "INVOKE_PROVIDER"}
    if any(found.values()):
        raise ProviderSessionError("CONFLICTING_PROVIDER_SESSION", "partial provider-session state exists")
    values = _expected(runtime, dispatch, provider)
    for key, value in values.items():
        atomic_write(runtime / STAGE_DIRS[key] / f"{value['provider_session_id']}.json", value)
    result = _verify_set(runtime, _found(runtime, mission_id))
    if not result:
        raise ProviderSessionError("PARTIAL_PROVIDER_SESSION", "provider-session artifact set is incomplete")
    return {**result, "mission_id": mission_id, "read_only": False, "duplicate_session": "NO", "next_authorized_action": "INVOKE_PROVIDER"}


def render(value: Mapping[str, Any]) -> str:
    blockers = value.get("blockers", [])
    return "\n".join(("Zeus Provider Session", "---------------------", f"Result                    : {value.get('result')}", f"Provider Session          : {'PASS' if value.get('result') == 'PASS' else 'FAIL'}", f"Session created           : {'YES' if value.get('provider_session_created') else 'NO'}", f"Session ID                : {value.get('provider_session_id', 'NONE')}", f"Dispatch unchanged        : {'PASS' if value.get('dispatch_artifacts') else 'FAIL'}", f"Provider unchanged        : {'PASS' if value.get('provider_selection_artifacts') else 'FAIL'}", f"Execution not started     : {'YES' if not value.get('execution_started') else 'NO'}", f"Invocation not started    : {'YES' if not value.get('provider_invoked') else 'NO'}", f"Replay                   : {value.get('replay', value.get('duplicate_session', 'NOT_RUN'))}", f"Artifact integrity PASS   : {'YES' if value.get('result') == 'PASS' else 'NO'}", f"Artifact cardinality PASS : {'YES' if len(value.get('artifacts', {})) == 5 else 'NO'}", f"Authority PASS            : {'YES' if value.get('result') == 'PASS' else 'NO'}", f"Repository PASS           : {'YES' if value.get('result') == 'PASS' else 'NO'}", f"Runtime PASS              : {'YES' if value.get('result') == 'PASS' else 'NO'}", f"Platform PASS             : {'YES' if value.get('result') == 'PASS' else 'NO'}", "Read-only YES" if value.get("read_only") else "Read-only NO (session materialized)", f"Blockers                 : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}", f"Next action              : {value.get('next_authorized_action')}"))
