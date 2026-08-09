#!/usr/bin/env python3
"""Regression matrix for receipt-backed publication baseline transitions."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp import publication_authority as authority


class AuthorizedPublicationTransitionBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holder = tempfile.TemporaryDirectory(prefix="zeus-transition-baseline-")
        self.runtime = Path(self.holder.name) / "runtime"
        self.publication_id = "PUBLICATION-11111111-1111-5111-8111-111111111111"
        self.mission_id = "MISSION-TRANSITION-01"
        self.wop_id = "WOP-TRANSITION-001"
        self.repository_id = "repo-transition"
        self.root = "/repo"
        self.identity = "git@example.invalid/repo.git"
        self.start = "a" * 40
        self.commit = "b" * 40
        self.runtime.mkdir(parents=True)
        self._write(self.runtime / "runtime-identity.json", {
            "repository": self.root,
            "repository_id": self.repository_id,
            "repository_identity": self.identity,
        })

    def tearDown(self) -> None:
        self.holder.cleanup()

    @staticmethod
    def _write(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def facts(self, *, head: str | None = None, origin: str | None = None,
              eos: str | None = None) -> dict:
        head = head or self.start
        origin = origin or self.start
        eos = eos or self.start
        return {
            "repository_root": self.root,
            "repository_id": self.repository_id,
            "repository_identity": self.identity,
            "branch": "main",
            "detached_head": False,
            "head": head,
            "origin_main": origin,
            "origin_main_ancestor_of_head": True,
            "head_ancestor_of_origin_main": head == origin,
            "ahead_count": 0 if head == origin else 1,
            "behind_count": 0,
            "index_clean": True,
            "eos_available": True,
            "eos_baseline": eos,
            "eos_identity_match": True,
            "eos_manifest_consistent": eos == head,
            "eos_baseline_manifest_consistent": True,
        }

    def transaction(self, state: str) -> dict:
        stop = authority.MILESTONES.index(state) + 1
        completed = list(authority.MILESTONES[:stop])
        record = {
            "schema_version": authority.PUBLICATION_SCHEMA,
            "publication_id": self.publication_id,
            "mission_id": self.mission_id,
            "wop_id": self.wop_id,
            "publication_cohort_id": "COHORT-11111111-1111-5111-8111-111111111111",
            "supersedes_publication_id": None,
            "repository_id": self.repository_id,
            "repository_root": self.root,
            "candidate_digest": "c" * 64,
            "starting_head": self.start,
            "starting_origin": self.start,
            "starting_eos_baseline": self.start,
            "commit_id": self.commit,
            "published_head": self.commit if state in authority.MILESTONES[8:] else None,
            "remote_ref": "refs/heads/main" if state in authority.MILESTONES[8:] else None,
            "prepublication_result": "PASS",
            "current_state": state,
            "completed_milestones": completed,
            "pending_milestones": list(authority.MILESTONES[stop:]),
            "next_authorized_action": authority.NEXT_BY_STATE[state],
            "milestones": {},
        }
        for milestone in completed:
            receipt = {
                "schema_version": authority.PUBLICATION_SCHEMA,
                "receipt_type": "zeus-publication-milestone",
                "milestone": milestone,
                "result": "PASS",
                "publication_id": self.publication_id,
                "mission_id": self.mission_id,
                "wop_id": self.wop_id,
                "publication_cohort_id": record["publication_cohort_id"],
                "supersedes_publication_id": None,
                "repository_id": self.repository_id,
                "input_digest": record["candidate_digest"],
            }
            if milestone == "COMMIT_CREATED":
                receipt.update({"commit_id": self.commit, "parent_id": self.start})
            elif milestone == "REMOTE_PUBLISHED":
                receipt.update({"commit_id": self.commit, "published_head": self.commit,
                                "remote_ref": "refs/heads/main"})
            elif milestone == "EOS_SYNCHRONIZED":
                receipt["eos_baseline"] = self.commit
            receipt["receipt_digest"] = authority._digest(receipt)
            path = authority.receipt_path(self.runtime, self.publication_id, milestone)
            self._write(path, receipt)
            record["milestones"][milestone] = {
                "receipt_path": str(path),
                "receipt_digest": receipt["receipt_digest"],
                "result": "PASS",
            }
        self._write(
            self.runtime / authority.TRANSACTION_DIR / f"{self.publication_id}.json",
            record,
        )
        return record

    def resolve(self, facts: dict) -> dict:
        return authority.resolve_repository_baseline(
            facts,
            runtime_root=self.runtime,
            mission_id=self.mission_id,
            wop_id=self.wop_id,
            publication_id=self.publication_id,
        )

    def test_fully_converged_steady_state_passes(self) -> None:
        value = authority.resolve_repository_baseline(self.facts())
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "STEADY_STATE_CONVERGED")

    def test_arbitrary_head_ahead_without_transaction_fails(self) -> None:
        value = authority.resolve_repository_baseline(
            self.facts(head=self.commit), runtime_root=self.runtime,
        )
        self.assertEqual(value["result"], "FAIL")

    def test_valid_commit_created_transition_passes(self) -> None:
        self.transaction("COMMIT_CREATED")
        value = self.resolve(self.facts(head=self.commit))
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "AUTHORIZED_COMMIT_CREATED_PRE_PUSH")
        self.assertEqual(value["next_authorized_action"], "PUSH_PUBLICATION")

    def test_commit_created_wrong_commit_id_fails(self) -> None:
        self.transaction("COMMIT_CREATED")
        value = self.resolve(self.facts(head="d" * 40))
        self.assertEqual(value["result"], "FAIL")

    def test_commit_created_missing_receipt_fails(self) -> None:
        self.transaction("COMMIT_CREATED")
        authority.receipt_path(self.runtime, self.publication_id, "COMMIT_CREATED").unlink()
        value = self.resolve(self.facts(head=self.commit))
        self.assertEqual(value["result"], "FAIL")

    def test_invalid_transaction_integrity_fails(self) -> None:
        record = self.transaction("COMMIT_CREATED")
        record["next_authorized_action"] = "SYNCHRONIZE_EOS"
        self._write(self.runtime / authority.TRANSACTION_DIR / f"{self.publication_id}.json", record)
        value = self.resolve(self.facts(head=self.commit))
        self.assertEqual(value["result"], "FAIL")

    def test_unrelated_mission_or_wop_fails(self) -> None:
        self.transaction("COMMIT_CREATED")
        for field, value in (("mission_id", "OTHER-MISSION"), ("wop_id", "OTHER-WOP")):
            arguments = {"mission_id": self.mission_id, "wop_id": self.wop_id,
                         "publication_id": self.publication_id}
            arguments[field] = value
            result = authority.resolve_repository_baseline(
                self.facts(head=self.commit), runtime_root=self.runtime, **arguments,
            )
            self.assertEqual(result["result"], "FAIL")

    def test_wrong_repository_identity_fails(self) -> None:
        self.transaction("COMMIT_CREATED")
        facts = self.facts(head=self.commit)
        facts["repository_identity"] = "git@example.invalid/other.git"
        self.assertEqual(self.resolve(facts)["result"], "FAIL")

    def test_remote_published_pre_eos_sync_passes(self) -> None:
        self.transaction("REMOTE_PUBLISHED")
        value = self.resolve(self.facts(head=self.commit, origin=self.commit))
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "AUTHORIZED_REMOTE_PUBLISHED_PRE_EOS_SYNC")

    def test_remote_published_missing_receipt_fails(self) -> None:
        self.transaction("REMOTE_PUBLISHED")
        authority.receipt_path(self.runtime, self.publication_id, "REMOTE_PUBLISHED").unlink()
        self.assertEqual(
            self.resolve(self.facts(head=self.commit, origin=self.commit))["result"],
            "FAIL",
        )

    def test_eos_synchronized_convergence_passes(self) -> None:
        self.transaction("EOS_SYNCHRONIZED")
        value = self.resolve(self.facts(head=self.commit, origin=self.commit, eos=self.commit))
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["classification"], "EOS_SYNCHRONIZED_CONVERGED")

    def test_status_replay_is_read_only(self) -> None:
        self.transaction("COMMIT_CREATED")
        before = {str(path.relative_to(self.runtime)): path.read_bytes()
                  for path in self.runtime.rglob("*") if path.is_file()}
        first = self.resolve(self.facts(head=self.commit))
        second = self.resolve(self.facts(head=self.commit))
        after = {str(path.relative_to(self.runtime)): path.read_bytes()
                 for path in self.runtime.rglob("*") if path.is_file()}
        self.assertEqual(first, second)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
