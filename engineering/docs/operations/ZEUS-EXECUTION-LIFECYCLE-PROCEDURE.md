# Zeus Execution Lifecycle Procedure

This controlled procedure defines the prepublication Development lifecycle for a receipt-backed Zeus submission.

## Authority and persistence

Authoritative Zeus submission establishes the submitted WOP's work authority
for its declared scope. Stage 1 transactions and their receipts are immutable
submission/provenance records. Admission, identity and integrity validation,
prerequisites, provider qualification, session safety, lifecycle, baseline,
explicit in-WOP approval gates, publication, synchronization, and closeout
remain separate downstream controls; they do not constitute another grant of
operator work authority. A derived record may be created or repaired only
from one validated Stage 1 transaction and must retain its transaction, WOP,
package, source, authority source, provider, dispatch, and repository
bindings.

`zeus submit` may report `DISPATCHED` only after the dispatch receipt, admission projection, execution projection, and reconciliation receipt have been atomically installed and re-read successfully. Failure produces a durable `BLOCKED` checkpoint with the original transaction identity and a resumable next action.

## Entry conditions and evidence

Entry requires one validated Stage 1 transaction, its receipt chain, resolved
repository and baseline bindings, and the applicable downstream authority
state. Each lifecycle transition emits evidence-backed receipts and remains
subject to reconciliation before the next transition is accepted.

## Canonical command path

`submit`, `execute-mission start`, `status`, `session`, `resume`, `suspend`, `cancel`, qualification, publication preparation, synchronization, and closeout resolve the exact requested transaction through the shared reconciliation transaction before consuming derived runtime state. No command resubmits a WOP or creates authority.

An explicitly authorized current administrative or reconciliation transaction
may enter the same Zeus-managed provider lifecycle without a fabricated
mission contract, WOP, or gate. Its operation, EMM, transaction identity,
transaction type, scope, write authority, provider mode, protected-Git
authority, and qualification authority must resolve from a canonical authority
record. Handoff prose can identify a transaction but cannot create or broaden
that authority. Normal WOP/gate execution retains the mission-to-WOP-to-gate
chain; both classes converge on a Zeus execution identity and Zeus-managed
bounded provider execution.

The managed execution context keeps four authorities distinct: transaction
authority resolves what work is authorized; provider authority limits Codex to
the bounded implementation scope; Zeus controller authority owns monitoring,
independent evaluation, receipt persistence, and successor resolution; and
qualification authority identifies who may qualify the transaction. Provider
authority is not Zeus controller authority. A provider prohibition on
self-qualification does not suppress a separately resolved
`qualification_authority: ZEUS`.

The routing invariant is explicit: Codex executes the bounded implementation;
Zeus qualifies the retained terminal evidence; the operator decides only when
the canonical approval policy requires it; and Zeus performs protected
lifecycle operations under its separate privileged authority. A Zeus-owned
qualification action is never represented as, or dispatched through, another
Codex provider task.

Qualification transactions are routed through a Zeus-capable supervisory
context. Zeus constructs the provider request with self-qualification
prohibited, observes the provider to a terminal state, resolves the canonical
operator-approval policy, and only then performs independent qualification.
Provider completion is never qualification. A provider/session context that
cannot qualify itself therefore remains valid for a Zeus-owned qualification
transaction; it is not treated as a qualification blocker.

Every authorized administrative execution receives a transaction-specific
provider contract derived from canonical authority. The contract includes the
transaction identity and type, objective, authorized and prohibited scope,
lifecycle boundary, protected operations, acceptance criteria, required
verification and evidence, and stop conditions. An absent or incomplete
contract fails closed before provider launch. A caller-supplied prompt is only
supplemental contract input; it cannot replace the authoritative objective or
criteria, and the generic acceptance-probe prompt is not a default execution
semantic.

Zeus qualification additionally requires evidence that the exact transaction
was executed, its objective was demonstrated, every authoritative acceptance
criterion was evaluated and passed, and required evidence was retained.
Provider exit zero, session integrity, and scope compliance are necessary but
not sufficient. Wrong-task execution, missing criteria evaluation, or absent
transaction evidence remains non-qualifying.

