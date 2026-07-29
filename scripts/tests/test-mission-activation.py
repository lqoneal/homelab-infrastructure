#!/usr/bin/env python3
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.lib.eos.mission_activation import ActivationService, Admission
from scripts.lib.eos.mission_contract import MissionContractError, Resolver


class MissionActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        subprocess.run(["git", "remote", "add", "origin", "ssh://example.invalid/repo"], cwd=self.root, check=True)
        (self.root / "seed").write_text("seed\n")
        subprocess.run(["git", "add", "seed"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "seed"], cwd=self.root, check=True, capture_output=True)
        self.head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()

        self.store = self.root / "engineering/mission-contracts/contracts"
        self.store.mkdir(parents=True)
        self.wop = self.root / "engineering/work-orders/WOP-1/immutable-wop.yaml"
        self.wop.parent.mkdir(parents=True)
        self.wop.write_text(
            yaml.safe_dump({
                "wop_id": "WOP-UUID-1", "status": "Active",
                "work_item_id": "WORK-1",
            })
        )
        self.registry = self.root / "engineering/registry/work-registry.yaml"
        self.registry.parent.mkdir(parents=True)
        self.registry.write_text(yaml.safe_dump({
            "schema_version": 1, "revision": 1, "updated_at": "2026-07-28",
            "serialization": "yaml", "mutation_history": [{
                "revision": 1, "previous_revision": 0, "at": "2026-07-28",
                "actor": "test", "action": "create", "reason": "fixture",
            }],
            "authority_boundary": {"registry": "operational"},
            "entities": {
                "work_items": [{
                    "registry_id": "WORK-1", "management_state": "ready",
                    "scope": "WOP-1", "revision": 1,
                    "updated_at": "2026-07-28", "transition_history": [{
                        "from": None, "to": "ready", "at": "2026-07-28",
                        "actor": "test", "reason": "admit",
                        "authority_reference": "APPROVAL-0",
                    }],
                    "project_id": "P-1",
                }],
                "dependencies": [],
            },
        }, sort_keys=False))
        self.project = self.root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        self.project.parent.mkdir(parents=True)
        self.project.write_text("---\ndocument_id: PROJ-0001\n---\n\n# Project State\n")
        self.approval = self.root / "engineering/approvals/APPROVAL-1.yaml"
        self.approval.parent.mkdir(parents=True)
        self.approval.write_text(yaml.safe_dump({
            "decision": "approved", "mission_id": "M-1",
            "contract_id": "MC-1", "authorizer": "owner",
        }))
        self.contract_path = self.store / "MC-1.yaml"
        self.write_contract()
        self.request_path = self.root / "engineering/mission-contracts/requests/REQ-1.yaml"
        self.request_path.parent.mkdir(parents=True)
        self.write_request()

    def tearDown(self):
        self.temp.cleanup()

    def contract(self):
        return {
            "schema_version": 1, "document_type": "MissionContract",
            "contract_id": "MC-1", "mission_id": "M-1", "registry_id": "WORK-1",
            "wop": {
                "id": "WOP-1",
                "locator": str(self.wop.relative_to(self.root)),
                "digest": hashlib.sha256(self.wop.read_bytes()).hexdigest(),
            },
            "repository": {
                "identity": self.root.name, "root": str(self.root),
                "remote": "ssh://example.invalid/repo", "branch": "main",
                "baseline": self.head,
            },
            "scope": {"included": ["seed"], "excluded": []},
            "permissions": {name: False for name in (
                "inspect", "modify", "generate_evidence", "reconcile_metadata",
                "stage", "commit", "create_branch", "push", "publish",
                "rollback", "reconcile_state", "close_mission",
            )},
            "roles": {
                "human_authorizer": "owner", "repository_operator": "owner",
                "orchestration_agent": "chatgpt", "execution_agent": "codex",
                "implementation_owner": "platform", "document_owner": "docs",
                "review_owner": "owner", "qualification_owner": "independent",
                "publication_owner": "owner", "evidence_reviewer": "owner",
            },
            "approvals": {"activation": "pending"},
            "dirty_tree": {"policy": "CLASSIFIED_DIRTY_ALLOWED"},
            "lifecycle": "candidate",
            "activation": {"actor": None, "record": None, "timestamp": None},
            "interruption": {"behavior": "recover"},
            "closeout": {"requirements": ["validation"]},
        }

    def request(self):
        return {
            "request_id": "REQ-1", "mission_id": "M-1",
            "contract_id": "MC-1", "actor": "owner",
            "expected_lifecycle": "candidate",
            "approval": {
                "locator": str(self.approval.relative_to(self.root)),
                "digest": hashlib.sha256(self.approval.read_bytes()).hexdigest(),
            },
        }

    def write_contract(self, value=None):
        self.contract_path.write_text(yaml.safe_dump(value or self.contract(), sort_keys=True))

    def write_request(self, value=None):
        self.request_path.write_text(yaml.safe_dump(value or self.request(), sort_keys=True))

    def decision(self):
        return Admission(self.root).decide(self.contract_path, self.request())

    def test_complete_admission(self):
        decision = self.decision()
        self.assertEqual(decision["decision"], "ADMIT")
        self.assertEqual(decision["reason_codes"], [])

    def test_deterministic_denial_paths(self):
        cases = {
            "baseline": ("BASELINE_MISMATCH", lambda c, r: c["repository"].update(baseline="0" * 40)),
            "repository": ("REPOSITORY_MISMATCH", lambda c, r: c["repository"].update(root="/wrong")),
            "role": ("SELF_AUTHORIZATION_PROHIBITED", lambda c, r: c["roles"].update(execution_agent="owner")),
            "scope": ("SCOPE_MISMATCH", lambda c, r: self._registry_scope("OTHER")),
            "lifecycle": ("MISSION_LIFECYCLE_INELIGIBLE", lambda c, r: c.update(lifecycle="suspended")),
            "wop": ("WOP_DIGEST_MISMATCH", lambda c, r: c["wop"].update(digest="0" * 64)),
            "approval": ("APPROVAL_INVALID", lambda c, r: r["approval"].update(digest="0" * 64)),
        }
        for name, (code, mutation) in cases.items():
            with self.subTest(name=name):
                contract, request = self.contract(), self.request()
                mutation(contract, request)
                self.write_contract(contract)
                decision = Admission(self.root).decide(self.contract_path, request)
                self.assertEqual(decision["decision"], "DENY")
                self.assertIn(code, decision["reason_codes"])
                self.write_contract()
                self._registry_scope("WOP-1")

    def _registry_scope(self, scope):
        value = yaml.safe_load(self.registry.read_text())
        value["entities"]["work_items"][0]["scope"] = scope
        self.registry.write_text(yaml.safe_dump(value))

    def test_atomic_activation_and_duplicate_replay(self):
        result = ActivationService(self.root).activate(self.request_path)
        self.assertEqual(result["state"], "COMMITTED")
        self.assertEqual(Resolver(self.root).resolve()["resolution"], "AUTHORIZED")
        registry = yaml.safe_load(self.registry.read_text())
        self.assertEqual(registry["entities"]["work_items"][0]["management_state"], "active")
        self.assertIn("MC-1", self.project.read_text())
        replay = ActivationService(self.root).activate(self.request_path)
        self.assertEqual(replay["transaction_id"], result["transaction_id"])

    def test_successor_activation_reconciles_already_active_registry_item(self):
        value = yaml.safe_load(self.registry.read_text())
        value["entities"]["work_items"][0]["management_state"] = "active"
        self.registry.write_text(yaml.safe_dump(value, sort_keys=False))
        result = ActivationService(self.root).activate(self.request_path)
        self.assertEqual(result["state"], "COMMITTED")
        registry = yaml.safe_load(self.registry.read_text())
        item = registry["entities"]["work_items"][0]
        self.assertEqual(item["management_state"], "active")
        self.assertEqual(item["revision"], 1)

    def test_conflicting_active_contract_denies(self):
        other = self.contract()
        other["contract_id"] = "MC-2"
        other["mission_id"] = "M-2"
        other["lifecycle"] = "active"
        other["approvals"]["activation"] = "approved"
        other["activation"] = {"actor": "owner", "record": "A", "timestamp": "T"}
        (self.store / "MC-2.yaml").write_text(yaml.safe_dump(other))
        with self.assertRaisesRegex(MissionContractError, "conflicts"):
            ActivationService(self.root).activate(self.request_path)

    def test_failure_rolls_back_every_repository_record(self):
        before = {
            path: path.read_bytes()
            for path in (self.contract_path, self.registry, self.project)
        }
        with self.assertRaisesRegex(MissionContractError, "injected"):
            ActivationService(self.root, fault_after="reconciliation").activate(self.request_path)
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)
        journal = json.loads(
            (self.root / "engineering/mission-contracts/transactions/TX-REQ-1.json").read_text()
        )
        self.assertEqual(journal["state"], "ROLLED_BACK")

    def test_interrupted_transaction_recovery(self):
        service = ActivationService(self.root)
        journal_path = self.root / "engineering/mission-contracts/transactions/TX-INT.json"
        journal_path.parent.mkdir(parents=True)
        before = self.contract_path.read_bytes()
        self.contract_path.write_text("damaged: true\n")
        journal_path.write_text(json.dumps({
            "state": "REPOSITORY_WRITTEN",
            "before": {
                str(self.contract_path.relative_to(self.root)): before.hex(),
            },
        }))
        result = service.recover("TX-INT")
        self.assertEqual(result["state"], "ROLLED_BACK")
        self.assertEqual(self.contract_path.read_bytes(), before)

    def test_terminal_lifecycle_denies_activation(self):
        value = self.contract()
        value["lifecycle"] = "completed"
        self.write_contract(value)
        with self.assertRaisesRegex(MissionContractError, "terminal"):
            ActivationService(self.root).activate(self.request_path)


if __name__ == "__main__":
    unittest.main()
