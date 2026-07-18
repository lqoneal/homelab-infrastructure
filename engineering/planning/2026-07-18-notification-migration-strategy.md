# Engineering Notification Migration Strategy

## Goal

Replace the synchronous process-oriented ntfy prototype with canonical
Handoff-oriented service delivery while preserving current notifications and
avoiding a flag-day cutover.

## Migration Phases

1. **Freeze and characterize:** preserve current behavior and tests; record
   titles, safe fields, signals, timeouts, exit handling, and failure isolation.
2. **Build service core offline:** implement envelope validation, persistence,
   routing, evidence, and fake adapter without touching the wrapper.
3. **Qualify identity and bridge:** implement the separately authorized stable
   Handoff identity/sequence interface and translate wrapper observations.
4. **Add ntfy adapter:** port secure configuration and request behavior behind
   the provider contract; run adapter contract tests.
5. **Shadow mode:** canonical events create obligations and evidence while the
   existing direct ntfy path remains authoritative for operator delivery.
6. **Equivalence gate:** compare event-to-message mapping, terminal coverage,
   latency bounds, failure isolation, redaction, retry, and multi-Handoff identity.
7. **Single-writer cutover:** disable direct wrapper transport calls and enable
   the service ntfy subscription in one bounded transaction.
8. **Remove compatibility shim:** only after rollback horizon and operational
   qualification; retain historical tests as regression cases.

## Compatibility Mapping

| Prototype observation | Canonical treatment |
| --- | --- |
| Codex Started | Handoff Started after allocated Handoff identity |
| Codex Complete | Handoff Completed only after execution/report matrix resolves |
| Report Qualification Failed | Report Qualification Failed plus Handoff Completion Rejected when execution passed |
| Codex Failed | Handoff Failed |
| Codex Interrupted | Handoff Interrupted |
| Codex Timed Out | Handoff Timed Out |
| Wrapper bypass | Engineering alert candidate or local diagnostic; not a Handoff transition without accepted identity |

## Rollback

Before cutover, rollback means disable shadow publishing. At cutover, preserve
the last direct-delivery configuration and a bounded reversal plan. Never run
both direct and service ntfy delivery as authoritative after cutover. Persisted
obligations and delivery evidence are never deleted to simulate rollback.

## Acceptance Conditions

- stable identity across multiple Handoffs in one Codex session;
- exactly one terminal event per attempt;
- no duplicate operator notifications at cutover;
- delivery outage recovery from the durable outbox;
- value-blind payload and secret redaction;
- direct-path functional equivalence;
- original execution and report qualification behavior preserved; and
- complete rollback and post-cutover evidence.
