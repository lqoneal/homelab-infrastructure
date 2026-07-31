# Generated Artifact Integration Matrix

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Artifact | Authoritative metadata / capability | Sync and regeneration trigger | Publication criterion | Verification |
|---|---|---|---|---|
| Gate Catalog generated sections | gate/state/relationship metadata; Synchronization | source revision or graph change; rebuild | valid lifecycle graph and manifest | reachability, cycle, ownership checks |
| Capability Matrix | capability/objective/qualification; Synchronization | capability or qualification revision | complete coverage | IDs and qualification coverage |
| Lifecycle Graph / Dependency Matrix | state/transition/prerequisite metadata; Synchronization | model revision | acyclic, reachable graph | graph validation |
| Verification Guide index | verification/interface metadata; Synchronization | interface contract revision | commands resolve read-only contract | command/index check |
| Qualification Report | evidence/criteria/qualification; Qualification | sealed qualification revision | complete independent result | receipt/criteria completeness |
| Information Dependency Graph | artifact/synchronization metadata; Synchronization | metadata relationship revision | one source owner per fact | direction/trigger coverage |
| Engineering Dashboard | runtime/checkpoint/status; Synchronization | event/checkpoint/freshness threshold | current provenance and freshness | drift reason/status |
| Closeout package | acceptance/reconciliation/closeout; Closeout | terminal record publication | terminal completeness | lineage/archive digest |

Each artifact is a derived or historical projection with source revisions, generator version, input manifest, output digest, synchronization status, and qualification status. It is reproducible from its recorded authoritative inputs; manual changes are drift.
