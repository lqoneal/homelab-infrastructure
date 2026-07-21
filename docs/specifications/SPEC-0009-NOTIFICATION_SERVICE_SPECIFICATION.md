---
document_id: SPEC-0009
title: Notification Service Specification
version: 1.6
status: Active
owner: Engineering Platform
created: 2026-07-18
last_updated: 2026-07-18
phase: HNS Decision Classification Recorded
domain: Engineering Platform
classification: Engineering Specification
predecessor_revision: SPEC-0009@1.5
successor_revision: null
approval_status: Approved
approval_authority: Homelab Infrastructure
approval_reference: Codex Handoff - SPEC-0009 Refinement: Engineering Decision Classification Model
approval_date: 2026-07-18
persistence_status: Persisted
source_of_truth: true
information_scope: Notification Service architecture, event model, lifecycle, ownership, interfaces, trust boundaries, reliability, compatibility, and deferred execution
declared_deferrals:
  - notification-service-implementation
  - canonical-event-envelope-qualification
  - eos-compatible-outbox-implementation
  - ntfy-adapter-migration
  - remote-approval-service-specification
  - remote-approval-service-implementation
  - dashboard-consumers
  - metrics-and-observability-consumers
  - eos-automation-consumers
  - frozen-per-ewo-resolved-manifest-consumption
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: STD-0003
  - type: related_to
    target: SPEC-0008
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: TPL-0002
  - type: related_to
    target: EOS-0003
  - type: related_to
    target: SERVICE-0002
  - type: indexed_by
    target: DOC-0001
tags:
  - notification-service
  - engineering-events
  - lifecycle
  - value-blind
  - transport-independent
  - deferred-execution
  - homelab-notification-system
  - hns
---

# Notification Service Specification

## 1. Purpose

This specification defines the Homelab Notification System as the authoritative
engineering event-record and delivery platform for the Engineering Platform.
Engineering producers publish value-blind lifecycle facts to HNS; HNS accepts
and durably persists those events, manages their delivery obligations, routes
them to authorized consumers and adapters, records delivery evidence, and
preserves failure isolation between engineering work and notification delivery.

This controlled specification does not activate EWO-000020, authorize
implementation, change the existing notification runtime, create Governance
authority, or establish a new controlled-document owner.

## 2. Architectural Context and Boundaries

The Notification Service is a cross-cutting platform service. It consumes
facts emitted by authoritative lifecycle owners and makes those facts available
to delivery adapters and future engineering consumers. HNS is authoritative for
the accepted event record and its delivery lifecycle; it is not the originator
or owner of the underlying engineering lifecycle fact.

The foundational responsibility model is:

| Role | Responsibility | Authority Boundary |
| --- | --- | --- |
| Engineering producer | Own the applicable lifecycle fact and publish its canonical event | Cannot delegate fact ownership to HNS or a provider merely by publishing |
| Homelab Notification System | Accept, validate, persist, replay, route, retry, and record delivery obligations and evidence | Authoritative for accepted event records and delivery state; cannot create or redefine source lifecycle facts |
| Notification provider | Transport or present an event and return provider acknowledgement or identifiers | Consumer/presentation mechanism only; owns no engineering fact or accepted HNS event |

Providers shall remain replaceable without changing producer contracts,
engineering event identity, lifecycle authority, or the authoritative HNS event
record.

The service shall preserve these boundaries:

- A Handoff is the atomic execution and notification unit.
- A Codex process, PID, terminal, wrapper invocation, or repository session is
  not a Handoff identity.
- The future Engineering Lifecycle Management Service (EMLS) is the
  authoritative owner of Handoff identity and lifecycle state. Until EMLS is
  implemented, a separately authorized Handoff Identity Authority conforming
  to section 7.2 is the only permitted transitional allocator; the wrapper
  consumes an allocated identity and never derives or owns one.
- EOS owns authoritative engineering-state persistence within its existing
  scope. A notification outbox may be an EOS persistence integration, but the
  Notification Service shall not redefine the EOS data model.
- Governance records and Active EWOs remain the only applicable sources of
  execution authority. Events, subscriptions, notifications, acknowledgements,
  and delivery receipts never grant or expand authority.
- The Work Registry remains a management projection and is not a notification
  authorization source.
- The qualified `engctl codex` implementation remains the operational baseline.
  This specification does not modify its Completion Report contract or report
  qualification behavior.

## 3. Goals and Non-Goals

### 3.1 Goals

- Define one versioned engineering event envelope.
- Model independent lifecycle events for every accepted Handoff.
- Separate lifecycle fact publication, routing, transport delivery, and
  delivery evidence.
- Support multiple adapters and multiple consumers without changing event
  producers.
- Preserve value-blind notification payloads and local secret handling.
- Provide deterministic ordering, idempotency, retry, and recovery rules.
- Support dashboards, monitoring, metrics, EOS automation, and a future Remote
  Approval Service through published interfaces.

### 3.2 Non-Goals

- Implement any component or adapter.
- Design the Remote Approval Service.
- Create approval authority or an approval decision model.
- Replace authoritative lifecycle, Governance, Work Registry, or EOS records.
- Carry prompts, Completion Reports, repository content, diffs, command output,
  credentials, tokens, endpoint values, or private configuration.
- Guarantee exactly-once delivery across external transports.
- Reactivate deferred Stage 2 heartbeat or Stage 3 structured-progress work.

## 4. Component Architecture

```text
Authoritative event producer
          |
          | publish(event)
          v
Event Ingress and Validation
          |
          v
Durable Outbox / Event Log -----> Delivery Evidence Store
          |
          v
Subscription and Routing Engine
       /       |        \
      v        v         v
 ntfy adapter webhook  internal consumer interface
      |        |         |
 operator   future UI   dashboards / monitoring / metrics / EOS automation
```

### 4.1 Event Producers

Authoritative event producers own a defined event family and submit facts
through the Publish Interface. Transitional producers may translate qualified
runtime observations only within the ownership and migration rules in section
7.1. Every producer shall supply stable event identity and, for Handoff events,
the allocated stable Handoff identity and sequence position obtained through
section 7.2. Producers shall not directly invoke transport adapters.

The future EMLS is the authoritative Handoff lifecycle producer. During
transition, the qualified Codex wrapper remains an observed runtime source
behind a separately qualified lifecycle bridge; it is not itself the
authoritative producer. Producer authentication or publish permission does not
confer authority over the lifecycle object referenced by an event.

### 4.2 Event Ingress and Validation

Ingress validates:

- envelope version and event type;
- required identity, timestamp, and sequence fields;
- known lifecycle transition compatibility;
- value-blind payload policy;
- producer authentication and publish permission;
- duplicate event identity; and
- size and field-count limits.

Invalid events are rejected before persistence and produce a value-blind local
diagnostic. Rejection shall not mutate lifecycle state.

### 4.3 Durable Outbox and Event Log

Accepted events enter an append-only outbox before delivery is attempted. The
outbox is the recovery boundary between lifecycle execution and external
transport availability.

The design requires an EOS-compatible persistence interface but does not define
or alter the EOS storage schema. A future implementation shall resolve that
interface under separate authority.

### 4.4 Subscription and Routing Engine

The routing engine matches an accepted event against versioned subscriptions.
Routing considers event type, project, repository, environment, severity, and
consumer capabilities. It shall not inspect private engineering content.

Each event/subscription pair creates an independent delivery obligation.
Failure of one consumer or adapter shall not block unrelated obligations.

### 4.5 Delivery Adapters

Adapters translate the canonical event envelope into transport-specific
requests. Initial compatibility includes the existing ntfy delivery behavior.
Future adapters may include authenticated webhooks, local event sockets, or
message brokers.

Adapters own transport encoding only. They shall not reinterpret lifecycle
state, authorize work, or alter the canonical event.

### 4.6 Delivery Evidence Store

Every delivery attempt records value-blind evidence including obligation ID,
attempt number, adapter identity, start and completion times, result class,
retry disposition, and safe transport status category.

Delivery evidence is operational evidence, not proof that a human observed or
accepted the notification. Explicit acknowledgement is a separate future
interface.

### 4.7 Homelab Notification System Deployment Direction

The approved product name is **Homelab Notification System**, with `hns` as
the suggested service identifier. The designated Raspberry Pi shall host the
central, always-on service independently of interactive workstation sessions.
It shall provide event ingestion, durable notification storage, local delivery
brokering, retry and delivery-status management, and provider routing.

