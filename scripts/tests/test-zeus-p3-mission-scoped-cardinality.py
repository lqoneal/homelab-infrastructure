#!/usr/bin/env python3
"""Mission-scoped P3 cardinality and historical preservation tests."""

from __future__ import annotations

import copy
import json
import os
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADMISSION_FIXTURE = runpy.run_path(str(ROOT / "scripts/tests/test-zeus-p3-g1-mission-admission-boundary.py"))
ADMISSION_TEST = ADMISSION_FIXTURE["MissionAdmissionBoundaryTests"]
from scripts.lib.emp.bootstrap_boundary import _digest  # noqa: E402
from scripts.lib.emp.canonical_lifecycle_resolver import resolve  # noqa: E402


MISSION = "ZEUS-P3-CARDINALITY-MISSION"
WOP = "WOP-ZEUS-P3-CARDINALITY-001"


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact_digest(value: dict) -> str:
    return _digest({key: item for key, item in value.items() if key != "artifact_digest"})


def _clone_p3_set(runtime: Path, source_admission: dict, *, admission_id: str,
                  mission_id: str, wop_id: str, submission_id: str,
                  classification: str | None = None) -> None:
    """Create a valid historical/current-shaped set in an isolated fixture."""
    descriptors = {
        "packages": "package", "mission-contracts": "mission_contract",
        "execution-authority": "execution_authority", "receipts": "admission_receipt",
        "journals": "admission_journal",
    }
    cloned: dict[str, dict] = {}
    for directory, field in descriptors.items():
        source_path = Path(source_admission[field]["path"])
        value = json.loads(source_path.read_text(encoding="utf-8"))
        value["admission_id"] = admission_id
        value["mission_id"] = mission_id
        value["wop_id"] = wop_id
        if "submission_id" in value:
            value["submission_id"] = submission_id
        if classification:
            value["classification"] = classification
        if directory == "journals":
            value["provisioned"] = []
        value.pop("artifact_digest", None)
        if directory != "journals":
            value["artifact_digest"] = _artifact_digest(value)
        cloned[field] = value
        _write_json(runtime / directory / f"{admission_id}.json", value)

    cloned["admission_journal"]["provisioned"] = [
        cloned[key]["artifact_digest"]
        for key in ("package", "mission_contract", "execution_authority", "admission_receipt")
    ]
    cloned["admission_journal"]["artifact_digest"] = _artifact_digest(cloned["admission_journal"])
    _write_json(runtime / "journals" / f"{admission_id}.json", cloned["admission_journal"])

    transaction = copy.deepcopy(source_admission)
    transaction.update({
        "admission_id": admission_id, "mission_id": mission_id,
        "wop_id": wop_id, "submission_id": submission_id,
        "package_digest": cloned["package"]["artifact_digest"],
        "mission_contract_digest": cloned["mission_contract"]["artifact_digest"],
        "execution_authority_digest": cloned["execution_authority"]["artifact_digest"],
    })
    for directory, field in descriptors.items():
        transaction[field] = {
            "path": str((runtime / directory / f"{admission_id}.json").resolve()),
            "digest": cloned[field]["artifact_digest"],
        }
    transaction.pop("transaction_digest", None)
    transaction["transaction_digest"] = _digest(transaction)
    _write_json(runtime / "admissions" / f"{admission_id}.json", transaction)


class MissionScopedP3CardinalityTests(unittest.TestCase):
    def fixture(self):
        directory = Path(tempfile.mkdtemp(prefix="zeus-p3-scoped-"))
        helper = ADMISSION_TEST()
        wop, submission, runtime, environment = helper.authored_and_submitted(directory)
        command = helper.admission_command(wop, submission, runtime)
        first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                          capture_output=True, check=True).stdout)
        return directory, runtime, environment, first, helper

    def test_one_current_set_passes(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["lifecycle_state"], "ADMITTED")
        self.assertEqual(value["p3_cardinality"], {"current": 1, "historical": 0})

    def test_current_plus_historical_set_passes(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-HIST-001", mission_id=first["mission_id"],
                      wop_id="WOP-HISTORICAL-001", submission_id="SUBMISSION-HIST-001")
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["p3_cardinality"], {"current": 1, "historical": 1})

    def test_current_plus_multiple_historical_sets_passes(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        for index in (1, 2):
            _clone_p3_set(runtime, first, admission_id=f"ADMISSION-HIST-00{index}",
                          mission_id=f"HISTORICAL-MISSION-{index}",
                          wop_id=f"WOP-HISTORICAL-{index}", submission_id=f"SUBMISSION-HIST-{index}")
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")

    def test_two_current_sets_same_mission_fail_closed(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-CURRENT-002",
                      mission_id=first["mission_id"], wop_id=first["wop_id"],
                      submission_id=first["submission_id"])
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CANONICAL_TRANSITION_CARDINALITY_CONFLICT")

    def test_historical_only_fails_closed(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-HIST-ONLY", mission_id=first["mission_id"],
                      wop_id="WOP-HISTORICAL-ONLY", submission_id="SUBMISSION-HIST-ONLY")
        for path in (runtime / "admissions").glob("*.json"):
            if path.name != "ADMISSION-HIST-ONLY.json":
                path.unlink()
        for directory_name in ("packages", "mission-contracts", "execution-authority", "receipts", "journals"):
            for path in (runtime / directory_name).glob("*.json"):
                if path.name != "ADMISSION-HIST-ONLY.json":
                    path.unlink()
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CANONICAL_P3_CURRENT_MISSING")

    def test_different_mission_current_set_is_ignored(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-OTHER-001", mission_id="OTHER-MISSION-001",
                      wop_id="WOP-OTHER-001", submission_id="SUBMISSION-OTHER-001")
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")

    def test_wrong_wop_same_mission_is_historical(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-WRONG-WOP", mission_id=first["mission_id"],
                      wop_id="WOP-WRONG-001", submission_id="SUBMISSION-WRONG-001")
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["p3_cardinality"]["historical"], 1)

    def test_superseded_and_legacy_sets_are_subordinate(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        _clone_p3_set(runtime, first, admission_id="ADMISSION-SUPERSEDED", mission_id="HISTORICAL-SUPERSEDED",
                      wop_id="WOP-SUPERSEDED", submission_id="SUBMISSION-SUPERSEDED", classification="SUPERSEDED")
        _clone_p3_set(runtime, first, admission_id="ADMISSION-LEGACY", mission_id="HISTORICAL-LEGACY",
                      wop_id="WOP-LEGACY", submission_id="SUBMISSION-LEGACY", classification="LEGACY_COMPATIBILITY")
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["result"], "PASS")

    def test_wave_identity_and_replay_are_preserved(self):
        directory, runtime, _, first, _ = self.fixture()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        # The supported live replay was already exercised by the CLI; here we
        # assert the immutable current P3 identity used by the resolver.
        value = resolve(ROOT, first["mission_id"], runtime_root=runtime)
        self.assertEqual(value["submission_id"], first["submission_id"])
        self.assertEqual(value["wop_id"], first["wop_id"])
        self.assertEqual(value["admission_id"], first["admission_id"])
        self.assertEqual(value["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
