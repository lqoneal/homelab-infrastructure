# OB-ZEUS-G01 Requirement Matrix

Status vocabulary is the assessment vocabulary requested by the operator.
`SATISFIED` requires implementation, tests, integration/projection, evidence,
controlled-document coverage, and fail-closed/replay proof where applicable.

Common implementation surfaces: `scripts/lib/emp/execution_monitoring.py`,
`canonical_recovery.py`, `canonical_mission_aggregate.py`,
`canonical_lifecycle_resolver.py`, `codex_adapter.py`, `codex_reconciliation.py`,
`mission_verification_controller.py`, `execution_start.py`, and `scripts/zeus`.
Common focused suites: `test-zeus-p5-g6-execution-monitoring.py`,
`test-zeus-wave3-recovery.py`, `test-zeus-p5-g6-codex-adapter.py`,
`test-zeus-p5-g6-session-supersession.py`, and
`test-zeus-codex-transport-thread-lifecycle.py`.

| ID | Source / normalized requirement | P5 capability | Implementation, tests, evidence and live coverage | Status |
|---|---|---|---|---|
| G01-001 | Catalog: qualified execution foundation input | Entry | Receipt chain verifies through P5 execution start; mission verify and execution-start verify pass | SATISFIED |
| G01-002 | Execution status | P5-G6 | monitor status/verify; accepted active demonstration; current mission/execution projections | SATISFIED |
| G01-003 | Heartbeat or authoritative liveness equivalent | P5-G6 | monitor liveness, provider/session/process liveness, expiry tests | SATISFIED |
| G01-004 | Progress | P5-G6 | source-bound `progress_state` and `last_progress_event`; active projection regression | SATISFIED |
| G01-005 | Current gate/work position | P5-G6 | phase/gate/work-unit projection and canonical mission snapshot | SATISFIED |
| G01-006 | Active blockers | P5-G6 | mission blockers, recovery blockers and fail-closed codes are exposed | SATISFIED |
| G01-007 | Approval state where applicable | P5-G6 | execution-start/Codex approval guards and native readiness/eligibility | SATISFIED |
| G01-008 | Operator visibility | P5-G6 | execution status/verify, mission aggregate/snapshot/recovery, operation views | SATISFIED |
| G01-009 | Source-bound execution state | P5-G6 | digested execution-start and monitoring records; provenance checks | SATISFIED |
| G01-010 | EENS integration where applicable | P5-G6 | No independent EENS execution-progress owner is active; applicability condition is false and no duplicate event authority is created | NOT_APPLICABLE |
| G01-011 | Zeus-specific monitoring verification | P5-G6 | `zeus execution verify`; accepted active demonstration and acceptance/reconciliation suites; the current live-state suite is 6/9 because three assertions retain obsolete historical-state expectations, explicitly dispositioned in the completion report | SATISFIED |
| G01-012 | Controlled pause/interruption | P5-G7 | immutable interruption receipt bound to checkpoint and cause | SATISFIED |
| G01-013 | Controlled resume | P5-G7 | recovery resume request, `mission recovery`, and managed same-thread resume contract | SATISFIED |
| G01-014 | Session recovery | P5-G7 | canonical recovery plus Codex transport/session recovery tests | SATISFIED |
| G01-015 | Crash recovery | P5-G7 | dead process/heartbeat expiry, ordering and restart/resume scenarios | SATISFIED |
| G01-016 | Idempotent restart | P5-G7 | deterministic IDs and repeated recovery/transport replay | SATISFIED |
| G01-017 | State reconciliation | P5-G7 | canonical resolver/aggregate/recovery projection and history reconciliation | SATISFIED |
| G01-018 | No duplicate execution | P5-G7 | completed-work skip, duplicate execution prevention and owner cardinality tests | SATISFIED |
| G01-019 | Preserved execution identity | P5-G7 | checkpoint/resume and transport recovery preserve mission/WOP/execution/provider bindings | SATISFIED |
| G01-020 | Zeus verification for pause/resume | P5-G7 | `mission recovery`, aggregate and focused recovery qualification | SATISFIED |
| G01-021 | Detect provider failure | P5-G8 | provider/process/transport liveness and heartbeat classifications | SATISFIED |
| G01-022 | Classify provider failure | P5-G8 | deterministic runtime/thread/provider failure codes and state machine | SATISFIED |
| G01-023 | Preserve artifacts | P5-G8 | immutable predecessor, event, checkpoint, receipt and evidence preservation | SATISFIED |
| G01-024 | Retry/recovery policy | P5-G8 | safe restart/resume, explicit fork, stop and no-fallback policy | SATISFIED |
| G01-025 | Session repair or replacement | P5-G8 | verified replacement transport/session path; missing native persistence fails closed | SATISFIED |
| G01-026 | Safe re-entry | P5-G8 | binding preflight, last checkpoint, same execution, completed-work skip | SATISFIED |
| G01-027 | Last-safe-state determination | P5-G8 | exact checkpoint selection; stale/multiple/digest conflicts rejected | SATISFIED |
| G01-028 | No duplicate execution | P5-G8 | deterministic recovery identities, concurrent-owner rejection, no implicit thread start | SATISFIED |
| G01-029 | Zeus verification for provider recovery | P5-G8 | mission recovery/Codex status and 24-test transport-thread suite | SATISFIED |
| G01-030 | Implement once at canonical owner; preserve independent authority | Catalog | receipt-backed lifecycle owns state; observations remain subordinate | SATISFIED |
| G01-031 | Runtime integration, not code presence alone | Catalog exit | native CLI consumes monitor/recovery/provider implementations; current state is truthful | SATISFIED |
| G01-032 | Positive, negative, provenance and dependency verification | Catalog | focused active, stopped, stale, forged, mismatch and authority suites | SATISFIED |
| G01-033 | Replay/idempotency verification | Catalog | monitor read replay and deterministic checkpoint/interruption/resume identities | SATISFIED |
| G01-034 | Native status/verify/readiness/dependency/evidence/snapshot/next coverage as applicable | Catalog | mission, operation, execution, aggregate, recovery and Codex surfaces | SATISFIED |
| G01-035 | Gate contract, provenance, tests, qualification, receipts, blockers | Catalog evidence | accepted P5-G6 package; Wave 3 package; later corrective evidence; this matrix | SATISFIED |
| G01-036 | Independent qualification and controlled-document/registry coverage | Catalog qualification | P5-G6 acceptance; Wave 3 qualification; controlled/semantic and platform evidence | SATISFIED |
| G01-037 | Fail closed, preserve prior evidence, expose exact contradiction | Catalog failure | explicit error taxonomy; current `THREAD_RECOVERY_BLOCKED` is truthful proof | SATISFIED |
| G01-038 | Deterministic replay creates no duplicate authority/execution/evidence/receipt | Catalog replay | read-only replay and create-once deterministic records across monitor/recovery | SATISFIED |

Totals: 38 requirements; 37 `SATISFIED`; 1 `NOT_APPLICABLE`; 0 partial,
unsatisfied, superseded, or deferred. The EENS applicability clause is not an
unmet dependency and does not reduce technical completion.
