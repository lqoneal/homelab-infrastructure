import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pmct)


class ContractTests(unittest.TestCase):
    def test_locked_contract_has_all_distinct_gates(self):
        value = pmct.matrix()
        self.assertEqual(len(value["gates"]), 30)
        self.assertEqual(
            [item["gate_id"] for item in value["gates"]],
            [f"OA-{number:02d}" for number in range(1, 31)],
        )
        self.assertEqual(len({item["title"] for item in value["gates"]}), 30)

    def test_every_gate_has_required_test_dimensions(self):
        for gate in pmct.matrix()["gates"]:
            for key in (
                "positive_demonstration", "negative_demonstration",
                "idempotency_demonstration", "interruption_demonstration",
                "evidence_requirements", "regression_gates",
            ):
                if key == "regression_gates" and gate["gate_id"] == "OA-01":
                    self.assertEqual(gate[key], [])
                else:
                    self.assertTrue(gate[key], (gate["gate_id"], key))


if __name__ == "__main__":
    unittest.main()
