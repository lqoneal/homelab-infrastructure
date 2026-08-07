import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.wop.canonical_package import (  # noqa: E402
    CanonicalPackageError,
    load,
    package_digest,
    validate,
)


REFERENCE = ROOT / "engineering/evidence/operation-beta/OB-CAGF-G01-REFERENCE-WOP-PACKAGE.yaml"


class CanonicalWopPackageTests(unittest.TestCase):
    def test_reference_package_is_non_executable_and_valid(self):
        package = load(REFERENCE)
        result = validate(package)
        self.assertEqual(result["result"], "PASS")
        self.assertFalse(result["executable"])
        self.assertEqual(result["extension_types"], ["CAGF_SOURCE_PROJECTION"])

    def test_digest_is_byte_stable_for_canonical_mapping(self):
        package = load(REFERENCE)
        first = package_digest(package)
        second = package_digest(json.loads(json.dumps(package, sort_keys=True)))
        self.assertEqual(first, second)

    def test_non_cagf_package_does_not_require_cagf_fields(self):
        package = load(REFERENCE)
        package["extensions"] = []
        package["integrity"] = {"package_digest": package_digest(package)}
        result = validate(package)
        self.assertEqual(result["extension_types"], [])

    def test_authority_dependency_fails_closed(self):
        package = load(REFERENCE)
        package["requirements"][0]["technical_dependencies"] = [{"kind": "AUTHORITY_DEPENDENCY", "requirement_id": "CAGF-G01-R02"}]
        with self.assertRaises(CanonicalPackageError):
            validate(package)

    def test_projection_cannot_be_authority(self):
        package = load(REFERENCE)
        package["extensions"][0]["payload"]["projection"]["authority"] = True
        package["integrity"] = {"package_digest": package_digest(package)}
        with self.assertRaises(CanonicalPackageError):
            validate(package)

    def test_unknown_dependency_and_cycle_fail_closed(self):
        package = load(REFERENCE)
        package["requirements"][0]["technical_dependencies"] = [{"kind": "DATA", "requirement_id": "UNKNOWN"}]
        package["integrity"] = {"package_digest": package_digest(package)}
        with self.assertRaises(CanonicalPackageError):
            validate(package)

        package = load(REFERENCE)
        package["requirements"][0]["technical_dependencies"] = [{"kind": "DATA", "requirement_id": "CAGF-G01-R02"}]
        package["requirements"][1]["technical_dependencies"] = [{"kind": "DATA", "requirement_id": "CAGF-G01-R01"}]
        package["integrity"] = {"package_digest": package_digest(package)}
        with self.assertRaises(CanonicalPackageError):
            validate(package)

    def test_tampered_digest_fails_closed(self):
        package = load(REFERENCE)
        package["integrity"]["package_digest"] = "0" * 64
        with self.assertRaises(CanonicalPackageError):
            validate(package)


if __name__ == "__main__":
    unittest.main()
