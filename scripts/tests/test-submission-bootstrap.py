#!/usr/bin/env python3
"""Qualification of the unpublished-WOP submission bootstrap envelope."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class SubmissionBootstrapTests(unittest.TestCase):
    def test_direct_source_creates_one_bound_chain_without_publication_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = Stage1Runtime(ROOT, Path(temporary) / "stage1",
                                   operator_resolver=lambda: "loneal").submit_development(FIXTURE)
            chain = result["bootstrap_chain"]
            self.assertEqual(chain["classification"], "UNPUBLISHED_WOP_SUBMISSION_BOOTSTRAP")
            self.assertEqual(result["submission_receipt"]["source_digest"], result["source_digest"])
            self.assertEqual(result["provenance_record"]["transaction_id"], chain["transaction_id"])
            self.assertEqual(result["execution_transaction"]["source_transaction_id"], chain["transaction_id"])
            self.assertIsNone(chain["publication_authority"])
            self.assertTrue(result["submission_receipt"]["receipt_digest"])

    def test_replay_preserves_all_bootstrap_identities(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Stage1Runtime(ROOT, Path(temporary) / "stage1",
                                    operator_resolver=lambda: "loneal")
            first = runtime.submit_development(FIXTURE)
            replay = runtime.submit_development(FIXTURE)
            for key in ("submission_transaction_id", "submission_receipt",
                        "provenance_record", "execution_transaction", "bootstrap_chain"):
                self.assertEqual(replay[key], first[key])
            self.assertTrue(replay["idempotent_replay"])

    def test_tampered_bootstrap_chain_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Stage1Runtime(ROOT, Path(temporary) / "stage1",
                                    operator_resolver=lambda: "loneal")
            result = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(result)
            forged["bootstrap_chain"]["source_digest"] = "0" * 64
            runtime.store.save(forged)
            with self.assertRaises(Stage1Error):
                runtime.store.find(result["instance_id"])


if __name__ == "__main__":
    unittest.main()
