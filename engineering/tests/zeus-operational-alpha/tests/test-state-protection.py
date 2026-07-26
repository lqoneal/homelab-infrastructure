import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pmct", ROOT / "lib/pmct.py")
pmct = importlib.util.module_from_spec(spec); spec.loader.exec_module(pmct)


class ProtectionTests(unittest.TestCase):
    def test_authorized_transition_flag_is_not_a_bypass(self):
        with tempfile.TemporaryDirectory(dir=pmct.REPOSITORY) as temporary:
            with patch.dict(os.environ, {"PMCT_RUNTIME_ROOT": temporary}):
                with self.assertRaisesRegex(pmct.PmctError, "no authorized"):
                    pmct.evidence_run(
                        pmct.matrix()["gates"][18], authorized_transition=True
                    )

    def test_runtime_must_remain_scoped(self):
        with patch.dict(os.environ, {"PMCT_RUNTIME_ROOT": "/tmp"}, clear=False):
            with self.assertRaisesRegex(pmct.PmctError, "scoped"):
                pmct.safe_runtime()

    def test_oa01_is_currently_not_ready(self):
        state = pmct.inspect_state()
        checks = pmct.evaluate(pmct.matrix()["gates"][0], state)
        result, _ = pmct.classify(pmct.matrix()["gates"][0], state, checks)
        self.assertEqual(result, "NOT_READY")


if __name__ == "__main__":
    unittest.main()
