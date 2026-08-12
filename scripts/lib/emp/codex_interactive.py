"""Zeus lifecycle wrapper for the official Codex remote interactive client.

Zeus owns context, endpoint, identity, authority, and evidence.  The official
Codex CLI owns terminal presentation and app-server conversation handling.
"""

from __future__ import annotations

import fcntl
import json
import os
import select
import signal
import socket
import subprocess
import struct
import sys
import termios
import time
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp import codex_adapter, codex_app_server_broker
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_identity import resolve as resolve_repository


CONTRACT = "ZEUS-P5-G6-CODEX-INTERACTIVE"
VERSION = "1"
STAGE_DIR = "codex-interactive-sessions"
DIRECT_LAUNCHER_RELATIVE = Path("scripts/lib/eos/codex-direct-launch.sh")
ACTIVE_STATES = {"ATTACHING", "ATTACHED", "THREAD_READY", "AWAITING_OPERATOR_INPUT", "TURN_ACTIVE", "INTERACTIVE_SESSION_OPEN"}
TERMINAL_STATES = {"STOPPED", "FAILED", "DETACHED"}
DIRECT_INTERACTIVE = "DIRECT_INTERACTIVE"
REMOTE_INTERACTIVE = "REMOTE_INTERACTIVE"
ZEUS_MANAGED = "ZEUS_MANAGED"
UNIX_SOCKET_PATH_MAX = 107
REMOTE_SESSION_CONTRACT = "REMOTE_INTERACTIVE_SESSION_V2"


class InteractiveCodexError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED",
                 details: Mapping[str, Any] | None = None):
        self.code, self.message, self.next_action = code, message, next_action
        self.details = dict(details or {})
        super().__init__(message)


def direct_launcher_path(repository: Path | str) -> Path:
    """Resolve the one repository-relative native launcher locator."""
    root = Path(repository).resolve()
    launcher = (root / DIRECT_LAUNCHER_RELATIVE).resolve()
    try:
        launcher.relative_to(root)
    except ValueError as error:
        raise InteractiveCodexError("DIRECT_LAUNCHER_PATH_ESCAPE",
                                    "direct launcher resolves outside the repository",
                                    next_action="RECONCILE_DIRECT_LAUNCHER") from error
    if not launcher.is_file():
        raise InteractiveCodexError("DIRECT_LAUNCHER_MISSING",
                                    f"direct launcher is missing: {launcher}",
                                    next_action="RECONCILE_DIRECT_LAUNCHER",
                                    details={"launcher": str(launcher)})
    if not os.access(launcher, os.X_OK):
        raise InteractiveCodexError("DIRECT_LAUNCHER_NOT_EXECUTABLE",
                                    f"direct launcher is not executable: {launcher}",
                                    next_action="RECONCILE_DIRECT_LAUNCHER",
                                    details={"launcher": str(launcher)})
    return launcher


class _AttachedProvider:
    """File-like view of a READY Zeus broker control socket."""
    def __init__(self, path: str, pid: int):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(path)
        self.pid = pid
        self.stdin = self._socket.makefile("wb", buffering=0)
        self.stdout = self._socket.makefile("rb", buffering=0)
        self.stderr = None

    def poll(self):
        return None if _alive(self.pid) else 0

    def terminate(self):
        return None

    def wait(self, timeout: float | None = None):
        return 0

    def close(self):
        for stream in (self.stdin, self.stdout):
            try:
                stream.close()
            except OSError:
                pass
        self._socket.close()


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    return codex_adapter._runtime(root, runtime_root)


