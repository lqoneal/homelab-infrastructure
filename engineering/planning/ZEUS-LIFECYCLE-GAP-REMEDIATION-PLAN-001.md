# Zeus Lifecycle Gap Remediation Plan

| Field | Value |
|---|---|
| `PLAN_ID` | `ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001` |
| `CLASSIFICATION` | `CURRENT_IMPLEMENTATION_PLAN; NOT_EXECUTION_AUTHORITY` |
| `STATUS` | `RECORDED_PENDING_OPERATOR_REVIEW` |
| `PARENT_MISSION` | `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` |
| `ASSOCIATED_WOP` | `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` |
| `LIFECYCLE_STATE` | `ADMISSION_REQUESTED; EXECUTION_HELD` |
| `SOURCE_EVIDENCE` | `engineering/evidence/operation-beta/comprehensive-controlled-document-and-lifecycle-runtime-reconciliation-001/LIFECYCLE-GAP-REGISTER.md` |
| `ROADMAP_EVIDENCE` | `engineering/evidence/operation-beta/comprehensive-controlled-document-and-lifecycle-runtime-reconciliation-001/RECOMMENDED-LIFECYCLE-REMEDIATION-ROADMAP.md` |
| `CURRENT_OPERATION` | `OPERATION-BETA` |
| `CAGF01_STATUS` | `DEFERRED` |

## 1. Authority and status model

This is the current implementation-planning record. The investigation
register and roadmap remain immutable evidence of what was observed and
recommended. This record preserves their IDs and recommendations, adds
implementation status and sequencing, and does not itself authorize
implementation, admission, execution, publication, push, or EOS
synchronization.

Gap planning states are:

`OPEN` → `READY` → `IN_IMPLEMENTATION` → `QUALIFIED` → `PUBLISHED` →
`VERIFIED` → `CLOSED`, with `BLOCKED` and `DEFERRED_BY_DEPENDENCY` available
at any pre-closure point. Current state for every gap is `OPEN` or
`DEFERRED_BY_DEPENDENCY`; no gap is complete.

The canonical lifecycle owner remains the receipt-backed canonical lifecycle
chain. Provider, session, monitoring, Operation Beta, autonomous, and legacy
views are subordinate or compatibility projections until a future mission
qualifies their convergence.

## 2. Persisted gap plan

The following entries preserve the investigation register's exact IDs,
severity, scope, finding, and remediation while adding the planning fields
needed for implementation control.