The HNS server is authoritative for accepted notification events, persistence,
delivery obligations, and delivery results. Source lifecycle owners remain
authoritative for the engineering facts they submit; HNS does not acquire
authority to create or reinterpret those facts. Desktop, browser, terminal,
mobile, email, and future endpoints are presentation or delivery adapters.

The required acceptance and delivery sequence is:

```text
Engineering lifecycle event
        ↓
Event accepted by Homelab Notification System
        ↓
Event persisted locally
        ↓
Local workstation delivery attempted
        ↓
Remote/mobile delivery attempted
        ↓
Delivery results recorded independently
```

An event is safely recorded when HNS has durably persisted it. Provider
delivery, human presentation, and acknowledgement are independent results and
are not prerequisites for event validity.

### 4.8 Reference Client and Delivery Tiers

`letoatreides` is the proposed first reference workstation client. Before
implementation, its operating system, availability, network behavior, and
native notification interface shall be validated. The intended client shall
maintain a persistent LAN connection, display native notifications, retain or
expose history, acknowledge receipt where supported, and recover missed events
after reconnecting.

HNS shall define three delivery tiers:

1. **Tier 1 — Immediate Local Delivery.** `letoatreides`, the engineering
   workstation, and future Homelab workstations use MQTT, WebSocket, or another
   design-qualified persistent LAN transport for the lowest practical and most
   predictable latency.
2. **Tier 2 — Local Operational Visibility.** A browser dashboard, terminal
   status view, durable event history, and future Engineering Platform
   interfaces provide visibility independent of transient desktop alerts.
3. **Tier 3 — Remote and Mobile Delivery.** iPhone and future remote endpoints
   use optional providers such as ntfy or email for best-effort awareness.

Apple push delivery and every other external mobile path are non-deterministic,
secondary channels. Successful iPhone presentation is neither authoritative
proof of event completion nor required proof of receipt.

The architecture baseline recommends SQLite in WAL mode as the event and
delivery store and authenticated WebSocket as the Tier 1 workstation transport.
They are not final implementation selections: Phase 1 shall collect comparable
facts without deciding, and Phase 2 shall confirm or revise the selections using
only validated evidence. The reasons, alternatives, and validation gates are
recorded in sections 8.8 and 8.9. The designated Raspberry Pi, lightweight
workstation agent, native adapters, and optional ntfy provider remain subject
to implementation qualification.

## 5. Engineering Event Model

### 5.1 Canonical Envelope

```json
{
  "schema_version": "1.0",
  "event_id": "evt_<stable-opaque-id>",
  "event_type": "engineering.handoff.started.v1",
  "occurred_at": "2026-07-18T00:00:00Z",
  "recorded_at": "2026-07-18T00:00:00Z",
  "producer": {
    "service_id": "engctl-codex",
    "instance_id": "<non-secret-instance-id>"
  },
  "subject": {
    "subject_type": "handoff",
    "handoff_id": "<stable-handoff-id>",
    "mission_id": "<mission-id-or-null>",
    "work_order_id": "<EWO-id-or-null>",
    "project_id": "<project-id>",
    "repository_id": "<repository-id>"
  },
  "sequence": 1,
  "correlation_id": "<mission-or-transaction-correlation-id>",
  "causation_id": "<prior-event-id-or-null>",
  "classification": {
    "execution": "RUNNING",
    "report_qualification": "NOT_EVALUATED",
    "overall_transaction": "RUNNING",
    "severity": "INFO"
  },
  "attributes": {
    "reason_code": "accepted",
    "elapsed_seconds": 0
  }
}
```

### 5.2 Envelope Rules

- `event_id` is globally unique and stable across retries.
- `handoff_id` is required for Handoff events and is independent of process or
  session identity.
- `sequence` is allocated by the authoritative Handoff lifecycle sequencer and
  is monotonically increasing within one Handoff stream.
- `occurred_at` records the source transition; `recorded_at` records ingestion.
- `correlation_id` groups related Handoffs without merging their lifecycles.
- `causation_id` supports traceable event chains without implying authority.
- Enumerated classifications are uppercase stable tokens.
- Attributes are type-bounded, allowlisted, value-blind, and event-specific.
- Unknown optional fields may be ignored by compatible consumers. Unknown major
  schema versions fail closed.

### 5.3 Required Event Catalog

| Event | Canonical Type | Meaning | Terminal |
| --- | --- | --- | --- |
| Handoff Started | `engineering.handoff.started.v1` | An accepted Handoff entered execution. | No |
| Handoff Progress | `engineering.handoff.progress.v1` | An explicit safe milestone was reached. | No |
| Report Qualified | `engineering.handoff.report-qualified.v1` | The final response passed the active report qualification contract. | No |
| Report Qualification Failed | `engineering.handoff.report-qualification-failed.v1` | Execution produced or ended with a missing or structurally nonconforming report. | No |
| Handoff Completed | `engineering.handoff.completed.v1` | Execution passed and report qualification passed, or was legitimately not applicable. | Yes |
| Handoff Completion Rejected | `engineering.handoff.completion-rejected.v1` | Execution passed but the required report failed qualification; the overall transaction failed without reclassifying execution as failed. | Yes |
| Handoff Blocked | `engineering.handoff.blocked.v1` | Execution stopped at a declared blocker; report qualification is recorded independently. | Yes |
| Handoff Failed | `engineering.handoff.failed.v1` | Execution ended unsuccessfully. | Yes |
| Handoff Timed Out | `engineering.handoff.timed-out.v1` | The configured execution bound expired. | Yes |
| Handoff Interrupted | `engineering.handoff.interrupted.v1` | Execution stopped because of a handled signal or operator interruption. | Yes |
| Handoff Cancelled | `engineering.handoff.cancelled.v1` | An authorized lifecycle owner cancelled an eligible Handoff. | Yes |

### 5.4 Supporting Service Events

| Event | Canonical Type | Purpose |
| --- | --- | --- |
| Delivery Deferred | `engineering.notification.delivery-deferred.v1` | An obligation was retained for retry. |
| Delivery Exhausted | `engineering.notification.delivery-exhausted.v1` | Automatic retry policy was exhausted. |
| Delivery Recovered | `engineering.notification.delivery-recovered.v1` | A previously deferred obligation succeeded. |
| Subscription Rejected | `engineering.notification.subscription-rejected.v1` | A subscription failed validation or authorization. |

Supporting service events shall use a separate notification-service subject and
shall not recursively create delivery-failure notifications through the same
failed route. Operators receive such conditions through a bounded fallback
diagnostic or a separately healthy route.

### 5.5 Initial Platform Event Catalog

The Notification Sprint shall implement the following provider-independent
catalog. Event names are versioned; presentation titles are adapter concerns.

| Event | Canonical Type | Subject | Required Context |
| --- | --- | --- | --- |
| Work Started | `engineering.work.started.v1` | work | mission, source host |
| Work Completed | `engineering.work.completed.v1` | work | mission, outcome, source host |
| Handoff Created | `engineering.handoff.created.v1` | handoff | mission ID, Handoff ID and mission-local number |
| Handoff Started | `engineering.handoff.started.v1` | handoff | mission ID, Handoff ID and attempt |
| Handoff Completed | `engineering.handoff.completed.v1` | handoff | mission ID, Handoff ID and outcome |
| Handoff Failed | `engineering.handoff.failed.v1` | handoff | mission ID, Handoff ID and safe reason code |
| Process Started | `engineering.process.started.v1` | process | parent Handoff when applicable, source host |
| Process Completed | `engineering.process.completed.v1` | process | parent Handoff when applicable, exit class |
| Process Failed | `engineering.process.failed.v1` | process | parent Handoff when applicable, safe reason code |
| Qualification Completed | `engineering.qualification.completed.v1` | qualification | related mission/Handoff, result |
| Publication Completed | `engineering.publication.completed.v1` | publication | artifact locator, related mission/Handoff |
| Milestone Recorded | `engineering.milestone.recorded.v1` | milestone | milestone ID, related project/mission |
| Engineering Alert | `engineering.alert.raised.v1` | alert | severity, priority, safe reason code |

Every event requires `schema_version`, globally unique `event_id`, canonical
`event_type`, UTC `occurred_at`, HNS-assigned UTC `recorded_at`, authenticated
producer service and instance IDs, `source_host`, project/repository scope,
severity, priority, correlation ID, and an idempotency key. Mission context is
required for mission work; Handoff context is required for Handoff events and
must combine stable opaque identity with the mission-local Handoff number.
Process identity may aid diagnostics but never substitutes for Handoff identity.

