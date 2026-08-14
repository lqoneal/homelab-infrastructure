import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.emp import managed_provider

class ManagedProviderTests(unittest.TestCase):
    def test_legitimate_zeus_receipt_is_controller_mutation_not_provider_change(self):
        receipt = "engineering/convergence/engineering-system-convergence/receipts/qualification/tx.json"
        value = managed_provider.attribute_mutations(
            provider_diff=["scripts/tests/example.py"],
            controller_diff=[receipt],
            provider_authorized_scope=["scripts/tests"],
        )
        self.assertEqual("PASS", value["scope_verification"])
        self.assertEqual([receipt], value["zeus_controller_diff"])
        self.assertEqual([], value["out_of_scope_provider_changes"])
        self.assertEqual("ZEUS_CONTROLLER_MUTATION", value["zeus_receipt_attribution"])
        self.assertEqual("YES", value["zeus_controller_mutation"])

    def test_provider_receipt_forgery_fails_even_if_path_is_listed(self):
        receipt = "engineering/convergence/engineering-system-convergence/receipts/qualification/tx.json"
        value = managed_provider.attribute_mutations(
            provider_diff=[receipt],
            provider_authorized_scope=["engineering/convergence/engineering-system-convergence/receipts/qualification"],
        )
        self.assertEqual("FAIL", value["provider_scope_compliance"])
        self.assertEqual([receipt], value["out_of_scope_provider_changes"])
        self.assertEqual("FAIL", value["terminal_reconciliation"])

    def test_controller_reconciliation_preserves_provider_scope_and_is_actor_aware(self):
        receipt = "engineering/convergence/engineering-system-convergence/receipts/qualification/tx.json"
        value = managed_provider.reconcile_controller_mutations(
            {"post_execution_diff": ["tmp/provider.txt"], "authorized_scope": ["tmp"]},
            [receipt],
        )
        self.assertEqual("PASS", value["scope_verification"])
        self.assertEqual(["tmp/provider.txt"], value["provider_post_execution_diff"])
        self.assertEqual([receipt], value["zeus_controller_diff"])

    def test_nonzero_provider_fails_closed_and_captures_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / ".git").mkdir()
            with patch.object(managed_provider.subprocess, "run", return_value=type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()), \
                 patch.object(managed_provider.subprocess, "Popen") as popen:
                process = popen.return_value; process.communicate.return_value = ("out", "err"); process.returncode = 7; process.pid = 12
                value = managed_provider.execute(repository=root, prompt="test", authorized_paths=[], codex_bin="codex")
            self.assertEqual(value["result"], "FAIL"); self.assertEqual(value["provider_exit_status"], 7)
            self.assertIsNone(value["provider_session_id"]); self.assertTrue(value["zeus_execution_id"])

    def test_out_of_scope_change_blocks_advancement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / ".git").mkdir()
            snapshots = iter(["", "?? outside.txt\n"])
            with patch.object(managed_provider.subprocess, "run", side_effect=[type("R", (), {"returncode": 0, "stdout": next(snapshots), "stderr": ""})(), type("R", (), {"returncode": 0, "stdout": next(snapshots), "stderr": ""})()]), \
                 patch.object(managed_provider.subprocess, "Popen") as popen:
                process = popen.return_value; process.communicate.return_value = ("", ""); process.returncode = 0; process.pid = 12
                value = managed_provider.execute(repository=root, prompt="test", authorized_paths=["tmp"])
            self.assertEqual(value["result"], "FAIL"); self.assertEqual(value["scope_verification"], "FAIL")

if __name__ == "__main__": unittest.main()
