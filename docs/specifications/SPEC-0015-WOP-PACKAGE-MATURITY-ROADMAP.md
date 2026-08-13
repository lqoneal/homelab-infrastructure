---
document_id: SPEC-0015
title: WOP Package Maturity Roadmap
version: 0.3
status: Draft
owner: Homelab Infrastructure
created: 2026-08-12
last_updated: 2026-08-12
classification: Engineering Specification
predecessor_revision: 0.1
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - Architecture approval, implementation authorization, execution, publication, and convergence integration remain pending.
  - EENS implementation, independent roadmap qualification, and roadmap convergence remain outside this transaction.
  - CR48 remains held under EGR-000007.
relationships:
  - type: governed_by
    target: STD-0006
  - type: governed_by
    target: EGR-000007
  - type: depends_on
    target: SPEC-0002
  - type: related_to
    target: SPEC-0016
  - type: indexed_by
    target: DOC-0001
tags: [wop, maturity, roadmap, planning-only]
---

# WOP Package Maturity Roadmap

## Purpose

This specification is the authoritative, planning-only WOP development roadmap.
It converts the post-CR47 assessment's complete capability-category coverage
into an ordered set of bounded engineering transactions that can later be
authorized and independently qualified. It does not authorize implementation,
execution, EENS work, publication, synchronization, or CR48.

The roadmap retains the canonical WOP architecture established by
`SPEC-0002`, `PROC-0001`, the WOP schemas under `engineering/wop/`, and the
admission, dispatch, lifecycle, evidence, and publication contracts already
owned by the repository. It creates no parallel lifecycle, identity owner,
mission ordering source, or publication authority.

Status at this revision: `DRAFT / IN DEVELOPMENT / NOT EXECUTABLE`. A roadmap
item is not a Zeus-discoverable execution gate merely because it is listed
here. `DOCUMENTED != APPROVED`; `PLANNED != AUTHORIZED`; `IMPLEMENTED !=
QUALIFIED`; and `QUALIFIED != PUBLISHED`, `SYNCHRONIZED`, or `CLOSED`.

## Scope

This specification covers planning for the canonical WOP package contract,
validation, identity, registration, submission, admission, dispatch, managed
provider execution, monitoring, evidence, qualification, recovery, replay,
publication, repository/EOS reconciliation, EENS interfaces, and closeout. It
does not authorize or implement any of those runtime activities, implement
EENS, converge roadmaps, or execute CR48.

## Model

The model is an ordered sequence of bounded planning items (`WOP-01` through
`WOP-11`) with explicit prerequisites, scope, non-scope, artifacts, lifecycle
semantics, evidence, tests, qualification, exits, recovery, Zeus implications,
and EENS interface dispositions. H01-H06 remain the requirement families and
the lifecycle matrix below is the canonical ordering model.

## Governing sequence

EGR-000007 requires the following sequence. This roadmap revision records item
1 at the operator-review boundary; item 2 is separately represented by the
current maturity-hardened SPEC-0016. No roadmap item below advances
qualification, convergence, or CR48:

1. Mature and harden this WOP development roadmap.
2. Mature and harden the EENS development roadmap (`SPEC-0016`).
3. Independently qualify the WOP roadmap.
4. Independently qualify the EENS roadmap.
5. Converge the qualified subsystem roadmaps into the canonical roadmap.
6. Maturity-harden the resulting canonical roadmap.
7. Independently requalify the canonical roadmap.
8. Perform a fresh CR48 readiness assessment.

No WOP item below may be interpreted as advancing independent qualification,
convergence, canonical-roadmap re-hardening, or CR48.

## Authority boundary

Zeus controls mission selection, lifecycle control, admission authority,
dispatch, provider selection, provider/session/execution bindings, monitoring,
recovery decisions, and execution-state projections. Zeus resolves the exact
provider/Codex invocation options for managed execution.

Codex executes only the authorized bounded scope in the authorized worktree.
Codex has no privileged Git or publication authority and cannot stage, commit,
push, publish, synchronize EOS, grant authority, or close a WOP. Zeus retains
control of staging, commit, push, publication transitions, and authoritative
synchronization. `ZEUS_MANAGED` is the required non-interactive execution model
for future managed Codex work; direct-interactive fallback is not a roadmap
substitute.

