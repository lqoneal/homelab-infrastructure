"""Focused tests for the passive Zeus Codex timing facility."""

from __future__ import annotations

import concurrent.futures
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.codex_session_timing import (
    SCHEMA_VERSION,
    TimingStore,
    average_statistics,
    format_duration,
    record_passive_managed_timing,
)


ZEUS = ROOT / "scripts/zeus"


def _fixed(value: int) -> datetime:
    return datetime(2026, 8, 9, 10, value, tzinfo=timezone.utc)


def _concurrent_record(root: str, index: int) -> str:
    store = TimingStore(root)
    record = store.record(
        record_id=f"concurrent-{index}",
        started_at=_fixed(index % 50),
        ended_at=_fixed((index % 50) + 1),
        elapsed_seconds=index + 1,
        child_exit_code=0,
        context={"invocation_mode": "DIRECT_CODEX_CLI", "command_surface": ["codex", "exec"]},
    )
    return record["record_id"]


class TimingMathTests(unittest.TestCase):
    def test_duration_formatting_boundaries_and_rounding(self) -> None:
        self.assertEqual("01:35", format_duration(95))
        self.assertEqual("01:02:05", format_duration(3725))
        self.assertEqual("12:23", format_duration(742.5))
        self.assertEqual("11:28", format_duration(688.4))

    def test_average_first_and_multiple_sessions(self) -> None:
        self.assertEqual({"sample_count": 0, "average_seconds": 0.0, "average_formatted": "00:00"}, average_statistics([]))
        self.assertEqual({"sample_count": 1, "average_seconds": 95.0, "average_formatted": "01:35"}, average_statistics([{"record_status": "COMPLETED", "elapsed_seconds": 95}]))
        self.assertEqual({"sample_count": 2, "average_seconds": 1910.0, "average_formatted": "31:50"}, average_statistics([
            {"record_status": "COMPLETED", "elapsed_seconds": 95},
            {"record_status": "COMPLETED", "elapsed_seconds": 3725},
        ]))


