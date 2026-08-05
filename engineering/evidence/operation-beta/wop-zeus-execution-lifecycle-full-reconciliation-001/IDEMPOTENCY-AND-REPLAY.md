# Idempotency and Replay

Repeated submission, status, session, start, and resume resolve the same transaction, admission, and execution identities. Existing valid projections are reused; missing derived projections are recreated; reconciliation IDs are deterministic for the same command and post-state.
