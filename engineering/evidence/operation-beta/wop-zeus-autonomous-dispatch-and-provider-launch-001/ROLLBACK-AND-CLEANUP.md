# Rollback and Cleanup

If session materialization fails after provider acknowledgment, the configured cleanup callback is invoked and the launch journal records `ROLLBACK_REQUIRED`. Immutable Stage 1 receipts remain untouched.
