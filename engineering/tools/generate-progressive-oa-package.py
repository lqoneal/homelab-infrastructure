#!/usr/bin/env python3
"""Generate the controlled, reviewable Progressive OA package assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001"

TITLES = [
    "Authoritative Baseline and Repository Identity",
    "Controlled Mission Authority",
    "Mission Contract Discovery",
    "Project and Operational Context Reconstruction",
    "Mission Staging Contract",
    "Mission Eligibility Evaluation",
    "Mission Selection",
    "WOP Resolution",
    "WOP Integrity and Admission",
    "Execution Context and Lease",
    "Qualified-Agent Registry",
    "Agent Selection",
    "Dispatch Preparation",
    "Human Dispatch Authorization",
    "Controlled Dispatch",
    "Execution Start and EENS Observation",
    "Gate and Handoff Progress Monitoring",
    "Approval Enforcement During Execution",
    "Evidence Capture",
    "Evidence Integrity and Provenance",
    "Independent Result Qualification",
    "Failure and Corrective-Work Generation",
    "Safe Interruption",
    "Resume and Idempotent Continuation",
    "Controlled State Reconciliation",
    "Completion Determination",
    "Operator Acceptance",
    "Mission Closeout",
    "End-to-End Representative Mission",
    "Operational Alpha Qualification and Declaration Preparation",
]

OBJECTIVES = [
    "Prove that Zeus operates from one identified, synchronized, integrity-valid repository and qualified baseline.",
    "Prove that no mission may execute without valid, current, discoverable authority.",
    "Prove deterministic discovery of exactly one applicable Mission Contract.",
    "Prove repository-only reconstruction of current project, phase, work, authority, and runtime context.",
    "Prove candidate missions are staged with stable identity, objective, scope, dependencies, priority, and state.",
    "Prove deterministic classification of eligible, blocked, deferred, and ineligible missions.",
    "Prove Zeus selects only an eligible staged mission according to controlled priority and policy.",
    "Prove deterministic resolution of the selected mission to one immutable WOP.",
    "Prove package integrity, schema validity, admission evaluation, and fail-closed rejection.",
    "Prove bounded execution context, principal identity, authority lease, expiry, and revocation behavior.",
    "Prove integrity-bound qualification and repository-preserving registration of execution agents.",
    "Prove Zeus selects only an agent qualified for repository, mission class, tools, and execution profile.",
    "Prove deterministic creation of a dispatch candidate without beginning execution.",
    "Prove explicit authorization, rejection, expiration, and replay-safe dispatch authorization receipts.",
    "Prove Zeus dispatches the admitted WOP to the selected qualified agent exactly once.",
    "Prove durable execution-start state and EENS lifecycle notification.",
    "Prove Zeus observes progress, handoffs, checkpoints, and failures through EENS.",
    "Prove protected actions pause for valid operator approval and cannot bypass the approval boundary.",
    "Prove append-only capture of commands, outputs, state, timestamps, identities, checksums, and completion markers.",
    "Prove evidence binding to repository commit, authority, mission, WOP, execution, gate, and agent.",
    "Prove a qualifier independent of the execution agent evaluates implementation and evidence.",
    "Prove fail-closed handling and bounded generation of separately authorized corrective work.",
    "Prove durable pause behavior without inferred completion or duplicated effects.",
    "Prove reconstruction from durable state and continuation from the first incomplete operation.",
    "Prove reconciliation of Zeus, EMP, PMCT, EENS, Project State, Work Registry, EOS, and controlled records.",
    "Prove mission implementation completion is evidence-calculated and distinct from acceptance.",
    "Prove explicit acceptance or rejection bound to the exact qualified result and evidence manifest.",
    "Prove completion reporting, final reconciliation, execution closure, and removal from active work.",
    "Prove the complete lifecycle using a bounded representative mission from staging through accepted closeout.",
    "Prove OA-01 through OA-29 remain valid, produce a candidate baseline, and prepare separately authorized declaration and freeze.",
]

SOURCES = [
    "docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md",
    "engineering/execution/execution-interface.yaml",
    "engineering/operations/zeus-operational-alpha-progress.md",
    "engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md",
    "engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml",
    "engineering/operations/zeus-mission-admission-runtime.md",
    "engineering/operations/zeus-mission-execution-runtime.md",
    "engineering/operations/zeus-operator-interface.md",
    "services/eens/README.md",
    "docs/project/PROJ-0001-PROJECT_STATE.md",
    "engineering/registry/work-registry.yaml",
]


def gate(number: int) -> dict:
    gate_id = f"OA-{number:02d}"
    prior = [] if number == 1 else [f"OA-{number - 1:02d}: ACCEPTED"]
    next_gate = f"OA-{number + 1:02d}" if number < 30 else "SEPARATELY_AUTHORIZED_OA_DECLARATION"
    return {
        "gate_id": gate_id,
        "sequence": number,
        "title": TITLES[number - 1],
        "mission_objective": OBJECTIVES[number - 1],
        "capability_being_established": TITLES[number - 1],
        "rationale": f"{TITLES[number - 1]} is a cumulative prerequisite for a trustworthy supervised Operational Alpha lifecycle.",
        "inherited_design_requirements": [
            "Preserve existing Zeus, EMP, EENS, WOP, PMCT, authority, evidence, recovery, reconciliation, and execution-interface semantics.",
            "Use owning interfaces; never infer authority, acceptance, completion, or reconciliation.",
            "Retain prior OA artifacts only as supporting historical evidence; confer no new-gate status.",
        ],
        "authoritative_source_references": SOURCES,
        "entry_prerequisites": prior + [
            "package admission receipt integrity PASS",
            "repository identity and authority bindings current",
            "exactly this gate is the first incomplete eligible gate",
        ],
        "required_implementation_work": [
            f"Implement or reconcile the production capability needed to satisfy {gate_id}.",
            "Add deterministic positive, negative, replay, interruption, and cumulative regression tests.",
            "Persist append-only evidence and reconcile every affected controlled record.",
        ],
        "prohibited_effects": [
            "begin any later gate",
            "inherit prior OA acceptance or completion",
            "self-approve or infer operator acceptance",
            "mutate historical OA evidence",
            "declare Operational Alpha or freeze the baseline",
        ],
        "positive_test_cases": [f"Demonstrate {OBJECTIVES[number - 1]} through the authoritative Zeus interface."],
        "negative_and_fail_closed_test_cases": [
            "Reject missing, malformed, ambiguous, unauthorized, stale, mismatched, and incomplete inputs without state advance.",
            "Prove later gates remain ineligible and no protected external effect occurs.",
        ],
        "idempotency_and_replay_tests": [
            "Repeat identical observations and requests; prove stable result and no duplicate transition, receipt, evidence, event, or dispatch."
        ],
        "safety_and_recovery_tests": [
            "Interrupt before and after each durable boundary; preserve incomplete state and resume at the first incomplete operation."
        ],
        "regression_suite": [f"OA-01 through {gate_id}", "scripts/tests", "engineering/tests/zeus-operational-alpha/tests"],
        "required_evidence": [
            "repository identity, branch, exact HEAD, upstream, and working-tree inventory",
            "authority, mission, WOP, execution, gate, agent, and timestamp bindings",
            "commands, stdout, stderr, exit codes, assertions, and checksums",
            "positive, negative, replay, interruption, recovery, and cumulative regression results",
            "controlled-record reconciliation report and VERIFIED marker",
        ],
        "exact_success_criteria": [
            OBJECTIVES[number - 1],
            "all required tests PASS and all negative cases fail closed",
            "evidence manifest integrity PASS",
            "records reconcile with no conflict",
            "operator acceptance receipt is valid before next-gate eligibility",
        ],
        "manual_verification_procedure": f"gates/{gate_id}/verification.md",
        "operator_acceptance_procedure": [
            f"zeus approve {gate_id} --operator OPERATOR",
            f"zeus gate receipt {gate_id}",
            "zeus resume",
        ],
        "state_transitions": [
            "PENDING -> IMPLEMENTATION_REQUIRED -> AWAITING_OPERATOR_VERIFICATION",
            "AWAITING_OPERATOR_VERIFICATION -> ACCEPTED | REJECTED",
            f"ACCEPTED -> enable {next_gate}",
            "failure, stale authority, invalid evidence, conflict, or interruption -> STOPPED_FAIL_CLOSED",
        ],
        "records_reconciled": ["Zeus runtime", "EMP", "PMCT", "EENS", "Project State", "Work Registry", "EOS", "controlled documents"],
        "completion_marker": f"runtime/evidence/{gate_id}/VERIFIED plus integrity-valid operator decision receipt",
        "next_gate_enabled": next_gate,
    }


def verification_guide(item: dict) -> str:
    gid = item["gate_id"]
    next_id = item["next_gate_enabled"]
    return f"""# {gid} Operator Verification Guide

