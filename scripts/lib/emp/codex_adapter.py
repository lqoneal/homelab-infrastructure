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
import subprocess
import time
import hashlib
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.mission_admission_boundary import _digest
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_identity import resolve as resolve_repository
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.eos import operational_beta


CONTRACT = "ZEUS-P5-G6-CODEX-ADAPTER"
VERSION = "1"
PROVIDER_ID = "zeus-local-loneal-01"
ADAPTER_ID = "zeus-codex-process-v1"
STAGE_DIR = "codex-sessions"
LOG_DIR = "codex-logs"
EVENT_DIR = "codex-events"
CODEX_HOME_DIR = "codex-home"
ACTIVE_STATES = {"ACTIVE", "RESUMED"}
STOPPED_STATES = {"INTERRUPTED", "STOPPED", "FAILED"}


class CodexAdapterError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code, self.message, self.next_action = code, message, next_action
        super().__init__(message)


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
        raise CodexAdapterError("EXECUTION_START_FAILURE", "execution-start verification failed")
    if execution.get("next_authorized_action") != "BEGIN_CONTROLLED_MISSION_WORK":
        raise CodexAdapterError("EXECUTION_NOT_READY", "execution is not at the controlled mission-work boundary")
    if execution.get("mission_work_started"):
        raise CodexAdapterError("MISSION_WORK_ALREADY_STARTED", "mission work is already active")
    authority = _authority(root)
    identity = resolve_repository(root)
    execution_id = execution["execution_id"]
    package = {
        "schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
        "mission_id": mission_id, "execution_id": execution_id,
        "execution_session_id": execution["execution_session_id"],
        "provider_id": execution["provider_id"], "provider_invocation_id": execution["provider_invocation_id"],
        "provider_session_id": execution.get("provider_session_id"),
        "repository": str(root), "repository_identity": identity["repository_identity"],
        "repository_id": identity["repository_id"], "repository_fingerprint": identity["repository_fingerprint"],
        "current_published_baseline": execution["current_published_baseline"],
        "execution_start_provenance_baseline": execution.get("execution_start_provenance_baseline"),
        "execution_start_baseline_relationship": execution.get("execution_start_baseline_relationship"),
        "execution_package_digest": None, "execution_authority_digest": None,
        "scope": {"owner": "Zeus", "mission_work_started": True,
                  "repository_work_started": True, "operator_approval_required": True,
                  "stop_boundary": "FIRST_CONTROLLED_EXECUTION_BOUNDARY"},
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
    if len(matches) > 1:
        raise CodexAdapterError("SESSION_CARDINALITY_CONFLICT", "more than one Codex session belongs to the mission")
    return matches[0] if matches else None


def _process_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


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
    source_home = Path.home() / ".codex"
    for name in ("auth.json", "config.toml"):
        target = path / name
        source = source_home / name
        if source.is_file() and not target.exists():
            try:
                target.symlink_to(source)
            except FileExistsError:
                pass


def _launch_handshake(root: Path, runtime: Path, session_id: str, log_path: Path,
                      codex_bin: str) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    paths = _startup_paths(runtime, session_id)
    _prepare_codex_home(paths["codex_home"])
    for marker in (paths["ready"], paths["exited"], paths["control"]):
        if marker.exists():
            marker.unlink()
    command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker",
               "--root", str(root), "--codex-home", str(paths["codex_home"]),
               "--log", str(log_path), "--ready", str(paths["ready"]),
               "--exited", str(paths["exited"]), "--codex-bin", codex_bin]
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


def session_identifier(package: Mapping[str, Any]) -> str:
    """Derive the stable Codex identity from immutable execution bindings."""
    return identifier("CODEX-SESSION", {"execution_id": package["execution_id"],
        "provider_id": package["provider_id"], "repository_identity": package["repository_identity"],
        "contract": [CONTRACT, VERSION]})


def _result(session: Mapping[str, Any], *, read_only: bool = True) -> dict[str, Any]:
    provider_pid = _marker_provider_pid(session) or session.get("provider_pid")
    alive = _process_alive(session.get("pid")) and _process_alive(provider_pid)
    state = session.get("state")
    if state in ACTIVE_STATES and not alive:
        state = "INTERRUPTED"
    return {"result": "PASS", "mission_id": session["mission_id"], "session_id": session["session_id"],
            "execution_id": session["execution_id"], "provider_id": session["provider_id"],
            "state": state, "process_alive": alive, "pid": session.get("pid"),
            "provider_pid": provider_pid,
            "provider_process": "RUNNING" if _process_alive(provider_pid) else "STOPPED",
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
            "execution_monitoring": "ACTIVE" if alive else "INACTIVE",
            "mission_work_started": bool(session.get("mission_work_started")),
            "repository_work_started": bool(session.get("repository_work_started")),
            "replay": "IDEMPOTENT", "package_digest": session.get("package_digest"),
            "logs": session.get("log_path"), "artifacts": {"session": session.get("path"),
            "events": session.get("event_directory")}, "blockers": [], "read_only": read_only,
            "next_authorized_action": "CONTINUE_CONTROLLED_MISSION_WORK" if alive else "RESUME_CODEX_SESSION"}


