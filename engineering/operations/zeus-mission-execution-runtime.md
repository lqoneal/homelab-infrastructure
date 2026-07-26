# Zeus Mission Execution Runtime

## Purpose and safety boundary

ZEUS-P2-008 adds a persistent, restartable execution coordinator for WOPs
produced by the Mission Admission Runtime. It owns execution sequencing,
checkpoints, diagnostics, and evidence. It does not approve WOPs, resolve
authority, commission production, or provide an operational dispatcher.

The repository-local state store is:

`<repository>/.zeus/runtime/mission-executions/<execution-id>.json`

Published evidence is create-only under:

`<repository>/.zeus/runtime/mission-executions/published-evidence/<execution-id>/`

State and evidence are digest protected. Evidence entries form a hash chain and
are published as read-only JSON files. The execution state store is
operational runtime state, not an authority source.

## State model

The runtime supports:

- `Pending`
- `Authorized`
- `Preparing`
- `Executing`
- `Waiting`
- `Suspended`
- `Resuming`
- `Verifying`
- `Completed`
- `Failed`
- `Cancelled`

Terminal states are `Completed`, `Failed`, and `Cancelled`. Waiting and
suspended executions retain their current gate and may resume. Completed gates
are never rerun.

## Gate engine

The fixed runtime gates are:

1. `VALIDATE_WOP`
2. `PREPARE_EXECUTION`
3. `EXECUTE_WORK`
4. `VERIFY_COMPLETION`

Validation recomputes the WOP submission digest and applies the existing WOP
Admission Controller. Preparation verifies that the repository HEAD still
matches the baseline captured during admission. Execution and verification
delegate to a typed handler; the runtime passes a stable
`gate_idempotency_key` derived from execution and gate identity.

The runtime persists `GATE_STARTED` before invoking a handler. On recovery it
uses the current gate and completed checkpoints to retry only incomplete work.
A handler must use the supplied idempotency key when it can create external
effects.

## Qualification execution

Qualification admissions ending in `QUALIFICATION_ONLY` may traverse the full
execution state machine. The built-in qualification handler performs no
external side effects, submission, or dispatch:

```text
scripts/zeus execute-mission start --admission-id MISSION-ADMISSION-ID
```

The evidence identifies execution as `QUALIFIED_SIMULATION`. Review-only WOP
behavior is unchanged.

## Operational execution boundary

An operational execution requires an admission with decision `ACCEPTED` and an
exact WOP binding. The checked-in runtime has no operational dispatcher and
always stops at `EXECUTE_WORK` with
`OPERATIONAL_DISPATCH_DISABLED`. No CLI flag can enable dispatch.

A future separately commissioned integration must inject a controlled handler
and explicitly enable the runtime boundary after authentic commissioning. That
work is outside P2-008.

## Commands and recovery

```text
scripts/zeus execute-mission status --execution-id EXECUTION-ID
scripts/zeus execute-mission suspend --execution-id EXECUTION-ID \
  --reason "operator pause"
scripts/zeus execute-mission resume --execution-id EXECUTION-ID
scripts/zeus execute-mission cancel --execution-id EXECUTION-ID \
  --reason "operator cancellation"
```

`scripts/mission-executionctl` exposes the same actions. Store overrides are
test-only and require `ZEUS_TESTING=1`.

Do not hand-edit an execution state, checkpoint, or evidence entry. On digest
failure, preserve the affected files for investigation and restore a verified
whole-state backup. A failed execution is terminal; create a separately
reviewed retry admission/execution rather than rewriting its history.

## Evidence and EENS

Evidence captures execution creation, gate starts, gate completions,
validation and handler results, checkpoints, waits, suspensions, recovery
actions, failures, cancellation, produced artifact references, and completion.

`EensExecutionSink` adapts the same evidence to the existing append-only EENS
EventStore. Its idempotency key binds the execution identifier and evidence
digest. EENS is an additional durable event projection; the execution state
and published evidence remain the recovery source.

## Controlled-document disposition

This operational guide documents repository behavior. It does not change
approval authority, adopt an operational dispatcher, or authorize production
execution.
