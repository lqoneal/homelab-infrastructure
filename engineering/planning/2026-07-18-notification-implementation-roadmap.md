# Engineering Notification Implementation Roadmap

## Prerequisites

- separately approved implementation authority;
- Active SPEC-0009 resolved as architecture baseline;
- disposition of current uncommitted wrapper work without absorbing it;
- qualified canonical envelope profile;
- qualified transitional Handoff Identity Authority or EMLS availability;
- approved EOS-compatible application persistence contract; and
- exact Notification Sprint boundary and acceptance plan.

## Recommended Sequence

### Phase 1 — Domain and Contract Foundation

Implement envelope types, validation, terminal mapping, ownership permissions,
value-blind policy, provider port, persistence port, clock, and deterministic
IDs. Validate with pure unit and property tests.

### Phase 2 — Durable Core

Implement event acceptance, transactional outbox, subscription versioning,
obligations, leases, attempts, retry scheduling, recovery, evidence queries,
and safe health. Test crash points and duplicate acceptance.

### Phase 3 — ntfy Adapter

Port current security and delivery behavior; add common adapter contract tests,
mock server tests, rate limiting, response classification, and secret-redaction
tests. Do not integrate the wrapper yet.

### Phase 4 — Identity and Lifecycle Bridge

Implement the qualified identity/sequence client and wrapper observation bridge.
Test multiple Handoffs per persistent session, resume, timeout, signals,
execution/report divergence, and exactly one terminal event.

### Phase 5 — Shadow and Migration

Run existing and service pipelines under a controlled comparison without
duplicate operator delivery. Produce equivalence evidence and execute the
single-writer cutover only after approval.

### Phase 6 — Operational Qualification

Validate provider outage/recovery, process crash, persistence restart,
duplicates, ordering, partial delivery, exhausted retry, configuration reload,
concurrent Handoffs, and graceful shutdown. Obtain operator confirmation for
bounded live ntfy tests.

### Phase 7 — Adoption

Publish client guidance and onboard `engctl`, EOS-safe integrations, and Mission
0 services incrementally. Future provider and event-family work remains
separately qualified.

## Validation Strategy

- unit: schema, terminal matrix, filters, redaction, retry math;
- contract: every persistence and provider adapter;
- integration: ingress-to-evidence using fake clock/provider;
- fault injection: crash before/after persistence and adapter response;
- compatibility: current ntfy behavior and wrapper exit/signal semantics;
- security: permissions, injection, unsafe fields, credential/log scanning;
- operational: restart, backlog drain, rate limit, concurrent Handoffs;
- repository: existing runtime, EOS, controlled-document, and platform suites.

## Exit Criteria

Implementation is ready for acceptance only when canonical identity, envelope,
outbox, routing, ntfy equivalence, delivery evidence, recovery, security,
failure isolation, and multi-Handoff operational qualification all pass with no
unresolved blocking finding.
