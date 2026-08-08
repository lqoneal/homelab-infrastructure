# Admission Supersession and Resume Reconciliation

## Findings

The cancelled-execution mismatch was a stale fixture. Current admission
supersession lineage resolves execution records from the selected
repository-bound user-state runtime. The test copied the predecessor admission
and execution only from the historical repository-local `.zeus/runtime`
store, so the current resolver correctly found no current cancelled execution.
The fixture now places that immutable execution evidence in an isolated
selected-runtime fixture. The production resolver was not weakened to consult
historical repository-local state implicitly.

The stale-terminal-chain failure was an obsolete expectation. The current
`resolve_for_resume` contract is explicitly read-only; it validates the
terminal successor baseline and fails closed when that baseline is stale. A
mutating successor is created only by the governed supersession/start path.
The test now proves the stale chain fails closed and that all admission files
remain byte-identical.

## Result

- Predecessor admission remains immutable: PASS.
- Cancelled execution lineage is preserved when present in current selected
  runtime: PASS.
- Stale successor classification is deterministic: PASS.
- Current-baseline successor path remains covered by existing supersession
  tests: PASS.
- Contradictory baseline and lineage cases remain fail closed: PASS.
- Read-only resume does not mutate: PASS.
- Atomic mutation remains confined to `resolve_for_start`: PASS.
- Replay/idempotency: PASS.

No admission runtime production behavior was changed.
