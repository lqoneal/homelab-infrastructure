# Zeus Progressive Manual Capability Test Contract

Version: 1.0
Identity: `ZEUS_PROGRESSIVE_MANUAL_CAPABILITY_TEST`
Authority: ZEUS-P2-020
Current result: `NOT_READY`

## Normative behavior

The PMCT is cumulative. `OA-NN` evaluates that gate and treats every earlier
gate as regression scope. The sequence OA-01 through OA-30 in
`PMCT-CAPABILITY-MATRIX.yaml` is locked: gates cannot be removed, merged,
reordered, or silently redefined.

A capability passes only when Zeus demonstrates the behavior through the
authoritative interface, rejects an invalid case safely, proves idempotency,
proves interruption/resume where applicable, produces complete durable
evidence, and retains all eligible earlier capabilities. Manual review remains
mandatory. A run does not mutate the controlled capability-state record or
self-approve a gate.

Controlled states are:

- `PASS`: every mandatory observable assertion passed and evidence is complete.
- `FAIL`: an available required capability behaved incorrectly or unsafely.
- `BLOCKED`: repository identity, authority, or a prerequisite prevented testing.
- `NOT_READY`: a mandatory interface or demonstration is unavailable.
- `EXPECTED_NOT_YET_IMPLEMENTED`: discovery classification for a future command.
- `NOT_APPLICABLE`: a test dimension does not apply to the gate.

Final run output includes `PMCT_RUN_ID`, `PMCT_GATE`, `PMCT_RESULT`,
`ZEUS_PROGRESSIVE_TEST_RESULT`, `PMCT_REPORT`, `PMCT_EVIDENCE`, and
`PMCT_COMPLETION_MARKER=COMPLETE`. Exit zero is reserved for a demonstrated
`PASS`; `FAIL`, `BLOCKED`, and `NOT_READY` exit nonzero. The harness does not
use `set -e`, so diagnostic collection continues after individual failures.

## Fixed production CLI acceptance contract

```text
zeus status
zeus authority status
zeus authority work-lifecycle
zeus authority restoration
zeus dispatcher status
zeus dispatcher policy
zeus dispatcher activation
zeus dispatcher probe
zeus agent registry
zeus agent qualify
zeus agent status
zeus agent select
zeus admission evaluate
zeus invocation probe
zeus eens status
zeus eens self-test
zeus evidence self-test
zeus qualification self-test
zeus reconciliation self-test
zeus next-action
```

Command discovery maps availability to each gate. Missing future commands are
not faked. A command absent before its gate is eligible is
`EXPECTED_NOT_YET_IMPLEMENTED`; when a selected gate requires it, the run is
`NOT_READY` (or `FAIL` if controlled state already claims that gate complete).

## State protection

Read-only is the default. A state-changing gate must be named as such in the
matrix and requires `--authorized-transition`, active scoped authority,
visible preflight, request identity, idempotency, resulting-state verification,
and no automatic roll-forward. P2-020 implements no state-changing procedure;
supplying the flag therefore blocks safely. There is no generic bypass.

Every run creates a unique directory and create-only JSON records, hashes every
evidence artifact, records no secret environment values, and writes `COMPLETE`
last. Duplicate run directories are rejected.