Severity is one of `DEBUG`, `INFO`, `NOTICE`, `WARNING`, `ERROR`, or `CRITICAL`.
Priority is one of `LOW`, `NORMAL`, `HIGH`, or `URGENT`. Severity describes the
condition; priority controls routing urgency. Neither grants engineering
authority.

## 6. Handoff Notification Lifecycle

```text
ACCEPTED
   |
   v
STARTED ----> PROGRESS (zero or more)
   |
   v
EXECUTION FINAL STATUS: PASS | FAIL | BLOCKED | TIMED_OUT | INTERRUPTED | CANCELLED
   |
   v
REPORT QUALIFICATION: PASS | FAIL | NOT_APPLICABLE
   |
   v
OVERALL TERMINAL EVENT
```

### 6.1 Lifecycle Rules

1. Exactly one `Handoff Started` event exists for an accepted execution attempt.
2. Progress events are explicit milestones, not arbitrary transcript streaming.
3. Progress frequency and heartbeat behavior remain deferred unless separately
   authorized.
4. Execution status and Report Qualification are independent dimensions.
5. `Handoff Completed` requires execution `PASS` and report qualification
   `PASS` when a controlled report is required, or `NOT_APPLICABLE` when the
   accepted execution contract legitimately requires no report.
6. Execution `PASS` with report qualification `FAIL` produces `Handoff
   Completion Rejected`. Its classifications are execution `PASS`, report
   qualification `FAIL`, and overall transaction `FAIL`; it shall never be
   represented as `Handoff Failed`.
7. Failed, blocked, timed-out, interrupted, and cancelled execution retain their
   execution classification. A report may independently pass or fail.
8. Only one overall terminal event is authoritative for an execution attempt.
   Later delivery retries do not change that event.
9. Resume creates a new execution attempt or continues the same attempt only as
   defined by the authoritative Handoff lifecycle owner. Notification state
   shall not decide resume semantics.

### 6.2 Deterministic Terminal-Event Mapping

After execution and any required report qualification reach final states, the
authoritative lifecycle producer shall emit exactly one terminal event from
this matrix. `ANY` includes `PASS`, `FAIL`, and `NOT_APPLICABLE` and does not
permit omission of the report-qualification classification.

| Execution | Report Qualification | Overall Transaction | Authoritative Terminal Event |
| --- | --- | --- | --- |
| `PASS` | `PASS` | `PASS` | Handoff Completed |
| `PASS` | `FAIL` | `FAIL` | Handoff Completion Rejected |
| `PASS` | `NOT_APPLICABLE` | `PASS` | Handoff Completed |
| `FAIL` | `ANY` | `FAIL` | Handoff Failed |
| `BLOCKED` | `ANY` | `BLOCKED` | Handoff Blocked |
| `TIMED_OUT` | `ANY` | `FAIL` | Handoff Timed Out |
| `INTERRUPTED` | `ANY` | `FAIL` | Handoff Interrupted |
| `CANCELLED` | `ANY` | `CANCELLED` | Handoff Cancelled |

`NOT_APPLICABLE` is valid only when the accepted execution contract requires no
qualified report. If a report is required but cannot be evaluated, Report
Qualification normalizes the result to `FAIL`. Report qualification events are
supporting facts; they do not compete with or replace the single terminal
lifecycle event.

## 7. Event Sources

### 7.1 Authoritative Event-Family Ownership

| Defined Event Family | Authoritative Producer | Transitional Producer | Transport Adapter | Consumers |
| --- | --- | --- | --- | --- |
| Handoff lifecycle (`started`, `progress`, and all terminal events) | Future EMLS | A separately qualified lifecycle bridge may translate wrapper observations after receiving an allocated Handoff ID. | None; adapters deliver accepted events only. | Notification routing, dashboards, monitoring, metrics, EOS automation, future Remote Approval observation. |
| Report qualification (`report-qualified`, `report-qualification-failed`) | Report Qualification component | Qualified wrapper report qualifier, acting as that component until extracted. | None. | EMLS/lifecycle bridge and authorized observers. |
| Notification delivery (`delivery-deferred`, `delivery-exhausted`, `delivery-recovered`, `subscription-rejected`) | Notification Service | None. | An adapter reports transport results to the Notification Service but cannot publish authoritative service events. | Operators, monitoring, and delivery-evidence consumers. |

Mission Orchestrator scheduling facts and EOS persistence or recovery facts are
reserved future event families. No canonical events for those families are
defined by this specification, so they shall not be published until their
types, lifecycle purposes, and permissions are separately specified and
qualified. If introduced, Mission Orchestrator and the EOS integration within
existing EOS authority are their respective authoritative producers.

An authoritative producer owns the fact. The Handoff lifecycle authority owns
sequence allocation across all producers contributing to a Handoff stream; a
producer's allocated sequence position does not transfer ownership of another
producer's fact. A transitional producer may translate an authoritative or
qualified runtime fact under an explicit migration contract, but it gains no
lifecycle or Governance authority. A transport adapter encodes delivery and is
never an event producer. A consumer observes events and cannot republish an
observation as the same authoritative transition.

The wrapper-to-EMLS migration boundary is the Publish Interface: during
transition, the wrapper remains an observed runtime source behind a qualified
lifecycle bridge. EMLS becomes the direct producer without changing the event
envelope, subscriptions, adapters, or consumers. The bridge and EMLS shall not
co-publish the same transition; cutover requires a single-writer epoch or
equivalent separately qualified fencing mechanism.

### 7.2 Stable Handoff Identity Ownership and Allocation Interface

EMLS owns the Handoff identity namespace and is the target authoritative
allocator. Before EMLS exists, only a separately authorized Handoff Identity
Authority may implement the same allocation interface:

```text
allocate_handoff_id(accepted_handoff_context, idempotency_key)
  -> Allocated(handoff_id) | Existing(handoff_id) | Rejected(code)
allocate_handoff_sequence(handoff_id, event_id)
  -> Allocated(sequence) | Existing(sequence) | Rejected(code)
```

The interface allocates one opaque, stable Handoff ID per accepted execution
attempt and returns the same ID for retries of the same idempotency key. The
accepted Handoff context supplies authority references but does not derive the
identifier from an EWO, process, PID, terminal, wrapper invocation, repository
session, or Codex conversation. The lifecycle bridge and wrapper consume the
returned ID. The same authority allocates one monotonically increasing sequence
position per stable event ID and returns that position idempotently. If no
authoritative ID or sequence position is available, no canonical Handoff event
may be published. Allocation implementation and migration remain Deferred
Execution.

## 8. Interfaces

The Handoff identity allocation interface is defined with its ownership rules
in section 7.2. The interfaces below do not allocate Handoff identity or alter
event-family ownership.

### 8.1 Publish Interface

```text
publish(event_envelope) -> Accepted(event_id) | Duplicate(event_id) | Rejected(code)
```

Requirements:

- authenticated producer identity;
- authorization by event family and project boundary;
- schema and value-blind validation;
- idempotent acceptance by `event_id`;
- persistence before success acknowledgement; and
- no synchronous dependency on external delivery.

### 8.2 Subscription Interface

```text
create_subscription(filter, delivery_target_reference, policy_reference)
update_subscription(subscription_id, expected_revision, changes)
suspend_subscription(subscription_id, reason_code)
resume_subscription(subscription_id, expected_revision)
get_subscription(subscription_id)
list_subscriptions(subject_scope, event_types)
```

Targets are opaque secret-store references. List and read responses shall never
return credentials, tokens, private topics, or full endpoint secrets.

### 8.3 Consumer Event Interface

```text
read_events(consumer_id, cursor, limit, filters) -> events, next_cursor
acknowledge(consumer_id, event_id, disposition)
```

This pull-oriented logical interface allows dashboards, monitoring, metrics,
and EOS automation to consume the same canonical stream without coupling to a
push transport. A future broker may implement equivalent semantics.

Acknowledgement confirms consumer processing only. It does not approve work,
accept risk, acknowledge Governance notice, or transition a Handoff.

### 8.4 Delivery Adapter Interface

```text
deliver(obligation_id, canonical_event, target_reference, attempt_context)
  -> Delivered(receipt_metadata)
   | RetryableFailure(safe_reason_code, retry_after)
   | PermanentFailure(safe_reason_code)
```

