# Controlled-Document Reconciliation

Current documents were updated in:

- `engineering/docs/architecture/ZEUS-RUNTIME-DISCOVERY-SPECIFICATION.md`
- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`
- `engineering/operations/zeus-operational-runtime.md`

They now define the Live Projection First priority across the full lifecycle,
distinguish immutable constants/historical literals/compatibility fallbacks
from prohibited hardcoded current authority, and describe receipt-provenance
baseline versus current published baseline. They state that current-valid
reconciliation receipts are generated from live projections and that
descendant publication is validated without mutating historical evidence.

The operational runtime document now distinguishes the repository-bound
user-state runtime that owns current canonical P2/P3/P4 lifecycle state from
the older repository-local OA orchestration compatibility store. The legacy
`active-publication.json` pointer is not a current canonical lifecycle
prerequisite.

Default controlled-document validation, semantic-all validation, conformance,
assurance, registry, schema, platform, and EOS validation passed. No current
normative conflict remains in the directly affected corpus.

