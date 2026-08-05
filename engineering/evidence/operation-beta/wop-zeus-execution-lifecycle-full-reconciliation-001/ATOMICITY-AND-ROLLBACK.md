# Atomicity and Rollback

`runtime_reconciliation._atomic_install` writes temporary admission, execution, and receipt files, fsyncs them, promotes them, and restores the exact pre-state on failure. The Stage 1 boundary calls this transaction before returning `DISPATCHED`; reconciliation failure stores a blocked checkpoint rather than reporting success.
