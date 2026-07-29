#!/usr/bin/env python3
"""Isolated qualification for verification-first Zeus gate approval."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/lib/emp/gate_approval.py"
sys.path.insert(0, str(ROOT))
from scripts.lib.emp import gate_decision  # noqa: E402
SPEC = importlib.util.spec_from_file_location("gate_approval", MODULE_PATH)
gate_approval = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = gate_approval
SPEC.loader.exec_module(gate_approval)

RUN_ID = "PMCT-20260726T220148Z-042c4ea4c6a3"
HEAD = "a" * 40


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GateApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repository = root / "repository"
        self.wop = root / "wop"
        self.runtime = self.repository / "runtime"
        self.run = self.runtime / RUN_ID
        self.run.mkdir(parents=True)
        (self.wop / "bin").mkdir(parents=True)
        (self.wop / "operator-approvals").mkdir()
        shutil.copy2(
            Path("/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP/bin/record-operator-approval"),
            self.wop / "bin/record-operator-approval",
        )
        (self.wop / "bin/resume-status").write_text(
            "#!/usr/bin/env bash\nprintf 'RESUME_STATUS=PAUSED\\n'\n"
        )
        (self.wop / "bin/check-gate-eligibility").write_text(
            "#!/usr/bin/env bash\n"
            "prev=$(printf '%02d' $((10#${1#OA-} - 1)))\n"
            "root=$(dirname \"$0\")/../operator-approvals\n"
            "repo=$(cd \"$root/../../repository\" && pwd)\n"
            "head=$(git -C \"$repo\" rev-parse HEAD)\n"
            "receipt=\n"
            "for candidate in \"$root/OA-${prev}.approved\" "
            "\"$root/OA-${prev}\"/*.approved; do\n"
            "  test -f \"$candidate\" || continue\n"
            "  test \"$(sed -n 's/^approved_head=//p' \"$candidate\")\" = \"$head\" "
            "|| continue\n"
            "  receipt=$candidate\n"
            "done\n"
            "if test -n \"$receipt\"; then\n"
            "  printf 'ELIGIBILITY=CONDITIONALLY_ELIGIBLE\\n'\n"
            "  exit 0\n"
            "fi\n"
            "printf 'BLOCKING_REASON=OA-%s_OPERATOR_ACCEPTANCE_REQUIRED\\n' \"$prev\" >&2\n"
            "exit 77\n"
        )
        for script in (self.wop / "bin").iterdir():
            script.chmod(0o755)
        subprocess.run(["git", "init", "-q", self.repository], check=True)
        subprocess.run(
            ["git", "-C", self.repository, "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", self.repository, "config", "user.name", "Test"],
            check=True,
        )
        (self.repository / "baseline").write_text("qualified\n")
        subprocess.run(["git", "-C", self.repository, "add", "baseline"], check=True)
        subprocess.run(["git", "-C", self.repository, "commit", "-qm", "baseline"], check=True)
        self.head = subprocess.run(
            ["git", "-C", self.repository, "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        result = {
            "schema_version": 1,
            "gate": "OA-01",
            "run_id": RUN_ID,
            "result": "PASS",
            "reasons": [
                "observable demonstration completed; manual approval remains required"
            ],
            "manual_review_required": True,
        }
        manifest = {
            "schema_version": 1,
            "gate": "OA-01",
            "run_id": RUN_ID,
            "result": "PASS",
            "repository": str(self.repository),
            "head": self.head,
            "implementation_baseline": self.head,
            "published_baseline": self.head,
            "active_authority_publication": "AUTHORITY-PUBLICATION-FIXTURE",
            "evidence_digest": "b" * 64,
            "completed_at": "2026-07-26T00:00:00Z",
        }
        (self.run / "capability-result.json").write_text(json.dumps(result))
        (self.run / "run-manifest.json").write_text(json.dumps(manifest))
        (self.run / "COMPLETE").write_text("PMCT_COMPLETION_MARKER=COMPLETE\n")
        artifacts = ["capability-result.json", "run-manifest.json", "COMPLETE"]
        (self.run / "artifacts.sha256").write_text(
            "".join(f"{digest(self.run / name)}  {name}\n" for name in artifacts)
        )
        self.state = (
            self.repository
            / "engineering/runtime/pmct/capability-state.yaml"
        )
        self.state.parent.mkdir(parents=True)
        self.state.write_text(yaml.safe_dump({
            "overall_result": "NOT_READY",
            "last_evaluated_gate": "OA-01",
            "last_run_id": "PMCT-20260725T000000Z-000000000000",
            "updated_at": "2026-07-25T00:00:00Z",
            "gates": {
                "OA-01": {
                    "status": "PASS",
                    "reason": "prior qualified run",
                    "implementation_status": "COMPLETE",
                    "codex_validation": "PASS",
                    "operator_verification": "PENDING",
                    "operator_acceptance": "NOT_RECORDED",
                    "gate_status": "AWAITING_OPERATOR_VERIFICATION",
                },
                "OA-02": {
                    "status": "NOT_READY",
                    "reason": "not yet evaluated",
                },
            },
        }))
        subprocess.run(
            ["git", "-C", self.repository, "add", "baseline",
             "engineering/runtime/pmct/capability-state.yaml"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", self.repository, "commit", "-qm", "baseline"],
            check=True,
        )
        self.head = subprocess.run(
            ["git", "-C", self.repository, "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        manifest["head"] = self.head
        manifest["implementation_baseline"] = self.head
        manifest["published_baseline"] = self.head
        (self.run / "run-manifest.json").write_text(json.dumps(manifest))
        (self.run / "artifacts.sha256").write_text(
            "".join(f"{digest(self.run / name)}  {name}\n" for name in artifacts)
        )
        (self.wop / "README.md").write_text("fixture\n")
        (self.wop / "MANIFEST.sha256").write_text(
            f"{digest(self.wop / 'README.md')}  README.md\n"
        )
        self.service = gate_approval.GateApprovalService(
            self.repository,
            self.wop,
            runtime=self.runtime,
            capability_state=self.state,
            operator="fixture-operator",
            clock=lambda: datetime(2026, 7, 26, tzinfo=timezone.utc),
            authority_binding={
                "head": self.head,
                "published_baseline": self.head,
                "active_authority_publication": "AUTHORITY-PUBLICATION-FIXTURE",
            },
        )

    def receipt(self) -> Path:
        receipts = self.service._receipt_paths("OA-01")
        self.assertEqual(len(receipts), 1)
        return receipts[0]

    def write_qualified_capability_reconciliation(self) -> None:
        state = yaml.safe_load(self.state.read_text())
        result = json.loads((self.run / "capability-result.json").read_text())
        manifest = json.loads((self.run / "run-manifest.json").read_text())
        gate = state["gates"]["OA-01"]
        gate["status"] = result["result"]
        gate["reason"] = "; ".join(result["reasons"])
        gate["codex_validation"] = "PASS"
        gate["gate_status"] = "AWAITING_OPERATOR_VERIFICATION"
        state["last_run_id"] = RUN_ID
        state["last_evaluated_gate"] = "OA-01"
        state["updated_at"] = manifest["completed_at"]
        state["overall_result"] = "NOT_READY"
        self.state.write_text(yaml.safe_dump(state, sort_keys=False))

    def decision_summary(self):
        return {
            "gate": "OA-01", "verification_status": "PASS",
            "verification_work_package": "P2-032",
            "repository_head": self.head, "published_baseline": self.head,
            "baseline_match": True,
            "active_publication": "AUTHORITY-PUBLICATION-FIXTURE",
            "pmct_result": "PASS", "pmct_run": RUN_ID,
            "current_binding_count": 1, "evidence_digest": "b" * 64,
            "dispatcher_state": "DISABLED", "oa02_state": "BLOCKED",
            "progressive_wop_state": "PAUSED",
            "current_lifecycle_next_action": "RECORD_OA-01_OPERATOR_ACCEPTANCE",
            "operator": "fixture-operator",
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_first_approval_prints_verification_and_records_nothing(self):
        with patch("builtins.print") as output:
            code = gate_approval.approve_command(
                self.service, "OA-01", assume_yes=False
            )
        self.assertEqual(code, 77)
        text = "\n".join(" ".join(map(str, call.args)) for call in output.call_args_list)
        self.assertIn("zeus verify OA-01", text)
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())

    def test_verification_is_durable_and_not_acceptance(self):
        binding = self.service.verify("OA-01")
        record = self.service.verification_record(binding)
        self.assertEqual(record["verification_result"], "PASS")
        self.assertEqual(record["operator"], "fixture-operator")
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())

    def test_second_approval_affirmative_records_and_verifies_receipt(self):
        self.service.verify("OA-01")
        result, _ = self.service.approve(
            "OA-01", assume_yes=False, confirmation=lambda _: "y"
        )
        self.assertEqual(result, "RECORDED")
        receipt = self.receipt()
        fields = dict(line.split("=", 1) for line in receipt.read_text().splitlines())
        self.assertEqual(fields["confirmation_mode"], "INTERACTIVE")
        self.assertEqual(fields["evidence_digest"], "b" * 64)
        self.assertIn("operator_verification_record", fields)
        self.assertTrue(receipt.with_suffix(".approved.sha256").is_file())

    def test_rejection_is_integrity_protected_idempotent_and_not_acceptance(self):
        self.service.verify("OA-01")
        with patch.object(gate_decision, "review", return_value=self.decision_summary()):
            first, replay = gate_decision.decide(
                self.service, "OA-01", reject=True, rationale="not ready",
                at=None, assume_yes=True,
            )
            second, replay_second = gate_decision.decide(
                self.service, "OA-01", reject=True, rationale="not ready",
                at=None, assume_yes=True,
            )
        self.assertEqual(first["decision"], "REJECT")
        self.assertFalse(replay)
        self.assertTrue(replay_second)
        self.assertEqual(first, second)
        self.assertFalse(self.service.receipt_exists("OA-01"))
        decision = next((self.wop / "operator-decisions/OA-01").glob("*.json"))
        self.assertTrue(decision.with_suffix(".json.sha256").is_file())

    def test_acceptance_reuses_receipt_and_conflicting_reject_fails(self):
        self.service.verify("OA-01")
        with patch.object(gate_decision, "review", return_value=self.decision_summary()):
            accepted, replay = gate_decision.decide(
                self.service, "OA-01", reject=False, rationale="qualified",
                at=None, assume_yes=True,
            )
            self.assertEqual(accepted["decision"], "ACCEPT")
            self.assertFalse(replay)
            self.assertTrue(self.service.receipt_exists("OA-01"))
            with self.assertRaisesRegex(
                gate_decision.GateApprovalError, "conflicting"
            ):
                gate_decision.decide(
                    self.service, "OA-01", reject=True, rationale="changed",
                    at=None, assume_yes=True,
                )

    def test_second_invocation_displays_confirmation_boundary_before_prompt(self):
        self.service.verify("OA-01")
        events = []

        def confirmation(prompt):
            events.append(prompt)
            return "n"

        with patch("builtins.print", side_effect=lambda *args, **_: events.append(" ".join(map(str, args)))):
            code = gate_approval.approve_command(
                self.service, "OA-01", assume_yes=False, confirmation=confirmation
            )
        self.assertEqual(code, 0)
        prompt_index = events.index("Approve OA-01? [y/N]: ")
        before = "\n".join(events[:prompt_index])
        self.assertIn("PMCT run: " + RUN_ID, before)
        self.assertIn("Qualified HEAD: " + self.head, before)
        self.assertIn("Verification: PASS", before)
        self.assertIn("Acceptance: NOT_RECORDED", before)

    def test_cancellation_records_nothing(self):
        self.service.verify("OA-01")
        result, _ = self.service.approve(
            "OA-01", assume_yes=False, confirmation=lambda _: ""
        )
        self.assertEqual(result, "CANCELLED")
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())

    def test_terminal_interruption_cancels_without_receipt(self):
        self.service.verify("OA-01")

        def interrupted(_):
            raise KeyboardInterrupt

        result, _ = self.service.approve(
            "OA-01", assume_yes=False, confirmation=interrupted
        )
        self.assertEqual(result, "CANCELLED")
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())

    def test_stale_head_invalidates_verification(self):
        self.service.verify("OA-01")
        (self.repository / "next").write_text("change\n")
        subprocess.run(["git", "-C", self.repository, "add", "next"], check=True)
        subprocess.run(["git", "-C", self.repository, "commit", "-qm", "next"], check=True)
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "HEAD mismatch"):
            self.service.approve("OA-01", assume_yes=True)

    def test_evidence_digest_change_invalidates_verification(self):
        binding = self.service.verify("OA-01")
        manifest = json.loads((self.run / "run-manifest.json").read_text())
        manifest["evidence_digest"] = "c" * 64
        (self.run / "run-manifest.json").write_text(json.dumps(manifest))
        artifacts = ["capability-result.json", "run-manifest.json", "COMPLETE"]
        (self.run / "artifacts.sha256").write_text(
            "".join(f"{digest(self.run / name)}  {name}\n" for name in artifacts)
        )
        self.assertIsNone(self.service.verification_record(self.service.binding("OA-01")))
        self.assertIsNotNone(binding)

    def test_wop_digest_change_invalidates_verification(self):
        binding = self.service.verify("OA-01")
        (self.wop / "README.md").write_text("changed fixture\n")
        (self.wop / "MANIFEST.sha256").write_text(
            f"{digest(self.wop / 'README.md')}  README.md\n"
        )
        self.assertIsNone(self.service.verification_record(self.service.binding("OA-01")))
        self.assertIsNotNone(binding)

    def test_invalid_completion_marker_fails(self):
        (self.run / "COMPLETE").write_text("INCOMPLETE\n")
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "completion marker"):
            self.service.verify("OA-01")

    def test_missing_completion_marker_fails(self):
        (self.run / "COMPLETE").unlink()
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "completion marker"):
            self.service.verify("OA-01")

    def test_contract_completion_marker_passes(self):
        binding = self.service.verify("OA-01")
        self.assertEqual(binding.run_id, RUN_ID)

    def test_duplicate_approval_is_rejected(self):
        self.service.verify("OA-01")
        self.service.approve("OA-01", assume_yes=True)
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "already exists"):
            self.service.approve("OA-01", assume_yes=True)

    def test_dirty_tracked_worktree_is_rejected(self):
        (self.repository / "baseline").write_text("dirty\n")
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "worktree"):
            self.service.verify("OA-01")

    def test_exact_pmct_capability_reconciliation_is_accepted(self):
        self.write_qualified_capability_reconciliation()
        binding = self.service.binding("OA-01")
        self.assertEqual(binding.run_id, RUN_ID)

    def test_tampered_pmct_capability_reconciliation_is_rejected(self):
        self.write_qualified_capability_reconciliation()
        state = yaml.safe_load(self.state.read_text())
        state["last_run_id"] = "PMCT-20260726T000000Z-ffffffffffff"
        self.state.write_text(yaml.safe_dump(state, sort_keys=False))
        with self.assertRaisesRegex(
            gate_approval.GateApprovalError, "authenticated PMCT"
        ):
            self.service.binding("OA-01")

    def test_staged_pmct_capability_reconciliation_is_rejected(self):
        self.write_qualified_capability_reconciliation()
        subprocess.run(
            [
                "git", "-C", self.repository, "add",
                "engineering/runtime/pmct/capability-state.yaml",
            ],
            check=True,
        )
        with self.assertRaisesRegex(
            gate_approval.GateApprovalError, "authenticated PMCT"
        ):
            self.service.binding("OA-01")

    def test_invalid_gate_is_rejected(self):
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "invalid gate"):
            self.service.verify("OA-31")

    def test_missing_pass_run_is_rejected(self):
        shutil.rmtree(self.run)
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "no PMCT PASS"):
            self.service.verify("OA-01")

    def test_failed_pmct_run_is_not_a_candidate(self):
        result = json.loads((self.run / "capability-result.json").read_text())
        result["result"] = "FAIL"
        (self.run / "capability-result.json").write_text(json.dumps(result))
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "no PMCT PASS"):
            self.service.resolve_run("OA-01")

    def test_manual_review_contract_is_required(self):
        result = json.loads((self.run / "capability-result.json").read_text())
        result["manual_review_required"] = False
        (self.run / "capability-result.json").write_text(json.dumps(result))
        artifacts = ["capability-result.json", "run-manifest.json", "COMPLETE"]
        (self.run / "artifacts.sha256").write_text(
            "".join(f"{digest(self.run / name)}  {name}\n" for name in artifacts)
        )
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "manual_review_required"):
            self.service.verify("OA-01")

    def test_ambiguous_pass_runs_are_rejected(self):
        self.state.write_text(yaml.safe_dump({"gates": {"OA-01": {"status": "PASS"}}}))
        other = self.runtime / "PMCT-20260726T220149Z-042c4ea4c6a4"
        shutil.copytree(self.run, other)
        result = json.loads((other / "capability-result.json").read_text())
        result["run_id"] = other.name
        (other / "capability-result.json").write_text(json.dumps(result))
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "ambiguous"):
            self.service.resolve_run("OA-01")

    def test_obsolete_pass_runs_are_ignored_for_current_authority_binding(self):
        obsolete = self.runtime / "PMCT-20260726T220149Z-042c4ea4c6a4"
        shutil.copytree(self.run, obsolete)
        result = json.loads((obsolete / "capability-result.json").read_text())
        result["run_id"] = obsolete.name
        (obsolete / "capability-result.json").write_text(json.dumps(result))
        manifest = json.loads((obsolete / "run-manifest.json").read_text())
        manifest.update({
            "run_id": obsolete.name,
            "head": "0" * 40,
            "implementation_baseline": "0" * 40,
            "published_baseline": "1" * 40,
            "active_authority_publication": "AUTHORITY-PUBLICATION-OBSOLETE",
        })
        (obsolete / "run-manifest.json").write_text(json.dumps(manifest))
        self.assertEqual(self.service.resolve_run("OA-01"), self.run)
        verified = self.service.verify("OA-01")
        self.assertEqual(verified.run_id, self.run.name)
        record = json.loads(
            self.service._verification_path("OA-01").read_text(encoding="utf-8")
        )
        self.assertEqual(record["verification_result"], "PASS")
        self.assertEqual(record["pmct_run_id"], self.run.name)
        self.assertEqual(self.service._receipt_paths("OA-01"), [])

    def test_only_obsolete_pass_runs_produce_no_current_candidate(self):
        manifest = json.loads((self.run / "run-manifest.json").read_text())
        manifest["active_authority_publication"] = "AUTHORITY-PUBLICATION-OBSOLETE"
        (self.run / "run-manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "no PMCT PASS"):
            self.service.resolve_run("OA-01")

    def test_yes_mode_requires_verification_and_records_mode(self):
        result, _ = self.service.approve("OA-01", assume_yes=True)
        self.assertEqual(result, "VERIFICATION_REQUIRED")
        self.service.verify("OA-01")
        result, _ = self.service.approve("OA-01", assume_yes=True)
        self.assertEqual(result, "RECORDED")
        receipt = self.receipt().read_text()
        self.assertIn("confirmation_mode=NONINTERACTIVE", receipt)

    def test_successor_preserves_historical_receipt_and_binds_lineage(self):
        historical = self.wop / "operator-approvals/OA-01.approved"
        historical.write_text(
            "gate=OA-01\npmct_run_id=PMCT-20260101T000000Z-000000000000\n"
            f"repository={self.repository}\napproved_head={'0' * 40}\n"
            f"evidence_digest={'1' * 64}\n"
        )
        historical.with_suffix(".approved.sha256").write_text(
            f"{digest(historical)}  {historical.name}\n"
        )
        before = historical.read_bytes()
        self.service.verify("OA-01")
        result, _ = self.service.approve("OA-01", assume_yes=True)
        self.assertEqual(result, "RECORDED")
        self.assertEqual(historical.read_bytes(), before)
        receipts = self.service._receipt_paths("OA-01")
        self.assertEqual(len(receipts), 2)
        successor = receipts[-1].read_text()
        self.assertIn(f"predecessor_receipt={historical}", successor)
        self.assertIn(f"predecessor_receipt_digest={digest(historical)}", successor)

    def test_duplicate_current_binding_rejected_with_historical_preserved(self):
        self.service.verify("OA-01")
        self.service.approve("OA-01", assume_yes=True)
        receipt = self.receipt()
        before = receipt.read_bytes()
        with self.assertRaisesRegex(gate_approval.GateApprovalError, "already exists"):
            self.service.approve("OA-01", assume_yes=True)
        self.assertEqual(receipt.read_bytes(), before)

    def test_broken_successor_lineage_is_not_authoritative(self):
        self.service.verify("OA-01")
        self.service.approve("OA-01", assume_yes=True)
        receipt = self.receipt()
        fields = receipt.read_text().replace(
            "predecessor_receipt=NONE", "predecessor_receipt=/wrong"
        )
        receipt.chmod(0o644)
        receipt.write_text(fields)
        checksum = receipt.with_suffix(".approved.sha256")
        checksum.chmod(0o644)
        checksum.write_text(
            f"{digest(receipt)}  {receipt.name}\n"
        )
        self.assertEqual(self.service._valid_receipts("OA-01"), [])

    def test_verification_checksum_tamper_invalidates_record(self):
        binding = self.service.verify("OA-01")
        path = self.wop / "operator-verifications/OA-01.verification.json"
        record = json.loads(path.read_text())
        record["operator"] = "other"
        path.write_text(json.dumps(record))
        self.assertIsNone(self.service.verification_record(binding))

    def test_operator_identity_change_invalidates_record(self):
        self.service.verify("OA-01")
        other = gate_approval.GateApprovalService(
            self.repository,
            self.wop,
            runtime=self.runtime,
            capability_state=self.state,
            operator="different-operator",
            clock=lambda: datetime(2026, 7, 26, tzinfo=timezone.utc),
            authority_binding={
                "head": self.head,
                "published_baseline": self.head,
                "active_authority_publication": "AUTHORITY-PUBLICATION-FIXTURE",
            },
        )
        binding = other.binding("OA-01")
        self.assertIsNone(other.verification_record(binding))

    def test_binding_change_after_confirmation_is_rejected(self):
        self.service.verify("OA-01")

        def mutate_wop(_):
            (self.wop / "README.md").write_text("changed after prompt\n")
            (self.wop / "MANIFEST.sha256").write_text(
                f"{digest(self.wop / 'README.md')}  README.md\n"
            )
            return "y"

        with self.assertRaisesRegex(
            gate_approval.GateApprovalError, "binding changed"
        ):
            self.service.approve(
                "OA-01", assume_yes=False, confirmation=mutate_wop
            )
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())

    def test_success_reports_only_conditional_next_gate_and_never_executes_it(self):
        self.service.verify("OA-01")
        with patch("builtins.print") as output:
            code = gate_approval.approve_command(
                self.service, "OA-01", assume_yes=True
            )
        self.assertEqual(code, 0)
        text = "\n".join(" ".join(map(str, call.args)) for call in output.call_args_list)
        self.assertIn("OA-02_ELIGIBILITY=CONDITIONALLY_ELIGIBLE", text)
        self.assertIn("NEXT_ACTION=RUN_OA-02_PRE_EXECUTION_VERIFICATION", text)
        self.assertNotIn("RUN OA-02", text)

    def test_failure_is_a_return_code_not_parent_shell_exit(self):
        environment = os.environ.copy()
        environment.update({
            "ZEUS_TESTING": "1",
            "ZEUS_GATE_REPOSITORY": str(self.repository),
            "ZEUS_GATE_WOP": str(self.wop),
            "ZEUS_GATE_PMCT_RUNTIME": str(self.runtime / "missing"),
            "ZEUS_GATE_CAPABILITY_STATE": str(self.state),
            "ZEUS_OPERATOR_STATE": str(self.repository / "operator.json"),
            "ZEUS_PROGRESSIVE_OA": "0",
        })
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "verify", "OA-01"],
            env=environment, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL:", result.stderr)
        record = json.loads(
            (self.wop / "operator-verifications/OA-01.verification.json").read_text()
        )
        self.assertEqual(record["verification_result"], "FAIL")
        self.assertFalse((self.wop / "operator-approvals/OA-01.approved").exists())


if __name__ == "__main__":
    unittest.main()
