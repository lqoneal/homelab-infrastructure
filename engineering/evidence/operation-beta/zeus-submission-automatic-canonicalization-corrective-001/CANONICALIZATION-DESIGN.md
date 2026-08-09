# Canonicalization Design

The new `scripts/lib/emp/wop_canonicalization.py` service is deterministic and idempotent. It validates the Development WOP contract, binds Operation Beta, repository identity, the published template/context digests, source digest, output digest, validation/lint results, source-to-output mapping, authority projection, and replay identity. It preserves `Wop Id`, `Mission Id`, and all source bytes. It never derives replacement hash identities.

An existing sidecar is verified. Conflicting identity, source/output digest, repository, or replay provenance fails closed. The existing `submission_boundary.py` remains the sole P2 engine and stops at `ADMISSION_REQUESTED`.

