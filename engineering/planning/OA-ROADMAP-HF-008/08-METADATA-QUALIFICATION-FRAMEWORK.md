# Metadata Qualification Framework

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

Qualification precedes publication and adoption of a metadata change. It validates the fact and all declared effects; it does not make an operational decision.

| Check | Pass condition |
|---|---|
| Identity and lineage | unique identity, monotonic revision, valid predecessor |
| Schema | canonical schema and immutable/mutable field rules pass |
| Ownership | exactly one authoritative owner per fact and relationship |
| Compatibility | declared producer, consumer, generator, and Zeus ranges resolve uniquely |
| Migration | deterministic fixtures, recovery, and reconciliation pass |
| Projection | regenerated outputs match expected manifests/digests |
| Synchronization | directional source-to-target operation and drift detection pass |
| Lifecycle | change does not alter OA gate ordering or lifecycle semantics |

The qualification record names inputs, validator versions, result, limitations, evidence references, and expiry/requalification trigger. Failure blocks publication of the candidate but preserves all evidence.
