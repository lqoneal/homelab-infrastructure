# Zeus Mission Projection Specification

Status: BETA-03F reconciled

Mission controllers consume one canonical, read-only mission projection. The
projection separates current operational state from immutable lifecycle history.

## Projection contract

Each mission projection exposes exactly:

- `current_admission`: one fresh, executable admission or `null`;
- `current_execution`: one active execution or `null`;
- `historical_admissions`: immutable prior admissions;
- `historical_executions`: immutable completed, cancelled, failed, or superseded executions.

An admission is current only when its lifecycle permits execution and its
immutable bound repository provenance is valid against the synchronized live
Development baseline. The canonical resolver proves repository identity,
`HEAD == origin/main == EOS`, and descendant ancestry; legitimate subsequent
publication does not mutate the admission record. A boundary that requires a
fresh equal-baseline admission must say so explicitly. An execution is
current only while it is in an active execution state. Cancelled and completed
records are never selected by recency.

## Controller rules

`mission explain`, status, queue, health, next-action, and operation views use
the same resolved projection object for human-readable and JSON output. They do
not search execution records independently or infer lifecycle state.

History, archive, evidence, qualification, and completion views may expose
historical records explicitly. Active views must not expose those records as
current state.

If multiple current admissions or executions exist, the projection fails closed
with the conflicting identifiers. If none exists, the projection reports
`current_execution: null`, execution state `NONE`, and the next authorized
action needed to proceed.

The resolver is read-only. It does not mutate runtime state, historical
evidence, production baseline `OA-v1.0.0`, or development planning baseline
`OB-PLAN-v1.0.0`.

## Canonical repository projection and Git automation contract

Current repository facts are consumed through the canonical read-only
projection exposed by `zeus repository projection --json`. Automation MUST
prefer stable Git plumbing or machine-oriented porcelain over human-oriented
output. The projection resolves repository identity, root, branch, HEAD,
`refs/remotes/origin/main`, HEAD/origin parity, index and tracked/untracked
worktree state, and EOS baseline/parity from live sources on every request.

The Git automation contract requires explicit refs, exit-code boolean checks,
NUL-delimited path collections, and `GIT_TERMINAL_PROMPT=0` for unattended
read-only Git operations. Ancestry uses `git merge-base --is-ancestor`; normal
`git status`, `git log`, or `git diff` text is not parsed when a stable
plumbing/porcelain interface exists. Operator-interactive publication remains
separate and may intentionally support credential prompting.

Lifecycle code follows Live Projection First: canonical live projection,
receipt-backed derived projection, authoritative persisted source, explicitly
bounded fallback, then hardcoded value only as a documented last resort. A
hardcoded current repository value, baseline, path, or authority state may not
override a live projection. Immutable protocol constants, schema enumerations,
historical evidence literals, test vectors, and explicitly documented
compatibility fallbacks are not current-state authority. Projection failure,
unavailable required refs, or contradictory EOS state fails closed rather than
returning guessed defaults.

### Machine interface rule

Zeus machine-to-machine execution uses canonical identifiers, typed operations,
explicit authority and state operands, deterministic exit codes, and
machine-readable contracts and results. Natural-language prose is not the
authoritative representation of executable work when equivalent semantics can
be represented structurally. Current-state operands are resolved from
canonical live Zeus projections wherever available; hardcoded runtime or
current-state data is a last resort and must be explicitly documented.
Structured JSON/YAML contracts are preferred for mission execution, WOP/work
execution, provider selection and dispatch, provider invocation and execution
sessions, publication, qualification, synchronization, and lifecycle
transitions.

For a submitted Development WOP whose canonical receipt state is
`ADMISSION_REQUESTED`, the P2 submission receipt and its immutable admission
request are the current mission projection. Zeus mission `show`, `state`,
`status`, `readiness`, `eligibility`, `authority`, `blockers`, `next`, and
`snapshot` surfaces consume that same resolver. The canonical next action is
`EVALUATE_MISSION_ADMISSION`; historical execution records and compatibility
projections cannot override it. Missing, ambiguous, contradictory, or
digest-invalid receipt evidence fails closed.

