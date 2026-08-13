---
document_id: SPEC-0016
title: EENS Maturity Roadmap
version: 0.2
status: Draft
owner: Homelab Infrastructure
created: 2026-08-12
last_updated: 2026-08-12
classification: Engineering Specification
predecessor_revision: 0.1
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - Architecture approval, implementation authorization, migration, deployment, publication, and convergence remain pending.
  - Independent WOP and EENS roadmap qualification remains a later transaction.
  - CR48 remains held under EGR-000007.
relationships:
  - type: governed_by
    target: STD-0006
  - type: governed_by
    target: EGR-000007
  - type: depends_on
    target: SPEC-0009
  - type: related_to
    target: SPEC-0015
  - type: indexed_by
    target: DOC-0001
tags: [eens, maturity, roadmap, planning-only]
---

# EENS Maturity Roadmap

## Purpose

This specification is the authoritative, planning-only EENS development
roadmap. It converts the post-CR47 EENS capability coverage into an ordered set
of bounded engineering transactions that can later be authorized and
independently qualified. It does not implement EENS or WOP, qualify either
roadmap, converge the roadmaps, publish engineering changes, synchronize EOS,
or execute CR48.

The roadmap preserves the canonical EENS ownership model established by
`SPEC-0009`, the notification architecture records under
`engineering/planning/`, the repository implementation under `services/eens/`,
and the Zeus/WOP authority boundaries. EENS is an event and notification
substrate, not a lifecycle authority, approval authority, execution authority,
repository authority, or EOS authority.

## Scope

This Draft governs the future hardening sequence for event contracts,
identity/correlation, producer and consumer ownership, authentication and
integrity, durable persistence, ordering, idempotent ingestion, transport,
delivery and acknowledgement, retry and failed-delivery handling, replay,
notifications, Zeus/WOP observation, deployment and recovery, diagnostics,
and independent qualification.

It does not select a new architecture, authorize a migration, deploy or
reconfigure the service, alter `SPEC-0015`, make a lifecycle transition, or
create a replacement roadmap. Existing planning recommendations (embedded
SQLite WAL, local/service-grade interfaces, and ntfy as an adapter) remain
subordinate to the canonical architecture and require separately authorized
implementation work.

## Model

Status at this revision is `DRAFT / IN DEVELOPMENT / NOT EXECUTABLE`.
`DOCUMENTED != APPROVED`; `PLANNED != AUTHORIZED`; `IMPLEMENTED != QUALIFIED`;
`EVENT OBSERVATION != AUTHORITATIVE STATE`; `NOTIFICATION DELIVERY != EVENT
PERSISTENCE`; and `EVENT REPLAY != LIFECYCLE RE-EXECUTION`.

The authoritative state remains with its owner: Zeus owns mission and
execution lifecycle authority; WOP owns immutable execution intent; canonical
approval mechanisms own approval authority; repository/Git/EOS mechanisms own
publication and synchronization authority. EENS records, validates, persists,
routes, delivers, and replays attributable engineering events and
notifications. Receipt, absence, delay, duplication, or replay of an EENS
event cannot itself authorize, reject, resume, complete, qualify, publish, or
close a lifecycle.

## Governing sequence

EGR-000007 requires this sequence, and this transaction performs only item 2:

1. WOP roadmap maturity hardening — complete at operator-review boundary.
2. EENS roadmap maturity hardening — this transaction.
3. Independent WOP roadmap qualification.
4. Independent EENS roadmap qualification.
5. Convergence of the qualified subsystem roadmaps.
6. Maturity hardening of the resulting canonical roadmap.
7. Independent requalification of the canonical roadmap.
8. Fresh CR48 readiness assessment.

No item in this specification advances step 3 or later.

## Authoritative inputs and evidence rule

The roadmap was hardened against:

- `docs/resolutions/EGR-000007-CR48-WOP-EENS-CONVERGENCE-DEFERRAL-AND-ROADMAP-MATURITY-HARDENING.md`;
- the authoritative post-CR47 hardening records
  `POST-CR47-WOP-EENS-ROADMAP-MATURITY-HARDENING-BOUNDARY.yaml` and
  `POST-CR47-WOP-EENS-ROADMAP-MATURITY-HARDENING-GOVERNANCE-DIRECTION.yaml`;
- the current uncommitted revision of `SPEC-0015` as a WOP-side interface
  input only;
