# Implementation Roadmap

Status: `PROPOSED SEQUENCING — NON-AUTHORITATIVE`

| Milestone | Depends on | Deliverable outcome |
|---|---|---|
| 1. Adopt logical vocabulary and identifiers | HF-007/HF-009 reference | entity types, ownership roster, schema/version policy |
| 2. Build metadata validation fixture set | 1 | canonical manifests and automated identity/relationship checks |
| 3. Establish schema registry and immutable fact store | 1–2 | versioned authoritative facts and adoption bindings |
| 4. Implement generator read path | 2–3 | reproducible lifecycle/dependency/verification projections |
| 5. Implement synchronization and reconciliation | 3–4 | directional projections, checkpoints, drift discrepancies |
| 6. Implement qualification pipeline | 2–5 | validation evidence and publication gating |
| 7. Add Zeus/API compatibility adapters | 3, 5–6 | stable version-aware read/verify interfaces |
| 8. Pilot a bounded non-authoritative projection | 4–7 | compare generated result with current planning reference |
| 9. Seek separate adoption for any operational use | 8 | authorized scope determined outside this proposal |

Milestones 1–4 can begin independently of operational adoption. No milestone authorizes changing HF-005 gates, mission semantics, or controlled documents.
