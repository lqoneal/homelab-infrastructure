#!/usr/bin/env python3
"""Observable next-action resolution and Zeus CLI qualification."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.next_action import resolve_next_action  # noqa: E402


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

    def test_priority_changes_with_authoritative_state(self):
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
                "COMMISSION_DISPATCHER",
            )
        finally:
            temporary.cleanup()
        temporary, root = self.repository(published_matches=True, active=True)
        try:
            self.assertEqual(
                resolve_next_action(root)["next_authorized_action"]["code"],
                "QUALIFY_PRODUCTION_AGENT",
            )
        finally:
            temporary.cleanup()

    def test_current_cli_reports_beta_and_does_not_modify_worktree(self):
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
        self.assertEqual(
            value["next_authorized_action"]["code"],
            "PUBLISH_SIGNED_REPOSITORY_BASELINE",
        )
        after = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain=v1"],
            text=True, capture_output=True, check=True,
        ).stdout
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
