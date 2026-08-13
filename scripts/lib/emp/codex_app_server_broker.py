"""Zeus supervisor for an official Codex app-server listener.

Managed execution remains ``codex app-server --stdio``.  Interactive remote
sessions use the documented ``codex app-server --listen ws://...`` transport;
this process supervises that listener, proves its WebSocket/JSON-RPC endpoint,
and records the provider receipt.  It never implements the operator UI.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import select
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


UNIX_SOCKET_PATH_MAX = 107


def _validate_control_socket(path: Path) -> None:
    if len(os.fsencode(str(path))) > UNIX_SOCKET_PATH_MAX:
        raise OSError("AF_UNIX_PATH_TOO_LONG")


def _write(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _environment(root: Path, codex_home: Path) -> dict[str, Any]:
    values = {
        "cwd": str(root), "home": os.environ.get("HOME", ""),
        "codex_home": str(codex_home), "tmpdir": os.environ.get("TMPDIR", "/tmp"),
        "term": os.environ.get("TERM", ""), "path": os.environ.get("PATH", ""),
        "auth_present": (codex_home / "auth.json").exists(),
        "config_present": (codex_home / "config.toml").exists(),
    }
    material = json.dumps(values, sort_keys=True).encode("utf-8")
    values["digest"] = hashlib.sha256(material).hexdigest()
    return values


def _recv_until(sock: socket.socket, marker: bytes, limit: int = 65536) -> bytes:
    data = bytearray()
    while marker not in data and len(data) < limit:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def _frame(payload: bytes) -> bytes:
    """Create one masked client-to-server WebSocket text frame."""
    mask = os.urandom(4)
    masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    length = len(masked)
    if length < 126:
        header = bytes((0x81, 0x80 | length))
    elif length < 65536:
        header = bytes((0x81, 0xFE)) + length.to_bytes(2, "big")
    else:
        header = bytes((0x81, 0xFF)) + length.to_bytes(8, "big")
    return header + mask + masked


def _read_frame(sock: socket.socket) -> bytes:
    header = sock.recv(2)
    if len(header) != 2:
        raise OSError("remote endpoint closed during WebSocket probe")
    length = header[1] & 0x7F
    if length == 126:
        length = int.from_bytes(sock.recv(2), "big")
    elif length == 127:
        length = int.from_bytes(sock.recv(8), "big")
    masked = bool(header[1] & 0x80)
    mask = sock.recv(4) if masked else b""
    payload = bytearray()
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            raise OSError("remote endpoint closed during WebSocket frame")
        payload.extend(chunk)
    if masked:
        return bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return bytes(payload)


def websocket_readiness(endpoint: str, *, timeout: float = 2.0) -> dict[str, Any]:
    """Perform a connection and initialize probe against one loopback WS URL."""
    if not endpoint.startswith("ws://"):
        raise ValueError("interactive remote endpoint must use ws://")
    address = endpoint.removeprefix("ws://").split("/", 1)[0]
    host, port_text = address.rsplit(":", 1)
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("remote listener is not loopback-only")
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (f"GET / HTTP/1.1\r\nHost: {host}:{port_text}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode()
    with socket.create_connection((host, int(port_text)), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        response = _recv_until(sock, b"\r\n\r\n")
        header = response.split(b"\r\n\r\n", 1)[0].decode("latin1")
        if not header.startswith("HTTP/1.1 101") or "upgrade: websocket" not in header.lower():
            raise OSError(f"unexpected WebSocket handshake: {header[:200]}")
        initialize = {"jsonrpc": "2.0", "id": "zeus-readiness",
                      "method": "initialize", "params": {
                          "clientInfo": {"name": "zeus-readiness", "version": "P5-G6"},
                          "capabilities": {}}}
        sock.sendall(_frame(json.dumps(initialize, separators=(",", ":")).encode()))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = _read_frame(sock)
            if not frame:
                continue
            opcode = frame[0] & 0x0F if len(frame) > 1 else 1
            if opcode == 8:
                break
            try:
                message = json.loads(frame.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if message.get("id") == "zeus-readiness":
                if "result" not in message:
                    raise OSError(f"initialize probe rejected: {message.get('error')}")
                return {"result": "PASS", "transport": "WEBSOCKET",
                        "protocol": "JSON-RPC", "initialize": "PASS"}
    raise TimeoutError("remote endpoint did not answer the initialize probe")


def _wait_for_listener(endpoint: str, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error = "listener did not accept a connection"
    while time.monotonic() < deadline:
        try:
            probe = websocket_readiness(endpoint, timeout=min(1.0, max(0.1, deadline - time.monotonic())))
            return {"socket_listening": True, "readiness_probe": probe,
                    "remote_endpoint_reachable": True, "remote_endpoint_identity": "PASS"}
        except (OSError, ValueError, TimeoutError) as error:
            last_error = f"{type(error).__name__}: {error}"
            time.sleep(0.05)
    raise TimeoutError(last_error)


def _run_stdio(args: argparse.Namespace) -> int:
    """Compatibility path for the managed adapter's structured stdio owner."""
    root = Path(args.root).resolve(); codex_home = Path(args.codex_home).resolve()
    log_path = Path(args.log).resolve(); ready_path = Path(args.ready).resolve()
    exit_path = Path(args.exited).resolve(); control_path = Path(args.control).resolve()
    _validate_control_socket(control_path)
    log_path.parent.mkdir(parents=True, exist_ok=True); ready_path.parent.mkdir(parents=True, exist_ok=True)
    control_path.parent.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ); environment["CODEX_HOME"] = str(codex_home)
    command = [args.codex_bin, *(args.provider_argument or ["app-server", "--stdio"])]
    provider: subprocess.Popen[bytes] | None = None
    server: socket.socket | None = None
    try:
        with log_path.open("ab") as log:
            provider = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        start_new_session=False, bufsize=0)
            assert provider.stdin is not None and provider.stdout is not None
            request = {"jsonrpc":"2.0", "id":1, "method":"initialize",
                       "params":{"clientInfo":{"name":"zeus","version":"P5-G6"},"capabilities":{}}}
            provider.stdin.write((json.dumps(request, separators=(",", ":")) + "\n").encode()); provider.stdin.flush()
            response = None; deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                line = provider.stdout.readline()
                if not line: break
                log.write(line); log.flush()
                try: value = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError: continue
                if value.get("id") == 1: response = value; break
            if not response or "result" not in response:
                _write(ready_path, {"result":"FAIL", "provider_pid":provider.pid, "command":command,
                                    "provider_mode":"MANAGED_STDIO", "transport":"STDIO",
                                    "error":"APP_SERVER_HANDSHAKE_FAILED", "exit_code":provider.poll()})
                return 1
            if control_path.exists(): control_path.unlink()
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); server.bind(str(control_path)); server.listen(4)
            server.setblocking(False)
            _write(ready_path, {"result":"PASS", "provider_pid":provider.pid, "command":command,
                                "provider_mode":"MANAGED_STDIO",
                                "transport":"STDIO", "remote_capable":False, "control_socket":str(control_path),
                                "environment":_environment(root, codex_home), "handshake":"PASS"})
            clients: list[socket.socket] = []
            while provider.poll() is None:
                readable, _, _ = select.select([server, provider.stdout] + clients, [], [], .25)
                if server in readable:
                    client, _ = server.accept(); client.setblocking(False); clients.append(client)
                for client in list(clients):
                    if client in readable:
                        data = client.recv(65536)
                        if not data: clients.remove(client); client.close()
                        else: provider.stdin.write(data); provider.stdin.flush()
                if provider.stdout in readable:
                    data = os.read(provider.stdout.fileno(), 65536)
                    if not data: break
                    log.write(data); log.flush()
                    for client in list(clients):
                        try: client.sendall(data)
                        except OSError: clients.remove(client); client.close()
            for client in clients: client.close()
            code = provider.wait(); _write(exit_path, {"result":"PASS" if code == 0 else "FAIL",
                                                       "completion":"NORMAL" if code == 0 else "ABNORMAL",
                                                       "provider_pid":provider.pid, "exit_code":code})
            return code
    except Exception as error:
        _write(ready_path, {"result":"FAIL", "command":command, "error_type":type(error).__name__, "error":str(error),
                            "error_code":"AF_UNIX_PATH_TOO_LONG" if "AF_UNIX_PATH_TOO_LONG" in str(error) else "BROKER_START_FAILED",
                            "provider_mode":"MANAGED_STDIO", "transport":"STDIO"})
        return 1
    finally:
        if server is not None: server.close()
        if control_path.exists(): control_path.unlink()
        if provider is not None and provider.poll() is None: provider.terminate()


