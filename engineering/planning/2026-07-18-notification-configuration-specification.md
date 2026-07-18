# Notification Configuration Specification

## Model

Separate non-secret routing policy from secret provider material.

```yaml
notification:
  schema_version: 1
  service:
    persistence_profile: eos-compatible-local-v1
    worker_count: 1
    default_deadline_seconds: 15
  providers:
    ntfy_primary:
      adapter: ntfy
      credential_ref: xdg://engineering/notifications/ntfy-primary
      rate_limit: {requests: 30, per_seconds: 60}
  routes:
    operator_handoffs:
      providers: [ntfy_primary]
      topic_ref: secret://ntfy/operator-topic
      priority_map: {INFO: default, WARNING: high, ERROR: urgent}
  subscriptions:
    handoff_terminal:
      event_types: [engineering.handoff.completed.v1, engineering.handoff.failed.v1]
      filters: {project_id: [homelab]}
      routes: [operator_handoffs]
      retry_policy: standard
  retry_policies:
    standard:
      max_attempts: 8
      initial_seconds: 5
      multiplier: 2
      max_seconds: 900
      jitter: bounded
```

This is an illustrative implementation profile, not a controlled schema.

## Requirements

- Version and validate the full configuration before activation.
- Atomically reload only a complete valid snapshot.
- Pin each obligation to the subscription and route version matched at intake.
- Use provider IDs and credential references, never inline secrets.
- Validate topics, recipients, filters, priorities, retry bounds, and rate limits.
- Reject unknown adapters, event major versions, unsafe fields, and cyclic fallbacks.
- Redact endpoint, topic, recipient, token, and credential values from logs.

## Secret Resolution

Retain XDG per-user mode-`0600` files for the first ntfy adapter or adopt an
approved secret provider later. The service resolves secret references only at
adapter invocation and passes the minimum necessary material to that adapter.

## Routing and Filtering

Allowed filter dimensions are canonical event type, project, repository,
environment, severity, and bounded subject classification. Filters never
inspect prompts, reports, logs, diffs, or arbitrary payload text.

## Retry and Rate Limits

Policies define maximum attempts, elapsed horizon, exponential bounds, jitter,
retryable classes, and recovery authorization. Apply provider and route token
buckets before dispatch. A rate-limited obligation remains durable and does
not block other providers.

## Configuration Precedence

Recommended precedence: explicit test override, approved service configuration,
XDG operator configuration, then safe defaults. Repository examples contain
placeholders only and must remain rejected for live delivery.
