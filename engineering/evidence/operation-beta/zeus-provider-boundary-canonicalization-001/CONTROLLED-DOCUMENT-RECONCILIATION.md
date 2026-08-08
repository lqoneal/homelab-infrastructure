# Controlled-Document Reconciliation

Updated current documentation in:

- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`
- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`

The current model now states that provider evaluation is mission-scoped,
provider identity comes from the live execution-agent registry, historical
cross-mission records are subordinate, current target ambiguity fails closed,
and the historical `MISSION-BETA-*` identifier is not a current selector.
Canonical machine-readable WOP submission, provenance-preserving source
canonicalization, submitted-WOP authority, and legacy compatibility remain
unchanged.

Structural controlled-document validation passed. Repository-wide
synchronization validation continues to report the pre-existing unrelated
fingerprint drift for the established SPEC/PROC/INF synchronization records;
it was not introduced by this corrective and is recorded in the validation
report.