Adapters shall be stateless with respect to engineering lifecycle and
idempotent where the transport permits.

### 8.5 Delivery Evidence Interface

```text
record_attempt(obligation_id, attempt, adapter_id, timestamps, result_class)
get_delivery_status(event_id, subscription_id)
list_delivery_failures(scope, safe_reason_class)
```

Evidence reads require operational authorization and return only value-blind
metadata.

### 8.6 Outbox Persistence Interface

```text
persist_accepted_event(canonical_event, delivery_obligations)
  -> Persisted(event_id) | Duplicate(event_id) | Unavailable(code)
recover_pending_obligations(cursor, limit)
  -> obligations, next_cursor
```

Persistence of an accepted event and its initial delivery obligations shall be
atomic. Recovery returns notification obligations only; it neither infers nor
mutates Handoff lifecycle state. This is an EOS-compatible integration
boundary, not an EOS schema definition or transfer of EOS ownership.

### 8.7 Future Remote Approval Integration Boundary

The event stream shall expose stable identity, correlation, ordering, and
subscription interfaces sufficient for a future Remote Approval Service to
observe events such as a separately defined approval-requested lifecycle fact.

The future service will require a distinct authenticated command interface to
submit an approval decision to the applicable Governance owner. That command
interface is not part of the Notification Service. In particular:

- notification delivery is not an approval request;
- event acknowledgement is not approval;
- a webhook response is not approval;
- subscriber identity is not Governance authority; and
- the Notification Service shall never translate a consumer action directly
  into an EWO or lifecycle transition.

This separation permits future integration without redesigning the event
envelope or routing architecture while leaving approval semantics undefined.

### 8.8 Persistent Event Store Baseline

SQLite in WAL mode is the current architecture recommendation for the
Raspberry Pi implementation baseline, subject to Phase 1 evidence and Phase 2
selection.
It provides transactional acceptance, crash recovery, indexed replay, mature
backup tooling, and sufficient single-node throughput without a database
service. PostgreSQL would add operational weight without a demonstrated
multi-writer requirement; append-only JSON or flat files do not provide safe
concurrent indexing and obligation transactions.

The logical schema is:

| Relation | Purpose | Principal Keys and Indexes |
| --- | --- | --- |
| `events` | Immutable canonical envelope and acceptance metadata | PK `event_id`; unique producer/idempotency key; indexes on recorded time, type, mission, Handoff, source host, severity/priority |
| `subscriptions` | Versioned endpoint filters and policy references | PK `subscription_id`; unique endpoint/filter revision |
| `obligations` | One independent delivery obligation per event/subscription | PK `obligation_id`; unique event/subscription; indexes on state and next attempt |
| `attempts` | Append-only delivery evidence | PK `attempt_id`; unique obligation/attempt number; index on completion/result |
| `consumer_cursors` | Durable replay and acknowledgement position | PK consumer/stream; index on last acknowledged event position |
| `service_metadata` | Schema version and maintenance state | PK metadata key |

Ingress uses one transaction to insert the event and initial obligations, then
acknowledges acceptance only after commit. Duplicate producer/idempotency keys
return the original event without adding obligations. Canonical event bodies
are immutable; corrections are new causally linked events.

Use an HNS-assigned monotonically increasing database position for replay while
retaining `event_id` as the public identity. Replay is `position > cursor`,
ordered by position, with bounded pages. WAL, database, and configuration must
reside on qualified persistent storage, not a transient filesystem. Backup uses
SQLite's online backup mechanism plus integrity verification; restore requires
schema validation, integrity check, and obligation recovery before ingress.

Retention is policy-driven. The baseline retains canonical events and terminal
delivery summaries for at least 90 days; verbose attempt records may compact
after 30 days only after terminal summary preservation. Unacknowledged events,
pending obligations, audit-relevant alerts, and records under an explicit hold
must not be removed. Exact values remain an operational-qualification gate.

### 8.9 Local Transport Decision

| Candidate | Latency | Complexity | Reliability/Recovery | Workstation Fit | Decision |
| --- | --- | --- | --- | --- | --- |
| MQTT | Excellent | Medium/high: separate broker, ACLs and topic design | QoS and persistent sessions help, but retained-message semantics do not replace HNS replay | Broad libraries | Defer; useful if device scale or non-HNS publishers justify a broker |
| WebSocket | Excellent | Low/medium: served by HNS | Bidirectional ack plus HNS cursor replay | Broad native and application support | Architecture recommendation; Phase 2 decision pending |
| Server-Sent Events | Excellent one-way | Low | Browser reconnect cursor is useful; client ack needs separate HTTP | Excellent browser fit | Use optionally for Tier 2 browser views |
| Long polling | Higher overhead and latency | Low | Straightforward cursor replay | Universal | Fallback only |
| Raw custom TCP | Excellent | High protocol/security burden | Must invent framing, auth, replay and compatibility | Variable | Rejected |

If confirmed in Phase 2, the protocol is authenticated TLS WebSocket on the LAN. After
connection, the client presents its stable endpoint ID and last durable cursor;
HNS replays missed events in order, then streams new events. The client sends
application-level received/processed acknowledgements. WebSocket frames carry
canonical envelopes and protocol control messages, not provider-formatted text.
Ping/pong detects broken connections; reconnect uses bounded exponential
backoff with jitter and resets promptly after a stable session.

The transport provides at-least-once delivery. HNS persistence and cursors,
not socket lifetime, provide reliability. Authentication, certificate trust,
LAN exposure, reconnect behavior, slow-consumer limits, and load/latency tests
are mandatory qualification gates.

### 8.10 Provider and Endpoint Architecture

Provider adapters implement the section 8.4 contract behind the routing
engine. The initial registry identifies `workstation-websocket`, `ntfy`, and
future `email`, `slack`, `discord`, and `sms` adapters by capability; provider
configuration and credentials are opaque secret references. Producers cannot
name provider credentials or call adapters. Adapter failure is recorded only
against its obligation and never blocks event acceptance or another tier.

The reference workstation agent shall:

- run independently of an interactive shell and maintain one authenticated
  WebSocket connection;
- persist endpoint identity, last acknowledged cursor, and a bounded local
  notification/history cache;
- deduplicate by `event_id` before native presentation;
- acknowledge receipt and, separately where useful, successful presentation;
- reconnect with jitter, request all events after its durable cursor, and
  present missed events according to policy rather than flooding the desktop;
- map severity/priority to native urgency without changing canonical facts;
- expose local history and health diagnostics; and
- keep credentials outside repository content, logs, and notification bodies.

The native adapter is selected only after `letoatreides` OS and desktop-session
facts are verified. Native presentation is transient and non-authoritative;
the agent's cursor and HNS event history remain the recovery sources.

## 9. Authentication and Authorization

### 9.1 Producer Authentication

Producers authenticate using machine-local workload identity, a protected
service credential, or a future platform identity mechanism. Identity shall be
bound to a stable `service_id`; process environment markers alone are
insufficient as cryptographic identity.

### 9.2 Producer Authorization

Publish permissions are least-privilege grants over:

- event families;
- project or repository scopes;
- subject types; and
- allowed attribute sets.

Authorization to publish a fact is not authority to cause the underlying
engineering transition.

### 9.3 Consumer Authorization

Consumers receive only subscribed event families and scopes. Sensitive routing
configuration and delivery evidence require separate permissions. Metrics
consumers should receive minimized or aggregated fields where possible.

### 9.4 Adapter Authentication

Transport credentials are stored in protected local or platform secret stores.
Adapters receive an opaque reference or short-lived credential at delivery
time. Secret values shall not enter events, logs, error messages, command-line
arguments, evidence records, or repository files.

## 10. Reliability and Retry Strategy

### 10.1 Delivery Semantics

The service provides durable at-least-once delivery per obligation. Consumers
and adapters shall deduplicate using `event_id` and `obligation_id`. The design
does not claim exactly-once delivery across external systems.

### 10.2 Ordering

- Preserve sequence order within a Handoff for consumers that request ordered
  delivery.
- Do not impose global ordering across unrelated Handoffs.
- A delayed progress event shall not be delivered after a terminal event to an
  ordered subscriber unless explicitly marked late.
- Delivery retries for one obligation shall not block later events for
  unrelated Handoffs or subscriptions.

### 10.3 Retry Classes

