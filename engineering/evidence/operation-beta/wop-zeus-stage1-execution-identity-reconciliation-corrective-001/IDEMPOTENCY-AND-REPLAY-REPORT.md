# Idempotency and Replay Report

Repeated reconciliation returned the same admission and canonical execution identity, reused the existing projection, and did not create duplicate lifecycle objects. A stale derived identity was repaired once; replay classified the resulting state as canonical.
