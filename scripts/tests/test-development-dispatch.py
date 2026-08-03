import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.development_dispatch import select_provider, automatic_executor


ROOT = Path(__file__).resolve().parents[2]


class DevelopmentDispatchTests(unittest.TestCase):
    def test_empty_registry_blocks_without_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "agents.json"
            registry.write_text(json.dumps({"agents": []}), encoding="utf-8")
            decision = select_provider(ROOT, registry_path=registry)
            self.assertEqual(decision["result"], "BLOCKED")
            record = {"wop_id": "WOP-X-001", "instance_id": "I", "package_digest": "pkg",
                      "authority_snapshot": {"authority_snapshot_digest": "auth"}}
            result = automatic_executor(ROOT, registry_path=registry)(record)
            self.assertNotIn("dispatch_receipt", result)

    def test_qualified_selection_is_deterministic_and_provider_neutral(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "agents.json"
            registry.write_text(json.dumps({"agents": [
                {"agent_id": "provider-b", "active": True, "qualification_status": "QUALIFIED", "repository_access_scope": [str(ROOT)]},
                {"agent_id": "provider-a", "active": True, "qualification_status": "QUALIFIED", "repository_access_scope": [str(ROOT)]},
                {"agent_id": "revoked", "active": False, "qualification_status": "QUALIFIED", "repository_access_scope": [str(ROOT)]},
            ]}), encoding="utf-8")
            result = automatic_executor(ROOT, registry_path=registry)({
                "wop_id": "WOP-X-001", "instance_id": "I", "package_digest": "pkg",
                "authority_snapshot": {"authority_snapshot_digest": "auth"},
            })
            self.assertEqual(result["dispatch_receipt"]["agent_id"], "provider-a")
            self.assertTrue(result["dispatch_receipt"]["assignment_id"].startswith("ZEUS-DISPATCH-"))
            self.assertEqual(result["dispatch_receipt"]["authority_snapshot_digest"], "auth")
            self.assertIn("provider_selection", result["receipts"])

    def test_dispatch_requires_frozen_authority_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "agents.json"
            registry.write_text(json.dumps({"agents": [{
                "agent_id": "provider-a", "active": True,
                "qualification_status": "QUALIFIED", "repository_access_scope": [str(ROOT)]
            }], "registry_digest": "registry"}), encoding="utf-8")
            result = automatic_executor(ROOT, registry_path=registry)({
                "wop_id": "WOP-X-001", "instance_id": "I", "package_digest": "pkg"
            })
            self.assertNotIn("dispatch_receipt", result)
            self.assertEqual(result["blocker"], "AUTHORITY_CHAIN_INTEGRITY_FAILURE")


if __name__ == "__main__":
    unittest.main()
