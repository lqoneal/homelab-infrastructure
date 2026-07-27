#!/usr/bin/env python3
import os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class CliStandardTests(unittest.TestCase):
    def test_help_aliases_from_arbitrary_directory(self):
        with tempfile.TemporaryDirectory() as td:
            env={**os.environ,"ZEUS_TESTING":"1","ZEUS_NO_INTRO":"1"}
            for command, cases in (
                (ROOT/"scripts/zeus", (("--help",),("help",),("help","next-action"))),
                (ROOT/"engineering/tests/zeus-operational-alpha/bin/pmct",
                 (("--help",),("help",),("help","inspect"))),
            ):
                for args in cases:
                    result=subprocess.run([str(command),*args],cwd=td,env=env,
                        text=True,capture_output=True)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertIn("usage:",result.stdout)

    def test_installer_is_idempotent_and_repository_bound(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td); env={**os.environ,"HOME":td,
                "PATH":f"{home/'.local/bin'}:{os.environ['PATH']}"}
            installer=ROOT/"scripts/install-engineering-cli"
            for _ in range(2):
                self.assertEqual(subprocess.run([str(installer),"install"],env=env).returncode,0)
            self.assertEqual(subprocess.run([str(installer),"verify"],env=env).returncode,0)
            self.assertEqual((home/".local/bin/zeus").resolve(),(ROOT/"scripts/zeus").resolve())
            self.assertEqual((home/".local/bin/pmct").resolve(),
                (ROOT/"engineering/tests/zeus-operational-alpha/bin/pmct").resolve())

if __name__ == "__main__":
    unittest.main()
