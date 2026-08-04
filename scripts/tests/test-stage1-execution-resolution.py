#!/usr/bin/env python3
"""Disposable qualification of the Stage 1 execution resolver."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.stage1_execution_resolution import (  # noqa: E402
    Stage1ExecutionResolutionError,
    resolve,
)
from scripts.lib.emp.stage1_runtime import Stage1Store  # noqa: E402


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Stage1ExecutionResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.package = base / "package"
        (self.package / "manifests").mkdir(parents=True)
        (self.package / "mission.yaml").write_text(yaml.safe_dump({
            "mission_id": "MISSION-DISPOSABLE-001", "wop_id": "WOP-DISPOSABLE-001",
            "phase_id": "PHASE-1", "revision": 1, "status": "Active",
            "title": "Disposable", "objective": "qualification",
        }))
        (self.package / "manifests" / "immutable-manifest.yaml").write_text("wop_id: WOP-DISPOSABLE-001\n")
        self.state = base / "stage1"
        self.admissions = base / "admissions"
        self.executions = base / "executions"
        def receipt(kind, **values):
            value = {"receipt_type": kind, **values}
            value["receipt_id"] = f"RECEIPT-{kind}"
            value["receipt_digest"] = digest(value)
            return value
        self.record = {
            "schema_version": 3, "lifecycle_integrity": "RECEIPT_BACKED_V1",
            "instance_id": "ZEUS-DEVELOPMENT-INSTANCE-001", "mission_id": "MISSION-DISPOSABLE-001",
            "wop_id": "WOP-DISPOSABLE-001", "state": "ADMITTED", "repository": str(ROOT),
            "execution_mode": "DEVELOPMENT",
            "package": str(self.package), "package_digest": "package-digest",
            "source_digest": "source-digest", "repository_baseline": "baseline",
            "authority_snapshot": {"authority_snapshot_digest": "authority-digest"},
            "phases": ["ADMITTED"],
            "receipts": {"admission": receipt("admission", admission_id="EMM-DEV-ADMISSION-001")},
        }
        Stage1Store(self.state).save(self.record)

    def tearDown(self):
        self.temp.cleanup()

    def test_resolves_transaction_without_runtime_projections(self):
        result = resolve(ROOT, self.state, self.admissions, self.executions)
        self.assertEqual("STAGE1", result["source"])
        self.assertEqual("ZEUS-DEVELOPMENT-INSTANCE-001", result["identities"]["transaction_id"])
        self.assertEqual("EMM-DEV-ADMISSION-001", result["admission_id"])
        self.assertIsNone(result["execution"])
        self.assertEqual("STAGE1_RECEIPT_BACKED", result["admission"]["runtime_source"])

    def test_conflicting_execution_projections_fail_closed(self):
        self.executions.mkdir()
        for suffix in ("a", "b"):
            (self.executions / f"MISSION-EXECUTION-{suffix}.json").write_text(json.dumps({
                "execution_id": f"MISSION-EXECUTION-{suffix}",
                "admission_id": "EMM-DEV-ADMISSION-001",
            }))
        with self.assertRaises(Stage1ExecutionResolutionError):
            resolve(ROOT, self.state, self.admissions, self.executions)


if __name__ == "__main__":
    unittest.main()
