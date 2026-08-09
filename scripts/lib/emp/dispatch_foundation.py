"""P5-G2 canonical provider-dispatch foundation.

The controller creates a provider-bound, non-live dispatch package.  It stops
at provider-session readiness: no provider adapter, process, session, or
execution API is called from this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_verification_controller import verify as verify_mission
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.provider_selection import _mission_artifacts, _verify_set, verify as verify_provider
from scripts.lib.emp.runtime_paths import resolve_runtime


DISPATCH_CONTRACT = "ZEUS-P5-G2-DISPATCH-FOUNDATION"
DISPATCH_VERSION = "1"
STAGE_DIRS = {
    "dispatch_transaction": "dispatches",
    "dispatch_package": "dispatch-packages",
    "dispatch_authorization": "dispatch-authorizations",
    "dispatch_receipt": "dispatch-receipts",
    "dispatch_journal": "dispatch-journals",
    "provider_session_readiness": "provider-session-readiness",
}
ARTIFACT_TYPES = {
    "dispatch_transaction": "dispatch-transaction",
    "dispatch_package": "dispatch-package",
    "dispatch_authorization": "dispatch-authorization",
    "dispatch_receipt": "dispatch-receipt",
    "dispatch_journal": "dispatch-journal",
    "provider_session_readiness": "provider-session-readiness",
}


class DispatchFoundationError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code = code
        self.message = message
        self.next_action = next_action
        super().__init__(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception as error:
        raise DispatchFoundationError("DISPATCH_ARTIFACT_INVALID", f"{path}: {error}") from error
    return value


def _found(runtime: Path, mission_id: str) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    result = {key: [] for key in STAGE_DIRS}
    for key, directory in STAGE_DIRS.items():
        path = runtime / directory
        if not path.is_dir():
            continue
        for item in sorted(path.glob("*.json")):
            value = _load(item)
            if value.get("mission_id") == mission_id:
                result[key].append((item, value))
    return result


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root:
        return Path(runtime_root).resolve()
    return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()


def _path(runtime: Path, descriptor: Mapping[str, Any], key: str) -> Path:
    raw = descriptor.get("path")
    if not isinstance(raw, str):
        raise DispatchFoundationError("DISPATCH_PATH_INVALID", f"{key} path is missing")
    value = Path(raw).resolve()
    try:
        value.relative_to(runtime)
    except ValueError as error:
        raise DispatchFoundationError("DISPATCH_PATH_ESCAPE", f"{key} path escapes authoritative runtime") from error
    if value.parent.name != STAGE_DIRS[key] or not value.is_file():
        raise DispatchFoundationError("DISPATCH_PATH_INVALID", f"{key} path is not canonical")
    return value


def _verify_set(runtime: Path, found: dict[str, list[tuple[Path, dict[str, Any]]]]) -> dict[str, Any] | None:
    if not any(found.values()):
        return None
    if any(len(values) != 1 for values in found.values()):
        raise DispatchFoundationError("DISPATCH_CARDINALITY_CONFLICT", "dispatch artifact cardinality is not exactly one per class")
    values = {key: items[0][1] for key, items in found.items()}
    anchor = values["dispatch_transaction"]
    dispatch_id = anchor.get("dispatch_id")
    if not dispatch_id or anchor.get("dispatch_state") != "READY_FOR_PROVIDER_SESSION":
        raise DispatchFoundationError("DISPATCH_STATE_INVALID", "dispatch transaction is not provider-session-ready")
    for key, value in values.items():
        if value.get("artifact_type") != ARTIFACT_TYPES[key]:
            raise DispatchFoundationError("DISPATCH_ARTIFACT_MISMATCH", f"{key} artifact type mismatch")
        supplied = value.get("artifact_digest")
        if supplied != digest({k: v for k, v in value.items() if k != "artifact_digest"}):
            raise DispatchFoundationError("DISPATCH_DIGEST_MISMATCH", f"{key} digest mismatch")
        if found[key][0][0].name != f"{dispatch_id}.json":
            raise DispatchFoundationError("DISPATCH_PATH_INVALID", f"{key} canonical filename mismatch")
        if value.get("dispatch_id") != dispatch_id:
            raise DispatchFoundationError("DISPATCH_IDENTITY_MISMATCH", f"{key} dispatch identity mismatch")
    for key, descriptor in (anchor.get("artifacts") or {}).items():
        if key not in values or descriptor.get("digest") != values[key].get("artifact_digest"):
            raise DispatchFoundationError("DISPATCH_ARTIFACT_MISMATCH", f"{key} descriptor digest mismatch")
        if _path(runtime, descriptor, key) != found[key][0][0].resolve():
            raise DispatchFoundationError("DISPATCH_PATH_INVALID", f"{key} descriptor path mismatch")
    identity_fields = ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "provider_selection_id", "provider_id", "execution_record_digest", "execution_authority_digest", "execution_package_digest", "current_published_baseline", "mission_provenance_baseline")
    for key, value in values.items():
        if any(value.get(field) != anchor.get(field) for field in identity_fields):
            raise DispatchFoundationError("DISPATCH_IDENTITY_MISMATCH", f"{key} identity chain mismatch")
    if any(anchor.get(field) for field in ("provider_session_created", "provider_invoked", "execution_started")):
        raise DispatchFoundationError("DISPATCH_BOUNDARY_FAILURE", "dispatch artifact crosses provider-session boundary")
    if anchor.get("dispatch_authorized") is not True or anchor.get("provider_session_eligible") is not True:
        raise DispatchFoundationError("DISPATCH_AUTHORIZATION_INVALID", "dispatch is not authorized and provider-session-ready")
    return {
        "result": "PASS", "replay": "IDEMPOTENT", "mission_id": anchor.get("mission_id"),
        "wop_id": anchor.get("wop_id"), "submission_id": anchor.get("submission_id"),
        "admission_id": anchor.get("admission_id"), "bootstrap_id": anchor.get("bootstrap_id"),
        "dispatch_id": dispatch_id,
        "dispatch_state": anchor["dispatch_state"], "dispatch_result": anchor.get("dispatch_result"),
        "dispatch_authorized": True, "provider_id": anchor["provider_id"],
        "provider_session_eligible": True, "provider_session_created": False,
        "provider_invoked": False, "execution_started": False,
        "artifacts": {key: {"path": str(items[0][0]), "digest": items[0][1]["artifact_digest"]} for key, items in found.items()},
        "next_authorized_action": "ESTABLISH_PROVIDER_SESSION",
    }


def _canonical_inputs(base: Mapping[str, Any], selection: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = base.get("artifacts", {})
    selected_provider = load_json(Path(selection["artifacts"]["selected_provider"]["path"]))
    return {
        "mission_id": base["mission_id"], "wop_id": base["wop_id"], "submission_id": base["submission_id"],
        "admission_id": base["admission_id"], "bootstrap_id": base["bootstrap_id"],
        "provider_selection_id": selection["provider_selection_id"], "provider_id": selection["provider_id"],
        "provider_type": selected_provider.get("provider_type"),
        "execution_record_digest": artifacts["execution_record"]["digest"],
        "execution_authority_digest": artifacts["execution_authority"]["digest"],
        "execution_package_digest": artifacts["execution_package"]["digest"],
        "mission_contract_digest": artifacts["mission_contract"]["digest"],
        "current_published_baseline": base["repository"]["published_baseline"],
        "mission_provenance_baseline": base["repository"]["mission_provenance_baseline"],
        "repository_identity": base["repository"].get("repository_identity") or base["repository"].get("canonical_repository_identity"),
        "dispatch_contract": [DISPATCH_CONTRACT, DISPATCH_VERSION],
    }


def _expected(runtime: Path, base: Mapping[str, Any], selection: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    inputs = _canonical_inputs(base, selection)
    dispatch_id = identifier("DISPATCH", inputs)
    common = {
        "schema_version": 1, "mission_id": base["mission_id"], "wop_id": base["wop_id"],
        "submission_id": base["submission_id"], "admission_id": base["admission_id"], "bootstrap_id": base["bootstrap_id"],
        "operation": "BETA", "authority_framework": "OPERATION_BETA", "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED",
        "provider_selection_id": selection["provider_selection_id"], "provider_id": selection["provider_id"],
        "provider_type": inputs.get("provider_type"), "dispatch_id": dispatch_id,
        "execution_record_digest": inputs["execution_record_digest"], "execution_authority_digest": inputs["execution_authority_digest"],
        "execution_package_digest": inputs["execution_package_digest"], "mission_contract_digest": inputs["mission_contract_digest"],
        "repository_identity": inputs["repository_identity"], "repository_path": str(Path(base["repository"].get("repository_path", "")).resolve()),
        "current_published_baseline": inputs["current_published_baseline"], "mission_provenance_baseline": inputs["mission_provenance_baseline"],
        "mission_baseline_relationship": base["repository"].get("mission_baseline_relationship"),
        "selection_policy": selection.get("selection_policy"), "dispatch_contract": {"id": DISPATCH_CONTRACT, "version": DISPATCH_VERSION},
        "provider_session_created": False, "provider_invoked": False, "execution_started": False,
    }
    refs = {key: {"path": str((runtime / STAGE_DIRS[key] / f"{dispatch_id}.json").resolve())} for key in STAGE_DIRS if key != "dispatch_transaction"}
    package = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_package"], package_state="READY_FOR_PROVIDER_SESSION",
                   references=base.get("artifacts", {}), restrictions={"provider_invocation": "PROHIBITED", "execution": "PROHIBITED"},
                   next_authorized_action="ESTABLISH_PROVIDER_SESSION")
    authorization = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_authorization"], dispatch_authorized=True,
                         authorization_result="PASS", approval_required=False, approval_status="NOT_REQUIRED",
                         provider_session_eligible=True)
    receipt = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_receipt"], receipt_type="dispatch", result="PASS", duplicate_dispatch="IDEMPOTENT")
    journal = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_journal"], states=["DISPATCH_EVALUATING", "DISPATCH_AUTHORIZED", "DISPATCH_CREATED", "READY_FOR_PROVIDER_SESSION"], provisioned=[])
    readiness = dict(common, artifact_type=ARTIFACT_TYPES["provider_session_readiness"], readiness_state="READY_FOR_PROVIDER_SESSION",
                     provider_session_eligible=True, next_action="ESTABLISH_PROVIDER_SESSION")
    transaction = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_transaction"], transaction_type="dispatch",
                       dispatch_state="READY_FOR_PROVIDER_SESSION", dispatch_result="PASS", dispatch_authorized=True,
                       provider_session_eligible=True, next_action="ESTABLISH_PROVIDER_SESSION", artifacts=refs)
    values = {"dispatch_transaction": transaction, "dispatch_package": package, "dispatch_authorization": authorization,
              "dispatch_receipt": receipt, "dispatch_journal": journal, "provider_session_readiness": readiness}
    for value in values.values():
        value["artifact_digest"] = digest(value)
    journal["provisioned"] = [values[key]["artifact_digest"] for key in values if key != "dispatch_journal"]
    journal["artifact_digest"] = digest({k: v for k, v in journal.items() if k != "artifact_digest"})
    transaction["artifacts"] = {key: {"path": refs[key]["path"], "digest": values[key]["artifact_digest"]} for key in refs}
    transaction["artifact_digest"] = digest({k: v for k, v in transaction.items() if k != "artifact_digest"})
    return values


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id = Path(repository).resolve(), str(mission_id).upper()
    runtime = _runtime(root, runtime_root)
    try:
        base = verify_mission(root, mission_id, runtime_root=runtime)
        if base.get("result") != "PASS":
            raise DispatchFoundationError("MISSION_VERIFICATION_FAILURE", "canonical mission verification is not PASS")
        provider = verify_provider(root, mission_id, runtime_root=runtime)
        if provider.get("result") != "PASS" or not provider.get("dispatch_eligible"):
            raise DispatchFoundationError("PROVIDER_VERIFICATION_FAILURE", "provider selection is not dispatch-eligible")
        found = _found(runtime, mission_id)
        existing = _verify_set(runtime, found)
        if existing:
            return {**existing, "schema_version": 1, "mission_id": mission_id, "read_only": True, "blockers": [], "next_authorized_action": "ESTABLISH_PROVIDER_SESSION"}
        selection = provider
        # Validate immutable source references before provisioning the dispatch.
        for name in ("execution_record", "execution_package", "mission_contract", "execution_authority"):
            path = Path(base["artifacts"][name]["path"]).resolve()
            if not path.is_file() or load_json(path).get("artifact_digest") != base["artifacts"][name]["digest"]:
                raise DispatchFoundationError("DISPATCH_INPUT_MISMATCH", f"{name} is not valid")
        return {"schema_version": 1, "result": "PASS", "read_only": True, "mission_id": mission_id,
                "dispatch_created": False, "dispatch_authorized": False, "provider_session_eligible": False,
                "provider_id": selection.get("provider_id"), "provider_selection_id": selection.get("provider_selection_id"),
                "blockers": [], "next_authorized_action": "MATERIALIZE_DISPATCH"}
    except DispatchFoundationError as error:
        return {"schema_version": 1, "result": "FAIL", "read_only": True, "mission_id": mission_id,
                "dispatch_created": False, "dispatch_authorized": False, "provider_session_eligible": False,
                "blockers": [{"code": error.code, "message": error.message}], "next_authorized_action": error.next_action}


def create(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root, mission_id = Path(repository).resolve(), str(mission_id).upper()
    runtime = _runtime(root, runtime_root)
    preview = verify(root, mission_id, runtime_root=runtime)
    if preview.get("result") != "PASS":
        return preview
    found = _found(runtime, mission_id)
    existing = _verify_set(runtime, found)
    if existing:
        return {**existing, "read_only": False, "duplicate_dispatch": "IDEMPOTENT", "next_authorized_action": "ESTABLISH_PROVIDER_SESSION"}
    base = verify_mission(root, mission_id, runtime_root=runtime)
    selection = verify_provider(root, mission_id, runtime_root=runtime)
    values = _expected(runtime, base, selection)
    if any(found.values()):
        raise DispatchFoundationError("CONFLICTING_DISPATCH", "partial dispatch state exists")
    for key, value in values.items():
        atomic_write(runtime / STAGE_DIRS[key] / f"{value['dispatch_id']}.json", value)
    result = _verify_set(runtime, _found(runtime, mission_id))
    if not result:
        raise DispatchFoundationError("PARTIAL_DISPATCH", "dispatch artifact set is incomplete")
    return {**result, "read_only": False, "duplicate_dispatch": "NO", "next_authorized_action": "ESTABLISH_PROVIDER_SESSION"}


def render(value: Mapping[str, Any]) -> str:
    blockers = value.get("blockers", [])
    return "\n".join((
        "Zeus Provider Dispatch", "-----------------------",
        f"Result                    : {value.get('result')}",
        f"Dispatch state            : {value.get('dispatch_state', 'NOT_MATERIALIZED')}",
        f"Dispatch authorized       : {'YES' if value.get('dispatch_authorized') else 'NO'}",
        f"Dispatch created          : {'YES' if value.get('dispatch_created', value.get('dispatch_state') == 'READY_FOR_PROVIDER_SESSION') else 'NO'}",
        f"Dispatch ID               : {value.get('dispatch_id', 'NONE')}",
        f"Provider ID               : {value.get('provider_id', 'NONE')}",
        f"Provider session eligible : {'YES' if value.get('provider_session_eligible') else 'NO'}",
        f"Provider session created  : {'YES' if value.get('provider_session_created') else 'NO'}",
        f"Provider invoked         : {'YES' if value.get('provider_invoked') else 'NO'}",
        f"Execution started         : {'YES' if value.get('execution_started') else 'NO'}",
        f"Replay                    : {value.get('replay', value.get('duplicate_dispatch', 'NOT_RUN'))}",
        f"Blockers                  : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}",
        f"Next action               : {value.get('next_authorized_action')}",
        "Read-only                : YES" if value.get("read_only") else "Read-only                : NO (dispatch materialized)",
    ))