WOP owns immutable execution intent and its canonical identity binding. EMM,
mission records, repository identity/baseline, provider qualification, and
approval records remain owned by their canonical systems. EENS owns event and
notification observation/delivery; it is not an authority source and cannot
advance a WOP by notification alone.

## Canonical lifecycle coverage

The ordered roadmap covers this complete lifecycle. The owner in parentheses is
the authoritative source of the semantic decision:

`AUTHOR` (WOP source/template) -> `VALIDATE` (WOP validator) -> `GENERATE`
(immutable package builder) -> `BIND` (canonical identity/digest) ->
`REGISTER` (canonical registry/EMM) -> `SUBMIT` (submission act) -> `ADMIT`
(Zeus/EMM admission) -> `READY` (lifecycle projection) -> `SELECT`
(qualified executor registry/Zeus) -> `DERIVE` (Zeus-to-provider/Codex plan) ->
`BIND EXECUTION` (Zeus provider/session/execution record) -> `START` (provider
and lifecycle) -> `MONITOR` (Zeus plus observed events) -> `EVIDENCE`
(executor/evidence contract) -> `COMPLETE` (execution result) -> `QUALIFY`
(independent qualifier) -> `RECOVER`/`RESUME`/`REPLAY` (Zeus recovery contract)
-> `PUBLISH` (controlled publication authority) -> `RECONCILE` (repository/EOS
authority) -> `CLOSE` (controlled closeout).

## Maturity vocabulary and evidence rule

Each capability is classified conservatively:

- **Implemented and qualified** means a repository implementation and a
  directly relevant passing test or qualification record establish the bounded
  behavior. It does not establish whole-WOP maturity.
- **Implemented, hardening required** means code/schema exists, but boundary,
  negative, integration, durability, or independent qualification evidence is
  incomplete.
- **Partially implemented** means only a slice, projection, fixture, or
  read-only path exists.
- **Not implemented** means no repository evidence supports the behavior.
- **EENS-dependent** means the WOP-side contract can be designed now, but the
  end-to-end behavior cannot be independently qualified until EENS is mature.
- **Convergence-dependent** means it must wait for both qualified subsystem
  roadmaps and the post-convergence canonical roadmap transaction.

No status may be promoted without an implementation locator, test/fixture
locator, observed result, identity/digest binding, and an independent
qualification disposition where the item claims qualification.

## Current implementation-state assessment

The assessment input at
`engineering/convergence/engineering-system-convergence/gates/C02-controlled-documentation-and-authority/corrective/ESC-C02-CORRECTIVE-001/gates/CR47/evidence/POST-CR47-WOP-ROADMAP-MATURITY-HARDENING-ASSESSMENT.yaml`
establishes that all required capability categories are covered. It does not
establish implementation maturity. The following state is the baseline for
future work:

| Capability slice | State | Repository basis and limitation |
|---|---|---|
| Source/template authoring | Partially implemented | WOP submission sections and existing work-order fixtures exist; one canonical authoring/construction path and full omission/placeholder qualification remain to be proven. |
| Deterministic validation | Implemented, hardening required | `engineering/wop/*.schema.yaml`, compatibility fixtures, and admission tests exist; cross-schema semantic closure and version migration qualification remain. |
| Immutable package generation | Partially implemented | `canonical-wop-package.schema.yaml` and immutable package contracts exist; atomic generation, stable bytes, and publication-grade immutability need qualification. |
| Identity and digest binding | Implemented, hardening required | Package/submission digests, baseline fields, and execution assignment checks exist; end-to-end identity lineage and collision/revision negatives need proof. |
| Registration | Partially implemented | EMM/work registries and publication records exist; one authoritative WOP registry lifecycle with stale/historical detection is not independently qualified. |
| Submission and admission | Implemented, hardening required | `engineering/admission/wop-submission.schema.yaml`, admission code, and negative tests exist; all lifecycle and authority combinations need matrix qualification. |
| Dispatch readiness | Implemented, hardening required | Assignment and dispatcher schemas/fixtures exist; durable readiness, lease expiry, and duplicate-dispatch recovery need proof. |
| Qualified executor selection | Implemented, hardening required | Execution-agent registry and provider-selection code exist; complete qualification revocation and deterministic selection evidence remains. |
| Zeus-to-provider/Codex derivation | Implemented, hardening required | `PROC-0001` and managed preflight/provider resolver define the boundary; full non-interactive dispatch and option-plan replay require independent proof. |
| Provider/session/execution identity | Partially implemented | Execution assignment and oversight/session records bind identities; collision, successor, and historical-owner qualification remains. |
| Start and monitoring | Partially implemented | Execution oversight state/event handling and focused tests exist; the complete WOP lifecycle projection and durable monitoring contract remain. |
| Evidence collection | Implemented, hardening required | Evidence packages and evidence contracts exist; requirement-level immutable indexing and negative evidence across all outcomes remain. |
| Completion and independent qualification | Partially implemented | Completion/qualification procedures and reports exist; independent WOP-result derivation and false-closure prevention need an end-to-end qualification. |
| Interruption recovery and replay | Implemented, hardening required | `scripts/lib/emp/execution_oversight.py` and `test-execution-oversight.py` cover event replay/interruption slices; all failure points and no-duplicate-effect guarantees remain. |
| Publication and EOS reconciliation | Implemented, hardening required | `PROC-0005` and repository/EOS procedures and evidence exist; WOP-specific publication failure, stale projection, and closeout qualification remain. |
| EENS interface | Partially implemented / EENS-dependent | Oversight tests consume authenticated EENS-shaped events; EENS taxonomy, delivery, replay, and independent subsystem qualification are not established by this roadmap. |

