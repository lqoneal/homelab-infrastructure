#!/usr/bin/env python3
"""Regression coverage for publication supersession/current cardinality."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp import publication_authority as authority  # noqa: E402
from scripts.lib.emp import publication_transaction as controller  # noqa: E402
from scripts.lib.emp.production_execution import digest  # noqa: E402


MISSION = "MISSION-SUPERSESSION-TEST"
WOP = "WOP-SUPERSESSION-TEST"
REPOSITORY = "repository-test"


def record(publication_id: str, state: str = "CANDIDATE_ISOLATED", *,
           supersedes: str | None = None, mission: str = MISSION,
           wop: str = WOP, repository: str = REPOSITORY,
           created_at: str = "2099-01-01T00:00:00Z") -> dict[str, object]:
    return {
        "publication_id": publication_id, "mission_id": mission, "wop_id": wop,
        "repository_id": repository, "current_state": state,
        "supersedes_publication_id": supersedes, "created_at": created_at,
        "updated_at": created_at,
    }


class PublicationLineageResolverTests(unittest.TestCase):
    def resolve(self, values: list[dict[str, object]]) -> dict[str, object]:
        return authority.resolve_transaction_lineage(values, mission_id=MISSION)

    def test_one_publication_is_the_only_current_transaction(self) -> None:
        value = self.resolve([record("PUBLICATION-A")])
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["current_ids"], ["PUBLICATION-A"])

    def test_qualified_terminal_plus_reprepare_resolves_fresh_only(self) -> None:
        values = [record("PUBLICATION-A", "PUBLICATION_QUALIFIED"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertEqual(value["current_ids"], ["PUBLICATION-B"])
        self.assertEqual(value["dispositions"]["PUBLICATION-A"], "HISTORICAL_QUALIFIED")

    def test_nonterminal_predecessor_plus_replacement_resolves_fresh_only(self) -> None:
        values = [record("PUBLICATION-A"), record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertEqual(value["current_ids"], ["PUBLICATION-B"])
        self.assertEqual(value["dispositions"]["PUBLICATION-A"], "SUPERSEDED")

    def test_explicit_multigeneration_lineage_resolves_only_the_tip(self) -> None:
        values = [record("PUBLICATION-A"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A"),
                  record("PUBLICATION-C", supersedes="PUBLICATION-B")]
        value = self.resolve(values)
        self.assertEqual(value["current_ids"], ["PUBLICATION-C"])
        self.assertEqual(value["dispositions"]["PUBLICATION-A"], "SUPERSEDED")
        self.assertEqual(value["dispositions"]["PUBLICATION-B"], "SUPERSEDED")

    def test_qualified_publication_is_fallback_when_no_open_transaction_exists(self) -> None:
        value = self.resolve([record("PUBLICATION-A", "PUBLICATION_QUALIFIED")])
        self.assertEqual(value["current_ids"], ["PUBLICATION-A"])
        self.assertEqual(value["dispositions"]["PUBLICATION-A"], "CURRENT_QUALIFIED")

    def test_failed_successor_does_not_retire_predecessor(self) -> None:
        values = [record("PUBLICATION-A"),
                  record("PUBLICATION-B", "FAILED", supersedes="PUBLICATION-A")]
        self.assertEqual(self.resolve(values)["current_ids"], ["PUBLICATION-A"])

    def test_two_unrelated_current_transactions_fail_closed(self) -> None:
        value = self.resolve([record("PUBLICATION-A"), record("PUBLICATION-B")])
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("PUBLICATION_CARDINALITY_CONFLICT", [item["code"] for item in value["errors"]])

    def test_incompatible_nonterminal_siblings_fail_closed(self) -> None:
        values = [record("PUBLICATION-A"), record("PUBLICATION-B", supersedes="PUBLICATION-A"),
                  record("PUBLICATION-C", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("INCOMPATIBLE_SUPERSESSION_LINEAGE", [item["code"] for item in value["errors"]])

    def test_qualified_sibling_is_historical_during_authorized_reprepare(self) -> None:
        values = [record("PUBLICATION-A"),
                  record("PUBLICATION-B", "PUBLICATION_QUALIFIED", supersedes="PUBLICATION-A"),
                  record("PUBLICATION-C", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["current_ids"], ["PUBLICATION-C"])
        self.assertEqual(value["dispositions"]["PUBLICATION-B"], "HISTORICAL_QUALIFIED")

    def test_wrong_mission_supersession_fails_closed(self) -> None:
        values = [record("PUBLICATION-A", mission="OTHER-MISSION"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertIn("SUPERSESSION_MISSION_MISMATCH", [item["code"] for item in value["errors"]])

    def test_wrong_wop_supersession_fails_closed(self) -> None:
        values = [record("PUBLICATION-A", wop="OTHER-WOP"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertIn("SUPERSESSION_WOP_MISMATCH", [item["code"] for item in value["errors"]])

    def test_missing_superseded_target_fails_closed(self) -> None:
        value = self.resolve([record("PUBLICATION-B", supersedes="PUBLICATION-MISSING")])
        self.assertIn("SUPERSEDED_PUBLICATION_MISSING", [item["code"] for item in value["errors"]])

    def test_supersession_cycle_fails_closed(self) -> None:
        values = [record("PUBLICATION-A", supersedes="PUBLICATION-B"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertIn("SUPERSESSION_CYCLE", [item["code"] for item in value["errors"]])

    def test_duplicate_publication_identity_fails_closed(self) -> None:
        value = self.resolve([record("PUBLICATION-A"), record("PUBLICATION-A")])
        self.assertIn("PUBLICATION_ID_AMBIGUOUS", [item["code"] for item in value["errors"]])

    def test_repository_mismatch_fails_closed(self) -> None:
        values = [record("PUBLICATION-A", repository="other-repository"),
                  record("PUBLICATION-B", supersedes="PUBLICATION-A")]
        value = self.resolve(values)
        self.assertIn("SUPERSESSION_REPOSITORY_MISMATCH", [item["code"] for item in value["errors"]])

    def test_timestamps_never_select_a_winner_and_resolution_is_read_only(self) -> None:
        values = [record("PUBLICATION-A", created_at="2099-01-01T00:00:00Z"),
                  record("PUBLICATION-B", created_at="2000-01-01T00:00:00Z")]
        before = copy.deepcopy(values)
        value = self.resolve(values)
        self.assertEqual(value["result"], "FAIL")
        self.assertFalse(value["timestamp_ordering_used"])
        self.assertEqual(values, before)


def run(cwd: Path, *args: str) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class PublicationSupersessionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.runtime = base / "runtime"
        self.remote = base / "remote.git"
        self.previous_eos = os.environ.get("EOS_WORKSPACE")
        os.environ["EOS_WORKSPACE"] = str(base / "eos")
        run(base, "git", "init", "--bare", str(self.remote))
        run(base, "git", "clone", str(self.remote), str(self.repo))
        run(self.repo, "git", "config", "user.name", "Zeus Test")
        run(self.repo, "git", "config", "user.email", "zeus@example.invalid")
        (self.repo / "README.md").write_text("baseline\n", encoding="utf-8")
        run(self.repo, "git", "add", "README.md")
        run(self.repo, "git", "commit", "-m", "baseline")
        run(self.repo, "git", "branch", "-M", "main")
        run(self.repo, "git", "push", "-u", "origin", "HEAD:refs/heads/main")
        self.manifest = base / "manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1, "mission_id": MISSION, "wop_id": WOP,
            "qualification_state": "QUALIFIED", "publication_state": "NOT_PERFORMED",
            "candidate_paths": ["candidate.txt"],
        }), encoding="utf-8")
        (self.repo / "candidate.txt").write_text("candidate-one\n", encoding="utf-8")

    def tearDown(self) -> None:
        if self.previous_eos is None:
            os.environ.pop("EOS_WORKSPACE", None)
        else:
            os.environ["EOS_WORKSPACE"] = self.previous_eos
        self.temp.cleanup()

    @staticmethod
    def file_hashes(path: Path) -> dict[str, str]:
        return {str(item): hashlib.sha256(item.read_bytes()).hexdigest()
                for item in sorted(path.rglob("*.json"))}

    def test_reprepare_replay_status_and_historical_receipts_are_stable(self) -> None:
        first = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        first_receipts = self.file_hashes(self.runtime / "publication-receipts" / first["publication_id"])
        first_transaction = (self.runtime / "publication-transactions" / f"{first['publication_id']}.json").read_bytes()
        index_before = run(self.repo, "git", "diff", "--cached", "--name-only")
        head_before = run(self.repo, "git", "rev-parse", "HEAD")
        manifest_before = self.manifest.read_bytes()
        (self.repo / "candidate.txt").write_text("candidate-two\n", encoding="utf-8")
        second = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        replay = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        mission_status = controller.status(self.repo, MISSION, runtime_root=self.runtime)
        repeated = controller.status(self.repo, MISSION, runtime_root=self.runtime)
        old_status = controller.status(self.repo, first["publication_id"], runtime_root=self.runtime)

        self.assertEqual(second["supersedes_publication_id"], first["publication_id"])
        self.assertEqual(replay["publication_id"], second["publication_id"])
        self.assertEqual(replay["publication_replay"], "IDEMPOTENT")
        self.assertEqual(mission_status["publication_id"], second["publication_id"])
        self.assertEqual(repeated["publication_id"], second["publication_id"])
        self.assertEqual(mission_status["next_authorized_action"], "VERIFY_PREPUBLICATION")
        self.assertEqual(mission_status["publication_disposition"], "CURRENT")
        self.assertEqual(old_status["publication_id"], first["publication_id"])
        self.assertEqual(old_status["publication_disposition"], "SUPERSEDED")
        self.assertFalse(old_status["current_publication"])
        self.assertEqual(self.file_hashes(self.runtime / "publication-receipts" / first["publication_id"]), first_receipts)
        self.assertEqual((self.runtime / "publication-transactions" / f"{first['publication_id']}.json").read_bytes(), first_transaction)
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only"), index_before)
        self.assertEqual(run(self.repo, "git", "rev-parse", "HEAD"), head_before)
        self.assertEqual(self.manifest.read_bytes(), manifest_before)
        self.assertIn("transaction_creation_authority", second)

    def test_current_transaction_integrity_failure_blocks_mission_lookup(self) -> None:
        value = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        path = self.runtime / "publication-transactions" / f"{value['publication_id']}.json"
        corrupted = json.loads(path.read_text(encoding="utf-8"))
        corrupted["next_authorized_action"] = "STAGE_PUBLICATION_CANDIDATE"
        path.write_text(json.dumps(corrupted), encoding="utf-8")
        with self.assertRaises(controller.PublicationTransactionError) as raised:
            controller.status(self.repo, MISSION, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE")

    def test_malformed_transaction_inventory_fails_closed(self) -> None:
        controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        malformed = self.runtime / "publication-transactions" / "PUBLICATION-deadbeef.json"
        malformed.write_text("not-json\n", encoding="utf-8")
        with self.assertRaises(controller.PublicationTransactionError) as raised:
            controller.status(self.repo, MISSION, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE")

    def test_receipt_bound_supersession_digest_mismatch_fails_closed(self) -> None:
        first = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        (self.repo / "candidate.txt").write_text("candidate-two\n", encoding="utf-8")
        second = controller.prepare(self.repo, MISSION, runtime_root=self.runtime, manifest=self.manifest)
        receipt_path = (self.runtime / "publication-receipts" / second["publication_id"] /
                        "PUBLICATION_DISCOVERED.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["supersedes_publication_id"] = "PUBLICATION-FORGED"
        receipt.pop("receipt_digest")
        receipt["receipt_digest"] = digest(receipt)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaises(controller.PublicationTransactionError) as raised:
            controller.status(self.repo, MISSION, runtime_root=self.runtime)
        self.assertEqual(raised.exception.code, "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE")
        self.assertEqual(first["publication_id"], second["supersedes_publication_id"])


if __name__ == "__main__":
    unittest.main()
