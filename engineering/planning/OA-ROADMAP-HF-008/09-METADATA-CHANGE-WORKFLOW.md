# Metadata Change Workflow

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

1. The authoritative owner creates a change proposal with purpose, affected entities, compatibility class, migration/recovery plan, and expected projections.
2. Validation checks identity, schema, relationships, ownership, and synchronization contracts.
3. Qualification runs version, migration, generator, Zeus, and lifecycle-regression checks against declared fixtures.
4. The owner publishes an immutable revision and records the qualification binding.
5. Consumers adopt explicitly; synchronization generates or rebuilds affected projections from the published source manifest.
6. Reconciliation verifies projected and runtime views, detects drift, and records recovery if needed.
7. The predecessor is deprecated and later retired/archived only under its declared policy.

No stage permits a derived artifact, runtime view, generator, or consumer to overwrite its authoritative source. Emergency recovery uses the same recorded lineage and qualification evidence; it does not create an untracked side path.