- `SPEC-0009`, `engineering/eens/production-eens-policy.yaml`, the notification
  architecture/design/catalog/roadmap records, and directly relevant
  procedures; and
- the actual source, deployment descriptors, and tests under `services/eens/`.

The hardening boundary records establish the authoritative assessment of the
roadmap-hardening condition and require complete decomposition, deterministic
dependencies, entry/exit conditions, fail-closed behavior, idempotency,
recovery/replay, evidence, negative-path qualification, and a Zeus-native
verification surface. They do not establish runtime maturity.

Every maturity claim below is limited to what the cited repository code,
tests, deployment records, or controlled evidence demonstrates. A schema,
fixture, event name, planning statement, or test helper alone is not evidence
of an implemented or qualified capability.

## Authority and ownership matrix

| Concern | Authoritative owner | EENS responsibility | Prohibited EENS effect |
|---|---|---|---|
| Mission and execution lifecycle | Zeus | Record attributable observations | Advance, reject, resume, or close execution |
| Immutable WOP intent and digest | WOP | Preserve bindings in envelopes and history | Rewrite package identity or revision |
| Approval authority and decision | Canonical approval mechanism/Zeus | Record request/result observations | Invent, replay, or approve a decision |
| Event identity and event history | EENS for the event record | Allocate/preserve event identity, sequence, causation, and integrity data | Replace mission, execution, provider, or session identity |
| Notification delivery | EENS | Route, deliver, retry, acknowledge, and retain delivery evidence | Treat delivery as lifecycle state |
| Publication and synchronization | Repository/Git/EOS authority | Observe receipts and failures | Publish, commit, push, or synchronize |
| Qualification | Independent qualifier | Supply evidence and observations | Self-qualify a roadmap or result |

## Current implementation-state assessment

| Capability | State | Repository basis and limitation |
|---|---|---|
| Basic event envelope and JSON validation | Implemented, hardening required | `services/eens/src/eens/events.py` validates a UUID event ID, timestamps, required fields, and JSON; it lacks the canonical SPEC-0009/WOP/Zeus envelope and authenticated integrity contract. |
| Event identity and idempotent ingestion | Implemented, hardening required | `store.py` has UUID identity, fingerprinting, unique idempotency keys, and conflict rejection; cross-domain identity and producer authorization are absent. |
| Durable append-only storage and sequence order | Implemented, hardening required | `store.py` uses SQLite WAL, FULL synchronous mode, an append table, and replay by sequence; migration, backup/restore, corruption detection, retention, and multi-process recovery are not qualified. |
| Consumer checkpoint and ordered replay | Implemented, hardening required | `consumer.py` provides named checkpoints and monotonic acknowledgement; atomic effect/checkpoint, out-of-order policy, cursor repair, consumer registration, and targeted replay are not established. |
| Handoff lifecycle production | Partially implemented | `lifecycle.py` emits only started/completed/failed handoff events; it is not the complete Zeus/WOP lifecycle taxonomy and does not prove authoritative producer ownership. |
| Runtime/process observation | Partially implemented | `runtime.py` wraps commands and emits simple lifecycle events; process events are not a substitute for Zeus execution facts and do not cover provider/session/execution identity. |
| ntfy notification delivery | Implemented, hardening required | `notify.py` and `server.py` deliver pending events and retain a checkpoint; there are no durable per-subscription obligations/attempts, bounded retry classes, dead-letter handling, or provider-neutral routing. |
| Producer authentication and event integrity | Not implemented | `events.py` has no signature/authentication or tamper verification; `production-eens-policy.yaml` is policy evidence, not an implemented trust boundary. |
| Taxonomy, registry, and schema version policy | Partially implemented | event type and schema-version strings exist; canonical family ownership, compatibility rules, and unknown-major-version rejection are not implemented/qualified. |
| WOP/Zeus identity correlation | Not implemented | Current events carry source/subject and arbitrary payload only; mission, WOP revision/digest, gate, execution, provider, invocation, session, agent, approval, evidence, and publication identities are not enforced. |
| Subscription/routing/consumer authorization | Not implemented | No subscription registry or authorized consumer routing implementation exists in `services/eens/`. |
| Approval/request and decision observation | Not implemented | Existing code does not implement approval request/result event contracts or replay-safe decision provenance. |
| Progress, blocker, interruption, checkpoint, resume, qualification, publication, EOS, and closeout observation | Not implemented as canonical EENS families | WOP defines the dependency surface in WOP-04 through WOP-10; EENS-side producers, contracts, and delivery qualification remain open. |
| Notification history and operator policy | Partially implemented | ntfy formatting and delivery exist; policy, destination selection, rendering separation, recipient acknowledgement, escalation, suppression, and history are not complete. |
| Restart and durable-store recovery | Partially implemented | systemd restart and SQLite persistence are present; service-state recovery, interrupted transaction cases, backup/restore, and deterministic reconstruction are not independently qualified. |
| Deployment and diagnostics | Implemented, hardening required | `services/eens/systemd/eens-notify.service`, config examples, health CLI, logs, and README exist; canonical deployment reconciliation, secret permissions, health semantics, and failure isolation remain. |
| Independent EENS qualification | Not implemented | No independent roadmap qualification result exists; this document only defines the later qualification boundary. |

