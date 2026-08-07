#!/usr/bin/env python3
"""Qualification tests for the read-only managed Codex handoff resolver."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp import codex_adapter, managed_handoff
from scripts.lib.emp.production_execution import digest


ROOT = Path(__file__).resolve().parents[2]


class ManagedCodexHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name) / "runtime"
        self.runtime.mkdir()
        self.execution = {
            "schema_version": 1,
            "mission_id": "MISSION-CODEX-HANDOFF-001",
            "wop_id": "WOP-CODEX-HANDOFF-001",
            "gate_id": "GATE-CODEX-HANDOFF-001",
            "execution_id": "EXECUTION-CODEX-HANDOFF-001",
            "execution_session_id": "EXECUTION-SESSION-CODEX-HANDOFF-001",
            "provider_session_id": "PROVIDER-SESSION-CODEX-HANDOFF-001",
            "provider_id": codex_adapter.PROVIDER_ID,
            "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
            "current_published_baseline": "BASELINE-CODEX-HANDOFF-001",
            "admission_id": "ADMISSION-CODEX-HANDOFF-001",
            "execution_started": False,
            "mission_work_started": False,
            "repository_work_started": False,
        }
        self._write_runtime("execution-start-transactions", self.execution)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_runtime(self, directory: str, value: dict) -> Path:
        location = self.runtime / directory
        location.mkdir(parents=True, exist_ok=True)
        key = value.get("session_id") if directory == codex_adapter.STAGE_DIR else value.get("execution_id", value.get("session_id", "record"))
        path = location / f"{key}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def _session(self, **overrides) -> dict:
        value = {
            "schema_version": 1,
            "session_id": "CODEX-SESSION-HANDOFF-001",
            "mission_id": self.execution["mission_id"],
            "wop_id": self.execution["wop_id"],
            "execution_id": self.execution["execution_id"],
            "execution_session_id": self.execution["execution_session_id"],
            "provider_session_id": self.execution["provider_session_id"],
            "provider_id": self.execution["provider_id"],
            "state": "STOPPED",
            "session_disposition": "CURRENT",
            "pid": None,
            "provider_pid": None,
            "mission_work_started": False,
            "repository_work_started": False,
        }
        value.update(overrides)
        value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
        return value

    def _resolve(self, text: str) -> dict:
        return managed_handoff.resolve_handoff(ROOT, text, runtime_root=self.runtime)

    def test_handoff_only_resolves_repository_operation_mission_wop_gate_and_baseline(self):
        value = self._resolve("""# bounded handoff\n\nThis is a read-only handoff.\n""")
        self.assertEqual("PASS", value["result"])
        self.assertEqual("OPERATION-BETA", value["operation_id"])
        self.assertEqual(self.execution["mission_id"], value["mission_id"])
        self.assertEqual(self.execution["wop_id"], value["wop_id"])
        self.assertEqual(self.execution["gate_id"], value["gate_id"])
        self.assertEqual(self.execution["current_published_baseline"], value["baseline"])
        self.assertEqual("NO", value["handoff_authority_source"])

    def test_explicit_metadata_is_validated_not_authoritative(self):
        value = self._resolve("""mission_id: MISSION-CODEX-HANDOFF-001\nwop_id: WOP-CODEX-HANDOFF-001\ngate_id: GATE-CODEX-HANDOFF-001\n""")
        self.assertEqual("PASS", value["result"])
        self.assertEqual("PASS", value["handoff_resolution"])

    def test_execution_and_admission_bindings_are_automatic(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual(self.execution["execution_id"], value["execution"]["execution_id"])
        self.assertEqual(self.execution["admission_id"], value["admission_id"])
        self.assertTrue(value["execution"]["execution_available"])

    def test_explicit_execution_and_baseline_contradictions_fail_closed(self):
        execution = self._resolve("execution_id: EXECUTION-NOT-BOUND\n")
        baseline = self._resolve("baseline: BASELINE-NOT-BOUND\n")
        self.assertEqual("BLOCKED", execution["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", execution["blocker"])
        self.assertEqual("BLOCKED", baseline["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", baseline["blocker"])

    def test_contradictory_metadata_fails_closed(self):
        value = self._resolve("mission_id: MISSION-NOT-AUTHORITATIVE\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_BINDING_CONTRADICTION", value["blocker"])

    def test_prose_cannot_create_authority_or_bypass_admission(self):
        value = managed_handoff.resolve_handoff(
            ROOT,
            "Please work on MISSION-PROSE-CREATED and WOP-PROSE-CREATED.\n",
            runtime_root=self.runtime,
        )
        self.assertEqual("PASS", value["result"])
        self.assertEqual(self.execution["mission_id"], value["mission_id"])
        self.assertNotEqual("MISSION-PROSE-CREATED", value["mission_id"])
        self.assertEqual("NO", value["handoff_authority_source"])

    def test_no_compatible_session_creates_plan_without_mutation(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertFalse(value["mutation_applied"])
        self.assertFalse(value["delivery"]["provider_contacted"])

    def test_compatible_stopped_session_resumes(self):
        self._write_runtime(codex_adapter.STAGE_DIR, self._session())
        value = self._resolve("handoff: current work\n")
        self.assertEqual("RESUME", value["managed_session"]["action"])

    def test_compatible_active_session_reuses(self):
        session = self._session(pid=os.getpid(), provider_pid=os.getpid(), state="ACTIVE")
        self._write_runtime(codex_adapter.STAGE_DIR, session)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("REUSE", value["managed_session"]["action"])

    def test_historical_session_is_preserved_and_not_reused(self):
        historical = self._session(
            session_id="CODEX-SESSION-HISTORICAL-BETA",
            mission_id="MISSION-BETA-562F443E16C69401",
            wop_id="WOP-HISTORICAL-BETA",
            execution_id="EXECUTION-HISTORICAL-BETA",
            execution_session_id="EXECUTION-SESSION-HISTORICAL-BETA",
            provider_session_id="PROVIDER-SESSION-HISTORICAL-BETA",
            state="STOPPED",
        )
        self._write_runtime(codex_adapter.STAGE_DIR, historical)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertTrue(value["managed_session"]["historical_session_preserved"])
        self.assertFalse(value["managed_session"]["historical_session_reused_for_new_handoff"])

    def test_incompatible_immutable_session_is_not_reused(self):
        incompatible = self._session(
            session_id="CODEX-SESSION-INCOMPATIBLE",
            execution_id="EXECUTION-OTHER-IMMUTABLE",
            state="ACTIVE",
            pid=os.getpid(),
            provider_pid=os.getpid(),
        )
        self._write_runtime(codex_adapter.STAGE_DIR, incompatible)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("CREATE", value["managed_session"]["action"])
        self.assertEqual("DO_NOT_REUSE", value["managed_session"]["session_reuse"])

    def test_multiple_compatible_sessions_fail_closed(self):
        self._write_runtime(codex_adapter.STAGE_DIR, self._session(session_id="CODEX-SESSION-DUPLICATE-A"))
        self._write_runtime(codex_adapter.STAGE_DIR, self._session(session_id="CODEX-SESSION-DUPLICATE-B"))
        value = self._resolve("handoff: current work\n")
        self.assertEqual("BLOCKED", value["result"])
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_handoff_does_not_imply_execution_or_publication_authority(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("PRESERVED", value["execution"]["execution_authority"])
        self.assertFalse(value["delivery"]["execution_started"])
        self.assertNotIn("publication_authority", value)

    def test_multiple_execution_candidates_block(self):
        second = dict(self.execution, execution_id="EXECUTION-CODEX-HANDOFF-002")
        self._write_runtime("execution-start-transactions", second)
        value = self._resolve("handoff: current work\n")
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", value["blocker"])

    def test_invocation_approval_converges_without_removing_downstream_controls(self):
        value = self._resolve("handoff: current work\n")
        self.assertEqual("NO", value["handoff_invocation_requires_redundant_approval"])
        self.assertEqual("YES", value["downstream_protected_approvals_preserved"])

    def test_file_and_stdin_cli_paths_are_available(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as stream:
            stream.write("handoff: current work\n")
            handoff_path = stream.name
        try:
            command = [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", handoff_path, "--json"]
            file_result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(0, file_result.returncode, file_result.stderr)
            self.assertEqual("PASS", json.loads(file_result.stdout)["result"])
            stdin_result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", "-", "--json"],
                cwd=ROOT, input="handoff: current work\n", text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, stdin_result.returncode, stdin_result.stderr)
            self.assertEqual("PASS", json.loads(stdin_result.stdout)["result"])
        finally:
            Path(handoff_path).unlink(missing_ok=True)

    def test_blocked_cli_path_is_fail_closed(self):
        self._write_runtime("execution-start-transactions", dict(self.execution, execution_id="EXECUTION-CODEX-HANDOFF-002"))
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "--runtime-root", str(self.runtime), "codex", "handoff", "-", "--json"],
            cwd=ROOT, input="handoff: current work\n", text=True, capture_output=True, check=False,
        )
        self.assertEqual(78, result.returncode)
        self.assertEqual("HANDOFF_RESOLUTION_AMBIGUOUS", json.loads(result.stdout)["blocker"])


if __name__ == "__main__":
    unittest.main()
