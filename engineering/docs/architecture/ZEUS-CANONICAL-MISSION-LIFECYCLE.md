# Zeus Canonical Mission Lifecycle

Development WOP execution and canonical Beta mission activation are linked but
separate authority domains. Stage 1 receipts remain authoritative history;
Mission Contracts, registry entries, and operational packages are derived
projections activated only after publication approval, EOS parity, and platform
validation.

The shared resolver persists target linkage during Development submission and
exposes it through `zeus mission` views. Its activation transaction is locked,
journaled, atomic, idempotent, and fail-closed.
