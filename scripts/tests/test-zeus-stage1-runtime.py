#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime  # noqa: E402


class FakeResolver:
    resolution = "AUTHORIZED"

    def __init__(self, root: Path):
        self.root = root

    def resolve(self, mission: str):
        contract = {
            "contract_id": f"MC-{mission}",
            "mission_id": mission,
            "repository": {
                "identity": self.root.name,
                "root": str(self.root),
                "branch": "main",
                "baseline": subprocess.check_output(
                    ["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True
                ).strip(),
            },
            "dirty_tree": {"policy": "CLEAN_REQUIRED"},
        }
        return {
            "resolution": self.resolution,
            "transactional_authority": self.resolution == "AUTHORIZED",
            "contract": contract,
            "evidence_digest": hashlib.sha256(mission.encode()).hexdigest(),
        }


class ZeusStage1RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.repository = base / "repo"
        self.repository.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(self.repository)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repository), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repository), "config", "user.name", "Zeus Test"], check=True)
        (self.repository / "README.md").write_text("test\n")
        subprocess.run(["git", "-C", str(self.repository), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.repository), "commit", "-m", "baseline"], check=True, capture_output=True)
        self.state = base / "state"
        self.package = base / "wop"
        self.make_package(self.package)
        self.at = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def make_package(path: Path):
        (path / "manifests").mkdir(parents=True)
        (path / "execution").mkdir()
        (path / "bootstrap.md").write_text("# Bootstrap\n")
        (path / "roadmap.md").write_text("# Roadmap\n")
        (path / "gates.yaml").write_text("gates:\n  - admission\n")
        (path / "manifests" / "package.yaml").write_text("schema_version: 1\n")
        (path / "execution" / "run.sh").write_text("#!/bin/sh\n")
        (path / "mission.yaml").write_text(yaml.safe_dump({
            "mission_id": "ZEUS-OPERATIONAL-ALPHA",
            "wop_id": "ZH-001",
            "objective": "Qualify supervised Operational Alpha.",
            "scope": ["repository qualification", "no mission execution"],
            "dependencies": ["OA-04"],
            "priority": 5,
            "candidate_state": "CANDIDATE",
            "required_execution_files": ["execution/run.sh"],
        }))

    def runtime(self):
        return Stage1Runtime(
            self.repository, self.state, resolver_factory=FakeResolver,
            operator_resolver=lambda: "operator",
        )

    def test_valid_package_is_admitted_staged_persisted_and_published(self):
        result = self.runtime().submit(self.package, at=self.at)
        self.assertEqual("STAGED", result["state"])
        self.assertEqual("MC-ZEUS-OPERATIONAL-ALPHA", result["contract_id"])
        self.assertEqual("PASS", result["validation_evidence"]["package_validation"]["result"])
        self.assertEqual("PASS", result["validation_evidence"]["repository_verification"]["result"])
        self.assertEqual(
            {
                "mission_id": "ZEUS-OPERATIONAL-ALPHA",
                "wop_id": "ZH-001",
                "objective": "Qualify supervised Operational Alpha.",
                "scope": ["repository qualification", "no mission execution"],
                "dependencies": ["OA-04"],
                "priority": 5,
                "state": "CANDIDATE",
            },
            result["staging_contract"],
        )
        self.assertEqual(64, len(result["staging_contract_digest"]))
        restarted = self.runtime()
        self.assertEqual(result["instance_id"], restarted.show("ZEUS-OPERATIONAL-ALPHA")["instance_id"])
        self.assertEqual(1, restarted.status()["states"]["STAGED"])
        self.assertEqual(1, len(restarted.list()))
        event_types = {
            json.loads(path.read_text())["event_type"]
            for path in (self.state / "eens").glob("*.json")
        }
        self.assertEqual(
            {"mission.submitted", "mission.validating", "mission.admitted", "mission.staged"},
            event_types,
        )

    def test_duplicate_submission_is_idempotent(self):
        first = self.runtime().submit(self.package, at=self.at)
        second = self.runtime().submit(self.package, at=self.at)
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(first["instance_id"], second["instance_id"])
        self.assertEqual(1, len(self.runtime().list()))

    def test_invalid_package_is_rejected_with_component_diagnostics(self):
        (self.package / "roadmap.md").unlink()
        with self.assertRaises(Stage1Error) as caught:
            self.runtime().submit(self.package, at=self.at)
        self.assertIn(
            {"component": "roadmap", "error": "missing"},
            caught.exception.evidence["validation_evidence"]["failures"],
        )
        self.assertEqual("REJECTED", caught.exception.evidence["state"])
        event_types = [
            json.loads(path.read_text())["event_type"]
            for path in (self.state / "eens").glob("*.json")
        ]
        self.assertIn("mission.rejected", event_types)

    def test_incomplete_staging_contract_is_rejected_without_staged_state(self):
        metadata = yaml.safe_load((self.package / "mission.yaml").read_text())
        for field in ("objective", "scope", "dependencies", "priority", "candidate_state"):
            with self.subTest(field=field):
                candidate = self.package.parent / f"missing-{field}"
                self.make_package(candidate)
                value = yaml.safe_load((candidate / "mission.yaml").read_text())
                value.pop(field)
                (candidate / "mission.yaml").write_text(yaml.safe_dump(value))
                runtime = Stage1Runtime(
                    self.repository,
                    self.state.parent / f"state-{field}",
                    resolver_factory=FakeResolver,
                    operator_resolver=lambda: "operator",
                )
                with self.assertRaises(Stage1Error):
                    runtime.submit(candidate, at=self.at)
                self.assertEqual(0, runtime.status()["states"]["STAGED"])

    def test_unauthorized_package_is_rejected(self):
        class Unauthorized(FakeResolver):
            resolution = "NO_AUTHORIZED_WORK"

        runtime = Stage1Runtime(
            self.repository, self.state, resolver_factory=Unauthorized,
            operator_resolver=lambda: "operator",
        )
        with self.assertRaisesRegex(Stage1Error, "NO_AUTHORIZED_WORK") as caught:
            runtime.submit(self.package, at=self.at)
        self.assertEqual("REJECTED", caught.exception.evidence["state"])

    def test_repository_verification_rejects_dirty_tree(self):
        (self.repository / "untracked").write_text("dirty\n")
        with self.assertRaisesRegex(Stage1Error, "repository verification failed") as caught:
            self.runtime().submit(self.package, at=self.at)
        failures = caught.exception.evidence["validation_evidence"]["repository_verification"]["failures"]
        self.assertIn("WORKING_TREE_NOT_CLEAN", failures)

    def test_tar_gz_submission_and_integrity(self):
        checksummed = self.package / "execution" / "run.sh"
        digest = hashlib.sha256(checksummed.read_bytes()).hexdigest()
        (self.package / "SHA256SUMS").write_text(f"{digest}  execution/run.sh\n")
        archive = self.package.parent / "wop.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            stream.add(self.package, arcname="wop")
        result = self.runtime().submit(archive, at=self.at)
        self.assertEqual(
            [{"path": "execution/run.sh", "result": "PASS"}],
            result["validation_evidence"]["package_validation"]["integrity"],
        )


if __name__ == "__main__":
    unittest.main()
