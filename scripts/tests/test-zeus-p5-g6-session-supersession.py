#!/usr/bin/env python3
"""Disposable P5-G6 stale-session supersession qualification."""

from __future__ import annotations

import json
import importlib.util
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import codex_adapter



ROOT = Path(__file__).resolve().parents[2]
_ZEUS_SPEC = importlib.util.spec_from_loader(
    "zeus_cli", importlib.machinery.SourceFileLoader("zeus_cli", str(ROOT / "scripts/zeus")))
zeus = importlib.util.module_from_spec(_ZEUS_SPEC)
_ZEUS_SPEC.loader.exec_module(zeus)
MISSION = "MISSION-BETA-562F443E16C69401"
WOP = "WOP-BETA-562F443E16C69401"
EXECUTION = "EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e"
OLD = "EXECUTION-SESSION-0d35cea3-1232-58f7-b202-92d0bfc256a3"
PROVIDER = "zeus-local-loneal-01"


class SessionSupersessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5g6-session-")
        self.runtime = Path(self.temp.name)
        self.old_event_dir = self.runtime / "codex-events" / OLD
        self.old_event_dir.mkdir(parents=True)
        self.old = {"schema_version": 1, "session_id": OLD, "mission_id": MISSION,
                    "wop_id": WOP, "execution_id": EXECUTION,
                    "execution_session_id": OLD, "provider_session_id": "PROVIDER-SESSION-1",
                    "provider_id": PROVIDER, "provider_pid": None, "pid": None,
                    "event_directory": str(self.old_event_dir), "path": str(self.runtime / "codex-sessions" / f"{OLD}.json"),
                    "state": "READY", "mission_work_started": False, "repository_work_started": False,
                    "package_digest": "package", "log_path": str(self.runtime / "old.log")}
        codex_adapter._save(self.runtime, self.old)
        self.original_event = codex_adapter._append_event(self.runtime, OLD, "LEGACY_MALFORMED_EVENT", {"legacy": True})

    def tearDown(self):
        self.temp.cleanup()

    def reconciliation(self, **changes):
        value = {"result": "PASS", "history_disposition": "EVENTS_NON_AUTHORITATIVE",
                 "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
                 "session_replacement_safe": True, "session_supersession_required": True}
        value.update(changes)
        return value

    def package(self, **changes):
        value = {"mission_id": MISSION, "wop_id": WOP, "execution_id": EXECUTION,
                 "execution_session_id": OLD, "provider_session_id": "PROVIDER-SESSION-1",
                 "provider_id": PROVIDER, "package_digest": "canonical-package"}
        value.update(changes)
        return value

    def run_supersede(self, **kwargs):
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()):
            return codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime, **kwargs)

    def test_stale_session_supersedes_once_and_preserves_history(self):
        before = json.dumps(codex_adapter.load_json(self.old_event_dir / "0001.json"), sort_keys=True)
        first = self.run_supersede()
        second = self.run_supersede()
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(first["replay"], "APPLIED")
        self.assertEqual(second["replay"], "IDEMPOTENT")
        self.assertEqual(first["new_session_id"], second["new_session_id"])
        self.assertEqual(len(list((self.runtime / "codex-sessions").glob("*.json"))), 2)
        old = codex_adapter._load(self.runtime / "codex-sessions" / f"{OLD}.json")
        self.assertEqual(old["session_disposition"], "SUPERSEDED")
        self.assertEqual(old["superseded_by"], first["new_session_id"])
        self.assertEqual(before, json.dumps(codex_adapter.load_json(self.old_event_dir / "0001.json"), sort_keys=True))
        replacement = codex_adapter._load(self.runtime / "codex-sessions" / f"{first['new_session_id']}.json")
        self.assertEqual(replacement["supersedes_session"], OLD)
        self.assertEqual(replacement["canonical_package_binding"], "PASS")

    def test_active_old_session_fails_closed(self):
        old = dict(self.old, pid=os.getpid())
        codex_adapter._save(self.runtime, old)
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()):
            with self.assertRaisesRegex(codex_adapter.CodexAdapterError, "active"):
                codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)

    def test_stale_pid_without_process_is_stopped_and_eligible(self):
        old = dict(self.old, pid=999999991, provider_pid=999999992)
        codex_adapter._save(self.runtime, old)
        value = codex_adapter.runtime_liveness(old)
        self.assertEqual(value["session_liveness"], "STOPPED")
        self.assertFalse(value["runtime_process_present"])
        self.assertFalse(value["provider_process_present"])

    def test_liveness_change_between_checks_fails_closed_with_evidence(self):
        stopped = {"runtime_process_present": False, "provider_process_present": False,
                   "runtime_classification": "STALE_ORPHANED_RUNTIME",
                   "runtime_process_identity": {"process_identity_digest": None},
                   "provider_process_identity": {"process_identity_digest": None}}
        live = {"runtime_process_present": True, "provider_process_present": True,
                "runtime_classification": "LIVE_PROVIDER_SESSION",
                "runtime_process_identity": {"process_identity_digest": "runtime-live"},
                "provider_process_identity": {"process_identity_digest": "provider-live"}}
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "runtime_liveness", side_effect=[stopped, live]):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "LIVENESS_CHANGED_DURING_TRANSACTION")
        self.assertEqual(raised.exception.details["precheck"]["live_sessions"], [])
        self.assertEqual(len(list((self.runtime / "codex-sessions").glob("*.json"))), 1)

    def test_stable_live_runtime_remains_protected(self):
        live = {"runtime_process_present": True, "provider_process_present": True,
                "runtime_classification": "LIVE_PROVIDER_SESSION",
                "runtime_process_identity": {"process_identity_digest": "runtime-live"},
                "provider_process_identity": {"process_identity_digest": "provider-live"}}
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "runtime_liveness", return_value=live):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "ACTIVE_SESSION_PROTECTION")
        self.assertIn("mutation_check", raised.exception.details)

    def test_prior_work_and_ambiguous_history_fail_closed(self):
        for field, expected in (("mission_work_actually_occurred", "PRIOR_MISSION_WORK"),
                                ("repository_work_actually_occurred", "PRIOR_REPOSITORY_WORK")):
            with self.subTest(field=field):
                with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation(**{field: "YES"})), \
                     patch.object(codex_adapter, "_package", return_value=self.package()):
                    with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                        codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)
                    self.assertEqual(raised.exception.code, expected)
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation(history_disposition="INDETERMINATE", session_replacement_safe=False)):
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)
            self.assertEqual(raised.exception.code, "AMBIGUOUS_HISTORY")

    def test_identity_mismatches_fail_closed(self):
        cases = (("expected_wop_id", "OTHER", "WOP_ID_BINDING_MISMATCH"),
                 ("expected_execution_id", "OTHER", "EXECUTION_ID_BINDING_MISMATCH"),
                 ("expected_provider_id", "OTHER", "PROVIDER_BINDING_MISMATCH"))
        for argument, value, expected in cases:
            with self.subTest(argument=argument):
                with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
                     patch.object(codex_adapter, "_package", return_value=self.package()):
                    with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                        codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime, **{argument: value})
                    self.assertEqual(raised.exception.code, expected)

    def test_begin_path_resolves_replacement_without_creating_another_session(self):
        result = self.run_supersede()
        replacement = codex_adapter._load(self.runtime / "codex-sessions" / f"{result['new_session_id']}.json")
        package = self.package(package_digest=replacement["package_digest"])
        diagnostics = {"provider_pid": os.getpid(), "command": ["disposable"], "environment": {},
                       "control_socket": "/tmp/disposable.sock", "remote_endpoint": None}
        with patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(type("P", (), {"pid": os.getpid()})(), diagnostics)), \
             patch.object(codex_adapter, "_process_alive", return_value=False), \
             patch.object(codex_adapter, "_append_event"):
            value = codex_adapter.start(ROOT, MISSION, approval=True, runtime_root=self.runtime, _resume=True)
        self.assertEqual(value["session_id"], result["new_session_id"])
        self.assertEqual(len(list((self.runtime / "codex-sessions").glob("*.json"))), 2)

    def test_current_session_converges_to_replacement(self):
        result = self.run_supersede()
        current = codex_adapter.current_session(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(current["session_id"], result["new_session_id"])
        self.assertEqual(current["supersedes_session"], OLD)

    def test_binding_resolver_exposes_distinct_identity_domains(self):
        transaction = {
            "mission_id": MISSION, "wop_id": WOP, "execution_id": EXECUTION,
            "execution_session_id": OLD, "provider_session_id": "PROVIDER-SESSION-1",
            "provider_id": PROVIDER,
        }
        directory = self.runtime / "execution-start-transactions"
        directory.mkdir()
        (directory / f"{EXECUTION}.json").write_text(json.dumps(transaction))
        binding = codex_adapter.resolve_session_binding(ROOT, mission_id=MISSION, runtime_root=self.runtime)
        self.assertEqual(binding["execution_session_id"], OLD)
        self.assertEqual(binding["provider_session_id"], "PROVIDER-SESSION-1")
        self.assertEqual(binding["codex_session_id"], OLD)

    def test_binding_resolver_normalizes_execution_identifier_case(self):
        transaction = {
            "mission_id": MISSION, "wop_id": WOP, "execution_id": EXECUTION,
            "execution_session_id": OLD, "provider_session_id": "PROVIDER-SESSION-1",
            "provider_id": PROVIDER,
        }
        directory = self.runtime / "execution-start-transactions"
        directory.mkdir()
        (directory / f"{EXECUTION}.json").write_text(json.dumps(transaction))
        binding = codex_adapter.resolve_session_binding(
            ROOT, execution_id=EXECUTION.upper(), runtime_root=self.runtime
        )
        self.assertEqual(binding["execution_id"], EXECUTION)

    def test_provider_session_alias_can_reach_canonical_supersession(self):
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_process_alive", return_value=False):
            result = codex_adapter.supersede_session(ROOT, MISSION, "PROVIDER-SESSION-1", runtime_root=self.runtime)
        self.assertEqual(result["result"], "PASS")

    def test_execution_session_alias_resolves_distinct_codex_identity(self):
        old_path = self.runtime / "codex-sessions" / f"{OLD}.json"
        old_path.unlink()
        managed = dict(self.old, session_id="CODEX-MANAGED-OLD",
                       path=str(self.runtime / "codex-sessions" / "CODEX-MANAGED-OLD.json"),
                       event_directory=str(self.runtime / "codex-events" / "CODEX-MANAGED-OLD"))
        codex_adapter._save(self.runtime, managed)
        with patch.object(codex_adapter, "reconcile_session_history", return_value=self.reconciliation()), \
             patch.object(codex_adapter, "_package", return_value=self.package()), \
             patch.object(codex_adapter, "_process_alive", return_value=False):
            result = codex_adapter.supersede_session(ROOT, MISSION, OLD, runtime_root=self.runtime)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["old_session_id"], "CODEX-MANAGED-OLD")