`zeus mission list --json` uses the same P2 submission receipt index. It may
also include Operation Beta planning entries, which remain a separate
planning projection; a submitted mission is added only after its P2 receipt
and admission-request chain resolve. A missing receipt is not routed through
an OA-01 selector or converted into a Mission Contract. Current mission
queries that do not resolve canonically return `MISSION_NOT_FOUND` or an
explicit canonical failure, preserving fail-closed behavior.

The same read-only canonical resolver consumes a contiguous P2 → P3 → P4 → P5
receipt chain when those downstream artifacts exist. P3 `ADMISSION_COMPLETE`
projects as `ADMITTED` with `EVALUATE_BOOTSTRAP_ELIGIBILITY`; P4
`READY_FOR_EXECUTION_PROVIDER` projects as `AWAITING_EXECUTION_DISPATCH` with
`EVALUATE_EXECUTION_PROVIDER`. Each downstream transaction must preserve the
P2 Mission/WOP/submission identity and its artifact digests. Duplicate or
orphaned canonical transitions fail closed. Stage 1 and provider/runtime
records remain subordinate compatibility evidence until their later lifecycle
waves qualify their integration; they cannot advance the canonical state.

P3 artifact cardinality is scoped to the requested canonical identity, not to
the total number of JSON files in the append-only runtime directories. The
current P3 set is the exactly one artifact set bound to the active P2
Mission/WOP/submission identity and repository runtime. Preserved records for
other missions, prior submissions, superseded revisions, or explicit legacy
compatibility remain historical evidence and are excluded from current
authority. Zero current candidates, more than one exact current candidate,
identity/digest disagreement, or a current P3 set with missing artifacts
fails closed. No historical artifact is deleted, rewritten, or selected by
recency.

P4 bootstrap cardinality follows the same mission-scoped rule. The current P4
set is the exactly one artifact chain bound to the active Mission ID, WOP ID,
submission receipt, admission receipt, bootstrap ID, repository binding, and
bootstrap transaction provenance. Preserved P4 chains for other missions,
historical submissions, superseded revisions, or explicit legacy compatibility
are classified as historical/subordinate and do not compete with current
cardinality. The P4 verifier also scopes prohibited downstream-artifact checks
to that same identity, so historical dispatch/provider/session evidence cannot
invalidate a current pre-provider P4 chain. Zero current candidates, duplicate
current candidates, invalid identity or digest provenance, and any downstream
artifact bound to the current chain fail closed. Replay returns the same
bootstrap identity and remains idempotent.

Provider-selection projections use the same immutable-provenance/live-lineage
contract. A provider-selection receipt records the publication baseline seen
when that transition was created; it is not a permanent requirement that
receipt baseline equal the current HEAD. Current validity requires repository
identity, Mission/WOP and receipt bindings, and a live
HEAD=origin/main=EOS projection whose Git history descends from the recorded
provider-selection baseline. Non-descendant history, identity or digest
contradiction, and ambiguous current target artifacts fail closed. Provider
selection is point-in-time evidence; the later dispatch boundary revalidates
live provider availability and qualification from the execution-agent registry.

Provider dispatch and provider-session establishment are separate, receipt-backed
Wave 2 transitions. `zeus dispatch create <MISSION_ID> --json` consumes the
current provider-selection projection and creates exactly one mission/WOP/
provider-bound dispatch set whose terminal state is
`READY_FOR_PROVIDER_SESSION`; replay is idempotent and does not invoke a
provider. `zeus provider-session create <MISSION_ID> --json` consumes that
dispatch set and creates exactly one dispatch-bound provider-session set whose
terminal state is `READY_FOR_PROVIDER_INVOCATION`; replay is idempotent and
does not invoke a provider or start execution. Historical and cross-mission
dispatch/session artifacts are preserved and excluded from current cardinality.
The canonical lifecycle state advances through the furthest verified
receipt-backed boundary while these projections expose current provider
identity, dispatch identity, session identity, and the next authorized action.
A stale P4 `AWAITING_EXECUTION_DISPATCH` value cannot override valid P5
dispatch, session, invocation, or execution-start receipts. Native mission
commands and `zeus status` use the same full downstream projection after these
artifacts exist; disagreement is a verification failure.

