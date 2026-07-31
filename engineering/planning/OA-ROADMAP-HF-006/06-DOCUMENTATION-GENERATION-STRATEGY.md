# Documentation Generation Strategy

Status: `PROPOSED — NON-AUTHORITATIVE`

## Pipeline

1. Author controlled gate, artifact, ownership, capability, and verification
   metadata once.
2. Validate schema, identities, owners, source availability, and directed
   information graph.
3. Generate lifecycle diagrams, dependency/reachability/cycle/ownership
   matrices, Gate Catalog sections, verification command index, qualification
   summaries, and dashboards.
4. Verify source-manifest and output digests plus semantic graph invariants.
5. Publish generated outputs atomically with provenance; archive prior output.

## Regeneration and synchronization

| Event | Timing | Required action |
|---|---|---|
| metadata or controlled source revision | before publication/qualification | regenerate affected closure of the dependency graph |
| receipt, qualification, or capability change | event-driven or bounded poll | regenerate status/dashboard views |
| scheduled health check | policy-defined interval | compare manifests, detect freshness/drift |
| detected drift/failure | immediately | record event, block affected derived claim, reconcile and rebuild |
| recovery after interruption | from last verified checkpoint | revalidate source manifest, regenerate incomplete outputs |

Publication requires a validated source manifest and records generator version,
input digests, output digests, and provenance. Manual maintenance of generated
sections is transitional debt, tracked until the generator is implemented and
qualified. The recommended implementation is a metadata-driven generator with
repository validation and graph analysis executed in qualification.