## Ordered development sequence

Each item is a separately bounded future transaction. The fields below are
mandatory for the transaction's WOP, implementation record, evidence package,
and qualification record; omitted fields are not implicitly satisfied.

### WOP-01 — Roadmap and authority baseline

- **Objective:** Freeze the canonical WOP lifecycle, ownership map, requirement
  register (H01-R01 through H06-R15), lifecycle coverage, and this maturity
  classification as the input to implementation.
- **Authoritative inputs:** This specification; EGR-000007; SPEC-0002;
  PROC-0001, PROC-0005; WOP schemas; CR47 assessment; DOC-0001.
- **Prerequisites:** EGR-000007 active; CR48 held; no implementation or
  convergence authority inferred.
- **Implementation scope:** Produce a machine-readable WOP traceability and
  dependency manifest that maps every requirement to one later work item,
  owner, state, evidence, and qualification test.
- **Explicit non-scope:** No runtime code, EENS code, schema redesign,
  canonical-roadmap convergence, publication, or CR48 action.
- **Artifacts/evidence/tests:** Baseline manifest, authority-boundary matrix,
  lifecycle-to-item matrix, dependency graph, negative authority review, and
  structure/schema validation.
- **Lifecycle semantics:** Roadmap state only; no WOP lifecycle transition.
- **Qualification/exit:** Independent reviewer confirms one owner per semantic,
  all 21 lifecycle stages mapped, no circular dependency, and no executable
  gate implied. Downstream: WOP-02.
- **Recovery/replay:** Preserve the prior manifest and review record; a failed
  transaction is superseded, never rewritten as passed.
- **Zeus/Codex:** Zeus remains the future execution controller; Codex may only
  perform the later bounded transaction under an authorized worktree.
- **EENS interface:** None beyond recording that event contracts are deferred
  to WOP-10 and SPEC-0016.

### WOP-02 — Canonical authoring, validation, and version policy

- **Objective:** Make source/template authoring deterministic and make invalid,
  incomplete, duplicate, stale, unsupported, and incompatible packages fail
  closed.
- **Prerequisites:** WOP-01; canonical schema owners confirmed.
- **Scope:** One construction path; required objective/scope/authority,
  prohibited effects, dependencies, DAG, criteria, evidence, interruption,
  completion, and revision metadata; compatibility and migration rules;
  machine-readable diagnostics.
- **Non-scope:** Dispatch, execution, EENS implementation, publication, or
  replacing SPEC-0002 ownership.
- **Artifacts/evidence/tests:** Authoring template/tool, canonical fixtures,
  duplicate-key and malformed negatives, stable diagnostic corpus, schema and
  semantic validation report, and migration provenance records.
- **Lifecycle semantics:** `AUTHOR -> VALIDATE`; validation creates no
  authority and does not admit or register a package.
- **Qualification/exit:** Identical source and inputs produce identical
  validated output; all required fields and prohibited-effect checks are
  exercised; unsupported revisions fail closed. Downstream: WOP-03.
- **Recovery/replay:** Failed generation leaves no active package; rerun uses
  the same source digest and cannot silently repair historical input.
