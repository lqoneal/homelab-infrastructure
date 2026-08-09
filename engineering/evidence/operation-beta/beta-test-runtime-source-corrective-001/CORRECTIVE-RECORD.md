# Beta Historical Runtime/Test-Source Corrective Record

## Record identity

- Corrective ID: `BETA-TEST-RUNTIME-SOURCE-CORRECTIVE-001`
- Scope: Zeus/Operation Beta test-runtime isolation and historical-state resolution
- Classification: `TEST_FIXTURE + STALE_ORPHANED_RUNTIME + INCOMPLETE_RECONCILIATION`
- Recorded at: `2026-08-07`
- Status: `RECORDED_FOR_SUBSEQUENT_AUTHORIZED_IMPLEMENTATION`
- Related CAGF WOP: none; this record is not part of `WOP-OB-CAGF-G01-CANONICAL-001`

## Diagnosed condition

- `BLOCKER_CODE=BETA_TEST_HISTORY_MISSING; RUNTIME_WRITE_UNAVAILABLE`
- `BLOCKER_MESSAGE=AssertionError: cancelled execution is not retained in history; focused authority tests fail with [Errno 30] Read-only file system`
- `BLOCKING_OBJECT=MISSION-EXECUTION-8c444488-9ee3-5e03-949f-dc750a0b918c`
- Historical mission: `ZDCL-01`
- Historical state: `Cancelled`
- Historical WOP: `WOP-ZDCL-01-FOUNDATION-001`
- `BLOCKING_STATE_SOURCE=.zeus/runtime/mission-executions historical store versus selected user-state runtime`
- `BLOCKING_STATE_OWNER=Zeus Operation Beta projection/test runtime`

The cancelled ZDCL-01 execution is valid immutable historical evidence. Native current-state resolution excludes it from active work, while the affected projection tests resolve the user-state runtime and therefore do not see the repository historical fixture. Focused authority tests additionally attempt to initialize a runtime under a read-only root. No active provider, session, listener, or execution process was present.

## Required future corrective

1. Define one explicit runtime-source contract for tests that inspect historical lifecycle evidence. The contract must identify the source, repository identity, fixture identity, and read-only versus writable mode.
2. Make historical projection tests consume the same canonical runtime-resolution model as native Zeus, with the cancelled ZDCL-01 fixture explicitly retained in historical state.
3. Give tests that require mutation an isolated writable runtime root created by the test harness; never use the operational user-state runtime for fixture mutation.
4. Preserve the cancelled execution and all immutable historical evidence. Do not copy, rewrite, delete, archive, or reconcile it merely to satisfy an assertion.
5. Fail closed when the runtime source is ambiguous, unavailable, read-only for a mutating test, or inconsistent with repository identity.
6. Prove deterministic isolation, cleanup, no operational-runtime contamination, and repeatable historical projection through focused and regression tests.

## Acceptance criteria for a later implementation

- Historical-state tests deterministically expose the cancelled ZDCL-01 execution in `history`, not `current`.
- Mutation-capable tests use a distinct writable runtime root and leave the operational runtime unchanged.
- Read-only tests perform no persistent runtime writes.
- A missing, mismatched, or unwritable runtime source produces a specific fail-closed diagnostic.
- Repeated runs produce identical historical projections and no duplicate lifecycle records.
- Focused Beta platform invariants, mission projection, and authority reconciliation tests pass in their declared modes.
- Existing native platform and Operation Beta verification remain passing.
- The historical execution record remains byte/integrity consistent.

## Dependency classification

`RUNTIME_TEST_CORRECTIVE_TECHNICAL_DEPENDENCY_OF_CAGF_G01=NO`

Rationale: CAGF-G01 consumes qualified source/projection contracts and has zero mission-authority dependencies. The corrective concerns test runtime-source selection and fixture isolation only. Native Operation Beta verification passes independently, and no CAGF requirement or interface reads, writes, or depends on the ZDCL-01 historical execution fixture. The corrective must not be added as a CAGF gate or requirement.

## Reconciliation boundary

- Existing read-only interface: `zeus mission legacy-reconciliation MISSION-BETA-562F443E16C69401 --json`
- Observed result: `PASS`, disposition `RECONCILED_HISTORICAL`, execution liveness `STOPPED`, repository work pending `false`, receipt `null`, replay `NOT_PERSISTED`
- Persistent reconciliation: not performed
- Corrective implementation: not performed
- Historical ZDCL record: preserved

## Safety and authorization

- No authority created or changed.
- No mission submitted, admitted, selected, or executed.
- No execution/provider/session state changed.
- No EOS or operational runtime mutation performed.
- Subsequent implementation requires separate operator authorization and must remain outside the CAGF-G01 WOP.

## Next authorized action

`OPERATOR_REVIEW_AND_SEPARATELY_AUTHORIZE_BETA_TEST_RUNTIME_SOURCE_CORRECTIVE`
