# Synchronization Architecture Integration

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Interface | Source owner → target | Trigger / validation | Failure behavior / reconciliation |
|---|---|---|---|
| Governance → Authority | Governance → authority consumers | decision publication; scope/lineage | reject invalid record; source owner corrects successor |
| EMP → Zeus | EMP → selection/decision projection | sealed snapshot; digest/applicability | Zeus reports mismatch; EMP reconciles planning fact |
| WOP → Zeus | WOP owner → admission projection | qualified package; immutable digest | block admission projection; WOP owner republishes successor |
| Zeus → EENS | Zeus decision facts → append-only events | event emission; sequence/digest | retry/record discrepancy; EENS owns event-store recovery |
| source systems → EOS | source owners → state projection | checkpoints; schema/freshness | replay/rebuild EOS projection from source |
| metadata → Documentation Generator | declared fact owners → generated docs | source revision; manifest/schema/graph | block publication; generator rebuilds after source correction |
| qualification → catalogs/dashboards | qualifier → derived status | sealed result; receipt applicability | stale status quarantined; rebuild projection |
| EOS/EENS → Zeus | EOS/EENS → read-only health view | checkpoint/event update; freshness | show stale/drift reason; source system reconciles |

Synchronization is never target-to-source. A synchronizer owns delivery and target rebuild, while the source owner remains authoritative for the fact. Version mismatches compare schema, revision, consumer adoption, input manifest, and digest; they produce a discrepancy and cannot be hidden by fallback.
