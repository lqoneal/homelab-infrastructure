# Schema Evolution Strategy

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

Schema evolution is append-first, explicit, and lineage-preserving. A proposed change supplies a field inventory, invariants, compatibility classification, migration plan, fixtures, and retirement impact before qualification.

| Rule | Requirement |
|---|---|
| Identity | Existing stable identifiers and immutable digests never change meaning. |
| Additive change | New fields must be optional until the next major version makes their use mandatory. |
| Semantic change | A field whose meaning changes receives a new field or a major schema version. |
| Defaulting | Defaults must be deterministic, declared, and materialized in the canonical projection. |
| Removal | Removal follows deprecation, supported migration, and retirement evidence. |
| Relationship change | Cardinality, owner, and lifecycle constraints are revalidated for every affected edge. |

A schema registry records supported versions, canonical schemas, compatibility ranges, migrations, qualification bindings, and retirement dates. It is a registry of metadata contracts, not a replacement for authoritative entity ownership.
