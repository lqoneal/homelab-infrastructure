#!/usr/bin/env python3
"""Regression tests for EMP Execution Oversight."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.execution_oversight import (
    DigestFixtureAuthenticator,
    ExecutionOversight,
    ExecutionState,
    OversightError,
    OversightStore,
    digest,
)
from scripts.lib.emp.wop_dispatch import ExecutionAssignment


REPOSITORY = str(ROOT)
BASELINE = "8246dc3460313d0d70d53fd949540bcc13148388"
START = datetime(2026, 7, 25, 2, 0, tzinfo=timezone.utc)


class ExecutionOversightTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state_path = Path(temporary.name) / "oversight.json"
        self.manager = ExecutionOversight(OversightStore(self.state_path))
        package = {
            "authority_chain": ["work-package", "mission", "governance"],
            "authorization_decision_digest": "1" * 64,
            "repository_baseline": BASELINE,
            "repository_identity": REPOSITORY,
            "mission_id": "EMP-MISSION-ZEUS-OVERSIGHT-QUALIFICATION",
            "requested_capabilities": ["execute"],
            "wop_digest": "2" * 64,
            "wop_id": "WOP-523e4567-e89b-42d3-a456-426614174000",
        }
        self.assignment = ExecutionAssignment.create(
            package=package,
            intended_agent="supervised-agent-1",
            expected_evidence=("execution-report",),
            dispatch_timestamp=START,
            approval_reference="APPROVAL-MISSION-K-001",
        )
        value = self.assignment.data
        self.dispatch_event = {
            "assignment_checksum": value["assignment_checksum"],
            "assignment_id": value["assignment_id"],
            "delivery_artifact": value["assignment_id"] + ".json",
            "from": "Ready",
            "human_approval_reference": "APPROVAL-MISSION-K-001",
            "to": "Dispatched",
            "wop_id": value["wop_id"],
        }
        self.dispatch_event["event_digest"] = digest(self.dispatch_event)
        self.session = self.manager.create_session(
            self.assignment, self.dispatch_event, created_at=START
        )
        self.authenticator = DigestFixtureAuthenticator()
        self.counter = 0

    def envelope(
        self,
        state: ExecutionState,
        *,
        payload=None,
        seconds=None,
        changes=None,
    ):
        self.counter += 1
        value = {
            "assignment_id": self.assignment.data["assignment_id"],
            "baseline_commit": BASELINE,
            "event_identifier": f"EENS-EVENT-{self.counter:04d}",
            "execution_agent": "supervised-agent-1",
            "execution_state": state.value,
            "payload": payload or {"event_type": "state_changed"},
            "producing_component": "EENS",
            "repository_identity": REPOSITORY,
            "session_id": self.session["session_id"],
            "timestamp": (
                START + timedelta(seconds=seconds or self.counter)
            ).isoformat(),
        }
        value.update(changes or {})
        value["authentication_digest"] = digest(value)
        return value

    def ingest(self, state, **kwargs):
        return self.manager.ingest_eens_event(
            self.session["session_id"],
            self.envelope(state, **kwargs),
            authenticator=self.authenticator,
        )

    def running(self):
        self.ingest(ExecutionState.ACCEPTED)
        self.ingest(ExecutionState.INITIALIZING)
        self.ingest(
            ExecutionState.RUNNING,
            payload={
                "checkpoint": "implementation-started",
                "event_type": "state_changed",
                "milestone": "implementation",
                "milestone_status": "pending",
            },
        )

    def test_session_is_deterministic_and_one_to_one(self) -> None:
        snapshot = self.manager.reconstruct(self.session["session_id"])
        self.assertEqual(snapshot["current_execution_state"], "Dispatched")
        self.assertEqual(snapshot["execution_agent_identity"], "supervised-agent-1")
        with self.assertRaisesRegex(OversightError, "one Execution Session"):
            self.manager.create_session(
                self.assignment, self.dispatch_event, created_at=START
            )

    def test_happy_path_reaches_completed(self) -> None:
        self.running()
        self.ingest(
            ExecutionState.COMPLETED,
            payload={
                "checkpoint": "agent-completed",
                "event_type": "state_changed",
                "milestone": "implementation",
                "milestone_status": "completed",
            },
        )
        replay = self.manager.reconstruct(self.session["session_id"])
        self.assertEqual(replay["current_execution_state"], "Completed")
        self.assertEqual(replay["completed_milestones"], ["implementation"])
        self.assertEqual(replay["pending_milestones"], [])

    def test_illegal_transition_fails_closed(self) -> None:
        with self.assertRaisesRegex(OversightError, "illegal execution transition"):
            self.ingest(ExecutionState.RUNNING)

    def test_terminal_state_is_immutable(self) -> None:
        self.running()
        self.ingest(ExecutionState.COMPLETED)
        with self.assertRaisesRegex(OversightError, "terminal"):
            self.ingest(ExecutionState.RUNNING)

    def test_eens_authentication_is_required(self) -> None:
        envelope = self.envelope(ExecutionState.ACCEPTED)
        envelope["authentication_digest"] = "0" * 64
        with self.assertRaisesRegex(OversightError, "authentication"):
            self.manager.ingest_eens_event(
                self.session["session_id"],
                envelope,
                authenticator=self.authenticator,
            )

    def test_eens_is_canonical_execution_event_source(self) -> None:
        envelope = self.envelope(
            ExecutionState.ACCEPTED,
            changes={"producing_component": "AGENT"},
        )
        envelope["authentication_digest"] = digest(
            {key: value for key, value in envelope.items() if key != "authentication_digest"}
        )
        with self.assertRaisesRegex(OversightError, "EENS"):
            self.manager.ingest_eens_event(
                self.session["session_id"], envelope, authenticator=self.authenticator
            )

    def test_all_event_bindings_are_enforced(self) -> None:
        changes = (
            {"assignment_id": "EA-wrong"},
            {"session_id": "SESSION-wrong"},
            {"repository_identity": "/wrong"},
            {"baseline_commit": "0" * 40},
            {"execution_agent": "wrong-agent"},
        )
        for change in changes:
            with self.subTest(change=change):
                envelope = self.envelope(ExecutionState.ACCEPTED, changes=change)
                envelope["authentication_digest"] = digest(
                    {
                        key: value
                        for key, value in envelope.items()
                        if key != "authentication_digest"
                    }
                )
                with self.assertRaisesRegex(OversightError, "binding"):
                    self.manager.ingest_eens_event(
                        self.session["session_id"],
                        envelope,
                        authenticator=self.authenticator,
                    )

    def test_duplicate_and_out_of_order_events_fail(self) -> None:
        envelope = self.envelope(ExecutionState.ACCEPTED, seconds=10)
        self.manager.ingest_eens_event(
            self.session["session_id"], envelope, authenticator=self.authenticator
        )
        with self.assertRaisesRegex(OversightError, "duplicate"):
            self.manager.ingest_eens_event(
                self.session["session_id"], envelope, authenticator=self.authenticator
            )
        with self.assertRaisesRegex(OversightError, "out of order"):
            self.ingest(ExecutionState.INITIALIZING, seconds=5)

    def test_approval_pause_and_explicit_resume(self) -> None:
        self.running()
        self.ingest(
            ExecutionState.WAITING_APPROVAL,
            payload={
                "approval_id": "EXEC-APPROVAL-1",
                "checkpoint": "pre-deploy",
                "event_type": "approval_requested",
            },
        )
        waiting = self.manager.reconstruct(self.session["session_id"])
        self.assertEqual(waiting["approval_status"], "awaiting")
        self.assertTrue(waiting["resume_eligibility"])
        with self.assertRaisesRegex(OversightError, "explicit approval"):
            self.ingest(ExecutionState.RESUMING)
        self.ingest(
            ExecutionState.WAITING_APPROVAL,
            payload={
                "approval_id": "EXEC-APPROVAL-1",
                "approval_status": "approved",
                "event_type": "approval_decision",
            },
        )
        self.ingest(ExecutionState.RESUMING)
        self.ingest(ExecutionState.RUNNING)
        self.assertEqual(
            self.manager.reconstruct(self.session["session_id"])[
                "current_execution_state"
            ],
            "Running",
        )

    def test_rejected_and_expired_approval_are_recorded(self) -> None:
        for decision in ("rejected", "expired"):
            with self.subTest(decision=decision):
                temporary = tempfile.TemporaryDirectory()
                self.addCleanup(temporary.cleanup)
                manager = ExecutionOversight(
                    OversightStore(Path(temporary.name) / "state.json")
                )
                session = manager.create_session(
                    self.assignment, self.dispatch_event, created_at=START
                )
                events = [
                    self.envelope(ExecutionState.ACCEPTED),
                    self.envelope(ExecutionState.INITIALIZING),
                    self.envelope(ExecutionState.RUNNING),
                    self.envelope(
                        ExecutionState.WAITING_APPROVAL,
                        payload={"event_type": "approval_requested"},
                    ),
                    self.envelope(
                        ExecutionState.WAITING_APPROVAL,
                        payload={
                            "approval_status": decision,
                            "event_type": "approval_decision",
                        },
                    ),
                ]
                for envelope in events:
                    envelope["session_id"] = session["session_id"]
                    envelope["authentication_digest"] = digest(
                        {
                            key: value
                            for key, value in envelope.items()
                            if key != "authentication_digest"
                        }
                    )
                    manager.ingest_eens_event(
                        session["session_id"],
                        envelope,
                        authenticator=self.authenticator,
                    )
                replay = manager.reconstruct(session["session_id"])
                self.assertEqual(replay["approval_status"], decision)
                self.assertFalse(replay["resume_eligibility"])

    def test_disconnect_interruption_builds_resume_plan(self) -> None:
        self.running()
        self.manager.detect_interruption(
            self.session["session_id"],
            cause="agent_disconnect",
            detected_at=START + timedelta(seconds=20),
        )
        replay = self.manager.reconstruct(self.session["session_id"])
        self.assertEqual(replay["current_execution_state"], "Paused")
        self.assertTrue(replay["resume_eligibility"])
        self.assertEqual(replay["expected_restart_point"], "implementation-started")
        self.assertEqual(replay["interruption_history"][0]["cause"], "agent_disconnect")

    def test_all_required_interruption_causes_are_supported(self) -> None:
        causes = {
            "agent_disconnect",
            "unexpected_termination",
            "repository_mismatch",
            "assignment_mismatch",
        }
        for cause in causes:
            with self.subTest(cause=cause):
                temporary = tempfile.TemporaryDirectory()
                self.addCleanup(temporary.cleanup)
                manager = ExecutionOversight(
                    OversightStore(Path(temporary.name) / "state.json")
                )
                session = manager.create_session(
                    self.assignment, self.dispatch_event, created_at=START
                )
                for state in (
                    ExecutionState.ACCEPTED,
                    ExecutionState.INITIALIZING,
                    ExecutionState.RUNNING,
                ):
                    envelope = self.envelope(state)
                    envelope["session_id"] = session["session_id"]
                    envelope["authentication_digest"] = digest(
                        {
                            key: value
                            for key, value in envelope.items()
                            if key != "authentication_digest"
                        }
                    )
                    manager.ingest_eens_event(
                        session["session_id"],
                        envelope,
                        authenticator=self.authenticator,
                    )
                manager.detect_interruption(
                    session["session_id"],
                    cause=cause,
                    detected_at=START + timedelta(minutes=2),
                )
                self.assertEqual(
                    manager.reconstruct(session["session_id"])[
                        "interruption_history"
                    ][0]["cause"],
                    cause,
                )

    def test_heartbeat_timeout_requires_elapsed_threshold(self) -> None:
        self.running()
        with self.assertRaisesRegex(OversightError, "has not elapsed"):
            self.manager.detect_interruption(
                self.session["session_id"],
                cause="heartbeat_timeout",
                detected_at=START + timedelta(seconds=5),
                heartbeat_timeout=timedelta(seconds=10),
            )
        self.manager.detect_interruption(
            self.session["session_id"],
            cause="heartbeat_timeout",
            detected_at=START + timedelta(seconds=20),
            heartbeat_timeout=timedelta(seconds=10),
        )

    def test_restart_replay_is_byte_equivalent(self) -> None:
        self.running()
        before = json.dumps(
            self.manager.reconstruct(self.session["session_id"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        restarted = ExecutionOversight(OversightStore(self.state_path))
        after = json.dumps(
            restarted.reconstruct(self.session["session_id"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(before, after)

    def test_tampered_ledger_and_payload_fail_on_restart(self) -> None:
        self.running()
        for target in ("ledger", "payload"):
            with self.subTest(target=target):
                value = json.loads(self.state_path.read_text())
                session = value["sessions"][self.session["session_id"]]
                if target == "ledger":
                    session["event_ledger"][-1]["execution_agent"] = "tampered"
                else:
                    event_id = session["event_ledger"][-1]["event_identifier"]
                    session["event_payloads"][event_id]["checkpoint"] = "tampered"
                path = Path(self.state_path.parent) / f"{target}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(OversightError, "hash|digest"):
                    ExecutionOversight(OversightStore(path))

    def test_cli_validates_and_replays(self) -> None:
        self.running()
        command = [str(ROOT / "scripts/execution-oversightctl"), str(self.state_path)]
        validate = subprocess.run(
            command + ["validate"], text=True, capture_output=True
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)
        replay = subprocess.run(
            command + ["replay", "--session", self.session["session_id"]],
            text=True,
            capture_output=True,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["current_execution_state"], "Running")

    def test_no_execution_dispatch_qualification_reconciliation_or_recovery(self) -> None:
        forbidden = {
            "execute",
            "dispatch",
            "qualify_evidence",
            "reconcile",
            "retry",
            "recover",
            "resume_automatically",
            "select_mission",
        }
        self.assertTrue(forbidden.isdisjoint(set(dir(self.manager))))


if __name__ == "__main__":
    unittest.main()
