# ZEUS-P2-019 Production Execution Foundation Architecture Report

Date: 2026-07-26
Result: IMPLEMENTED; production activation intentionally pending
Authority: authenticated `loneal` instruction ZEUS-P2-019

## Architecture

The foundation adds four control planes without changing the commissioned
production authority source:

1. `work_authority_lifecycle.py` separates implementation, qualification,
   commissioning, and operational eligibility.
2. `dispatcher-policy.yaml`, a baseline-bound activation record, and the
   version-2 agent registry supply production dispatch policy and state.
3. `production_execution.py` supplies readiness resolution, authenticated
   local invocation, signed durable EENS, signed evidence, independent
   qualification, and live reconciliation adapters.
4. Mission Admission and the Zeus CLI resolve production state rather than
   hardcoding dispatch disabled or enabled.

The local transport is a production contract, not an outbox substitute. It
binds the invocation token to the immutable assignment, validates the WOP
digest and selected agent, persists terminal state create-once, and returns the
same result on replay. Later remote transports can implement the same boundary.

## First-Qualification Authority Model

The controlled record
`engineering/authority/work-lifecycle/ZEUS-P2-019.json` proves the sequential
path through `QUALIFIED`. It does not contain commissioning or operational
eligibility claims. Every transition has an authorization and evidence
reference. Skipped transitions and purpose/state mismatches fail validation.

## Production Dispatcher and Activation

SPEC-0012 and `dispatcher-policy.yaml` define purpose, authority, activation,
eligibility, selection, no-automatic-retry behavior, interruption/resume,
timeout, cancellation, failure, evidence, oversight, reconciliation, and
closeout. Activation is independently signature- and digest-validated and bound to dispatcher
identity, implementation and policy versions, exact repository and baseline,
activating authority/time, supported mission/agent classes, required EENS,
evidence and reconciliation configurations, and revocation/suspension.

The repository activation is `PREPARED` with a post-commit baseline marker.
It cannot pass active validation.

## Production Execution-Agent Registry

The version-2 schema and validator cover all required identity, host, service,
capability, tool, repository-scope, constraint, qualification, evidence,
activity, freshness, trust, EENS, evidence-signing, resume and concurrency
fields. Fixtures are rejected. The checked-in registry is empty; no production
agent is fabricated or implicitly eligible.

## Admission-to-Dispatch and CLI Integration

Mission Admission now calls the production readiness resolver and preserves
reason-coded blockers in `dispatch_readiness`. Dispatch becomes true only when
activation, matching agent, repository baseline, policy, EENS, evidence,
reconciliation and runtime dependencies all pass.

`zeus dispatcher status|agents` exposes readiness, activation blockers and
eligible agents. Assignment, execution, EENS, evidence and reconciliation
inspection reads their durable production records. Production CLI construction
no longer decides readiness with a hardcoded Boolean.

## Production EENS Integration

EENS events use canonical payloads, stable UUID identities, detached SSH
signatures under namespace `zeus-eens`, append-only files, mission/assignment
correlation, idempotent replay and consumer checkpoints. SPEC-0012 enumerates
the normal, approval, interruption, failure, evidence, reconciliation and
closeout vocabulary. Qualification exercised every event contract; it did not
claim every mutually exclusive branch occurred in production.

## Execution Evidence and Qualification

Evidence binds WOP, mission, assignment, agent, repository, baseline, gate,
action, timestamps, output locator/digest and validation. Detached SSH
signatures use namespace `zeus-execution-evidence`. Qualification refuses
self-qualification and independently verifies identity bindings, signature,
digest, scope and expected result. Fixture signatures are not accepted by this
production verifier.

## Live Reconciliation Adapters

Adapters cover mission, work item, WOP, assignment, execution, evidence,
approval, project, work registry, completion, resume, controlled documents and
EENS checkpoints. Updates are scoped beneath a configured root, atomically
written, optimistic-lock protected and idempotent. Closeout policy requires all
adapters to complete.

## Runtime consistency and limitations

The prior isolated runtimes remain compatible. This milestone supplies
production bindings but deliberately does not activate them. Scheduling,
remote transport, EENS hardening, long-term evidence storage and cross-store
transaction semantics remain deferred. No operational WOP was dispatched.