| Failure Class | Treatment |
| --- | --- |
| Transient network, timeout, or service unavailable | Exponential backoff with bounded jitter. |
| Explicit transport rate limit | Honor safe bounded `Retry-After`, otherwise backoff. |
| Authentication failure | Suspend obligation; require credential remediation. |
| Invalid target or permanent client error | Permanent failure; no automatic retry. |
| Local persistence unavailable | Reject new acceptance or retain producer-side handoff according to the future persistence contract. |
| Unknown result after request transmission | Retry with the same idempotency identity and record ambiguity. |

### 10.4 Retry Policy

Policy is versioned and referenced by subscription. A future controlled value
set shall define attempt limits, minimum and maximum delay, jitter bounds,
retention, and escalation thresholds. Implementations shall avoid synchronized
retry storms and unbounded retention.

## 11. Failure Handling

### 11.1 Producer Failure

If an event cannot be durably accepted, ingress returns a deterministic failure
and records a safe local diagnostic. Whether lifecycle execution may continue
is decided by the authoritative execution contract, not by this service.

### 11.2 Delivery Failure

Delivery failure never rewrites the engineering lifecycle event. The obligation
transitions independently through pending, attempting, deferred, delivered, or
exhausted states.

### 11.3 Partial Delivery

An event may be delivered to some subscriptions and deferred or exhausted for
others. Aggregate status shall retain each independent result and shall not
collapse partial delivery into a false global success.

### 11.4 Recovery

On restart, the service reconstructs pending obligations from the durable
outbox and delivery evidence. It does not infer completion from process exit,
terminal output, or notification transport state.

### 11.5 Dead-Letter Handling

Exhausted obligations enter a bounded review queue containing only canonical
event references and value-blind failure evidence. Replay requires operational
authorization, preserves the original event identity, and creates new attempt
evidence.

## 12. Security Considerations

- Apply deny-by-default schemas and allowlisted attributes.
- Enforce payload, field, and batch-size limits.
- Reject control characters and transport-header injection.
- Use HTTPS or authenticated local IPC; never disable TLS verification.
- Keep target endpoints, topics, tokens, prompts, outputs, diffs, and repository
  content out of events and evidence.
- Redact safe diagnostics before delivery or persistence.
- Separate publish, subscribe, administer, replay, and evidence-read roles.
- Protect against forged producer identities, replayed publish requests,
  duplicate amplification, subscription exfiltration, and retry storms.
- Record attributable configuration changes without recording secret values.
- Bound event and delivery-evidence retention under the applicable persistence
  authority.
- Treat external delivery as an untrusted boundary and external
  acknowledgement as non-authoritative input.

## 13. Observability and Metrics

The service should expose value-blind metrics:

- accepted, rejected, and duplicate event counts;
- obligations created, delivered, deferred, and exhausted;
- delivery latency distributions;
- retry counts by safe reason class;
- oldest pending obligation age;
- outbox depth;
- consumer lag by opaque consumer identity; and
- schema-version usage.

Metrics shall not contain prompts, report bodies, repository paths, private
targets, tokens, or unbounded identifiers. Metric emission shall not recursively
depend on the same failed notification route.

## 14. Extensibility and Compatibility

### 14.1 Schema Evolution

- Additive optional fields are allowed within a major schema version.
- Required-field removal, semantic reinterpretation, or incompatible enum
  changes require a new major version.
- Event type versions are explicit suffixes.
- Producers may dual-publish only under a separately qualified migration plan.
- Consumers declare supported schema and event versions at subscription time.

### 14.2 Adapter Extensibility

New delivery adapters implement the stable adapter interface and do not require
producer changes. Adapter-specific data remains outside the canonical event.

### 14.3 Consumer Extensibility

Remote approval observation, dashboards, monitoring, EOS automation, and
metrics all consume the same canonical stream through independent
subscriptions. Adding one consumer does not alter existing producer or adapter
contracts.

### 14.4 Future Manifest-Driven Requirements

The event envelope permits a value-blind `contract_locator` extension after its
authority, disclosure, and persistence treatment are separately specified. It
shall identify, not duplicate, a frozen resolved contract.

### 14.5 Long-Term Engineering Event Platform Vision

HNS is implemented first as a notification system, but its provider-independent
event log, subscriptions, acknowledged streams, replay, and consumer interfaces
form a reusable foundation for a future Engineering Event Platform. Without
changing current scope, the same accepted stream may later support Engineering
Platform event streaming, operational dashboards, live engineering status, EOS
activity feeds, `engctl` status streaming, workflow visualization, telemetry,
future automation, and AI consumers.

This is an extensibility vision, not a current implementation requirement. The
Notification Sprint remains bounded to the accepted HNS phases and shall not
implement general telemetry, automation, AI integration, or portfolio-wide
event families merely because the interfaces can support them. Each future
producer, event family, or consumer requires its own ownership, security,
privacy, capacity, and qualification treatment.

### 14.6 Foundational Authority-Separation Principle

Every implementation and extension shall preserve this invariant:

> Source services own engineering lifecycle facts; HNS owns accepted event
> records, delivery obligations, and delivery evidence; presentation providers
> own neither.

Accordingly, HNS is the authoritative engineering event-record and delivery
platform, while providers are consumers of engineering events and presentation
mechanisms only. Providers shall not own, redefine, or become the authoritative
source of engineering lifecycle information.

Authentication proves which producer submitted an event but does not grant
that producer ownership of the referenced lifecycle fact. Persistence by HNS
does not transfer lifecycle authority. Delivery, provider acceptance, desktop
presentation, mobile presentation, consumer acknowledgement, and human
observation do not create, approve, complete, or alter engineering work.

### 14.7 Transport and Store Evolution Guidance

Authenticated TLS WebSocket remains the preferred Tier 1 architecture
recommendation because one persistent bidirectional channel can support low
latency delivery, replay cursors, acknowledgement, dashboards, live operational
views, and future Engineering Platform interfaces without provider coupling.
That broader utility strengthens the recommendation but does not bypass the
mandatory Phase 1 comparison or Phase 2 decision. New engineering evidence may
confirm or revise it.

SQLite WAL remains the preferred event-store recommendation because it combines
transactional durability with low single-node operational complexity on the
designated Raspberry Pi. Implementation shall isolate persistence behind the
section 8.6 port, use portable migrations and canonical export/replay formats,
avoid SQLite-specific behavior in domain logic, and preserve stable public
identities. Those boundaries permit later migration to PostgreSQL or another
qualified store without changing producers, consumers, event semantics, or
provider adapters.

### 14.8 Canonical Producer Identity Guidance

Every accepted event shall reference a registered producer identity. The
canonical producer descriptor should contain:

- stable opaque `producer_id`;
- human-readable `producer_name` for operations only;
- `producer_version` identifying the emitting contract implementation;
- stable `host_id` distinct from mutable display hostname;
- bounded declared `capabilities` or event-family claims; and
- `authentication_identity` or an opaque binding to the authenticated workload.

Ingress derives or verifies security-sensitive identity fields from the
authenticated connection; it shall not trust self-asserted display fields for
authorization. Producer registration binds permitted event families and scopes.
Examples may include Codex bridges, `engctl`, EOS, `homelabctl`, `sprinterctl`,
printer, backup, monitoring, and future Engineering Platform components, but
listing a candidate grants no publish permission and creates no immediate
implementation obligation.

### 14.9 Independent Event, Delivery, and Provider Identities

Implementations shall keep three identities distinct:

1. **Event ID** identifies one immutable engineering fact and remains stable
   across replay, routing, retries, and providers.
2. **Delivery ID** (the existing `obligation_id`) identifies one event-to-
   subscription/endpoint obligation. One event may have many Delivery IDs, and
   every retry retains the same Delivery ID with a new attempt number.
3. **Provider Notification ID** identifies the provider-specific artifact, such
   as an ntfy message, APNs identifier, desktop presentation, or future provider
   receipt. It is optional, adapter-owned evidence and never replaces Event ID
   or Delivery ID.

This separation is required for provider-independent auditing, retry analysis,
partial-delivery tracking, replay, deduplication, and migration. Provider IDs
shall be stored only as bounded, non-secret receipt metadata and may not be
used as engineering lifecycle identity.

### 14.10 Preferred Migration Pattern

The preferred evolution pattern is **Shadow Persistence → Muted Local Delivery
→ Controlled Dual Routing → Provider Cutover → Qualification → Prototype
Retirement**. It preserves a working notification path, creates comparison
evidence before presentation changes, prevents a flag-day migration, and delays
removal until rollback and operational qualification succeed. Section 19 owns
the detailed gates. This pattern guides HNS evolution and may inform similar
adapter migrations, but it does not authorize migration or generalize into a
new Engineering Platform procedure.