- **Zeus/Codex:** Zeus consumes the validated contract; Codex cannot infer
  omitted authority or provider options.
- **EENS interface:** No event dependency; validation may emit a future
  validation result event only under the EENS contract.

### WOP-03 — Immutable generation, canonical identity, digest, and registration

- **Objective:** Produce one immutable package revision and bind it to the
  canonical WOP, mission/gate/work identity, repository baseline, lineage, and
  digest before registration.
- **Prerequisites:** WOP-02; repository identity and baseline contracts;
  canonical registry owner identified.
- **Scope:** Atomic package generation; canonical identity and revision rules;
  cryptographic manifest; predecessor lineage; derived Stage-1 identity
  preservation; registration and stale/historical record handling.
- **Non-scope:** Admission approval, provider launch, execution, EENS runtime,
  publication to EOS, or a second identity registry.
- **Artifacts/evidence/tests:** Immutable package fixtures, digest/lineage
  manifest, registration receipt, revision collision and tamper negatives,
  regeneration byte-equivalence test, and registry reconstruction report.
- **Lifecycle semantics:** `GENERATE -> BIND -> REGISTER`; registration is
  not submission, admission, or authorization.
- **Qualification/exit:** Every runtime/derived reference resolves to exactly
  one canonical revision; digest, baseline, and lineage mismatch fail closed;
  historical records remain historical. Downstream: WOP-04.
- **Recovery/replay:** Interrupted generation is discarded or resumed by the
  same transaction identity; replacement revisions receive new identity and
  never rewrite historical evidence.
- **Zeus/Codex:** Zeus resolves the registered revision; Codex receives no
  registry or publication privilege.
- **EENS interface:** Optional future `WOP_REGISTERED` receipt contract is
  specified but not required for independent WOP registration qualification.

### WOP-04 — Submission, authorization, admission, and readiness

- **Objective:** Establish a fail-closed boundary from an operator-submitted
  package through Zeus/EMM admission and dispatch readiness.
- **Prerequisites:** WOP-03; active authority, mission contract, baseline,
  dependency, and admission owners.
- **Scope:** Submission act, identity/digest verification, authority and
  approval semantics, prerequisites, prohibited effects, lifecycle transitions,
  lease/readiness records, revocation, stale/historical detection, and
  admission decisions.
- **Non-scope:** Provider selection, process launch, execution monitoring,
  evidence qualification, EENS implementation, or publication.
- **Artifacts/evidence/tests:** Submission/admission records, accepted and
  rejected fixtures, authority/revocation matrix, duplicate and stale negatives,
  readiness/lease expiry tests, and Zeus admission reconstruction evidence.
- **Lifecycle semantics:** `SUBMIT -> ADMIT|REJECT|BLOCKED -> READY`; absence
  of approval is never approval; observation cannot transition state.
- **Qualification/exit:** Exactly one current admissible revision exists;
  unmet prerequisites and authority conflicts fail closed; admission is
  idempotent; readiness cannot be mistaken for dispatch or execution.
  Downstream: WOP-05.
- **Recovery/replay:** A duplicate submission returns the original decision;
  revoked, expired, or historical records cannot become current; failed
  admission creates no execution identity.
- **Zeus/Codex:** Zeus owns admission and readiness; Codex is not invoked before
  admission and cannot approve its own work.
- **EENS interface:** A future admission decision/receipt event may be observed
  but cannot be the admission authority or the sole qualification evidence.

### WOP-05 — Qualified executor selection and managed provider derivation

- **Objective:** Deterministically select a qualified executor and derive one
  immutable Zeus-managed provider/Codex invocation plan.
- **Prerequisites:** WOP-04; qualified executor registry; managed provider
  capability and option resolver; exact repository/worktree binding.
- **Scope:** Selection/revocation, capability compatibility, provider mode and
  transport, executable/version, authentication/configuration, sandbox and
  approval policy, work-contract capabilities, invocation-plan digest, and
  read-only preflight.
- **Non-scope:** Provider launch, mission execution, direct-interactive mode,
  changing unsupported options, EENS implementation, Git publication, or EOS.
- **Artifacts/evidence/tests:** Selection receipt, preflight plan, option
  resolution matrix, incompatibility negatives, same-input determinism test,
  and proof preflight creates no process/session/work.
- **Lifecycle semantics:** `READY -> SELECT -> DERIVE`; derivation is not
  `START` and does not grant authority.
