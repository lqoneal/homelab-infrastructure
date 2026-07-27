#!/usr/bin/env python3
import copy
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.emp import agent_qualification as aq


class AgentQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.binding = {
            "repository_identity": str(self.root),
            "repository_head": "a" * 40,
            "published_baseline": "a" * 40,
            "authority_publication": "AUTHORITY-PUBLICATION-test",
            "pmct_run": "PMCT-20260727T000000Z-000000000000",
            "oa01_pmct_run": "PMCT-20260727T000001Z-000000000000",
        }
        self.agent = {
            "agent_id": "zeus-local-test-01",
            "agent_type": "local-authenticated",
            "host_identity": "test-host",
            "service_identity": "test",
            "supported_mission_classes": ["engineering"],
            "supported_tools": ["zeus-cli"],
            "repository_access_scope": [str(self.root)],
            "execution_constraints": ["controlled-wop-only"],
            "qualification_status": "QUALIFIED",
            "qualification_evidence": [],
            "active": True,
            "last_validated_at": None,
            "trust_binding": "SHA256:test",
            "eens_identity": "test",
            "evidence_signing_identity": "test",
            "interruption_resume_capable": True,
            "concurrency_limit": 1,
            "_qualification_inputs": {
                "binding": self.binding,
                "requirements": {
                    "agent_identity": "PASS",
                    "repository_access": "PASS",
                },
            },
        }

    def tearDown(self):
        self.temporary.cleanup()

    def qualify(self):
        with patch.object(aq, "candidate", return_value=copy.deepcopy(self.agent)), \
             patch.object(aq, "_binding", return_value=self.binding):
            return aq.qualify(
                self.root,
                at=datetime(2026, 7, 27, 18, 0, tzinfo=timezone.utc),
            )

    def test_qualification_is_integrity_protected_and_idempotent(self):
        first, replay = self.qualify()
        second, replay2 = self.qualify()
        self.assertFalse(replay)
        self.assertTrue(replay2)
        self.assertEqual(first["qualification_digest"], second["qualification_digest"])
        with patch.object(aq, "_binding", return_value=self.binding):
            self.assertEqual(aq.registry(self.root)["qualified_agents"], [
                "zeus-local-test-01"
            ])

    def test_failed_requirement_records_nothing(self):
        failed = copy.deepcopy(self.agent)
        failed["_qualification_inputs"]["requirements"]["repository_access"] = "FAIL"
        with patch.object(aq, "candidate", return_value=failed):
            with self.assertRaisesRegex(aq.AgentQualificationError, "repository_access"):
                aq.qualify(self.root)
        self.assertEqual(list((self.root / ".zeus").rglob("*.json")), [])

    def test_revocation_preserves_history_and_removes_eligibility(self):
        qualified, _ = self.qualify()
        with patch.object(aq, "_binding", return_value=self.binding):
            revoked, replay = aq.revoke(
                self.root, "zeus-local-test-01",
                at=datetime(2026, 7, 27, 18, 1, tzinfo=timezone.utc),
            )
            view = aq.registry(self.root)
        self.assertFalse(replay)
        self.assertEqual(revoked["predecessor_qualification_digest"],
                         qualified["qualification_digest"])
        self.assertEqual(view["qualified_agents"], [])
        self.assertEqual(view["revoked_agents"], ["zeus-local-test-01"])
        self.assertEqual(len(list((self.root / ".zeus").rglob("*.json"))), 2)

    def test_registry_order_is_deterministic(self):
        one, _ = self.qualify()
        two = copy.deepcopy(one)
        two["agent"]["agent_id"] = "aaa-agent"
        two.pop("qualification_digest")
        two["qualification_digest"] = aq.digest(two)
        path = self.root / ".zeus/runtime/agents/qualifications/aaa.json"
        aq._atomic(path, two)
        path.with_suffix(".json.sha256").write_text(
            f"{aq._sha(path)}  {path.name}\n"
        )
        with patch.object(aq, "_binding", return_value=self.binding):
            self.assertEqual(aq.registry(self.root)["qualified_agents"],
                             ["aaa-agent", "zeus-local-test-01"])


if __name__ == "__main__":
    unittest.main()
