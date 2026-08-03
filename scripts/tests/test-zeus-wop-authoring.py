import subprocess
import sys
import tempfile
import unittest
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_packaging import extract, docx_template, markdown_template, template_metadata, package
from scripts.lib.emp.wop_schema import REQUIRED_FIELDS, format_description


class WopAuthoringTests(unittest.TestCase):
    def test_lint_uses_canonical_metadata_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = template_metadata("WOP-LINT-001", "LINT-01", str(ROOT))
            source = root / "valid.md"
            source.write_text(markdown_template(metadata), encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "lint", str(source), "--json"]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
            self.assertEqual(json.loads(first.stdout)["lint"]["result"], "PASS")

    def test_lint_invalid_metadata_is_controlled_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "incomplete.md"
            source.write_text("WOP ID: WOP-LINT-BAD-001\nMission ID: LINT-BAD-01\n", encoding="utf-8")
            before = source.read_bytes()
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "lint", str(source), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 78)
            self.assertNotIn("Traceback", result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value["result"], "FAIL")
            self.assertIn("title", value["lint"]["issues"])
            self.assertEqual(source.read_bytes(), before)

    def test_lint_malformed_input_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "malformed.md"
            source.write_bytes(b"\xff\xfe\x00")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "lint", str(source)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 78)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("Issue:", result.stdout)

    def test_lint_human_and_json_share_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            metadata = template_metadata("WOP-LINT-PARITY-001", "LINT-PARITY-01", str(ROOT))
            source = Path(temporary) / "parity.md"
            source.write_text(markdown_template(metadata), encoding="utf-8")
            human = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "lint", str(source)],
                capture_output=True, text=True, check=False,
            )
            machine = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "lint", str(source), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertEqual(machine.returncode, 0, machine.stderr)
            self.assertIn("WOP review: PASS", human.stdout)
            self.assertEqual(json.loads(machine.stdout)["lint"]["result"], "PASS")

    def test_format_is_schema_driven(self):
        value = format_description()
        self.assertEqual(value["required_fields"], list(REQUIRED_FIELDS))
        self.assertEqual(value["execution_modes"], ["DEVELOPMENT"])

    def test_markdown_and_docx_templates_validate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = template_metadata("WOP-AUTHORING-TEST-001", "AUTHORING-TEST-01", str(ROOT))
            markdown = root / "fixture.md"
            markdown.write_text(markdown_template(metadata), encoding="utf-8")
            extracted, _ = extract(markdown)
            self.assertEqual(extracted["wop_id"], metadata["wop_id"])
            docx = docx_template(metadata, root / "fixture.docx")
            extracted, _ = extract(docx)
            self.assertEqual(extracted["mission_id"], metadata["mission_id"])

    def test_validate_failure_is_non_mutating_and_lists_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "incomplete.md"
            source.write_text("WOP ID: WOP-INCOMPLETE-001\nMission ID: INCOMPLETE-01\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "validate", str(source)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 78)
            self.assertIn("Missing fields:", result.stderr)
            self.assertFalse((root := Path(temporary) / "engineering").exists())

    def test_submit_owns_validation_and_does_not_mutate_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "incomplete.md"
            source.write_text("WOP ID: WOP-INCOMPLETE-002\nMission ID: INCOMPLETE-02\n")
            runtime = Path(temporary) / "runtime"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "zeus"), "submit", str(source), "--json"],
                env={**os.environ, "ZEUS_RUNTIME_ROOT": str(runtime)},
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing fields:", result.stderr)
            self.assertIn("Mutation: Repository NONE", result.stderr)
            self.assertFalse(runtime.exists())

    def test_optional_inspection_is_not_a_submission_prerequisite(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "valid.md"
            metadata = template_metadata("WOP-DIRECT-001", "DIRECT-01", str(ROOT))
            source.write_text(markdown_template(metadata), encoding="utf-8")
            inspected = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "inspect", str(source), "--json"],
                capture_output=True, text=True, check=False)
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            metadata["objective"] = "changed after inspection"
            source.write_text(markdown_template(metadata), encoding="utf-8")
            # Submission re-parses the changed source; it never trusts the
            # prior inspection result.
            package_root, _ = package(source, Path(temporary) / "work-orders")
            self.assertIn("changed after inspection", (package_root / "mission.yaml").read_text(encoding="utf-8"))

    def test_init_and_inheritance_are_public_and_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "base.md"
            metadata = template_metadata("WOP-BASE-001", "BASE-01", str(ROOT))
            base.write_text(markdown_template(metadata), encoding="utf-8")
            generated = root / "derived.md"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "template",
                "--from", str(base), "--wop-id", "WOP-DERIVED-001", "--mission-id", "DERIVED-01",
                "--output", str(generated), "--json"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            validation = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "zeus"), "wop", "validate", str(generated), "--json"],
                capture_output=True, text=True, check=False)
            self.assertEqual(validation.returncode, 0, validation.stderr)

    def test_doctor_is_read_only_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "zeus"), "doctor", "--json"],
                env={**dict(__import__("os").environ), "ZEUS_RUNTIME_ROOT": str(Path(temporary) / "runtime")},
                capture_output=True, text=True, check=False)
            self.assertIn('"runtime"', result.stdout)
            self.assertFalse((Path(temporary) / "runtime").exists())


if __name__ == "__main__":
    unittest.main()