## Canonical event authority model

An EENS record has three separately evaluated layers:

1. **Authoritative state:** the state or decision held by Zeus, WOP, approval,
   or publication/EOS owner.
2. **Event representation:** an immutable, attributable EENS fact, request,
   decision observation, transition observation, failure, or diagnostic with
   identity and causation.
3. **Notification delivery:** a derived user-facing delivery obligation and
   its attempts/receipts. Delivery does not change either of the first two
   layers.

The event-family owner defines the canonical name, semantic meaning, and
authoritative producer. EENS owns acceptance and persistence of a valid event,
not the fact represented by that event. The following families are the
roadmap baseline; a later contract freeze may refine names only through the
canonical owner and qualification evidence.

| Event family | Producer/owner | Meaning and minimum binding | Ordering, deduplication, and delivery |
|---|---|---|---|
| Admission/submission | WOP/Zeus | Fact or decision observation; mission, WOP ID/revision/digest, submission/approval ID, correlation/causation | Ordered within lifecycle stream; key is producer event ID plus semantic attempt; durable observation, no authority transfer |
| Provider readiness/selection/preflight | Zeus/provider selector | Observation; mission, WOP digest, execution, provider, invocation, agent | After admission/readiness predecessor; duplicate-safe; delayed observation does not authorize dispatch |
| Execution binding/start/progress | Zeus/provider/executor | Fact/observation; execution, provider invocation, session, agent, WOP digest, gate/work identity | Monotonic stream sequence; duplicate delivery must not repeat execution |
| Blocker/failure/interruption/checkpoint/resume | Zeus/executor | Fact or observation; exact execution identity, checkpoint/evidence identity, predecessor/cause | Historical event retained; resume is an observation of Zeus authority, not an EENS command |
| Completion/qualification | Executor and independent qualifier | Fact/qualification result; execution, evidence, qualification identity, result, causation | Completion precedes qualification; one result identity is replayed, never re-created |
| Publication/EOS synchronization/closeout | Publication/EOS owner and Zeus observer | Receipt/failure observation; publication/sync transaction, document/repository identity, closeout identity | Delivery loss does not change publication state; stale receipts cannot close current work |
| Approval request/result | Canonical approval owner/Zeus | Request or decision observation; approval/request ID, subject, authority reference, decision provenance | Replay only re-observes; EENS never creates a decision or approval effect |
| Notification service | EENS | Delivery-deferred, delivery-exhausted, delivery-recovered, subscription-rejected diagnostics | Service subject; never recursively routes through the failed destination |
| Runtime diagnostic | EENS/process supervisor | Non-authoritative service/process fact with component identity | May be dropped only under explicit diagnostic retention policy; never substitutes for lifecycle evidence |

For every family, a frozen contract must specify the exact canonical event name,
schema version, authoritative producer, consumer(s), fact/request/decision/
transition/observation classification, payload allowlist, authority represented,
ordering predecessor, deduplication key, persistence, delivery expectation,
acknowledgement, replay behavior, failure behavior, qualification test, and
whether loss blocks execution or only notification.

## Identity and correlation model

The canonical envelope must preserve, when applicable, these existing
identities rather than inventing replacements: `mission_id`, `wop_id`, WOP
revision and digest, work-item/gate identity, `execution_id`, `provider_id`,
provider invocation ID, `session_id`, agent/executor ID, approval/request ID,
`event_id`, `correlation_id`, `causation_id`, evidence/qualification identity,
and publication/synchronization transaction identity.

