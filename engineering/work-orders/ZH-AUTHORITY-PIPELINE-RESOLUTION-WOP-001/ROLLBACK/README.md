# Rollback

Each modifying gate records its pre-state and bounded inverse here before the
change. Append-only publications and receipts are never removed. When a clean
inverse is impossible, stop and use recorded forward reconciliation.

