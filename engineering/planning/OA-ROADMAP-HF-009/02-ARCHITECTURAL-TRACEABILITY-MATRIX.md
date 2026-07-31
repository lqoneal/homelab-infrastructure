# Architectural Traceability Matrix

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Transition | Authoritative owner | Consumes → produces | Synchronization responsibility | Generated artifact | Verification / gate relation |
|---|---|---|---|---|---|
| Decision → authority | Governance | Governance Decision → Authority Record | source owner publishes | authority view | lineage/digest; initial HF-005 lifecycle entry |
| Authority → mission | mission owner | Authority Record → Mission, Contract | contract projection | mission plan | `zeus mission`; planned gate prerequisites |
| Mission → selection | selection owner | Mission, Eligibility Snapshot → Admission candidate | eligibility reconciliation | selection view | deterministic selection; admission predecessor |
| Contract → WOP | WOP owner | Mission Contract → WOP | package publication | WOP view | reference/digest; admission input |
| WOP → admission | admission owner | WOP, candidate → Admission Record | admission status projection | admission report | `zeus gate`; admissible lifecycle state |
| Admission → initiation | initiation owner | Admission Record → Initiation Result | initiation status projection | initiation report | lineage; work-start gate input |
| Initiation → dispatch | dispatch owner | Initiation Result → Dispatch | dispatch delivery | dispatch view | completeness; execution predecessor |
| Dispatch → execution | execution owner | Dispatch → Execution Attempt | read-only runtime projection | execution record | `zeus state`; execution gate evidence |
| Execution → observation | observation owner | Execution Attempt → Event | append-only event delivery | event stream | sequence/digest; evidence predecessor |
| Event → evidence | evidence owner | Event → Evidence | evidence index rebuild | evidence index | `zeus verify`; qualification input |
| Evidence → qualification | qualification owner | Evidence → Qualification | qualification status projection | qualification report | criteria/receipt; acceptance predecessor |
| Qualification → acceptance | acceptance record owner | Qualification → Acceptance | acceptance view rebuild | acceptance view | `zeus gate`; closeout input |
| Published facts → projections | source owner; synchronizer operates target | source manifest → derived/runtime view | source-to-target/replay | catalog, matrix, dashboard | digest/freshness/drift |
| Projection mismatch → reconciliation | reconciliation owner | manifests → Reconciliation | rebuild target only | reconciliation report | discrepancy closure; closeout input |
| Acceptance + reconciliation → closeout | closeout owner | terminal records → Closeout | archival projection | closeout package | `zeus lifecycle`; terminal HF-005 state |

Each row resolves to one producing owner and exact input revisions. “Gate relation” references the existing HF-005 lifecycle position; this matrix neither creates nor renumbers gates.
