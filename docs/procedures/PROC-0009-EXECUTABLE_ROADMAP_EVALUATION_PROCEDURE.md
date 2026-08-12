---
document_id: PROC-0009
title: Executable Roadmap Evaluation Procedure
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-08-09
last_updated: 2026-08-09
phase: Engineering System Convergence C02 Corrective
domain: Engineering Platform Planning and Execution
classification: Engineering Procedure
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Homelab Operator
approval_reference: EXECUTABLE ROADMAP STANDARDIZATION AND ESC-ROADMAP-001 HARDENING directive
approval_date: 2026-08-09
persistence_status: Pending
source_of_truth: true
semantic_validation_profile: Procedure
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: implements
    target: STD-0006
  - type: conforms_to
    target: SPEC-0001
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROJ-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - roadmap
  - evaluation
  - execution-sufficiency
  - fail-closed
  - cold-resume
---

# Executable Roadmap Evaluation Procedure

## Purpose

This procedure defines the repeatable, read-only method for evaluating an
engineering roadmap against STD-0006 and recording whether it is structurally
valid, execution-sufficient, and executable.

It evaluates contracts and evidence. It does not authorize or execute a gate,
approve roadmap content, transition roadmap state, publish controlled records,
synchronize EOS, reconcile a Registry, or repair findings.

## Scope

Use this procedure:

- before first claiming a roadmap is executable;
- after any material roadmap revision;
- before execution resumes when a binding or qualification is stale;
- during cold-resume qualification;
- when a planning-only roadmap is checked for truthful classification; and
- when a gate or terminal continuation contract is suspected to be
  ambiguous.

The generic evaluator may automate deterministic checks. Qualified review
remains required for semantic sufficiency, safety, and warning disposition.

## Entry Conditions and Prerequisites

Before evaluation:

1. resolve the exact repository root, branch, `HEAD`, upstream, and worktree;
2. identify the roadmap root, roadmap ID, and version;
3. verify that the evaluator will operate read-only;
4. identify STD-0006, this procedure, schemas, playbook catalog, state,
   Project State, binding manifest, and persisted evaluation locations;
5. preserve any existing result as evidence rather than editing it in place;
6. confirm no roadmap gate execution or state transition is included in the
   evaluation authority; and
7. stop if repository or roadmap identity is ambiguous.

For a mixed-generation roadmap, resolve each gate's explicit provenance before
schema validation. Use the historical or activation-era schema recorded by a
frozen gate, mark new-standard applicability `NOT_APPLICABLE`, and apply
STD-0006 only to gates marked prospective. Never infer the newest schema from
roadmap revision alone.

A dirty worktree does not automatically prevent evaluation, but the evaluator
shall identify pre-existing changes and shall not overwrite them. If those
changes overlap roadmap sources and make an exact version impossible to
identify, evaluation is blocked.

## Roles

| Role | Responsibility |
| --- | --- |
| Roadmap evaluator | Run deterministic checks, inspect semantic sufficiency, classify warnings/blockers, and produce the evaluation result. |
| Independent reviewer | Reproduce material checks and challenge coverage, artifact, result, authority, transition, and resume determinism. |
| Operator | Accept or reject the qualification and separately authorize any future gate or state transition. |
| Generic evaluator | Produce read-only derived evidence; it has no approval, publication, lifecycle, or execution authority. |

## Evaluation Sequence

### 1. Establish Starting State

Record repository root, branch, `HEAD`, upstream, worktree status, roadmap ID
and version, current gate, completed gates, next authorized action, state and
Project State binding, binding owner, standard/procedure revisions, and all
explicit safety exclusions.

Run the existing structural validator before editing or qualification. If it
fails, record `structural_result: FAIL`, `overall_result: NOT_EXECUTABLE`, and
stop without attempting to infer missing roadmap content.

### 2. Validate Structural Completeness

Validate roadmap, state, gate, result, playbook, and evaluation schemas. Resolve
every gate definition and result locator. Require unique gate IDs, known and
predecessor-only dependencies, consistent current/completed/blocked/pending
sets, coherent result/status/evidence state, exact Project State binding, and
valid source digests.

For each gate, require one deterministic successor or valid terminal semantics.
`next_gate: null` fails unless `terminal.is_terminal: true` and both external
continuation authority and action are non-empty. A non-terminal gate fails if
it declares no successor or an external continuation.

Also require unique immutable gate identities, distinct roadmap-order values,
and identity-based dependency/successor resolution. This permits insertion of
future maturity gates without renumbering existing identities. Verify the
roadmap's pending-only mutation policy, append-only history model, prospective
maturity model, active queue owner, and not-yet-active Zeus staging transfer
condition.