`event_id` identifies one event; a stream sequence orders events in a scoped
stream; `correlation_id` groups one mission/workflow; `causation_id` points to
the event or authoritative action that caused the representation; and the
idempotency key prevents repeated acceptance. These identifiers must be
deterministically serialized, retained on replay, and checked for conflicting
reuse. EENS may allocate only EENS-local event and delivery identities. It may
not allocate a replacement lifecycle, execution, session, approval, evidence,
publication, or synchronization identity.

## Delivery, acknowledgement, and notification model

The intended mature behavior is durable at-least-once delivery with idempotent
consumers and no exactly-once claim across external providers:

- event acceptance is atomic with durable persistence before an acceptance
  acknowledgement;
- each subscribed consumer receives an independent durable obligation;
- delivery attempts have stable obligation/attempt identity and a bounded
  retry classification;
- a consumer acknowledgement advances only after its effect is safely
  idempotent or transactionally checkpointed;
- duplicate deliveries, reconnects, service restarts, and provider responses
  are safe to repeat;
- transient failures retry with bounded policy; permanent/poison failures are
  quarantined or dead-lettered without blocking unrelated consumers;
- delayed or lost notification leaves authoritative state unchanged and
  remains visible as an undelivered observation;
- operator notification is a projection of a durable event, with destination,
  rendering, receipt, retry, suppression, escalation, and history separate from
  event persistence; and
- approval notifications can request attention but cannot become an
  unauthorized command channel.

At-most-once may be used only for explicitly disposable diagnostics after a
retention decision. No implementation may claim exactly-once external delivery
without direct architecture and test evidence.

## Ordered development sequence

Each item is a separately bounded future engineering transaction. Its outputs,
tests, and qualification disposition must be retained as immutable evidence.
Every item has an explicit non-scope and cannot be treated as implementation
authority merely because it is listed.

### EENS-01 — Authority, architecture, and maturity baseline

- **Objective:** Freeze one canonical EENS architecture owner, one event
  contract owner, one persistence boundary, and the state classification above.
- **Authoritative inputs:** This SPEC-0016 revision; EGR-000007 and both
  hardening records; SPEC-0009; SPEC-0015; notification planning records;
  `services/eens/`; PROC-0001 and applicable deployment/publication procedures.
- **Prerequisites:** WOP roadmap hardening complete at operator review; CR48
  held; no implementation, convergence, or migration authority.
- **Scope:** Produce an architecture/ownership decision record, legacy and
  competing-path disposition, capability evidence matrix, E01-E52-to-item
  traceability, and dependency DAG.
- **Non-scope:** Runtime code, data migration, deployment, new provider,
  schema migration, WOP modification, convergence, qualification, or CR48.
- **Artifacts/evidence/tests:** Decision record, authority matrix, state
  locators, traceability/DAG, no-parallel-lifecycle review, and controlled-
  document/graph validation.
- **Semantics:** Roadmap state only; no EENS event or lifecycle transition.
- **Exit/qualification:** One owner per concern, no unresolved duplicate
  authority, all later items mapped, no dependency cycle, and explicit
  fail-closed/stop conditions. Downstream: EENS-02.
- **Recovery:** Preserve failed baseline reviews and supersede them with a new
  revision; never edit a failed result into PASS.
- **Zeus/WOP/infrastructure:** Zeus remains lifecycle authority; WOP remains
  immutable intent owner; deployment facts are inventory only.

### EENS-02 — Canonical envelope, taxonomy, versioning, and identity contract

- **Objective:** Define the canonical event model and registry without
  implementing it.
- **Prerequisites:** EENS-01; SPEC-0009 and WOP-10 ownership inputs resolved.
- **Scope:** Envelope fields, family registry, schema/version compatibility,
  fact/request/decision/transition/observation classes, producer/consumer
  identities, mission/WOP/execution/provider/session/approval/evidence/
  publication correlations, event/causation/stream IDs, payload allowlists,
  and unknown/invalid contract fail-closed rules.
- **Non-scope:** Event bus, runtime producers, approval implementation,
  lifecycle state store, notification provider, or architecture replacement.
- **Artifacts/evidence/tests:** Versioned contract and registry, ownership
  matrix, canonical examples, JSON round-trip vectors, missing/unknown-major/
  conflicting-identity/late-event negatives, and WOP contract compatibility.
