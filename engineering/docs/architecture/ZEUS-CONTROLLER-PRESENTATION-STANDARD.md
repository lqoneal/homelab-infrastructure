# Zeus Controller Presentation Standard

Status: BETA-04 governed controller baseline

Normative invariants: `ENGINEERING-PLATFORM-INVARIANTS.md` and
`ZEUS-CONTROLLER-GOVERNANCE.md`

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
Normal output contains actionable state only. Operator orientation and command
guidance are available through `zeus intro`, `zeus --help`, and
`zeus --verbose COMMAND`; controllers never repeat the introductory banner by
default, including in JSON mode.

Controllers use four non-interchangeable terms:

- **Current Platform Mission**: the published platform-readiness mission,
  currently `BETA-04`.
- **Current Executable Mission**: the one mission with a fresh executable
  admission, or `NONE`.
- **Recommended Mission**: the eligible successor selected from roadmap
  authority, currently `ZDCL-01`.
- **Next Authorized Action**: the exact permitted transition; a recommendation
  is not execution authority.

No object may be labeled as two different current missions. Human and JSON
forms expose these distinctions from the same resolved object.

## Explain and queue contracts

Beta `mission explain` reports mission family, lifecycle, readiness,
dependencies, blockers, selection rationale, authority sources, and
production/development baselines. Queue projections report operation scope,
mission state, metrics, integrity, and the existing EMP selection interface.

Unknown missions, families, missing authority, conflicting state, invalid
dependencies, and production/development ambiguity fail closed.

## Current versus historical lifecycle state

All mission controllers consume the canonical mission projection. It exposes
`current_admission`, `current_execution`, `historical_admissions`, and
`historical_executions` as separate fields. Current execution is resolved from
active lifecycle state, never from the most recent record. A cancelled,
completed, failed, or superseded execution appears only in history interfaces.

When an active admission exists but no execution exists, explain and next-action
report `Execution State: NONE`, `Ready: YES`, and the exact authorized start
command. Multiple current records fail closed with their conflicting IDs.