Before independent qualification, Zeus performs an evidence-finalization
boundary for any retained managed session that lacks the canonical
transaction-acceptance fields. The finalizer binds the resolved transaction,
execution contract, and Zeus execution identity; evaluates each acceptance
criterion and required-evidence declaration against independently retained
verification artifacts; and records `executed_transaction_id`,
`transaction_objective_executed`, `acceptance_criteria_evaluated`, explicit
criterion results, and `required_evidence_retained`. Provider-emitted fields
with equivalent names are ignored. Missing or ambiguous evidence blocks the
transaction and never causes provider re-execution. Finalized evidence is
attributed to `ZEUS_CONTROLLER` with `PROVIDER_MUTATION=NO` and
`ZEUS_CONTROLLER_MUTATION=YES`; only then may the controller route the session
to independent qualification.

Worktree mutation attribution is actor-aware. `PROVIDER_POST_EXECUTION_DIFF`
contains only changes observed during Codex execution and is checked against
provider scope. `ZEUS_CONTROLLER_DIFF` contains controller-owned lifecycle and
evidence changes, including a Zeus qualification receipt. A legitimate Zeus
receipt is recorded as `RECEIPT_AUTHORITY=ZEUS`,
`PROVIDER_MUTATION=NO`, and `ZEUS_CONTROLLER_MUTATION=YES`; it is not a
provider out-of-scope change. Conversely, a provider-created or provider-
modified Zeus receipt is always a provider scope/authority failure, even if a
caller lists the receipt path in provider scope. Terminal reconciliation keeps
provider out-of-scope changes and unauthorized controller changes distinct.

### Operator approval requirements and administrative managed-session qualification

`engineering/authority/operator-approval-requirements.yaml` is the one
canonical, Engineering Governance-maintained policy for exceptional operator
decision boundaries. Zeus resolves it whenever a lifecycle decision might
require operator disposition. Active matching requirements identify the
requirement ID, reason, operator action, authority, and approval/rejection
transitions. Policy additions, removals, and deactivations therefore do not
require lifecycle implementation changes. Malformed or ambiguous policy is a
fail-closed condition. Explicitly declared higher-authority mission/WOP gates
remain legitimate approval boundaries.

Operator intervention is exceptional and policy-declared; successful execution
normally proceeds directly to independent Zeus qualification. Provider
completion never qualifies an administrative transaction. After a managed
session completes, Zeus independently checks provider exit zero, session
integrity, authorized scope compliance, out-of-scope changes, protected
actions, evidence completeness, terminal reconciliation, and applicable
transaction/WOP criteria. Provider final-report prose is evidence only and is
not authority. No `mission_id` is required for the administrative path.

If an active requirement matches, Zeus exposes its requirement ID and reason
and stops at that requirement's specified operator-decision action. Otherwise
Zeus invokes its qualification contract automatically, persists the
qualification evidence/receipt, and exposes the canonical qualified state and
next authorized action. A failed qualification enters the existing corrective
or reconciliation path. Qualification replay is idempotent; Codex cannot
approve or qualify itself, and retains no protected Git, publication, or EOS
authority.

No parallel approval policy is inferred from provider completion, receipt
persistence, qualification, or successor resolution. When no active policy
entry matches, `OPERATOR_APPROVAL_REQUIRED=NO` and
`OPERATOR_ACCEPTANCE=NOT_APPLICABLE`; Zeus proceeds through its qualification
boundary automatically.

On success Zeus records `QUALIFIED_OR_ACCEPTED_TERMINAL` (with operator
acceptance marked `NOT_APPLICABLE` when no requirement matched) and exposes
the canonical successor (`C02_POST_ACCEPTANCE_TEST_RECONCILIATION` for the
current administrative corrective chain) as the next action. Replaying the
qualification request against that terminal state returns the same result
without launching a provider. Mission-history acceptance continues through
the existing mission-bound accept-reconciliation path.

## Recovery and closeout

Reconciliation acquires a transaction-scoped lock, discovers projections, classifies missing/partial/stale/duplicate/divergent/corrupt state, prepares and validates all writes, atomically promotes them, verifies the result, and emits a sealed reconciliation receipt. Interrupted work is resumed from the durable Stage 1 checkpoint or rolled back. Qualification, publication, EOS synchronization, and closeout remain gated by their receipts and parity checks.
