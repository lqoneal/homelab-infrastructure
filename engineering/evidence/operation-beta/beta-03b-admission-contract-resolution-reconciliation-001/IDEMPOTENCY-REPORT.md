# Idempotency Report

Admission identity remains deterministic from the normalized request and
persisted state is digest protected. Repeating the same request returns the
existing compatible admission record. A changed request produces a distinct
identity; a state digest mismatch fails closed.
