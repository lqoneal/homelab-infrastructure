import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts" / "zeus"


class ZeusCliConsistencyTests(unittest.TestCase):
    def run_zeus(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(ZEUS), *args], cwd=cwd or ROOT,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                              capture_output=True, text=True, check=False)

    def test_platform_verify_is_distinct_and_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp) / "runtime"
            before = runtime.exists()
            result = self.run_zeus("platform", "verify", "--json", cwd=Path("/tmp"))
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertTrue(value["read_only"])
            self.assertEqual(value["result"], "PASS")
            self.assertFalse(runtime.exists() != before)

    def test_doctor_ready_for_review_on_recovery_branch(self):
        result = self.run_zeus("doctor", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"], "READY_FOR_REVIEW")

    def test_gate_and_mission_verify_remain_parseable(self):
        self.assertEqual(self.run_zeus("verify", "GATE-1", "--help").returncode, 0)
        result = self.run_zeus("mission", "verify", "CAGF-01", "--json")
        self.assertNotEqual(result.returncode, 2)

    def test_location_independent_platform_command(self):
        for location in ("/data", "/home/loneal", "/tmp"):
            result = self.run_zeus("platform", "verify", "--json", cwd=Path(location))
            self.assertEqual(result.returncode, 0, (location, result.stderr))


if __name__ == "__main__":
    unittest.main()
