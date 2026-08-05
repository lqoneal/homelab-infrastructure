import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.eos.platform_sync_verification import assess


def facts(**overrides):
    value = {"repository_identity": {"result": "PASS"}, "published_baseline": {"result": "PASS"}, "eos": {"result": "PASS"}, "baseline_parity": {"result": "PASS"}, "manifest_consistency": {"result": "PASS"}, "checkpoint": {"result": "HISTORICAL"}}
    value.update(overrides)
    return value


class ZeusPlatformSyncVerificationTests(unittest.TestCase):
    def test_synchronized_published_baseline_reports_pass_and_accurate_next_action(self):
        result = assess(facts())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["checks"]["synchronization"]["result"], "PASS")
        self.assertNotIn("publish", result["next_action"].lower())
        self.assertIn("do not repeat", result["next_action"].lower())

    def test_stale_eos_baseline_fails_closed(self):
        result = assess(facts(baseline_parity={"result": "FAIL", "reason": "EOS commit differs"}))
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(any("EOS commit differs" in defect for defect in result["defects"]))

    def test_mismatched_repository_identity_fails_closed(self):
        self.assertEqual(assess(facts(repository_identity={"result": "FAIL", "reason": "identity mismatch"}))["result"], "FAIL")

    def test_missing_eos_state_fails_closed(self):
        self.assertEqual(assess(facts(eos={"result": "FAIL", "reason": "canonical EOS state unresolved"}))["result"], "FAIL")

    def test_platform_verify_is_read_only_and_reports_live_sync(self):
        before_repo = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout
        eos_state = Path("/data/engineering/eos/state/EOS-STATE.md").read_bytes()
        with tempfile.TemporaryDirectory() as runtime:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/zeus"), "platform", "verify", "--json"], cwd=Path("/tmp"), env={**os.environ, "ZEUS_RUNTIME_ROOT": runtime, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["checks"]["eos"]["result"], "PASS")
        self.assertEqual(value["checks"]["synchronization"]["result"], "PASS")
        self.assertEqual(before_repo, subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(eos_state, Path("/data/engineering/eos/state/EOS-STATE.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
