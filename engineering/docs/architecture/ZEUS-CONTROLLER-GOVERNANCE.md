# Zeus Controller Governance

Status: Beta-03G normative specification

Zeus controllers shall consume one canonical resolved projection. They shall not search runtime records independently, infer lifecycle, or maintain a controller-owned queue, admission, execution, or mission state.

## Controller rules

- Active controllers shall expose current admission and zero or one current execution only.
- Historical admissions and executions shall be exposed through explicit history/archive interfaces.
- Human-readable and JSON forms shall be rendered from the same projection object and shall be semantically equivalent.
- Multiple current records, stale baselines, conflicting authority, and unknown lineage shall fail closed.
- Queue, roadmap, readiness, blockers, explain, status, health, metrics, and next-action views shall share the canonical mission projection boundary.

## Runtime boundaries

Submission owns submission. Admission owns admission. Execution owns execution. Evidence owns history. EOS owns synchronized platform state. The controller owns presentation only.

## Validation

The platform self-audit is the qualification boundary for these rules. Changes to a resolver, controller projection, runtime owner, or state schema shall add or update invariant fixtures before publication.
