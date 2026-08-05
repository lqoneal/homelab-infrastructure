import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ZeusP1G1AuthoringTests(unittest.TestCase):
    def source(self, directory, objective="Implement one bounded capability"):
        path = directory / "mission.yaml"
        path.write_text(
            "schema_version: '1.0'\noperation: BETA\nmission:\n"
            f"  title: Bounded mission\n  objective: {objective}\n  repository: homelab\n"
            "  scope:\n    include: [one capability]\n    exclude: [publication]\n"
            "  restrictions: [fail closed]\n  acceptance_criteria: [no placeholders]\n"
            "  validation: [focused tests pass]\n  evidence: [traceability]\n",
            encoding="utf-8",
        )
        return path

    def invoke(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/zeus"), *args], capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1"})

    def test_authoring_is_deterministic_and_replayable(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = self.source(directory)
            output = directory / "authored.md"
            first = self.invoke("wop", "template", str(source), "--output", str(output), "--json")
            second = self.invoke("wop", "template", str(source), "--output", str(output), "--json")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            a, b = json.loads(first.stdout), json.loads(second.stdout)
            self.assertEqual(a["wop_id"], b["wop_id"])
            self.assertEqual(a["mission_id"], b["mission_id"])
            self.assertTrue(b["replayed"])
            self.assertEqual(json.loads((output.with_suffix(".md.traceability.json")).read_text())["readiness"], "ADMISSION_READY")

    def test_changed_intent_changes_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            first = json.loads(self.invoke("wop", "template", str(self.source(directory)), "--output", str(directory / "a.md"), "--json").stdout)
            second = json.loads(self.invoke("wop", "template", str(self.source(directory, "Implement a different capability")), "--output", str(directory / "b.md"), "--json").stdout)
            self.assertNotEqual(first["wop_id"], second["wop_id"])
            self.assertNotEqual(first["mission_id"], second["mission_id"])

    def test_operational_alpha_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.source(Path(tmp))
            path.write_text(path.read_text().replace("operation: BETA", "operation: ALPHA"), encoding="utf-8")
            result = self.invoke("wop", "template", str(path), "--output", str(Path(tmp) / "out.md"), "--json")
            self.assertEqual(result.returncode, 78)
            self.assertIn("Operation Beta", result.stderr)


if __name__ == "__main__":
    unittest.main()