- **Qualification/exit:** One qualified candidate and one digest-bound plan
  resolve; conflicts and unsupported syntax fail closed; managed dispatch and
  preflight consume the same plan. Downstream: WOP-06.
- **Recovery/replay:** Failed preflight creates no replacement identity; a
  changed provider plan requires a new derivation and revalidation.
- **Zeus/Codex:** Zeus owns all provider/session/execution options and invokes
  Codex non-interactively; Codex receives only the bounded work contract.
- **EENS interface:** Provider-readiness observations may be events, but event
  delivery cannot select an executor or mutate authority.

### WOP-06 — Execution identity, dispatch, start, and runtime monitoring

- **Objective:** Bind one execution to the admitted package, provider, session,
  agent, repository, baseline, and invocation plan, then monitor it through
  explicit lifecycle states.
- **Prerequisites:** WOP-05; durable lifecycle store; dispatch and execution
  identity contracts; monitoring owner.
- **Scope:** Dispatch assignment, lease acquisition, provider/session/execution
  identity, launch/start, legal state transitions, heartbeats, checkpoint
  references, timeout classification, and terminal-state immutability.
- **Non-scope:** Requirement implementation itself, independent qualification,
  EENS subsystem implementation, publication, or automatic authority repair.
- **Artifacts/evidence/tests:** Dispatch/start/monitor receipts, identity
  binding matrix, provider/session collision negatives, duplicate launch tests,
  legal-transition matrix, heartbeat/timeout tests, and fresh-process replay.
- **Lifecycle semantics:** `READY -> DISPATCHED -> ACCEPTED -> INITIALIZING ->
  RUNNING -> COMPLETED|FAILED|PAUSED`; one current execution owner; terminal
  states are immutable.
- **Qualification/exit:** Exactly one execution identity exists for one
  assignment; a collision fails closed; launch failure is classified without
  fabricating completion; monitoring is reconstructable from durable records.
  Downstream: WOP-07 and WOP-08.
- **Recovery/replay:** Before dispatch, retry may reuse only the valid admission
  decision; after dispatch, preserve identity; provider launch failure and
  session collision require explicit disposition; no duplicate effect is
  inferred from a missing receipt.
- **Zeus/Codex:** Zeus creates and owns bindings and monitoring; Codex reports
  within the work contract and cannot create a successor session.
- **EENS interface:** Requires future execution-state event contract with
  producer, identity bindings, ordering, authentication, and duplicate behavior;
  WOP qualification may use a deterministic local observation adapter only if
  it proves the same contract without claiming EENS maturity.

### WOP-07 — Evidence, completion, independent qualification, and false-closure prevention

- **Objective:** Derive execution completion and WOP qualification from
  immutable, requirement-indexed evidence independently of executor assertion.
- **Prerequisites:** WOP-06; evidence contract; independent qualifier role;
  controlled completion and capability-qualification procedures.
- **Scope:** Evidence collection/indexing/digests, positive and negative
  evidence, requirement and gate results, executor/qualifier separation,
  completion report, controlled dispositions, and false-closure guards.
- **Non-scope:** EENS implementation, publication, EOS synchronization, or
  turning a state-field write into qualification.
- **Artifacts/evidence/tests:** Requirement evidence manifest, immutable ledger,
  completion report, qualification report, missing/stale/conflicting evidence
  negatives, independent-process reconstruction, and PASS/FAIL/BLOCKED/
  INDETERMINATE/NOT_APPLICABLE matrix.
- **Lifecycle semantics:** `RUNNING -> COMPLETED` records execution result only;
  `COMPLETED -> QUALIFIED|FAILED|BLOCKED|INDETERMINATE` is a separate
  qualification decision.
- **Qualification/exit:** Every requirement has attributable evidence and an
  independently derived result; incomplete, stale, or contradictory evidence
  cannot close the WOP. Downstream: WOP-08 and WOP-09.
- **Recovery/replay:** Qualification failure preserves evidence and requires a
  new disposition; replay is read-only and cannot rewrite evidence or promote
  closure.
- **Zeus/Codex:** Zeus verifies qualification inputs and records; Codex cannot
  qualify its own execution or completion.
- **EENS interface:** Evidence may reference event receipts, but event receipt
  alone is not requirement evidence unless the frozen contract defines payload,
  provenance, and independent corroboration.

### WOP-08 — Interruption recovery, deterministic resume, and replay

