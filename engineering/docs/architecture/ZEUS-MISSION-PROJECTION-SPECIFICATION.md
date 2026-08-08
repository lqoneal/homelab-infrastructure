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

An admission is current only when its lifecycle permits execution and its bound
repository baseline equals the current Development baseline. An execution is
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

The same read-only canonical resolver consumes a contiguous P2 → P3 → P4
receipt chain when those downstream artifacts exist. P3 `ADMISSION_COMPLETE`
projects as `ADMITTED` with `EVALUATE_BOOTSTRAP_ELIGIBILITY`; P4
`READY_FOR_EXECUTION_PROVIDER` projects as `AWAITING_EXECUTION_DISPATCH` with
`EVALUATE_EXECUTION_PROVIDER`. Each downstream transaction must preserve the
P2 Mission/WOP/submission identity and its artifact digests. Duplicate or
orphaned canonical transitions fail closed. Stage 1 and provider/runtime
records remain subordinate compatibility evidence until their later lifecycle
waves qualify their integration; they cannot advance the canonical state.

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
