# Operational Alpha Reference Architecture

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

Operational Alpha is modeled as an immutable-authoritative-fact architecture. Governance supplies a decision; the declared owner publishes an Authority Record; EMM captures versioned facts and relationships; capabilities consume exact revisions; synchronization produces only derived/runtime projections; qualification assesses evidence; and the existing HF-005 gate model records lifecycle progression through mission closeout.

```text
Governance Decision → Authority → EMM facts → capabilities → evidence/qualification
        ↓                              ↓                 ↓             ↓
  source ownership              generated artifacts ← synchronization ← events/runtime
                                                                ↓
                                             HF-005 Gate Catalog / verification / closeout
```

Architecture invariants: one authoritative owner per fact and relationship; explicit immutable identity, revision, and schema version; directional source-to-target synchronization; deterministic generated artifacts from recorded manifests; qualification before publication/adoption where applicable; and no projected, runtime, or historical record may overwrite an authoritative fact. Existing HF-005 states and OA gates remain the lifecycle contract.