## 15. Existing Runtime Compatibility

### 15.1 Current-State Assessment

Repository discovery found one implemented notification transport and one
calling subsystem:

| Component | Current Responsibility |
| --- | --- |
| `scripts/engctl` | Sources the helper and wrapper; exposes `engctl codex`; sets the repository root used for configuration fallback |
| `scripts/lib/eos/codex.sh` | Constructs value-blind messages and synchronously triggers start, terminal, timeout, interruption, report-qualification-failure, and wrapper-bypass notifications |
| `scripts/lib/notifications/ntfy.sh` | Discovers and validates configuration, creates an ntfy HTTP request, invokes curl, and returns provider success/failure |
| `configs/notifications.env.example` | Documents public configuration names and safe placeholder values |
| per-user or ignored `notifications.env` | Stores `NTFY_BASE_URL`, `NTFY_TOPIC`, optional `NTFY_TOKEN`, and `NTFY_PRIORITY` with required mode `0600` |
| notification regression tests | Exercise configuration rejection, secret handling, wrapper triggers, signals, timeouts, exit preservation, and provider-failure degradation |
| INF-0001 and historical records | Describe the accepted Stage 1 runtime, wrapper enforcement, and deferred Stage 2/3 work |

No HNS server, service unit, local broker, event API, database, delivery queue,
subscription registry, provider registry, workstation agent, dashboard, local
native adapter, delivery ledger, or replay endpoint exists. The Work Registry
records Stage 1 as completed, Stage 2 heartbeat and Stage 3 structured events as
deferred, and the former notification-service implementation item as cancelled.

Repository evidence identifies the proposed server hardware as operational
AST-000007, Raspberry Pi 5 (8 GB), but does not qualify it for HNS hosting.
Repository evidence does not establish `letoatreides` operating system,
availability, network behavior, or native notification interface.

### 15.2 Current Notification Flow and Trigger Inventory

```text
engctl codex invocation or wrapper-gate observation
        ↓
eos_codex_notification builds title and plaintext metadata
        ↓
notify_ntfy loads local shell configuration
        ↓
curl synchronously POSTs to NTFY_BASE_URL/NTFY_TOPIC
        ↓
ntfy accepts or rejects the request
        ↓
external provider and Apple push path attempt presentation
        ↓
wrapper continues regardless of notification result
```

| Trigger | Location | Timing | Result |
| --- | --- | --- | --- |
| Wrapper bypass | `eos_codex_wrapper_gate` | At protected resume/qualification entry when a Codex thread lacks the wrapper marker | Attempts `Codex Wrapper Bypass`; gate returns 78 |
| Process start | `eos_codex_run` | Immediately before launching the child | Attempts `Codex Started` |
| Signal | nested `eos_codex_interrupted` | After forwarding INT/TERM/HUP and waiting for child | Attempts `Codex Interrupted` |
| Timeout | `eos_codex_run` terminal branch | After timeout returns status 143 | Attempts `Codex Timed Out` |
| Successful wrapper completion | terminal branch | After child exit and report qualification | Attempts `Codex Complete` |
| Report contract rejection | terminal branch | Child exits zero but report qualification fails | Attempts `Codex Report Qualification Failed`; wrapper returns 65 |
| Process failure | terminal branch | Child exits nonzero outside timeout handling | Attempts `Codex Failed` |

The present implementation observes one wrapper process, not an accepted
Handoff identity. A long-lived or resumed Codex session can contain multiple
Handoffs without independent current notifications. There is no `Handoff
Created` trigger and no durable link among notifications.

### 15.3 Existing Behavior and Failure Semantics

- Every provider call is synchronous on the wrapper path, with a five-second
  connection timeout and 15-second total timeout. Start and completion can each
  add provider/network delay, although failure does not replace the child result.
- There is no retry, queue, replay, delivery acknowledgement, provider receipt,
  duplicate suppression, persisted event history, or missed-event recovery.
- Logging is limited to bounded stderr diagnostics and warnings. Provider
  results are not durably recorded.
- Messages contain status, repository, Work Order, optional duration/signal,
  and host. They omit prompts, output, diffs, repository content, and secrets.
- Configuration discovery prefers `NTFY_CONFIG_FILE`, then the XDG per-user
  file, then an ignored repository-local file. Mode `0600`, HTTPS, non-empty
  non-placeholder topic, and newline safety are enforced.
- curl input hides the topic and token from command-line arguments, uses normal
  TLS verification, and supports an optional bearer token.
- All triggers use the same default ntfy priority and fixed `codex,engineering`
  tags. Provider presentation owns subsequent mobile behavior and latency.

### 15.4 Technical Debt and Latency Contributors

| Finding | Consequence | Architectural Disposition |
| --- | --- | --- |
| Wrapper calls ntfy directly | Producer, presentation, and provider are coupled | Publish canonical events to HNS ingress; adapters route later |
| Process lifecycle substitutes for Handoff lifecycle | Multi-Handoff sessions are incomplete or ambiguous | Allocate stable mission/Handoff identity and emit each Handoff transition |
| Synchronous external HTTP | Provider DNS, TLS, network, service, and push latency affect wrapper wall time | Persist locally first; dispatch providers asynchronously |
| No event or delivery store | No authoritative history, audit, replay, or recovery | SQLite transactional event/obligation ledger |
| No idempotency or deduplication | Repeated triggers can duplicate presentation | Stable event/idempotency keys plus endpoint dedupe |
| No retries or classified outcomes | Transient provider failure is permanently lost | Independent obligations, classified retry and attempt evidence |
| One provider-specific configuration contract | New providers require producer/runtime changes | Provider registry and opaque adapter configuration |
| Shell-sourced configuration | Trusted file can execute shell code and is awkward for multiple endpoints | Move HNS configuration to validated data plus protected secret references |
| Fixed titles, tags and priority | Routing and urgency cannot express event semantics | Canonical severity/priority; adapter-specific presentation mapping |
| No local client path | iPhone delivery inherits external nondeterminism | Persistent authenticated LAN WebSocket to workstation agent |
| No service supervision | Notification capability depends on wrapper calls and external ntfy | Always-on Raspberry Pi service under host-native supervision |

Dominant current latency contributors are synchronous DNS/TCP/TLS setup,
provider request processing, ntfy-to-platform routing, Apple push scheduling,
device connectivity, and OS presentation. HNS removes the external segments
from Tier 1 by keeping a warm LAN connection, committing locally before route
dispatch, avoiding batching, and acknowledging at receipt and presentation.

The current runtime may be represented through a transitional lifecycle-bridge
mapping without changing its behavior. This bridge is distinct from a delivery
adapter:

| Current Runtime Signal | Planned Canonical Event |
| --- | --- |
| `Codex Started` | `engineering.handoff.started.v1` once a stable Handoff identity exists |
| progress update | `engineering.handoff.progress.v1` when separately authorized |
| `Codex Complete` plus report PASS | `engineering.handoff.completed.v1` |
| qualified Completion Report | `engineering.handoff.report-qualified.v1` before the terminal lifecycle event |
| `Codex Report Qualification Failed` after execution PASS | `engineering.handoff.report-qualification-failed.v1`, then `engineering.handoff.completion-rejected.v1` by the authoritative lifecycle producer |
| `Codex Failed` | `engineering.handoff.failed.v1` |
| `Codex Timed Out` | `engineering.handoff.timed-out.v1` |
| `Codex Interrupted` | `engineering.handoff.interrupted.v1` |

The current runtime has no canonical `Handoff Cancelled` signal and does not
independently expose a canonical `Handoff Blocked` signal unless separately
qualified. Those catalog events remain available to EMLS without implying a
wrapper change. For failed, blocked, timed-out, interrupted, or cancelled
execution, any report-qualification fact is published independently before the
single terminal event, as required by section 6.2.

This mapping is compatibility guidance only. Process-level signals shall not be
promoted to Handoff events until a stable Handoff identity and lifecycle source
are available. The lifecycle bridge publishes through ingress; it never invokes
the `ntfy` adapter or another transport directly.

## 16. Deferred Execution

Every item in this section is unimplemented, requires separate authorization,
and creates no implementation, migration, Governance, ETP, EOS, Work Registry,
or additional controlled-publication authority. Completed specification work shall not be
interpreted as authorization to execute this backlog.

