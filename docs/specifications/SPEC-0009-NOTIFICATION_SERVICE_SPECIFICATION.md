---
document_id: SPEC-0009
title: Notification Service Specification
version: 1.0
status: Active
owner: Engineering Platform
created: 2026-07-18
last_updated: 2026-07-18
phase: Notification Service Controlled Publication
domain: Engineering Platform
classification: Engineering Specification
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Handoff - Notification Service Controlled Publication
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
---

# Notification Service Specification

## 1. Purpose

This specification defines a reusable Engineering Platform Notification
Service architecture. The service publishes value-blind engineering lifecycle
events, routes them to authorized consumers and delivery adapters, records
delivery evidence, and preserves failure isolation between engineering work and
notification delivery.

This controlled specification does not activate EWO-000020, authorize
implementation, change the existing notification runtime, create Governance
authority, or establish a new controlled-document owner.

## 2. Architectural Context and Boundaries

The Notification Service is a cross-cutting platform service. It consumes
facts emitted by authoritative lifecycle owners and makes those facts available
to delivery adapters and future engineering consumers.

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

## 15. Existing Runtime Compatibility

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

1. Notification Service implementation.
2. Canonical engineering event envelope qualification.
3. EOS-compatible outbox implementation under the existing EOS ownership
   boundary.
4. Existing `ntfy` adapter migration after compatibility qualification.
5. Remote Approval Service Specification under separate design authority.
6. Remote Approval Service implementation under separate implementation
   authority.
7. Dashboard consumer implementation.
8. Metrics and observability consumer implementation.
9. EOS automation consumer implementation under the existing EOS boundary.
10. Frozen per-EWO resolved-manifest consumption enhancement described in
    section 16.2.

Supporting work within those separately authorized backlog items includes
stable Handoff identity allocation, wrapper-to-EMLS lifecycle-producer
migration, producer and consumer identity infrastructure, subscription
administration, retry-policy values and retention periods, structured progress
and heartbeat qualification, delivery acknowledgement UX, implementation
qualification, and operational migration.

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

## 19. Recommended Post-Publication Sequence

This sequence organizes the Deferred Execution backlog in section 16; it does
not duplicate or supersede that authoritative backlog. Every step requires
separate authorization:

1. Obtain separate authorization for the selected Deferred Execution scope.
2. Qualify the specified Handoff Identity Authority interface and
   authoritative event-family ownership model.
3. Define the EOS-compatible outbox persistence contract.
4. Qualify the envelope, lifecycle, security, and value-blind schemas.
5. Implement ingress and durable outbox before external adapters.
6. Implement subscription routing and delivery evidence.
7. Add an ntfy compatibility adapter and migrate only after equivalence tests.
8. Add internal consumer interfaces for dashboards, monitoring, metrics, and
   EOS automation.
9. Validate multi-Handoff recovery, retries, partial delivery, and failure
   isolation.
10. Produce the Remote Approval Service Specification under separate Governance
    authority before considering its implementation.

## 20. Planning Conclusion

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
