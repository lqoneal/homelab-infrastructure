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
            "engineering/operations/zeus-operational-alpha-progress.md",
            "docs/project/PROJ-0001-PROJECT_STATE.md",
            "engineering/work-orders/OA-01-IMPLEMENTATION-001/immutable-wop.yaml",
        ):
            self.copy_source(root, relative)
        return root

    def test_resolves_current_wop_without_reading_historical_progressive_state(self) -> None:
        root = self.fixture()
        value = resolve(root)
        self.assertEqual("RESOLVED", value["outcome"])
        self.assertEqual("OA-01", value["active_gate"])
        self.assertEqual("READY", value["status"])
        self.assertEqual("NOT_STARTED", value["execution_state"])
        self.assertEqual("ELIGIBLE", value["authority_record_creation_eligibility"])
        self.assertEqual("EXCLUDED_EVIDENCE_ONLY", value["historical_progressive_runtime"])

    def test_conflicting_projection_fails_with_operator_options(self) -> None:
        root = self.fixture()
        progress = root / "engineering/operations/zeus-operational-alpha-progress.md"
        progress.write_text(
            progress.read_text(encoding="utf-8").replace(
                "OA-01_STATE=READY", "OA-01_STATE=ACTIVE"
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
        self.assertEqual("OA-01", value["active_gate"])
        self.assertEqual("READY", value["status"])
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
        self.assertFalse(value["dispatch_permitted"])
        self.assertEqual(["CONVERGENCE_PREREQUISITES_INCOMPLETE"], value["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