- **Semantics:** Event IDs are immutable; historical events remain historical;
  a representation never becomes authoritative state.
- **Exit/qualification:** Every required family has an owner, identity
  bindings, ordering and deduplication key, retention and delivery class, and
  test vector. Downstream: EENS-03.
- **Recovery/Zeus/WOP:** Replay preserves all IDs; Zeus/WOP producers remain
  responsible for represented facts; EENS cannot synthesize them.

### EENS-03 — Authenticated ingress and durable append-only persistence

- **Objective:** Harden the accepted-event boundary and durable history.
- **Prerequisites:** EENS-02; approved producer trust and application-data
  boundary; no deployment in this transaction.
- **Scope:** Producer authentication, event-class authorization, integrity/
  tamper verification, atomic validation-and-append, durable acknowledgement,
  append-only history, sequence scope/order, conflict rejection, migrations,
  corruption detection/containment, retention/archive, backup/restore, and
  concurrent producer behavior.
- **Non-scope:** Consumer effects, external notification, approval decisions,
  WOP/Zeus runtime changes, or EOS storage mutation.
- **Artifacts/evidence/tests:** Persistence schema contract, trust/config
  record, migration/backup/restore plan, integrity evidence, crash-before/
  after-persist tests, duplicate/conflict/concurrency/corruption negatives,
  and acknowledged-event durability proof.
- **Semantics:** Invalid, unauthenticated, tampered, stale, or unauthorized
  events fail closed; accepted history cannot be rewritten.
- **Exit/qualification:** Accepted events survive restart/restore, no accepted
  event is lost, duplicate insertion is idempotent, and no forged producer is
  accepted. Downstream: EENS-04.
- **Recovery/Zeus/WOP/infrastructure:** Recovery preserves event identity and
  source authority; credentials stay outside payloads; Zeus/WOP remain owners.

### EENS-04 — Consumer registration, ordering, idempotency, replay, and recovery

- **Objective:** Provide independently safe consumer observation and replay.
- **Prerequisites:** EENS-03; EENS-02 stream and consumer identity contract.
- **Scope:** Consumer authorization/registration, subscriptions, scoped cursors,
  ordered and out-of-order policy, durable checkpoints, atomic effect/checkpoint
  where required, duplicate/late/missing handling, poison isolation,
  quarantine/dead-letter disposition, retry classification, backpressure,
  cursor repair, targeted replay, schema-aware reconstruction, and service/
  process/host/durable-store restart.
- **Non-scope:** Re-executing lifecycle actions, changing Zeus state, approval
  replay, or external notification routing.
- **Artifacts/evidence/tests:** Consumer contract, cursor store, replay report,
  fault-injection suite for every interruption point, duplicate/out-of-order/
  late/tampered/missing-event tests, and deterministic fresh-process rebuild.
- **Semantics:** Replay reproduces observations only; one poison event cannot
  block unrelated consumers; no duplicate authoritative effect is possible.
- **Exit/qualification:** Consumers resume deterministically, retain history,
  distinguish historical/current views, and expose failures without false
  completion. Downstream: EENS-05 and EENS-06.
- **Zeus/WOP:** Consumers may inform Zeus/WOP but cannot acknowledge authority;
  execution identity and evidence continuity are preserved.

### EENS-05 — Routing, durable delivery obligations, acknowledgement, and retry

- **Objective:** Separate event persistence from per-consumer and per-destination
  delivery accounting.
- **Prerequisites:** EENS-03 and EENS-04; EENS-02 event/consumer registry.
- **Scope:** Deterministic routing, subscription versions, obligation and
  attempt identities, at-least-once delivery, acknowledgements, retry/backoff,
  delayed delivery, connection loss, partial delivery, destination outage,
  poison/invalid event handling, dead-letter/quarantine, backpressure, and
  delivery evidence.
- **Non-scope:** Exactly-once claims, lifecycle authority, provider-specific
  architecture becoming canonical, or notification policy beyond its contract.
- **Artifacts/evidence/tests:** Routing matrix, persistence API contract,
  attempt/receipt schema, retry/dead-letter policy, crash-before/after-delivery
  tests, duplicate acknowledgement and restart tests, and delivery audit.
