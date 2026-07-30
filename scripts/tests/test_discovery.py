"""Bridge the repository's hyphenated test inventory into unittest discovery."""

import subprocess
import sys
import unittest
import os
from pathlib import Path


class RepositoryScriptTestInventory(unittest.TestCase):
    def test_complete_hyphenated_inventory(self):
        directory = Path(__file__).resolve().parent
        repository = directory.parents[1]
        failures = []
        for path in sorted(directory.glob("test-*.py")):
            result = subprocess.run(
                [sys.executable, str(path)], text=True, capture_output=True,
                check=False, cwd=repository,
                env={
                    **os.environ,
                    "PYTHONPATH": (
                        f"{repository}:{os.environ.get('PYTHONPATH', '')}"
                    ),
                },
            )
            if result.returncode:
                failures.append(
                    f"{path.name} exit={result.returncode}\n"
                    f"{result.stdout}\n{result.stderr}"
                )
        self.assertEqual([], failures, "\n\n".join(failures))


if __name__ == "__main__":
    unittest.main()
