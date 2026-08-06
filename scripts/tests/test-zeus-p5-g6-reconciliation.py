"""Disposable-runtime coverage for the P5-G6 reconciliation controller."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from scripts.lib.emp import codex_reconciliation
from scripts.lib.emp import codex_interactive
from scripts.lib.emp.production_execution import digest


ROOT = Path(__file__).resolve().parents[2]


class ReconciliationTests(unittest.TestCase):
    def test_process_identity_uses_boot_and_proc_ticks_not_wall_clock(self):
        process = subprocess.Popen(["sleep", "30"])
        try:
            identity = codex_reconciliation.process_identity(process.pid)
            self.assertIn("boot_id", identity)
            self.assertIsInstance(identity["process_start_ticks"], int)
            self.assertEqual(identity["starttime"], str(identity["process_start_ticks"]))
            self.assertEqual(identity["process_identity_digest"], identity["identity"])
            legacy = dict(identity, start_timestamp=time.time())
            self.assertNotEqual(codex_reconciliation._canonical_identity(legacy)["process_start_ticks"],
                                int(time.time()))
        finally:
            process.terminate(); process.wait(timeout=3)

    def test_legacy_identity_recovers_only_from_immutable_evidence(self):
        process = subprocess.Popen(["sleep", "30"])
        try:
            identity = codex_reconciliation.process_identity(process.pid)
            legacy = {"pid": process.pid, "process_group": identity["process_group"],
                      "command_digest": identity["command_digest"], "executable": identity["executable"]}
            self.assertEqual(codex_reconciliation._start_time_match(legacy, identity), "RECOVERED_PASS")
            self.assertEqual(codex_reconciliation._start_time_match(
                dict(legacy, process_start_ticks=identity["process_start_ticks"] + 1), identity), "FAIL")
            self.assertEqual(codex_reconciliation._start_time_match(
                dict(legacy, boot_id="different-boot"), identity), "FAIL")
        finally:
            process.terminate(); process.wait(timeout=3)

    def test_codex_home_resolution_prefers_authoritative_nested_receipt(self):
        home = "/tmp/receipt-codex-home"
        resolved = codex_reconciliation._resolve_codex_home(
            {"codex_home": None, "command_line": "broker --codex-home /tmp/other"},
            {"environment": {"codex_home": home}})
        self.assertEqual(resolved["codex_home"], home)
        self.assertEqual(resolved["codex_home_source"], "endpoint_receipt.environment.codex_home")

    def test_endpoint_processes_normalize_to_one_termination_unit(self):
        members = []
        for pid, ppid, group, command in ((10, 1, 10, "python -m scripts.lib.emp.codex_app_server_broker ws://127.0.0.1:45999"),
                                          (11, 10, 11, "node codex app-server --listen ws://127.0.0.1:45999"),
                                          (12, 11, 11, "codex app-server --listen ws://127.0.0.1:45999")):
            members.append({"endpoint_uri": "ws://127.0.0.1:45999", "listener_pid": pid,
                            "child_pid": pid, "process_group": group, "command_line": command,
                            "process_identity": {"pid": pid, "ppid": ppid, "process_group": group,
                                                  "alive": True}})
        units = codex_reconciliation._termination_units(members)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["member_pids"], [10, 11, 12])
        self.assertEqual(units[0]["process_groups"], [10, 11])
        self.assertEqual(units[0]["broker_pid"], 10)
    def _record(self, runtime: Path, process: subprocess.Popen[bytes], *, state: str = "STOPPED") -> Path:
        record = runtime / "codex-interactive-sessions" / "CODEX-SESSION-TEST.json"
        record.parent.mkdir(parents=True)
        identity = codex_reconciliation.process_identity(process.pid)
        value = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
                 "contract": {"id": "ZEUS-P5-G6-CODEX-INTERACTIVE", "version": "1"},
                 "session_id": "CODEX-SESSION-TEST", "mission_id": "MISSION-TEST",
                 "state": state, "pid": process.pid, "pid_identity": identity,
                 "repository": str(ROOT), "repository_id": "homelab-test",
                 "repository_identity": "git@example/homelab", "path": str(record)}
        value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
        record.write_text(json.dumps(value), encoding="utf-8")
        return record

    def test_dry_run_is_read_only_and_classifies_live_terminal_process(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            try:
                self._record(runtime, process)
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime)
                self.assertTrue(result["read_only"])
                self.assertEqual(result["reconciliation"]["entries"][0]["disposition"], "ORPHAN_LIVE_PROCESS")
                self.assertTrue(process.poll() is None)
                self.assertFalse(list((runtime / codex_reconciliation.RECEIPT_DIR).glob("*.json")))
            finally:
                process.terminate(); process.wait(timeout=3)

    def test_approved_reconciliation_terminates_with_receipt_and_replays(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            self._record(runtime, process)
            result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
            self.assertEqual(result["reconciliation"]["termination_receipts"][0]["result"], "PASS")
            self.assertIsNotNone(process.poll())
            replay = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
            self.assertTrue(replay["replayed"])
            self.assertEqual(replay["reconciliation"]["reconciliation_id"], result["reconciliation"]["reconciliation_id"])

    def test_unverified_live_process_is_never_mutation_eligible(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            try:
                record = self._record(runtime, process)
                value = json.loads(record.read_text(encoding="utf-8"))
                value.pop("pid_identity")
                value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
                record.write_text(json.dumps(value), encoding="utf-8")
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
                entry = result["reconciliation"]["entries"][0]
                self.assertEqual(entry["disposition"], "ORPHAN_IDENTITY_UNVERIFIED")
                self.assertTrue(process.poll() is None)
            finally:
                process.terminate(); process.wait(timeout=3)

    def test_duplicate_mission_records_report_cardinality_conflict(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            directory = runtime / "codex-interactive-sessions"
            directory.mkdir(parents=True)
            for suffix in ("A", "B"):
                value = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
                         "contract": {"id": "ZEUS-P5-G6-CODEX-INTERACTIVE", "version": "1"},
                         "session_id": f"CODEX-SESSION-{suffix}", "mission_id": "MISSION-DUP",
                         "state": "STOPPED", "pid": None, "repository": str(ROOT),
                         "repository_id": "homelab-test", "repository_identity": "git@example/homelab"}
                value["state_digest"] = digest(value)
                (directory / f"{suffix}.json").write_text(json.dumps(value), encoding="utf-8")
            result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime)
            self.assertEqual(result["reconciliation"]["cardinality"]["MISSION-DUP"]["observed"], 2)
            self.assertTrue(all(item["disposition"] == "ORPHAN_CARDINALITY_CONFLICT"
                                for item in result["reconciliation"]["entries"]))

    def _remote_record(self, runtime: Path, process: subprocess.Popen[bytes], endpoint: str,
                       *, session_id: str, diagnostic: bool) -> Path:
        record = runtime / "codex-interactive-sessions" / f"{session_id}.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        identity = codex_reconciliation.process_identity(process.pid)
        codex_home = runtime / "codex-home" / session_id
        receipt = {"result": "PASS", "endpoint_uri": endpoint,
                   "endpoint_creation_transaction_id": f"TX-{session_id}",
                   "endpoint_owner_session_id": session_id,
                   "environment": {"cwd": str(ROOT), "codex_home": str(codex_home)},
                   "readiness_probe": {"initialize": "PASS"}}
        value = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
                 "contract": {"id": "ZEUS-P5-G6-CODEX-INTERACTIVE", "version": "1"},
                 "session_id": session_id, "mission_id": None, "state": "CREATED",
                 "execution_mode": "REMOTE_INTERACTIVE", "provider_mode": "APP_SERVER_REMOTE",
                 "provider_transport": "WEBSOCKET", "repository": str(ROOT),
                 "repository_id": "homelab-test", "repository_identity": "git@example/homelab",
                 "endpoint_uri": endpoint, "remote_endpoint": endpoint,
                 "listener_pid": process.pid, "provider_pid": process.pid,
                 "listener_process_identity": identity, "codex_home": str(codex_home),
                 "endpoint_creation_transaction_id": f"TX-{session_id}",
                 "endpoint_receipt": receipt, "remote_client_pid": None if diagnostic else 999999,
                 "socket_listening": True, "path": str(record)}
        value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
        record.write_text(json.dumps(value), encoding="utf-8")
        return record

    def _fake_listener(self, temporary: Path, endpoint: str) -> subprocess.Popen[bytes]:
        binary = temporary / ("codex-" + endpoint.rsplit(":", 1)[1])
        binary.symlink_to("/usr/bin/python3")
        return subprocess.Popen([str(binary), "-c", "import time; time.sleep(30)",
                                 "app-server", "--listen", endpoint], start_new_session=True)

    def test_verified_diagnostic_cleanup_updates_dimensions_and_receipt(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            root = Path(temporary); runtime = root / "runtime"
            process = self._fake_listener(root, "ws://127.0.0.1:45101")
            try:
                self._remote_record(runtime, process, "ws://127.0.0.1:45101",
                                    session_id="CODEX-SESSION-DIAG", diagnostic=True)
                dry = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                session = dry["matching_sessions"][0]
                self.assertEqual(session["session_state"], "COMPLETED_DIAGNOSTIC")
                self.assertEqual(session["listener_state"], "READY")
                self.assertEqual(session["ownership_result"], "OWNERSHIP_VERIFIED")
                self.assertTrue(dry["proposed_actions"])
                self.assertTrue(dry["plan_digest"])
                self.assertEqual(len(dry["termination_units"]), 1)
                self.assertEqual(dry["proposed_actions"][0]["termination_unit_id"],
                                 dry["termination_units"][0]["termination_unit_id"])
                self.assertEqual(dry["proposed_actions"][0]["member_pids"],
                                 dry["termination_units"][0]["member_pids"])
                repeat = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                self.assertEqual(dry["plan_digest"], repeat["plan_digest"])
                plan = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                approved = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True,
                                                          expected_plan_digest=plan["plan_digest"])
                receipt = approved["reconciliation"]["termination_receipts"][0]
                self.assertEqual(receipt["result"], "PASS")
                self.assertFalse(process.poll() is None)
                saved = json.loads((runtime / "codex-interactive-sessions/CODEX-SESSION-DIAG.json").read_text())
                self.assertEqual(saved["session_state"], "STOPPED")
                self.assertFalse(saved["socket_listening"])
                verified = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                self.assertEqual(verified["required_actions"], [])
                self.assertEqual(verified["next_authorized_action"], "NO_RECONCILIATION_REQUIRED")
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

    def test_stale_reviewed_plan_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
            with self.assertRaises(codex_reconciliation.ReconciliationError) as raised:
                codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True,
                                               expected_plan_digest="stale-plan")
            self.assertEqual(raised.exception.code, "PLAN_STALE")

    def test_approved_reconciliation_requires_reviewed_digest(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            root = Path(temporary); runtime = root / "runtime"
            process = self._fake_listener(root, "ws://127.0.0.1:45105")
            try:
                self._remote_record(runtime, process, "ws://127.0.0.1:45105",
                                    session_id="CODEX-SESSION-DIGEST", diagnostic=True)
                with self.assertRaises(codex_reconciliation.ReconciliationError) as raised:
                    codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
                self.assertEqual(raised.exception.code, "PLAN_DIGEST_MISSING")
                self.assertIsNone(process.poll())
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

    def test_process_identity_result_is_available_when_proc_identity_is_complete(self):
        process = subprocess.Popen(["sleep", "30"])
        try:
            identity = codex_reconciliation.process_identity(process.pid)
            self.assertEqual(codex_reconciliation._process_identity_result(None, identity), "VERIFIED")
            self.assertEqual(codex_reconciliation._process_identity_result(None, {"alive": False}), "UNAVAILABLE")
        finally:
            process.terminate(); process.wait(timeout=3)

    def test_legacy_receipt_promotes_to_recovered_verified_with_explanation(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            process = self._fake_listener(Path(temporary), "ws://127.0.0.1:45991")
            try:
                identity = codex_reconciliation.process_identity(process.pid)
                legacy = {key: value for key, value in identity.items()
                          if key not in {"process_start_ticks", "boot_id", "process_identity_digest", "identity"}}
                endpoint = "ws://127.0.0.1:45991"
                receipt = {"result": "PASS", "endpoint_uri": endpoint,
                           "endpoint_owner_session_id": "CODEX-LEGACY",
                           "environment": {"cwd": str(ROOT), "codex_home": "/tmp/codex-home"}}
                owner = codex_reconciliation._ownership(
                    {"session_id": "CODEX-LEGACY", "endpoint_uri": endpoint,
                     "repository": str(ROOT), "codex_home": "/tmp/codex-home",
                     "endpoint_receipt": receipt, "listener_process_identity": legacy},
                    identity, endpoint, ROOT, members=[identity])
                self.assertEqual(owner["result"], "OWNERSHIP_RECOVERED_VERIFIED")
                self.assertTrue(owner["ownership_report"]["promotion_reason"])
                self.assertIn("LEGACY_EVIDENCE_RECOVERED", owner["promotion_reason"])
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

    def test_ownership_report_preserves_partial_and_immutable_mismatch(self):
        process = subprocess.Popen(["sleep", "30"])
        try:
            identity = codex_reconciliation.process_identity(process.pid)
            endpoint = "ws://127.0.0.1:45992"
            partial = codex_reconciliation._ownership(
                {"endpoint_uri": endpoint, "repository": str(ROOT)}, identity,
                endpoint, ROOT, members=[identity])
            self.assertIn(partial["result"], {"OWNERSHIP_PARTIAL", "OWNERSHIP_UNKNOWN"})
            self.assertIn("ownership_report", partial)
            mismatch = codex_reconciliation._ownership(
                {"endpoint_uri": "ws://127.0.0.1:45993", "repository": str(ROOT),
                 "listener_process_identity": {"pid": identity["pid"],
                                                 "process_group": identity["process_group"],
                                                 "process_start_ticks": identity["process_start_ticks"] + 1}},
                identity, "ws://127.0.0.1:45993", ROOT, members=[identity])
            self.assertEqual(mismatch["result"], "OWNERSHIP_MISMATCH")
            self.assertTrue(mismatch["immutable_conflicts"] or mismatch["ownership_report"]["immutable_conflicts"])
        finally:
            process.terminate(); process.wait(timeout=3)

    def test_remote_status_uses_canonical_detached_projection(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            root = Path(temporary); runtime = root / "runtime"
            process = self._fake_listener(root, "ws://127.0.0.1:45994")
            try:
                record = self._remote_record(runtime, process, "ws://127.0.0.1:45994",
                                            session_id="CODEX-SESSION-PROJECTION", diagnostic=False)
                value = json.loads(record.read_text(encoding="utf-8"))
                value.update({"state": "STOPPED", "session_state": "STOPPED", "client_state": "STOPPED",
                              "listener_state": "READY", "provider_state": "READY"})
                value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
                record.write_text(json.dumps(value), encoding="utf-8")
                status = codex_interactive.status(ROOT, session_id="CODEX-SESSION-PROJECTION", runtime_root=runtime)
                self.assertEqual(status["session_state"], "DETACHED")
                self.assertEqual(status["client_state"], "EXITED")
                self.assertEqual(status["listener_state"], "READY")
                self.assertEqual(status["session_next_authorized_action"], "ATTACH_OR_STOP")
                self.assertIn("ownership_result", status)
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

    def test_partial_result_reports_applied_work_and_preserved_targets(self):
        projection = {"termination_units": [], "cardinality": {"result": "PASS"},
                      "live_listeners": [], "matching_sessions": [], "paths": {}}
        actions = [{"action_id": "A1", "action_type": "STOP_DIAGNOSTIC_LISTENER",
                    "termination_unit_id": "U1", "endpoint_uri": "ws://127.0.0.1:36195",
                    "allowed": True, "ownership_result": "OWNERSHIP_RECOVERED_VERIFIED"},
                   {"action_id": "A2", "action_type": "PRESERVE_TARGET",
                    "termination_unit_id": "U2", "endpoint_uri": "ws://127.0.0.1:37051",
                    "allowed": False, "ownership_result": "OWNERSHIP_PARTIAL"}]
        receipt = {"result": "PARTIAL", "plan_digest": "digest", "proposed_actions": actions,
                   "actions_attempted": [actions[0]], "actions_completed": [{"signal_sequence": ["SIGTERM"],
                   "process_exit_result": True, "socket_closure_result": True}], "actions_failed": [],
                   "preserved_targets": [{"endpoint_uri": "ws://127.0.0.1:37051",
                   "preservation_reason": "OWNERSHIP_PARTIAL"}], "reconciliation_applied": True,
                   "reconciliation_fully_converged": False, "blockers": [
                       "UNRESOLVED_PARTIAL_OWNERSHIP_TARGETS", "TERMINAL_STATE_NOT_REACHED"],
                   "terminal_state_result": False, "cardinality": {"result": "PASS"}}
        response = codex_reconciliation._response(ROOT, Path("/tmp"), projection, actions,
                                                  receipt, replay=False, read_only=False)
        self.assertEqual(response["result"], "PARTIAL")
        self.assertTrue(response["reconciliation_applied"])
        self.assertFalse(response["reconciliation_fully_converged"])
        self.assertEqual(response["preserved_target_count"], 1)
        self.assertNotIn("RECONCILIATION_NOT_APPLIED", response["blockers"])
        self.assertEqual(response["next_authorized_action"], "RECONCILE_REMAINING_ORPHAN_OWNERSHIP")

    def test_replay_response_is_idempotent_and_has_zero_new_mutation(self):
        receipt = {"result": "PARTIAL", "plan_digest": "old", "proposed_actions": [],
                   "actions_completed": [{"signal_sequence": ["SIGTERM"],
                   "process_exit_result": True, "socket_closure_result": True}],
                   "reconciliation_applied": True, "reconciliation_fully_converged": False,
                   "terminal_state_result": False, "cardinality": {"result": "PASS"}}
        response = codex_reconciliation._response(ROOT, Path("/tmp"),
                                                  {"termination_units": [], "live_listeners": [],
                                                   "matching_sessions": [], "cardinality": {"result": "PASS"}},
                                                  [], receipt, replay=True, read_only=False)
        self.assertEqual(response["result"], "PASS")
        self.assertEqual(response["replay_result"], "IDEMPOTENT")
        self.assertEqual(response["processes_signaled"], 0)
        self.assertEqual(response["receipts_written"], 0)

    def test_completed_replay_projects_current_plan_and_historical_application_separately(self):
        projection = {
            "termination_units": [
                {"termination_unit_id": "U37051", "endpoint_uri": "ws://127.0.0.1:37051",
                 "ownership_result": "OWNERSHIP_PARTIAL"},
                {"termination_unit_id": "U39979", "endpoint_uri": "ws://127.0.0.1:39979",
                 "ownership_result": "OWNERSHIP_PARTIAL"}],
            "cardinality": {"result": "PASS"}, "live_listeners": [],
            "matching_sessions": [], "orphan_listeners": []}
        actions = [
            {"action_id": "A37051", "action_type": "PRESERVE_TARGET", "termination_unit_id": "U37051",
             "endpoint_uri": "ws://127.0.0.1:37051", "allowed": False,
             "ownership_result": "OWNERSHIP_PARTIAL"},
            {"action_id": "A39979", "action_type": "PRESERVE_TARGET", "termination_unit_id": "U39979",
             "endpoint_uri": "ws://127.0.0.1:39979", "allowed": False,
             "ownership_result": "OWNERSHIP_PARTIAL"}]
        receipt = {"result": "PARTIAL", "plan_digest": "historical-digest",
                   "reconciliation_id": "CODEX-RECON-historical", "receipt_digest": "receipt-digest",
                   "proposed_actions": [{"action_id": "A36195", "action_type": "STOP_DIAGNOSTIC_LISTENER",
                                         "allowed": True}],
                   "actions_completed": [{"result": "PASS", "signal_sequence": ["SIGTERM"]}],
                   "reconciliation_applied": True, "reconciliation_fully_converged": False,
                   "terminal_state_result": False, "cardinality": {"result": "PASS"}}
        response = codex_reconciliation._response(
            ROOT, Path("/tmp"), projection, actions, receipt, replay=True, read_only=False,
            current_plan_digest="current-digest", requested_plan_digest="historical-digest",
            completed_receipt_path=Path("/tmp/completed-receipt.json"), replay_result="IDEMPOTENT")
        self.assertEqual(response["result"], "PASS")
        self.assertEqual(response["replay_result"], "IDEMPOTENT")
        self.assertTrue(response["reconciliation_already_applied"])
        self.assertFalse(response["reconciliation_applied_this_invocation"])
        self.assertFalse(response["reconciliation_required"])
        self.assertFalse(response["reconciliation_fully_converged"])
        self.assertEqual(response["blockers"], [])
        self.assertEqual(response["next_authorized_action"], "REVIEW_PRESERVED_TARGETS")
        self.assertEqual(response["plan_digest"], "current-digest")
        self.assertEqual(response["replay_context"]["matched_completed_plan_digest"], "historical-digest")
        self.assertEqual(response["replay_context"]["current_plan_digest"], "current-digest")
        self.assertEqual(response["preserved_target_count"], 2)
        self.assertEqual(response["processes_signaled"], 0)

    def test_replay_receipt_lookup_requires_completed_receipt_and_rejects_conflicts(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            receipt_dir = runtime / codex_reconciliation.RECEIPT_DIR
            receipt_dir.mkdir()
            base = {"controller_version": codex_reconciliation.CONTROLLER_VERSION,
                    "plan_digest": "historical", "operator_approved": True,
                    "reconciliation_applied": True, "actions_completed": [{"result": "PASS"}]}
            self.assertEqual(codex_reconciliation._completed_receipt_matches(runtime, "missing"), [])
            (receipt_dir / "CODEX-RECON-one.json").write_text(json.dumps(base), encoding="utf-8")
            self.assertEqual(len(codex_reconciliation._completed_receipt_matches(runtime, "historical")), 1)
            (receipt_dir / "CODEX-RECON-two.json").write_text(
                json.dumps(dict(base, reconciliation_id="different")), encoding="utf-8")
            self.assertEqual(len(codex_reconciliation._completed_receipt_matches(runtime, "historical")), 2)

    def test_preserved_targets_are_terminally_reviewable_not_failed_reconciliation(self):
        projection = {"termination_units": [], "cardinality": {"result": "PASS"},
                      "live_listeners": [], "matching_sessions": [], "paths": {}}
        actions = [{"action_id": "P1", "action_type": "PRESERVE_TARGET",
                    "termination_unit_id": "U1", "endpoint_uri": "ws://127.0.0.1:37051",
                    "allowed": False, "ownership_result": "OWNERSHIP_PARTIAL"}]
        receipt = {"result": "PASS", "plan_digest": "digest", "proposed_actions": actions,
                   "preserved_targets": [{"endpoint_uri": "ws://127.0.0.1:37051",
                   "preservation_reason": "OWNERSHIP_PARTIAL"}], "blockers": [],
                   "reconciliation_applied": False, "reconciliation_applied_this_invocation": False,
                   "reconciliation_already_applied": False, "reconciliation_required": False,
                   "reconciliation_fully_converged": False, "terminal_state_result": False,
                   "cardinality": {"result": "PASS"}}
        response = codex_reconciliation._response(ROOT, Path("/tmp"), projection, actions,
                                                  receipt, replay=False, read_only=True)
        self.assertEqual(response["result"], "PASS")
        self.assertEqual(response["replay_result"], "NOT_REQUIRED")
        self.assertEqual(response["next_authorized_action"], "REVIEW_PRESERVED_TARGETS")
        self.assertFalse(response["reconciliation_applied_this_invocation"])
        self.assertFalse(response["reconciliation_already_applied"])
        self.assertFalse(response["reconciliation_required"])
        self.assertIn("PRESERVED_TARGETS_REMAIN", response["notices"])

    def test_unknown_orphan_returns_fail_closed_not_pass(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            root = Path(temporary); runtime = root / "runtime"
            process = self._fake_listener(root, "ws://127.0.0.1:45104")
            try:
                plan = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True,
                                                        expected_plan_digest=plan["plan_digest"])
                self.assertIn(result["result"], {"FAIL", "PARTIAL"})
                self.assertTrue(result["blockers"])
                self.assertIsNone(process.poll())
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)

    def test_operational_listener_becomes_detached_and_unknown_orphan_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            root = Path(temporary); runtime = root / "runtime"
            accepted = self._fake_listener(root, "ws://127.0.0.1:45102")
            orphan = self._fake_listener(root, "ws://127.0.0.1:45103")
            try:
                self._remote_record(runtime, accepted, "ws://127.0.0.1:45102",
                                    session_id="CODEX-SESSION-DETACHED", diagnostic=False)
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                session = next(item for item in result["matching_sessions"] if item["session_id"] == "CODEX-SESSION-DETACHED")
                self.assertEqual(session["session_state"], "DETACHED")
                self.assertEqual(session["client_state"], "EXITED")
                self.assertEqual(session["attachment_state"], "DETACHED")
                self.assertEqual(session["session_next_authorized_action"], "ATTACH_OR_STOP")
                retained = next(item for item in result["termination_units"]
                                if item["endpoint_uri"] == "ws://127.0.0.1:45102")
                self.assertEqual(retained["classification"], "RETAINED_DETACHED_SESSION")
                self.assertFalse(retained["required_action_enabled"])
                self.assertFalse(any(item["endpoint_uri"] == retained["endpoint_uri"]
                                     for item in result["proposed_actions"]))
                self.assertTrue(any(item["endpoint_uri"] == "ws://127.0.0.1:45103" for item in result["orphan_listeners"]))
                plan = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, dry_run=True)
                approved = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True,
                                                          expected_plan_digest=plan["plan_digest"])
                self.assertTrue(approved["unreconciled_orphans"] >= 1)
                self.assertIsNone(accepted.poll())
                self.assertIsNone(orphan.poll())
            finally:
                for process in (accepted, orphan):
                    if process.poll() is None:
                        process.terminate(); process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