## Intent and implementation

This gate is intended to {item['mission_objective'][0].lower() + item['mission_objective'][1:]}
The implementation procedure and evidence manifest describe the exact change made.
Every check is necessary to bind the observed behavior to the admitted package,
current repository, authority, agent, and cumulative predecessor state.

## Prerequisites

The package manifest and admission receipt must validate; `{gid}` must be the sole
active gate; the repository and EOS must be synchronized; gate implementation must
be complete; and the evidence directory must contain the generated manifest.

## Steps and expected results

1. Run `zeus gate show {gid}`. Expect JSON with `gate_id` equal to `{gid}` and the
   complete contract. Any missing field is FAIL.
2. Run `zeus gate objective {gid}`. Expect the objective in this guide. A different
   objective is FAIL.
3. Run `zeus gate evidence {gid}`. Expect the evidence template and runtime directory.
4. Run `zeus verify {gid}`. Expect all positive, negative, replay, recovery, and
   cumulative checks to report PASS and create `runtime/evidence/{gid}/VERIFIED`.
5. Run `scripts/engctl repository health`, `scripts/engctl eos sync-validate`,
   `scripts/engctl registry validate`, and `scripts/engctl validate`. Expect PASS.
6. Run `git status --short --branch` and `git rev-parse HEAD`. Expect the documented
   branch/commit and only the gate's authorized publication set.
