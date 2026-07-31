#!/usr/bin/env python3
"""ZEUS-P2-010 operational artifact gate handler qualification."""

from __future__ import annotations

import runpy
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.authority_resolution import digest  # noqa: E402
from scripts.lib.emp.gate_handlers import (  # noqa: E402
    GateHandlerFramework,
    HandlerRegistry,
)
from scripts.lib.emp.mission_admission_runtime import (  # noqa: E402
    AdmissionStateStore,
    MissionAdmissionRuntime,
)
from scripts.lib.emp.mission_execution_runtime import (  # noqa: E402
    EensExecutionSink,
    ExecutionStateStore,
    MissionExecutionRuntime,
)
from scripts.lib.emp.operational_gate_handler import (  # noqa: E402
    ActionCheckpointStore,
    OperationalArtifactGateHandler,
    OperationalContextError,
    OperationalExecutionContextService,
)


class OperationalGateHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.workspace = self.directory / "workspace"
        self.admissions = AdmissionStateStore(self.directory / "admissions")
        self.executions = ExecutionStateStore(self.directory / "executions")
        fixture = runpy.run_path(
            str(ROOT / "scripts/tests/test-authority-resolution-runtime.py")
        )
        source_path = self.directory / "authority.yaml"
        source_path.write_text(
            yaml.safe_dump(fixture["authoritative_state"](), sort_keys=True)
        )
        self.at = fixture["AT"]
        self.admission = MissionAdmissionRuntime(
            ROOT,
            self.admissions,
            authority_state_path=source_path,
            commissioning_probe=lambda root: {"commissioning_state": "READY"},
            enrollment_probe=lambda root: {
                "trust_compilation_ready": True,
                "missing_owners": [],
            },
            dispatch_probe=lambda **kwargs: {
                "dispatch_permitted": False,
                "reason": "SIMULATED_ADMISSION_ONLY",
            },
        ).start(
            {
                "mode": "qualification",
                "intent": "Qualify bounded operational artifact gates",
                "mission_id": fixture["MISSION"],
                "work_item_id": fixture["WORK"],
                "principal_id": fixture["PRINCIPAL"],
                "repository": str(ROOT),
            },
            at=self.at,
        )
        # This suite qualifies the isolated handler boundary.  Admission is
        # represented as an already-decided fixture so the tests do not
        # exercise the separate convergence-authority admission resolver.
        # Production admission remains fail-closed on that resolver.
        self.admission["request"]["mode"] = "operational"
        self.admission["status"] = "DECIDED"
        self.admission["failure"] = None
        self.admission["artifacts"]["admission_decision"] = {
            "admission_decision": "ACCEPTED",
            "dispatch_permitted": False,
        }
        self.admissions.save(self.admission)
        self.admission = self.admissions.load(self.admission["admission_id"])
        self.registry = HandlerRegistry()
        self.handler = OperationalArtifactGateHandler()
        self.registry.register(self.handler)
        self.registry.discover(ROOT / "engineering/handlers/operational")
        self.framework = GateHandlerFramework(self.registry)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def action(action_id, path, content):
        return {
            "action_id": action_id,
            "action_type": "create_artifact",
            "path": path,
            "content": content,
            "content_digest": digest({"content": content}),
        }

    @staticmethod
    def verify_action(action_id, path, content):
        return {
            "action_id": action_id,
            "action_type": "verify_artifact",
            "path": path,
            "content_digest": digest({"content": content}),
        }

    def plan(self):
        return {
            "schema_version": 1,
            "gates": {
                "EXECUTE_WORK": {
                    "dependencies": [],
                    "actions": [
                        self.action("create-primary", "artifacts/primary.txt", "alpha\n"),
                        self.action("create-secondary", "artifacts/secondary.txt", "beta\n"),
                    ],
                },
                "VERIFY_COMPLETION": {
                    "dependencies": ["EXECUTE_WORK"],
                    "actions": [
                        self.verify_action(
                            "verify-primary", "artifacts/primary.txt", "alpha\n"
                        ),
                        self.verify_action(
                            "verify-secondary", "artifacts/secondary.txt", "beta\n"
                        ),
                    ],
                },
            },
        }

    def provider(self, state, wop):
        return OperationalExecutionContextService.create(
            execution_id=state["execution_id"],
            mission_id=state["mission_id"],
            repository=ROOT,
            repository_baseline=state["repository_baseline"],
            wop_submission_digest=wop["submission_digest"],
            workspace=self.workspace,
            gate_plan=self.plan(),
            authorization={
                "decision": "AUTHORIZED",
                "execution_id": state["execution_id"],
                "reference": "P2-010-ISOLATED-QUALIFICATION-FIXTURE",
                "production_authority": False,
            },
        )

    def runtime(self, *, event_sink=None):
        return MissionExecutionRuntime(
            ROOT,
            self.executions,
            self.admissions,
            handler_framework=self.framework,
            operational_context_provider=self.provider,
            operational_dispatch_enabled=True,
            event_sink=event_sink,
        )

    def test_operational_handler_executes_real_isolated_artifact_gates(self):
        sink = EensExecutionSink(ROOT, self.directory / "eens.sqlite3")
        state = self.runtime(event_sink=sink).start(
            self.admission["admission_id"], at=self.at
        )
        self.assertEqual(state["state"], "Completed")
        self.assertEqual(
            (self.workspace / "artifacts/primary.txt").read_text(), "alpha\n"
        )
        self.assertEqual(
            (self.workspace / "artifacts/secondary.txt").read_text(), "beta\n"
        )
        delegated = [
            entry
            for entry in state["evidence"]
            if entry["event"] == "GATE_COMPLETED"
            and entry["payload"]["gate_id"]
            in {"EXECUTE_WORK", "VERIFY_COMPLETION"}
        ]
        self.assertTrue(
            all(
                item["payload"]["result"]["handler_id"]
                == "zeus.operational.artifact"
                for item in delegated
            )
        )
        self.assertTrue(
            all(item["payload"]["result"]["verification_first"] for item in delegated)
        )
        self.assertEqual(sink.store.count(), len(state["evidence"]))

    def test_action_checkpoint_resume_skips_completed_action(self):
        runtime = self.runtime()
        suspended = runtime.start(
            self.admission["admission_id"], at=self.at, max_gates=2
        )
        state = self.executions.load(suspended["execution_id"])
        operational = self.provider(
            state, self.admission["artifacts"]["wop_result"]["wop"]
        )
        first = self.plan()["gates"]["EXECUTE_WORK"]["actions"][0]
        result = self.handler._execute_action(self.workspace, first)
        ActionCheckpointStore(
            operational["workspace"], state["execution_id"], "EXECUTE_WORK"
        ).record(first["action_id"], result)

        completed = runtime.resume(state["execution_id"], at=self.at)
        self.assertEqual(completed["state"], "Completed")
        gate = next(
            entry
            for entry in completed["evidence"]
            if entry["event"] == "GATE_COMPLETED"
            and entry["payload"]["gate_id"] == "EXECUTE_WORK"
        )
        results = gate["payload"]["result"]["action_results"]
        self.assertEqual([item["action_id"] for item in results], ["create-secondary"])

    def test_cancellation_sentinel_stops_before_next_action(self):
        runtime = self.runtime()
        suspended = runtime.start(
            self.admission["admission_id"], at=self.at, max_gates=2
        )
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / ".cancel-requested").write_text("cancel\n")
        waiting = runtime.resume(suspended["execution_id"], at=self.at)
        self.assertEqual(waiting["state"], "Waiting")
        self.assertEqual(
            waiting["wait_reason"]["category"], "GATE_HANDLER_FAILURE"
        )
        self.assertFalse((self.workspace / "artifacts/primary.txt").exists())

    def test_context_tampering_and_missing_authorization_fail_closed(self):
        state = {
            "execution_id": "EXECUTION-TEST",
            "mission_id": "MISSION-TEST",
            "repository_baseline": "a" * 40,
        }
        with self.assertRaisesRegex(OperationalContextError, "not granted"):
            OperationalExecutionContextService.create(
                execution_id=state["execution_id"],
                mission_id=state["mission_id"],
                repository=ROOT,
                repository_baseline=state["repository_baseline"],
                wop_submission_digest="b" * 64,
                workspace=self.workspace,
                gate_plan=self.plan(),
                authorization={
                    "decision": "DENIED",
                    "execution_id": state["execution_id"],
                },
            )
        context = self.provider(
            self.executions.load(
                self.runtime()
                .start(self.admission["admission_id"], at=self.at, max_gates=1)[
                    "execution_id"
                ]
            ),
            self.admission["artifacts"]["wop_result"]["wop"],
        )
        tampered = deepcopy(context)
        tampered["mission_id"] = "TAMPERED"
        with self.assertRaisesRegex(OperationalContextError, "digest"):
            OperationalExecutionContextService.validate(tampered)

    def test_handler_manifest_is_strictly_operational(self):
        inventory = self.registry.inventory()
        self.assertEqual(inventory[0]["modes"], ["operational"])
        self.assertTrue(inventory[0]["mutating"])
        with self.assertRaisesRegex(Exception, "no compatible"):
            self.registry.negotiate(
                mode="qualification", gates=["EXECUTE_WORK"]
            )

    def test_production_runtime_still_blocks_without_explicit_enablement(self):
        state = MissionExecutionRuntime(
            ROOT,
            self.executions,
            self.admissions,
            handler_framework=self.framework,
            operational_context_provider=self.provider,
        ).start(self.admission["admission_id"], at=self.at)
        self.assertEqual(state["state"], "Waiting")
        self.assertEqual(
            state["wait_reason"]["category"], "OPERATIONAL_DISPATCH_DISABLED"
        )
        self.assertFalse(self.workspace.exists())


if __name__ == "__main__":
    unittest.main()