| ID | Severity / scope | Finding and authoritative recommendation | Status | Wave | Depends on | Owner / affected boundary |
|---|---|---|---|---|---|---|
| `GAP-001` | `HIGH / BLOCKS_INDEPENDENT_VERIFICATION` | P2 target discovery depends on selected runtime root; default surfaces do not expose it when the contract is absent. Implement a canonical runtime resolver and explicit P2/P3/P4 discovery tests. | `QUALIFIED` | 1 | P2 submission receipt and mission identity contract | Canonical P2 read model; receipt/mission CLI/projection tests |
| `GAP-002` | `HIGH / BLOCKS_LIFECYCLE_EXECUTION, BLOCKS_INDEPENDENT_VERIFICATION` | P2/P3/P4/Stage1/provider chain lacks one integrated mission-native transition resolver. Make the receipt chain canonical and projections subordinate only. | `QUALIFIED` | 1–2 | `GAP-001`, `GAP-006` | Lifecycle transition owner; submission/admission/bootstrap/Stage1/provider boundaries |
| `GAP-003` | `HIGH / BLOCKS_PUBLICATION` | Publication/EOS mutation and mission receipts are not proven as one authoritative chain. Add a bounded publication/sync receipt bridge with external mutation authority. | `DEFERRED_BY_DEPENDENCY` | 5 | `GAP-002`, `GAP-009`, `GAP-011` | Publication workflow and EOS integration; no direct mutation in this plan |
| `GAP-004` | `HIGH / BLOCKS_SAFE_RECOVERY` | Autonomous resolver and Stage1 fixtures require incompatible authority receipt contracts. Define a canonical adapter or unified receipt contract and fail closed on ambiguity. | `QUALIFIED_WAVE2_BOUNDARY` | 2 | `GAP-001`, `GAP-002` | Authority receipt adapter; autonomous lifecycle and Stage1 compatibility |
| `GAP-005` | `HIGH / BLOCKS_CLOSEOUT` | Canonical reconciliation closeout and legacy Beta closeout are duplicative. Retain legacy read-only compatibility and unify the terminal predicate. | `DEFERRED_BY_DEPENDENCY` | 6 | `GAP-002`, `GAP-003`, `GAP-009` | Canonical closeout owner; `beta_closeout.py` compatibility boundary |
| `GAP-006` | `HIGH / BLOCKS_INDEPENDENT_VERIFICATION` | Mission verification controller and current projection disagree on next action. Provide one canonical next-action resolver and migration tests. | `QUALIFIED` | 1 | P2/P3 lifecycle receipts; no admission advancement required for resolver tests | Canonical P2 next-action projection; command-surface tests |
| `GAP-007` | `MEDIUM / BLOCKS_INDEPENDENT_VERIFICATION` | No single native surface covers provider/session/process/monitor/evidence lifecycle. Add a mission-native read-only aggregate view. | `QUALIFIED_WAVE2_BOUNDARY` | 2 (Wave 7 acceptance expansion remains) | `GAP-002` and provider/session identity contracts | Zeus mission verification surfaces; provider/session/monitor projections |
| `GAP-008` | `MEDIUM / BLOCKS_SAFE_RECOVERY` | Recovery failure modes lack end-to-end proof. Add deterministic interruption/checkpoint/resume scenarios. | `QUALIFIED_WAVE3_BOUNDARY` | 3 | `GAP-002`, `GAP-004`, provider/session contract | Canonical recovery contract; monitoring, checkpoint, resume, and failure-ordering tests |
| `GAP-009` | `MEDIUM / BLOCKS_INDEPENDENT_VERIFICATION` | Qualification chain is component-tested, not real-mission independently proven. Bind qualification to receipt/evidence manifest chain. | `DEFERRED_BY_DEPENDENCY` | 4 | `GAP-002`, `GAP-008` | Evidence and qualification owner; requirement-level traceability |
| `GAP-010` | `LOW / TECHNICAL_DEBT` | Historical default mission identity remains in generic Codex compatibility fallback. Make the fallback explicitly legacy-only. | `DEFERRED_BY_DEPENDENCY` | 1 or compatibility maintenance | No execution dependency; preserve historical records | Legacy compatibility owner; default Codex fallback |
| `GAP-011` | `MEDIUM / BLOCKS_PUBLICATION` | Candidate scope verifier cannot accept the entire dirty worktree. Publish only exact isolated corrective hunks. | `OPEN` | 5 / publication prerequisite | Publication candidate isolation and operator review | Publication candidate verifier; repository boundary |
| `GAP-012` | `LOW / TECHNICAL_DEBT` | Layered validators report candidate drift under synchronization mode. Keep baseline fingerprints immutable; qualify the exact candidate. | `OPEN` | 5 / validation support | Exact candidate manifest; no EOS mutation | Validator/synchronization reporting; preserve baseline fingerprints |

For every gap, completion requires focused tests, integration proof, a
Zeus-native verification surface, authoritative state and receipt evidence,
replay/idempotency proof, and a negative/fail-closed proof where applicable.
The detailed per-gap contract is in the persistence evidence package's
`IMPLEMENTATION-READINESS-MATRIX.md` and `VALIDATION-REPORT.md`.

## 3. Dependency order and waves

The dependency order is:

