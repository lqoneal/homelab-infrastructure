"""Bridge the locked hyphenated PMCT inventory into unittest discovery."""

import subprocess
import unittest
from pathlib import Path


class OperationalAlphaTestInventory(unittest.TestCase):
    def test_complete_hyphenated_inventory(self):
        script = Path(__file__).resolve().parent / "run-tests.sh"
        result = subprocess.run(
            [str(script)], text=True, capture_output=True, check=False,
        )
        self.assertEqual(
            0, result.returncode, f"{result.stdout}\n{result.stderr}"
        )


if __name__ == "__main__":
    unittest.main()
