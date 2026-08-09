"""Regression coverage for managed runtime precedence and work contracts."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import codex_adapter, managed_work_contract


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-ZEUS-CORRECTIVE-001"
HISTORICAL_MISSION = "MISSION-HISTORICAL-001"
EXECUTION = "EXECUTION-ZEUS-CORRECTIVE-001"
EXECUTION_SESSION = "EXECUTION-SESSION-ZEUS-CORRECTIVE-001"
PROVIDER_SESSION = "PROVIDER-SESSION-ZEUS-CORRECTIVE-001"
PROVIDER = "zeus-local-loneal-01"


class ZeusExecutionLifecycleCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="zeus-lifecycle-corrective-")
        self.runtime = Path(self.temp.name)
        self.execution = {
            "mission_id": MISSION, "execution_id": EXECUTION,
            "execution_session_id": EXECUTION_SESSION, "provider_session_id": PROVIDER_SESSION,
            "provider_id": PROVIDER, "execution_started": True,
            "execution_monitoring_active": True,
        }
        self._write_execution(self.execution)
        self.live = self._write_session(
            mission_id=MISSION, execution_id=EXECUTION,
            execution_session_id=EXECUTION_SESSION, provider_session_id=PROVIDER_SESSION,
            pid=os.getpid(), provider_pid=os.getpid(), state="READY",
            updated_at="2020-01-01T00:00:00Z",
        )
        self.historical = self._write_session(
            mission_id=HISTORICAL_MISSION, execution_id="EXECUTION-HISTORICAL-001",
            execution_session_id="EXECUTION-SESSION-HISTORICAL-001",
            provider_session_id="PROVIDER-SESSION-HISTORICAL-001", pid=None, provider_pid=None,
            state="RECONCILED_HISTORICAL", mission_work_started=True,
            updated_at="2099-01-01T00:00:00Z",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_execution(self, value: dict) -> None:
        directory = self.runtime / "execution-start-transactions"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{value['execution_id']}.json").write_text(json.dumps(value), encoding="utf-8")

    def _write_session(self, *, mission_id: str, execution_id: str,
                       execution_session_id: str, provider_session_id: str,
                       pid: int | None, provider_pid: int | None, state: str,
                       mission_work_started: bool = False, **extra) -> dict:
        value = {
            "schema_version": 1, "session_id": f"CODEX-SESSION-{mission_id}",
            "mission_id": mission_id, "wop_id": f"WOP-{mission_id}",
            "execution_id": execution_id, "execution_session_id": execution_session_id,
            "provider_session_id": provider_session_id, "provider_id": PROVIDER,
            "state": state, "pid": pid, "provider_pid": provider_pid,
            "mission_work_started": mission_work_started, "repository_work_started": False,
            "session_disposition": "CURRENT", **extra,
        }
        codex_adapter._save(self.runtime, value)
        return value

    def _contract(self, path: Path, **changes) -> Path:
        value = {
            "schema_version": 1, "contract_type": managed_work_contract.CONTRACT_TYPE,
            "contract_id": "WORK-CONTRACT-ZEUS-CORRECTIVE-001", "mission_id": MISSION,
            "execution_id": EXECUTION, "execution_session_id": EXECUTION_SESSION,
            "provider_id": PROVIDER, "provider_session_id": PROVIDER_SESSION,
            "requested_action": "CONTINUE_CONTROLLED_MISSION_WORK",
            "actions": [{"action": "CONTINUE_CONTROLLED_MISSION_WORK"}],
        }
        value.update(changes)
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        return path

    def _history_session(self, *, session_id: str = "CODEX-SESSION-HISTORY-001") -> dict:
        session = dict(self.live, session_id=session_id, pid=None, provider_pid=None,
                       event_directory=str(self.runtime / "codex-events" / session_id),
                       path=str(self.runtime / "codex-sessions" / f"{session_id}.json"))
        codex_adapter._save(self.runtime, session)
        Path(session["event_directory"]).mkdir(parents=True, exist_ok=True)
        return session

    def _history_event(self, session: dict, sequence: int, event: str, payload: dict,
                       previous: str | None = None) -> str:
        value = {"schema_version": 1, "sequence": sequence, "session_id": session["session_id"],
                 "event": event, "payload": payload, "previous_event_digest": previous}
        value["event_digest"] = codex_adapter.digest(value)
        path = Path(session["event_directory"]) / f"{sequence:04d}.json"
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        return value["event_digest"]

    def _non_authoritative_reconciliation(self) -> dict:
        return {
            "result": "PASS", "history_disposition": "EVENTS_NON_AUTHORITATIVE",
            "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
            "history_safe_for_thread_recovery": True,
            "reconciliation_required": True,
            "reconciled_projection": {"mission_work_started": False, "repository_work_started": False},
        }

    def test_mission_scoped_and_global_selectors_prefer_live_binding(self):
        mission = codex_adapter.resolve_managed_runtime(ROOT, mission_id=MISSION, selector="latest", runtime_root=self.runtime)
        active = codex_adapter.resolve_managed_runtime(ROOT, selector="active", runtime_root=self.runtime)
        latest = codex_adapter.resolve_managed_runtime(ROOT, selector="latest", runtime_root=self.runtime)
        self.assertEqual("PASS", mission["result"])
        self.assertEqual(self.live["session_id"], mission["session"]["session_id"])
        self.assertEqual(MISSION, active["mission_id"])
        self.assertEqual(MISSION, latest["mission_id"])
        self.assertEqual("LIVE_MANAGED_RUNTIME", latest["resolution"])
        self.assertNotEqual(self.historical["session_id"], latest["session"]["session_id"])

    def test_historical_session_does_not_supersede_live_session(self):
        resolved = codex_adapter.resolve_managed_runtime(ROOT, selector="latest", runtime_root=self.runtime)
        self.assertFalse(resolved["historical"])
        self.assertEqual(self.live["execution_id"], resolved["execution"]["execution_id"])

    def test_work_contract_schema_and_all_identity_bindings_validate(self):
        path = self._contract(Path(self.temp.name) / "contract.json")
        result = managed_work_contract.validate(path, mission_id=MISSION, binding=self.live)
        self.assertEqual(MISSION, result["contract"]["mission_id"])
        self.assertEqual(64, len(result["source_digest"]))
        for field in ("mission_id", "execution_id", "execution_session_id", "provider_id", "provider_session_id"):
            mismatch = dict(self.live, **{field: "OTHER"})
            with self.subTest(field=field), self.assertRaises(managed_work_contract.WorkContractError):
                managed_work_contract.validate(path, mission_id=MISSION, binding=mismatch)

    def test_stale_binding_fails_closed(self):
        path = self._contract(Path(self.temp.name) / "contract.json")
        with self.assertRaisesRegex(managed_work_contract.WorkContractError, "superseded"):
            managed_work_contract.validate(path, mission_id=MISSION, binding=dict(self.live, state="SUPERSEDED"))

    def test_contract_digest_persistence_and_replay_are_idempotent(self):
        path = self._contract(Path(self.temp.name) / "contract.json")
        first = managed_work_contract.ingest(path, runtime=self.runtime, mission_id=MISSION, binding=self.live)
        second = managed_work_contract.ingest(path, runtime=self.runtime, mission_id=MISSION, binding=self.live)
        self.assertEqual("APPLIED", first["replay"])
        self.assertEqual("IDEMPOTENT", second["replay"])
        self.assertEqual(first["contract_payload_digest"], second["contract_payload_digest"])
        persisted = json.loads((self.runtime / "work-contracts" / f"{first['contract_id']}.json").read_text())
        self.assertEqual(first["source_digest"], persisted["source_digest"])
        self.assertEqual(first["contract_payload_digest"], persisted["contract_payload_digest"])

    def test_resume_returns_structured_contract_result_without_prose_execution(self):
        path = self._contract(Path(self.temp.name) / "contract.json")
        with patch.object(codex_adapter, "_provider_control_ready", return_value=True):
            first = codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime, work_contract=path)
            second = codex_adapter.resume(ROOT, MISSION, approval=True, runtime_root=self.runtime, work_contract=path)
        self.assertEqual("PASS", first["result"])
        self.assertEqual("PASS", second["result"])
        self.assertEqual("APPLIED", first["work_contract_replay"])
        self.assertEqual("IDEMPOTENT", second["work_contract_replay"])
        self.assertEqual("Zeus", first["work_contract"]["zeus_managed_execution_owner"])

    def test_cli_global_active_is_structured_json_and_mission_scoped(self):
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "status", "--active", "--json"],
            cwd=ROOT, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual("PASS", value["result"])
        self.assertEqual(MISSION, value["mission_id"])
        self.assertEqual("active", value["selector"])
        self.assertEqual(self.live["session_id"], value["resolved_runtime_session_id"])

    def test_no_work_events_is_automatically_satisfied_and_receipt_backed(self):
        session = self._history_session()
        reconciliation = {
            "result": "PASS", "history_disposition": "NO_WORK_EVENTS",
            "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
            "history_safe_for_thread_recovery": True,
            "reconciliation_required": False,
            "reconciled_projection": {"mission_work_started": False, "repository_work_started": False},
        }
        package = {"mission_id": MISSION, "wop_id": session["wop_id"], "execution_id": EXECUTION,
                   "execution_session_id": EXECUTION_SESSION, "provider_session_id": PROVIDER_SESSION,
                   "provider_id": PROVIDER, "package_digest": "package"}
        with patch.object(codex_adapter, "reconcile_session_history", return_value=reconciliation), \
             patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "_provider_liveness_snapshot", return_value={"fingerprints": [], "live_sessions": []}):
            value = codex_adapter.supersede_session(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)
        self.assertEqual("PASS", value["result"])
        receipt = list((self.runtime / codex_adapter.HISTORY_RECONCILIATION_RECEIPT_DIR).glob("*.json"))
        self.assertEqual(1, len(receipt))
        self.assertEqual("AUTOMATICALLY_SATISFIED_NO_WORK_EVENTS", json.loads(receipt[0].read_text())["decision"])

    def test_explicit_acceptance_is_bound_and_replays(self):
        session = self._history_session()
        first = self._history_event(session, 1, "CODEX_SESSION_CREATED", {})
        self._history_event(session, 2, "MISSION_WORK_STARTED", {"execution_id": EXECUTION}, first)
        with patch("scripts.lib.emp.execution_start.verify", return_value=self.execution):
            accepted = codex_adapter.accept_reconciliation(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)
            replay = codex_adapter.accept_reconciliation(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)
        self.assertEqual("ACCEPTED", accepted["decision"])
        self.assertEqual("IDEMPOTENT", replay["receipt"]["replay"])

    def test_missing_and_rejected_acceptance_fail_closed(self):
        session = self._history_session()
        first = self._history_event(session, 1, "CODEX_SESSION_CREATED", {})
        self._history_event(session, 2, "MISSION_WORK_STARTED", {"execution_id": EXECUTION}, first)
        with patch("scripts.lib.emp.execution_start.verify", return_value=self.execution), \
             patch.object(codex_adapter, "_package", return_value={"mission_id": MISSION, "wop_id": session["wop_id"],
                                                                      "execution_id": EXECUTION,
                                                                      "execution_session_id": EXECUTION_SESSION,
                                                                      "provider_session_id": PROVIDER_SESSION,
                                                                      "provider_id": PROVIDER}):
            with self.assertRaisesRegex(codex_adapter.CodexAdapterError, "accepted"):
                codex_adapter.supersede_session(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)
            codex_adapter.accept_reconciliation(ROOT, MISSION, session["session_id"], runtime_root=self.runtime,
                                                decision="REJECTED")
            with self.assertRaisesRegex(codex_adapter.CodexAdapterError, "rejected"):
                codex_adapter.supersede_session(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)

    def test_conflicting_authoritative_evidence_is_not_accepted(self):
        session = self._history_session()
        first = self._history_event(session, 1, "CODEX_SESSION_CREATED", {})
        self._history_event(session, 2, "MISSION_WORK_STARTED", {
            "execution_id": EXECUTION, "mission_id": MISSION, "wop_id": session["wop_id"],
            "session_id": session["session_id"], "provider_id": PROVIDER, "source_digest": "source",
        }, first)
        authoritative = dict(self.execution, mission_work_started=True)
        with patch("scripts.lib.emp.execution_start.verify", return_value=authoritative):
            with self.assertRaisesRegex(codex_adapter.CodexAdapterError, "prior mission work"):
                codex_adapter.accept_reconciliation(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)

    def test_lifecycle_and_runtime_actions_remain_separate(self):
        session = self._history_session()
        reconciliation = {
            "result": "PASS", "history_disposition": "NO_WORK_EVENTS",
            "mission_work_actually_occurred": "NO", "repository_work_actually_occurred": "NO",
            "history_safe_for_thread_recovery": True,
            "reconciliation_required": False,
            "reconciled_projection": {"mission_work_started": False, "repository_work_started": False,
                                      "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK"},
        }
        with patch.object(codex_adapter, "reconcile_session_history", return_value=reconciliation), \
             patch.object(codex_adapter, "_package", return_value={"mission_id": MISSION, "wop_id": session["wop_id"],
                                                                      "execution_id": EXECUTION,
                                                                      "execution_session_id": EXECUTION_SESSION,
                                                                      "provider_session_id": PROVIDER_SESSION,
                                                                      "provider_id": PROVIDER}), \
             patch.object(codex_adapter, "_provider_liveness_snapshot", return_value={"fingerprints": [], "live_sessions": []}):
            value = codex_adapter.supersede_session(ROOT, MISSION, session["session_id"], runtime_root=self.runtime)
        self.assertEqual("BEGIN_CONTROLLED_MISSION_WORK", value["next_authorized_action"])
        self.assertFalse(value["old_session_preserved"] is False)


if __name__ == "__main__":
    unittest.main()
