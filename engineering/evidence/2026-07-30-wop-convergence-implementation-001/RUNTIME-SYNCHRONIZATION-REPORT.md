# Runtime Synchronization Report

EOS receives the EMM identity/version and source digest in its deterministic
repository projection. The synchronization plan is directional
`authoritative_to_derived`, idempotent, and receipt-bound. The EENS adapter
uses a digest-derived idempotency key; the EMP adapter produces a derived
planning receipt. Neither adapter can overwrite its authoritative source.