class TimingStoreTests(unittest.TestCase):
    def test_records_are_atomic_append_only_and_summary_is_derived(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TimingStore(directory)
            first = store.record(record_id="one", started_at=_fixed(1), ended_at=_fixed(2), elapsed_seconds=95, child_exit_code=0)
            second = store.record(record_id="two", started_at=_fixed(3), ended_at=_fixed(4), elapsed_seconds=3725, child_exit_code=0)
            self.assertEqual(SCHEMA_VERSION, first["schema_version"])
            self.assertEqual("01:35", first["elapsed_formatted"])
            self.assertEqual("01:02:05", second["elapsed_formatted"])
            summary = store.summary()
            self.assertEqual(2, summary["sample_count"])
            self.assertEqual(1910.0, summary["average_seconds"])
            self.assertEqual("31:50", summary["average_formatted"])

            store.summary_path.write_text(json.dumps({"sample_count": 999}), encoding="utf-8")
            rebuilt = store.summary()
            self.assertEqual(2, rebuilt["sample_count"])
            self.assertEqual(1910.0, rebuilt["average_seconds"])
            self.assertEqual("31:50", rebuilt["average_formatted"])
            self.assertEqual(first, store.record(record_id="one", started_at=_fixed(1), ended_at=_fixed(2), elapsed_seconds=95, child_exit_code=99))
            self.assertEqual(2, len(store.records()))
            self.assertFalse(list(store.root.glob("*.tmp")))
            self.assertFalse(list(store.sessions.glob("*.tmp")))
            self.assertIsInstance(json.loads(store.summary_path.read_text(encoding="utf-8")), dict)

    def test_incomplete_records_do_not_count_and_same_id_finalization_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TimingStore(directory)
            store.sessions.mkdir(parents=True)
            (store.sessions / "partial.json").write_text(json.dumps({"record_id": "partial", "record_status": "STARTED"}), encoding="utf-8")
            self.assertEqual(0, store.summary()["sample_count"])
            observation = store.start(started_at=_fixed(5), started_monotonic=100.0)
            first = store.finalize(observation, child_exit_code=0, ended_at=_fixed(6), ended_monotonic=195.0)
            replay = store.finalize(observation, child_exit_code=17, ended_at=_fixed(7), ended_monotonic=500.0)
            self.assertEqual(first, replay)
            self.assertEqual(1, store.summary()["sample_count"])

    def test_concurrent_record_creation_has_no_lost_or_duplicate_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                ids = list(executor.map(lambda index: _concurrent_record(directory, index), range(16)))
            self.assertEqual(16, len(set(ids)))
            records = TimingStore(directory).records()
            self.assertEqual(16, len(records))
            self.assertEqual(16, TimingStore(directory).summary()["sample_count"])

    def test_passive_managed_integration_accepts_events_without_runtime_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record = record_passive_managed_timing(
                TimingStore(directory), record_id="managed-event-1", start_timestamp=_fixed(8),
                end_timestamp=_fixed(9), elapsed_seconds=60, mission_id="MISSION-1",
                execution_id="EXECUTION-1", codex_session_id="CODEX-1",
                execution_session_id="EXEC-SESSION-1", provider_session_id="PROVIDER-SESSION-1",
            )
            self.assertTrue(record["zeus_managed"])
            self.assertEqual("ZEUS_MANAGED", record["execution_classification"])
            self.assertEqual("MISSION-1", record["mission_id"])
            self.assertEqual("PASSIVE_LIFECYCLE_EVENT", record["invocation_mode"])
            self.assertFalse((Path(directory) / "runtime-identity.json").exists())


class DirectCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.fake = self.root / "fake-codex"
        self.fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, signal, sys\n"
            "print('CHILD_ARGS=' + json.dumps(sys.argv[1:]))\n"
            "print('CHILD_CWD=' + os.getcwd())\n"
            "print('CHILD_STDERR', file=sys.stderr)\n"
            "if os.environ.get('FAKE_SIGNAL'):\n"
            "    os.kill(os.getpid(), int(os.environ['FAKE_SIGNAL']))\n"
            "sys.exit(int(os.environ.get('FAKE_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _run(self, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "ZEUS_CODEX_BIN": str(self.fake),
            "ZEUS_CODEX_TIMING_ROOT": str(self.root / "logs"),
            **extra,
        }
        return subprocess.run([sys.executable, str(ZEUS), "codex", "timed", *args], cwd=self.root,
                              env=env, text=True, capture_output=True, check=False)

    def test_success_nonzero_and_stream_argument_workdir_exit_preservation(self) -> None:
        result = self._run("exec", "--sandbox", "workspace-write", "PROMPT", FAKE_EXIT="7",
                           ZEUS_CODEX_TIMING_MISSION_ID="MISSION-1", ZEUS_CODEX_TIMING_EXECUTION_ID="EXEC-1",
                           ZEUS_CODEX_TIMING_CODEX_SESSION_ID="CODEX-1")
        self.assertEqual(7, result.returncode)
        self.assertIn('CHILD_ARGS=["exec", "--sandbox", "workspace-write", "PROMPT"]', result.stdout)
        self.assertIn(f"CHILD_CWD={self.root}", result.stdout)
        self.assertIn("CHILD_STDERR", result.stderr)
        self.assertIn("CODEX_EXIT_CODE=7", result.stdout)
        record_path = next((self.root / "logs" / "sessions").glob("*.json"))
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(7, record["child_exit_code"])
        self.assertEqual("DIRECT", record["execution_classification"])
        self.assertFalse(record["zeus_managed"])
        self.assertEqual("MISSION-1", record["mission_id"])
        self.assertEqual("EXEC-1", record["execution_id"])
        self.assertEqual("CODEX-1", record["codex_session_id"])
        self.assertEqual(str(self.root), record["working_directory"])

    def test_signal_is_recorded_and_wrapper_preserves_signal_termination(self) -> None:
        result = self._run("exec", FAKE_SIGNAL=str(signal.SIGTERM))
        self.assertEqual(-signal.SIGTERM, result.returncode)
        record = json.loads(next((self.root / "logs" / "sessions").glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual("SIGNAL_SIGTERM", record["termination_classification"])

    def test_timing_does_not_create_or_mutate_zeus_runtime(self) -> None:
        runtime = self.root / "managed-runtime"
        result = self._run("exec", FAKE_EXIT="0", ZEUS_RUNTIME_ROOT=str(runtime))
        self.assertEqual(0, result.returncode)
        self.assertFalse(runtime.exists())

    def test_summary_cli_reads_only_timing_root(self) -> None:
        result = self._run("exec", FAKE_EXIT="0")
        self.assertEqual(0, result.returncode)
        env = {**os.environ, "ZEUS_CODEX_TIMING_ROOT": str(self.root / "logs"), "PYTHONDONTWRITEBYTECODE": "1"}
        summary = subprocess.run([sys.executable, str(ZEUS), "codex", "timing", "summary", "--json"], cwd=self.root,
                                 env=env, text=True, capture_output=True, check=False)
        self.assertEqual(0, summary.returncode, summary.stderr)
        self.assertEqual(1, json.loads(summary.stdout)["sample_count"])


if __name__ == "__main__":
    unittest.main()
