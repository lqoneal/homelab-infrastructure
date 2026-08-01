# Zeus Mission Projection Specification

Status: BETA-03F reconciled

Mission controllers consume one canonical, read-only mission projection. The
projection separates current operational state from immutable lifecycle history.

## Projection contract

Each mission projection exposes exactly:

- `current_admission`: one fresh, executable admission or `null`;
- `current_execution`: one active execution or `null`;
- `historical_admissions`: immutable prior admissions;
- `historical_executions`: immutable completed, cancelled, failed, or superseded executions.

An admission is current only when its lifecycle permits execution and its bound
repository baseline equals the current Development baseline. An execution is
current only while it is in an active execution state. Cancelled and completed
records are never selected by recency.

## Controller rules

`mission explain`, status, queue, health, next-action, and operation views use
the same resolved projection object for human-readable and JSON output. They do
not search execution records independently or infer lifecycle state.

History, archive, evidence, qualification, and completion views may expose
historical records explicitly. Active views must not expose those records as
current state.

If multiple current admissions or executions exist, the projection fails closed
with the conflicting identifiers. If none exists, the projection reports
`current_execution: null`, execution state `NONE`, and the next authorized
action needed to proceed.

The resolver is read-only. It does not mutate runtime state, historical
evidence, production baseline `OA-v1.0.0`, or development planning baseline
`OB-PLAN-v1.0.0`.
