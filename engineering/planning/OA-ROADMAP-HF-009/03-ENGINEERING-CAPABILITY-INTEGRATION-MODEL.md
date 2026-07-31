# Engineering Capability Integration Model

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Capability | Authoritative metadata consumed → produced | Artifacts / sync dependency | Lifecycle / interface / owner |
|---|---|---|---|
| Authority Resolution | Decision → Authority Record | authority view; source publication | entry; `zeus authority`; governance |
| Mission Planning | Authority → Mission, Contract | mission plan; contract projection | planning; `zeus mission`; mission owner |
| Mission Selection | Mission, Snapshot → Admission candidate | selection view; eligibility reconcile | selection; `zeus mission select`; selection owner |
| WOP Resolution | Contract → WOP | WOP view; package publication | resolution; `zeus state`; WOP owner |
| Admission | WOP, candidate → Admission Record | admission report; status projection | admission; `zeus gate`; admission owner |
| Engineering Work Initiation | Admission → Initiation Result | initiation report; status projection | initiation; `zeus state`; initiation owner |
| Dispatch | Initiation → Dispatch | dispatch view; delivery | dispatch; `zeus mission`; dispatch owner |
| Execution | Dispatch → Execution Attempt | execution record; runtime projection | execution; `zeus state`; execution owner |
| Observation | Attempt → Event | event stream; append-only delivery | observation; `zeus health`; observation owner |
| Evidence Collection | Event → Evidence | evidence index; index rebuild | evidence; `zeus verify`; evidence owner |
| Qualification | Evidence → Qualification | qualification report; status projection | qualification; `zeus verify`; qualifier |
| Acceptance | Qualification → Acceptance | acceptance view; status projection | acceptance; `zeus gate`; acceptance owner |
| Synchronization | published facts → projection state | catalog/matrix/dashboard; source-to-target | throughout; `zeus health`; synchronizer |
| Reconciliation | manifests → Reconciliation | reconciliation report; target rebuild | correction; `zeus state`; reconciler |
| Closeout | Acceptance, Reconciliation → Closeout | closeout package; archival projection | terminal; `zeus lifecycle`; closeout owner |

The capability chain is complete only when each consumer records a compatible version adoption. Qualification requirements are those defined by HF-008: identity, schema, ownership, compatibility, migration, projection, synchronization, and lifecycle checks.
