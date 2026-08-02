#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.emp import beta_closeout


class BetaCloseoutTests(unittest.TestCase):
    def test_published_receipts_qualify_independently(self):
        root = Path(__file__).resolve().parents[2]
        self.assertEqual(beta_closeout.qualify(root)["result"], "PASS")

    def test_acceptance_is_explicit_and_digest_sealed(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(beta_closeout, "qualify", return_value={"result": "PASS", "qualification_digest": "qualified"}):
            root = Path(directory)
            from datetime import datetime, timezone
            record = beta_closeout.accept(root, operator="operator", rationale="qualified", at=datetime(2026, 8, 2, tzinfo=timezone.utc))
            self.assertEqual(record["acceptance"]["status"], "ACCEPTED")
            self.assertFalse(record["authority"]["derived_from_session"])
            self.assertEqual(beta_closeout.load(root)["record_digest"], record["record_digest"])


if __name__ == "__main__": unittest.main()