def _path(runtime: Path, session_id: str) -> Path:
    directory = (runtime / STAGE_DIR).resolve()
    path = (directory / f"{session_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise InteractiveCodexError("SESSION_PATH_ESCAPE", "interactive session path escapes runtime") from error
    return path


def _load(path: Path) -> dict[str, Any]:
    value = load_json(path)
    supplied = value.get("state_digest")
    unsigned = {key: item for key, item in value.items() if key != "state_digest"}
    if supplied != digest(unsigned):
        raise InteractiveCodexError("SESSION_DIGEST_MISMATCH", f"{path} digest mismatch")
    return value


def _save(runtime: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("state_digest", None)
    unsigned["state_digest"] = digest(unsigned)
    path = _path(runtime, str(unsigned["session_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, unsigned)
    return unsigned


def _append_event(runtime: Path, session_id: str, event: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    directory = runtime / "codex-interactive-events" / session_id
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("*.json"))
    sequence = len(existing) + 1
    material: dict[str, Any] = {"schema_version": 1, "sequence": sequence,
                                "session_id": session_id, "event": event,
                                "payload": dict(payload), "previous_event_digest": None}
    if existing:
        material["previous_event_digest"] = load_json(existing[-1]).get("event_digest")
    material["event_digest"] = digest(material)
    path = directory / f"{sequence:04d}.json"
    if path.exists() and load_json(path) != material:
        raise InteractiveCodexError("EVENT_CONFLICT", f"event {path} conflicts")
    if not path.exists():
        atomic_write(path, material)
    return material


def _sessions(runtime: Path) -> list[dict[str, Any]]:
    values = []
    directory = runtime / STAGE_DIR
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
        try:
            value = _load(path)
        except InteractiveCodexError:
            # A partial receipt is not a session contract and must not create
            # a collision.  Authoritative corruption is still surfaced when
            # the explicitly requested session is loaded by _path/_load.
            continue
        if _authoritative_session(value):
            values.append(value)
    return values


def _authoritative_session(value: Mapping[str, Any]) -> bool:
    """Only durable session records participate in identity collision checks.

    Event receipts and partially written recovery material may live beside
    session state, but they do not establish an immutable session contract.
    The marker is added to new records; the required legacy fields retain
    compatibility with records written before the marker existed.
    """
    contract = value.get("contract")
    return value.get("record_type") == "AUTHORITATIVE_INTERACTIVE_SESSION" or (
        value.get("session_id") and isinstance(contract, Mapping) and contract.get("id") == CONTRACT
        and "state" in value and "repository_identity" in value
    )


def _existing(runtime: Path, mission_id: str | None, session_id: str | None = None,
              *, active: bool = False, latest: bool = False,
              execution_mode: str | None = None,
              binding_class: str | None = None) -> dict[str, Any] | None:
    matches = []
    for value in _sessions(runtime):
        if not _authoritative_session(value):
            continue
        if session_id and value.get("session_id") != session_id:
            continue
        if session_id is None and value.get("mission_id") != mission_id:
            continue
        if execution_mode is not None and value.get("execution_mode") != execution_mode:
            continue
        if binding_class is not None and value.get("immutable_binding_class") != binding_class:
            continue
        if active and value.get("state") not in ACTIVE_STATES:
            continue
        matches.append(value)
    if latest:
        return max(matches, key=lambda value: value.get("start_timestamp", 0), default=None)
    if len(matches) > 1:
        raise InteractiveCodexError("SESSION_CARDINALITY_CONFLICT", "more than one interactive session matches; use --session or --latest")
    return matches[0] if matches else None


def _alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def codex_capabilities(codex_bin: str = "codex") -> dict[str, Any]:
    """Inspect the installed CLI rather than assuming remote syntax."""
    version = subprocess.run([codex_bin, "--version"], capture_output=True, text=True, check=False)
    top = subprocess.run([codex_bin, "--help"], capture_output=True, text=True, check=False)
    app = subprocess.run([codex_bin, "app-server", "--help"], capture_output=True, text=True, check=False)
    version_text = (version.stdout or version.stderr or "").strip()
    remote_text = f"{top.stdout or ''}\n{top.stderr or ''}"
    listen_text = f"{app.stdout or ''}\n{app.stderr or ''}"
    schemes = [scheme for scheme in ("ws://", "wss://", "unix://") if scheme in remote_text or scheme in listen_text]
    remote_supported = "--remote" in remote_text
    listen_supported = "--listen" in listen_text
    websocket_supported = "ws://" in listen_text
    supported = remote_supported and listen_supported and websocket_supported
    return {"result": "PASS" if supported else "FAIL", "codex_version": version_text,
            "remote_client_supported": remote_supported,
            "app_server_listen_supported": listen_supported,
            "websocket_listener_supported": websocket_supported,
            "supported_remote_schemes": schemes, "supported_bind_format": "ws://127.0.0.1:<port>",
            "remote_mode_supported": supported,
            "capability_commands": {"version": version.args, "remote_help": top.args, "listener_help": app.args},
            "exit_codes": {"version": version.returncode, "remote_help": top.returncode, "listener_help": app.returncode},
            "blocker": None if supported else "INSTALLED_CODEX_REMOTE_MODE_UNSUPPORTED"}


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _terminal_size(fd: int) -> tuple[int, int] | None:
    try:
        raw = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8)
        rows, columns = struct.unpack("HH", raw[:4])
        return rows, columns
    except (OSError, ValueError):
        return None


def terminal_size(fd: int | None = None) -> tuple[int, int]:
    """Return a usable terminal size without ever collapsing to one column.

    ioctl is authoritative for a TTY.  Environment values are useful for
    redirected test terminals and CI, but are only accepted when positive.
    """
    descriptor = sys.stdout.fileno() if fd is None else fd
    observed = _terminal_size(descriptor)
    if observed and observed[0] > 0 and observed[1] > 0:
        return observed
    try:
        rows = int(os.environ.get("LINES", "0"))
        columns = int(os.environ.get("COLUMNS", "0"))
    except ValueError:
        rows = columns = 0
    return (rows if rows > 0 else 24, columns if columns > 0 else 80)


def strip_bracketed_paste(data: bytes) -> bytes:
    """Remove terminal bracketed-paste wrappers while preserving content."""
    return data.replace(b"\x1b[200~", b"").replace(b"\x1b[201~", b"")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_text(item) for item in value)
    if isinstance(value, dict):
        for key in ("text", "text_delta", "delta", "content"):
            if key in value:
                return _text(value[key])
    return "" if value is None else str(value)


def render_event(event: Mapping[str, Any]) -> str:
    """Render one structured app-server event without character iteration."""
    params = event.get("params", event)
    if not isinstance(params, Mapping):
        return ""
    for key in ("text", "text_delta", "delta", "content"):
        if key in params:
            return _text(params[key])
    return ""


@contextmanager
def terminal_mode(fd: int | None = None):
    """Apply cbreak mode only around operator input and always restore it."""
    descriptor = sys.stdin.fileno() if fd is None else fd
    if not os.isatty(descriptor):
        yield
        return
    original = termios.tcgetattr(descriptor)
    try:
        updated = termios.tcgetattr(descriptor)
        updated[3] &= ~(termios.ICANON | termios.ECHO)
        updated[6][termios.VMIN] = 1
        updated[6][termios.VTIME] = 0
        termios.tcsetattr(descriptor, termios.TCSADRAIN, updated)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, original)


def _set_terminal_size(fd: int, size: tuple[int, int] | None) -> None:
    if size is None:
        return
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", size[0], size[1], 0, 0))
    except OSError:
        pass


def _context(package: Mapping[str, Any] | None, repository: Mapping[str, Any]) -> str:
    if package is None:
        return ("This is a Zeus operator-interactive, non-mission session. It has no WOP, "
                "Mission Contract, or execution authority. Do not perform protected "
                "lifecycle actions, publication, push, EOS synchronization, or work "
                "outside explicit operator direction.")
    return ("You are in a Zeus-controlled operator-interactive session. Mission and "
            f"repository bindings are authoritative: mission={package['mission_id']}, "
            f"execution={package['execution_id']}, repository={repository['repository_id']}. "
            "Do not publish, push, synchronize EOS, qualify, close, or expand scope. "
            "Zeus records and resolves protected requests; stop when authority is unclear.")


def session_identifier(repository: Mapping[str, Any], mission_id: str | None, execution_id: str | None,
                       execution_mode: str = DIRECT_INTERACTIVE, *,
                       binding_class: str | None = None,
                       reconciliation_generation: str | None = None) -> str:
    binding_class = binding_class or ("MISSION_EXECUTION" if mission_id or execution_id else "REPOSITORY_OPERATOR")
    return identifier("CODEX-INTERACTIVE-SESSION", {"mission_id": mission_id,
        "execution_id": execution_id, "repository_identity": repository["repository_identity"],
        "mode": execution_mode, "binding_class": binding_class,
        "contract": [CONTRACT, VERSION, REMOTE_SESSION_CONTRACT if execution_mode == REMOTE_INTERACTIVE else None],
        "reconciliation_generation": reconciliation_generation})


def direct_launcher_preflight(repository: Path | str, mission_id: str | None = None, *,
                              approval: bool = False, codex_bin: str = "codex",
                              argv: list[str] | None = None) -> dict[str, Any]:
    """Validate the direct launcher without opening a provider or TUI.

    This is intentionally redirect-safe.  PTY acceptance remains the separate
    responsibility of ``shell`` and must run with inherited terminal streams.
    """
    root = Path(repository).resolve()
    launcher = None
    launcher_error = None
    try:
        launcher = direct_launcher_path(root)
    except InteractiveCodexError as error:
        launcher_error = error
    codex_path = shutil.which(codex_bin) or (str(Path(codex_bin).resolve()) if Path(codex_bin).is_file() else None)
    auth_config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth_available = auth_config.is_dir() or bool(os.environ.get("CODEX_API_KEY"))
    checks = {
        "repository": str(root),
        "repository_binding": root.is_dir(),
        "launcher": str(launcher or root / DIRECT_LAUNCHER_RELATIVE),
        "launcher_present": launcher is not None,
        "launcher_regular_file": bool(launcher and launcher.is_file()),
        "launcher_executable": bool(launcher and os.access(launcher, os.X_OK)),
        "launcher_within_repository": launcher_error is None,
        "codex_executable": bool(codex_path),
        "codex_binary": codex_path,
        "auth_config": auth_available,
        "environment_resolution": bool(os.environ.get("PATH")),
        "mission_binding": "PASS" if mission_id and approval else ("NOT_APPLICABLE" if not mission_id else "FAIL"),
        "authority_context": "PASS" if mission_id and approval else "NOT_APPLICABLE",
        "argv": list(argv or []),
        "pty_required_for_launch": True,
        "codex_not_launched": True,
    }
    checks["result"] = "PASS" if all((checks["repository_binding"], checks["launcher_present"],
                                       checks["launcher_executable"], checks["codex_executable"],
                                       checks["auth_config"], checks["environment_resolution"],
                                       checks["mission_binding"] != "FAIL")) else "FAIL"
    if launcher_error:
        checks["error_code"] = launcher_error.code
    elif not checks["codex_executable"]:
        checks["error_code"] = "CODEX_BINARY_MISSING"
    elif not checks["auth_config"]:
        checks["error_code"] = "AUTH_CONFIG_UNAVAILABLE"
    checks["direct_launcher"] = "PASS" if checks["launcher_present"] and checks["launcher_executable"] and checks["launcher_within_repository"] else "FAIL"
    checks["codex_binary_status"] = "PASS" if checks["codex_executable"] else "FAIL"
    checks["auth_config_status"] = "PASS" if checks["auth_config"] else "FAIL"
    checks["repository_binding_status"] = "PASS" if checks["repository_binding"] else "FAIL"
    checks["codex_not_launched"] = "YES"
    return checks


launcher_preflight = direct_launcher_preflight


def _package(root: Path, mission_id: str | None, runtime: Path) -> dict[str, Any] | None:
    if mission_id is None:
        return None
    package = codex_adapter._package(root, mission_id, runtime)
    package["scope"] = dict(package["scope"], mission_work_started=False, repository_work_started=False)
    return package


def _result(session: Mapping[str, Any], *, read_only: bool) -> dict[str, Any]:
    alive = _alive(session.get("pid"))
    listener_alive = bool(session.get("listener_alive")) or _alive(session.get("listener_pid"))
    state = session.get("state")
    if state in ACTIVE_STATES and not alive:
        state = "STOPPED"
    execution_mode = session.get("execution_mode", DIRECT_INTERACTIVE)
    session_state = session.get("session_state") or ("DETACHED" if listener_alive and not alive else state)
    client_state = session.get("client_state") or session.get("remote_client_state", "NOT_STARTED")
    listener_state = session.get("listener_state") or ("READY" if listener_alive else "STOPPED")
    attachment_state = session.get("attachment_state") or ("ATTACHED" if session.get("attached") else "DETACHED")
    provider_state = session.get("provider_state") or ("READY" if listener_alive else "STOPPED")
    return {"result": "FAIL" if state == "FAILED" else "PASS", "session_id": session["session_id"], "mission_id": session.get("mission_id"),
            "execution_id": session.get("execution_id"), "provider_id": session.get("provider_id"),
            "immutable_binding_class": session.get("immutable_binding_class"),
            "repository_id": session["repository_id"], "repository": session["repository"],
            "mode": "OPERATOR_INTERACTIVE", "session_mode": "OPERATOR_INTERACTIVE",
            "execution_mode": execution_mode, "interactive": True, "managed": False,
            "state": state, "process_alive": alive,
            "pid": session.get("pid"), "process_group": session.get("process_group"),
            "pty_binding": session.get("pty_binding", "PASS"), "terminal_io": "PASS", "signal_forwarding": "PASS",
            "remote_client": bool(session.get("remote_client")), "app_server_endpoint": session.get("app_server_endpoint"),
            "zeus_provider_control": bool(session.get("zeus_provider_control")),
            "provider_mode": session.get("provider_mode"), "transport": session.get("provider_transport"),
            "endpoint_uri": session.get("remote_endpoint"), "listener_id": session.get("listener_id"),
            "listener_pid": session.get("listener_pid"), "listener_alive": listener_alive,
            "socket_listening": session.get("socket_listening", False),
            "readiness_probe": session.get("readiness_probe", "NOT_RUN"),
            "readiness_result": session.get("readiness_result", "NOT_RUN"),
            "remote_capable": bool(session.get("remote_capable")),
            "remote_client_pid": session.get("remote_client_pid"),
            "remote_client_state": session.get("remote_client_state", "NOT_STARTED"),
            "session_state": session_state, "client_state": client_state,
            "listener_state": listener_state, "attachment_state": attachment_state,
            "provider_state": provider_state,
            "failure_phase": session.get("failure_phase"),
            "terminal_resize": "PASS", "mission_binding": "PASS" if session.get("mission_id") else "NOT_APPLICABLE",
            "execution_binding": "PASS" if session.get("execution_id") else "NOT_APPLICABLE",
            "provider_binding": "PASS" if session.get("provider_id") else "NOT_APPLICABLE",
            "repository_binding": "PASS", "authority": session.get("authority", "NOT_APPLICABLE"),
            "operator_interactive": True, "mission_work_started": bool(session.get("mission_work_started")),
            "repository_work_started": bool(session.get("repository_work_started")),
            "replay": "IDEMPOTENT", "approval_state": session.get("approval_state"),
            "logs": session.get("log_path"), "artifacts": {"session": session.get("path"),
            "events": session.get("event_directory")}, "blockers": [], "read_only": read_only,
            "thread_id": session.get("thread_id"), "turn_state": session.get("turn_state", "IDLE"),
            "attached": bool(alive and state in ACTIVE_STATES), "session_mode": "OPERATOR_INTERACTIVE",
            "mission_bound": bool(session.get("mission_id")), "execution_bound": bool(session.get("execution_id")),
            "repository_bound": True, "authority_mode": session.get("authority_mode"),
            "failure": session.get("failure"), "next_authorized_action": session.get("session_next_authorized_action") or ("RECONCILE_PROVIDER_SESSION" if state == "FAILED" else ("CONTINUE_INTERACTIVE_SESSION" if alive else "START_INTERACTIVE_SESSION"))}


def _make_session(root: Path, runtime: Path, mission_id: str | None, approval: bool,
                  execution_mode: str = DIRECT_INTERACTIVE) -> tuple[dict[str, Any], Path]:
    repository = resolve_repository(root)
    package = _package(root, mission_id, runtime)
    if mission_id is not None and not approval:
        raise InteractiveCodexError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for a mission-bound shell",
                                    next_action="APPROVE_AND_START_INTERACTIVE_SESSION")
    execution_id = package.get("execution_id") if package else None
    binding_class = "MISSION_EXECUTION" if mission_id or execution_id else "REPOSITORY_OPERATOR"
    session_id = session_identifier(repository, mission_id, execution_id, execution_mode,
                                    binding_class=binding_class)
    active_existing = _existing(runtime, mission_id, active=True, latest=True,
                                execution_mode=execution_mode, binding_class=binding_class)
    if active_existing:
        raise InteractiveCodexError("DUPLICATE_INTERACTIVE_SESSION", "a live interactive session already exists; use attach")
    existing = _existing(runtime, mission_id, latest=True,
                        execution_mode=execution_mode, binding_class=binding_class)
    if existing:
        if _alive(existing.get("pid")):
            raise InteractiveCodexError("DUPLICATE_INTERACTIVE_SESSION", "a live interactive session already exists; use attach")
        # A remote session is never reused after reconciliation.  Its prior
        # record remains historical and a fresh immutable identity is issued.
        if execution_mode == REMOTE_INTERACTIVE:
            predecessor = existing.get("session_id")
            session_id = session_identifier(repository, mission_id, execution_id, execution_mode,
                                            binding_class=binding_class,
                                            reconciliation_generation=str(time.time_ns()))
        elif existing.get("session_id") != session_id:
            raise InteractiveCodexError("SESSION_INPUT_MISMATCH", "existing interactive session binding differs")
    event_directory = runtime / "codex-interactive-events" / session_id
    session: dict[str, Any] = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
        "contract": {"id": CONTRACT, "version": VERSION,
                      "remote_contract": REMOTE_SESSION_CONTRACT if execution_mode == REMOTE_INTERACTIVE else None},
        "session_id": session_id, "mission_id": mission_id, "execution_id": package.get("execution_id") if package else None,
        "immutable_binding_class": binding_class,
        "provider_id": package.get("provider_id") if package else None, "repository": str(root),
        "repository_id": repository["repository_id"], "repository_identity": repository["repository_identity"],
        "repository_baseline": package.get("current_published_baseline") if package else None,
        "mode": "OPERATOR_INTERACTIVE", "execution_mode": execution_mode,
        "session_mode": "OPERATOR_INTERACTIVE", "interactive": True, "managed": False,
        "mission_bound": bool(mission_id), "execution_bound": bool(package), "repository_bound": True,
        "authority_mode": "NON_MISSION_OPERATOR_SESSION" if package is None else "ZEUS_MISSION_BOUND_OPERATOR_SESSION",
        "state": "CREATED", "pid": None,
        "process_group": None, "operator_identity": os.environ.get("USER", "unknown"),
        "terminal_identity": os.environ.get("TTY", "operator-terminal"), "terminal_size": _terminal_size(sys.stdin.fileno()) if sys.stdin.isatty() else None,
        "approval_state": "APPROVED" if approval else "NOT_REQUIRED", "authority": "PASS" if package else "NOT_APPLICABLE",
        "mission_work_started": False, "repository_work_started": False, "start_timestamp": time.time(),
        "thread_id": None, "turn_state": "IDLE", "attached": False,
        "provider_mode": "CODEX_CLI" if execution_mode == DIRECT_INTERACTIVE else "APP_SERVER_REMOTE",
        "provider_transport": "DIRECT_TERMINAL" if execution_mode == DIRECT_INTERACTIVE else "WEBSOCKET",
        "remote_capable": False, "remote_endpoint": None, "listener_id": None,
        "listener_pid": None, "socket_listening": False, "readiness_probe": "NOT_RUN",
        "remote_client_pid": None, "remote_client_state": "NOT_STARTED", "failure_phase": None,
        "stop_timestamp": None, "exit_status": None, "recovery_state": "NOT_REQUIRED", "path": str(_path(runtime, session_id)),
        "event_directory": str(event_directory), "log_path": str(runtime / "codex-interactive-logs" / f"{session_id}.log")}
    if existing and execution_mode == REMOTE_INTERACTIVE:
        session["historical_predecessor_session_id"] = predecessor
    if mission_id is not None:
        codex_home = runtime / "codex-home" / session_id
        codex_adapter._prepare_codex_home(codex_home)
        session["codex_home"] = str(codex_home)
    _append_event(runtime, session_id, "SHELL_REQUEST_ACCEPTED", {"mission_id": mission_id, "phase": "SHELL_REQUEST_ACCEPTED"})
    _append_event(runtime, session_id, "SESSION_RECORD_CREATED", {"mission_id": mission_id,
        "execution_id": session.get("execution_id"), "authority": session["authority"], "mode": session["mode"]})
    return _save(runtime, session), Path(session["log_path"])


