#!/usr/bin/env python3
"""Regression suite for the canonical Engineering Work Initiation bundle."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.work_initiation.authorization_bundle import (
    AuthorizationBundleError,
    DOCUMENT_TYPE,
    LEGACY_ENV,
    resolve,
)


class AuthorizationBundleContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for name in ("admission.json", "graph.yaml", "state.yaml", "receipt.yaml"):
            (self.root / name).write_text("{}\n", encoding="utf-8")
        (self.root / "wop.yaml").write_text(
            yaml.safe_dump({"wop_id": "WOP-12345678-1234-4234-9234-123456789abc"}),
            encoding="utf-8",
        )
        self.value = {
            "schema_version": 1,
            "document_type": DOCUMENT_TYPE,
            "admission_record": "admission.json",
            "authority_graph": "graph.yaml",
            "wop": "wop.yaml",
            "state": "state.yaml",
            "receipt": "receipt.yaml",
            "expected_authority": "work-package",
        }
        self.bundle = self.root / "bundle.json"
        self._write(self.value)

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, value):
        self.bundle.write_text(json.dumps(value), encoding="utf-8")

    def test_valid_authorization_bundle_is_normalized(self):
        result = resolve(self.bundle, {})
        self.assertEqual(result.source, "canonical_bundle")
        self.assertEqual(
            result.values["wop_id"], "WOP-12345678-1234-4234-9234-123456789abc"
        )
        for field in ("admission_record", "authority_graph", "wop", "state", "receipt"):
            self.assertTrue(Path(result.values[field]).is_absolute())

    def test_incomplete_bundle_fails_closed(self):
        del self.value["receipt"]
        self._write(self.value)
        with self.assertRaisesRegex(AuthorizationBundleError, "incomplete"):
            resolve(self.bundle, {})

    def test_conflicting_bundle_and_legacy_input_fails_closed(self):
        environment = {LEGACY_ENV["wop"]: str(self.root / "state.yaml")}
        with self.assertRaisesRegex(AuthorizationBundleError, "conflicts"):
            resolve(self.bundle, environment)

    def test_corrupted_bundle_fails_closed(self):
        self.bundle.write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(AuthorizationBundleError, "corrupted"):
            resolve(self.bundle, {})

    def test_legacy_compatibility_path_resolves_complete_inputs(self):
        environment = {
            LEGACY_ENV[field]: str(self.root / filename)
            for field, filename in {
                "admission_record": "admission.json",
                "authority_graph": "graph.yaml",
                "wop": "wop.yaml",
                "state": "state.yaml",
                "receipt": "receipt.yaml",
            }.items()
        }
        result = resolve(None, environment)
        self.assertEqual(result.source, "legacy_environment")
        self.assertEqual(
            result.values["wop_id"], "WOP-12345678-1234-4234-9234-123456789abc"
        )

    def test_unavailable_locator_fails_closed(self):
        self.value["receipt"] = "absent.yaml"
        self._write(self.value)
        with self.assertRaisesRegex(AuthorizationBundleError, "unavailable"):
            resolve(self.bundle, {})

    def test_unknown_field_and_invalid_wop_identity_fail_closed(self):
        self.value["unexpected"] = "value"
        self._write(self.value)
        with self.assertRaisesRegex(AuthorizationBundleError, "unknown fields"):
            resolve(self.bundle, {})
        del self.value["unexpected"]
        (self.root / "wop.yaml").write_text("wop_id: package-label\n", encoding="utf-8")
        self._write(self.value)
        with self.assertRaisesRegex(AuthorizationBundleError, "identity is invalid"):
            resolve(self.bundle, {})


if __name__ == "__main__":
    unittest.main()
