# Atomic Reconciliation Design

The reconciler locks by transaction, discovers and validates state, prepares fsynced temporary files, promotes admission/execution/receipt files, and restores backups on promotion failure. Replay is idempotent.