```text
GAP-001 + GAP-006
        ↓
GAP-002
        ↓
GAP-004 + GAP-007
        ↓
GAP-008
        ↓
GAP-009
        ↓
GAP-011 + GAP-012
        ↓
GAP-003
        ↓
GAP-005
        ↓
GAP-010 compatibility cleanup and final E2E proof
```

Wave 1 establishes canonical discovery, next-action resolution, and the
receipt-backed lifecycle owner. Wave 2 makes admission-to-execution a real
identity-preserving provider/session chain. Wave 3 makes monitoring,
interruption, checkpoint, and resume authoritative. Wave 4 binds evidence to
mission work and independent qualification. Wave 5 isolates publication and
reconciles repository/EOS receipts. Wave 6 establishes one terminal
predicate. Wave 7 exposes all lifecycle state through Zeus-native views and
Wave 8 proves the complete lifecycle with a bounded real qualification
mission. Waves are planning sequence only.

## 4. First implementation unit

The first safe implementation unit is a read-only canonical lifecycle
discovery and next-action resolver for `GAP-001` and `GAP-006`.

Proposed mission: `ZEUS-LIFECYCLE-FOUNDATION-CONVERGENCE-01`.

Proposed WOP: `WOP-ZEUS-LIFECYCLE-FOUNDATION-CONVERGENCE-001`.

It consumes existing receipt-backed P2 state, preserves identity, does not
admit or dispatch the parent lifecycle mission, and establishes the resolver
contract required by `GAP-002`. Its complete specification and executable
next handoff are evidence artifacts, not an executed WOP.

The Wave 1 continuation qualifies `GAP-002` at the receipt-backed resolver
boundary. It consumes the existing P2 submission receipt and, when present,
the identity-bound P3 admission and P4 bootstrap transactions. It does not
invoke admission, bootstrap, provider, session, execution, publication, or
EOS mutation. Provider/session convergence and later lifecycle work remain
deferred to their dependency-ordered gaps.

Wave 2 qualifies `GAP-004` and `GAP-007` at a bounded read-only boundary.
`ZEUS-CANONICAL-AUTHORITY-RECEIPT/1` normalizes the canonical P2 envelope and
explicitly classifies legacy Stage 1/autonomous receipt forms. The mission
aggregate consumes the canonical resolver and reports subordinate provider,
session, execution, process, monitoring, and evidence records only when
present and identity-valid. It does not materialize downstream state. Wave 7
remains responsible for expanding native lifecycle acceptance across every
later-stage surface.

Wave 3 qualifies `GAP-008` at a bounded receipt-backed recovery boundary.
`ZEUS-CANONICAL-RECOVERY/1` provides deterministic immutable checkpoint,
interruption, and resume-request envelopes. The canonical lifecycle chain owns
mission state; recovery validates exactly one execution-bound checkpoint,
preserves the existing execution identity, skips completed work on resume, and
fails closed on missing, stale, conflicting, or digest-invalid evidence. The
Wave 3 implementation does not admit or execute the parent mission and does
not claim final end-to-end recovery proof; later lifecycle waves remain
deferred.

## 5. WOP relationship

The existing seven-gate lifecycle WOP encompasses all twelve gaps. No source
revision is required: the source is byte-identical and already authorizes
convergence, receipt-backed transitions, negative/replay/recovery tests,
evidence, qualification, publication/EOS controls, closeout, and final
end-to-end proof. This planning record is subordinate traceability and does
not expand the WOP scope.

Gate mapping is maintained in
`engineering/evidence/operation-beta/zeus-lifecycle-gap-roadmap-persistence-001/WOP-GAP-TRACEABILITY.md`.

## 6. Required end state

All twelve gaps must independently reach `CLOSED` only after their evidence,
publication, and verification predicates are met. The parent lifecycle
mission must reach `CLOSED` only after the final end-to-end qualification,
repository/origin parity, EOS synchronization, and canonical closeout. Until
then, `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` remains
`ADMISSION_REQUESTED`, and `CAGF-01` remains deferred.
