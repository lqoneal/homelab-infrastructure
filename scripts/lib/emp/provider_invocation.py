"""P5-G4 bounded provider-invocation foundation.

This controller owns the invocation transaction up to provider acknowledgement.
The production ``engctl codex`` launcher is deliberately not called here: the
current gate uses a qualification adapter that exercises the canonical package
and returns a deterministic provider-bound acknowledgement without creating a
process, execution state, or mission work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.provider_session import verify as verify_provider_session
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.eos import operational_beta


INVOCATION_CONTRACT = "ZEUS-P5-G4-PROVIDER-INVOCATION-FOUNDATION"
INVOCATION_VERSION = "1"
INVOCATION_MODE = "QUALIFICATION_ADAPTER"
ADAPTER_ID = "zeus-bounded-artifact-handler-v1"
STAGE_DIRS = {
    "provider_invocation_transaction": "provider-invocations",
    "provider_invocation_authorization": "provider-invocation-authorizations",
    "provider_invocation_package": "provider-invocation-packages",
    "provider_invocation_acknowledgement": "provider-invocation-acknowledgements",
    "provider_invocation_receipt": "provider-invocation-receipts",
    "provider_invocation_journal": "provider-invocation-journals",
    "execution_start_readiness": "execution-start-readiness",
}
ARTIFACT_TYPES = {key: key.replace("_", "-") for key in STAGE_DIRS}


class ProviderInvocationError(ValueError):
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
        raise ProviderInvocationError("INVOCATION_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ProviderInvocationError("INVOCATION_ARTIFACT_INVALID", f"{path} is not an object")
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
        raise ProviderInvocationError("INVOCATION_PATH_INVALID", f"{key} path is missing")
    path = Path(raw).resolve()
    try:
        path.relative_to(runtime)
    except ValueError as error:
        raise ProviderInvocationError("INVOCATION_PATH_ESCAPE", f"{key} path escapes authoritative runtime") from error
    if path.parent.name != STAGE_DIRS[key] or not path.is_file():
        raise ProviderInvocationError("INVOCATION_PATH_INVALID", f"{key} path is not canonical")
    return path


def _verify_set(runtime: Path, found: dict[str, list[tuple[Path, dict[str, Any]]]]) -> dict[str, Any] | None:
    if not any(found.values()):
        return None
    if any(len(items) != 1 for items in found.values()):
        raise ProviderInvocationError("INVOCATION_CARDINALITY_CONFLICT", "invocation artifact cardinality is not exactly one per class")
    values = {key: items[0][1] for key, items in found.items()}
    anchor = values["provider_invocation_transaction"]
    invocation_id = anchor.get("provider_invocation_id")
    if not invocation_id or anchor.get("provider_invocation_state") != "READY_FOR_EXECUTION_START":
        raise ProviderInvocationError("INVOCATION_STATE_INVALID", "invocation is not execution-start-ready")
    for key, value in values.items():
        if value.get("artifact_type") != ARTIFACT_TYPES[key]:
            raise ProviderInvocationError("INVOCATION_ARTIFACT_MISMATCH", f"{key} artifact type mismatch")
        if value.get("artifact_digest") != digest({k: v for k, v in value.items() if k != "artifact_digest"}):
            raise ProviderInvocationError("INVOCATION_DIGEST_MISMATCH", f"{key} digest mismatch")
        if value.get("provider_invocation_id") != invocation_id:
            raise ProviderInvocationError("INVOCATION_IDENTITY_MISMATCH", f"{key} invocation identity mismatch")
        if value.get("mission_id") != anchor.get("mission_id"):
            raise ProviderInvocationError("INVOCATION_CROSS_MISSION", f"{key} mission identity mismatch")
        for field in ("provider_session_id", "provider_id", "dispatch_id", "execution_authority_digest", "execution_package_digest", "repository_identity", "current_published_baseline", "mission_provenance_baseline"):
            if value.get(field) != anchor.get(field):
                raise ProviderInvocationError("INVOCATION_BINDING_MISMATCH", f"{key} {field} binding mismatch")
        if found[key][0][0].name != f"{invocation_id}.json" or found[key][0][0].parent.name != STAGE_DIRS[key]:
            raise ProviderInvocationError("INVOCATION_PATH_INVALID", f"{key} path is not canonical")
    for key, descriptor in (anchor.get("artifacts") or {}).items():
        if key not in values or descriptor.get("digest") != values[key].get("artifact_digest"):
            raise ProviderInvocationError("INVOCATION_ARTIFACT_MISMATCH", f"{key} descriptor digest mismatch")
        if _path(runtime, key, descriptor) != found[key][0][0].resolve():
            raise ProviderInvocationError("INVOCATION_PATH_INVALID", f"{key} descriptor path mismatch")
    required = {
        "provider_invocation_authorized": True,
        "provider_invoked": True,
        "provider_acknowledged": True,
        "execution_start_eligible": True,
        "execution_started": False,
        "mission_work_started": False,
    }
    if any(anchor.get(key) != expected for key, expected in required.items()):
        raise ProviderInvocationError("INVOCATION_BOUNDARY_FAILURE", "invocation crosses the execution boundary")
    if anchor.get("invocation_mode") not in {"REAL", INVOCATION_MODE}:
        raise ProviderInvocationError("INVOCATION_MODE_INVALID", "invocation mode is unsupported")
    if values["provider_invocation_acknowledgement"].get("acknowledged") is not True:
        raise ProviderInvocationError("ACKNOWLEDGEMENT_MISSING", "provider acknowledgement is absent")
    return {
        "result": "PASS", "replay": "IDEMPOTENT", "invocation_replay": "IDEMPOTENT",
        "mission_id": anchor["mission_id"], "provider_invocation_id": invocation_id,
        "provider_session_id": anchor["provider_session_id"], "provider_id": anchor["provider_id"],
        "dispatch_id": anchor["dispatch_id"], "provider_invocation_state": anchor["provider_invocation_state"],
        "provider_invocation_result": "PASS", "provider_invocation_authorized": True,
        "provider_invocation_created": True,
        "provider_invoked": True, "provider_acknowledged": True,
        "execution_start_eligible": True, "execution_started": False, "mission_work_started": False,
        "invocation_mode": anchor["invocation_mode"],
        "artifacts": {key: {"path": str(items[0][0]), "digest": items[0][1]["artifact_digest"]} for key, items in found.items()},
        "next_authorized_action": "START_EXECUTION", "read_only": True, "blockers": [],
    }


def _published_baseline(root: Path, runtime: Path) -> dict[str, Any]:
    try:
        return resolve_baseline(root, Path("/data/engineering"), runtime_identity=_load(runtime / "runtime-identity.json"))
    except Exception as error:
        raise ProviderInvocationError("BASELINE_RESOLUTION_FAILURE", str(error)) from error


def _baseline_for_invocation(root: Path, runtime: Path, provenance_baseline: str) -> dict[str, Any]:
    try:
        return resolve_baseline(
            root, Path("/data/engineering"),
            mission_provenance_baseline=provenance_baseline,
            runtime_identity=_load(runtime / "runtime-identity.json"),
        )
    except Exception as error:
        raise ProviderInvocationError("BASELINE_RESOLUTION_FAILURE", str(error)) from error


def _resolve_package(root: Path, mission_id: str, runtime: Path, *, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    authority = operational_beta.authority(root, include_current_execution=False)
    if not (authority.get("result") == "PASS" and authority.get("authority_framework") == "OPERATION_BETA" and authority.get("authority_integrity") == "PASS" and authority.get("authority_resolution") == "PASS" and authority.get("oa_authority") == "SUPERSEDED"):
        raise ProviderInvocationError("AUTHORITY_FAILURE", "published Operation Beta authority chain failed")
    session = verify_provider_session(root, mission_id, runtime_root=runtime)
    if session.get("result") != "PASS" or session.get("session_state") != "READY_FOR_PROVIDER_INVOCATION":
        raise ProviderInvocationError("PROVIDER_SESSION_NOT_READY", "authoritative provider session is not invocation-ready")
    selection = session.get("provider_selection_artifacts", {})
    dispatch_refs = session.get("dispatch_artifacts", {})
    if not session.get("provider_session_id") or not session.get("provider_id") or not session.get("dispatch_id"):
        raise ProviderInvocationError("PROVIDER_SESSION_BINDING_MISSING", "provider session chain is incomplete")
    # Existing invocation provenance is immutable.  It is resolved against
    # the current publication by the shared resolver, so a later publication
    # is accepted when it is IDENTICAL or an ANCESTOR relationship.  New
    # invocations bind to the current published baseline.
    provenance_baseline = (existing or {}).get("current_published_baseline")
    if not provenance_baseline:
        current = _published_baseline(root, runtime)
        provenance_baseline = current.get("published_head")
    baseline = _baseline_for_invocation(root, runtime, provenance_baseline)
    if baseline.get("result") != "PASS":
        raise ProviderInvocationError("INVOCATION_PROVENANCE_INVALID", "invocation provenance baseline is invalid against the current publication")
    # The mission verifier is intentionally called with invocation integration
    # disabled to avoid a circular resolver; it still verifies every prior stage.
    from scripts.lib.emp.mission_verification_controller import verify as verify_mission
    mission = verify_mission(root, mission_id, runtime_root=runtime, include_provider_invocation=False)
    if mission.get("result") != "PASS":
        raise ProviderInvocationError("MISSION_VERIFICATION_FAILURE", "earlier mission stages failed verification")
    provider_id = session["provider_id"]
    provider = (mission.get("provider_selection") or {}).get("candidate_evaluation", [{}])[0].get("inventory_record", {})
    if not provider or provider.get("agent_id") != provider_id or provider.get("qualification_status") != "QUALIFIED":
        raise ProviderInvocationError("UNSUPPORTED_PROVIDER_ADAPTER", "selected provider has no qualified bounded adapter")
    if "bounded-artifact-handler" not in provider.get("supported_tools", []):
        raise ProviderInvocationError("UNSUPPORTED_PROVIDER_ADAPTER", "selected provider lacks bounded-artifact-handler")
    refs = mission.get("artifacts", {})
    required_refs = ("mission_contract", "execution_authority", "execution_package", "execution_record")
    if any(name not in refs for name in required_refs):
        raise ProviderInvocationError("INVOCATION_PACKAGE_INCOMPLETE", "canonical execution references are incomplete")
    mission_provenance = (existing or {}).get("mission_provenance_baseline")
    if existing is None:
        mission_provenance = (mission.get("repository") or {}).get("mission_provenance_baseline")
    package_inputs = {
        "mission_id": mission_id, "wop_id": mission.get("wop_id"), "submission_id": mission.get("submission_id"),
        "admission_id": mission.get("admission_id"), "bootstrap_id": mission.get("bootstrap_id"),
        "provider_selection_id": mission.get("provider_selection_id"), "dispatch_id": session["dispatch_id"],
        "provider_session_id": session["provider_session_id"], "provider_id": provider_id,
        "invocation_contract": [INVOCATION_CONTRACT, INVOCATION_VERSION],
        "execution_package_digest": refs["execution_package"]["digest"],
        "execution_authority_digest": refs["execution_authority"]["digest"],
        "repository_identity": baseline["identity"]["repository_identity"],
        "current_published_baseline": provenance_baseline,
        "mission_provenance_baseline": mission_provenance,
    }
    invocation_id = identifier("PROVIDER-INVOCATION", package_inputs)
    return {
        "mission": mission, "session": session, "provider": provider, "authority": authority,
        "baseline": baseline, "refs": refs, "dispatch_refs": dispatch_refs, "selection_refs": selection,
        "package_inputs": package_inputs, "provider_invocation_id": invocation_id,
        "invocation_provenance_baseline": provenance_baseline,
        "current_published_baseline": baseline["published_head"],
        "baseline_relationship": baseline.get("baseline_relationship", baseline.get("mission_baseline_relationship")),
    }


def _expected(root: Path, runtime: Path, resolved: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    inputs = resolved["package_inputs"]
    invocation_id = resolved["provider_invocation_id"]
    common = {
        "schema_version": 1, "mission_id": inputs["mission_id"], "wop_id": inputs["wop_id"],
        "submission_id": inputs["submission_id"], "admission_id": inputs["admission_id"], "bootstrap_id": inputs["bootstrap_id"],
        "provider_selection_id": inputs["provider_selection_id"], "dispatch_id": inputs["dispatch_id"],
        "provider_session_id": inputs["provider_session_id"], "provider_id": inputs["provider_id"],
        "authority_framework": "OPERATION_BETA", "authority_source": "published Operation Beta authority chain",
        "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED", "operation": "BETA",
        "repository_identity": inputs["repository_identity"], "current_published_baseline": inputs["current_published_baseline"],
        "mission_provenance_baseline": inputs["mission_provenance_baseline"], "invocation_mode": INVOCATION_MODE,
        "provider_invocation_id": invocation_id, "provider_invoked": True, "provider_acknowledged": True,
        "execution_start_eligible": True, "execution_started": False, "mission_work_started": False,
        "invocation_contract": {"id": INVOCATION_CONTRACT, "version": INVOCATION_VERSION},
    }
    refs = {key: {"path": str((runtime / STAGE_DIRS[key] / f"{invocation_id}.json").resolve())} for key in STAGE_DIRS if key != "provider_invocation_transaction"}
    package = dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_package"], package_state="PROVIDER_INVOCATION_ACCEPTED", package_inputs=dict(inputs), canonical_references=resolved["refs"], dispatch_artifacts=resolved["dispatch_refs"], provider_selection_artifacts=resolved["selection_refs"], provider_session_artifacts=resolved["session"].get("artifacts", {}), prohibited_actions=["START_EXECUTION", "MISSION_WORK", "REPOSITORY_MUTATION"], stop_condition="STOP_BEFORE_EXECUTION_START")
    values: dict[str, dict[str, Any]] = {
        "provider_invocation_package": package,
        "provider_invocation_authorization": dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_authorization"], authorization_result="PASS", provider_invocation_authorized=True, execution_authorized=False, next_authorized_action="START_EXECUTION"),
        "provider_invocation_acknowledgement": dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_acknowledgement"], acknowledged=True, adapter_id=ADAPTER_ID, provider_bound_context_digest=digest({"provider_id": inputs["provider_id"], "provider_session_id": inputs["provider_session_id"], "package_inputs": inputs}), acknowledgement_result="PASS"),
        "provider_invocation_receipt": dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_receipt"], receipt_type="provider-invocation", result="PASS", replay="IDEMPOTENT"),
        "provider_invocation_journal": dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_journal"], states=["PROVIDER_INVOCATION_EVALUATING", "PROVIDER_INVOCATION_AUTHORIZED", "PROVIDER_INVOCATION_ACCEPTED", "READY_FOR_EXECUTION_START"], provider_contacted=True, provider_acknowledged=True, execution_started=False),
        "execution_start_readiness": dict(common, artifact_type=ARTIFACT_TYPES["execution_start_readiness"], readiness_state="READY_FOR_EXECUTION_START", execution_start_eligible=True, next_action="START_EXECUTION"),
    }
    for key, value in values.items():
        value["artifact_digest"] = digest(value)
    transaction = dict(common, artifact_type=ARTIFACT_TYPES["provider_invocation_transaction"], provider_invocation_state="READY_FOR_EXECUTION_START", provider_invocation_result="PASS", provider_invocation_authorized=True, artifacts=refs)
    values["provider_invocation_transaction"] = transaction
    values["provider_invocation_transaction"]["artifacts"] = {key: refs[key] | {"digest": values[key]["artifact_digest"]} for key in refs}
    values["provider_invocation_transaction"]["artifact_digest"] = digest({k: v for k, v in values["provider_invocation_transaction"].items() if k != "artifact_digest"})
    return values


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id, runtime = Path(repository).resolve(), str(mission_id).upper(), _runtime(Path(repository).resolve(), runtime_root)
    try:
        found = _found(runtime, mission_id)
        existing = _verify_set(runtime, found)
        anchor = _load(existing["artifacts"]["provider_invocation_transaction"]["path"]) if existing else None
        resolved = _resolve_package(root, mission_id, runtime, existing=anchor)
        if existing:
            if existing.get("provider_invocation_id") != resolved["provider_invocation_id"]:
                raise ProviderInvocationError("INVOCATION_INPUT_MISMATCH", "invocation-critical input differs from immutable invocation binding")
            existing.update({
                "invocation_provenance_baseline": resolved["invocation_provenance_baseline"],
                "current_published_baseline": resolved["current_published_baseline"],
                "baseline_relationship": resolved["baseline_relationship"],
                "invocation_integrity": "PASS",
            })
            return existing
        return {"result": "PASS", "mission_id": mission_id, "provider_session_id": resolved["session"]["provider_session_id"], "provider_id": resolved["session"]["provider_id"], "provider_invocation_created": False, "provider_invoked": False, "execution_started": False, "mission_work_started": False, "read_only": True, "blockers": [], "next_authorized_action": "AUTHORIZE_PROVIDER_INVOCATION"}
    except ProviderInvocationError as error:
        return {"result": "FAIL", "mission_id": mission_id, "provider_invocation_created": False, "provider_invoked": False, "execution_started": False, "mission_work_started": False, "read_only": True, "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def create(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id, runtime = Path(repository).resolve(), str(mission_id).upper(), _runtime(Path(repository).resolve(), runtime_root)
    try:
        found = _found(runtime, mission_id)
        existing = _verify_set(runtime, found)
        anchor = _load(existing["artifacts"]["provider_invocation_transaction"]["path"]) if existing else None
        resolved = _resolve_package(root, mission_id, runtime, existing=anchor)
        if existing:
            if existing.get("provider_invocation_id") != resolved["provider_invocation_id"]:
                raise ProviderInvocationError("INVOCATION_INPUT_MISMATCH", "invocation-critical input differs from immutable invocation binding")
            return {**existing, "read_only": False, "duplicate_provider_invocation": "IDEMPOTENT"}
        if any(found.values()):
            raise ProviderInvocationError("INVOCATION_PARTIAL_STATE", "partial invocation state exists")
        values = _expected(root, runtime, resolved)
        for key, value in values.items():
            atomic_write(runtime / STAGE_DIRS[key] / f"{resolved['provider_invocation_id']}.json", value)
        result = _verify_set(runtime, _found(runtime, mission_id))
        if not result:
            raise ProviderInvocationError("INVOCATION_PARTIAL_STATE", "invocation artifact chain is incomplete")
        return {**result, "read_only": False, "duplicate_provider_invocation": "NO"}
    except ProviderInvocationError as error:
        return {"result": "FAIL", "mission_id": mission_id, "provider_invocation_created": False, "provider_invoked": False, "execution_started": False, "mission_work_started": False, "read_only": False, "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def render(value: Mapping[str, Any]) -> str:
    blockers = value.get("blockers", [])
    return "\n".join(("Zeus Provider Invocation", "------------------------", f"Result                    : {value.get('result')}", f"Invocation                : {'PASS' if value.get('result') == 'PASS' else 'FAIL'}", f"Invocation ID             : {value.get('provider_invocation_id', 'NONE')}", f"Provider                  : {value.get('provider_id', 'NONE')}", f"Provider session          : {value.get('provider_session_id', 'NONE')}", f"Invocation mode           : {value.get('invocation_mode', 'NOT_STARTED')}", f"Provider invoked          : {'YES' if value.get('provider_invoked') else 'NO'}", f"Provider acknowledged     : {'YES' if value.get('provider_acknowledged') else 'NO'}", f"Execution started         : {'YES' if value.get('execution_started') else 'NO'}", f"Mission work started      : {'YES' if value.get('mission_work_started') else 'NO'}", f"Replay                   : {value.get('invocation_replay', value.get('replay', 'NOT_RUN'))}", f"Artifact integrity        : {'PASS' if value.get('result') == 'PASS' else 'FAIL'}", f"Blockers                  : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}", f"Next action               : {value.get('next_authorized_action')}", "Read-only                 : YES" if value.get('read_only') else "Read-only                 : NO (invocation materialized)"))
