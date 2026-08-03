import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]

from scripts.lib.emp.runtime_adoption import RuntimeAdoptionError, adopt
from scripts.lib.emp.runtime_paths import runtime_identity


class RuntimeAdoptionTests(unittest.TestCase):
    def fixture(self, root: Path, repository_root: Path = ROOT) -> Path:
        (root / "evidence").mkdir(parents=True)
        (root / "stage1" / "eens").mkdir(parents=True)
        (root / "stage1" / "missions").mkdir(parents=True)
        (root / "orchestration-state.json").write_text('{"schema_version": 1, "missions": {}}')
        (root / "evidence" / "bootstrap-evidence.json").write_text(json.dumps({
            "schema_version": 1, "repository_root": str(repository_root.resolve()),
            "evidence_type": "zeus-operational-bootstrap", "operational_readiness": "READY",
        }))
        return root

    def test_dry_run_and_idempotent_adoption(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            source = self.fixture(home / "legacy")
            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                preview = adopt(ROOT, source=source, dry_run=True)
                self.assertEqual(preview["result"], "PASS")
                self.assertFalse((home / ".local/state/zeus-runtime").exists())
                first = adopt(ROOT, source=source)
                second = adopt(ROOT, source=source)
            self.assertEqual(first["action"], "MIGRATED")
            self.assertEqual(second["action"], "ALREADY_ADOPTED")
            self.assertEqual(first["adoption_id"], second["adoption_id"])
            self.assertTrue((home / ".local/state/zeus-runtime" / runtime_identity(ROOT)["repository_id"] / "runtime-binding.yaml").is_file())

    def test_foreign_repository_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            source = self.fixture(home / "legacy", Path("/foreign/repository"))
            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                with self.assertRaises(RuntimeAdoptionError):
                    adopt(ROOT, source=source)
            self.assertFalse((home / ".local/state/zeus-runtime").exists())

    def test_cli_runs_from_repository_root_without_pythonpath(self):
        result = subprocess.run(["python3", "scripts/zeus", "runtime", "adopt", "--dry-run", "--source", "/definitely/missing"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("legacy runtime source", result.stderr)


if __name__ == "__main__":
    unittest.main()