- **Objective:** Make every interruption and recovery path identity-preserving,
  deterministic, auditable, and safe against duplicate effects.
- **Prerequisites:** WOP-06 and WOP-07; durable checkpoint and evidence stores;
  recovery taxonomy and operator escalation authority.
- **Scope:** Interruption before/after dispatch, launch failure, session
  collision, duplicate prevention, partial execution, checkpoint atomicity,
  resume validation, deterministic replay, corrupt checkpoint handling,
  qualification failure, and false closure prevention.
- **Non-scope:** Fabricating authority, rewriting historical evidence, silently
  replacing execution identity, EENS implementation, or publication recovery.
- **Artifacts/evidence/tests:** Recovery state machine, checkpoint schema,
  scenario matrix, process/host restart tests, tamper/corruption negatives,
  byte-equivalent replay report, evidence-continuity report, and operator
  escalation records.
- **Lifecycle semantics:** Recovery may produce `PAUSED`, `RESUMABLE`,
  `REPLAYING`, `FAILED`, or `RECONCILED_HISTORICAL`; resume requires exact
  mission/WOP/execution/baseline/evidence bindings.
- **Qualification/exit:** All listed interruption and failure scenarios are
  tested; replay is idempotent; no new authority or identity is fabricated;
  partial execution and historical state remain visible. Downstream: WOP-09.
- **Recovery/replay:** This is the primary recovery item. Provider/session
  collisions fail closed; a successor gets a new identity only after canonical
  termination; historical sessions never become current or resumable.
- **Zeus/Codex:** Zeus decides retry/resume/escalation and owns recovery
  transitions; Codex may resume only the exact authorized contract.
- **EENS interface:** Requires interruption, checkpoint, resume, and failure
  events with correlation, ordering, idempotency, delivery expectation, and
  failure isolation. This portion remains EENS-dependent.

### WOP-09 — Publication, repository reconciliation, EOS synchronization, and closeout

- **Objective:** Close the WOP only through controlled publication and
  repository/EOS reconciliation after qualification.
- **Prerequisites:** WOP-07 qualified evidence; WOP-08 recovery qualification;
  PROC-0005; repository/EOS synchronization contract; publication authority.
- **Scope:** Publication candidate derivation, controlled publication receipt,
  Git/repository reconciliation, EOS projection comparison, publication and
  synchronization failure handling, stale/historical detection, and immutable
  closeout.
- **Non-scope:** Granting execution authority, changing EOS authority model,
  committing/pushing during roadmap hardening, EENS implementation, or CR48.
- **Artifacts/evidence/tests:** Publication manifest/receipt, repository and EOS
  comparison, failure/retry matrix, stale projection and partial publication
  negatives, closeout record, and final validation report.
- **Lifecycle semantics:** `QUALIFIED -> PUBLISHING -> PUBLISHED ->
  SYNCHRONIZING -> SYNCHRONIZED -> CLOSED`; each transition requires its own
  receipt and authority. No state field alone establishes a transition.
- **Qualification/exit:** Publication failure is recoverable without a second
  WOP identity; synchronization failure remains open and visible; closeout
  proves evidence, qualification, publication, and synchronization. Downstream:
  WOP-10 and independent roadmap qualification.
- **Recovery/replay:** Resume the same publication transaction when valid;
  reconcile historical partial results without rewriting them; prevent false
  closure when EOS or repository state is stale or incomplete.
- **Zeus/Codex:** Zeus/operator publication authority owns staging, commit,
  push, publication, and EOS synchronization; Codex cannot perform them.
- **EENS interface:** Publication/synchronization receipts may be observed, but
  delivery failure cannot erase the authoritative repository/EOS result. The
  WOP-side contract is independently testable; end-to-end delivery is
  EENS-dependent.

### WOP-10 — WOP-side EENS interface contract and boundary qualification

- **Objective:** Specify and locally qualify the WOP side of every EENS
  dependency without implementing or qualifying EENS.
- **Prerequisites:** WOP-01 through WOP-09; the current maturity-hardened
  SPEC-0016 is the EENS-side interface input, but its runtime implementation
  and independent qualification remain separate transactions.
- **Scope:** Event taxonomy and ownership matrix; producer; payload and exact
  identity bindings; delivery/observation expectation; ordering; correlation;
  idempotency; replay without lifecycle mutation; failure isolation; approval
  round trip; interruption/resume; receipt-backed closeout.