- **Semantics:** Ack means the defined consumer obligation completed, not that
  authoritative engineering state changed. Retry never creates a new event.
- **Exit/qualification:** Accepted events remain queryable, obligations are
  independently recoverable, failed consumers are isolated, and all failure
  classes are visible. Downstream: EENS-06.
- **Zeus/WOP/infrastructure:** Delivery delay blocks only the specified
  observation obligation, never Zeus/WOP lifecycle authority; destination
  credentials remain isolated.

### EENS-06 — Notification projection, operator delivery, and approval support

- **Objective:** Build a qualified planning boundary between durable events and
  user-facing notifications, including approval-support observations.
- **Prerequisites:** EENS-05; EENS-02 approval/event ownership and security
  disposition; no approval authority delegated to EENS.
- **Scope:** Notification policy, destination selection, value-blind rendering,
  operator/user delivery, receipt and recipient acknowledgement where required,
  suppression/deduplication, expiry/supersession, bounded escalation, history,
  ntfy adapter compatibility, provider-neutral port, approval-request and
  approval-result projections, and notification-service diagnostics.
- **Non-scope:** Approval decisions, command channels, secret publication,
  new external infrastructure, or mutation of lifecycle state on delivery.
- **Artifacts/evidence/tests:** Policy and routing matrix, renderer/redaction
  vectors, delivery/receipt records, unavailable-destination and retry tests,
  notification failure isolation, approval replay/forgery negatives, and
  notification-history reconstruction.
- **Semantics:** Notification is a derived projection; failure is visible and
  retriable but cannot erase or alter the event or authoritative state.
- **Exit/qualification:** Durable event history and notification history are
  distinguishable; no secret/command is emitted; approval identity and
  provenance are preserved; replay cannot repeat approval effects. Downstream:
  EENS-07.
- **Zeus/WOP:** Zeus owns approval/lifecycle decisions; WOP observations are
  routed only under WOP-10 contracts.

### EENS-07 — Zeus execution-observation integration

- **Objective:** Define and qualify EENS-side production/consumption contracts
  for Zeus-managed execution without moving authority into EENS.
- **Prerequisites:** EENS-02 through EENS-06; Zeus execution-oversight and
  provider/session contracts; WOP-04 through WOP-08 interface dispositions.
- **Scope:** Observations for admission, dispatch readiness, provider
  selection/preflight/invocation, provider/session/execution binding, start,
  progress, blocker, interruption, checkpoint, resume, completion,
  qualification, and failure; producer adapters; query/history surface; and
  identity/correlation validation.
- **Non-scope:** Zeus lifecycle implementation, provider launch, Codex
  invocation, WOP runtime, or treating EENS acknowledgement as a transition.
- **Artifacts/evidence/tests:** Producer/consumer ownership matrix, contract
  adapters, identity lineage examples, authenticated event vectors, late/
  duplicate/missing observation tests, and end-to-end observation evidence
  using controlled doubles.
- **Semantics:** EENS records what Zeus/provider authority reports; it cannot
  infer current state from notification absence or create a successor identity.
- **Exit/qualification:** Every WOP-04–WOP-08 EENS dependency has a producer,
  payload, binding, delivery, replay, failure, and qualification disposition;
  unresolved behavior is explicitly blocked. Downstream: EENS-08.
- **Recovery:** Provider/session collisions, launch failures, interruptions,
  partial execution, and resume preserve exact execution identity and evidence.

### EENS-08 — WOP publication, synchronization, and closeout observation

- **Objective:** Define the EENS-side contract for WOP-09 publication,
  repository/EOS reconciliation, and closeout observation.
- **Prerequisites:** EENS-07; WOP-09 and WOP-10 contract inputs; publication/
  synchronization owner and transaction identity defined outside EENS.
- **Scope:** Publication candidate/receipt/failure, repository reconciliation,
  EOS synchronization, stale/historical receipt detection, closeout
  observation, delivery failure, replay, and false-closure prevention.
- **Non-scope:** Git/EOS publication, commit/push, repository mutation,
  synchronization authority, or closing WOP/Zeus state.
- **Artifacts/evidence/tests:** Event-family contract, receipt binding matrix,
  publication/sync failure and stale-result tests, duplicate/replay evidence,
  and closeout observation report.
- **Semantics:** EENS delivery of a receipt is not the receipt's authority;
  missing notification cannot invalidate an authoritative published result;
  stale receipts cannot close current work.
