# Engineering Documentation Generator Architecture

Status: `PROPOSED INTERFACES — IMPLEMENTATION OUT OF SCOPE`

```text
EMM Ingestion -> Metadata Validator -> Dependency Resolver -> Canonical Manifest
 -> Deterministic Renderer -> Output Verifier -> Publication Coordinator
 -> Projection/Synchronization Monitor -> Archive
```

| Interface | Input | Output | Contract |
|---|---|---|---|
| Metadata Ingestion | EMM entities/relationships | canonical records | validates identity, schema, ownership |
| Dependency Resolver | requested artifact + records | ordered closure | resolves immutable revisions, rejects ambiguity |
| Renderer | template + canonical manifest | generated artifact | deterministic; no external mutable fact |
| Output Verifier | artifact + manifest | verification result | digest, provenance, reference, semantic checks |
| Publication Coordinator | verified output | atomic publication/archive result | publishes eligible output only |
| Sync Monitor | source/target checkpoints | freshness/drift event | detects mismatch; cannot modify source |
| Reconciliation Router | drift event | owner-routed work | source correction then regeneration |

Every output embeds EMM version, generator version, source entity revisions, source manifest digest, timestamp, output digest, synchronization status, and qualification status. Regeneration occurs on source revision, qualification change, explicit request, scheduled health check, or recovery.
