import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.repository_identity import RepositoryIdentityError, resolve, resolve_declared
from scripts.lib.emp.wop_packaging import package, template_metadata, markdown_template
from scripts.lib.emp.wop_validation import validate_source


ROOT = Path(__file__).resolve().parents[2]


class RepositoryIdentityTests(unittest.TestCase):
    def test_runtime_identity_values_and_aliases(self):
        identity = resolve(ROOT)
        self.assertEqual(identity["repository_id"], "homelab-6bd83f9079d6fc57")
        self.assertEqual(identity["repository_fingerprint"], "6bd83f9079d6fc5780ca2cb9a93060778a899cd97e82ef3d708f91a42dbda02d")
        for value in ("homelab", identity["repository_id"], identity["repository_fingerprint"], identity["repository_remote_identity"], str(ROOT)):
            self.assertEqual(resolve_declared(value, ROOT)["canonical_repository_identity"], str(ROOT))

    def test_unknown_alias_and_path_only_foreign_repo_fail(self):
        with self.assertRaises(RepositoryIdentityError):
            resolve_declared("other-repository", ROOT)
        with self.assertRaises(RepositoryIdentityError):
            resolve_declared("/tmp/homelab", ROOT)

    def test_validation_and_packaging_canonicalize_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "WOP-IDENTITY-001.md"
            metadata = template_metadata("WOP-IDENTITY-001", "IDENTITY-01", "homelab")
            source.write_text(markdown_template(metadata), encoding="utf-8")
            result = validate_source(source, repository_root=ROOT)
            self.assertTrue(result.valid)
            self.assertEqual(result.metadata["repository_identity"], str(ROOT))
            destination, details = package(source, Path(temporary) / "packages", repository_root=ROOT)
            self.assertFalse(details["replayed"])
            manifest = (destination / "manifests/immutable-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn(f"repository_identity: {ROOT}", manifest)

    def test_staged_source_digest_unchanged(self):
        source = Path("/data/engineering/staging/WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001-v2.1.md")
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), "6567d9eaac47bea91b0346731cc3bac91566ccfa52cb4e2e6d86f3da61ef5334")


if __name__ == "__main__":
    unittest.main()
