#!/usr/bin/env python3
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.lib.eos.mission_contract import Resolver, digest, transition, validate


class MissionContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        (self.root / "seed").write_text("seed\n")
        subprocess.run(["git", "add", "seed"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "seed"], cwd=self.root, check=True, capture_output=True)
        self.head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.store = self.root / "engineering/mission-contracts/contracts"
        self.store.mkdir(parents=True)
        self.wop = self.root / "wop.yaml"
        self.wop.write_text("wop_id: WOP-1\n")

    def tearDown(self):
        self.temp.cleanup()

    def contract(self, state="active"):
        return {
            "schema_version": 1, "document_type": "MissionContract",
            "contract_id": "MC-1", "mission_id": "M-1", "registry_id": "W-1",
            "wop": {"id": "WOP-1", "locator": "wop.yaml",
                    "digest": hashlib.sha256(self.wop.read_bytes()).hexdigest()},
            "repository": {"identity": self.root.name, "root": str(self.root),
                           "branch": "main", "baseline": self.head},
            "scope": {"paths": ["seed"]},
            "permissions": {x: False for x in (
                "inspect", "modify", "generate_evidence", "reconcile_metadata",
                "stage", "commit", "create_branch", "push", "publish",
                "rollback", "reconcile_state", "close_mission")},
            "roles": {
                "human_authorizer": "owner", "repository_operator": "owner",
                "orchestration_agent": "chatgpt", "execution_agent": "codex",
                "implementation_owner": "platform", "document_owner": "docs",
                "review_owner": "owner", "qualification_owner": "independent",
                "publication_owner": "owner", "evidence_reviewer": "owner",
            },
            "approvals": {"activation": "approved"},
            "dirty_tree": {"policy": "PATH_SCOPED_DIRTY_ALLOWED"},
            "lifecycle": state,
            "activation": {"actor": "owner", "record": "AUTH-1"},
            "interruption": {"behavior": "revalidate"},
            "closeout": {"requirements": ["revoke authority"]},
        }

    def write(self, value, name="MC-1.yaml"):
        path = self.store / name
        path.write_text(yaml.safe_dump(value, sort_keys=True))
        return path

    def test_zero_contracts_denies(self):
        self.assertEqual(Resolver(self.root).resolve()["resolution"], "NO_AUTHORIZED_WORK")

    def test_one_active_contract_authorizes(self):
        self.write(self.contract())
        result = Resolver(self.root).resolve()
        self.assertEqual(result["resolution"], "AUTHORIZED")
        self.assertTrue(result["transactional_authority"])

    def test_multiple_active_contracts_are_ambiguous(self):
        self.write(self.contract(), "one.yaml")
        other = self.contract(); other["contract_id"] = "MC-2"
        self.write(other, "two.yaml")
        self.assertEqual(Resolver(self.root).resolve()["resolution"], "AMBIGUOUS_AUTHORITY")

    def test_baseline_mismatch_denies(self):
        value = self.contract(); value["repository"]["baseline"] = "0" * 40
        self.write(value)
        self.assertEqual(Resolver(self.root).resolve()["resolution"], "BASELINE_MISMATCH")

    def test_authorized_commit_descending_from_activation_baseline(self):
        self.write(self.contract())
        (self.root / "later").write_text("later\n")
        subprocess.run(["git", "add", "later"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "authorized descendant"],
            cwd=self.root, check=True, capture_output=True,
        )
        self.assertEqual(Resolver(self.root).resolve()["resolution"], "AUTHORIZED")

    def test_missing_wop_is_invalid(self):
        value = self.contract(); value["wop"]["locator"] = "missing"
        self.assertIn("wop.locator: unresolved", validate(value, self.root))

    def test_self_approval_role_is_invalid(self):
        value = self.contract()
        value["roles"]["execution_agent"] = value["roles"]["human_authorizer"]
        self.assertIn("roles.execution_agent: cannot self-authorize", validate(value, self.root))

    def test_terminal_contract_cannot_reactivate(self):
        path = self.write(self.contract("completed"))
        with self.assertRaisesRegex(ValueError, "prohibited"):
            transition(path, self.root, "active", "owner", "AUTH", "completed")

    def test_suspend_and_resume(self):
        path = self.write(self.contract())
        transition(path, self.root, "suspended", "owner", "AUTH", "active")
        resumed = transition(path, self.root, "active", "owner", "AUTH-2", "suspended")
        self.assertEqual(resumed["lifecycle"], "active")
        self.assertEqual(resumed["contract_digest"], digest(resumed))


if __name__ == "__main__":
    unittest.main()
