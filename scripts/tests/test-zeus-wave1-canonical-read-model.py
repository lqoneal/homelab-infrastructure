#!/usr/bin/env python3
"""Wave 1 proof for canonical P2 mission discovery and next action."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.submission_boundary import _digest, mission_view  # noqa: E402
from scripts.lib.emp.wop_canonicalization import canonicalize  # noqa: E402


SOURCE = ROOT / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
WOP = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"


class Wave1CanonicalReadModelTests(unittest.TestCase):
    def invoke(self, runtime: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = {
            **os.environ,
            "ZEUS_RUNTIME_ROOT": str(runtime),
            "ZEUS_NO_INTRO": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), *args],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def tree_digest(root: Path) -> dict[str, str]:
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def submitted(self) -> tuple[Path, Path, Path]:
        holder = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="zeus-wave1-")))
        source = holder / "source-wop.md"
        shutil.copy2(SOURCE, source)
        canonicalize(source, ROOT)
        runtime = holder / "runtime"
        result = self.invoke(runtime, "submit", str(source), "--repository", str(ROOT), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return holder, source, runtime

    def test_all_native_read_surfaces_share_canonical_identity_and_next_action(self) -> None:
        _, _, runtime = self.submitted()
        before = self.tree_digest(runtime)
        actions = ("show", "state", "status", "readiness", "eligibility", "authority", "blockers", "next", "snapshot", "verify")
        projections = []
        for action in actions:
            result = self.invoke(runtime, "mission", action, MISSION, "--json")
            self.assertEqual(result.returncode, 0, f"{action}: {result.stderr}")
            value = json.loads(result.stdout)
            self.assertEqual(value["result"], "PASS", action)
            self.assertEqual(value["mission_id"], MISSION, action)
            self.assertEqual(value.get("wop_id", WOP), WOP, action)
            self.assertEqual(value.get("lifecycle_state", "ADMISSION_REQUESTED"), "ADMISSION_REQUESTED", action)
            self.assertEqual(value.get("blockers", []), [], action)
            self.assertEqual(value.get("next_authorized_action"), "EVALUATE_MISSION_ADMISSION", action)
            self.assertTrue(value["read_only"], action)
            projections.append(value)
        self.assertEqual(projections[3]["readiness"], "ADMISSION_REQUESTED")
        self.assertEqual(projections[4]["eligibility"], "ADMISSION_EVALUATION_PENDING")
        self.assertEqual(before, self.tree_digest(runtime))

    def test_exact_replay_is_deterministic_and_does_not_mutate_runtime(self) -> None:
        _, _, runtime = self.submitted()
        before = self.tree_digest(runtime)
        first = json.loads(self.invoke(runtime, "mission", "snapshot", MISSION, "--json").stdout)
        second = json.loads(self.invoke(runtime, "mission", "snapshot", MISSION, "--json").stdout)
        self.assertEqual(first, second)
        self.assertEqual(before, self.tree_digest(runtime))

    def test_live_mission_list_uses_canonical_submission_discovery(self) -> None:
        _, _, runtime = self.submitted()
        result = self.invoke(runtime, "mission", "list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        discovered = [item for item in value["missions"] if item.get("mission_id") == MISSION]
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0]["wop_id"], WOP)
        self.assertEqual(discovered[0]["lifecycle"], "ADMISSION_REQUESTED")
        self.assertEqual(discovered[0]["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")
        self.assertEqual(discovered[0]["canonical_lifecycle_owner"], "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN")
        self.assertTrue(discovered[0]["read_only"])

    def test_missing_current_mission_does_not_fall_through_to_oa_selector(self) -> None:
        holder = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="zeus-live-mission-missing-")))
        result = self.invoke(holder / "runtime", "mission", "show", MISSION, "--json")
        self.assertEqual(result.returncode, 78)
        value = json.loads(result.stdout)
        self.assertEqual(value["result"], "MISSION_NOT_FOUND")
        self.assertEqual(value["mission_id"], MISSION)
        self.assertNotIn("OA-01", json.dumps(value))

    def test_missing_request_and_tampered_next_action_fail_closed(self) -> None:
        _, _, runtime = self.submitted()
        receipt_path = next((runtime / "submissions/receipts").glob("*.json"))
        request_path = next((runtime / "submissions/requests").glob("*.json"))
        request_path.unlink()
        missing = self.invoke(runtime, "mission", "show", MISSION, "--json")
        self.assertEqual(missing.returncode, 78)
        self.assertIn("ADMISSION_REQUEST_PROJECTION_MISSING", json.loads(missing.stdout)["blockers"][0]["code"])

        # Recreate the request only for the independent contradiction case.
        request_path.write_text(
            json.dumps({
                "schema_version": 1, "request_type": "mission-admission-request",
                "admission_request_id": json.loads(receipt_path.read_text())["admission_request_id"],
                "submission_id": json.loads(receipt_path.read_text())["submission_id"],
                "submission_digest": json.loads(receipt_path.read_text())["submission_digest"],
                "mission_id": MISSION, "wop_id": WOP, "repository_identity": {},
                "invocation_count": 1, "mission_admission_executed": False,
            }, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = json.loads(receipt_path.read_text())
        receipt["next_action"] = "START_EXECUTION"
        receipt["receipt_digest"] = _digest({key: value for key, value in receipt.items() if key != "receipt_digest"})
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        contradiction = self.invoke(runtime, "mission", "next", MISSION, "--json")
        self.assertEqual(contradiction.returncode, 78)
        self.assertIn("CANONICAL_NEXT_ACTION_CONTRADICTION", {item["code"] for item in json.loads(contradiction.stdout)["blockers"]})

    def test_ambiguous_receipts_fail_closed(self) -> None:
        _, _, runtime = self.submitted()
        receipt = next((runtime / "submissions/receipts").glob("*.json"))
        shutil.copy2(receipt, receipt.with_name("duplicate-receipt.json"))
        result = self.invoke(runtime, "mission", "show", MISSION, "--json")
        self.assertEqual(result.returncode, 78)
        self.assertEqual(json.loads(result.stdout)["blockers"][0]["code"], "MISSION_IDENTITY_AMBIGUOUS")

    def test_historical_projection_cannot_override_current_p2_state(self) -> None:
        _, _, runtime = self.submitted()
        legacy = runtime / "mission-executions" / "historical.json"
        legacy.write_text(json.dumps({"mission_id": MISSION, "state": "CLOSED"}) + "\n", encoding="utf-8")
        result = self.invoke(runtime, "mission", "snapshot", MISSION, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["lifecycle_state"], "ADMISSION_REQUESTED")
        self.assertEqual(value["canonical_projection"], "P2_SUBMISSION_RECEIPT")
        self.assertEqual(value["historical_projections"], "PRESERVED_AND_EXCLUDED_FROM_CURRENT_STATE")

    def test_unrelated_mission_is_not_discovered(self) -> None:
        self.assertEqual(mission_view(Path(tempfile.mkdtemp()) / "submissions", "UNRELATED-MISSION-01")["result"], "MISSION_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
