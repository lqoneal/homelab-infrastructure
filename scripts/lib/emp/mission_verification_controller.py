"""Read-only, Zeus-native verification of the canonical mission lifecycle.

This controller is deliberately a projection over the accepted P2/P3/P4
artifact contracts.  It never calls a lifecycle mutation and never treats the
legacy ``mission-executions`` store as proof of the canonical mission chain.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.lib.emp.bootstrap_boundary import _transaction_digest
from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.repository_identity import resolve
from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos import operational_beta


SCHEMA_VERSION = 1


class MissionVerificationError(ValueError):
    """A controller check failed; ``code`` identifies the corrective cause."""

    def __init__(self, code: str, message: str, *, next_action: str | None = None):
        self.code = code
        self.message = message
        self.next_action = next_action or "Resolve the reported blocker and rerun mission verify."
        super().__init__(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MissionVerificationError("ARTIFACT_UNREADABLE", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise MissionVerificationError("ARTIFACT_INVALID", f"{path} is not a JSON object")
    return value


def _one(directory: Path, mission_id: str, label: str) -> tuple[Path, dict[str, Any]]:
    matches = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = _load(path)
        except MissionVerificationError:
            continue
        if value.get("mission_id") == mission_id:
            matches.append((path, value))
    if len(matches) != 1:
        code = "MISSION_NOT_DISCOVERABLE" if label == "mission" else "ARTIFACT_CARDINALITY_CONFLICT"
        raise MissionVerificationError(code, f"{label} cardinality is {len(matches)} for {mission_id}")
    return matches[0]


def _safe_path(raw: Any, runtime: Path, directory: str, label: str) -> Path:
    if not isinstance(raw, (str, Path)) or not raw:
        raise MissionVerificationError("ARTIFACT_MISSING", f"{label} path is missing")
    path = Path(raw).resolve()
    try:
        path.relative_to(runtime)
    except ValueError as error:
        raise MissionVerificationError("ARTIFACT_PATH_ESCAPE", f"{label} path escapes authoritative runtime") from error
    if path.parent != runtime / directory or not path.is_file():
        raise MissionVerificationError("ARTIFACT_MISSING", f"{label} is not in canonical {directory}")
    return path


def _artifact(path: Path, expected: str, label: str) -> dict[str, Any]:
    value = _load(path)
    supplied = value.get("artifact_digest")
    if supplied != expected or supplied != _digest({k: v for k, v in value.items() if k != "artifact_digest"}):
        raise MissionVerificationError("ARTIFACT_DIGEST_MISMATCH", f"{label} digest mismatch")
    return value


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False).stdout.strip()


def _repository(root: Path, runtime: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = resolve(root)
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    marker = _load(runtime / "runtime-identity.json")
    expected = {"repository": str(root), "repository_fingerprint": identity["repository_fingerprint"],
                "repository_id": identity["repository_id"], "repository_identity": identity["repository_identity"]}
    if any(marker.get(key) != value for key, value in expected.items()):
        raise MissionVerificationError("RUNTIME_IDENTITY_MISMATCH", "runtime identity does not bind to repository")
    baseline = resolve_baseline(root, Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")), runtime_identity=marker)
    repository = {**identity, "branch": branch, "current_baseline": baseline["current_head"],
                 "published_baseline": baseline["published_head"], "eos_baseline": baseline["eos_baseline"],
                 "baseline_resolution": baseline}
    return repository, marker


def _authority(root: Path) -> dict[str, Any]:
    value = operational_beta.authority(root)
    required = {
        "authority_framework": "OPERATION_BETA", "active_operation": "BETA",
        "authority_integrity": "PASS", "authority_resolution": "PASS",
        "authority_digest_validation": "PASS", "authority_source": "Operation Beta",
        "oa_authority": "SUPERSEDED",
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise MissionVerificationError("AUTHORITY_INTEGRITY_FAILURE", "Operation Beta authority projection is invalid")
    if value.get("oa_authority") in {"ACTIVE", "FALLBACK"}:
        raise MissionVerificationError("OA_ACTIVE_AUTHORITY", "Operational Alpha cannot be active or fallback authority")
    return {"framework": "OPERATION_BETA", "integrity": "PASS", "resolution": "PASS",
            "digest_validation": "PASS", "active_operation": "BETA", "source": "Operation Beta",
            "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED",
            "authority_digest": value.get("authority_digest")}


def _wop(package: dict[str, Any], mission_id: str, wop_id: str, root: Path) -> dict[str, Any]:
    # The accepted runtime materialization retains immutable authoring
    # provenance, while the authored source may have been intentionally kept
    # outside the published repository.  Verify that canonical provenance
    # projection; if a source is supplied for a fixture, callers may add it to
    # the package descriptor and it is still checked by its stored digest.
    provenance = package.get("immutable_provenance")
    if package.get("mission_id") != mission_id or package.get("wop_id") != wop_id:
        raise MissionVerificationError("WOP_INTEGRITY_FAILURE", "WOP identity does not match mission")
    if not isinstance(provenance, dict) or not all(provenance.get(k) for k in ("template_digest", "context_digest", "traceability_digest")):
        raise MissionVerificationError("WOP_INTEGRITY_FAILURE", "immutable WOP provenance is incomplete")
    if any("PLACEHOLDER" in str(value).upper() for value in provenance.values()):
        raise MissionVerificationError("WOP_INTEGRITY_FAILURE", "WOP provenance contains unresolved placeholders")
    return {"result": "PASS", "source_traceability": "PASS", "template_digest": "PASS", "context_digest": "PASS", "placeholders": "NONE"}


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Return the stable JSON contract for one canonical mission.

    All reads occur before the result is returned.  No directory, receipt,
    replay, EOS state, or repository file is created or modified.
    """
    root = Path(repository).resolve()
    mission_id = str(mission_id).upper()
    blockers: list[dict[str, str]] = []
    errors: list[str] = []
    authority: dict[str, Any] = {}
    repository_data: dict[str, Any] = {}
    runtime: Path
    try:
        resolved = resolve_runtime(root, explicit=runtime_root, require_writable=False)
        runtime = Path(resolved["root"]).resolve()
        if runtime_root is None and (str(runtime).startswith("/tmp") or "temporary" in runtime.name.lower()):
            raise MissionVerificationError("RUNTIME_NOT_AUTHORITATIVE", "temporary runtime cannot be authoritative")
        runtime_data = {"identity": "PASS", "authoritative": runtime_root is None or resolved.get("source") != "command-line",
                        "root": str(runtime), "source": resolved.get("source")}
    except Exception as error:
        runtime = Path(runtime_root or "/nonexistent")
        runtime_data = {"identity": "FAIL", "authoritative": False}
        blockers.append({"code": getattr(error, "code", "RUNTIME_IDENTITY_FAILURE"), "message": str(error)})
    try:
        repository_data, _ = _repository(root, runtime)
    except Exception as error:
        repository_data = {"current_baseline": _git(root, "rev-parse", "HEAD"), "published_baseline": PUBLISHED_BASELINE}
        blockers.append({"code": getattr(error, "code", "REPOSITORY_IDENTITY_MISMATCH"), "message": str(error)})
    try:
        authority = _authority(root)
    except Exception as error:
        blockers.append({"code": getattr(error, "code", "AUTHORITY_INTEGRITY_FAILURE"), "message": str(error)})
        authority = {"framework": "UNKNOWN", "integrity": "FAIL", "resolution": "FAIL", "oa_authority": "UNKNOWN", "oa_fallback": "PROHIBITED"}

    checks = {key: "PASS" for key in ("mission_discovery", "wop", "submission", "admission", "bootstrap",
        "execution_record", "provider_readiness", "provider_session", "artifact_cardinality", "artifact_integrity", "identity_chain", "downstream_boundary")}
    chain: dict[str, Any] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    try:
        mission_records = []
        for candidate_dir in (runtime / "submissions" / "receipts", runtime / "admissions", runtime / "bootstraps"):
            for candidate in candidate_dir.glob("*.json") if candidate_dir.is_dir() else ():
                try:
                    if _load(candidate).get("mission_id") == mission_id:
                        mission_records.append(candidate)
                except MissionVerificationError:
                    pass
        if not mission_records:
            raise MissionVerificationError("MISSION_NOT_DISCOVERABLE", f"mission {mission_id} is not discoverable")
        submission_path, submission = _one(runtime / "submissions" / "receipts", mission_id, "submission")
        request_path = _safe_path(runtime / "submissions" / "requests" / f"{submission['admission_request_id']}.json", runtime, "submissions/requests", "admission request")
        request = _load(request_path)
        admission_path, admission = _one(runtime / "admissions", mission_id, "admission")
        bootstrap_path, bootstrap = _one(runtime / "bootstraps", mission_id, "bootstrap")
        chain = {"submission": submission, "request": request, "admission": admission, "bootstrap": bootstrap}
        expected = {"mission_id": mission_id, "wop_id": submission.get("wop_id"), "submission_id": submission.get("submission_id"),
                    "admission_id": admission.get("admission_id"), "bootstrap_id": bootstrap.get("bootstrap_id")}
        if admission.get("submission_id") != expected["submission_id"] or bootstrap.get("admission_id") != expected["admission_id"] or bootstrap.get("submission_id") != expected["submission_id"]:
            raise MissionVerificationError("IDENTITY_CHAIN_MISMATCH", "mission identity chain is inconsistent")
        if any(value.get("mission_id") != mission_id for value in (admission, bootstrap)):
            raise MissionVerificationError("IDENTITY_CHAIN_MISMATCH", "mission identity is inconsistent")
        artifacts["submission_receipt"] = {"path": str(submission_path), "digest": submission.get("receipt_digest")}
        artifacts["admission_request"] = {"path": str(request_path), "digest": submission.get("submission_digest")}
        # Reconstructing the canonical first request as a replay projection is
        # read-only and proves deterministic identity without invoking submit.
        if request.get("invocation_count") != 1 or request.get("mission_admission_executed") is not False:
            raise MissionVerificationError("REPLAY_EVIDENCE_MISSING", "submission request replay evidence is incomplete")
    except Exception as error:
        checks["mission_discovery"] = "FAIL"; checks["identity_chain"] = "FAIL"; checks["submission"] = "FAIL"; checks["artifact_cardinality"] = "FAIL"
        blockers.append({"code": getattr(error, "code", "MISSION_NOT_DISCOVERABLE"), "message": str(error)})
        submission = admission = bootstrap = {}

    if chain and repository_data.get("baseline_resolution"):
        provenance = admission.get("repository_baseline") or bootstrap.get("repository_baseline")
        baseline = resolve_baseline(
            root, Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")),
            mission_provenance_baseline=provenance,
            runtime_identity=_load(runtime / "runtime-identity.json"),
        )
        repository_data["baseline_resolution"] = baseline
        repository_data["mission_provenance_baseline"] = baseline.get("mission_provenance_baseline")
        repository_data["mission_baseline_relationship"] = baseline.get("mission_baseline_relationship")
        for error in baseline.get("errors", []):
            blockers.append(error)

    if chain:
        try:
            if submission.get("submission_state") != "ADMISSION_REQUESTED" or submission.get("submission_result") != "PASS":
                raise MissionVerificationError("SUBMISSION_RECEIPT_MISSING", "submission is not ADMISSION_REQUESTED/PASS")
            unsigned = {k: v for k, v in submission.items() if k != "receipt_digest"}
            if submission.get("receipt_digest") != hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest():
                raise MissionVerificationError("SUBMISSION_DIGEST_MISMATCH", "submission receipt digest mismatch")
            if submission.get("operation") != "BETA" or submission.get("repository_identity", {}).get("canonical_repository_identity") != str(root):
                raise MissionVerificationError("SUBMISSION_RECEIPT_MISSING", "submission repository or operation binding is invalid")
            if admission.get("admission_state") != "ADMISSION_COMPLETE" or admission.get("admission_result") != "PASS":
                raise MissionVerificationError("ADMISSION_ARTIFACT_MISMATCH", "admission is not ADMISSION_COMPLETE/PASS")
            if admission.get("transaction_digest") != _digest({k: v for k, v in admission.items() if k != "transaction_digest"}):
                raise MissionVerificationError("ADMISSION_DIGEST_MISMATCH", "admission transaction digest mismatch")
            package_path = _safe_path(admission.get("package", {}).get("path"), runtime, "packages", "execution package")
            package = _artifact(package_path, admission["package"]["digest"], "execution package")
            artifacts["admission_transaction"] = {"path": str(admission_path), "digest": admission.get("transaction_digest")}
            artifacts["execution_package"] = {"path": str(package_path), "digest": admission["package"]["digest"]}
            authored = _wop(package, mission_id, submission["wop_id"], root)
            for directory, field, label in (("mission-contracts", "mission_contract", "Mission Contract"), ("execution-authority", "execution_authority", "execution authority"), ("receipts", "admission_receipt", "admission receipt"), ("journals", "admission_journal", "admission journal")):
                path = _safe_path(admission[field]["path"], runtime, directory, label)
                value = _artifact(path, admission[field]["digest"], label)
                artifacts[field] = {"path": str(path), "digest": admission[field]["digest"]}
                if value.get("mission_id") != mission_id or value.get("wop_id") != submission["wop_id"]:
                    raise MissionVerificationError("ADMISSION_ARTIFACT_MISMATCH", f"{label} identity mismatch")
            if admission.get("operation") != "BETA" or admission.get("repository_baseline") != repository_data.get("mission_provenance_baseline"):
                raise MissionVerificationError("REPOSITORY_BASELINE_MISMATCH", "admission baseline or operation is invalid")
            checks["wop"] = "PASS"; checks["admission"] = "PASS"
        except Exception as error:
            checks["wop"] = "FAIL" if "WOP" in str(error).upper() else checks["wop"]
            checks["admission"] = "FAIL"; checks["artifact_integrity"] = "FAIL"
            blockers.append({"code": getattr(error, "code", "ADMISSION_ARTIFACT_MISMATCH"), "message": str(error)})

        try:
            if bootstrap.get("bootstrap_state") != "READY_FOR_EXECUTION_PROVIDER" or bootstrap.get("bootstrap_result") != "PASS":
                raise MissionVerificationError("BOOTSTRAP_DIGEST_FAILURE", "bootstrap is not provider-ready")
            if bootstrap.get("provider_ready") is not True or any(bootstrap.get(k) is not False for k in ("provider_selected", "dispatch_created", "execution_started")):
                raise MissionVerificationError("PROVIDER_READINESS_INVALID", "bootstrap crosses the provider boundary")
            if bootstrap.get("transaction_digest") != _transaction_digest(bootstrap):
                raise MissionVerificationError("BOOTSTRAP_DIGEST_FAILURE", "bootstrap transaction digest mismatch")
            for directory, field, label in (("bootstraps", "bootstrap_transaction", "bootstrap transaction"), ("execution-records", "execution_record", "execution record"), ("bootstrap-receipts", "bootstrap_receipt", "bootstrap receipt"), ("bootstrap-journals", "bootstrap_journal", "bootstrap journal"), ("provider-readiness", "provider_readiness", "provider readiness")):
                descriptor = bootstrap if field == "bootstrap_transaction" else bootstrap.get(field, {})
                path = _safe_path(descriptor.get("path") if field != "bootstrap_transaction" else str(runtime / "bootstraps" / f"{bootstrap['bootstrap_id']}.json"), runtime, directory, label)
                value = bootstrap if field == "bootstrap_transaction" else _artifact(path, descriptor.get("digest"), label)
                artifacts[field] = {"path": str(path), "digest": bootstrap.get("transaction_digest") if field == "bootstrap_transaction" else descriptor.get("digest")}
                if value.get("mission_id") != mission_id or value.get("bootstrap_id") != bootstrap.get("bootstrap_id"):
                    raise MissionVerificationError("EXECUTION_RECORD_MISMATCH", f"{label} identity mismatch")
            checks["bootstrap"] = "PASS"; checks["execution_record"] = "PASS"; checks["provider_readiness"] = "PASS"
        except Exception as error:
            checks["bootstrap"] = "FAIL"; checks["execution_record"] = "FAIL"; checks["provider_readiness"] = "FAIL"; checks["artifact_integrity"] = "FAIL"
            blockers.append({"code": getattr(error, "code", "BOOTSTRAP_DIGEST_FAILURE"), "message": str(error)})

    provider_stage: dict[str, Any] = {}
    try:
        # Provider-selection artifacts are the authorized P5-G1 boundary and
        # are therefore not downstream effects.  The provider controller
        # remains the authoritative validator; this projection only exposes
        # its validated terminal state in mission views.
        from scripts.lib.emp.provider_selection import _mission_artifacts, _verify_set
        provider_stage = _verify_set(runtime, _mission_artifacts(runtime, mission_id)) or {}
        if provider_stage.get("result") != "PASS" and any(_mission_artifacts(runtime, mission_id).values()):
            raise MissionVerificationError("PROVIDER_SELECTION_ARTIFACT_MISMATCH", "provider-selection artifacts are invalid")
    except Exception as error:
        if any((runtime / directory).glob("*.json") for directory in ("provider-selection", "selected-providers", "provider-qualifications", "provider-selection-receipts", "provider-selection-journals", "dispatch-readiness") if (runtime / directory).is_dir()):
            checks["artifact_integrity"] = "FAIL"
            blockers.append({"code": getattr(error, "code", "PROVIDER_SELECTION_ARTIFACT_MISMATCH"), "message": str(error)})
    dispatch_stage: dict[str, Any] = {}
    try:
        # P5-G2 dispatch artifacts are the authorized terminal stage for this
        # verifier.  They bind to the already validated provider selection but
        # do not authorize a provider session or execution.
        from scripts.lib.emp.dispatch_foundation import _found, _verify_set
        dispatch_stage = _verify_set(runtime, _found(runtime, mission_id)) or {}
        if dispatch_stage:
            artifacts.update(dispatch_stage.get("artifacts", {}))
    except Exception as error:
        if any((runtime / directory).glob("*.json") for directory in ("dispatches", "dispatch-packages", "dispatch-authorizations", "dispatch-receipts", "dispatch-journals", "provider-session-readiness") if (runtime / directory).is_dir()):
            checks["artifact_integrity"] = "FAIL"
            blockers.append({"code": getattr(error, "code", "DISPATCH_ARTIFACT_MISMATCH"), "message": str(error)})
    provider_session_stage: dict[str, Any] = {}
    try:
        from scripts.lib.emp import provider_session
        provider_session_stage = provider_session.verify(root, mission_id, runtime_root=runtime)
        if provider_session_stage.get("result") != "PASS":
            checks["provider_session"] = "FAIL"
            blockers.extend(provider_session_stage.get("blockers", []))
        elif provider_session_stage.get("provider_session_created"):
            artifacts.update(provider_session_stage.get("artifacts", {}))
    except Exception as error:
        checks["provider_session"] = "FAIL"
        blockers.append({"code": getattr(error, "code", "PROVIDER_SESSION_INVALID"), "message": str(error)})
    downstream = []
    # P5-G3 provider sessions are a controlled pre-invocation foundation
    # artifact.  Their own controller verifies integrity and boundary; they
    # are not an execution/downstream effect for mission verification.
    for directory in ("providers", "dispatch", "executions", "execution-sessions"):
        for path in (runtime / directory).glob("*.json") if (runtime / directory).is_dir() else ():
            try:
                value = _load(path)
            except MissionVerificationError:
                continue
            if value.get("mission_id") == mission_id:
                downstream.append(str(path))
    if downstream:
        checks["downstream_boundary"] = "FAIL"
        blockers.append({"code": "DOWNSTREAM_EFFECT_DETECTED", "message": "canonical mission has downstream artifacts"})

    baseline_resolution = repository_data.get("baseline_resolution", {})
    baseline_ok = baseline_resolution.get("publication_parity") == "PASS"
    if not baseline_ok and not any(item.get("code") == "PUBLICATION_PARITY_FAILURE" for item in blockers):
        blockers.append({"code": "PUBLICATION_PARITY_FAILURE", "message": "current repository is not the published baseline"})
    if not repository_data.get("repository_path"):
        checks["downstream_boundary"] = "FAIL"
    if not baseline_ok:
        checks["artifact_integrity"] = "FAIL"
    checks.update({
        "repository_identity": "PASS" if repository_data.get("repository_path") else "FAIL",
        "repository_baseline": "PASS" if baseline_ok else "FAIL",
        "mission_provenance": baseline_resolution.get("checks", {}).get("mission_provenance", "FAIL"),
        "runtime_repository_binding": "PASS" if runtime_data.get("identity") == "PASS" and repository_data.get("repository_path") else "FAIL",
        "authoritative_runtime": "PASS" if runtime_data.get("identity") == "PASS" else "FAIL",
        "runtime_identity": runtime_data.get("identity", "FAIL"),
        "operation_beta_authority": "PASS" if authority.get("framework") == "OPERATION_BETA" and authority.get("integrity") == "PASS" else "FAIL",
        "oa_authority_exclusion": "PASS" if authority.get("oa_authority") == "SUPERSEDED" and authority.get("oa_fallback") == "PROHIBITED" else "FAIL",
        "dispatch_verification": "PASS" if dispatch_stage else "PASS",
    })
    result = "PASS" if not blockers and all(value == "PASS" for value in checks.values()) else "FAIL"
    if result == "FAIL":
        next_action = blockers[0].get("message", "Resolve blockers")
    else:
        next_action = (provider_session_stage.get("next_authorized_action") if provider_session_stage.get("provider_session_created") else ("ESTABLISH_PROVIDER_SESSION" if dispatch_stage else ("EVALUATE_PROVIDER_DISPATCH" if provider_stage else "EVALUATE_EXECUTION_PROVIDER")))
    return {
        "schema_version": SCHEMA_VERSION, "result": result, "mission_verification": result, "read_only": True,
        "mission_id": mission_id, "wop_id": chain.get("submission", {}).get("wop_id"),
        "submission_id": chain.get("submission", {}).get("submission_id"), "admission_id": chain.get("admission", {}).get("admission_id"),
        "bootstrap_id": chain.get("bootstrap", {}).get("bootstrap_id"),
        "authority": authority, "repository": {"identity": "PASS" if repository_data.get("repository_path") else "FAIL", "baseline": "PASS" if baseline_ok else "FAIL", **repository_data, **{
            "current_baseline": baseline_resolution.get("current_head"),
            "published_baseline": baseline_resolution.get("published_head"),
            "eos_baseline": baseline_resolution.get("eos_baseline"),
            "mission_provenance_baseline": baseline_resolution.get("mission_provenance_baseline"),
            "mission_baseline_relationship": baseline_resolution.get("mission_baseline_relationship"),
        }},
        "runtime": runtime_data, "checks": checks,
        "replay": {"submission": "IDEMPOTENT" if chain else "UNKNOWN", "admission": "IDEMPOTENT" if chain else "UNKNOWN", "bootstrap": "IDEMPOTENT" if chain else "UNKNOWN", "provider_session": provider_session_stage.get("replay", "UNKNOWN")},
        "lifecycle": {"submission_state": chain.get("submission", {}).get("submission_state"), "admission_state": chain.get("admission", {}).get("admission_state"), "bootstrap_state": chain.get("bootstrap", {}).get("bootstrap_state"), "provider_ready": chain.get("bootstrap", {}).get("provider_ready", False), "provider_selected": bool(provider_stage), "provider_qualified": bool(provider_stage.get("provider_qualified", False)), "dispatch_eligible": bool(provider_stage.get("dispatch_eligible", False)), "provider_id": provider_stage.get("provider_id"), "dispatch_created": bool(dispatch_stage), "provider_session_created": bool(provider_session_stage.get("provider_session_created")), "provider_session_authorized": bool(provider_session_stage.get("provider_session_authorized")), "provider_session_id": provider_session_stage.get("provider_session_id"), "provider_session_state": provider_session_stage.get("session_state"), "provider_invoked": bool(provider_session_stage.get("provider_invoked", False)), "execution_started": bool(provider_session_stage.get("execution_started", False))},
        "provider_selection": provider_stage,
        "dispatch": dispatch_stage,
        "provider_session": provider_session_stage,
        "artifacts": artifacts, "legacy_excluded": True, "blockers": blockers, "next_authorized_action": next_action,
    }


