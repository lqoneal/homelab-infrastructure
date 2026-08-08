# Controlled-Document Reconciliation

Updated current documentation/schema:

* `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`
* `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`
* `engineering/docs/cli/ZEUS-USER-GUIDE.md`
* `engineering/oversight/recovery-contract.schema.yaml`

The current corpus now states that the canonical lifecycle owns mission state,
recovery is subordinate, liveness is observational, `zeus mission recovery` is
read-only, checkpoints are identity/digest-bound, resume preserves execution
identity, and historical/stale/ambiguous evidence fails closed. Existing
machine-readable WOP preference, provenance-preserving canonicalization,
submitted-WOP authority, no generic second approval, and explicit WOP gates
remain unchanged. Historical evidence and completed WOPs were not rewritten.
