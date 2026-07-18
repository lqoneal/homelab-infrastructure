# Notification Provider Interface Specification

## Contract

```text
ProviderAdapter
  identity() -> ProviderDescriptor
  validate(config_ref) -> Valid | Invalid(reason_class)
  capabilities() -> CapabilitySet
  render(event, route) -> ProviderRequest | PermanentFailure(reason_class)
  deliver(request, idempotency_key, deadline) -> DeliveryResult
  health() -> Healthy | Degraded(reason_class) | Unavailable(reason_class)
```

Adapters receive an immutable canonical event plus a resolved, non-secret route
view. They return classified transport results and never mutate or republish
the event.

## Delivery Result

```text
Delivered(receipt_class, provider_message_id?, completed_at)
Deferred(reason_class, retry_after?)
Rejected(reason_class)
Unavailable(reason_class)
```

Provider message IDs are evidence only. `Delivered` does not prove human
observation or acceptance.

## Capabilities

- maximum title/body size;
- supported priority range;
- tags, actions, attachments, and markdown support;
- provider idempotency support;
- rate-limit metadata;
- synchronous receipt support; and
- acknowledgement support, if separately specified.

The routing layer selects only capabilities required by a subscription. It
shall not branch engineering workflows by provider.

## Initial ntfy Adapter

Reuse the current helper's HTTPS enforcement, bearer token, title, priority,
tags, bounded timeout, safe errors, and configuration validation. Move message
rendering behind the adapter and map transport status into generic result
classes. Topics and endpoints remain secret configuration references.

## Future Adapters

| Provider | Adapter-specific concern | Core remains unchanged |
| --- | --- | --- |
| Email | recipient policy, subject/body, SMTP/API receipt | event, obligation, retry, evidence |
| Slack | webhook/app authentication, blocks, rate limit | event and subscription contract |
| Discord | webhook/bot limits and embeds | event and delivery state |
| SMS | strict length, cost, opt-in, delivery receipt | event routing and evidence |
| Generic webhook | signing, TLS, status classification | ingress and outbox semantics |

## Adapter Qualification

Every adapter must pass a common contract suite for validation, rendering
determinism, secret redaction, timeout, transient/permanent classification,
rate limiting, idempotency, retry safety, and failure isolation. Live provider
tests are separately authorized and use non-sensitive synthetic events.
