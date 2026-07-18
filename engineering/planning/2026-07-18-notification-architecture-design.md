# Engineering Notification Architecture Design

## Status and Authority

This implementation architecture derives from Active SPEC-0009 Version 1.0.
SPEC-0009 remains authoritative. This plan creates no implementation authority
and does not redefine Governance, EOS, ETP, or controlled event semantics.

## Design Outcome

Implement one provider-independent Notification Service with an embedded-first,
single-writer deployment profile and stable interfaces that can later be hosted
as an Engineering Platform service without producer or adapter redesign.

```text
Authoritative owner / qualified transitional bridge
                  |
             publish(envelope)
                  v
       Ingress + schema/policy validation
                  v
        Durable event/outbox transaction
                  v
        Subscription and routing engine
             /          |          \
        ntfy adapter  future adapters  internal consumers
             \          |          /
               Delivery evidence
```

## Components

### Notification Service Core

Responsibilities:

- authenticate producers and validate family-level publish permission;
- validate schema, ownership, value-blind content, identity, sequence, and size;
- persist accepted events before acknowledgement;
- create independent event/subscription delivery obligations;
- dispatch due obligations through provider adapters;
- apply retry, rate-limit, dead-letter, and recovery policy;
- expose subscription and delivery-evidence reads; and
- emit bounded service diagnostics without recursive failure loops.

The core shall not allocate Governance authority, infer engineering lifecycle,
mutate EOS engineering state, render provider-specific messages, or claim human
acknowledgement.

### Persistence Boundary

Use a persistence port with atomic operations:

```text
accept_event(envelope, matched_subscription_versions)
claim_due_obligations(worker_id, lease_until, limit)
record_attempt(obligation_id, attempt)
complete_obligation(obligation_id, receipt)
defer_obligation(obligation_id, next_attempt_at, reason_class)
exhaust_obligation(obligation_id, reason_class)
```

The initial implementation may use SQLite WAL in an EOS-approved application
data location after the EOS-compatible outbox contract is separately
authorized. The storage schema belongs to the Notification Service adapter and
shall not redefine EOS state.

### Public Interfaces

- Publish: canonical envelope in; Accepted, Duplicate, or Rejected out.
- Subscribe: versioned route definition in; subscription identity/version out.
- Consumer: ordered pull or acknowledged stream for authorized internal users.
- Evidence: value-blind obligation and attempt status queries.
- Health: readiness, persistence, queue depth class, and adapter health without secrets.

Use a local Unix-domain socket or in-process client initially. Preserve the
same request/response contracts for a future authenticated service endpoint.

### Lifecycle

```text
STARTING -> RECOVERING -> READY -> DEGRADED -> DRAINING -> STOPPED
                         \-> FAILED
```

`READY` requires writable persistence and valid configuration. An unavailable
adapter produces `DEGRADED`, not loss of accepted events. Shutdown stops
ingress, releases or expires leases, records safe evidence, and drains within a
bounded deadline.

## Delivery Semantics

- At-least-once adapter invocation.
- Idempotent event acceptance by `event_id`.
- One obligation per event and subscription version.
- Stable provider idempotency key derived from obligation identity where supported.
- Per-Handoff ordered dispatch; unrelated Handoffs may execute concurrently.
- Delivery failure never changes authoritative engineering lifecycle state.
- Exhausted obligations remain queryable and recoverable under explicit policy.

## Error Classes

| Class | Treatment |
| --- | --- |
| Invalid envelope or unauthorized producer | Reject before persistence; safe diagnostic |
| Duplicate event | Return existing identity without new obligations |
| Persistence unavailable | Fail closed; producer retains/retries event |
| Transient provider/network failure | Retry with bounded exponential backoff and jitter |
| Rate limited | Honor safe retry-after bound; apply provider limiter |
| Permanent provider/configuration rejection | Exhaust or quarantine obligation; do not retry indefinitely |
| Worker crash or lease expiry | Reclaim obligation idempotently |
| Poison subscription or renderer | Isolate affected obligation and route; continue others |

## Security and Trust

- Value-blind allowlisted attributes only.
- Secrets resolved by provider configuration references, never event payloads.
- Producer authentication separated from lifecycle ownership.
- Provider credentials least-privilege and locally permissioned.
- Logs and evidence exclude endpoints, topics, tokens, prompts, reports, output, and repository content.
- Subscription administration requires separate authorization from event publication.

## Deployment Units

Recommended implementation modules:

```text
notification/domain       envelope, types, validation, state
notification/application  publish, route, dispatch, recover
notification/ports        persistence, clock, identity, adapter, auth
notification/adapters     sqlite, ntfy, future providers
notification/interfaces   local client, CLI, service endpoint
notification/testing      fakes, contract suites, fault injection
```

Module names are planning guidance, not authorized repository paths.