- **Non-scope:** EENS runtime, event bus, consumers, deployment, convergence,
  or claiming EENS-dependent WOP behavior complete.
- **Artifacts/evidence/tests:** Versioned WOP/EENS interface contract, payload
  examples, contract tests using a deterministic test double, duplicate/out-of-
  order/lost/late event negatives, and explicit producer/consumer disposition.
- **Reciprocal event-family baseline:** The WOP-side contract maps to the EENS
  families as follows: WOP-04 uses `Admission/submission` and
  `Approval request/result`; WOP-05 uses `Provider readiness/selection/preflight`;
  WOP-06 uses `Execution binding/start/progress`; WOP-07 uses
  `Completion/qualification`; WOP-08 uses
  `Blocker/failure/interruption/checkpoint/resume`; and WOP-09 uses
  `Publication/EOS synchronization/closeout`. Zeus/WOP or the named canonical
  owner produces the represented fact; EENS accepts, persists, routes, and
  replays the observation; WOP/Zeus consumes it only as a non-authoritative
  projection. `Notification service` and `Runtime diagnostic` are EENS-owned
  support families and cannot substitute for any WOP family.
- **Lifecycle semantics:** EENS observations are non-authoritative projections;
  only the owning WOP/Zeus/approval/repository authority can transition state.
- **Qualification/exit:** WOP-side validation and failure behavior pass without
  EENS runtime; all unresolved producer/delivery assumptions are listed;
  EENS-dependent items remain open. Downstream: independent WOP qualification,
  then independent EENS qualification and later WOP/EENS convergence.
- **Recovery/replay:** Replay of events is idempotent and cannot mutate
  historical lifecycle; missing or conflicting events fail closed or enter an
  explicit indeterminate state.
- **Zeus/Codex:** Zeus consumes only validated observations and retains control
  of lifecycle; Codex cannot acknowledge or synthesize authoritative events.
- **EENS interface:** This item is the contract boundary itself. Producer,
  payload, binding, delivery, replay, and failure behavior must be named for
  each event before convergence.

### WOP-11 — WOP roadmap completion package and independent qualification boundary

- **Objective:** Produce the independent WOP roadmap qualification package; do
  not qualify the roadmap in this hardening transaction.
- **Prerequisites:** WOP-01 through WOP-10 documented; EENS roadmap hardening
  complete for resolving cross-subsystem dependency dispositions; no
  convergence performed.
- **Scope:** Independent review of completeness, order, dependencies, state
  accuracy, authority boundaries, canonical alignment, Zeus/provider execution,
  recovery/replay, evidence/qualification, EENS interfaces,
  publication/synchronization, and convergence readiness.
- **Non-scope:** Implementing any WOP/EENS capability, converging roadmaps,
  re-hardening the canonical roadmap, qualifying EENS, or reassessing CR48.
- **Artifacts/evidence/tests:** Qualification input index, traceability matrix,
  dependency DAG and cycle check, implementation-state evidence matrix,
  lifecycle coverage matrix, authority-boundary review, test-result inventory,
  EENS contract disposition, negative/false-closure review, and signed
  independent qualification result.
- **Lifecycle semantics:** Qualification is a review transaction and does not
  transition a WOP package, EENS subsystem, EOS, or CR48.
- **Qualification/exit:** The independent qualifier records PASS/FAIL/BLOCKED/
  INDETERMINATE with exact unmet identifiers. PASS requires every criterion
  below and does not authorize convergence; after WOP qualification, the next
  governed action is independent EENS roadmap qualification, followed later by
  the sequence in EGR-000007.
- **Recovery/replay:** Qualification inputs are immutable and rerunnable; a
  failed review is preserved and superseded by a new review, never edited into
  PASS.
- **Zeus/Codex:** Zeus controls any future qualification execution boundary;
  Codex may supply bounded evidence only and has no qualification authority.
- **EENS interface:** Every dependency must be either WOP-side independently
  qualified or explicitly blocked pending EENS qualification and convergence.

## Independent WOP roadmap qualification transaction

This specification defines the boundary and inputs; it is not the qualification
result. The later transaction must consume exactly:

1. this SPEC-0015 revision and its digest;
2. EGR-000007 and the CR47 assessment;
3. SPEC-0002 and directly governing PROC-0001/PROC-0005 contracts;
4. the complete WOP-01–WOP-11 traceability/dependency manifest;
5. repository implementation, schema, fixture, test, and qualification
   locators for every maturity claim;
