# Corrective Design

`Stage1Runtime._canonical_resume_readiness` is a read-only projection. It
delegates authoritative checks to `_verify_recovery`, permits pending dispatch
artifacts only when the transaction is awaiting dispatch, and reports the
canonical command `scripts/zeus resume <mission>`.

A present but invalid dispatch receipt remains `NO_GO` as
`RECEIPT_CORRUPTION`. Missing governance/receipt/baseline/repository evidence
also remains fail closed. No authority is created or extended by readiness.