### 3. Resolve Execution Playbooks

Resolve each gate's catalog and playbook ID. Validate the catalog against its
declared schema. Require playbook gate ID to equal the gate definition ID.
Resolve result, review, state transition, persistence, and cold-resume contract
references to exactly one shared contract each.

Missing, duplicated, mismatched, or malformed playbooks are blockers. Large
shared contracts may be referenced; unvalidated prose references do not count.

### 4. Evaluate Procedural Sufficiency

Require a non-empty, ordered gate procedure and a non-empty playbook inventory
method. Confirm a qualified engineer can determine sequence, inputs, expected
outputs, command/safety class, prohibited actions, stop behavior, review, and
result without conversation.

An instruction such as "inventory everything" is insufficient unless the
discovery surfaces, coverage proof, classification, artifacts, cross-checks,
completeness, and result rules make "everything" objective.

### 5. Evaluate Discovery Sufficiency

Inspect every discovery surface:

- `REQUIRED` repository paths shall resolve inside the repository;
- `DYNAMIC` paths shall name a predecessor output or controlled creation
  process and may not hide a missing current input;
- `REFERENCE_ONLY` sources shall identify their non-current authority role;
- globs shall define roots and matching purpose;
- command surfaces shall identify a safe/read-only class; and
- optional surfaces shall state why absence is valid.

The surface set shall cover all objects named by the gate objective and scope.

### 6. Evaluate Coverage Determinism

Require at least one objective coverage rule per gate and coverage evidence for
each rule. Verify rules establish exhaustive enumeration, reconciliation,
unique accounting, graph or flow endpoint resolution, scenario coverage, or an
equivalent deterministic proof.

Require explicit treatment of exclusions and investigation gaps. "No issues
found" or a non-empty inventory does not prove coverage. An unproven required
rule blocks the gate and fails executable qualification.

### 7. Evaluate Classification Determinism

When `classification_required` is true, require non-empty unique finding and
severity vocabularies. Verify artifact classification fields consume that
vocabulary and that unknown values fail. When classification is not applicable,
the playbook shall declare false rather than omit the contract.

Compare the vocabulary with existing controlled equivalents and record a
warning when a new synonym is unnecessary. A missing or unbounded required
vocabulary is a blocker.

### 8. Evaluate Artifact Determinism

For every required structured output, resolve an artifact contract containing
artifact ID, title, format, purpose, minimum record fields, and completeness
key. Verify fields fit the gate subject and support coverage, classification,
evidence, ownership, and result determination.

Reject title-only outputs, generic records that cannot represent the gate's
subject, empty field sets, or contracts without unique completeness keys.
Cross-check the gate's required outputs against artifact contracts and record
any unstructured executive-only output as a warning or blocker according to
materiality.

### 9. Evaluate Evidence Sufficiency

Require evidence for discovery, coverage, artifact conformance, cross-checks,
completeness, result, scope/non-mutation or authorized mutation, review,
transition, persistence, and cold resume as applicable. Confirm evidence
locations are repository-relative and controlled by the gate.

Historical captured evidence is digest-validated without rewriting. Evidence
that cannot be reproduced or bound to the evaluated roadmap version blocks
qualification.

### 10. Evaluate Result Determinism

Require objective rules for `COMPLETE`, `COMPLETE_WITH_FINDINGS`, `BLOCKED`,
and `FAILED`. Confirm findings do not automatically fail an assessment whose
purpose is to discover findings. Confirm missing coverage, unsafe inspection,
or unresolved identity cannot result in completion.

Verify acceptance criteria, fail-closed conditions, artifact completeness, and
result rules lead materially equivalent evaluators to the same result.

### 11. Evaluate Authority and Fail-Closed Boundaries

Verify scope-out, prohibited operations, execution-authority declaration, stop
boundary, and terminal continuation preserve existing authority owners. An
executable roadmap shall not imply current-gate authority, automatic successor
authority, publication authority, or full-roadmap execution.

Verify missing, malformed, stale, conflicting, unknown, unbound, or
contradictory inputs stop safely. Any ambiguity that could authorize mutation,
hide incomplete coverage, or select a result is execution-significant.

### 12. Evaluate Review Boundary

Resolve the review contract and require qualified engineering review plus
operator review where defined. Review shall inspect coverage totals,
uniqueness, gaps, evidence, artifact conformance, result, blockers, scope, and
successor action before state changes.

### 13. Evaluate State-Transition Determinism

