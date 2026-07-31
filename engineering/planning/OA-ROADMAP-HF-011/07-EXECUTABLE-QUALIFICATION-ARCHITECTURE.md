# Executable Qualification Architecture

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

Qualification is an executable capability that consumes a sealed subject manifest, applicable criteria set/version, validator versions, and evidence references. It produces a sealed Qualification entity with per-check results, output digests, execution receipt, pass/fail/not-ready determination, and publication-readiness decision.

| Pipeline stage | Deterministic behavior |
|---|---|
| Intake | resolve exact subject, criteria, owner, and dependencies; reject unresolved inputs |
| Validate | run identity/lineage, schema, owner-directory, compatibility, lifecycle, graph, synchronization, and projection rules in declared order |
| Exercise | run required normal, missing, conflict, mismatch, retry/replay, and recovery fixtures |
| Determine | pass only when every required check passes; any failed required check is fail; unavailable required evidence is not-ready |
| Seal | persist criteria/validator/input versions, result set, logs/receipts, and immutable result digest |
| Gate publication | source or derived output may publish/adopt only when applicable sealed result is pass |
| Repeat | same sealed inputs, criteria, and validators produce the same result classification and output digest set |

Independent rerun uses the sealed manifest rather than mutable repository state. Qualification evaluates facts and projections but does not assume ownership of them or change OA gate semantics.