Provider invocation and execution-session establishment are later, distinct
receipt-backed boundaries. `zeus provider-invocation create <MISSION_ID>`
requires the verified provider-session chain and records one provider-bound
acknowledgement; replay is idempotent. The current foundation adapter uses
`QUALIFICATION_ADAPTER` semantics: it does not launch Codex or begin mission
work. `zeus execution-start create <MISSION_ID>` then establishes one
mission/WOP/provider/invocation-bound idle execution session and stops at
`READY_FOR_CONTROLLED_EXECUTION`; replay preserves the execution identity.
`execution-start begin` is the separate controlled mission-work boundary and
is not implied by either foundation transition. Historical and cross-mission
invocation/session/execution artifacts remain preserved and excluded from
current target-mission cardinality. Missing, conflicting, or ambiguous
current artifacts fail closed.

## Operation-wide current execution projection

Operation Beta consumes the canonical submitted-mission index and resolves
each current candidate through the same canonical lifecycle resolver used by
mission-native views. Exactly one nonterminal receipt-backed mission may own
Current Executable Mission. More than one current claim, a duplicate current
claim, or index/resolver disagreement fails closed. Unresolved compatibility
records and terminal historical missions remain visible as history but cannot
become current by recency or filesystem order.

The Operation projection carries the resolver-owned Mission ID, WOP ID,
lifecycle state, work-start flags, and lifecycle next action. The planning
selector remains separately exposed as Future Recommended Mission. A roadmap
row or CAGF candidate cannot create execution authority, and a stage-local
next action cannot replace the global lifecycle next action. Runtime recovery
is a separate subordinate field and does not advance lifecycle state.

## Authority and mission-native aggregate boundary

Current consumers use the `ZEUS-CANONICAL-AUTHORITY-RECEIPT/1` adapter. A P2
receipt's canonical authority envelope is authoritative for the current
mission. Stage 1 authority snapshots and autonomous dispatch receipts are
explicit `STAGE1_LEGACY` or `AUTONOMOUS_LEGACY` compatibility inputs; they are
normalized for inspection only and never silently promoted to current
authority. Missing, duplicate, digest-invalid, identity-conflicting, or
semantically contradictory authority receipts fail closed.

`zeus mission aggregate <MISSION_ID> --json` is the mission-native read-only
aggregate for provider, dispatch, provider-session, execution, process,
monitoring, and evidence observations. It consumes the canonical resolver
first. Downstream identities are exposed only when their bound records exist
and verify; absent downstream records are reported as `NOT_STARTED` or
`NOT_AVAILABLE`. Historical, stopped, superseded, and reconciled sessions are
preserved as history and cannot expose current execution readiness. The
aggregate does not create receipts, select providers, create sessions, start
execution, or mutate lifecycle state.

## Monitoring and recovery projection

Monitoring and recovery remain subordinate to the receipt-backed canonical
lifecycle chain. The `ZEUS-CANONICAL-RECOVERY/1` contract defines immutable
checkpoint, interruption-receipt, and resume-request envelopes under the
runtime's recovery directories. Each envelope binds the mission, WOP,
execution, provider, session, repository identity and baseline, source digest,
lifecycle position, and evidence position.
The structural contract is recorded in
`engineering/oversight/recovery-contract.schema.yaml`.

