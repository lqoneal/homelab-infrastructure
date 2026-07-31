# Engineering Metadata Model Specification

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

The EMM is the future engineering-information contract, not a database schema or storage mandate. A fact is authored once by its declared owner. A correction creates a successor fact and lineage rather than rewriting immutable history.

Every record has a globally unique `entity_id`, `entity_type`, `schema_version`, `revision`, `owner_ref`, `classification`, lifecycle state, provenance, and synchronization contract. Canonical identity is `entity_type:entity_id:revision`.

```yaml
entity_id: stable globally unique identifier
entity_type: controlled entity kind
schema_version: EMM semantic version
revision: monotonic successor revision
classification: AUTHORITATIVE | DERIVED | RUNTIME | HISTORICAL
owner_ref: exactly one authoritative role or subsystem
lifecycle_state: entity-type-controlled state
created_at: attributable timestamp
immutable_digest: canonical immutable-content digest
predecessor_ref: optional prior immutable revision
source_refs: immutable input entity revisions
synchronization:
  direction: SOURCE_TO_TARGET
  trigger: source_revision | event | scheduled_reconcile | operator_request
  owner_ref: synchronizer identity
  verification: digest | provenance | schema | semantic_predicate
  recovery: replay | rebuild | reconcile_at_source
```

Normative rules: authoritative entities have one owner; derived entities name complete source revisions, generator version, input manifest, and output digest; runtime entities declare checkpoint/freshness/recovery; historical entities are sealed; relationship records are first-class; and schema versions evolve independently of document versions. Consumers may use facts only after their applicable validation and qualification contract resolves.
