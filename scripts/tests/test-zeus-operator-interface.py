#!/usr/bin/env python3
"""Qualification tests for the Zeus global launcher and orientation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.operator_interface import (  # noqa: E402
    ORIENTATION_LIMIT,
    OperatorInterfaceStore,
    initial_state,
)
from scripts.lib.emp.orchestration import OrchestrationError  # noqa: E402

ZEUS = ROOT / "scripts/zeus"
INSTALLER = ROOT / "scripts/install-zeus-launcher"


def run_zeus(state: Path, *arguments: str, suppress: bool = False):
    environment = {
        **os.environ,
        "ZEUS_TESTING": "operator",
        "ZEUS_OPERATOR_STATE": str(state),
    }
    if suppress:
        environment["ZEUS_NO_INTRO"] = "1"
    return subprocess.run(
        [str(ZEUS), *arguments],
        text=True,
        capture_output=True,
        env=environment,
    )


class OperatorStateTests(unittest.TestCase):
    def test_fresh_initialization_and_persistence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            store = OperatorInterfaceStore(ROOT, path)
            self.assertEqual(store.load(), initial_state())
            self.assertEqual(store.increment()["invocation_count"], 1)
            self.assertEqual(
                OperatorInterfaceStore(ROOT, path).load()["invocation_count"], 1
            )
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_boundaries_one_one_hundred_and_one_hundred_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            store = OperatorInterfaceStore(ROOT, path)
            self.assertEqual(store.increment()["invocation_count"], 1)
            for _ in range(98):
                store.increment()
            self.assertEqual(store.increment()["invocation_count"], ORIENTATION_LIMIT)
            self.assertEqual(store.increment()["invocation_count"], ORIENTATION_LIMIT + 1)

    def test_strict_corruption_rejections(self):
        bad_values = [
            "{broken",
            json.dumps({**initial_state(), "schema_version": 2}),
            json.dumps({**initial_state(), "invocation_count": -1}),
            json.dumps({**initial_state(), "invocation_count": 1.5}),
            json.dumps({"schema_version": 1, "invocation_count": 0}),
            json.dumps({**initial_state(), "unexpected": True}),
        ]
        for serialized in bad_values:
            with self.subTest(serialized=serialized):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "state.json"
                    path.write_text(serialized)
                    with self.assertRaises(OrchestrationError):
                        OperatorInterfaceStore(ROOT, path).load()

    def test_symlinked_state_and_runtime_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target.json"
            target.write_text(json.dumps(initial_state()))
            link = base / "state.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(OrchestrationError, "symbolic"):
                OperatorInterfaceStore(ROOT, link).load()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            real = base / "real"
            real.mkdir()
            linked = base / "linked"
            linked.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(OrchestrationError, "symbolic"):
                OperatorInterfaceStore(base, linked / "state.json").load()


class CliTests(unittest.TestCase):
    def test_bare_help_and_explicit_help(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            bare = run_zeus(state)
            help_result = run_zeus(state, "--help")
            self.assertEqual(bare.returncode, 0, bare.stderr)
            self.assertIn("Supervised Zeus", bare.stdout)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("intro", help_result.stdout)

    def test_status_json_uses_live_beta_and_canonical_lifecycle_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            result = run_zeus(state, "status", "--json", suppress=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            for key in (
                "active_operation", "authority_source", "next_authorized_action",
                "current_platform_mission", "current_executable_mission",
                "canonical_lifecycle", "current_state_authority",
            ):
                self.assertIn(key, value)
            self.assertEqual(value["current_state_authority"], "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN")

    def test_status_human_surface_contains_required_sections(self):
        result = subprocess.run(
            [str(ZEUS), "status"],
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "ZEUS_NO_INTRO": "1",
                "ZEUS_PROGRESSIVE_OA": "0",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for section in ("Operation Beta authority", "Active gate:", "Next authorized action:"):
            self.assertIn(section, result.stdout)

    def test_orientation_is_explicit_and_stderr_separated(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            first = run_zeus(state, "status")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(
                json.loads(first.stdout)["current_state_authority"],
                "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
            )
            value = initial_state()
            value["invocation_count"] = 99
            state.write_text(json.dumps(value))
            hundred = run_zeus(state)
            self.assertEqual(hundred.stderr, "")
            hundred_one = run_zeus(state)
            self.assertNotIn("supervised engineering orchestration", hundred_one.stderr)
            verbose = run_zeus(state, "--verbose", "status")
            self.assertIn("supervised engineering orchestration", verbose.stderr)

    def test_help_and_parse_failures_count_but_state_override_does_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            self.assertEqual(run_zeus(state, "--help").returncode, 0)
            invalid = run_zeus(state, "not-a-command")
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(OperatorInterfaceStore(ROOT, state).load()["invocation_count"], 1)
            override = run_zeus(
                state,
                "--state",
                str(Path(temporary) / "engineering-state.json"),
                "status",
            )
            self.assertEqual(override.returncode, 0, override.stderr)
            self.assertEqual(
                OperatorInterfaceStore(ROOT, state).load()["invocation_count"], 1
            )

    def test_status_stdout_is_json_and_intro_review_survives_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            store = OperatorInterfaceStore(ROOT, state)
            for _ in range(101):
                store.increment()
            status = run_zeus(state, "--state", str(Path(temporary) / "missing"), "status")
            # An explicit engineering-state override deliberately bypasses counting.
            self.assertEqual(status.returncode, 0, status.stderr)
            json.loads(status.stdout)
            review = run_zeus(state, "intro")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("supervised engineering orchestration", review.stdout)
            report = run_zeus(state, "intro", "--status")
            self.assertEqual(json.loads(report.stdout)["invocation_count"], 101)

    def test_suppression_does_not_reset_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            result = run_zeus(state, "intro", "--status", suppress=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(OperatorInterfaceStore(ROOT, state).load()["invocation_count"], 0)


class LauncherTests(unittest.TestCase):
    def invoke(self, home: Path, action: str):
        environment = {
            **os.environ,
            "HOME": str(home),
            "PATH": f"{home / '.local/bin'}:{os.environ['PATH']}",
        }
        return subprocess.run(
            [str(INSTALLER), action],
            text=True,
            capture_output=True,
            env=environment,
            cwd="/tmp",
        )

    def test_install_verify_idempotence_outside_repo_and_remove(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            first = self.invoke(home, "install")
            second = self.invoke(home, "install")
            verified = self.invoke(home, "verify")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("already correct", second.stdout)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            launcher = home / ".local/bin/zeus"
            result = subprocess.run(
                [str(launcher), "--help"],
                text=True,
                capture_output=True,
                cwd="/tmp",
                env={
                    **os.environ,
                    "ZEUS_TESTING": "1",
                    "ZEUS_OPERATOR_STATE": str(home / "operator-state.json"),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.invoke(home, "remove").returncode, 0)
            self.assertFalse(launcher.exists())
            self.assertEqual(self.invoke(home, "remove").returncode, 0)

    def test_conflict_is_rejected_and_not_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            launcher = home / ".local/bin/zeus"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("conflict")
            result = self.invoke(home, "install")
            self.assertEqual(result.returncode, 78)
            self.assertEqual(launcher.read_text(), "conflict")
            remove = self.invoke(home, "remove")
            self.assertEqual(remove.returncode, 78)
            self.assertTrue(launcher.exists())


if __name__ == "__main__":
    unittest.main()
