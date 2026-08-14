"""Zeus-owned Codex session adapter for the P5-G6 controlled boundary.

The adapter is the only normal path from a verified execution-start record to
Codex.  It owns the session binding and process identity, while the provider
never owns mission authority.  Verification is read-only; ``start``,
``resume``, and ``stop`` are the only mutating operations.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
import hashlib
import shutil
import stat
import tomllib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_identity import resolve as resolve_repository
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos import operational_beta
from scripts.lib.emp.codex_reconciliation import process_identity


CONTRACT = "ZEUS-P5-G6-CODEX-ADAPTER"
VERSION = "1"
PROVIDER_ID = "zeus-local-loneal-01"
ADAPTER_ID = "zeus-codex-process-v1"
STAGE_DIR = "codex-sessions"
LOG_DIR = "codex-logs"
EVENT_DIR = "codex-events"
CODEX_HOME_DIR = "codex-home"
ACTIVE_TRANSITION_DIR = "execution-active-transitions"
MONITORING_DIR = "execution-monitoring"
ACTIVE_STATES = {"ACTIVE", "RESUMED"}
STOPPED_STATES = {"INTERRUPTED", "STOPPED", "FAILED"}
MANAGED_PROVIDER_MODE = "APP_SERVER_MANAGED"
MANAGED_PROVIDER_TRANSPORT = "STDIO"
MANAGED_APPROVAL_POLICY = "never"
MANAGED_SANDBOX = "workspace-write"
SUPPORTED_CODEX_VERSION = (0, 147)
ZEUS_OWNED_PROHIBITED_OPERATIONS = (
    "git_fetch", "git_stage", "git_commit", "git_push", "publication", "eos_synchronization",
    "mission_lifecycle_advance", "qualification_acceptance", "closeout",
)


class CodexAdapterError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED",
                 details: Mapping[str, Any] | None = None):
        self.code, self.message, self.next_action = code, message, next_action
        self.details = dict(details or {})
        super().__init__(message)


def resolve_provider_invocation_contract(
        repository: Path | str, *, work_contract: Path | str | None = None,
        codex_bin: str = "codex", requested_options: list[str] | tuple[str, ...] = (),
        runtime_root: Path | str | None = None,
        lifecycle_binding: Mapping[str, Any] | None = None,
        mission_id: str | None = None, transaction_id: str | None = None) -> dict[str, Any]:
    """Resolve the Zeus-owned managed Codex contract without starting Codex.

    Capability discovery is intentionally limited to executable metadata and
    help output.  The provider process, broker, session, and mission-work
    lifecycle are not created by this operation.
    """
    root = Path(repository).resolve()
    executable = shutil.which(codex_bin) if not Path(codex_bin).is_absolute() else codex_bin
    if not executable or not Path(executable).is_file():
        raise CodexAdapterError("CODEX_INCOMPATIBILITY", "Codex executable is unavailable",
                                details={"incompatibility": "CODEX_EXECUTABLE_UNAVAILABLE"})

    def inspect(arguments: list[str], capability: str) -> str:
        try:
            completed = subprocess.run([executable, *arguments], cwd=root, capture_output=True,
                                       text=True, check=False, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CodexAdapterError("CODEX_INCOMPATIBILITY", f"Codex {capability} discovery failed: {error}",
                                    details={"incompatibility": f"{capability.upper()}_DISCOVERY_FAILED"}) from error
        output = (completed.stdout + "\n" + completed.stderr).strip()
        if completed.returncode:
            raise CodexAdapterError("CODEX_INCOMPATIBILITY", f"Codex {capability} discovery failed",
                                    details={"incompatibility": f"{capability.upper()}_DISCOVERY_FAILED",
                                             "return_code": completed.returncode})
        return output

    if work_contract is None:
        raise CodexAdapterError("WORK_CONTRACT_REQUIRED", "ZEUS_MANAGED execution requires a work contract",
                                next_action="PROVIDE_WORK_CONTRACT")
    version_output = inspect(["--version"], "version")
    version = next((line.strip() for line in version_output.splitlines()
                    if line.strip().startswith("codex-cli ")), version_output.splitlines()[0])
    version_match = re.fullmatch(r"codex-cli (\d+)\.(\d+)\.(\d+)(?:[-+].*)?", version)
    if not version_match or tuple(map(int, version_match.groups()[:2])) != SUPPORTED_CODEX_VERSION:
        raise CodexAdapterError("CODEX_INCOMPATIBILITY", "installed Codex version is outside the qualified policy",
                                details={"incompatibility": "UNSUPPORTED_CODEX_VERSION", "installed_version": version,
                                         "supported_policy": "codex-cli 0.147.x"})
    app_help = inspect(["app-server", "--help"], "app_server")
    exec_help = inspect(["exec", "--help"], "exec")
    resume_help = inspect(["exec", "resume", "--help"], "resume")
    required_syntax = {"app-server": "app-server", "--strict-config": "--strict-config",
                       "--listen": "--listen", "stdio://": "stdio://"}
    missing = [option for option, marker in required_syntax.items() if marker not in app_help]
    capability_missing = []
    if not ("--json" in exec_help and "--output-last-message" in exec_help and "--sandbox" in exec_help):
        capability_missing.append("EXEC_RESULT_OUTPUT")
    if not ("SESSION_ID" in resume_help and "--last" in resume_help and "--strict-config" in resume_help):
        capability_missing.append("EXEC_RESUME")
    unsupported = [option for option in requested_options if option not in app_help]
    prohibited = [option for option in requested_options
                  if option == "--dangerously-bypass-approvals-and-sandbox"]
    if missing or unsupported or prohibited or capability_missing:
        raise CodexAdapterError(
            "CODEX_INCOMPATIBILITY", "managed Codex invocation options are incompatible",
            details={"incompatibility": "UNSUPPORTED_PROVIDER_OPTIONS",
                     "missing_required_options": missing,
                     "missing_capabilities": capability_missing,
                     "unsupported_options": sorted(set(unsupported + prohibited))},
        )

    contract_path = Path(work_contract).resolve()
    try:
        loaded = __import__("yaml").safe_load(contract_path.read_text(encoding="utf-8"))
    except (__import__("yaml").YAMLError, OSError, UnicodeError) as error:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract cannot be loaded",
                                details={"incompatibility": "MALFORMED_WORK_CONTRACT"}) from error
    if not isinstance(loaded, Mapping):
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract root must be a mapping",
                                details={"incompatibility": "INVALID_WORK_CONTRACT_ROOT"})
    contract_value = dict(loaded)
    contract_id = contract_value.get("work_contract_id")
    declared_mission = contract_value.get("mission_id")
    declared_transaction = contract_value.get("transaction_id") or contract_value.get("execution_id")
    repository_value = contract_value.get("repository")
    authority = contract_value.get("authority")
    lifecycle = contract_value.get("subject_lifecycle_authority", {})
    if not isinstance(contract_id, str) or not contract_id.strip():
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract identity is required",
                                details={"incompatibility": "WORK_CONTRACT_ID_MISSING"})
    if mission_id is not None and declared_mission != mission_id:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract mission identity differs from Zeus request",
                                details={"incompatibility": "MISSION_CONTEXT_MISMATCH"})
    if transaction_id is not None and declared_transaction != transaction_id:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract transaction identity differs from Zeus binding",
                                details={"incompatibility": "TRANSACTION_CONTEXT_MISMATCH"})
    if not isinstance(repository_value, Mapping) or not isinstance(repository_value.get("path"), str) or not repository_value["path"].strip():
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract repository path is required",
                                details={"incompatibility": "REPOSITORY_BINDING_MISSING"})
    if not isinstance(authority, Mapping) or not isinstance(lifecycle, Mapping):
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract authority structures must be mappings",
                                details={"incompatibility": "MALFORMED_AUTHORITY"})
    declared_repository = Path(repository_value["path"]).resolve()
    if not declared_repository.is_dir() or declared_repository != root:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract repository differs from the Zeus workspace",
                                details={"incompatibility": "REPOSITORY_BINDING_MISMATCH",
                                         "declared_repository": str(declared_repository), "workspace": str(root)})
    def authorized(name: str) -> bool:
        value = authority.get(name)
        return value is True or (isinstance(value, Mapping) and value.get("authorized") is True)
    if contract_value.get("work_type") != "ENGINEERING_IMPLEMENTATION" or not all(
            authorized(name) for name in ("engineering_implementation", "command_execution")):
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract lacks managed execution capabilities",
                                details={"incompatibility": "CAPABILITY_AUTHORITY_MISSING",
                                         "required_work_type": "ENGINEERING_IMPLEMENTATION",
                                         "required_capabilities": ["engineering_implementation", "command_execution"]})
    requested_operations = contract_value.get("requested_operations", [])
    if not isinstance(requested_operations, list) or any(not isinstance(item, str) for item in requested_operations):
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "requested_operations must be a list of strings",
                                details={"incompatibility": "MALFORMED_REQUESTED_OPERATIONS"})
    qualification_authority = authorized("qualification_execution")
    if "qualification" in requested_operations and not qualification_authority:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "qualification execution was requested without Zeus qualification authority",
                                details={"incompatibility": "QUALIFICATION_AUTHORITY_MISSING"})
    prohibited_operations = contract_value.get("prohibited_operations", [])
    if not isinstance(prohibited_operations, list) or any(not isinstance(item, str) for item in prohibited_operations):
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "prohibited_operations must be a list of strings",
                                details={"incompatibility": "MALFORMED_PROHIBITED_OPERATIONS"})
    missing_prohibitions = sorted(set(ZEUS_OWNED_PROHIBITED_OPERATIONS) - set(prohibited_operations))
    if missing_prohibitions:
        raise CodexAdapterError("WORK_CONTRACT_INCOMPATIBLE", "work contract does not preserve Zeus-owned operation boundaries",
                                details={"incompatibility": "PRIVILEGE_BOUNDARY_INCOMPLETE",
                                         "missing_prohibitions": missing_prohibitions})

    source_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).resolve()
    auth_path = source_home / "auth.json"
    config_path = source_home / "config.toml"
    if not auth_path.is_file():
        raise CodexAdapterError("CODEX_INCOMPATIBILITY", "Codex authentication is unavailable",
                                details={"incompatibility": "UNAUTHENTICATED", "auth_path": str(auth_path)})
    if config_path.is_file():
        try:
            tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise CodexAdapterError("CODEX_INCOMPATIBILITY", f"Codex configuration is invalid: {error}",
                                    details={"incompatibility": "MISCONFIGURED", "config_path": str(config_path)}) from error
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        conflicts = sorted(key for key in ("approval_policy", "sandbox_mode") if key in config)
        if conflicts:
            raise CodexAdapterError("CODEX_INCOMPATIBILITY", "Codex configuration conflicts with Zeus-managed policy",
                                    details={"incompatibility": "CONFIGURATION_CONFLICT", "conflicting_keys": conflicts})

    runtime = _runtime(root, runtime_root)
    writable_anchor = runtime
    missing_hierarchy = []
    while not writable_anchor.exists():
        missing_hierarchy.append(writable_anchor.name)
        if writable_anchor.parent == writable_anchor:
            break
        writable_anchor = writable_anchor.parent
    try:
        anchor_stat = writable_anchor.stat()
        groups = set(os.getgroups()) | {os.getegid()}
        owner_writable = (anchor_stat.st_uid == os.geteuid()
                          and bool(anchor_stat.st_mode & stat.S_IWUSR)
                          and bool(anchor_stat.st_mode & stat.S_IXUSR))
        group_writable = anchor_stat.st_gid in groups and bool(anchor_stat.st_mode & stat.S_IWGRP) and bool(anchor_stat.st_mode & stat.S_IXGRP)
        other_writable = bool(anchor_stat.st_mode & stat.S_IWOTH) and bool(anchor_stat.st_mode & stat.S_IXOTH)
    except OSError:
        owner_writable = group_writable = other_writable = False
    if not (owner_writable or group_writable or other_writable):
        raise CodexAdapterError("CODEX_INCOMPATIBILITY", "per-session CODEX_HOME cannot be materialized",
                                details={"incompatibility": "CODEX_HOME_NOT_WRITABLE",
                                         "runtime_root": str(runtime)})
    planned_codex_home = runtime / CODEX_HOME_DIR / "<managed-session-id>"

    command = [str(Path(executable).resolve()), "app-server", "--strict-config", "--listen", "stdio://"]
    contract_digest = digest(contract_value)
    binding = dict(lifecycle_binding or {})
    if binding and (binding.get("provider_id") != PROVIDER_ID or not binding.get("provider_session_id")
                    or not binding.get("provider_invocation_id") or not binding.get("execution_id")):
        raise CodexAdapterError("PROVIDER_BINDING_INCOMPATIBLE", "authoritative lifecycle provider binding is incomplete or incompatible")
    execution_authorized = any(
        value is True or (isinstance(value, Mapping) and value.get("authorized") is True)
        for key, value in lifecycle.items() if key in {"mission_execution", "mission_dispatch"}
    )
    plan = {
        "result": "PASS", "preflight_status": "AVAILABLE", "provider_id": PROVIDER_ID,
        "execution_mode": "ZEUS_MANAGED", "session_mode": "ZEUS_MANAGED",
        "provider_mode": MANAGED_PROVIDER_MODE, "provider_transport": MANAGED_PROVIDER_TRANSPORT,
        "codex_binary": command[0], "codex_version": version, "supported_version_policy": "codex-cli 0.147.x", "command": command,
        "required_codex_invocation_arguments": command[1:], "supported_options": sorted(required_syntax),
        "unsupported_options": [], "approval_policy": MANAGED_APPROVAL_POLICY,
        "interaction": "NON_INTERACTIVE", "sandbox": MANAGED_SANDBOX,
        "workspace": str(root), "repository_binding": "PASS", "session_binding_required": True,
        "provider_session_binding_required": True, "execution_binding_required": True,
        "app_server_protocol": "JSON-RPC", "strict_config": True,
        "config_path": str(config_path), "config_present": config_path.is_file(),
        "authentication": "PRESENT", "auth_path": str(auth_path),
        "codex_home": str(planned_codex_home), "codex_home_isolation": "PER_SESSION",
        "codex_home_writable": True, "runtime_materialization_anchor": str(writable_anchor),
        "runtime_missing_components": list(reversed(missing_hierarchy)),
        "work_contract": str(contract_path) if contract_path else None,
        "work_contract_id": contract_id, "work_contract_digest": contract_digest,
        "work_contract_capabilities": "PASS", "lifecycle_execution_authorized": execution_authorized,
        "mission_context": "BOUND" if mission_id else "DECLARED_BY_WORK_CONTRACT" if declared_mission else "NOT_BOUND",
        "transaction_context": "BOUND" if transaction_id else "DECLARED_BY_WORK_CONTRACT" if declared_transaction else "NOT_BOUND",
        "qualification_authority": "AVAILABLE" if qualification_authority else "NOT_GRANTED",
        "requested_operations": sorted(requested_operations),
        "prohibited_operations": sorted(set(prohibited_operations)),
        "authoritative_provider_binding": binding or None,
        "provider_binding": "PASS" if binding else "NOT_APPLICABLE_BOOTSTRAP_PREFLIGHT",
        "normal_completion_semantics": "BROKER_EXIT_ZERO_AND_PROVIDER_EXIT_ZERO",
        "abnormal_completion_semantics": "NONZERO_OR_SIGNAL_RECORDED_FAILED_AND_RECONCILED",
        "configuration_precedence": "ZEUS_THREAD_PARAMETERS_OVERRIDE_PROVIDER_DEFAULTS",
        "provider_started": False, "mission_work_started": False, "repository_work_started": False,
        "read_only": True, "next_authorized_action": "START_CODEX_SESSION" if execution_authorized else "RETURN_TO_AUTHORIZED_OPERATOR_BOUNDARY",
    }
    plan["plan_digest"] = digest({key: value for key, value in plan.items() if key != "plan_digest"})
    return plan


def _execution_verification_error(execution: Mapping[str, Any]) -> CodexAdapterError:
    blockers = execution.get("blockers") or []
    blocker = blockers[0] if blockers and isinstance(blockers[0], Mapping) else {}
    return CodexAdapterError(
        str(blocker.get("code") or "EXECUTION_START_FAILURE"),
        str(blocker.get("message") or "execution-start verification failed"),
        next_action=str(execution.get("next_authorized_action") or "STOP_FAIL_CLOSED"),
    )


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root:
        return Path(runtime_root).resolve()
    return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()


def _session_path(runtime: Path, session_id: str) -> Path:
    path = (runtime / STAGE_DIR / f"{session_id}.json").resolve()
    try:
        path.relative_to((runtime / STAGE_DIR).resolve())
    except ValueError as error:
        raise CodexAdapterError("SESSION_PATH_ESCAPE", "Codex session path escapes runtime") from error
    return path


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception as error:
        raise CodexAdapterError("SESSION_ARTIFACT_INVALID", f"{path}: {error}") from error
    supplied = value.get("state_digest")
    unsigned = {key: item for key, item in value.items() if key != "state_digest"}
    if supplied != digest(unsigned):
        raise CodexAdapterError("SESSION_DIGEST_MISMATCH", f"{path} digest mismatch")
    return value


def _save(runtime: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("state_digest", None)
    unsigned["state_digest"] = digest(unsigned)
    atomic_write(_session_path(runtime, str(unsigned["session_id"])), unsigned)
    return unsigned


def _append_event(runtime: Path, session_id: str, event: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    directory = runtime / EVENT_DIR / session_id
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("*.json"))
    sequence = len(existing) + 1
    material = {"schema_version": 1, "sequence": sequence, "session_id": session_id,
                "event": event, "payload": dict(payload),
                "previous_event_digest": None}
    if existing:
        previous = load_json(existing[-1])
        material["previous_event_digest"] = previous.get("event_digest")
    material["event_digest"] = digest(material)
    path = directory / f"{sequence:04d}.json"
    if path.exists():
        current = load_json(path)
        if current != material:
            raise CodexAdapterError("EVENT_CONFLICT", f"event {path} conflicts with immutable state")
    else:
        atomic_write(path, material)
    return material


def _authority(root: Path) -> dict[str, Any]:
    value = operational_beta.authority(root)
    required = {"authority_framework": "OPERATION_BETA", "authority_integrity": "PASS",
                "authority_resolution": "PASS", "authority_digest_validation": "PASS",
                "oa_authority": "SUPERSEDED"}
    if any(value.get(key) != expected for key, expected in required.items()):
        raise CodexAdapterError("AUTHORITY_FAILURE", "published Operation Beta authority chain failed")
    return {"framework": "OPERATION_BETA", "source": "published Operation Beta authority chain",
            "digest": value.get("authority_digest"), "integrity": "PASS", "oa_authority": "SUPERSEDED"}


def _package(root: Path, mission_id: str, runtime: Path) -> dict[str, Any]:
    from scripts.lib.emp.execution_start import verify as verify_execution_start
    execution = verify_execution_start(root, mission_id, runtime_root=runtime)
    if execution.get("result") != "PASS":
        raise _execution_verification_error(execution)
    if execution.get("mission_id") != mission_id:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution-start mission binding differs from requested mission")
    if not execution.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISSING", "execution-start has no bound WOP")
    if not execution.get("execution_session_id") or not execution.get("provider_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISSING", "execution-start session bindings are incomplete")
    if not execution.get("provider_id") or not execution.get("provider_invocation_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISSING", "execution-start provider bindings are incomplete")
    if execution.get("blockers") or execution.get("approvals_required"):
        raise CodexAdapterError("EXECUTION_BLOCKED", "execution has an active blocker or outstanding approval")
    if execution.get("execution_start_state") != "READY_FOR_CONTROLLED_EXECUTION":
        raise CodexAdapterError("EXECUTION_STATE_INVALID", "execution is not at READY_FOR_CONTROLLED_EXECUTION")
    if execution.get("next_authorized_action") != "BEGIN_CONTROLLED_MISSION_WORK":
        raise CodexAdapterError("EXECUTION_NOT_READY", "execution is not at the controlled mission-work boundary")
    if execution.get("mission_work_started"):
        raise CodexAdapterError("MISSION_WORK_ALREADY_STARTED", "mission work is already active")
    authority = _authority(root)
    identity = resolve_repository(root)
    execution_id = execution["execution_id"]
    package = {
        "schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
        "mission_id": mission_id, "wop_id": execution.get("wop_id"), "execution_id": execution_id,
        "execution_session_id": execution["execution_session_id"],
        "provider_id": execution["provider_id"], "provider_invocation_id": execution["provider_invocation_id"],
        "provider_session_id": execution.get("provider_session_id"),
        "repository": str(root), "repository_identity": identity["repository_identity"],
        "repository_id": identity["repository_id"], "repository_fingerprint": identity["repository_fingerprint"],
        "current_published_baseline": execution["current_published_baseline"],
        "execution_start_provenance_baseline": execution.get("execution_start_provenance_baseline"),
        "execution_start_baseline_relationship": execution.get("execution_start_baseline_relationship"),
        "execution_package_digest": None, "execution_authority_digest": None,
        "scope": {"owner": "Zeus", "mission_work_started": False,
                  "repository_work_started": False, "operator_approval_required": False,
                  "stop_boundary": "FIRST_CONTROLLED_EXECUTION_BOUNDARY",
                  "sandbox": "workspace-write"},
        "work_authority": {"source": "operator-submitted WOP",
                            "wop_id": execution.get("wop_id"),
                            "admission_id": execution.get("admission_id")},
        "authority": authority,
    }
    start_transaction = runtime / "execution-start-transactions" / f"{execution_id}.json"
    if start_transaction.is_file():
        transaction = load_json(start_transaction)
        package["execution_package_digest"] = transaction.get("execution_package_digest")
        package["execution_authority_digest"] = transaction.get("execution_authority_digest")
    package["package_digest"] = digest(package)
    return package


def _existing(runtime: Path, mission_id: str) -> dict[str, Any] | None:
    matches = []
    directory = runtime / STAGE_DIR
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
        value = _load(path)
        if value.get("mission_id") == mission_id:
            matches.append(value)
    historical_states = {"SUPERSEDED", "RECONCILED_HISTORICAL", "STOPPED", "FAILED", "INTERRUPTED", "COMPLETED"}
    historical_dispositions = {"SUPERSEDED", "HISTORICAL", "RECONCILED_HISTORICAL"}
    current = [value for value in matches if value.get("session_disposition") not in historical_dispositions
               and value.get("state") not in historical_states]
    if len(current) > 1:
        raise CodexAdapterError("SESSION_CARDINALITY_CONFLICT", "more than one current Codex session belongs to the mission")
    if current:
        return current[0]
    return None


def _all_sessions(runtime: Path, mission_id: str | None = None) -> list[dict[str, Any]]:
    directory = runtime / STAGE_DIR
    values = [_load(path) for path in sorted(directory.glob("*.json"))] if directory.is_dir() else []
    return [value for value in values if mission_id is None or value.get("mission_id") == mission_id]


def select_session(repository: Path | str, mission_id: str | None = None, *,
                   session_id: str | None = None, latest: bool = False,
                   active: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Resolve one Zeus-managed execution session, read-only and fail-closed."""
    if sum(bool(value) for value in (session_id, latest, active)) > 1:
        raise CodexAdapterError("SESSION_SELECTOR_CONFLICT", "select exactly one of --session, --latest, or --active")
    runtime = _runtime(Path(repository).resolve(), runtime_root)
    mission = str(mission_id).upper() if mission_id else None
    values = [value for value in _all_sessions(runtime, mission)
              if value.get("execution_mode", "ZEUS_MANAGED") == "ZEUS_MANAGED"
              and value.get("managed") is not False]
    if session_id:
        values = [value for value in values if value.get("session_id") == session_id]
        if len(values) != 1:
            raise CodexAdapterError("SESSION_NOT_FOUND", "the requested managed session is not uniquely discoverable")
        selected = values[0]
    else:
        live = [value for value in values if value.get("state") not in STOPPED_STATES
                and value.get("state") not in {"SUPERSEDED", "RECONCILED_HISTORICAL", "COMPLETED"}
                and runtime_liveness(value).get("session_live")]
        if active:
            if len(live) > 1:
                raise CodexAdapterError("SESSION_SELECTION_AMBIGUOUS", "multiple live managed sessions match; use --session")
            if not live:
                raise CodexAdapterError("SESSION_NOT_FOUND", "no live authoritative managed session matches --active")
            selected = live[0]
        else:
            candidates = [value for value in values
                          if value.get("state") not in {"SUPERSEDED", "RECONCILED_HISTORICAL"}] if latest else values
            if not candidates:
                raise CodexAdapterError("SESSION_NOT_FOUND", "no compatible managed session matches the selector")
            timestamps = [value.get("start_timestamp", 0) for value in candidates]
            if latest and timestamps.count(max(timestamps)) > 1:
                raise CodexAdapterError("SESSION_SELECTION_AMBIGUOUS", "multiple managed sessions have equal latest authority; use --session")
            selected = max(candidates, key=lambda value: (value.get("start_timestamp", 0), value.get("session_id", "")))
    return {"result": "PASS", "session": selected,
            "session_id": selected.get("session_id"), "mission_id": selected.get("mission_id"),
            "selector": "session" if session_id else "active" if active else "latest" if latest else "current",
            "read_only": True}