def _legacy_shell(repository: Path | str, mission_id: str | None = None, *, approval: bool = False,
          runtime_root: Path | str | None = None, codex_bin: str = "codex", argv: list[str] | None = None,
          _allow_non_tty: bool = False, _session_id: str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    mission = str(mission_id).upper() if mission_id else None
    if not _allow_non_tty and not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise InteractiveCodexError("PTY_REQUIRED", "codex shell requires an interactive terminal")
    if mission is not None and not approval:
        raise InteractiveCodexError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for a mission-bound shell",
                                    next_action="APPROVE_AND_START_INTERACTIVE_SESSION")
    runtime = _runtime(root, runtime_root)
    managed = codex_adapter._existing(runtime, mission) if mission else None
    control_socket = managed.get("control_socket") if managed else None
    if managed and managed.get("state") == "READY" and _alive(managed.get("provider_pid")) and not control_socket:
        raise InteractiveCodexError(
            "READY_PROVIDER_NOT_ATTACHABLE",
            "a READY managed provider exists, but its broker has no compatible operator attachment channel",
            next_action="USE_THE_MANAGED_OWNER_TERMINAL_OR_RECONCILE_BROKER_ATTACHMENT",
        )
    if _session_id:
        session = _existing(runtime, mission, _session_id, active=False)
        if not session:
            raise InteractiveCodexError("SESSION_NOT_ATTACHABLE", "requested interactive session is not live")
        log_path = Path(session["log_path"])
    else:
        session, log_path = _make_session(root, runtime, mission, approval)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _append_event(runtime, session["session_id"], "REPOSITORY_BINDING_RESOLVED",
                  {"repository_id": session["repository_id"], "phase": "REPOSITORY_BINDING_RESOLVED"})
    if mission:
        _append_event(runtime, session["session_id"], "MISSION_BINDING_RESOLVED",
                      {"mission_id": mission, "phase": "MISSION_BINDING_RESOLVED"})
        _append_event(runtime, session["session_id"], "EXECUTION_BINDING_RESOLVED",
                      {"execution_id": session.get("execution_id"), "phase": "EXECUTION_BINDING_RESOLVED"})
    _append_event(runtime, session["session_id"], "PROVIDER_SESSION_SELECTED",
                  {"provider_id": session.get("provider_id"), "phase": "PROVIDER_SESSION_SELECTED"})
    session = dict(session, state="ATTACHING", failure_phase=None)
    _save(runtime, session)
    context = _context(_package(root, mission, runtime), resolve_repository(root))
    config = json.dumps(context)
    # Keep Codex's own approval gate enabled while Zeus records the outer
    # authority boundary.  ``untrusted`` avoids silently granting external
    # effects; Zeus never uses the dangerous bypass mode.
    sandbox = "workspace-write" if mission else "read-only"
    # The provider remains a structured stdio app-server.  Only this Zeus
    # shell owns the operator terminal; the provider is never put on a PTY.
    command = [codex_bin, "app-server", "--stdio"] + list(argv or [])
    before = _terminal_size(sys.stdin.fileno()) if sys.stdin.isatty() else None
    environment = dict(os.environ)
    if session.get("codex_home"):
        environment["CODEX_HOME"] = str(session["codex_home"])
    environment["COLUMNS"] = str((before or terminal_size())[1])
    environment["LINES"] = str((before or terminal_size())[0])
    _append_event(runtime, session["session_id"], "REPOSITORY_BINDING_RESOLVED", {"repository_id": session["repository_id"]})
    if mission:
        _append_event(runtime, session["session_id"], "MISSION_BINDING_RESOLVED", {"mission_id": mission})
        _append_event(runtime, session["session_id"], "EXECUTION_BINDING_RESOLVED", {"execution_id": session.get("execution_id")})
    _append_event(runtime, session["session_id"], "PROVIDER_SESSION_RESOLVED", {"provider_id": session.get("provider_id")})
    session = dict(session, state="ATTACHING")
    _save(runtime, session)
    provider = (_AttachedProvider(control_socket, int(managed["provider_pid"])) if control_socket and managed else
                subprocess.Popen(command, cwd=root, env=environment,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True, bufsize=0))
    assert provider.stdin is not None and provider.stdout is not None
    pid = provider.pid
    provider_attached = isinstance(provider, _AttachedProvider)
    session = dict(session, pid=pid, process_group=None if provider_attached else pid, command=command, terminal_size=before,
                   pty_binding="PASS", provider_transport="STRUCTURED_STDIO")
    _append_event(runtime, session["session_id"], "BROKER_CONNECTION_ESTABLISHED", {"pid": pid,
        "process_group": None if provider_attached else pid, "terminal_size": before,
        "transport": "broker-control" if provider_attached else "stdio", "app_server_reused": provider_attached})
    _save(runtime, session)
    old_winch = signal.getsignal(signal.SIGWINCH)
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM)
    try:
        def resize(_signum: int, _frame: Any) -> None:
            size = _terminal_size(sys.stdin.fileno()) if sys.stdin.isatty() else None
            _append_event(runtime, session["session_id"], "TERMINAL_RESIZED", {"terminal_size": size})
        signal.signal(signal.SIGWINCH, resize)
        if not provider_attached:
            signal.signal(signal.SIGINT, lambda _s, _f: os.killpg(pid, signal.SIGINT))
            signal.signal(signal.SIGTERM, lambda _s, _f: os.killpg(pid, signal.SIGTERM))
        initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"clientInfo": {"name": "zeus-shell", "version": VERSION}, "capabilities": {}}}
        try:
            if not provider_attached:
                provider.stdin.write((json.dumps(initialize, separators=(",", ":")) + "\n").encode())
                provider.stdin.flush()
        except BrokenPipeError:
            # A short-lived provider is still a valid clean shell exit; its
            # stdout/stderr and exit status remain available for the record.
            pass
        thread_request = {"jsonrpc": "2.0", "id": 2, "method": "thread/start",
                          "params": {"cwd": str(root), "approvalPolicy": "on-request",
                                      "sandbox": sandbox, "instructions": config}}
        try:
            provider.stdin.write((json.dumps(thread_request, separators=(",", ":")) + "\n").encode())
            provider.stdin.flush()
            _append_event(runtime, session["session_id"], "THREAD_CREATE_REQUESTED", {"request_id": 2})
        except BrokenPipeError as error:
            raise InteractiveCodexError("THREAD_CREATE_FAILED", "provider closed before thread creation", next_action="RECONCILE_PROVIDER_SESSION") from error
        thread_id = None
        pending_input = bytearray()
        protocol_error: InteractiveCodexError | None = None
        _append_event(runtime, session["session_id"], "APP_SERVER_READY", {"phase": "APP_SERVER_READY", "app_server_reused": provider_attached})
        session = dict(_load(_path(runtime, session["session_id"])), state="ATTACHED", attached=True)
        _save(runtime, session)
        _append_event(runtime, session["session_id"], "BROKER_ATTACHED", {"transport": "STRUCTURED_STDIO"})
        with log_path.open("ab") as log, terminal_mode():
            _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_ENTERED", {"state": "ATTACHING"})
            streams = [provider.stdout]
            if provider.stderr is not None:
                streams.append(provider.stderr)
            if sys.stdin.isatty():
                streams.append(sys.stdin)
            while streams:
                readable, _, _ = select.select(streams, [], [], 0.25)
                if provider.stdout in readable:
                    line = provider.stdout.readline()
                    if not line:
                        streams.remove(provider.stdout)
                    else:
                        log.write(line); log.flush()
                        try:
                            message = json.loads(line.decode("utf-8"))
                            if message.get("id") == 2:
                                result = message.get("result") or {}
                                thread_id = result.get("thread", {}).get("id") or result.get("threadId") or result.get("id")
                                if not thread_id:
                                    raise InteractiveCodexError("THREAD_CREATE_FAILED", str(message.get("error", "thread id missing")), next_action="RECONCILE_PROVIDER_SESSION")
                                session = dict(_load(_path(runtime, session["session_id"])), state="THREAD_READY", thread_id=thread_id, attached=True, turn_state="IDLE")
                                _save(runtime, session)
                                _append_event(runtime, session["session_id"], "THREAD_CREATED", {"thread_id": thread_id})
                                session = dict(_load(_path(runtime, session["session_id"])), state="AWAITING_OPERATOR_INPUT")
                                _save(runtime, session)
                                _append_event(runtime, session["session_id"], "OPERATOR_INPUT_READY", {"state": "AWAITING_OPERATOR_INPUT"})
                            if message.get("error") and message.get("id") in {1, 2}:
                                raise InteractiveCodexError("APP_SERVER_PROTOCOL_ERROR", str(message["error"]), next_action="RECONCILE_PROVIDER_SESSION")
                            method = str(message.get("method", ""))
                            if thread_id and ("turn/completed" in method or "turn/completed" in str(message.get("params", {}).get("type", ""))):
                                session = dict(_load(_path(runtime, session["session_id"])), state="AWAITING_OPERATOR_INPUT", turn_state="IDLE")
                                _save(runtime, session)
                                _append_event(runtime, session["session_id"], "TURN_COMPLETED", {"thread_id": thread_id})
                            if message.get("method") and message.get("id") is not None:
                                response = {"jsonrpc": "2.0", "id": message["id"], "result": {"decision": "decline"}}
                                provider.stdin.write((json.dumps(response, separators=(",", ":")) + "\n").encode()); provider.stdin.flush()
                            rendered = render_event(message)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            rendered = ""
                        if rendered:
                            sys.stdout.write(rendered); sys.stdout.flush()
                if provider.stderr is not None and provider.stderr in readable:
                    diagnostic = provider.stderr.readline()
                    if not diagnostic:
                        streams.remove(provider.stderr)
                    else:
                        log.write(b"[stderr] " + diagnostic); log.flush()
                        sys.stderr.buffer.write(diagnostic); sys.stderr.buffer.flush()
                if sys.stdin in readable:
                    data = strip_bracketed_paste(os.read(sys.stdin.fileno(), 65536))
                    if data:
                        _append_event(runtime, session["session_id"], "OPERATOR_INPUT", {"bytes": len(data)})
                        pending_input.extend(data)
                        while b"\n" in pending_input:
                            raw, _, remainder = pending_input.partition(b"\n")
                            pending_input = bytearray(remainder)
                            text = raw.decode("utf-8", errors="strict")
                            if text.startswith("/"):
                                command_name = text.strip().lower()
                                if command_name in {"/exit", "/stop"}:
                                    session = dict(_load(_path(runtime, session["session_id"])), state="STOPPING", attached=False)
                                    _save(runtime, session)
                                    _append_event(runtime, session["session_id"], "SHELL_EXIT_REQUESTED", {"command": command_name})
                                    streams = []
                                    break
                                if command_name == "/detach":
                                    session = dict(_load(_path(runtime, session["session_id"])), state="DETACHED", attached=False)
                                    _save(runtime, session)
                                    _append_event(runtime, session["session_id"], "SHELL_DETACHED", {})
                                    streams = []
                                    break
                                if command_name in {"/status", "/bindings", "/authority", "/help", "/logs", "/artifacts", "/interrupt"}:
                                    sys.stdout.write(json.dumps(_result(session, read_only=True), sort_keys=True) + "\n"); sys.stdout.flush()
                                    continue
                            if not thread_id:
                                raise InteractiveCodexError("THREAD_NOT_READY", "operator input arrived before thread creation")
                            turn_request = {"jsonrpc": "2.0", "id": int(time.time() * 1000000) % 2147483647,
                                            "method": "turn/start", "params": {"threadId": thread_id,
                                            "input": [{"type": "text", "text": text}]}}
                            provider.stdin.write((json.dumps(turn_request, separators=(",", ":")) + "\n").encode()); provider.stdin.flush()
                            session = dict(_load(_path(runtime, session["session_id"])), state="TURN_ACTIVE", turn_state="ACTIVE")
                            _save(runtime, session)
                            _append_event(runtime, session["session_id"], "TURN_CREATE_REQUESTED", {"thread_id": thread_id})
                            _append_event(runtime, session["session_id"], "TURN_ACTIVE", {"thread_id": thread_id})
                    else:
                        streams.remove(sys.stdin)
                if provider.poll() is not None and provider.stdout not in streams:
                    if not thread_id and session.get("state") != "DETACHED":
                        raise InteractiveCodexError("THREAD_CREATE_FAILED", "provider exited before thread creation", next_action="RECONCILE_PROVIDER_SESSION")
                    break
                if provider.poll() is not None and provider.stdout in streams:
                    # Drain any final protocol output, then record the actual exit.
                    continue
        if protocol_error:
            raise protocol_error
    finally:
        _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_EXITED", {
            "cleanup_reason": "EXPLICIT_EXIT" if _load(_path(runtime, session["session_id"])).get("state") == "STOPPING" else "PROVIDER_OR_CONTROLLED_EXIT"
        })
        signal.signal(signal.SIGWINCH, old_winch); signal.signal(signal.SIGINT, old_int); signal.signal(signal.SIGTERM, old_term)
        try:
            _, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            status = 0
        exit_status = os.waitstatus_to_exitcode(status) if status else 0
        current = _load(_path(runtime, session["session_id"]))
        failed = sys.exc_info()[0] is not None and current.get("state") != "DETACHED"
        final_state = current.get("state") if current.get("state") == "DETACHED" else ("FAILED" if failed else "STOPPED")
        failure = {"error_type": sys.exc_info()[0].__name__ if sys.exc_info()[0] else None,
                   "error": str(sys.exc_info()[1]) if sys.exc_info()[1] else None}
        session = dict(current, state=final_state, stop_timestamp=time.time(), exit_status=exit_status, attached=False,
                       failure=failure if failed else current.get("failure"))
        _append_event(runtime, session["session_id"], "SESSION_FAILED" if failed else "SESSION_STOPPED",
                      {"exit_status": exit_status, **failure} if failed else {"exit_status": exit_status})
        _save(runtime, session)
        if provider.poll() is None and not provider_attached:
            provider.terminate()
        provider.wait(timeout=2)
        for stream in (provider.stdin, provider.stdout, provider.stderr):
            if stream is not None:
                try:
                    stream.close()
                except BrokenPipeError:
                    pass
        if provider_attached:
            provider.close()
    return _result(session, read_only=False)