### 16.1 Ordered Engineering Backlog

The mandatory first five items form **Phase 1 — Infrastructure Discovery and
Validation**. They are read-only, establish facts, and shall not finalize an
implementation technology or alter infrastructure:

1. **Current-state notification validation:** identify and map all notification
   documents, scripts, wrappers, configurations, services, runtime behavior,
   existing backlog entries, triggers, latency characteristics, and operational
   limitations.
2. **Raspberry Pi hosting validation:** confirm the designated host, storage,
   hardware model, operating system, memory, availability, network placement,
   available services, uptime expectations, backup/recovery constraints, and
   deployment suitability.
3. **`letoatreides` endpoint validation:** confirm operating system,
   availability, network role and reconnect behavior, desktop environment,
   notification capabilities, native APIs, startup behavior, and reference
   client suitability.
4. **Candidate technology fact collection:** evaluate SQLite, MQTT, WebSocket,
   Server-Sent Events, and any justified lightweight alternatives against the
   observed hosts and requirements without selecting a final technology.
5. **Baseline metrics:** measure publication, end-to-end notification,
   workstation delivery, mobile delivery, retry behavior, duplicate behavior,
   and delivery reliability using a documented clock and sample method.

Items 6 through 12 form **Phase 2 — Implementation Planning** and shall use
only the evidence accepted from Phase 1:

6. **Event-contract design:** finalize provider-independent event types,
   envelope versioning, timestamps, source host, mission and per-mission
   Handoff identity, severity, priority, duplicate-suppression keys, and
   compatibility rules.
7. **Persistent event-store selection and design:** select and qualify the lightweight
   durable store, acceptance transaction, retention, recovery, and missed-event
   query model while preserving the existing EOS ownership boundary.
8. **Local transport selection:** decide among MQTT, WebSocket, Server-Sent
   Events, and justified
   alternatives against LAN latency, persistence, authentication, reconnect,
   endpoint extensibility, and operational simplicity.
9. **Workstation and deployment architecture:** define service placement,
   persistent connection, history,
   acknowledgement where supported, reconnect, missed-event retrieval,
   duplicate suppression, packaging, and supervision.
10. **Provider, native adapter, and retry design:** define the first workstation
   presentation integration without making presentation authoritative.
   Retain ntfy as an optional mobile adapter; define independent endpoint
    obligations, attempt evidence, retry policy, exhaustion, recovery,
    acknowledgement semantics, and failure isolation.
11. **Latency objectives and qualification criteria:** derive measurable
    acceptance, local-presentation, reconnect-recovery, mobile, durability,
    security, backup, recovery, and rollback targets from the baseline.
12. **Validated implementation plan:** finalize the gated Phase 3 sequence,
    dependencies, validation gates, compatibility strategy, and rollback plan.

Items 13 through 20 form **Phase 3 — Notification Sprint Implementation** and
remain deferred until the validated plan is reviewed and accepted:

13. **Core Notification Service.**
14. **Persistent Event Store.**
15. **Local Transport Layer.**
16. **Reference Workstation Client.**
17. **ntfy Provider Adapter.**
18. **Prototype migration:** replace process-oriented triggering with direct
    Handoff-lifecycle emission for every engineering Handoff; preserve the
    working ntfy path until replacement equivalence is validated, avoid a
    transition outage, and remove obsolete behavior only after validation.
19. **Operational qualification:** validate durability, multi-client delivery,
    retry, duplicate suppression, reconnect recovery, tier independence,
    source-host and mission/Handoff identity, observability, latency, security,
    backup/recovery, and rollback.
20. **Future consumers:** implement the Tier 2 dashboard/terminal consumers,
    metrics and observability consumers, and EOS automation consumers under
    their existing ownership boundaries.
21. **Remote Approval Service:** specify and implement separately; HNS
    notification or acknowledgement does not define approval authority.
22. **Frozen per-EWO resolved-manifest consumption:** retain the separately
    deferred enhancement described in section 16.2.

Supporting work within those separately authorized backlog items includes
stable Handoff identity allocation, wrapper-to-EMLS lifecycle-producer
migration, producer and consumer identity infrastructure, subscription
administration, retry-policy values and retention periods, structured progress
and heartbeat qualification, delivery acknowledgement UX, implementation
qualification, and operational migration.

The initial producer integration scope includes engineering Handoff lifecycle,
Codex execution lifecycle, `engctl`, EOS, Mission 0 services, and future
Engineering Platform components. Notifications remain Handoff-oriented rather
than process-session-oriented. Handoff numbering restarts at Handoff 1 for each
mission; identifiers and payloads shall always preserve mission context and
shall never treat a Handoff number as portfolio-global.

The initial event-design catalog shall evaluate engineering work started;
Handoff created, started, completed, and failed; process started, completed,
and failed; qualification completed; publication completed; milestone
recorded; and engineering alert. Architecture design owns the final names and
definitions.

### 16.2 Future Architectural Enhancement

The following enhancement is explicitly Deferred Execution:

> Replace the centralized baseline Completion Report contract with direct
> consumption of the frozen per-EWO resolved-manifest locator.

The current qualified Completion Report implementation remains the operational
baseline. This enhancement shall not modify it without separate authorization.

## 17. Implementation Qualification Criteria

An implementation shall not be eligible for authorization or operational
acceptance until its separately authorized evidence demonstrates:

1. one authoritative source for each lifecycle event family;
2. stable Handoff identity independent of process and session lifetime;
3. schema validation and value-blind payload fixtures;
4. deterministic lifecycle and terminal-event compatibility;
5. independent execution, Report Qualification, and overall classifications;
6. durable outbox recovery and idempotent retry fixtures;
7. secret non-disclosure across events, logs, evidence, and transports;
8. adapter and consumer compatibility tests;
9. notification failure isolation from engineering execution;
10. no authority transfer through events or acknowledgements;
11. compatibility with the qualified ETP runtime implementation; and
12. Remote Approval observation compatibility without defining approval
    semantics or command authority.

## 18. Architecture Preservation Validation

| Boundary | Result | Rationale |
| --- | --- | --- |
| Governance authority | PRESERVED | Events and acknowledgements explicitly carry no authority. |
| ETP semantics | PRESERVED | Existing resolved execution and report contracts remain unchanged. |
| Work Registry | PRESERVED | No registry schema, state, or ownership role is assigned. |
| EOS data model | PRESERVED | Only a future persistence interface is identified. |
| Notification runtime | PRESERVED | Current ntfy and wrapper behavior are mapped, not modified. |
| Wrapper implementation | PRESERVED | No wrapper change is specified or performed. |
| Remote Approval compatibility | COMPATIBLE | Observation uses the event stream; decisions require a separate future command interface. |

## 19. Migration Strategy and Implementation Roadmap

The Notification Sprint follows **Discover → Validate → Design → Implement →
Qualify**. Phase 1 is the mandatory entry point. No migration occurs through
this publication.

### 19.0 Engineering Decision Classification Model

For each material implementation question, planning records shall distinguish
the following categories:

| Classification | Meaning | Permitted Treatment |
| --- | --- | --- |
| **Known** | A fact supported by objective, reproducible engineering evidence, such as measured infrastructure characteristics, verified repository behavior, confirmed platform capability, documented interfaces, or validated operational observation | May be cited as an implementation input with its evidence source, collection time, method, and material limitations |
| **Unknown** | A relevant fact not yet established with adequate evidence | Must become an explicit discovery objective; shall not be silently converted into an assumption or architecture constraint |
| **Decision** | An implementation choice that evaluates alternatives against requirements and Known facts | Remains unresolved until its prerequisite Unknowns are converted to Known facts; the selected outcome shall cite evidence, alternatives, tradeoffs, and validation conditions |

Architectural preference, familiarity, convention, or an unverified inventory
entry is not sufficient by itself to classify an item as Known or to finalize a
Decision. When evidence conflicts, is stale, or is incomplete, the item remains
Unknown or the Decision remains open. A Decision may be revisited when new
validated evidence materially changes its premises.

The advisory workflow is:

```text
Engineering question
        ↓
Classify each material input as Known, Unknown, or Decision
        ↓
Collect and record evidence for Unknown items
        ↓
Convert supported Unknowns to Known; record remaining limitations
        ↓
Resolve Decisions using validated Known facts
        ↓
Record rationale and validation gates
        ↓
Proceed with the separately approved implementation
```

