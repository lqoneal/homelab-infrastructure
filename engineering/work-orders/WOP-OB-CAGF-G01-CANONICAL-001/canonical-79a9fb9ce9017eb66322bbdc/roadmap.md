# Canonical WOP requirements

## Objective

Adapt the validated canonical package without creating authority.

## Sequencing

Requirements execute in the canonical dependency order.

## Dependencies

Technical prerequisites are resolved before dependent requirements.

## Completion

Completion requires all declared requirements and operator review.

## Traceability

Each requirement remains bound to the canonical package, mission, WOP, gate, and evidence locator.

- CAGF-G01-R01: declare canonical ownership for every input
- CAGF-G01-R02: normalize source-bound inputs
- CAGF-G01-R03: establish stable source and aggregate digests
- CAGF-G01-R04: reject invalid identity/dependency/cycle/stale/conflicting/malformed inputs
- CAGF-G01-R05: generate one deterministic Operation Beta mission/readiness projection
- CAGF-G01-R06: preserve source/projection separation
- CAGF-G01-R07: emit immutable provenance and bounded publication manifest
- CAGF-G01-R08: qualify byte stability
- CAGF-G01-R09: qualify replay idempotency without duplicates
- CAGF-G01-R10: enforce bounded publication only after qualification
- CAGF-G01-R11: expose identity/status/readiness/blockers/provenance/snapshot/next action through Zeus
- CAGF-G01-R12: provide stable qualified technical input to downstream consumers