`zeus mission recovery <MISSION_ID> --json` is a read-only mission-native view.
It reports monitoring ownership, interruption state, checkpoint identity,
resume eligibility, completed-work position, and evidence position. Missing
downstream execution state remains `NOT_STARTED`; provider/session/process
liveness is observational and cannot advance the canonical lifecycle.

A checkpoint is selected only when exactly one identity-valid current record
exists. Missing, stale, digest-invalid, identity-conflicting, or multiple
checkpoints fail closed. Resume requests preserve the existing execution ID,
skip work already recorded complete, and are create-only/idempotent; they do
not invoke a provider or manufacture lifecycle progression. Historical or
reconciled checkpoints are never resumable.

## Publication transaction projection

Mission publication fields are subordinate projections of one authoritative,
persisted publication transaction. `PREPUBLICATION_VERIFIED` is visible only
when the transaction records `prepublication_result=PASS`, references a valid
digest-bound milestone receipt, moves the milestone from pending to completed,
and survives a fresh runtime reload. Until then the publication next action is
`VERIFY_PREPUBLICATION` or an explicit recovery action; it is never staging.

The publication transaction state resolver exclusively derives publication
next actions. Repository, candidate, and cohort projections may invalidate or
block that action, but no read model may advance beyond the durable milestone.
Transient verification success and an unreferenced receipt grant no authority.
Verification/persistence failure is fail-closed, and unchanged verify-pre
replay preserves one receipt and the same staging-readiness state.

## Managed runtime resolution and continuation contracts

Instruction handoff and managed continuation are separate contracts. Future
instruction handoffs conform to
`engineering/oversight/codex-handoff-contract.schema.yaml` and are accepted
read-only through `zeus codex handoff` by file or stdin. They carry bounded
instructions and never create mission, WOP, execution, provider, session,
approval, recovery, or supersession authority. The managed continuation
contract below remains the only structured continuation transaction for an
already authorized managed execution.

Managed Codex selectors use one precedence policy:

`mission-qualified live authoritative binding > live execution/provider/session state > historical or reconciled records`.

The policy is shared by mission-qualified, `--active`, and `--latest` managed
selectors. A reconciled historical record cannot supersede a live binding due
to timestamp, sequence, filesystem order, or discovery order. Equal-authority
ambiguity fails closed.

Managed Codex lifecycle state has three non-interchangeable identities:

1. Zeus execution identity: mission, WOP, execution, execution-session,
   provider, provider-session, and `CODEX-SESSION-*` wrapper IDs.
2. Codex transport identity: the replaceable local broker/app-server process,
   STDIO connection, websocket listener, socket, endpoint, and related PIDs.
3. Codex persisted-thread identity: the native thread ID and its rollout/index
   state under the bound `CODEX_HOME`.

Transport liveness never proves thread validity or invalidity. A dead transport
plus a valid persisted thread resolves to
`RESTART_CODEX_TRANSPORT_AND_RESUME_THREAD`; native `thread/resume` must return
the same thread ID. A valid thread is forked only under an explicit
fork-required decision using native `thread/fork`, and the new thread must name
its native parent. Missing, corrupt, incompatible, cross-boundary, or
concurrently owned threads resolve to `THREAD_RECOVERY_BLOCKED`. Resume failure
cannot silently create a thread, and new-thread creation requires explicit
canonical recovery authority. These rules are transport-neutral for local
STDIO and remote app-server connections and replay-safe.

Machine continuation uses the structured contract at
`engineering/oversight/work-contract.schema.yaml`:

```text
scripts/zeus codex resume <MISSION_ID> --approve --work-contract PATH --json
```

Zeus validates the contract schema and exact mission, execution, execution
session, provider, and provider-session bindings before continuation. It
persists the source digest, normalized contract digest, binding snapshot, and
append-only acceptance event under the managed runtime. Replaying the same
contract against the same binding is idempotent; mismatched, stale, or
superseded bindings fail closed. The contract is a Zeus transaction and is not
translated into arbitrary prose for an unrelated `codex exec` invocation.
