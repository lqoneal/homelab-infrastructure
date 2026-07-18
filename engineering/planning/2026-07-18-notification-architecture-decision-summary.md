# Engineering Notification Architecture Decision Summary

## Decisions

1. Active SPEC-0009 remains the authoritative architecture; this plan is its
   implementation specialization.
2. Handoff—not process, PID, terminal, wrapper, repository session, or Codex
   conversation—is the primary lifecycle unit.
3. Lifecycle fact ownership, event persistence, routing, transport delivery,
   and delivery evidence remain separate.
4. Producers publish canonical events and never call provider adapters.
5. The service provides durable at-least-once delivery with idempotent event
   acceptance and independent obligations.
6. ntfy is the first adapter, not the notification architecture.
7. Provider configuration and credentials are referenced outside events and
   redacted from evidence.
8. The implementation starts embedded/local but preserves service-grade
   interfaces for future Engineering Platform hosting.
9. Stable Handoff identity and sequence allocation are hard prerequisites for
   canonical Handoff publication.
10. Existing process events remain compatibility observations; additional
    Work, qualification, publication, milestone, process, and alert families
    require separate specification and qualification.
11. Migration uses shadow comparison and a fenced single-writer cutover.
12. Automation, Remote Approval design, new providers, dashboards, metrics,
    EOS automation, and broader event families remain follow-on work.

## Rejected Alternatives

- Direct provider calls from every workflow: duplicates logic and couples
  engineering behavior to transports.
- Treating Codex process lifetime as Handoff identity: violates SPEC-0009 and
  fails persistent multi-Handoff sessions.
- Best-effort delivery without persistence: loses events during provider or
  process failure.
- Exactly-once external delivery claims: not enforceable across general
  providers.
- Encoding Governance decisions in notifications: transfers authority into an
  observational subsystem.
- Immediate replacement of the prototype: creates unnecessary operational risk.

## Review Gate

Before implementation, review this plan against SPEC-0009 and authorize an
exact sprint scope. Any need to change canonical ownership, lifecycle,
identity, envelope, EOS boundaries, or deferred controlled requirements must
return to Engineering Governance rather than being resolved in code.

## Planning Recommendation

Accept this implementation architecture as the Notification Sprint planning
baseline, subordinate to SPEC-0009, and begin implementation only through a
separately approved Active Work Order.
