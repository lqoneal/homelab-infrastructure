# Zeus Controller Presentation Standard

Status: Beta-02 reconciled controller baseline

Human-readable and machine-readable controller output are two renderings of
one resolved authoritative object. Formatting must not perform a second state
calculation or maintain presentation authority.

## Active and historical views

`zeus mission list` is the active development view and resolves Operation Beta
missions only. Completed Operational Alpha work remains available through
`zeus mission completed`, `zeus mission history`, or `zeus mission archive`.
Roadmaps and operation-wide queue views may include completed work for progress
context.

Operation Beta is the active Development context. `OA-v1.0.0` remains the
Production baseline and historical Alpha context. The queue is operation-wide;
execution environment is bound only during admitted mission execution.

## Explain and queue contracts

Beta `mission explain` reports mission family, lifecycle, readiness,
dependencies, blockers, selection rationale, authority sources, and
production/development baselines. Queue projections report operation scope,
mission state, metrics, integrity, and the existing EMP selection interface.

Unknown missions, families, missing authority, conflicting state, invalid
dependencies, and production/development ambiguity fail closed.