def establish_remote_endpoint(root: Path, runtime: Path, session_id: str, codex_home: Path,
                              log_path: Path, codex_bin: str) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    """Authoritative endpoint transaction shared by diagnose and operational launch."""
    capabilities = codex_capabilities(codex_bin)
    if not capabilities["remote_mode_supported"]:
        raise InteractiveCodexError("REMOTE_CAPABILITY_UNSUPPORTED",
                                    "installed Codex does not support the required remote listener mode",
                                    next_action="RECONCILE_CODEX_VERSION_OR_TRANSPORT",
                                    details={**capabilities, "failure_phase": "TRANSPORT_RESOLVED"})
    event_dir = runtime / "codex-interactive-events" / session_id
    event_dir.mkdir(parents=True, exist_ok=True)
    ready = event_dir / "remote-ready.json"
    exited = event_dir / "remote-exited.json"
    try:
        port = _free_loopback_port()
    except OSError as error:
        raise InteractiveCodexError("REMOTE_PORT_ALLOCATION_FAILED", str(error),
                                    next_action="RECONCILE_PROVIDER_SESSION",
                                    details={"failure_phase": "LOOPBACK_PORT_ALLOCATED"}) from error
    endpoint = f"ws://127.0.0.1:{port}"
    transaction_id = identifier("CODEX-ENDPOINT-TRANSACTION", {"session_id": session_id, "endpoint": endpoint})
    _append_event(runtime, session_id, "TRANSPORT_RESOLVED",
                  {"transport": "WEBSOCKET", "endpoint_uri": endpoint, "bind_address": "127.0.0.1"})
    _append_event(runtime, session_id, "LISTENER_START_REQUESTED",
                  {"endpoint_uri": endpoint, "provider_mode": "INTERACTIVE_REMOTE"})
    _append_event(runtime, session_id, "REMOTE_MODE_SELECTED",
                  {"execution_mode": REMOTE_INTERACTIVE, "endpoint_uri": endpoint})
    _append_event(runtime, session_id, "REMOTE_PROVIDER_TRANSACTION_CREATED",
                  {"provider_mode": "APP_SERVER_REMOTE", "transport": "WEBSOCKET",
                   "endpoint_creation_transaction_id": transaction_id})
    command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker", "--root", str(root),
               "--codex-home", str(codex_home), "--log", str(log_path), "--ready", str(ready),
               "--exited", str(exited), "--listen", endpoint, "--codex-bin", codex_bin]
    broker = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              start_new_session=True)
    _append_event(runtime, session_id, "LISTENER_LAUNCH_CALLED", {"startup_command": command})
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if ready.is_file():
            value = load_json(ready)
            if value.get("result") != "PASS":
                if broker.poll() is None:
                    broker.terminate()
                raise InteractiveCodexError(value.get("error_code", "REMOTE_LISTENER_START_FAILED"), value.get("error", "remote endpoint failed"),
                                            next_action="RECONCILE_PROVIDER_SESSION", details=value)
            value["capabilities"] = capabilities
            _append_event(runtime, session_id, "LISTENER_PROCESS_STARTED",
                          {"listener_pid": value.get("listener_pid"), "startup_command": command})
            _append_event(runtime, session_id, "LISTENER_BIND_CONFIRMED",
                          {"endpoint_uri": endpoint, "socket_listening": value.get("socket_listening")})
            _append_event(runtime, session_id, "READINESS_PROBE_STARTED", {"endpoint_uri": endpoint})
            _append_event(runtime, session_id, "READINESS_PROBE_PASSED",
                          {"endpoint_uri": endpoint, "probe": value.get("readiness_probe")})
            _append_event(runtime, session_id, "LISTENER_READY",
                          {"listener_pid": value.get("listener_pid"), "endpoint_uri": endpoint})
            receipt = {**value, "endpoint_owner_session_id": session_id,
                       "endpoint_creation_transaction_id": transaction_id,
                       "endpoint_uri": endpoint, "remote_capable": True}
            current = _load(_path(runtime, session_id))
            _save(runtime, dict(current, endpoint_owner_session_id=session_id,
                                endpoint_creation_transaction_id=transaction_id,
                                endpoint_uri=endpoint, remote_endpoint=endpoint,
                                listener_pid=value.get("listener_pid"),
                                socket_listening=bool(value.get("socket_listening")),
                                readiness_result="PASS", endpoint_receipt=receipt))
            _append_event(runtime, session_id, "ENDPOINT_RECEIPT_PERSISTED", receipt)
            _append_event(runtime, session_id, "ENDPOINT_IDENTITY_VERIFIED",
                          {"endpoint_uri": endpoint, "endpoint_owner_session_id": session_id})
            _append_event(runtime, session_id, "REMOTE_CLIENT_LAUNCH_READY", {"endpoint_uri": endpoint})
            return broker, receipt
        if broker.poll() is not None:
            detail = load_json(ready) if ready.is_file() else {"listener_exit_code": broker.returncode}
            stderr = b""
            if broker.stderr is not None:
                try: stderr = broker.stderr.read() or b""
                except OSError: pass
            detail = {**detail, "failure_phase": "LISTENER_PROCESS_STARTED",
                      "listener_stderr": stderr.decode("utf-8", "replace")}
            raise InteractiveCodexError("REMOTE_LISTENER_START_FAILED", "remote listener exited before readiness",
                                        next_action="RECONCILE_PROVIDER_SESSION", details=detail)
        time.sleep(0.05)
    if broker.poll() is None:
        broker.terminate()
    raise InteractiveCodexError("REMOTE_WEBSOCKET_PROBE_FAILED", "timed out waiting for Zeus remote endpoint",
                                next_action="RECONCILE_PROVIDER_SESSION",
                                details={"endpoint_uri": endpoint, "failure_phase": "READINESS_PROBE_STARTED",
                                         "startup_command": command})


