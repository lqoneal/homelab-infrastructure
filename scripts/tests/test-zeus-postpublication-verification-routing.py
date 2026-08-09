#!/usr/bin/env python3
"""Regression coverage for the canonical Zeus postpublication route."""

from __future__ import annotations

import contextlib
import importlib.util
import importlib.machinery
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import publication_transaction as controller


ROOT = Path(__file__).resolve().parents[2]
PUBLICATION = "PUBLICATION-POSTVERIFY-TEST-001"


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    value = subprocess.run([*args], cwd=cwd, text=True, capture_output=True, check=False)
    if value.returncode:
        raise AssertionError(value.stderr or value.stdout)
    return value


class PostpublicationVerificationRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="zeus-postpublication-routing-")
        base = Path(self.temp.name)
        self.remote = base / "remote.git"
        self.repo = base / "repo"
        self.runtime = base / "runtime"
        self.eos = base / "eos"
        self.previous_eos = os.environ.get("EOS_WORKSPACE")
        os.environ["EOS_WORKSPACE"] = str(self.eos)
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
        (self.repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        self.manifest = base / "manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "mission_id": "MISSION-POSTVERIFY-TEST",
            "wop_id": "WOP-POSTVERIFY-TEST",
            "qualification_state": "QUALIFIED",
            "publication_state": "NOT_PERFORMED",
            "candidate_paths": ["candidate.txt"],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        if self.previous_eos is None:
            os.environ.pop("EOS_WORKSPACE", None)
        else:
            os.environ["EOS_WORKSPACE"] = self.previous_eos
        self.temp.cleanup()

    def _eos_synchronized(self) -> dict:
        record = controller.prepare(
            self.repo, "MISSION-POSTVERIFY-TEST", runtime_root=self.runtime, manifest=self.manifest
        )
        record = controller.verify(
            self.repo, record["publication_id"], runtime_root=self.runtime, run_validators=False
        )
        record = controller.stage(self.repo, record["publication_id"], runtime_root=self.runtime)
        record = controller.verify_staged(self.repo, record["publication_id"], runtime_root=self.runtime)
        record = controller.commit(self.repo, record["publication_id"], runtime_root=self.runtime)
        record = controller.push(self.repo, record["publication_id"], runtime_root=self.runtime)
        record["eos_synchronized_baseline"] = record["commit_id"]
        return controller._record_milestone(
            self.runtime, record, "EOS_SYNCHRONIZED", eos_baseline=record["commit_id"]
        )

    def _cli(self, action: str, publication_id: str) -> tuple[int, dict]:
        loader = importlib.machinery.SourceFileLoader(
            "zeus_cli_postverify_test", str(ROOT / "scripts" / "zeus")
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        output = io.StringIO()
        interface = self.runtime / "operator-state.json"
        environment = {
            "ZEUS_TESTING": "1",
            "ZEUS_OPERATOR_STATE": str(interface),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        with patch.object(module, "ROOT", self.repo), patch.dict(os.environ, environment, clear=False), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = module.main([
                "--runtime-root", str(self.runtime), "publication", action,
                publication_id, "--json",
            ])
        return code, json.loads(output.getvalue())

    def _pass_projection(self, record: dict) -> dict:
        return {
            "result": "PASS", "repository_id": record["repository_id"],
            "head": record["commit_id"], "origin_main": record["commit_id"],
            "eos_baseline": record["commit_id"], "eos_parity": True,
        }

    def test_canonical_cli_advances_eos_to_postpublication_and_persists_receipt(self):
        record = self._eos_synchronized()
        projection = self._pass_projection(record)
        with patch.object(controller, "_revalidate_authority", return_value={"result": "PASS"}), \
             patch.object(controller, "project_repository", return_value=projection):
            code, value = self._cli("verify-post", record["publication_id"])
        self.assertEqual(0, code)
        self.assertEqual("POSTPUBLICATION_VERIFIED", value["current_state"])
        self.assertEqual("QUALIFY_PUBLICATION", value["next_authorized_action"])
        persisted = controller._load_transaction(self.runtime, record["publication_id"])
        self.assertEqual("POSTPUBLICATION_VERIFIED", persisted["current_state"])
        receipt_ref = persisted["milestones"]["POSTPUBLICATION_VERIFIED"]
        receipt = json.loads(Path(receipt_ref["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual("PASS", receipt["result"])
        self.assertEqual(receipt["receipt_digest"], receipt_ref["receipt_digest"])
        self.assertEqual("QUALIFY_PUBLICATION", persisted["next_authorized_action"])

    def test_premature_postpublication_verification_fails_closed(self):
        record = controller.prepare(
            self.repo, "MISSION-POSTVERIFY-TEST", runtime_root=self.runtime, manifest=self.manifest
        )
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.verify(
                self.repo, record["publication_id"], runtime_root=self.runtime,
                postpublication=True,
            )
        self.assertEqual("PUBLICATION_TRANSITION_NOT_AUTHORIZED", error.exception.code)
        self.assertFalse(
            (self.runtime / "publication-receipts" / record["publication_id"] /
             "POSTPUBLICATION_VERIFIED.json").exists()
        )

    def test_prepublication_route_cannot_masquerade_as_postpublication(self):
        record = self._eos_synchronized()
        code, value = self._cli("verify-pre", record["publication_id"])
        self.assertEqual(78, code)
        self.assertEqual("PUBLICATION_TRANSITION_NOT_AUTHORIZED", value["blockers"][0]["code"])
        self.assertEqual("EOS_SYNCHRONIZED", controller._load_transaction(
            self.runtime, record["publication_id"]
        )["current_state"])

    def test_postpublication_replay_is_idempotent_and_qualification_is_downstream(self):
        record = self._eos_synchronized()
        with self.assertRaises(controller.PublicationTransactionError) as error:
            controller.qualify(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual("PUBLICATION_TRANSITION_NOT_AUTHORIZED", error.exception.code)
        projection = self._pass_projection(record)
        with patch.object(controller, "_revalidate_authority", return_value={"result": "PASS"}), \
             patch.object(controller, "project_repository", return_value=projection):
            code, first = self._cli("verify-post", record["publication_id"])
            replay_code, replay = self._cli("verify-post", record["publication_id"])
            qualified = controller.qualify(self.repo, record["publication_id"], runtime_root=self.runtime)
        self.assertEqual(0, code)
        self.assertEqual(0, replay_code)
        self.assertFalse(first["replayed"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(first["milestones"]["POSTPUBLICATION_VERIFIED"], replay["milestones"]["POSTPUBLICATION_VERIFIED"])
        self.assertEqual("PUBLICATION_QUALIFIED", qualified["current_state"])


if __name__ == "__main__":
    unittest.main()
