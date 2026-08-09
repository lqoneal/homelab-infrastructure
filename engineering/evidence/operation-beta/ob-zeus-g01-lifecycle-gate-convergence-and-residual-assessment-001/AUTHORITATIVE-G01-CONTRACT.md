# Authoritative OB-ZEUS-G01 Contract

## Authority order

1. The machine-readable canonical gate catalog is the deterministic gate
   contract: `engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml`.
2. Its controlled Markdown companion describes the same gate inventory and
   dependency graph.
3. `ZEUS-CANONICAL-DEVELOPMENT-ROADMAP.md` supplies the normalized P5-G6,
   P5-G7, and P5-G8 capability meanings.
4. The active WOP supplies executable lifecycle scope, but its later Gates
   5–7 do not enlarge G01.
5. Historical gap plans and point-in-time reports are evidence and
   traceability, not superior authority.

## Normalized contract

`OB-ZEUS-G01` is the Zeus/ZDCL capability gate titled **Monitoring pause/resume
and provider recovery**. Its required input is the qualified execution
foundation from G00. It produces authoritative liveness, progress projection,
and recovery re-entry for G02 and other consumers.

Its substantive scope is:

- P5-G6: execution status, authoritative liveness, progress/current work
  position, blockers, approvals where applicable, operator visibility,
  source-bound execution state, applicable EENS integration, and independent
  Zeus monitoring verification;
- P5-G7: pause/resume, session and crash recovery, idempotent restart, state
  reconciliation, preserved execution identity, no duplicate execution, and
  Zeus verification;
- P5-G8: provider fault detection/classification, artifact preservation,
  retry/recovery policy, repair or replacement, safe re-entry, last-safe-state
  selection, no duplicate execution, and Zeus verification;
- cross-cutting: one canonical owner, deterministic positive/negative,
  provenance/dependency, replay and fail-closed proof, native projections,
  qualified evidence, controlled-document coverage, and immutable prior
  evidence.

## Excluded G02/later scope

Completion receipt/journal, provider terminal state, execution-completion
authority, evidence-result qualification, controlled publication,
repository/origin/EOS synchronization, terminal closeout, and the sacrificial
end-to-end `CLOSED` proof belong to `OB-ZEUS-G02`, integrated qualification, or
later lifecycle acceptance. They are not G01 residuals.

The previous G02 contract incorrectly named `evidence_qualification` both as
an entry input and as Phase 6/7 work inside G02. This assessment removes that
circular dependency; G02 now depends only on G01's monitoring/recovery output.

## Acceptance interpretation

Capability acceptance does not require the current mission to be actively
executing during a read-only assessment. It requires qualified active-state
proof, integrated commands, negative/replay tests, and truthful live
projection of the current non-active state. P5-G6 has an accepted active
demonstration. P5-G7/G8 have published deterministic disposable-runtime proof
plus live read-only integration. An unrecoverable provider instance must fail
closed; it need not manufacture missing thread persistence to demonstrate a
valid recovery controller.