Resolve the state-transition contract and verify it orders validation, review,
gate status, state sets and pointers, Project State, binding digests, full
validation, governed persistence, published relationship verification, cold
resume, and successor exposure.

The evaluation may validate this future contract without performing a
transition. A roadmap that depends on an implicit or conversational transition
is not executable.

### 14. Evaluate Persistence

Resolve the persistence contract. Require declared result/evidence locations,
artifact and digest validation, binding updates, truthful pending-versus-
persisted status, governed publication, and post-publication verification.

Local working-tree success shall not be reported as committed, pushed,
published, synchronized, or historically persisted.

### 15. Evaluate Cold Resume

From a fresh shell and without conversation/provider/session identity:

1. run `engctl roadmap validate`;
2. run `engctl roadmap evaluate`;
3. resolve the current gate with `engctl roadmap gate CXX`;
4. run `engctl resume` in its controlled read-only convergence mode;
5. compare program, roadmap ID/version, qualification, completed/current gates,
   blockers, evidence, and next authorized action; and
6. compare pre/post source hashes or equivalent read-only proof.

Repeat over identical inputs and compare semantic output. Run negative fixtures
for missing playbook, classification, artifact schema, completeness test,
terminal continuation, unknown dependency, and state/result contradiction.

### 16. Determine Overall Result

Use `PASS` only when every execution-significant dimension and gate passes.
Use `NOT_EXECUTABLE` when any execution-significant criterion fails.

Warnings may be recorded only for observations that do not undermine
determinism, safety, authority, coverage, evidence, result, transition,
persistence, or resume. A `PLANNING_ONLY` roadmap may be structurally valid;
its overall result remains `NOT_EXECUTABLE` and `executable: false` without
being structurally noncompliant.

Historical and activation-era gate criteria are reported as
`NOT_APPLICABLE` to STD-0006. They do not weaken the prospective qualification
of C03 and later gates. A defect in a current or otherwise active contract is
reported as a blocker or append-only corrective input; evaluation never edits
that active contract to make the result pass.

### 17. Persist the Evaluation Result

Write the schema-valid result to the roadmap's declared evaluation location.
It shall contain:

```yaml
schema_version: 1
roadmap_id: ROADMAP-ID
roadmap_version: VERSION
evaluation_standard:
  standard: STD-0006@1.0
  procedure: PROC-0009@1.0
  playbook_contract: CONTRACT-ID@VERSION
evaluated_at: ISO-8601
structural_result: PASS
procedural_result: PASS
discovery_result: PASS
coverage_result: PASS
classification_result: PASS
artifact_contract_result: PASS
evidence_result: PASS
result_determinism_result: PASS
authority_boundary_result: PASS
fail_closed_result: PASS
review_boundary_result: PASS
state_transition_result: PASS
persistence_result: PASS
cold_resume_result: PASS
gate_results: []
warnings: []
blockers: []
overall_result: PASS
executable: true
```

Bind the exact roadmap version and evaluation sources. A later material change
invalidates this result until reevaluation.

## Command Interface

The canonical interface is:

```text
engctl roadmap validate
engctl roadmap evaluate
engctl roadmap gate CXX
```

`validate` reports structural validity and live execution sufficiency as
separate fields. `evaluate` emits the complete machine-readable live result.
`gate` exposes the gate definition and its playbook reference for inspection.

All three commands are read-only. Successful structure/evaluation returns exit
status 0. Invalid structure, evaluator error, or executable qualification
failure returns nonzero when the command is evaluating an executable claim.
Unknown commands and malformed arguments return nonzero with an error.

## Stop and Failure Conditions

Stop and report `NOT_EXECUTABLE` when:

- repository, roadmap, gate, state, result, evidence, Project State, or binding
  identity is ambiguous or contradictory;
- a required schema, playbook, surface, vocabulary, artifact contract,
  coverage rule, cross-check, completeness test, result rule, review,
  transition, persistence, or cold-resume contract is missing;
- a required discovery surface is absent without valid dynamic semantics;
- terminal continuation is ambiguous;
- a dependency is unknown or non-predecessor;
- coverage cannot be proven;
- an operation's safety or authority class is unknown;
- two evaluators could select materially different results from the contract;
- a persisted qualification belongs to another roadmap version; or
- evaluation would require gate execution, state mutation, publication,
  synchronization, or repair.

An evaluator failure is not a roadmap gate result and shall not advance state.

## Recovery and Resume

If evaluation is interrupted, preserve the last complete starting-state and
dimension evidence. Resume by revalidating repository identity, roadmap
version, worktree, bindings, and all previously completed dimension inputs.
Recompute any dimension whose source changed. Never resume from conversational
claims or a partial result file.

