import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_packaging import (  # noqa: E402
    PackagingError,
    adapt_canonical_package,
    is_canonical_source,
)


SOURCE = ROOT / "engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-wop-package.yaml"


class CanonicalStage1IntegrationTests(unittest.TestCase):
    def test_classifier_is_explicit(self):
        self.assertTrue(is_canonical_source(SOURCE))
        with tempfile.TemporaryDirectory() as temporary:
            arbitrary = Path(temporary) / "arbitrary.yaml"
            arbitrary.write_text("schema_version: 1\npackage_identity: {}\n", encoding="utf-8")
            self.assertFalse(is_canonical_source(arbitrary))

    def test_adapter_is_deterministic_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            first, first_info = adapt_canonical_package(SOURCE, Path(left), repository_root=ROOT)
            second, second_info = adapt_canonical_package(SOURCE, Path(right), repository_root=ROOT)
            self.assertEqual(first_info["canonical_package_digest"], second_info["canonical_package_digest"])
            self.assertEqual(first_info["source_digest"], second_info["source_digest"])
            first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
            second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
            self.assertEqual(first_files, second_files)
            for relative in first_files:
                self.assertEqual(hashlib.sha256((first / relative).read_bytes()).hexdigest(), hashlib.sha256((second / relative).read_bytes()).hexdigest(), str(relative))

    def test_adapter_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, first_info = adapt_canonical_package(SOURCE, root, repository_root=ROOT)
            second, second_info = adapt_canonical_package(SOURCE, root, repository_root=ROOT)
            self.assertEqual(first, second)
            self.assertFalse(first_info["replayed"])
            self.assertTrue(second_info["replayed"])
            self.assertEqual(first_info["canonical_package_digest"], second_info["canonical_package_digest"])

    def test_native_readonly_interfaces_accept_canonical_source(self):
        for action in ("validate", "inspect", "verify"):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/zeus"), "wop", action, str(SOURCE), "--json"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('"result": "PASS"', result.stdout)
            self.assertIn('"mutating": false', result.stdout)

    def test_invalid_canonical_source_fails_before_stage1(self):
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.yaml"
            invalid.write_text(SOURCE.read_text(encoding="utf-8").replace("c7a90c8854c170474d21059463bda616b93cd1886ee372a2fa1c4ab4ebc1b85c", "0" * 64), encoding="utf-8")
            with self.assertRaises(PackagingError):
                adapt_canonical_package(invalid, Path(temporary) / "out", repository_root=ROOT)


if __name__ == "__main__":
    unittest.main()
