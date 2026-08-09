#!/usr/bin/env python3
"""GAP-002 proof for the receipt-backed canonical lifecycle resolver."""

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
SOURCE = ROOT / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
WOP = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"

sys.path.insert(0, str(ROOT))

from scripts.lib.emp.bootstrap_boundary import bootstrap  # noqa: E402
from scripts.lib.emp.canonical_lifecycle_resolver import resolve  # noqa: E402
from scripts.lib.emp import dispatch_foundation, execution_start, provider_invocation, provider_selection, provider_session  # noqa: E402
from scripts.lib.emp.mission_admission_boundary import admit  # noqa: E402
from scripts.lib.emp.wop_canonicalization import canonicalize  # noqa: E402


class CanonicalLifecycleResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holder = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="zeus-wave1-chain-")))
        self.source = self.holder / "source-wop.md"
        shutil.copy2(SOURCE, self.source)
        canonicalize(self.source, ROOT)
        self.runtime = self.holder / "runtime"
        self.environment = {
            **os.environ,
            "ZEUS_RUNTIME_ROOT": str(self.runtime),
            "ZEUS_NO_INTRO": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "submit", str(self.source), "--repository", str(ROOT), "--json"],
            cwd=ROOT, env=self.environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.submission = json.loads(result.stdout)

    @staticmethod
    def digest_tree(root: Path) -> dict[str, str]:
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()
        }

    def test_p2_is_the_first_contiguous_canonical_state(self) -> None:
        before = self.digest_tree(self.runtime)
        value = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["lifecycle_state"], "ADMISSION_REQUESTED")
        self.assertEqual(value["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")
        self.assertEqual(value["canonical_state_source"], "P2_SUBMISSION_RECEIPT")
        self.assertEqual(value["legacy_stage1_projection"]["classification"], "NONE")
        self.assertEqual(before, self.digest_tree(self.runtime))

    def test_p3_and_p4_extend_one_identity_bound_chain(self) -> None:
        admission = admit(
            self.submission["receipt_path"], wop=self.source, repository=ROOT, runtime_root=self.runtime,
        )
        p3 = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(p3["result"], "PASS")
        self.assertEqual(p3["lifecycle_state"], "ADMITTED")
        self.assertEqual(p3["next_authorized_action"], "EVALUATE_BOOTSTRAP_ELIGIBILITY")
        self.assertEqual(len(p3["lifecycle_chain"]), 2)
        bootstrap(admission["admission_receipt"]["path"], repository=ROOT, runtime_root=self.runtime)
        p4 = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(p4["result"], "PASS")
        self.assertEqual(p4["lifecycle_state"], "AWAITING_EXECUTION_DISPATCH")
        self.assertEqual(p4["next_authorized_action"], "EVALUATE_EXECUTION_PROVIDER")
        self.assertEqual(len(p4["lifecycle_chain"]), 3)
        self.assertEqual(p4["mission_id"], MISSION)
        self.assertEqual(p4["wop_id"], WOP)
        self.assertFalse(p4["provider_selected"])
        self.assertFalse(p4["execution_started"])

    def test_exact_replay_is_read_only_and_deterministic(self) -> None:
        admission = admit(
            self.submission["receipt_path"], wop=self.source, repository=ROOT, runtime_root=self.runtime,
        )
        bootstrap(admission["admission_receipt"]["path"], repository=ROOT, runtime_root=self.runtime)
        before = self.digest_tree(self.runtime)
        first = resolve(ROOT, MISSION, runtime_root=self.runtime)
        second = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(first, second)
        self.assertEqual(before, self.digest_tree(self.runtime))

    def test_duplicate_canonical_transition_fails_closed(self) -> None:
        admission = admit(
            self.submission["receipt_path"], wop=self.source, repository=ROOT, runtime_root=self.runtime,
        )
        source = self.runtime / "admissions" / f"{admission['admission_id']}.json"
        shutil.copy2(source, source.with_name("duplicate-admission.json"))
        value = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CANONICAL_TRANSITION_CARDINALITY_CONFLICT")

    def test_historical_stage1_projection_cannot_advance_canonical_state(self) -> None:
        legacy = self.runtime / "stage1" / "historical.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text(json.dumps({"mission_id": MISSION, "wop_id": "LEGACY-WOP", "state": "CLOSED"}) + "\n", encoding="utf-8")
        value = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["lifecycle_state"], "ADMISSION_REQUESTED")
        self.assertEqual(value["legacy_stage1_projection"]["current_state_authority"], "EXCLUDED_FROM_CANONICAL_CHAIN")

    def test_unrelated_malformed_projection_does_not_affect_target(self) -> None:
        unrelated = self.runtime / "admissions" / "unrelated-malformed.json"
        unrelated.parent.mkdir(parents=True, exist_ok=True)
        unrelated.write_text("not-json\n", encoding="utf-8")
        value = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["mission_id"], MISSION)

    def test_downstream_evidence_without_p2_fails_closed(self) -> None:
        runtime = self.holder / "orphan-runtime"
        (runtime / "admissions").mkdir(parents=True)
        (runtime / "admissions" / "orphan.json").write_text(json.dumps({"mission_id": MISSION}) + "\n", encoding="utf-8")
        value = resolve(ROOT, MISSION, runtime_root=runtime)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CANONICAL_SUBMISSION_MISSING")

    def _establish_full_idle_chain(self) -> dict[str, str]:
        admission = admit(
            self.submission["receipt_path"], wop=self.source, repository=ROOT, runtime_root=self.runtime,
        )
        bootstrap_result = bootstrap(admission["admission_receipt"]["path"], repository=ROOT, runtime_root=self.runtime)
        selection = provider_selection.select(ROOT, MISSION, runtime_root=self.runtime)
        dispatch = dispatch_foundation.create(ROOT, MISSION, runtime_root=self.runtime)
        session = provider_session.create(ROOT, MISSION, runtime_root=self.runtime)
        invocation = provider_invocation.create(ROOT, MISSION, runtime_root=self.runtime)
        execution = execution_start.create(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(selection["result"], "PASS", selection)
        self.assertEqual(dispatch["result"], "PASS", dispatch)
        self.assertEqual(session["result"], "PASS", session)
        self.assertEqual(invocation["result"], "PASS", invocation)
        self.assertEqual(execution["result"], "PASS", execution)
        return {"admission_id": bootstrap_result["admission_id"], "dispatch_id": dispatch["dispatch_id"],
                "provider_session_id": session["provider_session_id"], "provider_invocation_id": invocation["provider_invocation_id"],
                "execution_id": execution["execution_id"], "execution_session_id": execution["execution_session_id"]}

    def test_valid_downstream_receipts_correct_stale_awaiting_projection(self) -> None:
        identities = self._establish_full_idle_chain()
        before = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(before["result"], "PASS")
        self.assertEqual(before["lifecycle_state"], "READY_FOR_CONTROLLED_EXECUTION")
        self.assertEqual(before["canonical_state_source"], "P5_EXECUTION_START_RECEIPT")
        self.assertEqual(before["next_authorized_action"], "BEGIN_CONTROLLED_MISSION_WORK")
        self.assertEqual(before["execution_state"], "READY_FOR_CONTROLLED_EXECUTION")
        for key, expected in identities.items():
            self.assertEqual(before[key], expected)
        self.assertFalse(before["mission_work_started"])
        self.assertFalse(before["repository_work_started"])

        replay = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(before, replay)
        self.assertEqual(before["lifecycle_chain"][-1]["next_action"], "BEGIN_CONTROLLED_MISSION_WORK")

    def test_downstream_digest_binding_and_cardinality_fail_closed(self) -> None:
        self._establish_full_idle_chain()
        dispatch_path = next((self.runtime / "dispatch-receipts").glob("*.json"))
        original = json.loads(dispatch_path.read_text(encoding="utf-8"))
        dispatch_path.write_text(json.dumps({**original, "provider_id": "forged-provider"}, sort_keys=True) + "\n", encoding="utf-8")
        invalid = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(invalid["result"], "FAIL")
        self.assertIn(invalid["blockers"][0]["code"], {"DISPATCH_DIGEST_MISMATCH", "DISPATCH_IDENTITY_MISMATCH"})

        dispatch_path.write_text(json.dumps(original, sort_keys=True) + "\n", encoding="utf-8")
        execution_path = self.runtime / "execution-start-receipts" / "EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e.json"
        if not execution_path.exists():
            execution_path = next((self.runtime / "execution-start-receipts").glob("*.json"))
        duplicate = execution_path.with_name("duplicate-execution-start.json")
        shutil.copy2(execution_path, duplicate)
        conflict = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(conflict["result"], "FAIL")
        self.assertEqual(conflict["blockers"][0]["code"], "EXECUTION_CARDINALITY_CONFLICT")

    def test_historical_and_planning_projections_cannot_override_execution_authority(self) -> None:
        self._establish_full_idle_chain()
        historical = self.runtime / "stage1" / "historical-closed.json"
        historical.parent.mkdir(parents=True, exist_ok=True)
        historical.write_text(json.dumps({"mission_id": MISSION, "state": "CLOSED"}) + "\n", encoding="utf-8")
        unrelated = self.runtime / "dispatches" / "other-mission.json"
        unrelated.parent.mkdir(parents=True, exist_ok=True)
        unrelated.write_text(json.dumps({"mission_id": "OTHER-MISSION", "dispatch_id": "DISPATCH-OTHER"}) + "\n", encoding="utf-8")
        value = resolve(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["lifecycle_state"], "READY_FOR_CONTROLLED_EXECUTION")
        self.assertEqual(value["next_authorized_action"], "BEGIN_CONTROLLED_MISSION_WORK")
        self.assertEqual(value["legacy_stage1_projection"]["current_state_authority"], "EXCLUDED_FROM_CANONICAL_CHAIN")
        self.assertFalse(value["mission_work_started"])
        self.assertFalse(value["repository_work_started"])


if __name__ == "__main__":
    unittest.main()
