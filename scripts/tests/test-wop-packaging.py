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
from scripts.lib.emp.wop_packaging import (
    PackagingError, extract, package, _parse, template_metadata, markdown_template,
    docx_template,
)


MARKDOWN = markdown_template(template_metadata(
    "WOP-PACKAGING-FIXTURE-001", "PACKAGING-FIXTURE", str(ROOT)
))

CANONICAL_BOUNDARY_SUFFIX = """
Approval Authorized Lifecycle State: Active
Authoritative References: PROC-0001@1.11, TPL-0001@1.7, STD-0000, STD-0001, STD-0002, STD-0003, STD-0004
Execution Package Authority Node Id: work-package
Execution Package Authorization Decision Record: ADR-BOUNDARY-FIXTURE
Sections Completion Report Requirement: completion evidence
Sections Deliverables: bounded package
Sections Dependencies And Entry Criteria: clean baseline
Sections Execution Sequence: validate then package
Sections Explicit Authority: no external effects
Sections Governing References: published contract
Sections Mission Classification: development qualification
Sections Prohibited Activities: production changes
Sections Publication And Synchronization: governed publication only
Sections Scope: bounded packaging
Sections Stop Resume And Escalation: stop on mismatch
Sections Success And Acceptance Criteria: package validates
Sections Validation Profile: canonical validators
"""


class WopPackagingTests(unittest.TestCase):
    def test_peer_headings_terminate_sections_but_nested_headings_do_not(self):
        metadata = _parse("""WOP ID: WOP-BOUNDARY-FIXTURE-001
Mission ID: BOUNDARY-FIXTURE
Title: Boundary Fixture
Objective: Verify section boundaries.
## Scope
### In scope
- preserve nested scope content
## Explicit authority
- no authority expansion
Execution Mode: DEVELOPMENT
Governance Authority: Engineering Governance
Repository Identity: /data/engineering/repositories/homelab
Effect Profile: DEVELOPMENT-BOUNDARY-NONPRODUCTION
Protected Baselines: OA-v1.0.0, OB-PLAN-v1.0.0
Gates: VALIDATE
Qualification Requirements: boundary evidence
## Completion Requirements
- completion evidence only
## Transaction Identification
This must not be completion metadata.
""" + CANONICAL_BOUNDARY_SUFFIX)
        self.assertIn("preserve nested scope content", metadata["scope"])
        self.assertNotIn("## Explicit authority", metadata["scope"])
        self.assertEqual(metadata["completion_requirements"], ["completion evidence only"])
        self.assertNotIn("## Transaction Identification", metadata["completion_requirements"])

    def test_canonical_package_preserves_field_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "boundary.md"
            source.write_text("""WOP ID: WOP-BOUNDARY-PACKAGE-001
Mission ID: BOUNDARY-PACKAGE
Title: Boundary Package
Objective: Verify canonical boundary serialization.
Dependencies: none
## Scope
### In scope
- bounded packaging
## Explicit authority
- no external effects
Execution Mode: DEVELOPMENT
Governance Authority: Engineering Governance
Repository Identity: /data/engineering/repositories/homelab
Effect Profile: DEVELOPMENT-BOUNDARY-NONPRODUCTION
Protected Baselines: OA-v1.0.0, OB-PLAN-v1.0.0
Gates: VALIDATE
Qualification Requirements: package evidence
## Completion Requirements
- completion evidence
## Transaction Identification
This section is not a completion requirement.
""" + CANONICAL_BOUNDARY_SUFFIX)
            package_root, result = package(source, root / "work-orders")
            metadata, _ = validate_package(package_root)
            self.assertEqual(metadata["scope"], ["bounded packaging"])
            self.assertEqual(metadata["completion_requirements"], ["completion evidence"])
            self.assertNotIn("Transaction Identification", " ".join(metadata["completion_requirements"]))
            self.assertTrue(result["promoted"])
    def test_markdown_normalization_and_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source.md"; source.write_text(MARKDOWN)
            package_root, result = package(source, root / "runtime")
            self.assertTrue(result["packaged"])
            metadata, evidence = validate_package(package_root)
            self.assertEqual(metadata["wop_id"], "WOP-PACKAGING-FIXTURE-001")
            self.assertEqual(evidence["result"], "PASS")
            self.assertTrue((package_root / "source-wop.md").is_file())

    def test_docx_input_is_parsed_and_canonical_metadata_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = docx_template(
                template_metadata("WOP-DOCX-CANONICAL-001", "DOCX-CANONICAL", str(ROOT)),
                Path(temporary) / "source.docx",
            )
            package_root, result = package(source, Path(temporary) / "runtime")
            self.assertEqual(result["package_id"], package_root.name)
            self.assertEqual(result["replayed"], False)

    def test_docx_table_metadata_is_normalized(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "table.docx"
            rows = "".join(
                f"<w:tr><w:tc><w:p><w:r><w:t>{key}</w:t></w:r></w:p></w:tc>"
                f"<w:tc><w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc></w:tr>"
                for key, value in [
                    (key.replace("_", " ").title(), value)
                    for key, value in template_metadata(
                        "WOP-TABLE-FIXTURE-001", "TABLE-FIXTURE", str(ROOT)
                    ).items()
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
            source.write_text(MARKDOWN.replace("preserve protected baselines", "changed protected baselines"))
            changed, _ = package(source, runtime_root)
            with self.assertRaises(Stage1Error) as raised:
                runtime.submit_development(changed)
            self.assertIn("supersession", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
