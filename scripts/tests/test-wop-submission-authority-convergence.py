#!/usr/bin/env python3
"""Focused proof of the submitted-WOP authority convergence."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.emp import codex_adapter


class SubmittedWopAuthorityTests(unittest.TestCase):
    def fixture(self, *, action: str = "execute", gate: bool = False,
                admitted: bool = True, admission_decision: str | None = None) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp(prefix="zeus-submitted-wop-"))
        (root / "engineering/metadata").mkdir(parents=True)
        (root / "engineering/work-orders/test").mkdir(parents=True)
        wop = {
            "wop_id": "WOP-TEST-SUBMITTED-001", "revision": 1,
            "status": "ACTIVE", "mission_id": "MISSION-TEST-001",
            "phase_id": "PHASE-TEST-001",
            "execution_context": {"baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0"},
            "scope": ["bounded test work"],
            "submission_authority": {
                "submission": {"submitted": True, "submission_id": "SUBMISSION-TEST-001"},
                "permitted_actions": [action],
                "scope_digest": "scope-test",
            },
        }
        if gate:
            wop["approval_gate"] = {"id": "GATE-TEST-001"}
        if admitted or admission_decision:
            wop["admission"] = {
                "admission_decision": admission_decision or "ACCEPTED", "wop_id": wop["wop_id"]
            }
        path = root / "engineering/work-orders/test/immutable-wop.yaml"
        path.write_text(yaml.safe_dump(wop, sort_keys=True), encoding="utf-8")
        source_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        emm = {
            "schema_version": 1, "emm_id": "TEST-EMM", "version": "1.0",
            "baseline_id": "OA-IMPLEMENTATION-BASELINE-1.0", "entities": [{
                "entity_type": "ImplementationWOP", "entity_id": wop["wop_id"],
                "revision": 1, "authoritative_owner": "WOP Owner",
                "classification": "Authoritative",
                "source": "engineering/work-orders/test/immutable-wop.yaml",
                "source_digest": source_digest,
            }]
        }
        (root / "engineering/metadata/operational-alpha-emm.yaml").write_text(
            yaml.safe_dump(emm, sort_keys=True), encoding="utf-8"
        )
        return root, path

    def test_submitted_wop_is_sufficient_without_three_second_grants(self) -> None:
        root, _ = self.fixture()
        value = ConvergenceRuntime(root).resolve(
            wop_id="WOP-TEST-SUBMITTED-001", revision=1,
            action="execute", correlation_id="submission-test",
        )
        self.assertEqual("RESOLVED", value["outcome"])
        self.assertEqual("SUBMITTED_WOP", value["authority_mode"])
        self.assertEqual("operator-submitted WOP", value["authority_source"])
        self.assertNotIn("authority_record", value["inputs"])

    def test_scope_and_admission_fail_closed(self) -> None:
        root, _ = self.fixture(action="inspect")
        denied = ConvergenceRuntime(root).resolve(
            wop_id="WOP-TEST-SUBMITTED-001", revision=1,
            action="execute", correlation_id="scope-test",
        )
        self.assertEqual("INTEGRITY_FAILURE", denied["outcome"])
        # An absent admission record is compatible with the standalone
        # resolver; an explicit failed admission is not.
        root, _ = self.fixture(admitted=False, admission_decision="RESUBMISSION_REQUIRED")
        result = ConvergenceRuntime(root).resolve(
            wop_id="WOP-TEST-SUBMITTED-001", revision=1,
            action="execute", correlation_id="admission-test",
        )
        self.assertNotEqual("RESOLVED", result["outcome"])

    def test_explicit_in_wop_approval_gate_remains_enforced(self) -> None:
        root, _ = self.fixture(gate=True)
        result = ConvergenceRuntime(root).resolve(
            wop_id="WOP-TEST-SUBMITTED-001", revision=1,
            action="execute", correlation_id="gate-test",
        )
        self.assertEqual("INTEGRITY_FAILURE", result["outcome"])
        self.assertIn("OPERATOR_APPROVAL_REQUIRED", result["reasons"][0])

    def test_codex_workspace_write_is_bound_to_submitted_wop_without_generic_approval(self) -> None:
        package = {
            "execution_id": "EXECUTION-SUBMITTED-001", "provider_id": codex_adapter.PROVIDER_ID,
            "repository_identity": str(ROOT), "repository_id": "repo",
            "mission_id": "MISSION-TEST-001", "wop_id": "WOP-TEST-SUBMITTED-001",
            "package_digest": "package", "provider_invocation_id": "INV-1",
            "provider_session_id": "PS-1", "execution_session_id": "ES-1",
            "authority": {"integrity": "PASS"},
            "work_authority": {"source": "operator-submitted WOP"},
            "scope": {"sandbox": "workspace-write"},
        }
        diagnostics = {"provider_pid": 1, "command": ["codex"], "environment": {},
                       "control_socket": "/tmp/zeus-test.sock", "remote_endpoint": None}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(codex_adapter, "_package", return_value=package), \
                patch.object(codex_adapter, "_existing", return_value=None), \
                patch.object(codex_adapter, "_launch_handshake", return_value=(type("P", (), {"pid": 1})(), diagnostics)), \
                patch.object(codex_adapter, "_append_event"), \
                patch.object(codex_adapter, "_save", side_effect=lambda _runtime, value: dict(value)):
            value = codex_adapter.start(ROOT, "MISSION-TEST-001", approval=False,
                                        runtime_root=Path(directory))
        self.assertEqual("workspace-write", value["sandbox"])
        self.assertFalse(value["read_only"])

    def test_historical_wop_source_is_not_modified(self) -> None:
        path = ROOT / "engineering/work-orders/OA-01-IMPLEMENTATION-001/immutable-wop.yaml"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        ConvergenceRuntime(ROOT).resolve(
            wop_id="WOP-OA-01-IMPLEMENTATION-001", revision=1,
            action="inspect", correlation_id="historical-read-only",
        )
        self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