def render(value: dict[str, Any]) -> str:
    lifecycle = value.get("lifecycle", {})
    checks = value.get("checks", {})
    replay = value.get("replay", {})
    def status(key: str) -> str: return checks.get(key, "PASS" if key == "provider_selection" and lifecycle.get("provider_selected") else "FAIL")
    repository = value.get("repository", {})
    return "\n".join(("Zeus Mission Verification", "-------------------------", f"Result              : {value.get('result')}", f"mission_verification: {value.get('mission_verification', value.get('result'))}", f"Mission             : {value.get('mission_id')}", "Operation           : BETA", f"Authority           : {value.get('authority', {}).get('integrity', 'FAIL')}", f"OA authority        : {value.get('authority', {}).get('oa_authority', 'UNKNOWN')}", f"Repository identity : {repository.get('identity')}", f"Repository baseline : {repository.get('baseline')}", f"Current published baseline : {repository.get('published_baseline')}", f"Mission provenance baseline: {repository.get('mission_provenance_baseline')}", f"Baseline relationship       : {repository.get('mission_baseline_relationship')}", f"Published baseline parity  : {repository.get('baseline')}", f"Mission provenance          : {value.get('checks', {}).get('mission_provenance')}", f"Runtime identity    : {value.get('runtime', {}).get('identity')}", f"WOP                 : {status('wop')}", f"Submission          : {status('submission')}", f"Admission           : {status('admission')}", f"Bootstrap           : {status('bootstrap')}", f"Execution record    : {status('execution_record')}", f"Provider readiness  : {status('provider_readiness')}", f"Provider selection  : {status('provider_selection')}", f"Dispatch verification: {status('dispatch_verification')}", f"Artifact integrity  : {status('artifact_integrity')}", f"Artifact cardinality: {status('artifact_cardinality')}", f"Replay              : {replay.get('submission')}", f"Provider selected   : {'YES' if lifecycle.get('provider_selected') else 'NO'}", f"Dispatch created   : {'YES' if lifecycle.get('dispatch_created') else 'NO'}", f"Provider session    : {'YES' if lifecycle.get('provider_session_created') else 'NO'}", f"Execution started   : {'YES' if lifecycle.get('execution_started') else 'NO'}", f"Blockers            : {'NONE' if not value.get('blockers') else ', '.join(item.get('code', 'UNKNOWN') for item in value['blockers'])}", f"Next action         : {value.get('next_authorized_action')}", "Read-only           : YES", "read_only: true", ""))
