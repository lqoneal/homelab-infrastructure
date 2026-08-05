# Idempotency and Replay

Replay of unchanged source returns the existing transaction with `idempotent_replay: true`, preserving all IDs, digests, snapshots, packages, receipts, and projections. Changed source or conflicting authority is rejected and requires a new transaction.
