# Zeus Mission Queue and Scheduling Specification

Status: Beta controller-integrated planning baseline

## Authority and ownership

The mission queue is a read-only projection of authoritative mission state. It
does not own mission identity, lifecycle, priority, admission, or execution
order.

| Function | Owner | Existing interface |
| --- | --- | --- |
| staging and portfolio policy | EMP | `zeus submit`, `zeus missions list` |
| eligibility and dependency evaluation | Zeus | `zeus mission readiness`, `zeus mission blockers` |
| deterministic selection | Zeus | `zeus missions select`, `zeus mission queue next` |
| admission enforcement | Zeus / ZDCL boundary | `zeus admit-mission start` |
| synchronized platform state | EOS | EOS synchronization and validation |
| derived projections | CAGF-compatible projection layer | `zeus mission queue`, controllers |
| lifecycle events and notifications | EENS | event integration remains the event-system contract |

EMP's orchestration store remains the existing submission and prioritization
record. The WOP lifecycle manager remains the existing fail-closed lifecycle
boundary. No parallel queue, scheduler, mission registry, or admission store
is introduced by this specification.

## Submission and lifecycle

The authoritative submission path is:

```text
zeus submit <WOP_PACKAGE> [submission and policy options]
```

It records the authorized request in the existing EMP orchestration state,
including repository/baseline binding, priority, dependencies, approvals,
resources, and blocking conditions. Submission does not promise execution
order.

The admission path is separate and fail-closed:

```text
zeus admit-mission start ...
zeus execute-mission start --admission-id <ADMISSION_ID>
```

Admission verifies mission, authority, repository, baseline, agent, and
execution context before the execution boundary can be crossed.

## Queue projection

The following read-only projections are supported:

```text
zeus mission queue list
zeus mission queue show <MISSION_ID>
zeus mission queue next
zeus mission queue blockers
zeus mission queue history
```

When Beta is the active Development operation, these queue views resolve the
Beta operation-wide projection. Execution environment is an admitted mission
attribute and never a queue partition. Completed Alpha work is available from
the dedicated `zeus mission completed`, `history`, and `archive` views.

The projection reports submitted, staged, eligible, blocked, active, and
completed entries plus derived counts. It derives from the Mission Knowledge
Model and existing orchestration/lifecycle services. It never writes queue
state and never overrides authority, dependencies, readiness, or operator
policy.

The queue's `next` view is a readiness projection. Final scheduling selection
continues through `zeus missions select`, where EMP policy and priority are
applied after authoritative dependency and readiness checks. FIFO never
overrides a blocker, dependency, priority, or readiness condition.

## Fail-closed rules

The queue and admission views fail closed on missing or malformed authority,
unknown missions, invalid dependency graphs, lifecycle inconsistency,
repository/baseline drift, unauthorized admission, and production/development
state confusion. Metrics are recalculated from authoritative state for each
request and are not persisted as authority.

## Traceability

The existing records provide the following explainable path:

```text
submission -> validation -> staging -> eligibility -> selection
-> admission -> dispatch -> execution -> qualification -> acceptance
-> publication -> closeout
```

Where a legacy or historical record does not expose every intermediate event,
the projection reports the available authoritative state and does not invent
missing history.

## Admission lineage

Admission freshness is a prerequisite to selection and execution. Queue and
mission projections expose the submission ID, admission ID, admitted/current
baselines, freshness result, and supersession lineage when available. A stale
admission remains visible in history but is never projected as executable; the
fresh replacement is the active candidate when its authority and readiness
checks pass.
## Execution projection

When an admitted mission has an existing execution record, queue and mission
controllers project its execution ID, state, gate, wait category, diagnostics,
and resume action. These are read-only projections of the execution record;
the queue does not own execution state. A single active execution is resolved
automatically by the execution CLI, while ambiguous active executions fail
closed and require an explicit ID.
