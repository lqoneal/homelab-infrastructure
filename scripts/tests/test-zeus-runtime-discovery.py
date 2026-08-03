import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp.runtime_paths import RuntimeDiscoveryError, initialize_runtime, resolve_runtime


class RuntimeDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.repository = Path(__file__).resolve().parents[2]
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)

    def test_user_default_is_repository_bound_and_deterministic(self):
        with patch.dict(os.environ, {"HOME": self.home.name}, clear=False):
            first = resolve_runtime(self.repository)
            second = resolve_runtime(self.repository)
        self.assertEqual(first["root"], second["root"])
        self.assertEqual(first["source"], "user-state-default")
        self.assertIn(first["identity"]["repository_id"], str(first["root"]))

    def test_environment_precedes_user_default_and_initializes_idempotently(self):
        target = Path(self.home.name) / "runtime"
        with patch.dict(os.environ, {"HOME": self.home.name, "ZEUS_RUNTIME_ROOT": str(target)}, clear=False):
            first = initialize_runtime(self.repository)
            marker_before = (target / "runtime-identity.json").read_text()
            second = initialize_runtime(self.repository)
        self.assertEqual(first["source"], "environment")
        self.assertEqual(second["root"], target.resolve())
        self.assertEqual(marker_before, (target / "runtime-identity.json").read_text())
        self.assertTrue((target / "stage1").is_dir())

    def test_explicit_override_precedes_environment(self):
        explicit = Path(self.home.name) / "explicit"
        env = Path(self.home.name) / "environment"
        with patch.dict(os.environ, {"ZEUS_RUNTIME_ROOT": str(env)}, clear=False):
            result = resolve_runtime(self.repository, explicit=explicit)
        self.assertEqual(result["source"], "command-line")
        self.assertEqual(result["root"], explicit.resolve())

    def test_repository_configuration_is_supported(self):
        configured_repository = Path(self.home.name) / "repo"
        (configured_repository / ".zeus").mkdir(parents=True)
        target = Path(self.home.name) / "configured"
        (configured_repository / ".zeus" / "config.yaml").write_text(
            "runtime:\n  root: ~/configured\n"
        )
        with patch.dict(os.environ, {"HOME": self.home.name}, clear=False):
            result = resolve_runtime(configured_repository)
        self.assertEqual(result["source"], "repository-config")
        self.assertEqual(result["root"], target.resolve())

    def test_foreign_binding_is_rejected(self):
        target = Path(self.home.name) / "runtime"
        target.mkdir()
        (target / "runtime-identity.json").write_text(json.dumps({"repository_fingerprint": "foreign"}))
        with patch.dict(os.environ, {"ZEUS_RUNTIME_ROOT": str(target), "HOME": self.home.name}, clear=False):
            with self.assertRaises(RuntimeDiscoveryError):
                resolve_runtime(self.repository)

    def test_repository_local_runtime_is_rejected(self):
        with self.assertRaises(RuntimeDiscoveryError):
            resolve_runtime(self.repository, explicit=self.repository / ".zeus" / "runtime")

    def test_read_only_resolution_does_not_create_runtime(self):
        target = Path(self.home.name) / "not-created"
        with patch.dict(os.environ, {"ZEUS_RUNTIME_ROOT": str(target)}, clear=False):
            result = resolve_runtime(self.repository)
        self.assertEqual(result["root"], target.resolve())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
