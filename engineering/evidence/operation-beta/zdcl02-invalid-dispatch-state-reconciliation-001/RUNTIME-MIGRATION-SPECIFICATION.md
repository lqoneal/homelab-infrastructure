# Runtime Migration Specification

For an invalid dispatch, Zeus preserves the exact object, emits a deterministic reconciliation receipt/event, removes the active dispatch binding, retains predecessor receipts, sets `AWAITING_EXECUTION_DISPATCH`, and recomputes the state digest. A later resume freezes a fresh authority snapshot before redispatch. No provider launch or payload execution is performed.