- **Exit/qualification:** WOP-09 dependencies are compatible with SPEC-0015,
  every transaction identity is preserved, and publication/sync failures remain
  visible without false closure. Downstream: EENS-09.
- **Zeus/WOP/infrastructure:** Zeus and publication/EOS owners remain
  authoritative; EENS only observes; repository and deployed-service paths
  remain separate.

### EENS-09 — Deployment, security, observability, and operational recovery

- **Objective:** Harden the canonical runtime boundary and prove restart and
  operational behavior without deploying in this transaction.
- **Prerequisites:** EENS-03 through EENS-08; approved architecture and
  persistence contract; deployment target decision.
- **Scope:** Canonical source versus deployment path, runtime user, startup/
  restart, configuration and secret permissions, database location/migrations,
  backup/restore, health/readiness/degraded states, logs/diagnostics, service
  isolation, workstation/Zeus connectivity, failure containment, and LOpi or
  other canonical deployment-target reconciliation.
- **Non-scope:** Live deployment, restart, reconfiguration, secret rotation,
  infrastructure expansion, or EOS synchronization.
- **Artifacts/evidence/tests:** Deployment manifest, configuration contract,
  permission review, migration/restore record, health/diagnostic schema,
  process/host/store/transport outage tests, and security scans for secrets,
  forged producers, tampering, replay, and privilege escalation.
- **Semantics:** Startup recovery reconstructs event and delivery history;
  service failure does not fabricate loss or authority; unavailable adapters
  produce a visible degraded state.
- **Exit/qualification:** A fresh process/host can deterministically recover,
  no acknowledged event is lost, diagnostics are attributable and redacted,
  and runtime/repository separation is explicit. Downstream: EENS-10.
- **Zeus/WOP:** Connectivity is an observation path only; no EENS service
  account receives Zeus, Git, publication, or EOS privilege.

### EENS-10 — Independent EENS roadmap qualification boundary

- **Objective:** Define the later independent qualification transaction; do not
  qualify this roadmap during hardening.
- **Prerequisites:** EENS-01 through EENS-09 documented; WOP roadmap remains
  unmodified; no convergence or implementation authority inferred.
- **Scope:** Review completeness, order, dependency acyclicity, maturity-state
  accuracy, event model, identity/correlation, producer/consumer ownership,
  authority boundary, persistence, delivery/ack/retry/idempotency, replay and
  recovery, historical/current distinction, Zeus integration, WOP interface,
  notification separation, security, deployment, tests, and convergence
  readiness.
- **Non-scope:** EENS/WOP runtime implementation, WOP qualification,
  convergence, canonical-roadmap re-hardening, publication, EOS, or CR48.
- **Artifacts/evidence/tests:** Qualifier input index containing this SPEC-0016
  digest, EGR-000007, hardening records, SPEC-0009, SPEC-0015 digest,
  EENS-01–EENS-09 manifests, implementation/test locators, capability-state
  matrix, event ownership/identity matrix, dependency DAG/cycle result,
  persistence/delivery/replay fault results, deployment/security results, and
  unresolved dependency register.
- **Semantics:** Qualification is a review transaction and cannot transition
  an EENS event, WOP, Zeus, EOS, or CR48.
- **Exit/qualification:** The independent qualifier produces attributable
  `PASS`, `FAIL`, `BLOCKED`, or `INDETERMINATE` evidence with exact unmet item
  identifiers. PASS proves roadmap quality only and is required before later
  convergence; it is not EENS runtime qualification.
- **Recovery:** Inputs and result are immutable and rerunnable; a failed result
  is preserved and superseded, never edited into PASS.
- **Zeus/WOP/infrastructure:** Qualification has an independently controlled
  boundary; it verifies, but does not grant, any implementation or deployment
  authority.

## Cross-item recovery and replay invariants

These invariants apply to every future item that handles events, delivery,
integration, or recovery:

- Duplicate submission, duplicate delivery, duplicate acknowledgement, and
  idempotency-key reuse with different content are detected and handled without
  duplicate authoritative effects.
- Out-of-order, late, missing, stale, historical, invalid, or tampered events
  remain attributable; they are rejected, quarantined, or represented as
  indeterminate according to the frozen contract, never silently promoted.
- Service interruption before persistence fails closed; interruption after
  persistence retains the event; interruption after delivery before
  acknowledgement safely redelivers under the same obligation identity.
