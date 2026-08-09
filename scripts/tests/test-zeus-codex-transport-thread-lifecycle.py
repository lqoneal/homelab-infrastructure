"""Regression tests for independent Codex transport and persisted-thread lifecycles."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import codex_adapter, codex_reconciliation


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
THREAD = "019fe4e4-26c2-7462-a4b6-197f7183dae0"


class FakeProcess:
    def __init__(self, pid: int = 991001):
        self.pid = pid
        self.terminated = False
        self.killed = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return 0


class CodexTransportThreadLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-thread-lifecycle-")
        self.runtime = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def package(self):
        value = {
            "mission_id": MISSION, "wop_id": "WOP-BOUND", "execution_id": "EXECUTION-BOUND",
            "execution_session_id": "EXECUTION-SESSION-BOUND", "provider_id": codex_adapter.PROVIDER_ID,
            "provider_session_id": "PROVIDER-SESSION-BOUND", "provider_invocation_id": "INVOCATION-BOUND",
            "repository": str(ROOT), "repository_identity": "git@example/homelab",
            "repository_id": "homelab-test", "repository_fingerprint": "fingerprint",
            "package_digest": "mutable-package-digest", "authority": {"integrity": "PASS"},
        }
        value["session_id"] = codex_adapter.session_identifier(value)
        return value

    def session(self, *, persisted=True, corrupt=False, live=False, **overrides):
        package = self.package()
        session_id = package.pop("session_id")
        codex_home = self.runtime / codex_adapter.CODEX_HOME_DIR / session_id
        rollout = codex_home / "sessions/2026/08/09" / f"rollout-{THREAD}.jsonl"
        rollout.parent.mkdir(parents=True, exist_ok=True)
        if persisted:
            rollout.write_text("not-json\n" if corrupt else json.dumps({"session_meta": {"id": THREAD}}) + "\n",
                               encoding="utf-8")
        log = self.runtime / codex_adapter.LOG_DIR / f"{session_id}.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        value = {
            **package, "schema_version": 1, "session_id": session_id, "session_disposition": "CURRENT",
            "state": "READY", "pid": os.getpid() if live else 991101,
            "provider_pid": os.getpid() if live else 991102,
            "provider_mode": "APP_SERVER_MANAGED", "provider_transport": "STDIO",
            "native_thread_id": THREAD, "native_session_id": THREAD,
            "native_thread_path": str(rollout), "native_thread_cwd": str(ROOT),
            "native_thread_ephemeral": False, "startup_diagnostics": {"codex_home": str(codex_home)},
            "log_path": str(log), "event_directory": str(self.runtime / codex_adapter.EVENT_DIR / session_id),
            "path": str(self.runtime / codex_adapter.STAGE_DIR / f"{session_id}.json"),
            "control_socket": str(self.runtime / "control.sock"),
            "mission_work_started": False, "repository_work_started": False,
        }
        value.update(overrides)
        return value

    def save(self, session):
        return codex_adapter._save(self.runtime, session)

    def diagnostics(self, session, process):
        return {
            "provider_pid": process.pid, "command": ["codex", "app-server", "--stdio"],
            "environment": {"codex_home": session["startup_diagnostics"]["codex_home"]},
            "control_socket": str(self.runtime / "replacement.sock"), "remote_endpoint": None,
            "broker_identity": {"pid": process.pid}, "provider_identity": {"pid": process.pid},
        }

    def native_response(self, request, *, fork=False):
        thread_id = "019fe4e4-fork-7000-a4b6-197f7183dae0" if fork else THREAD
        thread = {"id": thread_id, "sessionId": THREAD, "path": self.session()["native_thread_path"],
                  "cwd": str(ROOT), "status": {"type": "idle"}}
        if fork:
            thread["forkedFromId"] = THREAD
        return {"jsonrpc": "2.0", "id": request["id"], "result": {"thread": thread}}

    def test_live_transport_valid_thread_is_attachable(self):
        value = codex_adapter.thread_lifecycle(ROOT, self.session(live=True), runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "ACTIVE_OR_ATTACHABLE")
        self.assertEqual(value["runtime_recovery_action"], "ATTACH_OR_CONTINUE")

    def test_dead_transport_valid_thread_is_resumable(self):
        value = codex_adapter.thread_lifecycle(ROOT, self.session(), runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "TRANSPORT_STOPPED_THREAD_RESUMABLE")
        self.assertEqual(value["runtime_recovery_action"], "RESTART_CODEX_TRANSPORT_AND_RESUME_THREAD")

    def test_dead_transport_does_not_require_thread_replacement(self):
        value = codex_adapter.thread_lifecycle(ROOT, self.session(), runtime_root=self.runtime)
        self.assertTrue(value["transport_replacement_required"])
        self.assertFalse(value["thread_replacement_required"])

    def test_replacement_transport_resumes_same_native_thread(self):
        session = self.save(self.session())
        process = FakeProcess(os.getpid())
        requests = []
        with patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, self.diagnostics(session, process))), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "_control_request", side_effect=lambda _socket, request, **_: (
                 requests.append(request) or self.native_response(request))):
            value = codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual([item["method"] for item in requests], ["thread/read", "thread/resume"])
        self.assertEqual(value["thread_id_before"], THREAD)
        self.assertEqual(value["thread_id_after"], THREAD)
        self.assertTrue(value["same_native_thread"])

    def test_bindings_survive_native_resume(self):
        session = self.save(self.session())
        process = FakeProcess(os.getpid())
        with patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, self.diagnostics(session, process))), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "_control_request", side_effect=lambda _socket, request, **_: self.native_response(request)):
            codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        saved = codex_adapter._existing(self.runtime, MISSION)
        for field in ("mission_id", "wop_id", "execution_id", "execution_session_id",
                      "provider_id", "provider_session_id", "repository_id"):
            self.assertEqual(saved[field], session[field])

    def test_transport_recovery_does_not_mark_mission_work_started(self):
        self.assertFalse(self._successful_recovery()["mission_work_started"])

    def test_transport_recovery_does_not_mark_repository_work_started(self):
        self.assertFalse(self._successful_recovery()["repository_work_started"])

    def _successful_recovery(self):
        session = self.save(self.session())
        process = FakeProcess(os.getpid())
        with patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, self.diagnostics(session, process))), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "_control_request", side_effect=lambda _socket, request, **_: self.native_response(request)):
            return codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)

    def test_repeated_recovery_is_idempotent(self):
        session = self.save(self.session(live=True))
        with patch.object(codex_adapter, "_provider_control_ready", return_value=True), \
             patch.object(codex_adapter, "_launch_handshake") as launch:
            value = codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        launch.assert_not_called()
        self.assertEqual(value["duplicate_codex_session"], "IDEMPOTENT")
        self.assertEqual(value["session_id"], session["session_id"])

    def test_duplicate_concurrent_transport_owner_is_rejected(self):
        session = self.save(self.session())
        self.save(self.session(live=True, session_id="CODEX-OTHER",
                               path=str(self.runtime / codex_adapter.STAGE_DIR / "CODEX-OTHER.json")))
        value = codex_adapter.thread_lifecycle(ROOT, session, runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "THREAD_RECOVERY_BLOCKED")
        self.assertEqual(value["runtime_recovery_action"], "RESOLVE_CODEX_THREAD_OWNERSHIP_CONFLICT")

    def test_partial_transport_owner_blocks_replacement(self):
        session = self.session(pid=os.getpid(), provider_pid=991102)
        value = codex_adapter.thread_lifecycle(ROOT, session, runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "THREAD_RECOVERY_BLOCKED")
        self.assertEqual(value["runtime_recovery_action"], "RESOLVE_CODEX_TRANSPORT_OWNERSHIP")
        self.assertFalse(value["transport_replacement_safe"])

    def test_missing_thread_fails_closed(self):
        value = codex_adapter.thread_lifecycle(ROOT, self.session(persisted=False), runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "THREAD_RECOVERY_BLOCKED")
        self.assertFalse(value["thread_resume_eligible"])

    def test_corrupt_thread_fails_closed(self):
        value = codex_adapter.thread_lifecycle(ROOT, self.session(corrupt=True), runtime_root=self.runtime)
        self.assertEqual(value["thread_persistence_state"], "INVALID")
        self.assertEqual(value["runtime_classification"], "THREAD_RECOVERY_BLOCKED")

    def test_wrong_mission_binding_fails(self):
        package = self.package(); package["mission_id"] = "OTHER-MISSION"
        with self.assertRaises(codex_adapter.CodexAdapterError):
            codex_adapter._verify_session_package_binding(self.session(), package)

    def test_wrong_execution_binding_fails(self):
        package = self.package(); package["execution_id"] = "OTHER-EXECUTION"
        with self.assertRaises(codex_adapter.CodexAdapterError):
            codex_adapter._verify_session_package_binding(self.session(), package)

    def test_wrong_provider_binding_fails(self):
        package = self.package(); package["provider_id"] = "other-provider"
        with self.assertRaises(codex_adapter.CodexAdapterError):
            codex_adapter._verify_session_package_binding(self.session(), package)

    def test_wrong_repository_binding_fails(self):
        response = self.native_response({"id": "wrong-repository"})
        response["result"]["thread"]["cwd"] = "/tmp/not-this-repository"
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            codex_adapter._validate_native_thread_response(response, expected_thread_id=THREAD, repository=ROOT)
        self.assertEqual(raised.exception.code, "REPOSITORY_BINDING_MISMATCH")

    def test_authority_failure_blocks_before_transport_launch(self):
        self.save(self.session())
        with patch.object(codex_adapter, "_package", side_effect=codex_adapter.CodexAdapterError(
                "AUTHORITY_FAILURE", "authority failed")), \
             patch.object(codex_adapter, "_launch_handshake") as launch:
            with self.assertRaises(codex_adapter.CodexAdapterError):
                codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        launch.assert_not_called()

    def test_fork_only_when_explicitly_requested(self):
        session = self.save(self.session())
        process = FakeProcess(os.getpid()); methods = []
        def response(_socket, request, **_kwargs):
            methods.append(request["method"])
            return self.native_response(request, fork=request["method"] == "thread/fork")
        with patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, self.diagnostics(session, process))), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "_control_request", side_effect=response):
            value = codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime, fork_thread=True)
        self.assertEqual(methods, ["thread/read", "thread/fork"])
        self.assertEqual(value["duplicate_codex_session"], "FORKED")

    def test_fork_preserves_native_lineage(self):
        response = self.native_response({"id": "fork"}, fork=True)
        value = codex_adapter._validate_native_thread_response(
            response, expected_thread_id=None, repository=ROOT, forked_from_id=THREAD)
        self.assertEqual(value["native_thread_forked_from_id"], THREAD)
        self.assertNotEqual(value["native_thread_id"], THREAD)

    def test_resume_failure_never_falls_back_to_thread_start(self):
        session = self.save(self.session()); process = FakeProcess(); methods = []
        def reject(_socket, request, **_kwargs):
            methods.append(request["method"])
            if request["method"] == "thread/resume":
                raise codex_adapter.CodexAdapterError("PROVIDER_REQUEST_REJECTED", "resume rejected")
            return self.native_response(request)
        with patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, self.diagnostics(session, process))), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "_control_request", side_effect=reject):
            with self.assertRaises(codex_adapter.CodexAdapterError):
                codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime)
        self.assertEqual(methods, ["thread/read", "thread/resume"])
        self.assertNotIn("thread/start", methods)
        self.assertTrue(process.terminated)

    def test_status_exposes_one_coherent_recovery_action(self):
        self.save(self.session())
        value = codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["next_authorized_action"], value["runtime_recovery_action"])
        self.assertEqual(value["runtime_classification"], "TRANSPORT_STOPPED_THREAD_RESUMABLE")

    def test_remote_disconnect_preserves_resumable_thread_semantics(self):
        value = codex_reconciliation._dimensions(
            {"endpoint_uri": "ws://127.0.0.1:4500", "native_thread_id": THREAD,
             "thread_persisted": True, "remote_client_pid": None}, None, {"result": "PASS"})
        self.assertEqual(value["transport_liveness"], "STOPPED")
        self.assertTrue(value["thread_resume_eligible"])
        self.assertFalse(value["thread_replacement_required"])
        self.assertEqual(value["session_next_authorized_action"], "RESTART_REMOTE_TRANSPORT_AND_RESUME_THREAD")

    def test_read_only_status_does_not_mutate_runtime(self):
        self.save(self.session())
        before = {path.relative_to(self.runtime): path.read_bytes() for path in self.runtime.rglob("*") if path.is_file()}
        codex_adapter.status(ROOT, MISSION, runtime_root=self.runtime)
        after = {path.relative_to(self.runtime): path.read_bytes() for path in self.runtime.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_stopped_transport_with_no_thread_restarts_without_creating_thread(self):
        session = self.session(native_thread_id=None, native_session_id=None, native_thread_path=None)
        value = codex_adapter.thread_lifecycle(ROOT, session, runtime_root=self.runtime)
        self.assertEqual(value["runtime_classification"], "TRANSPORT_STOPPED_THREAD_NOT_CREATED")
        self.assertEqual(value["runtime_recovery_action"], "RESTART_CODEX_TRANSPORT")


if __name__ == "__main__":
    unittest.main()