Phase 1 primarily converts Unknowns into Known facts and does not finalize
Decision items. Phase 2 resolves Decisions using accepted Phase 1 evidence.
Phase 3 implements only the reviewed decisions within its approved scope. This
model reinforces the existing roadmap; it does not add a phase, technology,
deliverable, implementation obligation, or authority mechanism.

### 19.1 Phase 1 — Infrastructure Discovery and Validation

Phase 1 is entirely read-only and makes no final technology selection. It shall
validate the Raspberry Pi, `letoatreides`, and the existing notification path;
collect comparable SQLite, MQTT, WebSocket, Server-Sent Events, and justified
alternative facts; and establish repeatable latency, retry, duplicate, and
reliability metrics.

Required deliverables are an Infrastructure Validation Report, Platform
Capability Assessment, Notification Baseline Metrics, Candidate Technology
Evaluation, updated Project State, and Completion Report. Phase 1 exits only
when facts, collection methods, limitations, and unresolved unknowns are
reviewable and no infrastructure or runtime change occurred.

### 19.2 Phase 2 — Implementation Planning

Phase 2 may begin only after Phase 1 evidence is accepted. Using only validated
facts, it finalizes the transport and store selections, workstation and
deployment architecture, retry policy, latency objectives, operational
qualification criteria, dependencies, gates, rollback, and phased sequence.
It performs no implementation. Architecture recommendations in sections 8.8
and 8.9 remain provisional until this phase confirms or revises them.

### 19.3 Phase 3 — Notification Sprint Implementation

Phase 3 requires review and acceptance of the validated implementation plan.
Each implementation subphase requires its own bounded handoff, preserves the
existing ntfy path until cutover validation, and has an explicit rollback to
the last qualified state.

| Phase | Implementation Scope | Dependencies | Validation Gate | Rollback Boundary |
| --- | --- | --- | --- | --- |
| 3.1 — Core service | Raspberry Pi service skeleton, authenticated ingress, schema validation, routing boundaries, health endpoint and supervision | Accepted Phase 2 plan; host/storage/network qualification; event ownership and identity contract | Service restart, authentication rejection, schema fixtures, no provider dependency | Stop HNS; current wrapper remains unchanged |
| 3.2 — Persistent event store | Validated store schema, transactional event/obligation acceptance, backup, retention and recovery | 3.1; qualified persistent storage | Crash/restart, duplicate acceptance, integrity, backup/restore, cursor replay | Restore verified database or stop HNS; wrapper still uses ntfy |
| 3.3 — Local transport layer | Validated transport, cursor replay, ack, reconnect and slow-client handling | 3.1–3.2; certificate and endpoint identity design | LAN latency, disconnect/reconnect, missed-event replay, duplicate suppression, load and authorization | Disable transport listener; no effect on legacy path |
| 3.4 — Reference workstation client | `letoatreides` agent, durable cursor/cache, native adapter, history and health | Verified OS/network/native API; 3.3 | Native presentation, session independence, reboot, reconnect, offline replay and dedupe | Stop/uninstall agent; legacy mobile path continues |
| 3.5 — ntfy provider adapter | HNS adapter with protected configuration, async obligations and delivery evidence | 3.1–3.2; compatibility fixtures | Payload equivalence, secret safety, timeout/retry classes, partial failure | Disable HNS ntfy subscription; retain legacy helper |
| 3.6 — Migration from prototype | Lifecycle bridge publishes canonical events while legacy notification remains available; controlled shadow, dual-route, then single-writer cutover | Stable Handoff identity; 3.1–3.5 | Every Handoff independently recorded; no outage; no duplicate presentation; rollback rehearsal | Re-enable legacy wrapper trigger and disable HNS producer epoch |
| 3.7 — Operational qualification | End-to-end durability, latency, security, backup/recovery, observability and retirement evidence | All prior gates | Acceptance targets met over restart, network loss, provider outage and multi-Handoff tests | Retain prototype until qualification accepted |

Migration stages are:

1. **Observe:** baseline current ntfy timing and failure behavior without changing
   triggers.
2. **Shadow persist:** publish canonical events to HNS while legacy ntfy remains
   the presenting path; compare expected and persisted events.
3. **Shadow local delivery:** run the reference agent with presentation muted;
   validate ordering, replay, acknowledgement, dedupe, and latency.
4. **Controlled dual route:** enable local presentation while retaining legacy
   ntfy; use distinct idempotency and presentation policy to prevent duplicate
   operator alerts.
5. **Provider cutover:** route ntfy through HNS and disable the direct helper
   only after equivalence and rollback rehearsal.
6. **Lifecycle cutover:** replace process-derived events with direct per-Handoff
   lifecycle publication under a fenced single-writer epoch.
7. **Retire:** remove obsolete wrapper notification logic and configuration only
   after operational qualification and an observation window with no unresolved
   event loss, duplicates, or latency regressions.

Rollback never deletes HNS history. It stops new canonical publication or
delivery at a defined phase boundary, restores the previously qualified direct
ntfy trigger if necessary, and records the rollback condition. Database schema
changes require forward-compatible migrations and a verified pre-migration
backup. Provider failure never requires rollback of local authoritative event
recording.

## 20. Architecture Decision Summary

| Decision | Baseline |
| --- | --- |
| Service placement | Always-on designated Raspberry Pi; AST-000007 requires HNS host qualification |
| Event authority | Source systems own lifecycle facts; HNS owns accepted notification records, obligations and delivery evidence |
| Persistence | SQLite WAL recommendation; final selection deferred to Phase 2 evidence review |
| Tier 1 transport | Authenticated TLS WebSocket recommendation; final selection deferred to Phase 2 evidence review |
| Tier 2 transport | Event query/history API; optional SSE for browser live updates |
| Tier 3 providers | Asynchronous adapters; ntfy first, mobile presentation non-authoritative |
| Delivery semantics | Durable at-least-once with event/obligation deduplication |
| Reference endpoint | `letoatreides`, gated on OS, availability, network and native API validation |
| Latency posture | Persist locally, route local first, keep connections warm, avoid batching, dispatch providers asynchronously |
| Migration | Shadow, controlled dual route, provider cutover, lifecycle cutover, observation, retirement |

## 21. Planning Conclusion

The proposed architecture separates authoritative lifecycle facts from
delivery mechanics, preserves Handoff-level identity, and provides reusable
publish, subscribe, consumer, adapter, and evidence interfaces. Future services
can consume the same event stream without redesigning producers or transports.

This controlled publication creates no Notification Service implementation
authority.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-18 | Published the qualified Notification Service architecture, deterministic event lifecycle, ownership and identity boundaries, transport-independent interfaces, reliability model, trust boundaries, runtime compatibility, and explicit Deferred Execution backlog without authorizing implementation. |
| 1.1 | 2026-07-18 | Recorded the approved Homelab Notification System direction: Raspberry Pi authority, `letoatreides` reference client, three delivery tiers, authoritative local persistence, secondary mobile delivery, bounded implementation backlog, and outage-free ntfy migration without beginning implementation. |
| 1.2 | 2026-07-18 | Established the HNS implementation architecture baseline from repository assessment: canonical platform event catalog, SQLite WAL store, authenticated WebSocket Tier 1 transport, provider and workstation interfaces, current-flow and technical-debt analysis, staged migration, rollback, validation gates, and seven-phase roadmap without runtime or Governance changes. |
| 1.3 | 2026-07-18 | Inserted mandatory read-only Infrastructure Discovery and Validation before evidence-based Implementation Planning and the seven-subphase Notification Sprint; made technology recommendations provisional pending validated facts and preserved implementation deferral. |
| 1.4 | 2026-07-18 | Accepted advisory architecture observations: long-term Engineering Event Platform vision, foundational authority separation, WebSocket and SQLite evolution rationale, canonical producer identity, independent event/delivery/provider identities, future-consumer extensibility, and the preferred staged migration pattern without expanding scope or sequencing. |
| 1.5 | 2026-07-18 | Recorded HNS as the authoritative engineering event-record and delivery platform, clarified producer/HNS/provider responsibilities, made providers explicitly replaceable consumers and presentation mechanisms, and preserved source lifecycle ownership and implementation scope. |
| 1.6 | 2026-07-18 | Recorded the advisory Known/Unknown/Decision classification model, evidence-conversion workflow, and Phase 1/2/3 relationship without changing architecture, sequencing, scope, technologies, or implementation obligations. |