- Consumer failure, provider failure, notification-destination failure,
  process failure, host failure, and durable-store failure preserve event
  identity, history, and recoverable cursors.
- Deterministic replay reconstructs observations and notification accounting
  only. It never
  repeats approval, execution, provider launch, publication, synchronization,
  or closeout effects.
- EENS never manufactures missing authority, replaces lifecycle identities,
  rewrites historical evidence, or treats notification absence as state.

## Dependency order and convergence hold

The internal dependency order is strictly:

`EENS-01 -> EENS-02 -> EENS-03 -> EENS-04 -> EENS-05 -> EENS-06 -> EENS-07 -> EENS-08 -> EENS-09 -> EENS-10`.

EENS-07 and EENS-08 depend on WOP-side contracts from WOP-04 through WOP-10,
but do not converge the roadmaps. EENS-10 depends on the hardened WOP-side
interface input and records unresolved compatibility rather than resolving it
by architectural invention. Both independent subsystem qualifications must
pass before EGR-000007 step 5. Canonical convergence, whole-roadmap
rehardening, canonical requalification, implementation, and CR48 reassessment
remain held.

## Independent EENS roadmap qualification transaction

The later qualifier must consume exactly the following controlled inputs and
produce exact evidence for each criterion:

1. This SPEC-0016 revision and immutable digest.
2. EGR-000007 and the post-CR47 hardening boundary/governance records.
3. SPEC-0009 and directly governing procedures.
4. Current SPEC-0015 revision and digest as the WOP interface input, without
   modifying it.
5. EENS-01–EENS-10 traceability and dependency artifacts.
6. Repository implementation, schemas, planning records, deployment
   descriptors, tests, and qualification locators used for every state claim.
7. Event authority, producer/consumer, identity/correlation, and
   authoritative-state/event/notification matrices.
8. Persistence, ordering, delivery, acknowledgement, retry, idempotency,
   replay, recovery, security, deployment, and notification fault evidence.
9. Zeus/WOP interface compatibility and unresolved dependency register.
10. Contemporaneous HEAD, controlled-document validation, and proof that no
    runtime, convergence, staging, publication, EOS, or CR48 action occurred.

The qualifier must verify complete capability coverage, ordered prerequisites
and exits, no circular dependencies, conservative maturity claims, authority
boundaries, all required identity bindings, event-family ownership, durable
history, delivery semantics, replay safety, notification separation, Zeus and
WOP completeness, deployment/recovery completeness, and convergence readiness.

## Validation

Before operator review, validate front matter, document identity, required
semantic headings, unique EENS-01–EENS-10 identifiers, complete capability
coverage, explicit prerequisites/non-scope/exits, dependency acyclicity,
maturity locators, event producer/consumer ownership, identity/correlation
coverage, persistence/delivery/replay semantics, Zeus/WOP boundaries,
notification separation, security, deployment/recovery, and the independent
qualification boundary. Run applicable non-mutating controlled-document and
EENS tests using a writable temporary directory outside the repository if
needed.

Validation must also confirm that only SPEC-0016 is intentionally modified,
all pre-existing unrelated worktree changes remain untouched, HEAD is
unchanged, nothing is staged, CR48 remains held, and no EENS or WOP runtime is
implemented. A repository-wide validator defect attributable solely to a known
pre-existing unrelated controlled-document record must be reported, not fixed
by expanding this transaction.

## Compliance

This document remains a `PLANNING_ONLY` Draft under SPEC-0001/STD-0006 and
EGR-000007. It is not an implementation work order, execution gate,
qualification result, publication authority, EOS synchronization authority, or
CR48 readiness decision. Future substantive changes to SPEC-0009, SPEC-0015,
governing procedures, deployment records, or the canonical convergence roadmap
are downstream dependencies to be recorded here or handled by their own
controlled transactions.

## Revision history

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-12 | Initial Draft planning-only EENS maturity roadmap. |
| 0.2 | 2026-08-12 | Converted capability coverage into an ordered EENS maturity sequence with implementation-state evidence, event authority, identity, delivery, replay, recovery, Zeus/WOP, deployment, and independent qualification boundaries. |
| 0.3 | 2026-08-12 | Made service interruption, consumer failure, and deterministic replay obligations explicit in the recovery invariants. |
