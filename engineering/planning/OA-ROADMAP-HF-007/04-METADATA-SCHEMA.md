# Logical Metadata Schema

Status: `PROPOSED — TECHNOLOGY-NEUTRAL`

| Field class | Definition |
|---|---|
| Required | `entity_id`, `entity_type`, `schema_version`, `revision`, `classification`, `owner_ref`, `lifecycle_state`, `created_at`, `immutable_digest` |
| Optional | `predecessor_ref`, `expiry_at`, `retention_policy_ref`, `qualification_ref`, `labels`, `external_locator` |
| Immutable | identity, type, schema version for revision, owner, time, canonical digest, source refs, lineage |
| Mutable runtime only | checkpoint, freshness, delivery/replay checkpoint, reconciliation status; each update attributable |
| Derived | effective status, reachability, source-manifest digest, eligibility, capability coverage, dashboard fields |
| Identity | identifier unique in type; `(type,id,revision)` globally unique; successor names predecessor |

| Entity family | Required attributes | Validation / identity rules |
|---|---|---|
| decision/authority | subject, scope, validity, signer/decision identity, lineage | one applicable effective authority; revocation wins |
| repository/baseline | repository identity, commit/tree, integrity result | baseline binds one repository/digest |
| mission/contract/inventory/snapshot | mission identity, policy/mapping, dependencies, source manifest | IDs stable; contract reproducible; snapshot immutable |
| WOP/admission/EWI | package digest, applicability, receipt type, expiry, bindings | receipts typed; EWI terminal |
| attempt/event/evidence | attempt/fence, sequence, effect, producer, checksum | sequence monotonic; uncertain effect not inferred complete |
| qualification/acceptance | frozen subject, criteria/decision, reviewer independence | no self-qualification; exact-subject acceptance |
| reconciliation/closeout | source/target revisions, direction, disposition | target cannot correct source |
| artifact/registry/dashboard | artifact class, owner, sources, generator/provenance | every derived artifact has complete manifest |

Entities with target representations require source refs, target locator, `SOURCE_TO_TARGET` direction, trigger, synchronizer, freshness policy, verification predicate, drift status, reconciliation owner, and recovery mode.
