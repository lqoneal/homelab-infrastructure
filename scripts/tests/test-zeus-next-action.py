#!/usr/bin/env python3
"""Observable next-action resolution and Zeus CLI qualification."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.next_action import resolve_next_action  # noqa: E402
from scripts.lib.emp.oa02_lifecycle import resolve as resolve_oa02  # noqa: E402


class NextActionTests(unittest.TestCase):
    def repository(self, *, published_matches=False, active=False, qualified=False):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "PMCT"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "pmct@example.invalid"], check=True)
        marker = root / "marker"; marker.write_text("state")
        subprocess.run(["git", "-C", str(root), "add", "marker"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "state"], check=True)
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        paths = [
            root / "engineering/authority",
            root / "engineering/dispatch",
            root / "engineering/runtime/pmct",
            root / "engineering/registry",
        ]
        for path in paths: path.mkdir(parents=True, exist_ok=True)
        authority = {
            "operationally_configured": True,
            "repositories": {"homelab": {
                "canonical_locator": str(root),
                "baseline_commit": head if published_matches else "0" * 40,
            }},
        }
        (root / "engineering/authority/operational-authority-state.yaml").write_text(
            yaml.safe_dump(authority)
        )
        (root / "engineering/dispatch/dispatcher-activation.json").write_text(
            json.dumps({"status": "ACTIVE" if active else "PREPARED"})
        )
        agents = [{
            "active": True, "qualification_status": "QUALIFIED"
        }] if qualified else []
        (root / "engineering/dispatch/execution-agent-registry.json").write_text(
            json.dumps({"agents": agents})
        )
        gates = {f"OA-{number:02d}": {"status": "NOT_READY"} for number in range(1, 31)}
        (root / "engineering/runtime/pmct/capability-state.yaml").write_text(
            yaml.safe_dump({
                "overall_result": "NOT_READY", "last_evaluated_gate": "OA-01",
                "gates": gates,
            })
        )
        (root / "engineering/registry/work-registry.yaml").write_text(
            yaml.safe_dump({"entities": {"work_items": []}})
        )
        return temporary, root

    def test_publication_precedes_oa01_verification(self):
        temporary, root = self.repository()
        try:
            self.assertEqual(
                resolve_next_action(root)["next_authorized_action"]["code"],
                "PUBLISH_SIGNED_REPOSITORY_BASELINE",
            )
        finally:
            temporary.cleanup()
        temporary, root = self.repository(published_matches=True)
        try:
            self.assertEqual(
                resolve_next_action(root)["next_authorized_action"]["code"],
                "RUN_OA-01_VERIFICATION",
            )
        finally:
            temporary.cleanup()

    def test_verification_precedes_acceptance(self):
        temporary, root = self.repository(published_matches=True)
        try:
            with patch(
                "scripts.lib.emp.next_action._oa01_lifecycle",
                return_value={
                    "verification_passed": True,
                    "acceptance_recorded": False,
                },
            ):
                self.assertEqual(
                    resolve_next_action(root)["next_authorized_action"]["code"],
                    "RECORD_OA-01_OPERATOR_ACCEPTANCE",
                )
        finally:
            temporary.cleanup()

    def test_matching_acceptance_reaches_oa02_preflight_not_dispatcher(self):
        temporary, root = self.repository(published_matches=True)
        try:
            with patch(
                "scripts.lib.emp.next_action._oa01_lifecycle",
                return_value={
                    "verification_passed": True,
                    "acceptance_recorded": True,
                },
            ):
                value = resolve_next_action(root)
                self.assertEqual(
                    value["next_authorized_action"]["code"],
                    "RUN_OA-02_PRE_EXECUTION_VERIFICATION",
                )
                self.assertNotEqual(
                    value["next_authorized_action"]["code"],
                    "COMMISSION_DISPATCHER",
                )
        finally:
            temporary.cleanup()

    def test_stale_or_mismatched_evidence_cannot_advance(self):
        temporary, root = self.repository(published_matches=True)
        try:
            for lifecycle in (
                {"verification_passed": False, "acceptance_recorded": False},
                {"verification_passed": False, "acceptance_recorded": True},
            ):
                with self.subTest(lifecycle=lifecycle), patch(
                    "scripts.lib.emp.next_action._oa01_lifecycle",
                    return_value=lifecycle,
                ):
                    self.assertEqual(
                        resolve_next_action(root)["next_authorized_action"]["code"],
                        "RUN_OA-01_VERIFICATION",
                    )
        finally:
            temporary.cleanup()

    def test_current_cli_reports_lifecycle_phase_and_does_not_modify_worktree(self):
        pointer = ROOT / ".zeus/runtime/authority/active-publication.json"
        pointer_before = pointer.read_bytes()
        publication = (
            ROOT / ".zeus/runtime/authority/publications/"
            "AUTHORITY-PUBLICATION-7dc94267-ab5e-4a7f-b962-f6ce3335f307"
        )
        artifact_before = {
            path.relative_to(publication): path.read_bytes()
            for path in publication.rglob("*") if path.is_file()
        }
        before = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain=v1"],
            text=True, capture_output=True, check=True,
        ).stdout
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "next-action", "--json"],
            text=True, capture_output=True, check=False,
            env={"ZEUS_TESTING": "operator", "ZEUS_NO_INTRO": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["zeus_mode"], "BETA")
        self.assertEqual(value["operational_dispatch"], "DISABLED")
        repository = value["repository"]
        expected_action = (
            "PUBLISH_SIGNED_REPOSITORY_BASELINE"
            if repository["implementation_baseline"]
            != repository["published_baseline"]
            else (
                (
                    resolve_oa02(ROOT)["next_action"]
                    if value["oa01_lifecycle"]["operator_acceptance"] == "RECORDED"
                    else "RECORD_OA-01_OPERATOR_ACCEPTANCE"
                )
                if value["oa01_lifecycle"]["operator_verification"] == "PASS"
                else "RUN_OA-01_VERIFICATION"
            )
        )
        self.assertEqual(value["next_authorized_action"]["code"], expected_action)
        self.assertIn(
            value["oa01_lifecycle"]["operator_verification"], {"ABSENT", "PASS"}
        )
        self.assertIn(
            value["oa01_lifecycle"]["operator_acceptance"],
            {"NOT_RECORDED", "RECORDED"},
        )
        after = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain=v1"],
            text=True, capture_output=True, check=True,
        ).stdout
        self.assertEqual(after, before)
        self.assertEqual(pointer.read_bytes(), pointer_before)
        self.assertEqual({
            path.relative_to(publication): path.read_bytes()
            for path in publication.rglob("*") if path.is_file()
        }, artifact_before)
        eligibility = subprocess.run(
            [
                "/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP/"
                "bin/check-gate-eligibility",
                "OA-02",
            ],
            text=True, capture_output=True, check=False,
        )
        eligibility_output = eligibility.stdout + eligibility.stderr
        if value["oa01_lifecycle"]["operator_acceptance"] == "RECORDED":
            self.assertEqual(eligibility.returncode, 0)
            self.assertIn("ELIGIBILITY=CONDITIONALLY_ELIGIBLE", eligibility_output)
        else:
            self.assertEqual(eligibility.returncode, 77)
            self.assertIn("OA-02_ELIGIBILITY=BLOCKED", eligibility_output)
            self.assertIn(
                "BLOCKING_REASON=OA-01_OPERATOR_ACCEPTANCE_REQUIRED",
                eligibility_output,
            )


if __name__ == "__main__":
    unittest.main()