If evaluation fails, correct the roadmap only under separate revision
authority, advance its version, update bindings, and repeat the entire
evaluation. Do not edit the result to `PASS` independently of live checks.

## Outputs and Reconciliation

Required outputs are:

- starting-state record;
- gap or prior-qualification assessment;
- controlled-authority decision;
- resolved execution-contract evidence;
- roadmap-hardening traceability when evaluation follows revision;
- machine-readable evaluation result;
- negative-test and validation report;
- cold-resume test; and
- completion report stopping at operator review.

Reconcile the accepted roadmap version to its state, Project State binding,
binding manifest, controlled-document relationships, and persisted evaluation.
Reconciliation does not include EOS or Registry mutation unless separately
authorized by the authority that owns those stores.

## Evidence and Review

Evidence shall include exact commands, exit status, relevant output, input
versions, schema results, per-gate criteria, warnings, blockers, negative-case
classification, read-only proof, and cold-resume comparison.

The independent reviewer shall reproduce structural, playbook, terminal,
classification, artifact, completeness, state-transition, persistence, and
cold-resume determinations. The operator reviews the complete result and decides
whether to accept the qualification. No automated output makes that decision.

## Validation and Acceptance

This procedure is successfully completed when:

- every STD-0006 dimension has an explicit result;
- every gate has a reproducible criteria result;
- negative cases fail closed;
- planning-only behavior is distinguished from structural failure;
- the live and persisted result agree for the exact roadmap version;
- cold resume is deterministic and read-only;
- warnings and blockers are explicit;
- no gate or state transition was performed; and
- the result stops at operator review.

## Compliance

Use of this procedure is compliant only when the evaluator remains read-only,
does not infer authority, preserves historical evidence, records all failures,
and applies the qualification rule without waivers for execution-significant
ambiguity.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-08-09 | Established the reusable read-only executable-roadmap evaluation sequence, machine-readable result, CLI behavior, negative cases, persistence, review, and cold-resume procedure. |

## Lifecycle Transition History

| Revision | Date | Previous State | New State | Authority |
| --- | --- | --- | --- | --- |
| PROC-0009@1.0 | 2026-08-09 | Draft | Review | Executable Roadmap Standardization operator directive |
| PROC-0009@1.0 | 2026-08-09 | Review | Approved | Homelab Operator |
| PROC-0009@1.0 | 2026-08-09 | Approved | Active | Homelab Operator; persistence remains Pending because commit and push are prohibited |

## Human-Readable Completion and Version Evaluation

For every completed gate, roadmap evaluation MUST verify that the gate has a
human-readable completion summary in addition to its machine-readable result
and required evidence.

For manually executed roadmap gates, evaluation MUST verify before state
advancement that:

1. the result has been validated;
2. `SUMMARY.md` or the declared equivalent exists;
3. the summary is consistent with the result/evidence;
4. the cumulative roadmap history has been updated;
5. the next authorized action is explicitly identified.

When evaluating an authoritative roadmap modification, the evaluator MUST also
verify that roadmap versioning advanced appropriately and that the persisted
roadmap version agrees with any associated roadmap state projection.

A roadmap modification without the required version advancement is not an
acceptable executable-roadmap update.

Human-readable summaries are not substitutes for machine-readable evidence.
Any contradiction between the summary and machine-readable authority is a
fail-closed evaluation condition.

## Pre-Creation Verification Procedure

Before creating or copying any roadmap-controlled or controlled-document-like
artifact:

1. identify the intended artifact before writing it;
2. attempt all applicable Zeus-native discovery and verification commands;
3. record Zeus availability and the verification surfaces actually used;
4. query authoritative document/index/registry information for identity and
   purpose overlap;
5. inspect existing controlled documentation for conflicting or redundant
   authority;
6. validate intended repository placement;
7. validate controlled identifier uniqueness;
8. determine whether an existing document should be revised instead of a new
   document being created;
9. record PRE_CREATE_VERIFICATION=PASS or FAIL;
10. only after PASS may the creation operation execute.

If Zeus cannot perform an applicable check, the evaluator must record the
specific Zeus capability gap before using repository-native fallback
verification.

Fallback verification must include the authoritative controlled-document
validator and repository discovery/index inspection appropriate to the
artifact.

A document created before this verification has completed is nonconforming and
must not be accepted merely because later validation succeeds.

For evidence preservation, do not copy controlled documents with live document
identifiers into discoverable repository evidence paths. Prefer digests, Git
identities, diffs, or another representation that cannot be mistaken for a
second controlled authority.
