#!/usr/bin/env python3
"""Focused qualification for the Zeus-native publication transaction controller."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp import publication_transaction as controller  # noqa: E402


def run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    value = subprocess.run([*args], cwd=cwd, text=True, capture_output=True, check=False)
    if check and value.returncode:
        raise AssertionError(value.stderr or value.stdout)
    return value


class PublicationTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.remote = base / "remote.git"
        self.repo = base / "repo"
        self.runtime = base / "runtime"
        self.previous_eos = os.environ.get("EOS_WORKSPACE")
        os.environ["EOS_WORKSPACE"] = str(base / "eos")
        run(base, "git", "init", "--bare", str(self.remote))
        run(base, "git", "clone", str(self.remote), str(self.repo))
        run(self.repo, "git", "config", "user.name", "Zeus Test")
        run(self.repo, "git", "config", "user.email", "zeus-test@example.invalid")
        (self.repo / "README.md").write_text("baseline\n", encoding="utf-8")
        run(self.repo, "git", "add", "README.md")
        run(self.repo, "git", "commit", "-m", "baseline")
        run(self.repo, "git", "branch", "-M", "main")
        run(self.repo, "git", "push", "-u", "origin", "HEAD:refs/heads/main")
        run(self.repo, "git", "fetch", "origin", "main")
        self.mission = "MISSION-PUBLICATION-TEST"
        self.manifest = base / "manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "mission_id": self.mission,
            "wop_id": "WOP-PUBLICATION-TEST",
            "qualification_state": "QUALIFIED",
            "publication_state": "NOT_PERFORMED",
            "candidate_paths": ["candidate.txt"],
        }), encoding="utf-8")
        (self.repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        (self.repo / "unrelated file.txt").write_text("preserve\n", encoding="utf-8")

    def tearDown(self) -> None:
        if self.previous_eos is None:
            os.environ.pop("EOS_WORKSPACE", None)
        else:
            os.environ["EOS_WORKSPACE"] = self.previous_eos
        self.temp.cleanup()

    def test_review_mode_is_read_only_and_prepare_is_deterministic(self) -> None:
        before = controller.inspect(self.repo, self.mission, runtime_root=self.runtime)
        self.assertTrue(before["read_only"])
        self.assertEqual(before["next_authorized_action"], "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY")
        review = controller.run(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        self.assertEqual(review["result"], "READY_FOR_REVIEW")
        self.assertEqual(review["next_authorized_action"], "APPROVE_PUBLICATION")
        first = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        replay = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        self.assertEqual(first["publication_id"], replay["publication_id"])
        self.assertEqual(first["candidate_paths"], ["candidate.txt"])
        classified = controller.classify(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        self.assertIn("unrelated file.txt", [item["path"] for item in classified["classification"]["paths"]])

    def test_prepublication_verification_exact_staging_and_replay(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        verified = controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        self.assertEqual(verified["result"], "PASS")
        staged = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(staged["current_state"], "CANDIDATE_STAGED")
        self.assertEqual(staged["next_authorized_action"], "VERIFY_STAGED_SET")
        self.assertNotIn("STAGED_SET_VERIFIED", staged["milestones"])
        replay = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(replay["publication_id"], staged["publication_id"])
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout.splitlines(), ["candidate.txt"])
        verified_staged = controller.verify_staged(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(verified_staged["current_state"], "STAGED_SET_VERIFIED")
        self.assertEqual(verified_staged["next_authorized_action"], "COMMIT_PUBLICATION")
        committed = controller.commit(self.repo, record["publication_id"], runtime_root=self.runtime)
        commit_replay = controller.commit(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(committed["commit_id"], commit_replay["commit_id"])
        self.assertEqual(committed["current_state"], "COMMIT_CREATED")

    def test_candidate_isolated_exposes_only_verification(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        status = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        inspection = controller.inspect(self.repo, record["publication_id"], runtime_root=self.runtime)
        mission = controller.mission_projection(self.repo, self.mission, runtime_root=self.runtime)
        self.assertEqual(status["current_state"], "CANDIDATE_ISOLATED")
        self.assertIsNone(status["prepublication_result"])
        self.assertNotIn("PREPUBLICATION_VERIFIED", status["completed_milestones"])
        self.assertIn("PREPUBLICATION_VERIFIED", status["pending_milestones"])
        self.assertEqual(status["next_authorized_action"], "VERIFY_PREPUBLICATION")
        self.assertEqual(inspection["next_authorized_action"], "VERIFY_PREPUBLICATION")
        self.assertEqual(mission["publication_state"], "CANDIDATE_ISOLATED")
        self.assertEqual(mission["next_authorized_action"], "VERIFY_PREPUBLICATION")
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "PUBLICATION_TRANSITION_NOT_AUTHORIZED")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_verify_persists_receipt_state_and_fresh_reload_before_authority(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        frozen_digest = record["candidate_digest"]
        index_before = run(self.repo, "git", "diff", "--cached", "--name-only").stdout
        original_save = controller._save
        observed_before_persistence: list[str] = []

        def observing_save(runtime: Path, value: dict) -> None:
            if value.get("current_state") == "PREPUBLICATION_VERIFIED":
                observed_before_persistence.append(
                    controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)["next_authorized_action"]
                )
            original_save(runtime, value)

        with patch.object(controller, "_save", side_effect=observing_save):
            verified = controller.verify(
                self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False
            )
        self.assertEqual(observed_before_persistence, ["VERIFY_PREPUBLICATION"])
        self.assertEqual(verified["result"], "PASS")
        self.assertEqual(verified["current_state"], "PREPUBLICATION_VERIFIED")
        self.assertEqual(verified["prepublication_result"], "PASS")
        self.assertIn("PREPUBLICATION_VERIFIED", verified["completed_milestones"])
        self.assertNotIn("PREPUBLICATION_VERIFIED", verified["pending_milestones"])
        self.assertEqual(verified["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertEqual(verified["candidate_digest"], frozen_digest)
        milestone = verified["milestones"]["PREPUBLICATION_VERIFIED"]
        receipt = json.loads(Path(milestone["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual(receipt["receipt_digest"], milestone["receipt_digest"])
        self.assertEqual(receipt["publication_id"], record["publication_id"])
        self.assertEqual(receipt["input_digest"], frozen_digest)
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        self.assertEqual(persisted["current_state"], "PREPUBLICATION_VERIFIED")
        self.assertEqual(persisted["prepublication_result"], "PASS")
        fresh = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        mission = controller.mission_projection(self.repo, self.mission, runtime_root=self.runtime)
        self.assertEqual(fresh["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertEqual(fresh["transaction_integrity"]["result"], "PASS")
        self.assertEqual(mission["publication_state"], "PREPUBLICATION_VERIFIED")
        self.assertEqual(mission["prepublication_result"], "PASS")
        self.assertEqual(mission["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, index_before)

    def test_verify_replay_is_idempotent_and_preserves_receipt_lineage(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        first = controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        first_receipt = dict(first["milestones"]["PREPUBLICATION_VERIFIED"])
        replay = controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["result"], "PASS")
        self.assertEqual(replay["current_state"], "PREPUBLICATION_VERIFIED")
        self.assertEqual(replay["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertEqual(replay["milestones"]["PREPUBLICATION_VERIFIED"], first_receipt)
        self.assertEqual(replay["completed_milestones"].count("PREPUBLICATION_VERIFIED"), 1)
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_verification_failure_is_fail_closed(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        (self.repo / "candidate.txt").write_text("changed-after-freeze\n", encoding="utf-8")
        failed = controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        self.assertEqual(failed["result"], "FAIL")
        self.assertNotEqual(failed["prepublication_result"], "PASS")
        self.assertNotIn("PREPUBLICATION_VERIFIED", failed["completed_milestones"])
        self.assertNotEqual(failed["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertFalse((self.runtime / "publication-receipts" / record["publication_id"] / "PREPUBLICATION_VERIFIED.json").exists())
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_transaction_persistence_failure_and_orphan_receipt_fail_closed(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        with patch.object(controller, "_save", side_effect=OSError("simulated persistence failure")):
            with self.assertRaises(controller.PublicationTransactionError) as error:
                controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        self.assertEqual(error.exception.code, "PUBLICATION_TRANSACTION_PERSISTENCE_FAILED")
        orphan = self.runtime / "publication-receipts" / record["publication_id"] / "PREPUBLICATION_VERIFIED.json"
        self.assertTrue(orphan.is_file())
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        self.assertEqual(persisted["current_state"], "CANDIDATE_ISOLATED")
        self.assertIsNone(persisted["prepublication_result"])
        self.assertNotIn("PREPUBLICATION_VERIFIED", persisted["milestones"])
        status = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(status["next_authorized_action"], "VERIFY_PREPUBLICATION")
        self.assertNotEqual(status["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        orphan_digest = json.loads(orphan.read_text(encoding="utf-8"))["receipt_digest"]
        recovered = controller.verify(
            self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False
        )
        self.assertEqual(recovered["result"], "PASS")
        self.assertEqual(
            recovered["milestones"]["PREPUBLICATION_VERIFIED"]["receipt_digest"],
            orphan_digest,
        )
        self.assertEqual(recovered["next_authorized_action"], "STAGE_PUBLICATION_CANDIDATE")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_invalid_receipt_binding_revokes_staging_authority(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        verified = controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        receipt_path = Path(verified["milestones"]["PREPUBLICATION_VERIFIED"]["receipt_path"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["input_digest"] = "forged"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        status = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(status["result"], "FAIL")
        self.assertEqual(status["next_authorized_action"], "RECOVER_PUBLICATION_TRANSACTION")
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "PREPUBLICATION_AUTHORITY_NOT_DURABLE")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_unexpected_staged_path_fails_closed(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        run(self.repo, "git", "add", "--", "unrelated file.txt")
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "UNEXPECTED_STAGED_PATH")

    def test_stage_recovers_exact_index_after_transaction_persistence_failure(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        with patch.object(controller, "_save", side_effect=OSError("simulated persistence failure")):
            with self.assertRaises(controller.PublicationTransactionError) as error:
                controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "PUBLICATION_TRANSACTION_PERSISTENCE_FAILED")
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        self.assertEqual(persisted["current_state"], "PREPUBLICATION_VERIFIED")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout.splitlines(), ["candidate.txt"])
        recovered = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(recovered["current_state"], "CANDIDATE_STAGED")
        self.assertEqual(recovered["next_authorized_action"], "VERIFY_STAGED_SET")
        receipt = json.loads(Path(recovered["milestones"]["CANDIDATE_STAGED"]["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual(receipt["staged_tree_digest"], recovered["candidate_digest"])

    def test_stage_recovery_rejects_changed_staged_content(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        (self.repo / "candidate.txt").write_text("changed-index-content\n", encoding="utf-8")
        run(self.repo, "git", "add", "--", "candidate.txt")
        (self.repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "STAGED_CONTENT_MISMATCH")
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        self.assertEqual(persisted["current_state"], "PREPUBLICATION_VERIFIED")

    def test_stage_recovery_rejects_missing_candidate_path(self) -> None:
        (self.repo / "second.txt").write_text("second\n", encoding="utf-8")
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["candidate_paths"] = ["candidate.txt", "second.txt"]
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        run(self.repo, "git", "add", "--", "candidate.txt")
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "STAGED_CANDIDATE_PATH_MISSING")

    def test_stage_rejects_ambiguous_persistence_without_index_mutation(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        persisted["staged_tree_digest"] = persisted["candidate_digest"]
        controller._save(self.runtime, persisted)
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(error.exception.code, "AMBIGUOUS_STAGE_RECOVERY_STATE")
        self.assertEqual(run(self.repo, "git", "diff", "--cached", "--name-only").stdout, "")

    def test_status_rejects_persisted_staged_digest_mismatch(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        staged = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        staged["staged_tree_digest"] = "0" * 64
        controller._save(self.runtime, staged)
        failed = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(failed["result"], "FAIL")
        self.assertEqual(failed["candidate_authority_revalidation"]["blocked"][0]["code"], "STAGED_TREE_DIGEST_MISMATCH")

    def test_staged_digest_uses_index_bytes_and_detects_poststage_tamper(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        staged = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        (self.repo / "candidate.txt").write_text("worktree-only-change\n", encoding="utf-8")
        status = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(status["result"], "PASS")
        self.assertEqual(status["staged_tree_digest"], staged["candidate_digest"])
        run(self.repo, "git", "add", "--", "candidate.txt")
        failed = controller.status(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(failed["result"], "FAIL")
        self.assertEqual(failed["blockers"][0]["code"], "STALE_CLASSIFICATION")
        self.assertEqual(failed["candidate_authority_revalidation"]["blocked"][0]["code"], "STAGED_CONTENT_MISMATCH")

    def test_mission_projection_ignores_stale_transaction(self) -> None:
        first = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        (self.repo / "candidate.txt").write_text("candidate-v2\n", encoding="utf-8")
        second = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        self.assertNotEqual(first["publication_id"], second["publication_id"])
        projection = controller.mission_projection(self.repo, self.mission, runtime_root=self.runtime)
        self.assertEqual(projection["publication_id"], second["publication_id"])
        self.assertEqual(projection["publication_state"], "CANDIDATE_ISOLATED")
        self.assertEqual(projection["publication_blockers"], [])

    def test_push_replay_does_not_create_second_commit(self) -> None:
        record = controller.prepare(self.repo, self.mission, runtime_root=self.runtime, manifest=self.manifest)
        controller.verify(self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False)
        controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        controller.verify_staged(self.repo, record["publication_id"], runtime_root=self.runtime)
        committed = controller.commit(self.repo, record["publication_id"], runtime_root=self.runtime)
        pushed = controller.push(self.repo, record["publication_id"], runtime_root=self.runtime)
        replay = controller.push(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(pushed["published_head"], committed["commit_id"])
        self.assertEqual(replay["published_head"], pushed["published_head"])
        self.assertEqual(run(self.repo, "git", "rev-list", "--count", "HEAD").stdout.strip(), "2")


if __name__ == "__main__":
    unittest.main()
