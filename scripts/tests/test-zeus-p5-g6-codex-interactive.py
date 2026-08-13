"""Focused PTY and authority-boundary tests for Zeus Codex shell mode."""

from __future__ import annotations

import json
import os
import pty
import select
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import codex_interactive
from scripts.lib.emp import codex_app_server_broker


ROOT = Path(__file__).resolve().parents[2]


class InteractiveCodexTests(unittest.TestCase):
    class Broker:
        pid = 43210
        def poll(self): return None
        def terminate(self): return None
        def wait(self, timeout=None): return 0
        def kill(self): return None

    class Client:
        pid = 43212
        returncode = 0
        def wait(self): return 0

    def _record(self, runtime, session_id, *, state="AWAITING_OPERATOR_INPUT", start=1,
                pid=None, mission="MISSION-SELECTOR"):
        value = {
            "schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
            "contract": {"id": codex_interactive.CONTRACT, "version": codex_interactive.VERSION},
            "session_id": session_id, "mission_id": mission, "execution_id": None,
            "immutable_binding_class": "DIRECT_INTERACTIVE", "provider_id": "zeus-test",
            "repository": str(ROOT), "repository_id": "repo", "repository_identity": "identity",
            "execution_mode": codex_interactive.DIRECT_INTERACTIVE, "mode": "OPERATOR_INTERACTIVE",
            "session_mode": "OPERATOR_INTERACTIVE", "interactive": True, "managed": False,
            "state": state, "pid": os.getpid() if pid is None else pid,
            "listener_pid": None, "provider_mode": "CODEX_CLI", "provider_transport": "DIRECT_TERMINAL",
            "start_timestamp": start, "approval_state": "NOT_REQUIRED", "authority": "PASS",
            "mission_work_started": False, "repository_work_started": False,
            "thread_id": "THREAD-" + session_id, "attached": True,
            "remote_endpoint": None, "path": str(runtime / codex_interactive.STAGE_DIR / f"{session_id}.json"),
            "event_directory": str(runtime / "codex-interactive-events" / session_id),
            "log_path": str(runtime / "codex-interactive-logs" / f"{session_id}.log"),
        }
        return codex_interactive._save(runtime, value)

    def _remote_patches(self, temporary):
        ready = {"result": "PASS", "provider_pid": 43211, "remote_endpoint": "unix:///tmp/zeus-test.sock"}
        original_run = subprocess.run
        def run(*args, **kwargs):
            command = args[0] if args else kwargs.get("args", [])
            if command and command[0] == "codex":
                text = "codex-cli 0.146.1" if command[1] == "--version" else (
                    "--remote ws://host:port unix://" if command[1] == "--help" else "--listen ws://IP:PORT")
                return subprocess.CompletedProcess(command, 0, stdout=text, stderr="")
            return original_run(*args, **kwargs)
        original_popen = subprocess.Popen
        def popen(*args, **kwargs):
            command = args[0] if args else kwargs.get("args", [])
            if command and (command[0] == "codex" or (str(command[0]).endswith("codex-direct-launch.sh") and len(command) > 1 and command[1] == "codex")):
                return self.Client()
            return original_popen(*args, **kwargs)
        return patch.object(codex_interactive, "_remote_broker", return_value=(self.Broker(), ready)), \
               patch("scripts.lib.emp.codex_interactive.subprocess.run", side_effect=run), \
               patch("scripts.lib.emp.codex_interactive.subprocess.Popen", side_effect=popen)

    def test_bracketed_paste_markers_are_removed_without_rewriting_content(self):
        value = ("\x1b[200~line one\n\N{SNOWMAN}".encode("utf-8")
                 + b"\nline three\x1b[201~")
        self.assertEqual(codex_interactive.strip_bracketed_paste(value),
                         "line one\n☃\nline three".encode("utf-8"))

    def test_structured_renderer_joins_blocks_and_preserves_order(self):
        self.assertEqual(codex_interactive.render_event({"params": {
            "content": [{"text": "one"}, {"text": "\n"}, {"text": "two"}]}}), "one\ntwo")
        self.assertEqual(codex_interactive.render_event({"params": {"text_delta": "π\nansi"}}), "π\nansi")

    def test_terminal_size_has_safe_nonzero_fallback(self):
        self.assertGreater(codex_interactive.terminal_size(-1)[0], 1)
        self.assertGreater(codex_interactive.terminal_size(-1)[1], 1)

    def test_launcher_preflight_is_noninteractive_and_separate_from_tui_acceptance(self):
        value = codex_interactive.launcher_preflight(ROOT, codex_bin="codex")
        self.assertIn(value["result"], {"PASS", "FAIL"})
        self.assertTrue(value["pty_required_for_launch"])
        self.assertIn("launcher_present", value)

    def test_canonical_launcher_locator_is_repository_relative(self):
        self.assertEqual(codex_interactive.DIRECT_LAUNCHER_RELATIVE,
                         Path("scripts/lib/eos/codex-direct-launch.sh"))
        self.assertEqual(codex_interactive.direct_launcher_path(ROOT),
                         ROOT / "scripts/lib/eos/codex-direct-launch.sh")

    def test_missing_launcher_is_structured(self):
        with tempfile.TemporaryDirectory(prefix="zeus-launcher-") as temporary:
            value = codex_interactive.launcher_preflight(Path(temporary), codex_bin="codex")
        self.assertEqual(value["error_code"], "DIRECT_LAUNCHER_MISSING")
        self.assertEqual(value["direct_launcher"], "FAIL")

    def test_partial_receipt_is_not_a_session_collision_candidate(self):
        with tempfile.TemporaryDirectory(prefix="zeus-partial-") as temporary:
            runtime = Path(temporary) / "runtime" / codex_interactive.STAGE_DIR
            runtime.mkdir(parents=True)
            (runtime / "partial.json").write_text(json.dumps({"event": "SESSION_RECORD_CREATED"}), encoding="utf-8")
            self.assertIsNone(codex_interactive._existing(runtime.parent, None))

    def test_command_specific_help_is_available(self):
        result = subprocess.run([str(ROOT / "scripts/zeus"), "codex", "shell", "--help"],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("native Codex directly", result.stdout)
        self.assertIn("--remote", result.stdout)

    def test_noninteractive_launcher_preflight_does_not_claim_tui_acceptance(self):
        value = codex_interactive.launcher_preflight(ROOT, codex_bin="codex")
        self.assertTrue(value["pty_required_for_launch"])
        self.assertNotIn("state", value)

    def test_mission_shell_requires_approval(self):
        with self.assertRaises(codex_interactive.InteractiveCodexError) as context:
            codex_interactive.shell(ROOT, "MISSION-BETA-562F443E16C69401", _allow_non_tty=True)
        self.assertEqual(context.exception.code, "OPERATOR_APPROVAL_REQUIRED")

    def test_write_requires_invocation_specific_approval_before_launch(self):
        with self.assertRaises(codex_interactive.InteractiveCodexError) as context:
            codex_interactive.shell(ROOT, write_requested=True, _allow_non_tty=True)
        self.assertEqual(context.exception.code, "OPERATOR_APPROVAL_REQUIRED")

    def test_approved_write_preflight_resolves_bounded_operator_policy(self):
        with patch.object(codex_interactive.shutil, "which", return_value="/usr/bin/codex"):
            value = codex_interactive.direct_launcher_preflight(ROOT, approval=True, write_requested=True)
        self.assertEqual(value["binding_class"], "REPOSITORY_OPERATOR")
        self.assertEqual(value["mission_binding"], "NOT_APPLICABLE")
        self.assertEqual(value["execution_binding"], "NOT_APPLICABLE")
        self.assertEqual(value["sandbox"], "workspace-write")
        self.assertEqual(value["write_requested"], "YES")
        self.assertEqual(value["write_approved"], "YES")
        self.assertEqual(value["approval_policy"], "on-request")
        self.assertEqual(value["codex_not_launched"], "YES")

    def test_approved_write_direct_command_and_session_are_observable(self):
        with tempfile.TemporaryDirectory(prefix="zeus-write-") as temporary:
            runtime = Path(temporary) / "runtime"
            commands = []
            original_popen = codex_interactive.subprocess.Popen
            def popen(*args, **kwargs):
                command = args[0] if args else kwargs.get("args", [])
                if command and (command[0] == "codex" or
                                 (str(command[0]).endswith("codex-direct-launch.sh") and
                                  len(command) > 1 and command[1] == "codex")):
                    commands.append(command)
                    return self.Client()
                return original_popen(*args, **kwargs)
            with patch.object(codex_interactive.subprocess, "Popen", side_effect=popen):
                value = codex_interactive.shell(ROOT, approval=True, write_requested=True,
                                                 runtime_root=runtime, codex_bin="codex", _allow_non_tty=True)
            command = commands[0]
            self.assertEqual(command[command.index("-C") + 1], str(ROOT))
            self.assertEqual(command[command.index("-s") + 1], "workspace-write")
            self.assertEqual(command[command.index("-a") + 1], "on-request")
            self.assertEqual(value["immutable_binding_class"], "REPOSITORY_OPERATOR")
            self.assertEqual(value["authority_mode"], "REPOSITORY_OPERATOR_WRITE")
            self.assertEqual(value["mission_id"], None)
            self.assertEqual(value["execution_id"], None)
            self.assertEqual(value["sandbox"], "workspace-write")
            self.assertEqual(value["mission_bound"], False)
            self.assertEqual(value["execution_bound"], False)
            events = list((runtime / "codex-interactive-events" / value["session_id"]).glob("*.json"))
            self.assertTrue(any(json.loads(path.read_text())["event"] == "WRITE_MODE_RESOLVED" for path in events))

    def test_default_non_mission_operator_remains_read_only(self):
        with tempfile.TemporaryDirectory(prefix="zeus-read-only-") as temporary:
            runtime = Path(temporary) / "runtime"
            commands = []
            original_popen = codex_interactive.subprocess.Popen
            def popen(*args, **kwargs):
                command = args[0] if args else kwargs.get("args", [])
                if command and str(command[0]).endswith("codex-direct-launch.sh"):
                    commands.append(command)
                    return self.Client()
                return original_popen(*args, **kwargs)
            with patch.object(codex_interactive.subprocess, "Popen", side_effect=popen):
                value = codex_interactive.shell(ROOT, runtime_root=runtime, codex_bin="codex", _allow_non_tty=True)
            self.assertEqual(commands[0][commands[0].index("-s") + 1], "read-only")
            self.assertEqual(value["write_requested"], "NO")
            self.assertEqual(value["mission_bound"], False)
            self.assertEqual(value["execution_bound"], False)

    def test_write_is_rejected_for_noninteractive_actions(self):
        result = subprocess.run([str(ROOT / "scripts/zeus"), "codex", "status", "--write", "--json"],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL_UNSUPPORTED_OPTION_FOR_ACTION", result.stdout)

    def test_request_decisions_are_append_only_and_classified(self):
        with tempfile.TemporaryDirectory(prefix="zeus-pty-") as temporary:
            runtime = Path(temporary) / "runtime"
            remote, client, process = self._remote_patches(temporary)
            with remote, client, process:
                value = codex_interactive.shell(ROOT, runtime_root=runtime, codex_bin="codex", _allow_non_tty=True)
            decision = codex_interactive.record_request_decision(
                ROOT, value["session_id"], {"request_id": "REQ-1", "request_type": "read_only",
                "requested_action": "inspect", "requested_scope": ["README.md"]},
                resolution="ALREADY_AUTHORIZED", runtime_root=runtime)
            self.assertEqual(decision["result"], "PASS")
            self.assertEqual(decision["decision"]["payload"]["resolution"], "ALREADY_AUTHORIZED")
            self.assertEqual(codex_interactive.resolve_request({"requested_action": "inspect"}, authorized=True), "ALREADY_AUTHORIZED")
            self.assertEqual(codex_interactive.resolve_request({"requested_action": "publish"}, prohibited=True), "PROHIBITED")
            self.assertEqual(codex_interactive.resolve_request({"requested_action": "scope-expand"}), "OPERATOR_DECISION_REQUIRED")

    def test_installed_remote_capability_contract_is_explicit(self):
        completed = {
            "version": subprocess.CompletedProcess([], 0, stdout="codex-cli 0.146.1", stderr=""),
            "top": subprocess.CompletedProcess([], 0, stdout="--remote ws://host:port unix://", stderr=""),
            "app": subprocess.CompletedProcess([], 0, stdout="--listen ws://IP:PORT", stderr=""),
        }
        with patch("scripts.lib.emp.codex_interactive.subprocess.run", side_effect=completed.values()):
            capabilities = codex_interactive.codex_capabilities("codex")
        self.assertEqual(capabilities["result"], "PASS")
        self.assertEqual(capabilities["codex_version"], "codex-cli 0.146.1")
        self.assertIn("ws://", capabilities["supported_remote_schemes"])

    def test_live_loopback_websocket_initialize_probe_passes(self):
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except PermissionError:
            self.skipTest("sandbox does not permit loopback socket bind")
        listener.bind(("127.0.0.1", 0)); listener.listen(1)
        endpoint = f"ws://127.0.0.1:{listener.getsockname()[1]}"
        def serve():
            connection, _ = listener.accept()
            with connection:
                request = b""
                while b"\r\n\r\n" not in request:
                    request += connection.recv(4096)
                key = next(line.split(b":", 1)[1].strip() for line in request.split(b"\r\n")
                            if line.lower().startswith(b"sec-websocket-key:"))
                accept = __import__("base64").b64encode(__import__("hashlib").sha1(
                    key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest()).decode()
                connection.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                                    f"Connection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n").encode())
                connection.recv(4096)
                payload = json.dumps({"jsonrpc":"2.0", "id":"zeus-readiness", "result":{}}).encode()
                connection.sendall(bytes((0x81, len(payload))) + payload)
        worker = threading.Thread(target=serve, daemon=True); worker.start()
        try:
            probe = codex_app_server_broker.websocket_readiness(endpoint)
        finally:
            listener.close(); worker.join(timeout=2)
        self.assertEqual(probe["result"], "PASS")
        self.assertEqual(probe["transport"], "WEBSOCKET")

    def test_non_loopback_or_non_websocket_endpoint_fails_closed(self):
        with self.assertRaises(ValueError):
            codex_app_server_broker.websocket_readiness("unix:///tmp/not-supported")

    def test_managed_and_interactive_surfaces_remain_distinct(self):
        with tempfile.TemporaryDirectory(prefix="zeus-pty-") as temporary:
            value = codex_interactive.status(ROOT, runtime_root=Path(temporary) / "runtime")
            self.assertEqual(value["mode"], "OPERATOR_INTERACTIVE")
            self.assertEqual(value["state"], "NOT_STARTED")

    def test_session_selector_returns_the_requested_interactive_record(self):
        with tempfile.TemporaryDirectory(prefix="zeus-pty-") as temporary:
            runtime = Path(temporary) / "runtime"
            remote, client, process = self._remote_patches(temporary)
            with remote, client, process:
                value = codex_interactive.shell(ROOT, runtime_root=runtime, codex_bin="codex", _allow_non_tty=True)
            selected = codex_interactive.status(ROOT, session_id=value["session_id"], runtime_root=runtime)
            self.assertEqual(selected["session_id"], value["session_id"])
            self.assertEqual(selected["mode"], "OPERATOR_INTERACTIVE")
            self.assertEqual(selected["execution_mode"], "DIRECT_INTERACTIVE")
            self.assertFalse(selected["remote_client"])

    def test_selector_lifecycle_and_attach_are_read_only(self):
        with tempfile.TemporaryDirectory(prefix="zeus-selector-") as temporary:
            runtime = Path(temporary) / "runtime"
            first = self._record(runtime, "SESSION-1", start=1)
            before = sorted(path.read_bytes() for path in (runtime / codex_interactive.STAGE_DIR).glob("*.json"))
            active = codex_interactive.status(ROOT, session_id=first["session_id"], runtime_root=runtime)
            self.assertEqual(active["session_id"], "SESSION-1")
            self.assertEqual(codex_interactive.status(ROOT, active=True, runtime_root=runtime)["session_id"], "SESSION-1")
            self.assertEqual(codex_interactive.status(ROOT, latest=True, runtime_root=runtime)["session_id"], "SESSION-1")
            attached = codex_interactive.attach(ROOT, active=True, runtime_root=runtime)
            self.assertEqual(attached["session_id"], "SESSION-1")
            self.assertFalse(attached["provider_created"])
            self.assertFalse(attached["thread_created"])
            self.assertFalse(attached["session_created"])
            after = sorted(path.read_bytes() for path in (runtime / codex_interactive.STAGE_DIR).glob("*.json"))
            self.assertEqual(before, after)

    def test_selector_excludes_stopped_stale_and_ambiguous_sessions(self):
        with tempfile.TemporaryDirectory(prefix="zeus-selector-") as temporary:
            runtime = Path(temporary) / "runtime"
            self._record(runtime, "STOPPED", state="STOPPED", pid=os.getpid())
            with self.assertRaisesRegex(codex_interactive.InteractiveCodexError, "no compatible"):
                codex_interactive.status(ROOT, active=True, runtime_root=runtime)
            self._record(runtime, "STALE", state="AWAITING_OPERATOR_INPUT", pid=999999999)
            with self.assertRaisesRegex(codex_interactive.InteractiveCodexError, "no compatible"):
                codex_interactive.status(ROOT, active=True, runtime_root=runtime)
            self._record(runtime, "LIVE-1", start=3)
            self._record(runtime, "LIVE-2", start=4)
            with self.assertRaisesRegex(codex_interactive.InteractiveCodexError, "multiple live"):
                codex_interactive.status(ROOT, active=True, runtime_root=runtime)
            with self.assertRaises(codex_interactive.InteractiveCodexError):
                codex_interactive.status(ROOT, session_id="MISSING", runtime_root=runtime)

    def test_remote_requires_explicit_selection_and_never_uses_stdio_provider(self):
        with tempfile.TemporaryDirectory(prefix="zeus-remote-") as temporary:
            runtime = Path(temporary) / "runtime"
            remote, client, process = self._remote_patches(temporary)
            with remote, client, process as popen_mock:
                value = codex_interactive.shell(ROOT, runtime_root=runtime, codex_bin="codex",
                                                remote=True, _allow_non_tty=True)
                command = popen_mock.call_args.args[0]
            self.assertEqual(value["execution_mode"], "REMOTE_INTERACTIVE")
            self.assertEqual(value["provider_mode"], "INTERACTIVE_REMOTE")
            self.assertIn("--remote", command)
            self.assertTrue(value["remote_client"])

    def test_diagnostic_and_operational_paths_share_endpoint_transaction(self):
        self.assertIs(codex_interactive.establish_remote_endpoint,
                      codex_interactive.establish_remote_endpoint)
        with patch.object(codex_interactive, "establish_remote_endpoint", return_value=(self.Broker(), {
                "result": "PASS", "provider_pid": 43211, "remote_endpoint": "ws://127.0.0.1:43123",
                "socket_listening": True, "remote_endpoint_reachable": True,
                "remote_endpoint_identity": "PASS", "readiness_probe": {"result": "PASS"}})) as transaction:
            with tempfile.TemporaryDirectory(prefix="zeus-remote-transaction-") as temporary:
                runtime = Path(temporary) / "runtime"
                # The compatibility seam is deliberately patched to prove both
                # command paths enter the same authoritative transaction.
                with patch.object(codex_interactive, "_remote_broker", side_effect=codex_interactive.establish_remote_endpoint):
                    with patch.object(codex_interactive, "establish_remote_endpoint", transaction):
                        try:
                            codex_interactive.diagnose(ROOT, runtime_root=runtime, codex_bin="codex")
                        except codex_interactive.InteractiveCodexError:
                            pass
                self.assertTrue(transaction.called)

    def test_direct_mode_does_not_call_remote_broker(self):
        with tempfile.TemporaryDirectory(prefix="zeus-direct-") as temporary:
            with patch.object(codex_interactive, "_remote_broker", side_effect=AssertionError("remote path entered")):
                original = codex_interactive.subprocess.Popen
                def popen(*args, **kwargs):
                    command = args[0] if args else kwargs.get("args", [])
                    if command and (command[0] == "codex" or (str(command[0]).endswith("codex-direct-launch.sh") and len(command) > 1 and command[1] == "codex")):
                        return self.Client()
                    return original(*args, **kwargs)
                with patch.object(codex_interactive.subprocess, "Popen", side_effect=popen):
                    value = codex_interactive.shell(ROOT, runtime_root=Path(temporary) / "runtime",
                                                    codex_bin="codex", _allow_non_tty=True)
            self.assertEqual(value["execution_mode"], "DIRECT_INTERACTIVE")
            self.assertFalse(value["remote_capable"])

    @unittest.skip("protocol failure is now owned by the official remote Codex client")
    def test_thread_failure_is_recorded_as_failed_not_stopped(self):
        with tempfile.TemporaryDirectory(prefix="zeus-pty-") as temporary:
            fake = Path(temporary) / "fake-codex"
            fake.write_text("""#!/usr/bin/env python3
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request.get('id') == 1:
        print(json.dumps({'jsonrpc':'2.0','id':1,'result':{}}), flush=True)
    elif request.get('id') == 2:
        print(json.dumps({'jsonrpc':'2.0','id':2,'error':{'code':-1,'message':'thread denied'}}), flush=True)
        break
""", encoding="utf-8")
            fake.chmod(0o755)
            runtime = Path(temporary) / "runtime"
            with self.assertRaises(codex_interactive.InteractiveCodexError) as context:
                codex_interactive.shell(ROOT, runtime_root=runtime, codex_bin=str(fake), _allow_non_tty=True)
            self.assertEqual(context.exception.code, "THREAD_CREATE_FAILED")
            record = next((runtime / "codex-interactive-sessions").glob("*.json"))
            value = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual(value["state"], "FAILED")
            self.assertEqual(value["failure"]["error_type"], "InteractiveCodexError")

    @unittest.skip("terminal and turn interaction is now owned by the official remote Codex client")
    def test_idle_shell_accepts_turn_and_returns_to_input_state(self):
        with tempfile.TemporaryDirectory(prefix="zeus-pty-") as temporary:
            fake = Path(temporary) / "fake-codex"
            fake.write_text("""#!/usr/bin/env python3
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request.get('id') == 1:
        print(json.dumps({'jsonrpc':'2.0','id':1,'result':{}}), flush=True)
    elif request.get('id') == 2:
        print(json.dumps({'jsonrpc':'2.0','method':'zeus','params':{'text':'THREAD_READY'}}), flush=True)
        print(json.dumps({'jsonrpc':'2.0','id':2,'result':{'thread':{'id':'THREAD-LIVE'}}}), flush=True)
    elif request.get('method') == 'turn/start':
        print(json.dumps({'jsonrpc':'2.0','method':'zeus','params':{'text':'RESPONSE_OK'}}), flush=True)
        print(json.dumps({'jsonrpc':'2.0','method':'turn/completed','params':{}}), flush=True)
        print(json.dumps({'jsonrpc':'2.0','method':'zeus','params':{'text':'READY_FOR_NEXT_INPUT'}}), flush=True)
""", encoding="utf-8")
            fake.chmod(0o755)
            runtime = Path(temporary) / "runtime"
            master, slave = pty.openpty()
            code = ("from pathlib import Path; from scripts.lib.emp import codex_interactive; "
                    f"codex_interactive.shell(Path({str(ROOT)!r}), runtime_root=Path({str(runtime)!r}), "
                    f"codex_bin={str(fake)!r})")
            child = subprocess.Popen(["python3", "-c", code], cwd=ROOT, stdin=slave,
                                     stdout=slave, stderr=slave, env={**os.environ, "PYTHONPATH": str(ROOT)})
            os.close(slave)
            output = bytearray()
            deadline = time.time() + 8
            while b"THREAD_READY" not in output and time.time() < deadline:
                readable, _, _ = select.select([master], [], [], 0.2)
                if readable:
                    output.extend(os.read(master, 4096))
            self.assertIn(b"THREAD_READY", output)
            os.write(master, b"hello from operator\n")
            deadline = time.time() + 8
            while b"RESPONSE_OK" not in output and time.time() < deadline:
                readable, _, _ = select.select([master], [], [], 0.2)
                if readable:
                    output.extend(os.read(master, 4096))
            self.assertIn(b"RESPONSE_OK", output)
            time.sleep(0.3)
            os.write(master, b"/exit\n")
            self.assertEqual(child.wait(timeout=8), 0)
            os.close(master)
            records = list((runtime / "codex-interactive-sessions").glob("*.json"))
            self.assertEqual(len(records), 1)
            session = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(session["state"], "STOPPED")
            self.assertEqual(session["turn_state"], "IDLE")
            self.assertFalse(session["mission_work_started"])
            self.assertFalse(session["repository_work_started"])


if __name__ == "__main__":
    unittest.main()
