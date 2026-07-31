# Synchronization Pipeline Model

Status: `PROPOSED — NON-AUTHORITATIVE`

| Operation | Source → destination | Trigger | Validation / verification | Failure and reconciliation |
|---|---|---|---|---|
| ingest | owner fact → EMM interface | create/successor | identity, owner, schema, digest | reject; owner supplies valid successor |
| resolve | EMM entities → dependency closure | consumer/generation request | existence, lifecycle, relationship integrity | `UNKNOWN`; no favorable view |
| generate | validated closure → derived artifact | source-manifest change | deterministic render and output digest | retain prior history; mark target stale |
| project | runtime/history → dashboard/status | event/checkpoint/freshness interval | provenance, sequence, freshness | `DIRTY`/`BLOCKED`; replay checkpoint |
| publish | verified artifact → target/index | publication request | qualification, provenance, complete manifest | abort atomic publication; preserve evidence |
| reconcile | source owner → drifted target | drift event/operator request | source re-read and target comparison | source owner resolves; rebuild target |
| recover | verified checkpoint → incomplete pipeline | interruption | revalidate sources/generator version | idempotent replay or block |

Direction is always source to destination. EENS may persist failure events, EOS may project synchronization state, and Zeus may expose blockers; none changes the authoritative source or reconciliation owner.
