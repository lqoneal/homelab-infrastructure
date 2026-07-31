# Generator Runtime Architecture

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

| Phase | Execution behavior | Evidence / recovery |
|---|---|---|
| Discover | receive a named projection request and exact metadata revision/range | resolution receipt; reject ambiguous/missing input |
| Load | resolve all source entities and schemas through canonical resolution | sorted immutable input manifest |
| Order | construct dependency graph; topologically order sources and projections | graph/cycle/reachability result; block invalid graph |
| Generate | apply version-compatible generator and template to canonical manifest | generator version, output digest, provenance block |
| Qualify | submit output/manifest to Qualification Engine | sealed pass/fail result |
| Publish | publish only qualified output as Derived/Historical, never Authoritative | publication receipt |
| Restart/recover | resume from immutable manifest and idempotency key; rebuild target from source | replay/rebuild receipt; no source write |

Generator state is runtime checkpoint data. Identical manifest, generator version, and projection contract must yield identical output digest. A new generator version is a new qualified execution contract, not a mutation of a prior output.
