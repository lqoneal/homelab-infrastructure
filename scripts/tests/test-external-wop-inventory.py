#!/usr/bin/env python3
"""External WOP inventory classification tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.lib.authority_pipeline.external_wop_inventory import inventory


class ExternalInventoryTests(unittest.TestCase):
    def test_classifies_duplicate_divergent_and_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external"
            canonical = root / "canonical"
            repository = root / "repository"
            external.mkdir()
            canonical.mkdir()
            (repository / "scripts").mkdir(parents=True)
            (repository / "engineering").mkdir()
            (external / "same").write_text("equal\n")
            (canonical / "other").write_text("equal\n")
            (external / "name").write_text("external\n")
            (canonical / "name").write_text("canonical\n")
            (external / "unique").write_text("unique\n")
            value = inventory(external, canonical, repository)
            classes = {
                item["path"]: item["classification"] for item in value["comparison"]
            }
            self.assertEqual(classes["same"], "DUPLICATE_CONTENT")
            self.assertEqual(classes["name"], "DIVERGENT_SAME_NAME")
            self.assertEqual(
                classes["unique"], "EXTERNAL_UNIQUE_REQUIRES_SEMANTIC_REVIEW"
            )


if __name__ == "__main__":
    unittest.main()
