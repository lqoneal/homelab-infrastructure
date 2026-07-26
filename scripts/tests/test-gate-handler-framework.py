#!/usr/bin/env python3
"""ZEUS-P2-009 Operational Gate Handler Framework tests."""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.gate_handlers import (  # noqa: E402
    API_VERSION,
    REQUIRED_CAPABILITIES,
    GateHandlerError,
    GateHandlerFramework,
    GateHandlerTimeout,
    HandlerManifest,
    HandlerRegistry,
    QualificationGateHandler,
    qualification_framework,
)
from scripts.lib.emp.mission_admission_runtime import (  # noqa: E402
    AdmissionStateStore,
    MissionAdmissionRuntime,
)
from scripts.lib.emp.mission_execution_runtime import (  # noqa: E402
    ExecutionStateStore,
    MissionExecutionRuntime,
)

AT = datetime(2026, 7, 27, 8, 0, tzinfo=timezone.utc)


def context(completed=()):
    return {
        "execution_id": "MISSION-EXECUTION-TEST",
        "gate_idempotency_key": "MISSION-EXECUTION-TEST:EXECUTE_WORK",
        "mission_id": "ZEUS-P2-009-QUALIFICATION",
        "repository": str(ROOT),
        "wop": {"submission_digest": "a" * 64},
        "completed_gates": list(completed),
        "checkpoints": [],
        "cancellation_requested": False,
        "retry_count": 0,
        "at": "2026-07-27T08:00:00Z",
    }


class SlowHandler(QualificationGateHandler):
    manifest = HandlerManifest(
        handler_id="zeus.qualification.slow",
        version="1.0.0",
        api_version=API_VERSION,
        modes=("qualification",),
        gates=("EXECUTE_WORK",),
        capabilities=frozenset(REQUIRED_CAPABILITIES),
        mutating=False,
    )

    def execute_required(self, gate_id, execution_context, work):
        time.sleep(1)
        return super().execute_required(gate_id, execution_context, work)


class FailingHandler(SlowHandler):
    manifest = HandlerManifest(
        handler_id="zeus.qualification.failing",
        version="1.0.0",
        api_version=API_VERSION,
        modes=("qualification",),
        gates=("EXECUTE_WORK",),
        capabilities=frozenset(REQUIRED_CAPABILITIES),
        mutating=False,
    )

    def execute_required(self, gate_id, execution_context, work):
        raise RuntimeError("isolated failure")


class GateHandlerFrameworkTests(unittest.TestCase):
    def test_manifest_discovery_and_capability_negotiation(self):
        registry = HandlerRegistry()
        registry.register(QualificationGateHandler())
        manifests = registry.discover(ROOT / "engineering/handlers")
        self.assertEqual(len(manifests), 1)
        self.assertEqual(
            registry.inventory()[0]["handler_id"],
            "zeus.qualification.reference",
        )
        selected = registry.negotiate(
            mode="qualification",
            gates=["EXECUTE_WORK", "VERIFY_COMPLETION"],
        )
        self.assertIsInstance(selected, QualificationGateHandler)
        with self.assertRaisesRegex(GateHandlerError, "no compatible"):
            registry.negotiate(mode="operational", gates=["EXECUTE_WORK"])

    def test_verification_first_trace_and_previously_satisfied_skip(self):
        framework = qualification_framework(ROOT)
        result = framework.execute(
            mode="qualification", gate_id="EXECUTE_WORK", context=context()
        )
        self.assertTrue(result["verification_first"])
        self.assertEqual(
            [item["step"] for item in result["handler_trace"]],
            [
                "VERIFY_CURRENT",
                "DETERMINE_REQUIRED",
                "EXECUTE_REQUIRED",
                "VERIFY_RESULT",
            ],
        )
        self.assertFalse(result["side_effects_performed"])
        skipped = framework.execute(
            mode="qualification",
            gate_id="EXECUTE_WORK",
            context=context(("EXECUTE_WORK",)),
        )
        self.assertEqual(skipped["disposition"], "PREVIOUSLY_SATISFIED")
        self.assertEqual(skipped["handler_trace"][2]["step"], "SKIP_SATISFIED")

    def test_timeout_terminates_isolated_handler(self):
        registry = HandlerRegistry()
        handler = SlowHandler()
        registry.register(handler)
        registry.activate_registered(handler.manifest.handler_id)
        framework = GateHandlerFramework(registry, timeout_seconds=0.05)
        with self.assertRaisesRegex(GateHandlerTimeout, "timed out"):
            framework.execute(
                mode="qualification", gate_id="EXECUTE_WORK", context=context()
            )

    def test_handler_failure_is_structured_and_isolated(self):
        registry = HandlerRegistry()
        handler = FailingHandler()
        registry.register(handler)
        registry.activate_registered(handler.manifest.handler_id)
        framework = GateHandlerFramework(registry)
        with self.assertRaisesRegex(GateHandlerError, "isolated failure"):
            framework.execute(
                mode="qualification", gate_id="EXECUTE_WORK", context=context()
            )

    def test_incompatible_discovered_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.yaml"
            value = QualificationGateHandler.manifest.to_mapping()
            value["api_version"] = "zeus-gate-handler/999"
            path.write_text(yaml.safe_dump(value, sort_keys=False))
            registry = HandlerRegistry()
            registry.register(QualificationGateHandler())
            with self.assertRaisesRegex(GateHandlerError, "incompatible"):
                registry.discover(temporary)

    def test_execution_runtime_uses_discovered_verification_first_handler(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            admissions = AdmissionStateStore(directory / "admissions")
            admission = MissionAdmissionRuntime(ROOT, admissions).start(
                {
                    "mode": "qualification",
                    "intent": "Qualify verification-first handlers",
                    "mission_id": "ZEUS-P2-009-QUALIFICATION",
                    "phase_id": "GATE-HANDLERS",
                    "repository": str(ROOT),
                },
                at=AT,
            )
            state = MissionExecutionRuntime(
                ROOT,
                ExecutionStateStore(directory / "executions"),
                admissions,
            ).start(admission["admission_id"], at=AT)
            self.assertEqual(state["state"], "Completed")
            delegated = [
                entry
                for entry in state["evidence"]
                if entry["event"] == "GATE_COMPLETED"
                and entry["payload"]["gate_id"]
                in {"EXECUTE_WORK", "VERIFY_COMPLETION"}
            ]
            self.assertEqual(len(delegated), 2)
            self.assertTrue(
                all(
                    entry["payload"]["result"]["verification_first"]
                    for entry in delegated
                )
            )
            self.assertTrue(
                all(
                    entry["payload"]["result"]["handler_id"]
                    == "zeus.qualification.reference"
                    for entry in delegated
                )
            )


if __name__ == "__main__":
    unittest.main()
