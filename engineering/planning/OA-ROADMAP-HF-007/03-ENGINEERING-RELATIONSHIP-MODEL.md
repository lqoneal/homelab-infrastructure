# Engineering Relationship Model

Status: `PROPOSED — NON-AUTHORITATIVE`

| Producer → consumer | Produced-fact owner | Direction | Validation | Lifecycle constraint |
|---|---|---|---|---|
| Governance Decision → Authority Record | Governance | source → issuance | identity, signer, scope | attributable decision |
| Authority Record → Mission Contract | Governance / EMP derives | source → derivation | effective revision, mapping, digest | one effective authority |
| Repository/Baseline + sources → REAC | each source owner | sources → derived context | owner, freshness, precedence | projection cannot become source |
| Project State/Registry → Inventory/Snapshot | fact owner / EMP | source → planning | revision, schema, dependencies | snapshot freezes source set |
| Snapshot → Selection → WOP | EMP / Zeus / WOP publisher | source → consumer | digest, policy, applicability | binds one snapshot |
| WOP + context → Admission | admission owner | source → receipt | immutable package, receipt type | receipt expires by policy |
| Admission + authority → EWI Result | Zeus EWI | source → decision | current compatible inputs | EWI is terminal initiator |
| EWI ALLOW → Attempt | Zeus | source → runtime | freshness, reservation, fence | one effect boundary |
| Attempt → Event/Evidence | Zeus/agent; EENS/sealer | runtime → history | attempt binding, sequence, checksum | no evidence rewrite |
| Evidence → Qualification → Acceptance | sealer / qualifier / acceptance owner | source → decision | immutable subject, independence | acceptance never inferred |
| terminal facts → Reconciliation/Closeout | source owner / Zeus/EMP | source → projection/history | direction, revision, safe effects | source owner corrects drift |
| EMM metadata → generated artifact | metadata owner / generator | source → derived | manifest, schema, graph, deterministic digest | output cannot write source |

Each relationship has one owner for its produced fact. Multiple consumers are allowed; multiple authoritative producers are not. An absent or reverse direction, invalid source state, or missing validation makes the relationship invalid.
