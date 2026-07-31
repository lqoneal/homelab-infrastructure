# Engineering Capability Model

Status: `PROPOSED TECHNOLOGY-NEUTRAL MODEL — NON-AUTHORITATIVE`

Capabilities define reusable responsibilities, not implementations or authority changes. Each consumes versioned EMM facts, produces facts or projections under its declared owner, synchronizes only source-to-target, and publishes a stable public interface contract.

| Capability | Purpose and lifecycle position | Consumes → produces | Owner / sync / qualification | Public interface and generated artifacts |
|---|---|---|---|---|
| Authority Resolution | resolve initial authorization | Governance Decision → Authority Record | governance source owner; publish to consumers; authority/lineage check | `zeus authority`; authority view |
| Mission Planning | define planned mission | Authority Record → Mission, Mission Contract | mission owner; source-to-contract projection; schema check | `zeus mission`; mission plan |
| Mission Selection | select eligible mission | Mission, Eligibility Snapshot → Admission candidate | selection owner; reconcile eligibility; determinism check | `zeus mission select`; selection view |
| WOP Resolution | resolve work package | Mission Contract → WOP | WOP owner; contract-to-WOP sync; reference check | `zeus state`; WOP view |
| Admission | admit eligible work | WOP, Admission candidate → Admission Record | admission owner; publish admission; precondition check | `zeus gate`; admission report |
| Engineering Work Initiation | initiate engineering work | Admission Record → Initiation Result | initiation owner; status projection; lineage check | `zeus state`; initiation report |
| Dispatch | create executable dispatch | Initiation Result → Dispatch record | dispatch owner; directional dispatch sync; completeness check | `zeus mission`; dispatch view |
| Execution | perform declared work | Dispatch record → Execution Attempt | execution owner; observe status; contract check | `zeus state`; execution record |
| Observation | record observed state | Execution Attempt → Event | observation owner; append-only sync; event integrity check | `zeus health`; event stream |
| Evidence Collection | bind evidence | Event → Evidence | evidence owner; source manifest; digest/provenance check | `zeus verify`; evidence index |
| Qualification | assess evidence | Evidence → Qualification | qualification owner; publish result; criteria check | `zeus verify`; qualification report |
| Acceptance | record acceptance outcome | Qualification → Acceptance | acceptance record owner; status projection; valid qualification check | `zeus gate`; acceptance view |
| Synchronization | project authoritative facts | published facts → derived/runtime views | synchronizer owner; source-to-target only; digest/freshness check | `zeus health`; sync dashboard |
| Reconciliation | resolve drift | source/projection manifests → Reconciliation | reconciliation owner; rebuild target; discrepancy closure check | `zeus state`; reconciliation report |
| Closeout | preserve terminal record | Acceptance, Reconciliation → Closeout | closeout owner; archive projection; terminal completeness check | `zeus lifecycle`; closeout package |

The ordered rows express capability dependencies, not a revision of OA gates. The only lifecycle start is resolved authorization; closeout is terminal after acceptance and reconciliation. A capability may reject input but produces no alternate authoritative lifecycle path.