def run(args: argparse.Namespace) -> int:
    if args.listen is None:
        return _run_stdio(args)
    root = Path(args.root).resolve(); codex_home = Path(args.codex_home).resolve()
    log_path = Path(args.log).resolve(); ready_path = Path(args.ready).resolve()
    exit_path = Path(args.exited).resolve(); endpoint = args.listen
    log_path.parent.mkdir(parents=True, exist_ok=True); ready_path.parent.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ); environment["CODEX_HOME"] = str(codex_home)
    command = [args.codex_bin, "app-server", "--listen", endpoint]
    provider: subprocess.Popen[bytes] | None = None
    diagnostics: dict[str, Any] = {"failure_phase": None, "startup_command": command,
                                   "transport": "WEBSOCKET", "endpoint_uri": endpoint,
                                   "bind_address": endpoint.removeprefix("ws://").rsplit(":", 1)[0],
                                   "provider_mode": "INTERACTIVE_REMOTE"}
    try:
        with log_path.open("ab") as log:
            provider = subprocess.Popen(command, cwd=root, env=environment,
                                        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                        start_new_session=True)
            diagnostics.update({"listener_process_started": True, "listener_pid": provider.pid})
            probe = _wait_for_listener(endpoint, args.timeout)
            diagnostics.update({"result": "PASS", "provider_pid": provider.pid,
                                "remote_endpoint": endpoint,
                                "listener_state": "READY", "remote_capable": True,
                                "listener_process_alive": provider.poll() is None,
                                "endpoint_uri_valid": True, **probe,
                                "environment": _environment(root, codex_home)})
            _write(ready_path, diagnostics)
            code = provider.wait()
            _write(exit_path, {"result": "PASS" if code == 0 else "FAIL",
                               "completion": "NORMAL" if code == 0 else "ABNORMAL", "provider_pid": provider.pid,
                               "exit_code": code, "endpoint_uri": endpoint})
            return code
    except Exception as error:
        diagnostics.update({"result": "FAIL", "failure_phase": "READINESS_PROBE_STARTED",
                            "error_type": type(error).__name__, "error": str(error),
                            "listener_exit_code": provider.poll() if provider else None,
                            "listener_stderr": "see log_path", "log_path": str(log_path)})
        _write(ready_path, diagnostics)
        return 1
    finally:
        if provider is not None and provider.poll() is None:
            provider.terminate()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True); parser.add_argument("--codex-home", required=True)
    parser.add_argument("--log", required=True); parser.add_argument("--ready", required=True)
    parser.add_argument("--exited", required=True); parser.add_argument("--listen")
    parser.add_argument("--control"); parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--provider-argument", action="append")
    parser.add_argument("--timeout", type=float, default=15.0)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
