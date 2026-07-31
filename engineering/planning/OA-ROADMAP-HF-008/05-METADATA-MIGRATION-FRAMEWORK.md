# Metadata Migration Framework

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

A migration transforms a qualified source revision into a successor authoritative revision or a derived compatibility projection. It is directional, repeatable, version-pinned, and auditable.

| Phase | Requirement | Evidence |
|---|---|---|
| Plan | source/target schemas, scope, owner, compatibility and rollback declared | migration manifest |
| Prepare | snapshot immutable source references and validate eligibility | signed input manifest |
| Transform | apply deterministic mapping without source mutation | mapping version and output digests |
| Validate/qualify | validate target and affected relationships before use | validation and qualification bindings |
| Publish/adopt | publish successor, then record each consumer adoption | publication and adoption records |
| Reconcile | compare all expected projections with source manifests | reconciliation result |
| Recover | replay, rebuild, or restore prior consumer binding | recovery record |

Rollback changes consumer adoption to the last qualified compatible revision; it does not delete a published successor. If a transformation is not reversible, downgrade is unavailable and recovery is by replay from the immutable source snapshot. Migration preserves the source entity owner; a migration operator owns only the transformation process.
