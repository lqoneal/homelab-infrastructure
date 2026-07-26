import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class DiscoveryTests(unittest.TestCase):
    def test_current_and_future_commands_are_distinguished(self):
        value = pmct.command_surface()
        self.assertTrue(value["zeus status"]["available"])
        self.assertTrue(value["zeus next-action"]["available"])
        self.assertEqual(
            value["zeus next-action"]["classification"], "AVAILABLE"
        )
        self.assertEqual(set(value), set(pmct.matrix()["production_cli_contract"]))


if __name__ == "__main__":
    unittest.main()
