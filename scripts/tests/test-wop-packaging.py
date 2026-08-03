#!/usr/bin/env python3
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.stage1_runtime import Stage1Runtime, Stage1Error, validate_package
from scripts.lib.emp.wop_packaging import PackagingError, extract, package


MARKDOWN = """WOP ID: WOP-PACKAGING-FIXTURE-001
Mission ID: PACKAGING-FIXTURE
Title: Packaging Fixture
Objective: Exercise native WOP packaging.
Scope: validate source; preserve source; prepare bounded evidence
Dependencies: none
Execution Mode: DEVELOPMENT
Governance Authority: Engineering Governance
Repository Identity: /data/engineering/repositories/homelab
Effect Profile: DEVELOPMENT-PACKAGING-NONPRODUCTION
Protected Baselines: OA-v1.0.0, OB-PLAN-v1.0.0
Gates: VALIDATE, QUALIFY, CLOSE
Qualification Requirements: package validation
Completion Requirements: prepare publication candidate
"""


class WopPackagingTests(unittest.TestCase):
    def test_markdown_normalization_and_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source.md"; source.write_text(MARKDOWN)
            package_root, result = package(source, root / "runtime")
            self.assertTrue(result["packaged"])
            metadata, evidence = validate_package(package_root)
            self.assertEqual(metadata["wop_id"], "WOP-PACKAGING-FIXTURE-001")
            self.assertEqual(evidence["result"], "PASS")
            self.assertTrue((package_root / "source-wop.md").is_file())

    def test_docx_input_is_parsed_and_missing_metadata_is_reported(self):
        source = ROOT / "WOP-BETA-07-STRENGTHEN-DEVELOPMENT-MODE-CANONICAL-SPECIFICATION-001.docx"
        package_root, result = package(source, Path(tempfile.mkdtemp()) / "runtime")
        self.assertEqual(result["package_id"], package_root.name)
        self.assertEqual(result["replayed"], False)

    def test_docx_table_metadata_is_normalized(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "table.docx"
            rows = "".join(
                f"<w:tr><w:tc><w:p><w:r><w:t>{key}</w:t></w:r></w:p></w:tc>"
                f"<w:tc><w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc></w:tr>"
                for key, value in [
                    ("WOP ID", "WOP-TABLE-FIXTURE-001"), ("Mission ID", "TABLE-FIXTURE"),
                    ("Title", "Table Fixture"), ("Objective", "Validate table metadata"),
                    ("Scope", "bounded fixture"), ("Dependencies", "none"),
                    ("Execution Mode", "DEVELOPMENT"), ("Governance Authority", "Engineering Governance"),
                    ("Repository Identity", str(ROOT)), ("Effect Profile", "DEVELOPMENT-NONPRODUCTION"),
                    ("Protected Baselines", "OA-v1.0.0, OB-PLAN-v1.0.0"), ("Gates", "VALIDATE"),
                    ("Qualification Requirements", "package validation"), ("Completion Requirements", "close"),
                ]
            )
            xml = f'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>{rows}</w:tbl></w:body></w:document>'''
            with ZipFile(source, "w", ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", xml)
            package_root, _ = package(source, root / "work-orders")
            metadata, _ = validate_package(package_root)
            self.assertEqual(metadata["wop_id"], "WOP-TABLE-FIXTURE-001")

    def test_invalid_document_and_conflicting_metadata_fail_without_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); invalid = root / "invalid.docx"; invalid.write_bytes(b"not a docx")
            destination = root / "runtime"
            with self.assertRaises(PackagingError): package(invalid, destination)
            self.assertFalse(destination.exists())
            conflict = root / "conflict.md"; conflict.write_text(MARKDOWN + "\nWOP ID: WOP-OTHER-002\n")
            with self.assertRaises(PackagingError) as raised:
                package(conflict, destination)
            self.assertIn("conflicting", str(raised.exception))
            self.assertFalse(destination.exists())

    def test_failed_manifest_validation_and_interrupted_promotion_leave_no_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source.md"; source.write_text(MARKDOWN)
            destination = root / "work-orders"
            with patch("scripts.lib.emp.stage1_runtime.validate_package", side_effect=Stage1Error("manifest invalid")):
                with self.assertRaises(Stage1Error):
                    package(source, destination)
            self.assertFalse((destination / "WOP-PACKAGING-FIXTURE-001").exists())
            with patch("scripts.lib.emp.wop_packaging.os.replace", side_effect=OSError("promotion interrupted")):
                with self.assertRaises(OSError):
                    package(source, destination)
            self.assertFalse((destination / "WOP-PACKAGING-FIXTURE-001").exists())

    def test_successful_promotion_and_repeated_packaging_are_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source.md"; source.write_text(MARKDOWN)
            destination = root / "work-orders"
            package_root, first = package(source, destination)
            replay_root, replay = package(source, destination)
            self.assertEqual(package_root, replay_root)
            self.assertTrue(first["promoted"])
            self.assertTrue(replay["replayed"])
            self.assertTrue((package_root / "source-wop.md").is_file())
            self.assertFalse(any(path.name.startswith(".zeus-wop-staging-") for path in destination.parent.iterdir()))

    def test_source_change_requires_supersession(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source.md"; source.write_text(MARKDOWN)
            runtime_root = root / "runtime"; package_root, _ = package(source, runtime_root)
            runtime = Stage1Runtime(ROOT, root / "stage1", operator_resolver=lambda: "loneal")
            runtime.submit_development(package_root)
            source.write_text(MARKDOWN.replace("prepare bounded evidence", "changed bounded evidence"))
            changed, _ = package(source, runtime_root)
            with self.assertRaises(Stage1Error) as raised:
                runtime.submit_development(changed)
            self.assertIn("supersession", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