7. Run `zeus explain {gid}` and inspect every file returned by
   `zeus gate evidence {gid}`. Confirm checksums, identities, timestamps, exit codes,
   assertions, reconciliation, and the `VERIFIED` marker.

PASS requires every expected result and no unexplained mutation. FAIL includes any
nonzero verification, absent evidence, checksum mismatch, stale authority, unexpected
working-tree path, reconciliation conflict, or later-gate activity.

## Decision and continuation

Reject with `zeus decline {gid} --operator OPERATOR`; this persists a rejection and
stops fail closed. Accept only after PASS with
`zeus approve {gid} --operator OPERATOR`. Confirm the receipt using
`zeus gate receipt {gid}`. Run `zeus resume`; the controller recognizes the receipt
and directly enables `{next_id}` without a new mission authorization. After OA-30,
resume stops at declaration preparation and requests separate declaration/freeze authority.
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gate_items = [gate(number) for number in range(1, 31)]
    specification = {
        "schema_version": 1,
        "document_id": "ZEUS-OA-GATE-SPEC-002",
        "title": "Zeus Operational Alpha Gate Specification",
        "status": "Controlled",
        "mission": "Zeus Operational Alpha",
        "sequence": "OA-01 through OA-30; strictly cumulative; no inherited status",
        "gates": gate_items,
    }
    (OUT / "gate-specification.yaml").write_text(yaml.safe_dump(specification, sort_keys=False, width=110))
    roadmap_lines = [
        "# Zeus Operational Alpha Roadmap",
        "",
        "Controlled ID: ZEUS-OA-ROADMAP-002",
        "Status: Controlled",
        "Supersedes execution sequencing in GH-ZEUS-OA-CERTIFICATION-001 without deleting historical evidence.",
        "",
        "Every gate begins unaccepted. Prior implementation and evidence may support verification but confer no status.",
        "",
        "| Gate | Engineering objective | Enables |",
        "| --- | --- | --- |",
    ]
    trace_lines = [
        "# Operational Alpha Traceability Matrix", "",
        "| Gate | Mission capability | Primary inherited sources | Verification contract |",
        "| --- | --- | --- | --- |",
    ]
    for item in gate_items:
        roadmap_lines.append(f"| {item['gate_id']} | {item['mission_objective']} | {item['next_gate_enabled']} |")
        trace_lines.append(f"| {item['gate_id']} | {item['capability_being_established']} | PROC-0001; execution-interface; PMCT; Zeus progress | `gate-specification.yaml` and `gates/{item['gate_id']}/verification.md` |")
        directory = OUT / "gates" / item["gate_id"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "objective.yaml").write_text(yaml.safe_dump({
            "gate_id": item["gate_id"], "title": item["title"],
            "mission_objective": item["mission_objective"],
            "operational_alpha_trace": "ZEUS-OA-GATE-SPEC-002",
            "status": "UNSTARTED",
        }, sort_keys=False))
        (directory / "implementation.md").write_text(
            f"# {item['gate_id']} Implementation Procedure\n\n"
            f"Implement only the work necessary to satisfy: {item['mission_objective']}\n\n"
            "Follow package preflight, preserve historical evidence, execute the specified positive/negative/replay/recovery tests, "
            "capture append-only evidence, reconcile affected records, publish only where repository procedures permit, then set "
            "`AWAITING_OPERATOR_VERIFICATION`. Do not record acceptance or begin the next gate.\n"
        )
        (directory / "verification.md").write_text(verification_guide(item))
        (directory / "evidence-template.yaml").write_text(yaml.safe_dump({
            "schema_version": 1, "package_id": "GH-ZEUS-OA-PROGRESSIVE-001",
            "gate_id": item["gate_id"], "status": "UNSTARTED",
            "bindings": {"repository": None, "commit": None, "authority": None, "mission": None, "wop": None, "execution": None, "agent": None},
            "tests": {"positive": [], "negative": [], "replay": [], "recovery": [], "regression": []},
            "commands": [], "artifacts": [], "reconciliation": {}, "completion_marker": None,
        }, sort_keys=False))
    (OUT / "ROADMAP.md").write_text("\n".join(roadmap_lines) + "\n")
    (OUT / "TRACEABILITY.md").write_text("\n".join(trace_lines) + "\n")
    runtime_state = OUT / "runtime/state.json"
    if not runtime_state.exists():
        runtime_state.parent.mkdir(parents=True, exist_ok=True)
        runtime_state.write_text(json.dumps({
            "schema_version": 1,
            "package_id": "GH-ZEUS-OA-PROGRESSIVE-001",
            "status": "READY",
            "active_gate": "OA-01",
            "gates": {
                f"OA-{number:02d}": {"state": "PENDING", "acceptance_receipt": None}
                for number in range(1, 31)
            },
        }, indent=2, sort_keys=True) + "\n")
    manifest_paths = sorted(path for path in OUT.rglob("*") if path.is_file() and path.name != "MANIFEST.sha256" and "runtime" not in path.parts)
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(OUT)}" for path in manifest_paths]
    (OUT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
