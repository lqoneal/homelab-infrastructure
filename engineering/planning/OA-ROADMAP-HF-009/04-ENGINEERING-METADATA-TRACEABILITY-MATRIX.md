# Engineering Metadata Traceability Matrix

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Metadata family | Authoritative owner | Lifecycle role | Consumers | Derived/historical outputs | Verification |
|---|---|---|---|---|---|
| Governance Decision, Authority Record | Governance | authorization entry | planning, Zeus | authority view | scope, lineage, digest |
| Repository Identity, Baseline | repository owner | context/baseline | EMP, qualification | baseline report | identity/revision |
| Mission, Contract, Inventory, Snapshot | respective mission owner | planning/selection | WOP, admission | plan/selection view | schema, applicability |
| WOP, Admission, Initiation, Dispatch | respective fact owner | executable preparation | execution | WOP/admission/dispatch views | immutable reference/completeness |
| Attempt, Event, Evidence | execution/observation/evidence owner | execution observation | qualification, EOS/EENS | event stream/evidence index | sequence, digest, provenance |
| Qualification, Acceptance, Reconciliation, Closeout | respective record owner | terminal assessment | gates, dashboards, archive | reports/status/closeout package | criteria, receipt, lineage |
| Project State, Registries, Dashboard state | named source owner | runtime/projection | Zeus, operators | dashboard | checkpoint, freshness, drift |
| Engineering Artifact | declared artifact owner | authored/derived/historical record | generator, API | catalog/matrices/guides | class, owner, input manifest |

All records carry HF-007 identity, owner, classification, lifecycle state, immutable digest, source references, and synchronization contract. Exact entity definitions remain in HF-007’s Entity Catalog; this table integrates rather than repeats that contract.