class ZeusSupersessionCliTests(unittest.TestCase):
    """Exercise argparse plus Zeus dispatch, not only the adapter contract."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5g6-cli-")

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, *arguments):
        output = StringIO()
        with redirect_stdout(output):
            code = zeus.main(["--runtime-root", self.temp.name, "codex", *arguments, "--json"])
        return code, json.loads(output.getvalue())

    def test_parser_and_dispatch_reach_canonical_adapter(self):
        result = {"result": "PASS", "replay": "APPLIED", "new_session_id": "CODEX-SESSION-REPLACEMENT"}
        with patch.object(zeus.codex_adapter, "supersede_session", return_value=result) as supersede:
            code, value = self.invoke("supersede", MISSION, "--session", OLD, "--approve")
        self.assertEqual(code, 0)
        self.assertEqual(value, result)
        supersede.assert_called_once_with(
            zeus.ROOT, MISSION, OLD, reason="NON_AUTHORITATIVE_RECONCILED_HISTORY",
            runtime_root=Path(self.temp.name),
        )

    def test_missing_approval_and_session_fail_at_cli_boundary(self):
        code, value = self.invoke("supersede", MISSION, "--session", OLD)
        self.assertEqual(code, 78)
        self.assertEqual(value["blockers"][0]["code"], "OPERATOR_APPROVAL_REQUIRED")
        code, value = self.invoke("supersede", MISSION, "--approve")
        self.assertEqual(code, 78)
        self.assertEqual(value["blockers"][0]["code"], "OLD_SESSION_REQUIRED")

    def test_adapter_failure_is_bounded_json(self):
        failure = codex_adapter.CodexAdapterError("DISPOSABLE_FAILURE", "bounded failure")
        with patch.object(zeus.codex_adapter, "supersede_session", side_effect=failure):
            code, value = self.invoke("supersede", MISSION, "--session", OLD, "--approve")
        self.assertEqual(code, 78)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "DISPOSABLE_FAILURE")

    def test_unrelated_codex_action_remains_managed(self):
        status = {"result": "PASS", "mission_id": MISSION, "mission_work_started": False,
                  "repository_work_started": False}
        with patch.object(zeus.codex_adapter, "status", return_value=status) as managed_status:
            code, value = self.invoke("status", MISSION)
        self.assertEqual(code, 0)
        self.assertEqual(value, status)
        managed_status.assert_called_once()


if __name__ == "__main__":
    unittest.main()
