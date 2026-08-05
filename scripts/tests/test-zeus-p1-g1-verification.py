import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_verification import compare_replay, unresolved_tokens, verify_replay


class ZeusP1G1VerificationTests(unittest.TestCase):
    def test_replay_ignores_filesystem_locations_and_preserves_identity(self):
        first = {"path": "/one/a.md", "repository": {"canonical_repository_identity": "homelab"}, "wop_id": "WOP-BETA-1", "mission_id": "MISSION-BETA-1", "source": {"path": "/one/mission.yaml", "digest": "a"}, "template": {"path": "/repo/template.md", "digest": "b"}, "context": {"digest": "c"}, "output_digest": "d", "readiness": "ADMISSION_READY", "blockers": [], "next_action": "zeus submit /one/a.md"}
        second = json.loads(json.dumps(first).replace("/one", "/two").replace("/repo", "/other-repo"))
        result = compare_replay(first, second)
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(all(result["preserved_fields"].values()))

    def test_token_aware_placeholder_check_ignores_prose(self):
        self.assertEqual(unresolved_tokens("This prose mentions placeholders without defining one."), [])
        self.assertEqual(unresolved_tokens("{{WOP_ID}} <PLACEHOLDER> @@MISSION_ID@@"), ["{{WOP_ID}}", "<PLACEHOLDER>", "@@MISSION_ID@@"])

    def test_replay_passes_for_equivalent_outputs_in_different_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_dir, second_dir = root / "first", root / "second"
            first_dir.mkdir(); second_dir.mkdir()
            output = "# WOP\nThis prose mentions placeholders.\n"
            trace = {"result": "PASS", "readiness": "ADMISSION_READY", "wop_id": "WOP-BETA-1", "mission_id": "MISSION-BETA-1", "repository": {"canonical_repository_identity": "homelab"}, "source": {"path": "SOURCE", "digest": "a", "normalized_digest": "n"}, "template": {"path": "TEMPLATE", "digest": "b"}, "context": {"digest": "c"}, "output_digest": __import__("hashlib").sha256(output.encode()).hexdigest(), "blockers": [], "next_action": "zeus submit OUTPUT"}
            for directory in (first_dir, second_dir):
                path = directory / "wop.md"
                path.write_text(output, encoding="utf-8")
                value = dict(trace)
                value["source"] = dict(trace["source"], path=str(directory / "mission.yaml"))
                value["template"] = dict(trace["template"], path=str(directory / "template.md"))
                value["next_action"] = f"zeus submit {path}"
                path.with_suffix(".md.traceability.json").write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(verify_replay(first_dir / "wop.md", second_dir / "wop.md")["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
