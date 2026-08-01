# BETA-01 Architecture Decision Record

## Decision

Extend the existing EMP/Zeus orchestration and Mission Knowledge Model
projections. Do not create a parallel queue, scheduler, mission registry,
admission system, or lifecycle model.

## Rationale

The repository already provides submission, priority/dependency records,
eligibility, deterministic selection, WOP admission, execution context,
hash-bound lifecycle state, and recovery. The only material gap was that the
human-readable queue projection exposed eligible IDs only. Extending that
projection preserves identifiers and authority boundaries while satisfying the
inspection and metrics requirements.

## Consequences

Queue metrics and views are recalculated from authoritative state. Submission
and admission remain separate operations. Any missing or conflicting authority
continues to fail closed.
