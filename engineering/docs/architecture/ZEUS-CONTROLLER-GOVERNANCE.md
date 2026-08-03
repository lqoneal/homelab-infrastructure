# Zeus Controller Governance

Status: BETA-04 normative specification

Zeus controllers shall consume one canonical resolved projection. They shall not search runtime records independently, infer lifecycle, or maintain a controller-owned queue, admission, execution, or mission state.

Runtime discovery is also canonical: controllers consume the root selected by
`runtime_paths.py`; they do not infer repository-local paths or require an
exported `ZEUS_RUNTIME_ROOT` during normal Development Mode.

## Controller rules

- Active controllers shall expose current admission and zero or one current execution only.
- Historical admissions and executions shall be exposed through explicit history/archive interfaces.
- Human-readable and JSON forms shall be rendered from the same projection object and shall be semantically equivalent.
- Multiple current records, stale baselines, conflicting authority, and unknown lineage shall fail closed.
- Queue, roadmap, readiness, blockers, explain, status, health, metrics, and next-action views shall share the canonical mission projection boundary.
- Current Platform Mission, Current Executable Mission, Recommended Mission,
  and Next Authorized Action are distinct projection fields. Only a fresh
  admitted mission may populate Current Executable Mission.
- Normal controller output shall omit orientation and general help. Those are
  explicit `intro`, `--help`, or `--verbose` views.

## Runtime boundaries

Submission owns submission. Admission owns admission. Execution owns execution. Evidence owns history. EOS owns synchronized platform state. The controller owns presentation only.

Read-only commands (`mission explain`, `status`, `queue`, `roadmap`, and
`next-action`) may not create, lock, initialize, or update runtime state.
Mutation commands are the only runtime writers: submit, admit, execute,
publish, and synchronize. A failed mutation write is a fail-closed result.

## Validation

The platform self-audit is the qualification boundary for these rules. Changes to a resolver, controller projection, runtime owner, or state schema shall add or update invariant fixtures before publication.