def selected_status(repository: Path | str, mission_id: str | None = None, *,
                    session_id: str | None = None, latest: bool = False,
                    active: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    selected = select_session(repository, mission_id, session_id=session_id, latest=latest,
                              active=active, runtime_root=runtime_root)
    value = status(repository, str(selected["session"].get("mission_id")), runtime_root=runtime_root)
    value.update({"selector": selected["selector"], "resolved_session_id": selected["session_id"],
                  "read_only": True})
    return value


def current_session(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any] | None:
    """Resolve the one current managed session while retaining superseded history."""
    return _existing(_runtime(Path(repository).resolve(), runtime_root), str(mission_id).upper())


def resolve_session_binding(repository: Path | str, *, mission_id: str | None = None,
                            execution_id: str | None = None,
                            runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Resolve the execution, provider, and Codex session namespaces together.

    ``session_id`` historically meant the Codex-managed session in monitoring,
    while execution-start artifacts use ``execution_session_id``.  Keep those
    identities explicit and require one matching managed session rather than
    guessing from a display projection.
    """
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    wanted_mission = str(mission_id).upper() if mission_id else None
    wanted_execution = str(execution_id).upper() if execution_id else None
    transactions = []
    directory = runtime / "execution-start-transactions"
    if directory.is_dir():
        transactions = [load_json(path) for path in sorted(directory.glob("*.json"))]
    matches = [value for value in transactions
               if (wanted_execution and str(value.get("execution_id", "")).upper() == wanted_execution)
               or (wanted_mission and str(value.get("mission_id", "")).upper() == wanted_mission)]
    if len(matches) != 1:
        raise CodexAdapterError("EXECUTION_BINDING_AMBIGUOUS", "execution binding is not uniquely discoverable")
    execution = matches[0]
    if wanted_mission and str(execution.get("mission_id", "")).upper() != wanted_mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution binding differs from requested mission")
    if wanted_execution and str(execution.get("execution_id", "")).upper() != wanted_execution:
        raise CodexAdapterError("EXECUTION_BINDING_MISMATCH", "execution binding differs from requested execution")
    sessions = _all_sessions(runtime, execution.get("mission_id"))
    candidates = [value for value in sessions
                  if value.get("execution_id") == execution.get("execution_id")
                  and value.get("execution_session_id") == execution.get("execution_session_id")
                  and value.get("provider_session_id") == execution.get("provider_session_id")
                  and value.get("provider_id") == execution.get("provider_id")]
    if len(candidates) > 1:
        raise CodexAdapterError("CODEX_SESSION_BINDING_AMBIGUOUS", "multiple Codex sessions share the execution binding")
    session = candidates[0] if candidates else None
    return {
        "result": "PASS", "mission_id": execution.get("mission_id"),
        "wop_id": execution.get("wop_id"), "execution_id": execution.get("execution_id"),
        "execution_session_id": execution.get("execution_session_id"),
        "provider_session_id": execution.get("provider_session_id"),
        "provider_id": execution.get("provider_id"),
        "codex_session_id": session.get("session_id") if session else None,
        "session_id": session.get("session_id") if session else None,
        "session_state": session.get("state") if session else None,
        "session_disposition": session.get("session_disposition") if session else None,
        "session_event_directory": session.get("event_directory") if session else None,
        "session": session, "execution": execution,
        "mapping_cardinality": "ONE" if session else "EXECUTION_ONLY",
        "read_only": True,
    }


def runtime_liveness(session: Mapping[str, Any]) -> dict[str, Any]:
    """Project process, provider, and managed-session liveness together.

    A recorded PID is only a locator.  ``process_identity`` verifies that the
    PID currently exists and is not a zombie; it is not treated as evidence
    that mission work is active.  This projection is shared by status,
    monitoring, and supersession safety checks.
    """
    process = process_identity(session.get("pid"))
    provider_pid = _marker_provider_pid(session) or session.get("provider_pid")
    provider = process_identity(provider_pid)
    process_present = bool(process.get("alive"))
    provider_present = bool(provider.get("alive"))
    any_present = process_present or provider_present
    session_live = process_present and provider_present
    return {
        "session_record_state": session.get("state"),
        "runtime_process_state": process.get("process_state") if process_present else "STOPPED",
        "runtime_process_present": process_present,
        "runtime_process_id": session.get("pid") if process_present else None,
        "runtime_process_identity": process,
        "runtime_process_owns_codex_session": ("YES" if process_present else "NO"),
        "provider_process_present": provider_present,
        "provider_process_id": provider_pid if provider_present else None,
        "provider_process_identity": provider,
        "provider_liveness": "ALIVE" if provider_present else "STOPPED" if provider_pid else "UNKNOWN",
        "mission_work_active": bool(session.get("mission_work_started")) and session_live,
        "repository_work_active": bool(session.get("repository_work_started")) and session_live,
        "session_live": session_live,
        "session_liveness": "ALIVE" if session_live else "PARTIAL" if any_present else "STOPPED",
        "runtime_classification": ("LIVE_PROVIDER_SESSION" if any_present and not session.get("mission_work_started")
                                    else "ACTIVE_MISSION_EXECUTION" if session_live and session.get("mission_work_started")
                                    else "STALE_ORPHANED_RUNTIME"),
    }


def _liveness_fingerprint(session: Mapping[str, Any], projection: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return stable facts for mutation-time liveness comparison.

    Observation timestamps and derived presentation fields are intentionally
    excluded.  Process identity digests prevent a reused PID from comparing
    equal to the original process when the runtime records contain identity
    evidence.
    """
    process = projection.get("runtime_process_identity") or {}
    provider = projection.get("provider_process_identity") or {}
    return (
        session.get("session_id"),
        bool(projection.get("runtime_process_present")),
        bool(projection.get("provider_process_present")),
        process.get("process_identity_digest"),
        provider.get("process_identity_digest"),
        projection.get("runtime_classification"),
    )


def _provider_liveness_snapshot(sessions: list[Mapping[str, Any]], provider_id: str) -> dict[str, Any]:
    """Resolve one canonical provider/session liveness snapshot."""
    projections = [
        (dict(session), runtime_liveness(session))
        for session in sessions
        if session.get("provider_id") == provider_id
    ]
    live = [
        {"session_id": session.get("session_id"), "liveness": projection}
        for session, projection in projections
        if projection.get("runtime_process_present") or projection.get("provider_process_present")
    ]
    return {
        "live_sessions": live,
        "fingerprints": [_liveness_fingerprint(session, projection) for session, projection in projections],
    }


def supersede_session(repository: Path | str, mission_id: str, old_session_id: str, *,
                      reason: str = "NON_AUTHORITATIVE_RECONCILED_HISTORY",
                      runtime_root: Path | str | None = None,
                      expected_wop_id: str | None = None,
                      expected_execution_id: str | None = None,
                      expected_provider_id: str | None = None) -> dict[str, Any]:
    """Create exactly one idle replacement for a safely reconciled stale session.

    This is the sole mutating session-repair path.  It never removes the
    predecessor or its event journal, and it refuses active, worked, ambiguous,
    or identity-divergent state.
    """
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    mission = str(mission_id).upper(); provider = expected_provider_id or PROVIDER_ID
    sessions = _all_sessions(runtime)
    requested_session_id = old_session_id
    predecessors = [value for value in sessions if value.get("session_id") == old_session_id]
    if not predecessors:
        # The operator-facing target may be the bound execution-session or
        # provider-session identity.  Resolve it only when exactly one Codex
        # record owns the complete immutable binding.
        aliases = [value for value in sessions
                   if old_session_id in {value.get("execution_session_id"), value.get("provider_session_id")}
                   and value.get("mission_id") == mission]
        if len(aliases) == 1:
            predecessors = aliases
        elif len(aliases) > 1:
            raise CodexAdapterError("CODEX_SESSION_BINDING_AMBIGUOUS", "session alias resolves to multiple Codex sessions")
    if len(predecessors) != 1:
        raise CodexAdapterError("OLD_SESSION_NOT_FOUND", "the requested stale session is not uniquely discoverable")
    old = predecessors[0]
    # From this point onward all lineage is recorded against the actual
    # Codex-managed identity, while the caller's alias is retained for audit.
    old_session_id = str(old["session_id"])
    if old.get("mission_id") != mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "stale session is bound to another mission")
    if old.get("provider_id") != provider:
        raise CodexAdapterError("PROVIDER_BINDING_MISMATCH", "stale session is bound to another provider")

    reconciliation = reconcile_session_history(root, mission, runtime_root=runtime, session=old)
    if reconciliation.get("history_disposition") == "INDETERMINATE":
        raise CodexAdapterError("AMBIGUOUS_HISTORY", "session history is indeterminate")
    if reconciliation.get("mission_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_MISSION_WORK", "prior mission work prevents session replacement")
    if reconciliation.get("repository_work_actually_occurred") != "NO":
        raise CodexAdapterError("PRIOR_REPOSITORY_WORK", "prior repository work prevents session replacement")
    if reconciliation.get("history_disposition") != "EVENTS_NON_AUTHORITATIVE" or not reconciliation.get("session_replacement_safe"):
        raise CodexAdapterError("RECONCILIATION_NOT_ACCEPTED", "accepted non-authoritative reconciliation is required")
    execution = _package(root, mission, runtime)
    for field, expected in (("wop_id", expected_wop_id), ("execution_id", expected_execution_id), ("provider_id", expected_provider_id)):
        if expected is not None and execution.get(field) != expected:
            raise CodexAdapterError(f"{field.upper()}_BINDING_MISMATCH", f"execution binding differs for {field}")
    for field in ("execution_id", "provider_id", "execution_session_id", "provider_session_id"):
        if old.get(field) and execution.get(field) != old.get(field):
            raise CodexAdapterError("SESSION_BINDING_MISMATCH", f"stale session binding differs for {field}")
    if old.get("wop_id") and execution.get("wop_id") != old.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISMATCH", "stale session is bound to another WOP")

    precheck = _provider_liveness_snapshot(sessions, provider)
    linked = [value for value in sessions if value.get("supersedes_session") == old_session_id]
    if len(linked) > 1:
        raise CodexAdapterError("SESSION_SUCCESSOR_CONFLICT", "stale session has multiple replacements")
    if linked:
        replacement = linked[0]
        if replacement.get("mission_id") != mission or replacement.get("execution_id") != execution["execution_id"] or replacement.get("provider_id") != provider:
            raise CodexAdapterError("SESSION_BINDING_MISMATCH", "existing replacement has divergent bindings")
        return {"result": "PASS", "replay": "IDEMPOTENT", "mutation_applied": False,
                "requested_session_id": requested_session_id,
                "old_session_id": old_session_id, "new_session_id": replacement["session_id"],
                "old_session_disposition": "SUPERSEDED", "old_session_preserved": True,
                "supersedes_session": old_session_id, "session_binding": "PASS",
                "canonical_package_binding": "PASS", "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}

    # Re-resolve immediately before the first durable supersession write.  A
    # provider can stop after preflight or appear during the transaction; the
    # mutation must not guess across that boundary.
    mutation_check = _provider_liveness_snapshot(sessions, provider)
    if mutation_check["fingerprints"] != precheck["fingerprints"]:
        raise CodexAdapterError(
            "LIVENESS_CHANGED_DURING_TRANSACTION",
            "provider/session liveness changed between supersession checks",
            details={"precheck": precheck, "mutation_check": mutation_check},
        )
    if mutation_check["live_sessions"]:
        raise CodexAdapterError(
            "ACTIVE_SESSION_PROTECTION",
            "an existing provider/session runtime is active",
            details={"mutation_check": mutation_check},
        )

    replacement_id = identifier("CODEX-SESSION-REPLACEMENT", {
        "old_session_id": old_session_id, "mission_id": mission, "execution_id": execution["execution_id"],
        "provider_id": provider, "reason": reason,
    })
    event_directory = runtime / EVENT_DIR / replacement_id
    replacement = dict(execution, schema_version=1, contract={"id": CONTRACT, "version": VERSION},
                       session_id=replacement_id, state="READY", pid=None, provider_pid=None,
                       control_socket=None, remote_endpoint=None, log_path=str(runtime / LOG_DIR / f"{replacement_id}.jsonl"),
                       event_directory=str(event_directory), path=str(_session_path(runtime, replacement_id)),
                       mission_work_started=False, repository_work_started=False, started_by="zeus",
                       operator_approval=False, app_server_handshake="NOT_RUN", startup_diagnostics=None,
                       execution_mode="ZEUS_MANAGED", session_mode="ZEUS_MANAGED", provider_mode="APP_SERVER_MANAGED",
                       provider_transport="STDIO", remote_capable=False, readiness_result="PASS",
                       session_disposition="CURRENT", supersedes_session=old_session_id,
                       supersession_reason=reason, supersession_reconciliation=reconciliation,
                       canonical_package_binding="PASS")
    replacement["log_path"] = str(runtime / LOG_DIR / f"{replacement_id}.jsonl")
    old = dict(old, state="SUPERSEDED", session_disposition="SUPERSEDED", superseded_by=replacement_id,
               supersession_reason=reason, supersession_reconciliation=reconciliation)
    _save(runtime, old)
    _append_event(runtime, replacement_id, "CODEX_SESSION_REPLACED", {
        "supersedes_session": old_session_id, "reason": reason, "mission_id": mission,
        "wop_id": execution.get("wop_id"), "execution_id": execution.get("execution_id"), "provider_id": provider,
    })
    saved = _save(runtime, replacement)
    return {"result": "PASS", "replay": "APPLIED", "mutation_applied": True,
            "requested_session_id": requested_session_id,
            "old_session_id": old_session_id, "new_session_id": saved["session_id"],
            "old_session_disposition": "SUPERSEDED", "old_session_preserved": True,
            "supersedes_session": old_session_id, "session_binding": "PASS",
            "canonical_package_binding": "PASS", "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"}


def reconcile_session_history(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
                               session: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Reconcile Codex session work history without changing runtime state.

    Session events are evidence, not proof of applied mission work.  A work
    event is authoritative only when it carries the bound identity and has
    corroboration in the canonical execution/active-transition records.  The
    result is deliberately a projection: applying a session supersession or
    other runtime mutation remains a separate, explicitly authorized action.
    """
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    mission = str(mission_id).upper()
    current = dict(session) if session is not None else _existing(runtime, mission)
    if not current:
        return {"result": "PASS", "mission_id": mission, "history_disposition": "NO_SESSION",
                "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
                "reconciliation_required": False, "session_reuse_allowed": False,
                "session_supersession_required": False, "read_only": True}

    event_directory = Path(str(current.get("event_directory") or runtime / EVENT_DIR / current["session_id"]))
    # Read only numbered journal events.  Readiness markers such as
    # ``app-server-ready.json`` live beside the journal but are not events.
    paths = sorted(event_directory.glob("[0-9][0-9][0-9][0-9].json")) if event_directory.is_dir() else []
    events: list[dict[str, Any]] = []
    chain_errors: list[str] = []
    expected = 1
    for path in paths:
        try:
            event = load_json(path)
        except Exception as error:
            chain_errors.append(f"INVALID_EVENT:{path.name}:{error}")
            continue
        events.append(event)
        if event.get("sequence") != expected:
            chain_errors.append(f"SEQUENCE_GAP:{expected}:{event.get('sequence')}")
        if event.get("session_id") != current.get("session_id"):
            chain_errors.append(f"SESSION_BINDING:{path.name}")
        unsigned = {key: value for key, value in event.items() if key != "event_digest"}
        if event.get("event_digest") != digest(unsigned):
            chain_errors.append(f"EVENT_DIGEST:{path.name}")
        previous = events[-2].get("event_digest") if len(events) > 1 else None
        if event.get("previous_event_digest") != previous:
            chain_errors.append(f"PREVIOUS_DIGEST:{path.name}")
        expected += 1

    work_events = [event for event in events if event.get("event") in
                   {"MISSION_WORK_STARTED", "MISSION_WORK_RESUMED"}]
    execution = {}
    try:
        from scripts.lib.emp.execution_start import verify as verify_execution_start
        execution = verify_execution_start(root, mission, runtime_root=runtime)
    except Exception as error:
        chain_errors.append(f"EXECUTION_SOURCE_UNAVAILABLE:{error}")

    execution_id = current.get("execution_id")
    active_path = _active_path(runtime, str(execution_id)) if execution_id else None
    active_record = load_json(active_path) if active_path and active_path.is_file() else None
    authoritative_execution_work = execution.get("mission_work_started") is True
    authoritative_repository_work = execution.get("repository_work_started") is True
    active_work = bool(active_record and active_record.get("mission_work_started") is True)
    repository_receipts = list((runtime / "repository-work-receipts").glob("*.json")) if (runtime / "repository-work-receipts").is_dir() else []
    corroborating_work = authoritative_execution_work or active_work
    corroborating_repository = authoritative_repository_work or bool(repository_receipts)

    missing_provenance = []
    for event in work_events:
        payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
        for field in ("execution_id", "mission_id", "wop_id", "session_id", "provider_id", "source_digest"):
            if not (event.get(field) or payload.get(field)):
                missing_provenance.append(f"{event.get('event')}:{field}")

    if work_events and corroborating_work:
        disposition = "HISTORICAL_WORK_CONFIRMED"
        mission_work = "YES"
    elif work_events and not corroborating_work and (chain_errors or missing_provenance):
        disposition = "EVENTS_NON_AUTHORITATIVE"
        mission_work = "NO"
    elif work_events:
        disposition = "INDETERMINATE"
        mission_work = "INDETERMINATE"
    else:
        disposition = "NO_WORK_EVENTS"
        mission_work = "YES" if authoritative_execution_work else "NO"

    if corroborating_repository:
        repository_work = "YES"
    elif disposition == "INDETERMINATE":
        repository_work = "INDETERMINATE"
    else:
        repository_work = "NO"

    safe_unused = disposition in {"EVENTS_NON_AUTHORITATIVE", "NO_WORK_EVENTS"} and not corroborating_work and not corroborating_repository
    return {
        "result": "PASS" if disposition != "INDETERMINATE" else "FAIL",
        "mission_id": mission, "session_id": current.get("session_id"),
        "execution_id": execution_id, "provider_id": current.get("provider_id"),
        "mission_work_event_count": sum(event.get("event") == "MISSION_WORK_STARTED" for event in events),
        "mission_work_resumed_event_count": sum(event.get("event") == "MISSION_WORK_RESUMED" for event in events),
        "event_ids": [event.get("event_digest") for event in work_events],
        "event_provenance": "INSUFFICIENT" if missing_provenance else "PRESENT",
        "event_authority": "NON_AUTHORITATIVE" if disposition == "EVENTS_NON_AUTHORITATIVE" else "CORROBORATED" if corroborating_work else "NOT_ESTABLISHED",
        "chain_errors": chain_errors, "missing_provenance": missing_provenance,
        "mission_work_actually_occurred": mission_work,
        "repository_work_actually_occurred": repository_work,
        "corroborating_execution_evidence": {"execution_work": authoritative_execution_work, "active_record": active_work},
        "corroborating_repository_evidence": {"execution_work": authoritative_repository_work, "receipt_count": len(repository_receipts)},
        "history_disposition": disposition,
        "previous_projection": {"mission_work_started": current.get("mission_work_started"),
                                 "repository_work_started": current.get("repository_work_started"),
                                 "scope": current.get("scope")},
        "reconciled_projection": {"mission_work_started": mission_work == "YES",
                                   "repository_work_started": repository_work == "YES",
                                   "execution_state": execution.get("execution_start_state"),
                                   "next_authorized_action": execution.get("next_authorized_action")},
        "reconciliation_required": bool(work_events and (chain_errors or missing_provenance or disposition != "NO_WORK_EVENTS")),
        "session_reuse_allowed": False,
        "session_supersession_required": safe_unused or disposition == "EVENTS_NON_AUTHORITATIVE",
        "session_replacement_safe": safe_unused,
        "read_only": True,
    }


def _process_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _provider_control_ready(session: Mapping[str, Any]) -> bool:
    """Return whether the bound provider runtime can accept control traffic.

    PID presence is not sufficient here: retirement can leave stale PID
    metadata behind, and the broker's Unix socket is the actual control
    resource used by the active transition.  Reuse the canonical liveness
    projection and require the persisted control channel to exist before
    treating a session as resumable/idempotently live.
    """
    liveness = runtime_liveness(session)
    control_socket = session.get("control_socket")
    return bool(liveness.get("session_live") and control_socket and Path(str(control_socket)).exists())


def _startup_paths(runtime: Path, session_id: str) -> dict[str, Path]:
    # AF_UNIX is limited to a small byte-sized path on Linux.  Keep durable
    # receipts in the runtime tree, but put the ephemeral control socket in a
    # short shared runtime location so deep repository/runtime roots cannot
    # make launch fail mysteriously.
    socket_root = Path("/tmp/zeus-sockets")
    socket_name = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24] + ".sock"
    control = socket_root / socket_name
    if len(os.fsencode(str(control))) > 107:
        raise CodexAdapterError("AF_UNIX_PATH_TOO_LONG",
                                f"control socket path exceeds AF_UNIX limit: {control}",
                                next_action="SHORTEN_RUNTIME_SOCKET_LOCATION")
    return {
        "codex_home": runtime / CODEX_HOME_DIR / session_id,
        "ready": runtime / EVENT_DIR / session_id / "app-server-ready.json",
        "exited": runtime / EVENT_DIR / session_id / "app-server-exited.json",
        "control": control,
    }


def _marker_provider_pid(session: Mapping[str, Any]) -> int | None:
    path = Path(str(session.get("event_directory", ""))) / "app-server-ready.json"
    if not path.is_file():
        return None
    try:
        value = load_json(path)
        pid = value.get("provider_pid")
        return pid if isinstance(pid, int) else None
    except Exception:
        return None


def _prepare_codex_home(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    source_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    for name in ("auth.json", "config.toml"):
        target = path / name
        source = source_home / name
        if source.is_file() and not target.exists():
            try:
                target.symlink_to(source)
            except FileExistsError:
                pass


def _launch_handshake(root: Path, runtime: Path, session_id: str, log_path: Path,
                      codex_bin: str, invocation: Mapping[str, Any] | None = None) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    paths = _startup_paths(runtime, session_id)
    _prepare_codex_home(paths["codex_home"])
    for marker in (paths["ready"], paths["exited"], paths["control"]):
        if marker.exists():
            marker.unlink()
    command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker",
               "--root", str(root), "--codex-home", str(paths["codex_home"]),
               "--log", str(log_path), "--ready", str(paths["ready"]),
               "--exited", str(paths["exited"]), "--codex-bin", codex_bin]
    if invocation:
        for item in invocation["required_codex_invocation_arguments"]:
            command.append(f"--provider-argument={item}")
    command.extend(["--control", str(paths["control"])])
    broker = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              start_new_session=True)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if paths["ready"].is_file():
            value = load_json(paths["ready"])
            if value.get("result") != "PASS":
                raise CodexAdapterError("APP_SERVER_HANDSHAKE_FAILED", value.get("error", "Codex handshake failed"))
            return broker, value
        if broker.poll() is not None:
            raise CodexAdapterError("APP_SERVER_HANDSHAKE_FAILED", "Codex app-server broker exited before handshake")
        time.sleep(0.1)
    raise CodexAdapterError("APP_SERVER_HANDSHAKE_TIMEOUT", "Codex app-server handshake timed out")


def session_identifier(package: Mapping[str, Any], *, succession: int = 0) -> str:
    """Derive the stable Codex identity from immutable execution bindings."""
    return identifier("CODEX-SESSION", {"execution_id": package["execution_id"],
        "provider_id": package["provider_id"], "repository_identity": package["repository_identity"],
        "contract": [CONTRACT, VERSION], "succession": succession})


def _result(session: Mapping[str, Any], *, read_only: bool = True) -> dict[str, Any]:
    liveness = runtime_liveness(session)
    provider_pid = _marker_provider_pid(session) or session.get("provider_pid")
    alive = liveness["session_live"]
    state = session.get("state")
    if state in ACTIVE_STATES and not alive:
        state = "INTERRUPTED"
    return {"result": "PASS", "mission_id": session["mission_id"], "session_id": session["session_id"],
            "codex_session_id": session["session_id"], "execution_session_id": session.get("execution_session_id"),
            "provider_session_id": session.get("provider_session_id"),
            "provider_invocation_id": session.get("managed_provider_invocation_id", session.get("provider_invocation_id")),
            "lifecycle_provider_invocation_id": session.get("provider_invocation_id"),
            "execution_id": session["execution_id"], "provider_id": session["provider_id"],
            "state": state, "process_alive": alive, "pid": session.get("pid"),
            "provider_pid": provider_pid,
            "provider_process": "RUNNING" if liveness["provider_process_present"] else "STOPPED",
            "provider_liveness": liveness["provider_liveness"],
            "runtime_process_present": liveness["runtime_process_present"],
            "runtime_process_owns_codex_session": liveness["runtime_process_owns_codex_session"],
            "session_liveness": liveness["session_liveness"],
            "runtime_classification": liveness["runtime_classification"],
            "app_server_handshake": session.get("app_server_handshake", "NOT_RUN"),
            "execution_mode": session.get("execution_mode", "ZEUS_MANAGED"),
            "session_mode": session.get("session_mode", "ZEUS_MANAGED"),
            "interactive": False, "managed": True,
            "provider_mode": session.get("provider_mode", "APP_SERVER_MANAGED"),
            "transport": session.get("provider_transport", "STDIO"),
            "remote_capable": bool(session.get("remote_capable", False)),
            "endpoint_uri": session.get("remote_endpoint"),
            "readiness_result": session.get("readiness_result", "NOT_RUN"),
            "startup_diagnostics": session.get("startup_diagnostics"),
            "mission_bound": True, "execution_bound": True, "repository_bound": True,
            "authority": "PASS", "session_identity": "PASS", "provider_identity": "PASS",
            "sandbox": (session.get("scope") or {}).get("sandbox", "workspace-write"),
            "execution_monitoring": "ACTIVE" if alive else "INACTIVE",
            "mission_work_started": bool(session.get("mission_work_started")),
            "repository_work_started": bool(session.get("repository_work_started")),
            "replay": "IDEMPOTENT", "package_digest": session.get("package_digest"),
            "plan_digest": session.get("plan_digest"), "work_contract_id": session.get("work_contract_id"),
            "work_contract_digest": session.get("work_contract_digest"),
            "logs": session.get("log_path"), "artifacts": {"session": session.get("path"),
            "events": session.get("event_directory")}, "blockers": [], "read_only": read_only,
            "next_authorized_action": "CONTINUE_CONTROLLED_MISSION_WORK" if alive else
            "BEGIN_CONTROLLED_MISSION_WORK" if session.get("session_disposition") == "CURRENT" else "RESUME_CODEX_SESSION"}


def status(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    runtime = _runtime(Path(repository).resolve(), runtime_root)
    session = _existing(runtime, str(mission_id).upper())
    if not session:
        return {"result": "PASS", "mission_id": str(mission_id).upper(), "state": "NOT_STARTED",
                "mission_bound": False, "execution_bound": False, "repository_bound": False,
                "blockers": [], "read_only": True, "next_authorized_action": "START_CODEX_SESSION"}
    value = _result(session)
    try:
        value["history_reconciliation"] = reconcile_session_history(repository, mission_id,
                                                                       runtime_root=runtime, session=session)
    except CodexAdapterError as error:
        value["history_reconciliation"] = {"result": "FAIL", "history_disposition": "INDETERMINATE",
                                            "blockers": [{"code": error.code, "message": error.message}],
                                            "read_only": True}
    try:
        from scripts.lib.emp import execution_monitoring
        from scripts.lib.emp.legacy_lifecycle_reconciliation import (
            inspect as inspect_legacy, overlay as overlay_legacy,
            qualify_history as qualify_legacy_history,
        )
        transaction_path, transaction = execution_monitoring._find_transaction(runtime, session["execution_id"])
        monitoring = execution_monitoring._monitoring_record(runtime, str(transaction["execution_id"]))
        legacy = inspect_legacy(repository, runtime, transaction=transaction, monitoring=monitoring)
        value["history_reconciliation"] = qualify_legacy_history(value["history_reconciliation"], legacy)
        if value["history_reconciliation"].get("lifecycle_reconciliation") == "QUALIFIED_BY_P5_G6_ACCEPTANCE":
            value = overlay_legacy(value, legacy)
            value.update({"state": "RECONCILED_HISTORICAL", "execution_monitoring": "INACTIVE",
                          "mission_work_started": True, "repository_work_started": False})
        else:
            value.update({"state": "RECONCILED_HISTORICAL", "execution_monitoring": "INACTIVE",
                          "mission_work_started": True, "repository_work_started": False,
                          "next_authorized_action": "OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION",
                          "legacy_reconciliation": legacy})
    except Exception:
        pass
    return value


def _active_path(runtime: Path, execution_id: str) -> Path:
    directory = (runtime / ACTIVE_TRANSITION_DIR).resolve()
    path = (directory / f"{execution_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise CodexAdapterError("ACTIVE_TRANSITION_PATH_ESCAPE", "active transition path escapes runtime") from error
    return path


def _monitoring_path(runtime: Path, execution_id: str) -> Path:
    directory = (runtime / MONITORING_DIR).resolve()
    path = (directory / f"{execution_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise CodexAdapterError("MONITORING_PATH_ESCAPE", "monitoring path escapes runtime") from error
    return path


def _read_active(runtime: Path, execution_id: str) -> dict[str, Any] | None:
    path = _active_path(runtime, execution_id)
    if not path.is_file():
        return None
    value = load_json(path)
    supplied = value.get("record_digest")
    unsigned = {key: item for key, item in value.items() if key != "record_digest"}
    if supplied != digest(unsigned):
        raise CodexAdapterError("ACTIVE_TRANSITION_DIGEST_MISMATCH", "active transition digest mismatch")
    return value


def _write_projection(runtime: Path, execution_id: str, value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("record_digest", None)
    unsigned["record_digest"] = digest(unsigned)
    atomic_write(_active_path(runtime, execution_id), unsigned)
    atomic_write(_monitoring_path(runtime, execution_id), unsigned)
    return unsigned


def _control_request(control_socket: str, request: Mapping[str, Any], *, timeout: float = 15.0) -> dict[str, Any]:
    """Send one bounded JSON-RPC request through the already-bound broker."""
    if not control_socket:
        raise CodexAdapterError("CONTROL_CHANNEL_MISSING", "bound provider session has no control channel",
                                next_action="RECONCILE_PROVIDER_SESSION")
    deadline = time.monotonic() + timeout
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(max(0.1, timeout))
            client.connect(control_socket)
            client.sendall((json.dumps(dict(request), separators=(",", ":")) + "\n").encode())
            wanted = request.get("id")
            buffer = b""
            while time.monotonic() < deadline:
                chunk = client.recv(65536)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, _, buffer = buffer.partition(b"\n")
                    if not line:
                        continue
                    try:
                        value = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if value.get("id") == wanted:
                        if value.get("error"):
                            raise CodexAdapterError("PROVIDER_REQUEST_REJECTED", str(value["error"]),
                                                    next_action="RECONCILE_PROVIDER_SESSION")
                        return value
    except (OSError, TimeoutError) as error:
        raise CodexAdapterError("PROVIDER_CONTROL_FAILED", str(error),
                                next_action="RECONCILE_PROVIDER_SESSION") from error
    raise CodexAdapterError("PROVIDER_REQUEST_TIMEOUT", "provider did not acknowledge controlled mission work",
                            next_action="RECONCILE_PROVIDER_SESSION")


def begin_controlled_mission_work(repository: Path | str, mission_id: str, *, approval: bool = False,
                                  prompt: str | None = None, runtime_root: Path | str | None = None,
                                  codex_bin: str = "codex", launch: bool = True) -> dict[str, Any]:
    """Consume the bound execution-start boundary exactly once.

    The immutable P5-G5 execution-start artifacts remain unchanged.  This
    operation verifies them, uses the same provider/session identity, asks
    the bound broker to create a controlled turn, then atomically records the
    active projection consumed by P5-G6 monitoring.
    """
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission = str(mission_id).upper()
    from scripts.lib.emp.execution_start import verify as verify_execution_start
    execution = verify_execution_start(root, mission, runtime_root=runtime)
    if execution.get("result") != "PASS":
        raise _execution_verification_error(execution)
    if execution.get("mission_id") != mission:
        raise CodexAdapterError("MISSION_BINDING_MISMATCH", "execution-start mission binding differs from requested mission")
    if not execution.get("wop_id"):
        raise CodexAdapterError("WOP_BINDING_MISSING", "execution-start has no bound WOP")
    if not execution.get("execution_session_id") or not execution.get("provider_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISSING", "execution-start session bindings are incomplete")
    if not execution.get("provider_id") or not execution.get("provider_invocation_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISSING", "execution-start provider bindings are incomplete")
    if execution.get("blockers") or execution.get("approvals_required"):
        raise CodexAdapterError("EXECUTION_BLOCKED", "execution has an active blocker or outstanding approval")
    if execution.get("execution_start_state") != "READY_FOR_CONTROLLED_EXECUTION":
        raise CodexAdapterError("EXECUTION_STATE_INVALID", "execution is not at READY_FOR_CONTROLLED_EXECUTION")
    if execution.get("next_authorized_action") != "BEGIN_CONTROLLED_MISSION_WORK":
        raise CodexAdapterError("EXECUTION_NOT_READY", "execution is not at the controlled mission-work boundary")
    execution_id = execution["execution_id"]
    existing_active = _read_active(runtime, execution_id)
    if existing_active:
        return dict(existing_active, result="PASS", replay="IDEMPOTENT", duplicate_execution="NO",
                    read_only=False, mutation_applied=False)
    authority = _authority(root)
    session = _existing(runtime, mission)
    if session and session.get("execution_id") != execution_id:
        raise CodexAdapterError("EXECUTION_IDENTITY_MISMATCH", "provider session is bound to another execution")
    if session and session.get("provider_id") != execution.get("provider_id"):
        raise CodexAdapterError("PROVIDER_BINDING_MISMATCH", "provider session is bound to another provider")
    if session and session.get("execution_session_id") and session.get("execution_session_id") != execution.get("execution_session_id"):
        raise CodexAdapterError("SESSION_BINDING_MISMATCH", "provider session is bound to another execution session")
    if session and session.get("provider_session_id") and session.get("provider_session_id") != execution.get("provider_session_id"):
        raise CodexAdapterError("PROVIDER_SESSION_BINDING_MISMATCH", "provider session identity differs from execution-start binding")
    if not session:
        if not launch:
            raise CodexAdapterError("SESSION_NOT_READY", "bound provider session is not available")
        start(repository, mission, approval=approval, prompt=prompt, runtime_root=runtime, codex_bin=codex_bin)
        session = _existing(runtime, mission)
    elif not _provider_control_ready(session):
        if not launch:
            raise CodexAdapterError("SESSION_NOT_READY", "bound provider session is not live")
        resume(repository, mission, approval=approval, runtime_root=runtime, codex_bin=codex_bin)
        session = _existing(runtime, mission)
    if not session or not _provider_control_ready(session):
        raise CodexAdapterError("PROVIDER_NOT_ALIVE", "bound provider session is not live",
                                next_action="RECONCILE_PROVIDER_SESSION")
    if session.get("mission_work_started"):
        raise CodexAdapterError("MISSION_WORK_STATE_CONFLICT", "provider session already claims mission work")
    request_id = f"zeus-controlled-work-{execution_id}"
    authority = session.get("managed_authority") or {}
    authority_instruction = (
        f"Zeus authority binding: mission={mission}; transaction={execution_id}; "
        f"mission_context={authority.get('mission_context', 'BOUND')}; "
        f"transaction_context={authority.get('transaction_context', 'BOUND')}; "
        f"qualification_execution={authority.get('qualification_authority', 'NOT_GRANTED')}. "
        "Qualification execution is permitted only when explicitly AVAILABLE; qualification acceptance and closeout remain Zeus-owned. "
        "Prohibited operations: git fetch/stage/commit/push, publication, EOS synchronization, mission lifecycle advancement, and closeout."
    )
    instruction = prompt or (
        "Begin the bounded Zeus-controlled mission-work turn. Continue through "
        "deterministic successor work while the canonical controller resolves "
        "authority and no policy-required stop condition applies. Report a "
        "machine-readable result; do not approve, qualify, publish, stage, "
        "commit, push, synchronize EOS, or advance lifecycle state yourself."
    )
    instruction = authority_instruction + " " + instruction
    thread_response = _control_request(session.get("control_socket"), {
        "jsonrpc": "2.0", "id": request_id, "method": "thread/start",
        "params": {"cwd": str(root), "approvalPolicy": MANAGED_APPROVAL_POLICY, "sandbox": MANAGED_SANDBOX,
                    "instructions": instruction},
    })
    thread_result = thread_response.get("result") or {}
    thread_id = (thread_result.get("thread") or {}).get("id") or thread_result.get("threadId") or thread_result.get("id")
    if not thread_id:
        raise CodexAdapterError("THREAD_ID_MISSING", "provider did not return a controlled thread identity",
                                next_action="RECONCILE_PROVIDER_SESSION")
    _control_request(session.get("control_socket"), {
        "jsonrpc": "2.0", "id": f"{request_id}-turn", "method": "turn/start",
        "params": {"threadId": thread_id, "input": [{"type": "text", "text": instruction}]},
    })
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    active = {
        "schema_version": 1, "record_type": "BOUND_ACTIVE_EXECUTION", "result": "PASS",
        "mission_id": mission, "wop_id": execution.get("wop_id"), "execution_id": execution_id,
        "execution_session_id": execution.get("execution_session_id"), "provider_session_id": execution.get("provider_session_id"),
        "provider_id": execution.get("provider_id"), "provider_invocation_id": execution.get("provider_invocation_id"),
        "session_id": session["session_id"], "runtime_transaction_id": identifier("ACTIVE-EXECUTION", {"execution_id": execution_id, "session_id": session["session_id"]}),
        "authority": authority, "execution_state": "EXECUTING", "execution_monitoring_active": True,
        "mission_work_started": True, "repository_work_started": False,
        "provider_process_state": "RUNNING", "provider_liveness": "ALIVE", "execution_liveness": "ALIVE",
        "session_state": "ACTIVE", "current_work_position": "P5-G6:CONTROLLED_MISSION_WORK",
        "current_gate": "P5-G6", "current_gate_name": "Execution Monitoring Foundation",
        "progress_state": "ACTIVE", "completed_work_units": [], "active_work_units": ["CONTROLLED_MISSION_WORK"],
        "remaining_work_units": [], "blockers": [], "approvals_required": [],
        "last_progress_event": "MISSION_WORK_STARTED", "last_progress_timestamp": now,
        "next_authorized_action": "CONTINUE_CONTROLLED_MISSION_WORK", "source_records": {
            "execution_start": execution.get("artifacts", {}).get("execution_start_transaction", {}).get("path"),
            "provider_session": session.get("path"), "provider_invocation_id": execution.get("provider_invocation_id"),
        }, "source_digests": {"execution_start_provenance_baseline": execution.get("execution_start_provenance_baseline")},
        "created_at": now,
    }
    session = dict(session, state="ACTIVE", mission_work_started=True, repository_work_started=False,
                   execution_monitoring_active=True, active_execution_id=execution_id,
                   last_progress_event="MISSION_WORK_STARTED", last_progress_timestamp=now)
    projection = _write_projection(runtime, execution_id, active)
    try:
        saved_session = _save(runtime, session)
    except Exception as error:
        for path in (_active_path(runtime, execution_id), _monitoring_path(runtime, execution_id)):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise CodexAdapterError("ACTIVE_STATE_COMMIT_FAILED", str(error),
                                next_action="RECONCILE_EXECUTION_STATE") from error
    _append_event(runtime, session["session_id"], "MISSION_WORK_STARTED", {
        "execution_id": execution_id, "wop_id": execution.get("wop_id"), "current_work_position": active["current_work_position"]})
    return dict(projection, result="PASS", session_id=saved_session["session_id"], replay="APPLIED",
                duplicate_execution="NO", mutation_applied=True, read_only=False)


def start(repository: Path | str, mission_id: str, *, approval: bool = False,
           prompt: str | None = None, runtime_root: Path | str | None = None,
           codex_bin: str = "codex", launch: bool = True, _resume: bool = False,
           work_contract: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission_id = str(mission_id).upper()
    package = _package(root, mission_id, runtime)
    invocation = resolve_provider_invocation_contract(root, work_contract=work_contract, codex_bin=codex_bin,
                                                       lifecycle_binding=package, mission_id=mission_id,
                                                       transaction_id=package["execution_id"])
    existing = _existing(runtime, mission_id)
    all_mission_sessions = _all_sessions(runtime, mission_id)
    session_id = (existing.get("session_id") if existing and existing.get("session_disposition") == "CURRENT"
                  else session_identifier(package, succession=len(all_mission_sessions)))
    if existing:
        if existing.get("session_id") != session_id or existing.get("package_digest") != package["package_digest"]:
            raise CodexAdapterError("ACTIVE_SESSION_PROTECTION", "an active managed session owns a different immutable lifecycle binding",
                                    details={"active_session_id": existing.get("session_id")})
        if (existing.get("work_contract_digest") != invocation["work_contract_digest"]
                or existing.get("plan_digest") != invocation["plan_digest"]):
            raise CodexAdapterError("ACTIVE_SESSION_PROTECTION", "an active managed session owns a different immutable contract or plan",
                                    details={"active_session_id": existing.get("session_id")})
        if _provider_control_ready(existing):
            return _result(existing, read_only=False) | {"duplicate_codex_session": "IDEMPOTENT"}
        if not _resume:
            raise CodexAdapterError("SESSION_INTERRUPTED", "existing Codex session is not live; use Zeus resume")
        log_path = Path(existing["log_path"])
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, invocation["codex_binary"], invocation)
        resumed = dict(existing, state="READY", pid=process.pid, provider_pid=diagnostics["provider_pid"],
                       command=diagnostics["command"], app_server_handshake="PASS",
                       startup_diagnostics=diagnostics["environment"],
                       control_socket=diagnostics.get("control_socket"),
                       remote_endpoint=diagnostics.get("remote_endpoint"),
                       execution_mode="ZEUS_MANAGED", session_mode="ZEUS_MANAGED",
                       provider_mode="APP_SERVER_MANAGED", provider_transport="STDIO",
                       remote_capable=False, readiness_result="PASS",
                       mission_work_started=False, repository_work_started=False)
        _append_event(runtime, session_id, "CODEX_SESSION_RESUMED", {"pid": process.pid,
                                                                       "provider_pid": diagnostics["provider_pid"]})
        _append_event(runtime, session_id, "APP_SERVER_HANDSHAKE_COMPLETED", {"provider_pid": diagnostics["provider_pid"]})
        saved = _save(runtime, resumed)
        return _result(saved, read_only=False) | {"duplicate_codex_session": "RESUMED"}
    if package["provider_id"] != PROVIDER_ID:
        raise CodexAdapterError("PROVIDER_SUBSTITUTION", "unsupported provider identity")
    log_path = runtime / LOG_DIR / f"{session_id}.jsonl"; log_path.parent.mkdir(parents=True, exist_ok=True)
    event_directory = runtime / EVENT_DIR / session_id
    command = invocation["command"]
    session = {"schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
               **package, "session_id": session_id, "state": "CREATED", "pid": None,
               "command": command, "resolved_invocation_plan": invocation,
               "plan_digest": invocation["plan_digest"], "work_contract": invocation["work_contract"],
               "work_contract_id": invocation["work_contract_id"],
               "work_contract_digest": invocation["work_contract_digest"],
               "managed_provider_invocation_id": identifier("MANAGED-PROVIDER-INVOCATION", {
                   "session_id": session_id, "plan_digest": invocation["plan_digest"]}),
               "log_path": str(log_path), "event_directory": str(event_directory),
               "mission_work_started": False, "repository_work_started": False,
               "started_by": "zeus", "operator_approval": False, "path": str(_session_path(runtime, session_id)),
               "app_server_handshake": "NOT_RUN", "startup_diagnostics": None,
               "execution_mode": "ZEUS_MANAGED", "session_mode": "ZEUS_MANAGED",
               "provider_mode": "APP_SERVER_MANAGED", "provider_transport": "STDIO",
               "remote_capable": False, "readiness_result": "NOT_RUN",
               "managed_authority": {key: invocation.get(key) for key in (
                   "mission_context", "transaction_context", "qualification_authority",
                   "requested_operations", "prohibited_operations")}}
    _append_event(runtime, session_id, "CODEX_SESSION_CREATED", {"pid": None, "authority": package["authority"]})
    _save(runtime, session)
    try:
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, invocation["codex_binary"], invocation)
    except CodexAdapterError as error:
        session["state"] = "FAILED"; session["failure"] = error.message
        _append_event(runtime, session_id, "CODEX_SESSION_FAILED", {"code": error.code, "message": error.message})
        _save(runtime, session)
        raise
    session["state"] = "READY"; session["pid"] = process.pid
    session["provider_pid"] = diagnostics["provider_pid"]
    session["command"] = diagnostics["command"]
    session["app_server_handshake"] = "PASS"
    session["startup_diagnostics"] = diagnostics["environment"]
    session["control_socket"] = diagnostics.get("control_socket")
    session["remote_endpoint"] = diagnostics.get("remote_endpoint")
    session["execution_mode"] = "ZEUS_MANAGED"; session["session_mode"] = "ZEUS_MANAGED"
    session["provider_mode"] = "APP_SERVER_MANAGED"; session["provider_transport"] = "STDIO"
    session["remote_capable"] = False; session["readiness_result"] = "PASS"
    session["mission_work_started"] = False; session["repository_work_started"] = False
    _append_event(runtime, session_id, "CODEX_PROCESS_BOUND", {"pid": process.pid,
                                                               "provider_pid": diagnostics["provider_pid"]})
    _append_event(runtime, session_id, "APP_SERVER_HANDSHAKE_COMPLETED", {"provider_pid": diagnostics["provider_pid"]})
    saved = _save(runtime, session)
    return _result(saved, read_only=False) | {"duplicate_codex_session": "NEW"}


def resume(repository: Path | str, mission_id: str, *, approval: bool = False,
           runtime_root: Path | str | None = None, codex_bin: str = "codex",
           work_contract: Path | str | None = None) -> dict[str, Any]:
    runtime = _runtime(Path(repository).resolve(), runtime_root); mission_id = str(mission_id).upper(); session = _existing(runtime, mission_id)
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    if _provider_control_ready(session):
        return _result(session, read_only=False) | {"duplicate_codex_session": "IDEMPOTENT"}
    return start(repository, mission_id, approval=approval, runtime_root=runtime, codex_bin=codex_bin,
                 work_contract=work_contract,
                 prompt=(
                     "Resume the Zeus-bound controlled mission-work session. "
                     "Reconcile prior state before any work and continue from "
                     "the first incomplete canonical transition. Stop only "
                     "when Zeus resolves a genuine policy, authority, "
                     "qualification, execution, or protected-operation boundary."
                 ), _resume=True)


def stop(repository: Path | str, mission_id: str, *, approval: bool = False,
         runtime_root: Path | str | None = None) -> dict[str, Any]:
    runtime = _runtime(Path(repository).resolve(), runtime_root); session = _existing(runtime, str(mission_id).upper())
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    if _process_alive(session.get("pid")):
        try:
            os.killpg(session["pid"], signal.SIGTERM)
        except OSError as error:
            raise CodexAdapterError("SESSION_STOP_FAILED", str(error)) from error
    session = dict(session); session["state"] = "RECONCILED_HISTORICAL"; session["stopped_by"] = "zeus"
    session["session_disposition"] = "HISTORICAL"
    _append_event(runtime, session["session_id"], "CODEX_SESSION_STOPPED", {"pid": session.get("pid")})
    saved = _save(runtime, session)
    return _result(saved, read_only=False)


def logs(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = status(repository, mission_id, runtime_root=runtime_root)
    if value.get("state") == "NOT_STARTED":
        return value | {"logs": None}
    path = Path(value["logs"]); value["log_content"] = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    return value


def artifacts(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    return status(repository, mission_id, runtime_root=runtime_root)


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Read-only adapter verification, including the immutable package binding."""
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    session = _existing(runtime, str(mission_id).upper())
    if not session:
        return status(root, mission_id, runtime_root=runtime)
    package = _package(root, str(mission_id).upper(), runtime)
    if package["package_digest"] != session.get("package_digest"):
        raise CodexAdapterError("SESSION_INPUT_MISMATCH", "current execution package differs from Codex session binding")
    return _result(session)

# --- CR46 ZO-059 / ZO-060: provider-facing read-only projections ---
def gate_execution_provenance_projection(
    gate_id: str,
    **context: Any,
) -> dict[str, Any]:
    from scripts.lib.emp.stage1_runtime import (
        classify_gate_execution_provenance,
    )

    return {
        **classify_gate_execution_provenance(
            gate_id,
            **context,
        ),
        "owner_surface": "codex_adapter",
    }


def immutable_commit_dependency_projection(
    root: Path | str,
    commit: str,
    *,
    entrypoints: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    from scripts.lib.emp.publication_candidate_authority import (
        qualify_immutable_commit_dependency_closure,
    )

    return {
        **qualify_immutable_commit_dependency_closure(
            root,
            commit,
            entrypoints=entrypoints,
        ),
        "owner_surface": "codex_adapter",
    }
