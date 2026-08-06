"""Focused P5-G6 Zeus-owned Codex adapter tests."""

from __future__ import annotations

import json
import importlib.util
from importlib.machinery import SourceFileLoader
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from scripts.lib.emp import codex_adapter

ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
_ZEUS_SPEC = importlib.util.spec_from_loader("zeus_cli", SourceFileLoader("zeus_cli", str(ROOT / "scripts/zeus")))
zeus = importlib.util.module_from_spec(_ZEUS_SPEC)
assert _ZEUS_SPEC.loader is not None
_ZEUS_SPEC.loader.exec_module(zeus)


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.runtime_directory = tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-")
        self.runtime = Path(self.runtime_directory.name)

    def tearDown(self):
        self.runtime_directory.cleanup()

    def test_every_codex_action_has_one_explicit_controller(self):
        self.assertEqual(zeus.CODEX_CONTROLLER_ROUTING, {
            "status": "managed.status", "logs": "managed.logs", "artifacts": "managed.artifacts",
            "start": "managed.start", "resume": "managed.resume", "stop": "managed.stop",
            "shell": "interactive.shell", "interactive": "interactive.shell", "attach": "interactive.attach",
            "reconcile": "reconciliation.reconcile",
        })

    def test_status_is_read_only_and_not_started_before_operator_action(self):
        before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        value = codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(value["result"], "PASS")
        self.assertIn(value["state"], {"NOT_STARTED", "READY", "STOPPED", "INTERRUPTED"})
        self.assertTrue(value["read_only"])
        self.assertEqual(before, after)

    def test_start_requires_explicit_operator_approval(self):
        with self.assertRaises(codex_adapter.CodexAdapterError) as context:
            codex_adapter.start(ROOT, MISSION, approval=False)
        self.assertEqual(context.exception.code, "OPERATOR_APPROVAL_REQUIRED")

    def test_session_identity_is_deterministic_and_bound(self):
        package = {"execution_id": "EXECUTION-1", "provider_id": "zeus-local-loneal-01", "repository_identity": "git@example/repo"}
        self.assertEqual(codex_adapter.session_identifier(package), codex_adapter.session_identifier(package))
        altered = dict(package, provider_id="other-provider")
        self.assertNotEqual(codex_adapter.session_identifier(package), codex_adapter.session_identifier(altered))

    def test_zeus_cli_exposes_only_zeus_codex_surface(self):
        result = subprocess.run([str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "status", MISSION, "--json"], cwd=ROOT,
                                capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["result"], "PASS")
        self.assertIn(value["next_authorized_action"], {"START_CODEX_SESSION", "RESUME_CODEX_SESSION", "CONTINUE_CONTROLLED_MISSION_WORK"})

    def test_execution_start_remains_the_input_authority(self):
        value = codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        self.assertNotIn("invocation_provenance_baseline", value)
        self.assertNotIn("execution_start_provenance_baseline", value)
        self.assertIn(value["execution_bound"], {True, False})

    def test_startup_diagnostics_and_handshake_are_projected_without_work(self):
        value = codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        if value["state"] == "READY":
            self.assertEqual(value["app_server_handshake"], "PASS")
            self.assertIn(value["process_alive"], {True, False})
            self.assertIn(value["provider_process"], {"RUNNING", "STOPPED"})
            self.assertFalse(value["mission_work_started"])
            self.assertFalse(value["repository_work_started"])
            self.assertTrue(value["startup_diagnostics"]["config_present"])
            self.assertIn("digest", value["startup_diagnostics"])

    def test_broker_control_socket_reuses_ready_app_server_transport(self):
        with tempfile.TemporaryDirectory(prefix="zeus-broker-") as temporary:
            root = Path(temporary)
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                probe.bind(str(root / "probe.sock"))
            except PermissionError:
                self.skipTest("sandbox does not permit Unix-domain socket bind")
            finally:
                probe.close()
            fake = root / "fake-codex"
            fake.write_text("""#!/usr/bin/env python3
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request.get('id') == 1:
        print(json.dumps({'jsonrpc':'2.0','id':1,'result':{}}), flush=True)
    elif request.get('id') == 2:
        print(json.dumps({'jsonrpc':'2.0','id':2,'result':{'thread':{'id':'BROKER-THREAD'}}}), flush=True)
""", encoding="utf-8")
            fake.chmod(0o755)
            log = root / "provider.log"
            ready = root / "ready.json"
            exited = root / "exited.json"
            control = root / "control.sock"
            command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker", "--root", str(ROOT),
                       "--codex-home", str(root / "codex-home"), "--log", str(log), "--ready", str(ready),
                       "--exited", str(exited), "--control", str(control), "--codex-bin", str(fake)]
            broker = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.time() + 8
                while not ready.exists() and time.time() < deadline:
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), broker.stderr.read().decode() if broker.poll() is not None else "")
                diagnostics = json.loads(ready.read_text(encoding="utf-8"))
                self.assertEqual(diagnostics.get("handshake"), "PASS", diagnostics)
                self.assertEqual(diagnostics["control_socket"], str(control))
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(str(control))
                client.sendall(b'{"jsonrpc":"2.0","id":2,"method":"thread/start","params":{}}\n')
                self.assertIn(b'BROKER-THREAD', client.recv(4096))
                client.close()
            finally:
                broker.terminate()
                broker.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
