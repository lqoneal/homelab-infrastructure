# Metadata Deprecation & Retirement Model

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

Deprecation announces an end to new use; retirement removes the revision from new resolution; archival seals its record and dependencies for historical verification. None deletes an immutable engineering fact.

| State | New use | Existing reference | Required record |
|---|---|---|---|
| Active | allowed | allowed | support range |
| Deprecated | prohibited unless exception is recorded | readable and reproducible | replacement, deadline, migration path |
| Retired | prohibited | historical resolution only | consumer migration/reconciliation completion |
| Archived | prohibited | preserved immutable history | retention location, digest, lineage |

Retirement requires no active compatible consumer binding, no unresolved migration/reconciliation discrepancy, and regeneration capability for required historical artifacts. Retiring a schema never invalidates archived entity revisions; their schema and generator adapters are retained as part of historical reproducibility.