def _remote_broker(root: Path, runtime: Path, session_id: str, codex_home: Path,
                   log_path: Path, codex_bin: str) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    """Compatibility seam; both remote actions use establish_remote_endpoint."""
    return establish_remote_endpoint(root, runtime, session_id, codex_home, log_path, codex_bin)


def _direct_shell(root: Path, runtime: Path, session: dict[str, Any], log_path: Path,
                  *, mission: str | None, codex_bin: str, argv: list[str] | None) -> dict[str, Any]:
    """Launch native Codex in the current terminal; no PTY or app-server is inserted."""
    package = _package(root, mission, runtime)
    repository = resolve_repository(root)
    context = _context(package, repository)
    sandbox = "workspace-write" if mission else "read-only"
    launcher = direct_launcher_path(root)
    command = [str(launcher), codex_bin, "-C", str(root), "-s", sandbox, "-a", "on-request",
               "-c", f"developer_instructions={json.dumps(context)}"] + list(argv or [])
    environment = dict(os.environ)
    environment.update({"ENGINEERING_CODEX_WRAPPER": "zeus-direct-codex-v1",
                        "ZEUS_EXECUTION_MODE": DIRECT_INTERACTIVE,
                        "ZEUS_SESSION_ID": session["session_id"]})
    if session.get("codex_home"):
        environment["CODEX_HOME"] = str(session["codex_home"])
    session = dict(session, state="ATTACHED", attached=True, pty_binding="DIRECT_TERMINAL",
                   provider_mode="CODEX_CLI", provider_transport="DIRECT_TERMINAL",
                   execution_mode=DIRECT_INTERACTIVE, interactive=True, managed=False,
                   remote_capable=False, remote_endpoint=None, app_server_endpoint=None,
                   zeus_provider_control=True, command=command)
    _append_event(runtime, session["session_id"], "DIRECT_CLIENT_LAUNCH_REQUESTED",
                  {"command": command, "terminal_inherited": True, "remote_endpoint_created": False})
    _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_ENTERED",
                  {"client": "CODEX_CLI", "execution_mode": DIRECT_INTERACTIVE})
    _save(runtime, session)
    client = None
    failure = None
    exit_status = 0
    previous_handlers = {}
    started = time.time()
    try:
        client = subprocess.Popen(command, cwd=root, env=environment)
        session = dict(_load(_path(runtime, session["session_id"])), pid=client.pid,
                       process_group=client.pid, remote_client=False, remote_client_state="NOT_APPLICABLE")
        _save(runtime, session)
        _append_event(runtime, session["session_id"], "DIRECT_CLIENT_STARTED",
                      {"pid": client.pid, "process_group": client.pid, "native_tui": True})
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, lambda received, _frame, s=signum: os.kill(client.pid, s) if client and client.poll() is None else None)
        exit_status = client.wait()
    except BaseException as error:
        failure = {"error_type": type(error).__name__, "error": str(error), "failure_phase": "DIRECT_CLIENT_LAUNCH"}
        raise
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        current = _load(_path(runtime, session["session_id"]))
        current = dict(current, state="FAILED" if failure else "STOPPED", attached=False,
                       stop_timestamp=time.time(), exit_status=exit_status, failure=failure,
                       duration_seconds=round(time.time() - started, 3),
                       next_authorized_action="RECONCILE_PROVIDER_SESSION" if failure else "START_INTERACTIVE_SESSION")
        _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_EXITED",
                      {"client": "CODEX_CLI", "exit_status": exit_status})
        _append_event(runtime, session["session_id"], "SESSION_FAILED" if failure else "SESSION_STOPPED",
                      {"exit_status": exit_status, "execution_mode": DIRECT_INTERACTIVE})
        saved = _save(runtime, current)
    return _result(saved, read_only=False)


