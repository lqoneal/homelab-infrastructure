# Engineering Information Dependency Graph

Status: `PROPOSED — NON-AUTHORITATIVE`

This graph describes information flow, not mission execution ordering.

```text
Governance Decision -> Authority Record -> Mission Contract -> REAC
Repository/Baseline ------------------------------^          |
Project State + Work Registry -> Mission Inventory -> Snapshot -> Selection
Authority + Contract + Selection -> immutable WOP -> Admission -> EWI receipt
EWI + attempt/events -> evidence -> qualification -> acceptance -> closeout
all declared metadata -> lifecycle model/catalog/matrices/verification index
source-owner facts -> EOS projection -> dashboards and health views
```

| Source artifact | Authoritative producer | Consumer / target | Direction and trigger | Sync owner | Verification |
|---|---|---|---|---|---|
| Governance Decision | Governance | Authority Record | decision → issuance; approved revision | Governance | identity, signature, lineage |
| Authority Record | Governance | resolver, EMP, WOP, Zeus | source → consumer evaluation; issue/revoke | resolver coordinates evaluation | effective revision, scope, expiry |
| Mission Contract | EMP | REAC, WOP, admission, catalog views | source → consumers; contract revision | EMP / consumer validates | deterministic digest/provenance |
| repository/baseline | repository owner | REAC, admission | source → observation; baseline change | repository owner | identity/tree/integrity |
| Project State/Work Registry | respective owner | EMP inventory | source → planning; owner revision | EMP consumes | owner identity, revision, schema |
| Mission Inventory | EMP | eligibility snapshot/selector | source → snapshot; planning change | EMP | stable identity and dependency result |
| snapshot/selection | EMP / Zeus | WOP resolver | source → consumer; sealed snapshot | Zeus | digest/policy/tie-break |
| WOP | WOP publisher | admission | source → receipt; publication/qualification | admission owner | immutable digest/applicability |
| admission/EWI receipts | typed owner / Zeus | execution and verification views | source → consumers; receipt issuance | receipt owner | type, freshness, binding |
| execution events | EENS | replay, EOS/Zeus health views | source → projection; event append | EENS | sequence/digest/checkpoint |
| evidence/qualification | sealer / qualifier | acceptance, reports | source → consumers; sealed result | source owner | immutable subject/independence |
| source metadata/contracts | declared metadata owners | lifecycle model, matrices, catalog | source → generated docs; metadata revision | documentation generator | schema, digest, graph validation |
| gate/capability metadata | roadmap owner | verification index, capability matrix | source → generated views; gate revision | documentation generator | reference and command resolution |
| EOS runtime state | EOS | dashboards | source → projection; checkpoint/update | EOS | source revision/freshness |
| qualification/closeout records | qualifier/Zeus/EMP | dashboards, historical archive | source → reports/archive; sealed revision | report generator/archive owner | receipt digest and retention |

Every edge is one-way. Consumers must retain the producer revision and
verification result. A target drift is repaired by re-reading the source and
regenerating the target, never by treating the target as a source.