6. the canonical lifecycle and authority-boundary matrix;
7. recovery/replay scenario and negative-test results;
8. WOP-side EENS contract and unresolved dependency disposition;
9. publication/EOS reconciliation and closeout contract; and
10. the contemporaneous repository HEAD and controlled-document validation
    result.

The qualifier must produce independently attributable evidence for: roadmap
completeness; sequencing consistency; dependency correctness and absence of
cycles; implementation-state accuracy; authority-boundary correctness;
canonical architecture alignment; Zeus/provider and non-interactive Codex
execution completeness; recovery/replay completeness; evidence and independent
qualification completeness; EENS interface completeness; publication,
synchronization, and closeout completeness; and convergence readiness.

The qualification must explicitly test that no item authorizes runtime work,
that no EENS-dependent item is silently marked complete, that no historical
record becomes current, that no recovery path fabricates authority or identity,
and that CR48 remains held. A PASS is a roadmap-quality disposition only; it
does not qualify WOP runtime, EENS runtime, the converged roadmap, or CR48.

## Cross-phase recovery and replay invariants

These invariants apply to every phase that handles lifecycle state, evidence,
publication, or observation:

- Before dispatch, interruption preserves the admission decision and creates no
  execution identity.
- After dispatch, interruption preserves the exact execution identity and
  assignment; retry cannot create a duplicate effect.
- Provider launch failure and provider/session collision fail closed and are
  explicitly classified.
- A successor execution, if authorized after canonical termination, receives a
  new identity and retains a link to the historical predecessor.
- Partial execution resumes only from a digest-verified checkpoint and keeps
  evidence continuity; deterministic replay is idempotent.
- Qualification failure, publication failure, and synchronization failure keep
  the WOP open and preserve all historical evidence.
- Stale or historical lifecycle records cannot satisfy current readiness or
  closeout; false closure is prohibited.
- Recovery never fabricates authority, rewrites historical evidence, silently
  creates replacement identity, or treats notification as authority.

## Dependency order and convergence hold

Within WOP, dependencies are strictly:

`WOP-01 -> WOP-02 -> WOP-03 -> WOP-04 -> WOP-05 -> WOP-06 ->
WOP-07 -> WOP-08 -> WOP-09 -> WOP-10 -> WOP-11`.

WOP-10 has a WOP-side qualification path but its end-to-end event behavior is
blocked by EENS maturity. WOP-11 cannot PASS on EENS-dependent claims until the
EENS roadmap has been maturity hardened and its dependency dispositions are
available. Neither WOP-10 nor WOP-11 converges the roadmaps. Convergence,
canonical-roadmap re-hardening, requalification, and CR48 reassessment remain
the later EGR-000007 steps.

## Validation

Before this revision is accepted for operator review, validate front matter,
document identity, headings, tables, cross-references, unique item identifiers,
complete lifecycle coverage, mandatory phase fields, dependency acyclicity,
state-claim locators, and explicit EENS/Zeus boundaries. Validate with the
repository's non-mutating controlled-document and WOP/platform checks where
available. Do not stage, commit, push, publish, synchronize EOS, execute CR48,
implement WOP runtime, or implement EENS as part of roadmap hardening.

Any future substantive change to SPEC-0002, PROC-0001, PROC-0005, SPEC-0016,
or the canonical convergence roadmap is a recorded downstream dependency, not
an expansion of this transaction.

## Compliance

This document remains a `PLANNING_ONLY` Draft under STD-0006 and the controlled
document policy. It retains SPEC-0015 identity and authority, aligns to the
canonical architecture and procedures named above, and does not create
implementation, execution, publication, synchronization, EENS, or CR48
authority. Promotion requires the independent qualification transaction,
applicable governance disposition, and later EGR-000007 sequencing.

## Revision history

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-12 | Initial Draft planning-only maturity roadmap. |
| 0.2 | 2026-08-12 | Converted category coverage into an ordered WOP lifecycle roadmap with implementation-state assessment, explicit bounded work items, recovery/replay semantics, Zeus/Codex and EENS boundaries, and independent qualification requirements. |
| 0.3 | 2026-08-12 | Corrected duplicate trailing sections, refreshed post-hardening sequencing, and added the reciprocal EENS event-family baseline. |