def status(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    runtime = _runtime(Path(repository).resolve(), runtime_root)
    session = _existing(runtime, str(mission_id).upper())
    if not session:
        return {"result": "PASS", "mission_id": str(mission_id).upper(), "state": "NOT_STARTED",
                "mission_bound": False, "execution_bound": False, "repository_bound": False,
                "blockers": [], "read_only": True, "next_authorized_action": "START_CODEX_SESSION"}
    return _result(session)


def start(repository: Path | str, mission_id: str, *, approval: bool = False,
           prompt: str | None = None, runtime_root: Path | str | None = None,
           codex_bin: str = "codex", launch: bool = True, _resume: bool = False) -> dict[str, Any]:
    if not approval:
        raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED", "operator approval is required before Codex launch", next_action="APPROVE_AND_START_CODEX")
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission_id = str(mission_id).upper()
    package = _package(root, mission_id, runtime)
    existing = _existing(runtime, mission_id)
    session_id = session_identifier(package)
    if existing:
        if existing.get("session_id") != session_id or existing.get("package_digest") != package["package_digest"]:
            raise CodexAdapterError("SESSION_INPUT_MISMATCH", "existing Codex session has a different immutable binding")
        if _process_alive(existing.get("pid")) and _process_alive(existing.get("provider_pid") or _marker_provider_pid(existing)):
            return _result(existing, read_only=False) | {"duplicate_codex_session": "IDEMPOTENT"}
        if not _resume:
            raise CodexAdapterError("SESSION_INTERRUPTED", "existing Codex session is not live; use Zeus resume")
        log_path = Path(existing["log_path"])
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, codex_bin)
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
    command = [codex_bin, "app-server", "--stdio"]
    session = {"schema_version": 1, "contract": {"id": CONTRACT, "version": VERSION},
               **package, "session_id": session_id, "state": "CREATED", "pid": None,
               "command": command, "log_path": str(log_path), "event_directory": str(event_directory),
               "mission_work_started": False, "repository_work_started": False,
               "started_by": "zeus", "operator_approval": True, "path": str(_session_path(runtime, session_id)),
               "app_server_handshake": "NOT_RUN", "startup_diagnostics": None,
               "execution_mode": "ZEUS_MANAGED", "session_mode": "ZEUS_MANAGED",
               "provider_mode": "APP_SERVER_MANAGED", "provider_transport": "STDIO",
               "remote_capable": False, "readiness_result": "NOT_RUN"}
    _append_event(runtime, session_id, "CODEX_SESSION_CREATED", {"pid": None, "authority": package["authority"]})
    _save(runtime, session)
    try:
        process, diagnostics = _launch_handshake(root, runtime, session_id, log_path, codex_bin)
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
           runtime_root: Path | str | None = None, codex_bin: str = "codex") -> dict[str, Any]:
    if not approval:
        raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED", "operator approval is required before resume")
    runtime = _runtime(Path(repository).resolve(), runtime_root); mission_id = str(mission_id).upper(); session = _existing(runtime, mission_id)
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    if _process_alive(session.get("pid")) and _process_alive(session.get("provider_pid")):
        return _result(session, read_only=False) | {"duplicate_codex_session": "IDEMPOTENT"}
    return start(repository, mission_id, approval=approval, runtime_root=runtime, codex_bin=codex_bin,
                 prompt="Resume the Zeus-bound controlled mission-work session. Reconcile prior state before any work; stop at the operator boundary.", _resume=True)


def stop(repository: Path | str, mission_id: str, *, approval: bool = False,
         runtime_root: Path | str | None = None) -> dict[str, Any]:
    if not approval:
        raise CodexAdapterError("OPERATOR_APPROVAL_REQUIRED", "operator approval is required before stop")
    runtime = _runtime(Path(repository).resolve(), runtime_root); session = _existing(runtime, str(mission_id).upper())
    if not session:
        raise CodexAdapterError("SESSION_NOT_FOUND", "no Codex session belongs to mission")
    if _process_alive(session.get("pid")):
        try:
            os.killpg(session["pid"], signal.SIGTERM)
        except OSError as error:
            raise CodexAdapterError("SESSION_STOP_FAILED", str(error)) from error
    session = dict(session); session["state"] = "STOPPED"; session["stopped_by"] = "zeus"
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
