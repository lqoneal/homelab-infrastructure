# Controlled-Document Reconciliation

Updated current documentation to make P4 current-versus-historical authority
explicit:

- `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`
- `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md`
- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`

The documents now state that P4 cardinality is scoped to the Mission/WOP/
submission/admission/bootstrap chain, historical append-only records remain
preserved, current-chain downstream records fail closed, and exact replay is
idempotent. No schema change was needed; the existing artifact envelopes
already carry the required identity and digest fields.

Current validation found no unresolved document conflict. Historical Beta
documentation and evidence were not rewritten.
