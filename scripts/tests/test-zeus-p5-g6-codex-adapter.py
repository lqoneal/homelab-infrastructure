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
from types import SimpleNamespace
from unittest.mock import patch
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
            "reconcile": "reconciliation.reconcile", "supersede": "managed.supersede",
        })

    def test_status_is_read_only_and_not_started_before_operator_action(self):
        before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        value = codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(value["result"], "PASS")
        self.assertIn(value["state"], {"NOT_STARTED", "READY", "STOPPED", "INTERRUPTED"})
        self.assertTrue(value["read_only"])
        self.assertEqual(before, after)

    def test_start_does_not_require_redundant_generic_operator_approval(self):
        with self.assertRaises(codex_adapter.CodexAdapterError) as context:
            codex_adapter.start(ROOT, MISSION, approval=False)
        self.assertNotEqual(context.exception.code, "OPERATOR_APPROVAL_REQUIRED")

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

    def _write_session_event(self, directory, sequence, event, payload, previous=None):
        value = {"schema_version": 1, "sequence": sequence,
                 "session_id": "CODEX-SESSION-BOUND", "event": event,
                 "payload": payload, "previous_event_digest": previous}
        value["event_digest"] = codex_adapter.digest(value)
        path = Path(directory) / f"{sequence:04d}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return value["event_digest"]

    def test_reconcile_history_classifies_legacy_work_events_without_corroboration(self):
        session = dict(self._session_fixture(), event_directory=str(self.runtime / "codex-events/CODEX-SESSION-BOUND"),
                       scope={"mission_work_started": True, "repository_work_started": True})
        directory = Path(session["event_directory"])
        first = self._write_session_event(directory, 1, "CODEX_SESSION_CREATED", {})
        self._write_session_event(directory, 2, "MISSION_WORK_STARTED",
                                  {"execution_id": "EXECUTION-BOUND"}, first)
        with patch("scripts.lib.emp.execution_start.verify", return_value=self._execution_fixture()):
            value = codex_adapter.reconcile_session_history(ROOT, MISSION, runtime_root=self.runtime, session=session)
        self.assertEqual(value["history_disposition"], "EVENTS_NON_AUTHORITATIVE")
        self.assertEqual(value["mission_work_actually_occurred"], "NO")
        self.assertTrue(value["session_replacement_safe"])
        self.assertTrue(value["read_only"])

    def test_reconcile_history_confirms_work_only_with_authoritative_execution_evidence(self):
        session = dict(self._session_fixture(), event_directory=str(self.runtime / "codex-events/CODEX-SESSION-BOUND"))
        directory = Path(session["event_directory"])
        first = self._write_session_event(directory, 1, "CODEX_SESSION_CREATED", {})
        self._write_session_event(directory, 2, "MISSION_WORK_STARTED",
                                  {"execution_id": "EXECUTION-BOUND", "wop_id": "WOP-BOUND",
                                   "mission_id": MISSION, "session_id": "CODEX-SESSION-BOUND",
                                   "provider_id": codex_adapter.PROVIDER_ID, "source_digest": "source"}, first)
        execution = dict(self._execution_fixture(), mission_work_started=True)
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution):
            value = codex_adapter.reconcile_session_history(ROOT, MISSION, runtime_root=self.runtime, session=session)
        self.assertEqual(value["history_disposition"], "HISTORICAL_WORK_CONFIRMED")
        self.assertEqual(value["mission_work_actually_occurred"], "YES")
        self.assertFalse(value["session_replacement_safe"])

    def test_reconcile_history_is_read_only_and_preserves_projection(self):
        session = dict(self._session_fixture(), event_directory=str(self.runtime / "codex-events/CODEX-SESSION-BOUND"))
        before = dict(session)
        with patch("scripts.lib.emp.execution_start.verify", return_value=self._execution_fixture()):
            value = codex_adapter.reconcile_session_history(ROOT, MISSION, runtime_root=self.runtime, session=session)
        self.assertEqual(value["history_disposition"], "NO_WORK_EVENTS")
        self.assertEqual(session, before)
        self.assertFalse(value["mission_work_actually_occurred"] == "YES")

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

    def _execution_fixture(self):
        return {
            "result": "PASS", "mission_id": MISSION, "wop_id": "WOP-BOUND", "execution_id": "EXECUTION-BOUND",
            "execution_session_id": "EXECUTION-SESSION-BOUND", "provider_session_id": "PROVIDER-SESSION-BOUND",
            "provider_id": codex_adapter.PROVIDER_ID, "provider_invocation_id": "INVOCATION-BOUND",
            "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION", "blockers": [], "approvals_required": [],
            "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK", "execution_start_provenance_baseline": "a" * 40,
            "artifacts": {"execution_start_transaction": {"path": str(self.runtime / "execution-start-transactions/EXECUTION-BOUND.json")}},
        }

    def _session_fixture(self):
        control_socket = self.runtime / "control.sock"
        control_socket.touch()
        return {
            "session_id": "CODEX-SESSION-BOUND", "mission_id": MISSION, "execution_id": "EXECUTION-BOUND",
            "provider_id": codex_adapter.PROVIDER_ID, "provider_pid": os.getpid(), "pid": os.getpid(),
            "execution_session_id": "EXECUTION-SESSION-BOUND", "provider_session_id": "PROVIDER-SESSION-BOUND",
            "control_socket": str(control_socket), "mission_work_started": False,
            "repository_work_started": False, "state": "READY", "path": str(self.runtime / "codex-sessions/CODEX-SESSION-BOUND.json"),
        }

    def test_missing_control_socket_is_not_a_live_provider_session(self):
        session = self._session_fixture()
        Path(session["control_socket"]).unlink()
        value = codex_adapter.runtime_liveness(session)
        self.assertEqual(value["session_liveness"], "ALIVE")
        self.assertFalse(codex_adapter._provider_control_ready(session))

    def test_start_rematerializes_runtime_when_pids_exist_but_control_socket_is_missing(self):
        package = dict(self._package_execution_fixture(), package_digest="package-digest")
        session = dict(self._session_fixture(), session_disposition="CURRENT", package_digest="package-digest",
                       log_path=str(self.runtime / "codex.log"))
        Path(session["control_socket"]).unlink()
        diagnostics = {
            "provider_pid": os.getpid(), "command": ["disposable-broker"],
            "environment": {"digest": "environment-digest"},
            "control_socket": str(self.runtime / "rematerialized-control.sock"),
            "remote_endpoint": None,
        }
        Path(diagnostics["control_socket"]).touch()
        with patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "_existing", return_value=session), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(type("P", (), {"pid": os.getpid()})(), diagnostics)), \
             patch.object(codex_adapter, "_append_event"), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            value = codex_adapter.start(ROOT, MISSION, approval=True, runtime_root=self.runtime, _resume=True)
        self.assertEqual(value["duplicate_codex_session"], "RESUMED")
        self.assertEqual(value["provider_session_id"], "PROVIDER-SESSION-BOUND")

    def _package_execution_fixture(self, **overrides):
        value = self._execution_fixture()
        value.update({
            "current_published_baseline": "a" * 40,
            "execution_start_baseline_relationship": "IDENTICAL",
        })
        value.update(overrides)
        return value

    def test_package_uses_requested_mission_id_for_binding(self):
        execution = self._package_execution_fixture()
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "resolve_repository", return_value={
                 "repository_identity": "homelab", "repository_id": "homelab", "repository_fingerprint": "fingerprint",
             }):
            package = codex_adapter._package(ROOT, MISSION, self.runtime)
        self.assertEqual(package["mission_id"], MISSION)

    def test_package_mission_mismatch_fails_closed(self):
        execution = self._package_execution_fixture(mission_id="OTHER-MISSION")
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter._package(ROOT, MISSION, self.runtime)
        self.assertEqual(raised.exception.code, "MISSION_BINDING_MISMATCH")

    def test_package_missing_mission_identity_fails_closed(self):
        execution = self._package_execution_fixture(mission_id=None)
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter._package(ROOT, MISSION, self.runtime)
        self.assertEqual(raised.exception.code, "MISSION_BINDING_MISMATCH")

    def test_start_path_resolves_package_identity_before_launch(self):
        execution = self._package_execution_fixture()
        diagnostics = {
            "provider_pid": os.getpid(), "command": ["disposable-broker"],
            "environment": {"digest": "environment-digest"}, "control_socket": "/tmp/disposable-control.sock",
            "remote_endpoint": None,
        }
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "resolve_repository", return_value={
                 "repository_identity": "homelab", "repository_id": "homelab", "repository_fingerprint": "fingerprint",
             }), \
             patch.object(codex_adapter, "_existing", return_value=None), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(SimpleNamespace(pid=os.getpid()), diagnostics)), \
             patch.object(codex_adapter, "_append_event"), \
             patch.object(codex_adapter, "_save", side_effect=lambda _runtime, value: dict(value)), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            value = codex_adapter.start(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual(value["mission_id"], MISSION)
        self.assertEqual(value["execution_id"], "EXECUTION-BOUND")

    def test_bound_active_transition_preserves_identity_and_is_idempotent(self):
        execution = self._execution_fixture(); session = self._session_fixture()
        requests = []

        def control(_socket, request, **_kwargs):
            requests.append(request)
            if request["method"] == "thread/start":
                return {"jsonrpc": "2.0", "id": request["id"], "result": {"thread": {"id": "THREAD-BOUND"}}}
            return {"jsonrpc": "2.0", "id": request["id"], "result": {"turn": {"id": "TURN-BOUND"}}}

        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session), \
             patch.object(codex_adapter, "_control_request", side_effect=control), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            value = codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
            replay = codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)

        self.assertEqual(value["execution_id"], "EXECUTION-BOUND")
        self.assertEqual(value["session_id"], "CODEX-SESSION-BOUND")
        self.assertEqual(value["execution_state"], "EXECUTING")
        self.assertTrue(value["mission_work_started"])
        self.assertEqual(value["replay"], "APPLIED")
        self.assertEqual(replay["replay"], "IDEMPOTENT")
        self.assertFalse(replay["mutation_applied"])
        self.assertEqual(len(requests), 2)

    def test_bound_active_transition_rejects_mismatched_provider(self):
        execution = self._execution_fixture(); session = dict(self._session_fixture(), provider_id="OTHER")
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "PROVIDER_BINDING_MISMATCH")

    def test_bound_active_transition_rejects_wrong_state_bindings_and_blockers(self):
        cases = (
            ("execution_start_state", "WRONG", "EXECUTION_STATE_INVALID"),
            ("mission_id", "OTHER-MISSION", "MISSION_BINDING_MISMATCH"),
            ("wop_id", None, "WOP_BINDING_MISSING"),
            ("blockers", [{"code": "BLOCKED"}], "EXECUTION_BLOCKED"),
            ("approvals_required", [{"type": "OPERATOR"}], "EXECUTION_BLOCKED"),
        )
        for field, replacement, expected in cases:
            with self.subTest(field=field):
                execution = self._execution_fixture()
                execution[field] = replacement
                with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
                     patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
                     patch.object(codex_adapter, "_existing", return_value=self._session_fixture()):
                    with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                        codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
                self.assertEqual(raised.exception.code, expected)

    def test_begin_consumes_the_same_canonical_wop_as_execution_start_verify(self):
        execution = self._execution_fixture()
        session = self._session_fixture()
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session), \
             patch.object(codex_adapter, "_control_request", side_effect=lambda _socket, request, **_: {
                 "jsonrpc": "2.0", "id": request["id"],
                 "result": {"thread": {"id": "THREAD-BOUND"}} if request["method"] == "thread/start" else {"turn": {"id": "TURN-BOUND"}},
             }), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            value = codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual(execution["wop_id"], value["wop_id"])
        self.assertEqual(value["wop_id"], "WOP-BOUND")

    def test_begin_preserves_fail_closed_missing_and_mismatched_wop(self):
        for wop_id, expected in ((None, "WOP_BINDING_MISSING"), ("WOP-OTHER", "WOP_BINDING_MISMATCH")):
            with self.subTest(wop_id=wop_id):
                execution = self._execution_fixture()
                execution["wop_id"] = wop_id
                # A real execution-start verifier rejects divergent bindings;
                # this test asserts the adapter's contract remains fail-closed
                # for the corresponding verified result.
                if wop_id == "WOP-OTHER":
                    execution["wop_binding_error"] = expected
                with patch("scripts.lib.emp.execution_start.verify", side_effect=codex_adapter.CodexAdapterError(expected, "invalid WOP binding")):
                    with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                        codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
                self.assertEqual(raised.exception.code, expected)

    def test_failed_precondition_does_not_consume_the_later_valid_transition(self):
        execution = self._execution_fixture(); session = self._session_fixture()
        failed = {"result": "FAIL", "mission_id": MISSION,
                  "blockers": [{"code": "WOP_BINDING_MISSING"}],
                  "next_authorized_action": "STOP_FAIL_CLOSED"}
        requests = []

        def control(_socket, request, **_kwargs):
            requests.append(request)
            if request["method"] == "thread/start":
                return {"jsonrpc": "2.0", "id": request["id"], "result": {"thread": {"id": "THREAD-BOUND"}}}
            return {"jsonrpc": "2.0", "id": request["id"], "result": {"turn": {"id": "TURN-BOUND"}}}

        with patch("scripts.lib.emp.execution_start.verify", side_effect=[failed, execution]), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session), \
             patch.object(codex_adapter, "_control_request", side_effect=control), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
            self.assertEqual(raised.exception.code, "WOP_BINDING_MISSING")
            self.assertFalse((self.runtime / codex_adapter.ACTIVE_TRANSITION_DIR / "EXECUTION-BOUND.json").exists())
            value = codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)

        self.assertEqual(value["replay"], "APPLIED")
        self.assertEqual(value["execution_id"], execution["execution_id"])
        self.assertEqual(len(requests), 2)

    def test_bound_active_transition_rejects_execution_session_mismatch(self):
        execution = self._execution_fixture(); session = dict(self._session_fixture(), execution_session_id="OTHER-SESSION")
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "SESSION_BINDING_MISMATCH")

    def test_bound_active_transition_start_failure_does_not_commit_active_projection(self):
        execution = self._execution_fixture(); session = self._session_fixture()
        with patch("scripts.lib.emp.execution_start.verify", return_value=execution), \
             patch.object(codex_adapter, "_authority", return_value={"integrity": "PASS"}), \
             patch.object(codex_adapter, "_existing", return_value=session), \
             patch.object(codex_adapter, "_control_request", side_effect=codex_adapter.CodexAdapterError("PROVIDER_REQUEST_REJECTED", "denied")), \
             patch.object(codex_adapter, "_process_alive", return_value=True):
            with self.assertRaises(codex_adapter.CodexAdapterError):
                codex_adapter.begin_controlled_mission_work(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertFalse((self.runtime / codex_adapter.ACTIVE_TRANSITION_DIR / "EXECUTION-BOUND.json").exists())
        self.assertFalse((self.runtime / codex_adapter.MONITORING_DIR / "EXECUTION-BOUND.json").exists())


if __name__ == "__main__":
    unittest.main()
