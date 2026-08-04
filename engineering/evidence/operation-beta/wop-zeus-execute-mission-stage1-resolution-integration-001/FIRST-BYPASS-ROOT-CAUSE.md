# First Bypass Root Cause

The first bypass was the `session`/`status` branch in `scripts/zeus`: it called `resolve_execution_id` and then `ExecutionStateStore.load` while the authoritative Stage 1 submission existed only under `stage1/missions/`. The earlier resolver was only an in-memory fallback and returned `NOT_MATERIALIZED` for session when no execution projection existed.

The corrective places canonical Stage 1 resolution and hydration before every direct admission or execution projection access in the execute-mission path.
