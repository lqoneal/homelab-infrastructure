# Resolver Integration Design

Stage 1 remains authoritative. The resolver validates `RECEIPT_BACKED_V1`, Development mode, mission/WOP metadata, admission receipt identity, requested identity bindings, and execution projection ambiguity. It derives compatibility projections without deriving new lifecycle identities or receipts.

Hydration is opt-in at the CLI boundary and uses create-only pair installation. If both files exist, it is idempotent; if exactly one exists, it fails closed. No operator-visible lifecycle step was added.
