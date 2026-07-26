#!/usr/bin/env python3
"""Regression tests for the closed SPEC-0001 relationship vocabulary."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/validate_controlled_documents.py"
SPEC = spec_from_file_location("controlled_document_validator", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

CANONICAL_TYPES = {
    "governed_by", "governs", "implements", "implemented_by",
    "conforms_to", "constrains", "depends_on", "required_by",
    "validated_by", "validates", "authorized_by", "authorizes",
    "produces", "produced_by", "indexes", "indexed_by",
    "supersedes", "superseded_by", "related_to",
}
NONCANONICAL_TYPES = {"uses", "evidenced_by", "published_by", "discovers"}


class RelationshipVocabularyTests(unittest.TestCase):
    def test_validator_accepts_exact_canonical_vocabulary(self) -> None:
        self.assertEqual(VALIDATOR.RELATIONSHIP_TYPES, CANONICAL_TYPES)

    def test_known_noncanonical_variants_are_rejected(self) -> None:
        self.assertTrue(NONCANONICAL_TYPES.isdisjoint(VALIDATOR.RELATIONSHIP_TYPES))

    def test_repository_relationships_are_canonical_and_resolved(self) -> None:
        files = VALIDATOR.repository_markdown_files()
        identities, duplicates = VALIDATOR.document_identity_map(files)
        self.assertFalse(duplicates)
        validation = VALIDATOR.Validation()
        VALIDATOR.validate_repository_relationships(validation, identities)
        self.assertFalse(validation.errors)


if __name__ == "__main__":
    unittest.main()
