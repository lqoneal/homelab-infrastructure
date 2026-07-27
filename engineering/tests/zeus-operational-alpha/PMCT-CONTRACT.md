# Zeus Progressive Manual Capability Test Contract

Version: 1.0
Identity: `ZEUS_PROGRESSIVE_MANUAL_CAPABILITY_TEST`
Authority: ZEUS-P2-020
Current overall result: `NOT_READY` (OA-01 Codex demonstration `PASS`;
independent operator verification pending; operator acceptance not recorded;
OA-02 blocked; OA-02 through OA-30 not accepted)

## Normative behavior

The PMCT is cumulative. `OA-NN` evaluates that gate and treats every earlier
gate as regression scope. The sequence OA-01 through OA-30 in
`PMCT-CAPABILITY-MATRIX.yaml` is locked: gates cannot be removed, merged,
reordered, or silently redefined.

A capability passes only when Zeus demonstrates the behavior through the
authoritative interface, rejects an invalid case safely, proves idempotency,
proves interruption/resume where applicable, produces complete durable
evidence, and retains all eligible earlier capabilities. Manual review remains
mandatory. A PMCT `PASS` is a Codex demonstration result, not operator
verification or gate acceptance. A completed run atomically reconciles the
controlled capability-state ledger with its run ID, completion time, result,
and evaluated gate. It does not record operator verification, record operator
acceptance, or self-approve a gate.
No later gate is eligible until the preceding gate has both a `PASS`
demonstration and separately recorded operator acceptance.

Independent verification is a checksummed durable record distinct from Codex
validation and operator acceptance. It binds the gate, exact PMCT run,
repository and qualified HEAD, evidence and evidence-manifest digests,
operator identity and timestamp, WOP identity, and WOP manifest digest.
`zeus approve OA-NN` cannot prompt until a matching `zeus verify OA-NN` record
exists. After explicit confirmation it revalidates the complete binding before
calling the internal persistence primitive.

The immutable acceptance receipt additionally binds the verification record
and its digest, approval time, and interactive or noninteractive confirmation
mode. Duplicate receipt creation is rejected.

Controlled states are:

- `PASS`: every mandatory observable assertion passed and evidence is complete.
- `FAIL`: an available required capability behaved incorrectly or unsafely.
- `BLOCKED`: repository identity, authority, or a prerequisite prevented testing.
- `NOT_READY`: a mandatory interface or demonstration is unavailable.
- `EXPECTED_NOT_YET_IMPLEMENTED`: discovery classification for a future command.
- `NOT_APPLICABLE`: a test dimension does not apply to the gate.

Operator-verification lifecycle uses a separate, non-terminal readiness
vocabulary and must not be confused with PMCT demonstration results:

- `READY`: publication, authority, repository identity, and current HEAD
  prerequisites permit independent verification, but no matching evidence
  exists;
- `NOT_READY`: verification prerequisites are unsatisfied;
- `PASS`: independent verification executed and produced an integrity-valid
  record for the current binding;
- `FAIL`: independent verification executed and failed;
- `ABSENT`: the evidence-presence value when no verification record exists.

A stale, failed, malformed, or differently bound verification record remains
historical evidence but is treated as absent for a current binding whose
prerequisites are satisfied. It cannot suppress current readiness or satisfy
verification.

At the post-P2-025 publication boundary, OA-01 operator verification is
`READY` with evidence `ABSENT`. The earlier Codex demonstration remains a
separate `PASS`; neither value records operator acceptance.

Final run output includes `PMCT_RUN_ID`, `PMCT_GATE`, `PMCT_RESULT`,
`ZEUS_PROGRESSIVE_TEST_RESULT`, `PMCT_REPORT`, `PMCT_EVIDENCE`, and
`PMCT_COMPLETION_MARKER=COMPLETE`. Exit zero is reserved for a demonstrated
`PASS`; `FAIL`, `BLOCKED`, and `NOT_READY` exit nonzero. The harness does not
use `set -e`, so diagnostic collection continues after individual failures.
`pmct inspect <PMCT-RUN-ID>` and `pmct report <PMCT-RUN-ID>` resolve only that
completed run. Gate-based `pmct report OA-NN` is retained as an interactive
latest-run convenience and is not sufficient for exact-run evidence proof.

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

Authoritative-state observation is the default. Inspection commands shall not
modify authoritative engineering state, tracked repository content, or
operational decision state. A PMCT run has one explicit controlled-write
exception: after sealing its evidence, it atomically updates the PMCT
capability-state ledger with the exact completed run. It shall not modify any
other authoritative or operational decision state:

- authoritative engineering state includes published baselines, authority,
  project state, PMCT capability state, qualification state, dispatcher state,
  execution state, and mission state;
- repository state means tracked repository content and Git identity;
- operational decision state includes the next authorized action, capability
  qualification, Operational Alpha progression, dispatcher authorization, and
  production eligibility.

Authority activation is operational state, but it is stored as create-only,
read-only-after-publication, integrity-verified artifacts plus an
integrity-bound active pointer outside tracked Git content.
Activation therefore cannot change the HEAD being published. Gate acceptance
history is append-only: successor receipts bind the exact predecessor digest,
and a historical receipt never authorizes a different repository HEAD,
PMCT run, or evidence binding.

Lifecycle precedence is publication, current-binding gate verification,
explicit matching acceptance, and only then next-gate pre-execution
eligibility. Dispatcher commissioning cannot be selected while the current
gate still awaits verification or acceptance.

Runtime presentation telemetry is permitted only when it is explicitly
documented, deterministic, bounded, non-authoritative, and never consumed by
engineering decisions, PMCT qualification, authority resolution, dispatcher
logic, or promotion decisions. The currently approved example is the
operator-interface `invocation_count`. PMCT evidence creation beneath
`engineering/runtime/pmct/runs/` is separately required test output, not
presentation telemetry. The corresponding capability-state reconciliation is
authoritative PMCT metadata and is never verification or acceptance.

The capability-state file has a dual persistence contract: the committed copy
is the version-controlled schema and last reconciled baseline, while the
working-tree copy may contain exactly one completed-run reconciliation. Gate
verification does not ignore that tracked delta. It reconstructs the expected
file from the committed copy plus the selected integrity-verified PMCT result
and manifest, and accepts it only when:

- it is the sole tracked modification;
- it is unstaged;
- every resulting field equals the deterministic reconciliation;
- the run matches repository, HEAD, implementation baseline, published
  baseline, and active authority publication.

Any staged capability-state change, additional tracked path, malformed state,
or field not derived from the selected run fails the clean-worktree gate.
Thus PMCT runtime output does not force a commit/publication loop and cannot
mask an arbitrary source modification.

Gate verification selects only a PMCT `PASS` whose manifest matches the
current repository path, HEAD, implementation baseline, published baseline,
and active authority publication. Historical runs remain preserved but are
ineligible after any of those bindings changes.

A state-changing gate must be named as such in the matrix and requires
`--authorized-transition`, active scoped authority, visible preflight, request
identity, idempotency, resulting-state verification, and no automatic
roll-forward. P2-020 implements no state-changing procedure; supplying the
flag therefore blocks safely. There is no generic bypass.

Every run creates a unique directory and create-only JSON records, hashes every
evidence artifact, records no secret environment values, and writes `COMPLETE`
last. Duplicate run directories are rejected.
