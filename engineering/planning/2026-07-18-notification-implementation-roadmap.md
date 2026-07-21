# Engineering Notification Implementation Roadmap

## Mandatory Entry Sequence

### Phase 1 — Infrastructure Discovery and Validation

This phase is entirely read-only. It shall not finalize implementation choices,
modify infrastructure, deploy services, or change notification runtime.

Validate and report:

- Raspberry Pi hardware model, OS, storage, memory, connectivity, uptime
  expectations, available services, and deployment suitability;
- `letoatreides` OS, availability, network role, desktop environment, native
  notification APIs, startup behavior, and reference-client suitability;
- all current wrappers, scripts, ntfy configuration, triggers, latency
  characteristics, retry/duplicate behavior, and limitations;
- comparable SQLite, MQTT, WebSocket, Server-Sent Events, and justified
  alternative facts; and
- measured publication, workstation, mobile, retry, duplicate, and delivery
  reliability baselines with documented methods and limitations.

Deliverables are the Infrastructure Validation Report, Platform Capability
Assessment, Notification Baseline Metrics, Candidate Technology Evaluation,
updated Project State, and Completion Report.

### Phase 2 — Implementation Planning

Begin only after Phase 1 evidence is reviewed and accepted. Using only validated
facts, finalize transport and event-store selections, workstation architecture,
deployment model, retry policy, latency objectives, operational qualification
criteria, dependencies, rollback, and the gated implementation sequence. No
implementation occurs in this phase.

Architecture recommendations for SQLite WAL and authenticated WebSocket remain
provisional until this phase confirms or revises them.

### Phase 3 — Notification Sprint Implementation

Begin only after the validated implementation plan is reviewed and accepted.
The expected bounded subphases are:

1. Core Notification Service.
2. Persistent Event Store.
3. Local Transport Layer.
4. Reference Workstation Client.
5. ntfy Provider Adapter.
6. Migration from Prototype.
7. Operational Qualification.

Implementation prerequisites also include disposition of current uncommitted
wrapper work without absorbing it, a qualified canonical envelope and stable
Handoff identity source, an approved application-persistence boundary, and an
exact Notification Sprint scope and acceptance plan.

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
