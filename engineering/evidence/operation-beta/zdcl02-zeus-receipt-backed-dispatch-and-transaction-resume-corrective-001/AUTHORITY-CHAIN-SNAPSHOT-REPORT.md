# Singular Execution Authority Verification

Zeus is the sole lifecycle authority. The implementation freezes one authority snapshot before provider selection with a deterministic snapshot ID and digest. The snapshot binds governance authority, WOP/package identity, repository fingerprint, protected baselines, Development mode, effect profile, transaction profile, approval state, permitted effects, and prohibited effects. Provider-selection and dispatch receipts carry the same snapshot digest. A provider result cannot independently advance lifecycle state.

Conflicting authority declarations are rejected as `AUTHORITY_CHAIN_INTEGRITY_FAILURE` before Stage 1 state creation; the focused test suite verifies no mutation in that case.
