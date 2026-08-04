# Duplication and Idempotency Report

Resolution is deterministic by transaction/admission identity. A second
matching admission or execution projection is rejected as ambiguous. Repeated
resolution returns the same Stage 1 transaction and admission identities;
existing execution identity is reused. No replacement transaction or receipt
is generated.

Disposable tests passed for no-projection resolution and conflicting execution
projection rejection. Stage 1 regression tests passed (7 tests).
