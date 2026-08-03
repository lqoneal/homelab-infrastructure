import json
import os
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZEUS = ROOT / "scripts" / "zeus"
SPEC = importlib.util.spec_from_loader("zeus_cli", SourceFileLoader("zeus_cli", str(ZEUS)))
ZEUS_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ZEUS_MODULE)


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

    def test_protected_baseline_aggregate_and_parity(self):
        reducer = ZEUS_MODULE.protected_baseline_summary
        passing = {
            "OA-v1.0.0": {"result": "PASS", "commit": "oa"},
            "OB-PLAN-v1.0.0": {"result": "PASS", "commit": "ob"},
        }
        self.assertEqual(reducer(passing), "PASS")
        self.assertEqual(reducer({**passing, "other": {"result": "FAIL"}}), "FAIL")
        self.assertEqual(reducer({"one": {"result": "BLOCKED"}, "two": {"result": "PASS"}}), "BLOCKED")
        self.assertEqual(reducer(None), "UNKNOWN")
        self.assertEqual(reducer({}), "UNKNOWN")
        self.assertEqual(reducer({"bad": {"commit": "x"}}), "UNKNOWN")

        human = self.run_zeus("platform", "verify")
        self.assertEqual(human.returncode, 0, human.stderr)
        machine = json.loads(self.run_zeus("platform", "verify", "--json").stdout)
        self.assertIn("Protected Baselines: PASS", human.stdout)
        self.assertEqual(set(machine["checks"]["protected_baselines"]), {"OA-v1.0.0", "OB-PLAN-v1.0.0"})
        verbose = self.run_zeus("platform", "verify", "--verbose")
        self.assertIn("OA-v1.0.0", verbose.stdout)
        self.assertIn("73b22f44dd8ee4d70f0c943ed19e1569022f856a", verbose.stdout)
        self.assertIn("OB-PLAN-v1.0.0", verbose.stdout)
        self.assertIn("b928c1541aa7ba42132f288927924818632f7cd2", verbose.stdout)

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
