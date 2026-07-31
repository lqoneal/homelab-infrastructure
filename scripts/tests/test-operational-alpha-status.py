#!/usr/bin/env python3
"""Current Operational Alpha status-resolution tests."""

from __future__ import annotations

import shutil
import sys
import tempfile
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.operational_alpha_status import (
    OperationalAlphaStatusError,
    resolve,
)


class OperationalAlphaStatusTests(unittest.TestCase):
    def copy_source(self, destination: Path, relative: str) -> None:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in (
            "engineering/work-orders/OA-01-IMPLEMENTATION-001/immutable-wop.yaml",
            "engineering/work-orders/OA-02-ADMISSION-ACTIVATION-AND-EXECUTION-001/immutable-wop.yaml",
            "engineering/operations/zeus-operational-alpha-progress.md",
            "docs/project/PROJ-0001-PROJECT_STATE.md",
            "engineering/work-orders/OA-03-EXECUTION-001/immutable-wop.yaml",
            "engineering/work-orders/OA-04-EXECUTION-001/immutable-wop.yaml",
            "engineering/work-orders/OA-05-EXECUTION-001/immutable-wop.yaml",
            "engineering/work-orders/OA-06-EXECUTION-001/immutable-wop.yaml",
            "engineering/work-orders/OA-07-EXECUTION-001/immutable-wop.yaml",
            "engineering/missions/operational-alpha-mission-knowledge.yaml",
            "engineering/metadata/operational-alpha-emm.yaml",
            "engineering/lifecycle-transitions/implementation-wop-lifecycle-transition.spec.yaml",
            "engineering/lifecycle-transitions/records/OA-03-READY-TO-ACTIVE.yaml",
            "engineering/lifecycle-transitions/records/OA-04-READY-TO-ACTIVE.yaml",
            "engineering/lifecycle-transitions/records/OA-05-READY-TO-ACTIVE.yaml",
            "engineering/lifecycle-transitions/records/OA-06-READY-TO-ACTIVE.yaml",
            "engineering/lifecycle-transitions/records/OA-07-READY-TO-ACTIVE.yaml",
            "engineering/authority-records/AR-OA-03-001.yaml",
            "engineering/authority-records/AR-OA-04-001.yaml",
            "engineering/authority-records/AR-OA-05-001.yaml",
            "engineering/authority-records/AR-OA-06-001.yaml",
            "engineering/authority-records/AR-OA-07-001.yaml",
            "engineering/execution/plans/WOP-bfdce94b-ef22-4d1e-bfda-633252794d5a.yaml",
            "engineering/execution/plans/WOP-48f1d7d1-4995-5f3e-9b5e-fb2f69595111.yaml",
            "engineering/execution/plans/WOP-0ec591ec-7c16-5bf7-8ed8-002ec9c4547f.yaml",
            "engineering/execution/plans/WOP-9ed7762f-c143-5a58-9a21-63fae5a06c05.yaml",
            "engineering/execution/plans/WOP-72d7c7f0-4632-5721-8fbf-65dbf89c7b1a.yaml",
            "engineering/activation-records/ACT-OA-03-001.yaml",
            "engineering/activation-records/ACT-OA-04-001.yaml",
            "engineering/activation-records/ACT-OA-05-001.yaml",
            "engineering/activation-records/ACT-OA-06-001.yaml",
            "engineering/activation-records/ACT-OA-07-001.yaml",
            "engineering/authority-records/AR-OA-01-001.yaml",
            "engineering/authority-records/AR-OA-02-001.yaml",
            "engineering/execution/plans/WOP-OA-01-IMPLEMENTATION-001.yaml",
            "engineering/execution/plans/WOP-502ce342-7fc9-577c-b906-07b00bf2a615.yaml",
            "engineering/activation-records/ACT-OA-01-001.yaml",
            "engineering/activation-records/ACT-OA-02-001.yaml",
        ):
            self.copy_source(root, relative)
        return root

    def test_resolves_current_wop_without_reading_historical_progressive_state(self) -> None:
        root = self.fixture()
        value = resolve(root)
        self.assertEqual("RESOLVED", value["outcome"])
        self.assertEqual("OA-07", value["active_gate"])
        self.assertEqual("ACTIVE", value["status"])
        self.assertEqual("COMPLETED", value["execution_state"])
        self.assertEqual("ELIGIBLE", value["authority_record_creation_eligibility"])
        self.assertEqual("ELIGIBLE", value["successor_eligibility"])
        self.assertEqual("EXCLUDED_EVIDENCE_ONLY", value["historical_progressive_runtime"])

    def test_conflicting_projection_fails_with_operator_options(self) -> None:
        root = self.fixture()
        progress = root / "engineering/operations/zeus-operational-alpha-progress.md"
        progress.write_text(
            progress.read_text(encoding="utf-8").replace(
                "CURRENT_GATE_STATE=ACTIVE", "CURRENT_GATE_STATE=READY"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(OperationalAlphaStatusError, "resolution options"):
            resolve(root)

    def test_cli_excludes_superseded_progressive_runtime(self) -> None:
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "status", "--json"], cwd=ROOT,
            env={**os.environ, "ZEUS_NO_INTRO": "1"}, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual("OA-07", value["active_gate"])
        self.assertEqual("ACTIVE", value["status"])
        self.assertEqual("EXCLUDED_EVIDENCE_ONLY", value["historical_progressive_runtime"])

    def test_dispatcher_status_uses_convergence_prerequisites_not_pmct(self) -> None:
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "dispatcher", "status"], cwd=ROOT,
            env={**os.environ, "ZEUS_NO_INTRO": "1"}, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual("CONVERGENCE_AUTHORITY", value["model"])
        self.assertTrue(value["dispatch_permitted"])
        self.assertEqual([], value["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
