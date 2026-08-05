# Interruption Recovery

Locks are transaction-scoped. Temporary files are removed after promotion or rollback. Replaying the same Stage 1 transaction reuses immutable receipts and deterministically recreates missing derived projections. No WOP resubmission or identity replacement is required.
