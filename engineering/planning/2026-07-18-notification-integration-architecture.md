# Engineering Notification Integration Architecture

## Integration Principle

Lifecycle owners publish facts. The Notification Service persists and routes
them. Adapters deliver them. Consumers observe them. None of these actions
changes the originating lifecycle or grants authority.

## Integration Points

| Source | Integration boundary | Initial treatment |
| --- | --- | --- |
| Codex lifecycle | Qualified wrapper-to-Handoff lifecycle bridge | Translate safe start, terminal, timeout, interruption, and report qualification observations after stable Handoff ID allocation |
| `engctl` | Notification client and operator diagnostics | Publish through service client; optional future `engctl notify status/test` must not accept arbitrary unsafe content |
| EOS | Persistence port and recovery coordination | Supply approved application-data location/transaction contract; Notification Service cannot mutate engineering state |
| EMLS | Canonical Handoff identity, sequence, and lifecycle producer | Future direct owner; replaces bridge at fenced single-writer cutover |
| PROC-0006 qualification | Candidate future qualified event bridge | No new canonical family until separately specified |
| PROC-0005 publication | Candidate future publication evidence bridge | Publish only after separately qualified event ownership and schema |
| Milestone records | Candidate future controlled-record observer | Observe persisted record; never infer approval from a notification |
| Mission 0 services | Publish/consumer SDK | Adopt stable envelope and subscriptions without provider knowledge |
| Dashboards/metrics/automation | Consumer interface | Read accepted events; cannot republish observations as authoritative facts |

## Handoff Identity Dependency

Canonical Handoff events require the SPEC-0009 allocation interface. The
wrapper may not derive identity from PID, terminal, Codex session, EWO, or
repository. Implementation must either qualify the transitional Handoff
Identity Authority or wait for EMLS. No ID means no canonical Handoff publish.

## Single-Writer Migration

During transition, only the qualified lifecycle bridge publishes Handoff
events. EMLS cutover uses an epoch/fence so bridge and EMLS cannot co-publish a
transition. Provider adapters and consumers remain unchanged.

## Failure Isolation

- Producer success depends on durable acceptance, not external delivery.
- Engineering execution does not fail because ntfy, email, or another provider fails.
- Persistence failure rejects publication so the producer can retain/retry the event.
- One adapter, route, subscription, or consumer cannot block unrelated obligations.
- Service health is observable through a safe independent diagnostic path.

## Compatibility

The ntfy compatibility subscription shall reproduce current value-blind start
and terminal operator notifications during shadow validation. Direct wrapper
delivery remains the operational path until equivalence and cutover are
authorized.
