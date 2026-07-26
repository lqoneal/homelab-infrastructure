import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class CumulativeTests(unittest.TestCase):
    def test_each_gate_regresses_every_earlier_gate(self):
        for sequence, gate in enumerate(pmct.matrix()["gates"], 1):
            self.assertEqual(
                gate["regression_gates"],
                [f"OA-{item:02d}" for item in range(1, sequence)],
            )

    def test_oa30_cannot_ignore_prior_gates(self):
        gate = pmct.matrix()["gates"][-1]
        self.assertEqual(len(gate["regression_gates"]), 29)
        self.assertEqual(gate["prerequisites"], ["OA-29"])


if __name__ == "__main__":
    unittest.main()
