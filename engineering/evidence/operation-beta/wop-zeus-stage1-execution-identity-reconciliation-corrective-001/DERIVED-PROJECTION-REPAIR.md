# Derived Projection Repair

A disposable execution projection with a valid transaction binding but stale `execution_id` was classified `STALE_EXECUTION_PROJECTION`. Reconciliation rebuilt the derived projection at the canonical Stage 1 identity and installed it atomically. Immutable Stage 1 records were not edited. A projection with invalid digest or a different transaction binding remains fail-closed as corrupted/divergent.
