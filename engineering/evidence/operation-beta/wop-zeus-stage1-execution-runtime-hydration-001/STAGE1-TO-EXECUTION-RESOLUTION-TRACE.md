# Stage 1 to Execution Resolution Trace

The first failing point was `scripts/zeus:resolve_execution_id`: it searched
only `mission-executions` and never consulted Stage 1. `status`, `session`,
and `resume` consequently failed with “no active execution exists”; `start`
also required a separately materialized admission ID.

The new path is Stage 1 load and digest verification -> receipt-backed
admission identity -> identity/package/authority checks -> in-memory admission
projection -> existing execution projection, if present -> execution runtime.
Missing, corrupt, ambiguous, or conflicting inputs fail closed.