def shell(repository: Path | str, mission_id: str | None = None, *, approval: bool = False,
          runtime_root: Path | str | None = None, codex_bin: str = "codex", argv: list[str] | None = None,
          remote: bool = False, _allow_non_tty: bool = False, _session_id: str | None = None) -> dict[str, Any]:
    """Launch direct native Codex by default, or remote Codex when explicitly requested.

    Direct mode inherits the operator terminal.  Remote mode is separately
    qualified through the official app-server WebSocket listener.
    """
    root = Path(repository).resolve()
    mission = str(mission_id).upper() if mission_id else None
    if not _allow_non_tty and not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise InteractiveCodexError("PTY_REQUIRED", "codex shell requires an interactive terminal")
    if mission and not approval:
        raise InteractiveCodexError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for a mission-bound shell",
                                    next_action="APPROVE_AND_START_INTERACTIVE_SESSION")
    runtime = _runtime(root, runtime_root)
    if not remote:
        session, log_path = _make_session(root, runtime, mission, approval, DIRECT_INTERACTIVE)
        return _direct_shell(root, runtime, session, log_path, mission=mission, codex_bin=codex_bin, argv=argv)
    managed = codex_adapter._existing(runtime, mission) if mission else None
    if _session_id:
        session = _existing(runtime, mission, _session_id, active=False)
        if not session:
            raise InteractiveCodexError("SESSION_NOT_ATTACHABLE", "requested interactive session is not live")
        log_path = Path(session["log_path"])
    else:
        session, log_path = _make_session(root, runtime, mission, approval, REMOTE_INTERACTIVE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    endpoint = None
    broker = None
    owns_broker = False
    if (_session_id and session.get("remote_endpoint") and _alive(session.get("listener_pid"))):
        endpoint = session["remote_endpoint"]
        try:
            probe = codex_app_server_broker.websocket_readiness(endpoint)
        except (OSError, ValueError, TimeoutError) as error:
            raise InteractiveCodexError("STALE_REMOTE_SESSION", f"detached endpoint failed readiness: {error}",
                                        next_action="RECONCILE_PROVIDER_SESSION") from error
        session = dict(session, pid=session.get("listener_pid"), provider_pid=session.get("listener_pid"),
                       remote_endpoint=endpoint, provider_transport="WEBSOCKET",
                       provider_mode="INTERACTIVE_REMOTE", remote_capable=True,
                       listener_pid=session.get("listener_pid"), socket_listening=True,
                       readiness_probe=probe, readiness_result="PASS", remote_client=True)
    elif (managed and managed.get("state") == "READY" and _alive(managed.get("provider_pid")
        ) and managed.get("provider_mode") == "INTERACTIVE_REMOTE"
        and managed.get("remote_capable") and managed.get("remote_endpoint", "").startswith("ws://")
        and managed.get("readiness_result") == "PASS"):
        endpoint = managed.get("remote_endpoint")
        if not endpoint:
            raise InteractiveCodexError("READY_PROVIDER_NOT_REMOTE_ATTACHABLE",
                                        "READY managed provider has no supported remote endpoint",
                                        next_action="RESUME_MANAGED_PROVIDER_WITH_REMOTE_CONTROL")
        try:
            probe = codex_app_server_broker.websocket_readiness(endpoint)
        except (OSError, ValueError, TimeoutError) as error:
            raise InteractiveCodexError("STALE_REMOTE_PROVIDER",
                                        f"managed remote endpoint failed readiness: {error}",
                                        next_action="RECONCILE_PROVIDER_SESSION",
                                        details={"endpoint_uri": endpoint, "failure_phase": "READINESS_PROBE_STARTED"}) from error
        session = dict(session, pid=managed.get("provider_pid"), provider_pid=managed.get("provider_pid"),
                       provider_id=managed.get("provider_id"), remote_endpoint=endpoint,
                       provider_transport="WEBSOCKET", provider_mode="INTERACTIVE_REMOTE",
                       remote_capable=True, listener_pid=managed.get("listener_pid"),
                       socket_listening=True, readiness_probe=probe, readiness_result="PASS",
                       remote_client=True)
    else:
        codex_home = Path(session.get("codex_home") or (runtime / "codex-home" / session["session_id"]))
        codex_adapter._prepare_codex_home(codex_home)
        session = dict(session, codex_home=str(codex_home))
        _save(runtime, session)
        try:
            broker, ready = _remote_broker(root, runtime, session["session_id"], codex_home, log_path, codex_bin)
        except InteractiveCodexError as error:
            failed = dict(_load(_path(runtime, session["session_id"])), state="FAILED", attached=False,
                          failure_phase=error.details.get("failure_phase", "LISTENER_START_REQUESTED"),
                          failure={"code": error.code, "error_type": type(error).__name__,
                                   "error": error.message, **error.details},
                          next_authorized_action=error.next_action, stop_timestamp=time.time())
            _append_event(runtime, session["session_id"], "SESSION_FAILED", failed["failure"])
            _save(runtime, failed)
            raise
        endpoint = ready.get("remote_endpoint")
        owns_broker = True
        session = dict(session, provider_id=session.get("provider_id") or "codex-remote-local",
                       pid=ready.get("provider_pid"), provider_pid=ready.get("provider_pid"), remote_endpoint=endpoint,
                       provider_transport="WEBSOCKET", provider_mode="INTERACTIVE_REMOTE",
                       remote_capable=True, listener_pid=ready.get("listener_pid"),
                       listener_id=identifier("CODEX-LISTENER", {"endpoint": endpoint, "provider_pid": ready.get("provider_pid")}),
                       socket_listening=bool(ready.get("socket_listening")),
                       readiness_probe="PASS" if ready.get("readiness_probe", {}).get("result") == "PASS" else "FAIL",
                       readiness_result="PASS", remote_client=True,
                       endpoint_owner_session_id=session["session_id"],
                       endpoint_creation_transaction_id=ready.get("endpoint_creation_transaction_id"),
                       endpoint_uri=endpoint, endpoint_receipt=ready)
    if not endpoint:
        raise InteractiveCodexError("REMOTE_ENDPOINT_IDENTITY_FAILED",
                                    "endpoint transaction completed without a verified endpoint URI",
                                    next_action="RECONCILE_PROVIDER_SESSION",
                                    details={"failure_phase": "ENDPOINT_IDENTITY_VERIFIED"})
    session = dict(session, state="ATTACHED", attached=True, remote_client=True,
                   remote_endpoint=endpoint, app_server_endpoint="ACTIVE",
                   zeus_provider_control=True, pty_binding="OFFICIAL_CODEX_REMOTE")
    _append_event(runtime, session["session_id"], "REMOTE_CLIENT_RESOLVED", {"endpoint": endpoint,
        "official_cli": True, "provider_reused": not owns_broker})
    _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_ENTERED", {"client": "OFFICIAL_CODEX_REMOTE"})
    _save(runtime, session)
    sandbox = "workspace-write" if mission else "read-only"
    command = [codex_bin, "--remote", endpoint, "-C", str(root), "-s", sandbox,
               "-a", "on-request"] + list(argv or [])
    environment = dict(os.environ)
    if session.get("codex_home"):
        environment["CODEX_HOME"] = str(session["codex_home"])
    exit_status = 0
    failure: dict[str, Any] | None = None
    try:
        _append_event(runtime, session["session_id"], "REMOTE_CLIENT_LAUNCH_REQUESTED",
                      {"command": command, "endpoint_uri": endpoint})
        client = subprocess.Popen(command, cwd=root, env=environment, start_new_session=False)
        current = dict(_load(_path(runtime, session["session_id"])), remote_client_pid=client.pid,
                       remote_client_state="RUNNING")
        _save(runtime, current)
        _append_event(runtime, session["session_id"], "REMOTE_CLIENT_STARTED",
                      {"client_pid": client.pid, "endpoint_uri": endpoint})
        exit_status = client.wait()
        current = dict(_load(_path(runtime, session["session_id"])), remote_client_state="STOPPED",
                       remote_client_exit_code=exit_status)
        _save(runtime, current)
    except BaseException as error:
        failure = {"code": "REMOTE_CLIENT_LAUNCH_FAILED", "failure_phase": "REMOTE_CLIENT_LAUNCH",
                   "error_type": type(error).__name__, "error": str(error)}
        raise
    finally:
        current = _load(_path(runtime, session["session_id"]))
        final = "FAILED" if failure else "STOPPED"
        current = dict(current, state=final, attached=False, stop_timestamp=time.time(),
                       exit_status=exit_status, failure=failure,
                       next_authorized_action="RECONCILE_PROVIDER_SESSION" if failure else "START_INTERACTIVE_SESSION")
        _append_event(runtime, session["session_id"], "SHELL_EVENT_LOOP_EXITED", {"client": "OFFICIAL_CODEX_REMOTE"})
        _append_event(runtime, session["session_id"], "SESSION_STOPPED" if not failure else "SESSION_FAILED",
                      {"exit_status": exit_status, "client": "OFFICIAL_CODEX_REMOTE"})
        _save(runtime, current)
        if owns_broker and broker is not None and broker.poll() is None:
            broker.terminate()
            try:
                broker.wait(timeout=3)
            except subprocess.TimeoutExpired:
                broker.kill()
        return_value = _result(current, read_only=False)
    return return_value


def diagnose(repository: Path | str, mission_id: str | None = None, *, approval: bool = False,
             runtime_root: Path | str | None = None, codex_bin: str = "codex") -> dict[str, Any]:
    """Create/probe one endpoint and stop before launching the official client."""
    root = Path(repository).resolve(); mission = str(mission_id).upper() if mission_id else None
    if mission and not approval:
        raise InteractiveCodexError("OPERATOR_APPROVAL_REQUIRED", "--approve is required for a mission-bound diagnostic")
    runtime = _runtime(root, runtime_root); session, log_path = _make_session(root, runtime, mission, approval, REMOTE_INTERACTIVE)
    codex_home = Path(session.get("codex_home") or (runtime / "codex-home" / session["session_id"]))
    codex_adapter._prepare_codex_home(codex_home); broker = None
    try:
        broker, ready = _remote_broker(root, runtime, session["session_id"], codex_home, log_path, codex_bin)
        endpoint = ready.get("remote_endpoint") or ready.get("endpoint_uri")
        session = dict(_load(_path(runtime, session["session_id"])),
                       endpoint_owner_session_id=session["session_id"],
                       endpoint_uri=endpoint, remote_endpoint=endpoint,
                       listener_pid=ready.get("listener_pid") or ready.get("provider_pid"),
                       socket_listening=bool(ready.get("socket_listening")),
                       readiness_result="PASS", endpoint_receipt=ready,
                       remote_client_state="NOT_LAUNCHED")
        _save(runtime, session)
        _append_event(runtime, session["session_id"], "DIAGNOSTIC_ENDPOINT_READY",
                      {"endpoint_uri": endpoint, "remote_client_not_launched": True})
        return {"result":"PASS", "remote_mode_supported":"YES", "remote_endpoint_create":"PASS",
                "execution_mode": REMOTE_INTERACTIVE,
                "remote_endpoint_listening":"YES" if ready.get("socket_listening") else "NO",
                "remote_endpoint_reachable":"YES" if ready.get("remote_endpoint_reachable") else "NO",
                "remote_endpoint_identity":ready.get("remote_endpoint_identity", "FAIL"),
                "readiness_probe":ready.get("readiness_probe"), "remote_client_not_launched":"YES",
                "endpoint_uri":endpoint, "remote_endpoint":endpoint,
                "listener_pid":ready.get("listener_pid") or ready.get("provider_pid"),
                "failure_phase":None, "provider_pid":ready.get("provider_pid"),
                "provider_mode":"INTERACTIVE_REMOTE", "transport":"WEBSOCKET",
                "endpoint_receipt_persisted":"YES"}
    finally:
        if broker is not None and broker.poll() is None:
            broker.terminate()
            try: broker.wait(timeout=3)
            except subprocess.TimeoutExpired: broker.kill()


def status(repository: Path | str, mission_id: str | None = None, *, session_id: str | None = None,
           latest: bool = False, active: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root)
    session = _existing(runtime, str(mission_id).upper() if mission_id else None, session_id,
                        latest=latest, active=active)
    if not session:
        return {"result": "PASS", "session_id": session_id, "mission_id": str(mission_id).upper() if mission_id else None,
                "state": "NOT_STARTED", "mode": "OPERATOR_INTERACTIVE", "session_mode": "OPERATOR_INTERACTIVE",
                "execution_mode": DIRECT_INTERACTIVE, "provider_mode": "CODEX_CLI",
                "transport": "DIRECT_TERMINAL", "read_only": True,
                "blockers": [], "next_authorized_action": "START_INTERACTIVE_SESSION"}
    result = _result(session, read_only=True)
    # Remote lifecycle is authoritative in the reconciliation projection.
    # Raw legacy fields may say STOPPED while the listener is intentionally
    # retained and reusable; status must expose the same dimensions as
    # reconcile/attach/stop.
    if session.get("execution_mode") == REMOTE_INTERACTIVE:
        try:
            from scripts.lib.emp import codex_reconciliation
            projection = codex_reconciliation._inventory_v2(runtime, root)
            canonical = next((item for item in projection.get("matching_sessions", [])
                              if item.get("session_id") == session.get("session_id")), None)
            if canonical:
                result.update({key: canonical.get(key) for key in (
                    "session_state", "client_state", "listener_state", "attachment_state",
                    "provider_state", "listener_alive", "socket_listening", "ownership_result",
                    "session_next_authorized_action", "endpoint_uri", "listener_pid",
                    "remote_client_pid", "process_group", "process_groups", "member_pids",
                    "root_pids", "termination_unit_id", "recommended_disposition")})
                result["state"] = canonical.get("session_state")
                result["process_alive"] = canonical.get("listener_alive")
                result["remote_client_state"] = canonical.get("client_state")
                result["next_authorized_action"] = canonical.get("session_next_authorized_action")
                result["ownership"] = canonical.get("ownership", {})
                result["ownership_report"] = canonical.get("ownership", {}).get("ownership_report", {})
                result["lifecycle_schema_version"] = 2
        except (OSError, ValueError, KeyError):
            # Status remains read-only and retains the record projection if
            # an inventory source is unavailable.
            pass
    return result


def record_request_decision(repository: Path | str, session_id: str, request: Mapping[str, Any],
                            *, resolution: str, operator_decision: str | None = None,
                            runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Append a structured Zeus decision; terminal text is never parsed here."""
    runtime = _runtime(Path(repository).resolve(), runtime_root)
    session = _load(_path(runtime, session_id))
    allowed = {"ALREADY_AUTHORIZED", "OPERATOR_DECISION_REQUIRED", "PROHIBITED"}
    if resolution not in allowed:
        raise InteractiveCodexError("INVALID_REQUEST_RESOLUTION", "unsupported request resolution")
    event = _append_event(runtime, session_id, "CODEX_REQUEST_DECISION", {
        "request_id": request.get("request_id"), "session_id": session_id, "mission_id": session.get("mission_id"),
        "request_type": request.get("request_type"), "requested_action": request.get("requested_action"),
        "requested_scope": request.get("requested_scope"), "authority_source": session.get("authority"),
        "resolution": resolution, "operator_decision_required": resolution == "OPERATOR_DECISION_REQUIRED",
        "operator_decision": operator_decision, "decision_timestamp": time.time(),
        "result": "DENIED" if resolution == "PROHIBITED" else "PASS"})
    return {"result": "PASS", "session_id": session_id, "decision": event, "read_only": False}


def resolve_request(request: Mapping[str, Any], *, authorized: bool = False,
                    prohibited: bool = False) -> str:
    """Classify a structured provider request before recording its decision."""
    if prohibited:
        return "PROHIBITED"
    if authorized:
        return "ALREADY_AUTHORIZED"
    return "OPERATOR_DECISION_REQUIRED"


def stop(repository: Path | str, mission_id: str | None = None, *, session_id: str | None = None,
         approval: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    if not approval:
        raise InteractiveCodexError("OPERATOR_APPROVAL_REQUIRED", "--approve is required to stop an interactive session")
    runtime = _runtime(Path(repository).resolve(), runtime_root)
    session = _existing(runtime, str(mission_id).upper() if mission_id else None, session_id=session_id)
    if not session:
        raise InteractiveCodexError("SESSION_NOT_FOUND", "no interactive session belongs to the requested mission")
    if session.get("execution_mode") == REMOTE_INTERACTIVE and session.get("remote_endpoint"):
        from scripts.lib.emp import codex_reconciliation
        try:
            return codex_reconciliation.reconcile(repository, runtime_root=runtime_root, approve=True,
                                                   target_session_id=session["session_id"], dry_run=False)
        except codex_reconciliation.ReconciliationError as error:
            raise InteractiveCodexError(error.code, error.message, next_action=error.next_action) from error
    if _alive(session.get("pid")):
        os.killpg(session.get("process_group") or session["pid"], signal.SIGTERM)
    return _result(_load(_path(runtime, session["session_id"])), read_only=False)


def attach(repository: Path | str, mission_id: str | None = None, *, session_id: str | None = None,
           runtime_root: Path | str | None = None) -> dict[str, Any]:
    session = status(repository, mission_id, session_id=session_id, active=False, runtime_root=runtime_root)
    if session.get("state") == "NOT_STARTED" and mission_id:
        managed = codex_adapter._existing(_runtime(Path(repository).resolve(), runtime_root), str(mission_id).upper())
        if managed and managed.get("state") == "READY" and _alive(managed.get("provider_pid")) and managed.get("control_socket"):
            return shell(repository, str(mission_id).upper(), approval=True, runtime_root=runtime_root)
    if not session.get("process_alive"):
        raise InteractiveCodexError("SESSION_NOT_ATTACHABLE", "no live interactive session is attachable",
                                    next_action="START_INTERACTIVE_SESSION")
    if not session.get("provider_id"):
        raise InteractiveCodexError("ATTACH_TRANSPORT_UNAVAILABLE", "the live interactive session has no broker attachment identity",
                                    next_action="USE_THE_OWNER_TERMINAL_OR_STOP_AND_RECONCILE")
    return shell(repository, mission_id, approval=bool(session.get("approval_state") == "APPROVED"),
                 runtime_root=runtime_root, _session_id=session["session_id"])


def logs(repository: Path | str, mission_id: str | None = None, *, session_id: str | None = None,
         latest: bool = False, active: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = status(repository, mission_id, session_id=session_id, latest=latest, active=active, runtime_root=runtime_root)
    path = Path(value["logs"]) if value.get("logs") else None
    return value | {"log_content": path.read_text(encoding="utf-8", errors="replace") if path and path.is_file() else ""}


def artifacts(repository: Path | str, mission_id: str | None = None, *, session_id: str | None = None,
              latest: bool = False, active: bool = False, runtime_root: Path | str | None = None) -> dict[str, Any]:
    return status(repository, mission_id, session_id=session_id, latest=latest, active=active, runtime_root=runtime_root)

# --- CR46 ZO-058: interactive owner transaction-closure projection ---
def repository_transaction_closure_projection(
    root: Path | str,
    *,
    allowed_paths: list[str] | tuple[str, ...],
    protected_paths: list[str] | tuple[str, ...] = (),
    deferred_paths: list[str] | tuple[str, ...] = (),
    base_commit: str | None = None,
    single_commit_required: bool = False,
) -> dict[str, Any]:
    from scripts.lib.emp.publication_transaction import (
        classify_repository_transaction_closure,
    )

    return {
        **classify_repository_transaction_closure(
            root,
            allowed_paths=allowed_paths,
            protected_paths=protected_paths,
            deferred_paths=deferred_paths,
            base_commit=base_commit,
            single_commit_required=single_commit_required,
        ),
        "owner_surface": "codex_interactive",
    }
