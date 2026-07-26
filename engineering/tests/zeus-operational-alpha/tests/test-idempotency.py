import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class IdempotencyTests(unittest.TestCase):
    def test_discovery_is_repeatable(self):
        self.assertEqual(pmct.command_surface(), pmct.command_surface())

    def test_duplicate_create_only_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "record.json"
            pmct.write_json(path, {"value": 1})
            with self.assertRaises(FileExistsError):
                pmct.write_json(path, {"value": 1})


if __name__ == "__main__":
    unittest.main()
