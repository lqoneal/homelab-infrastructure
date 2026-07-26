import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class EvidenceTests(unittest.TestCase):
    def test_complete_run_has_integrity_manifest_and_no_secret_environment(self):
        with tempfile.TemporaryDirectory(dir=pmct.REPOSITORY) as temporary:
            runtime = Path(temporary) / "runtime"
            with patch.dict(os.environ, {"PMCT_RUNTIME_ROOT": str(runtime), "SECRET_TOKEN": "do-not-copy"}):
                result, directory = pmct.evidence_run(pmct.matrix()["gates"][0])
            self.assertIn(result["result"], pmct.TERMINAL_RESULTS)
            self.assertTrue((directory / "COMPLETE").is_file())
            hashes = (directory / "artifacts.sha256").read_text()
            for line in hashes.splitlines():
                expected, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)
            self.assertNotIn("do-not-copy", "".join(
                path.read_text(errors="ignore") for path in directory.iterdir()
                if path.is_file()
            ))
            manifest = json.loads((directory / "run-manifest.json").read_text())
            self.assertRegex(manifest["evidence_digest"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
