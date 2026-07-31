# Automatic Synchronization by Design

Status: `PROPOSED — NON-AUTHORITATIVE`

## Principle

Synchronization is an architectural property, not a closeout activity. Every
engineering subsystem shall declare the authoritative source for each fact,
its derived representations, a one-way synchronization mechanism, its owner,
trigger, verification, drift detector, reconciliation route, and recovery
behavior. A derived representation may be stale or unavailable; it may never
become authoritative merely because its source is unavailable.

## Required synchronization contract

| Field | Requirement |
|---|---|
| Fact identifier and schema revision | stable identity for the synchronized fact |
| Authoritative source and owner | exactly one writer of the fact |
| Representation and classification | authoritative, derived, runtime, or historical |
| Direction and mechanism | source → target, with event, pull, or deterministic generation mechanism |
| Trigger and freshness target | publication, source revision, event, scheduled reconcile, or explicit operator request |
| Synchronization owner | accountable component that performs/coordinates the transfer |
| Verification | digest, revision, schema, provenance, and semantic predicate |
| Drift and reconciliation | detectable mismatch, owner-routed correction, no reverse overwrite |
| Recovery | checkpoint/replay/rebuild behavior and safe failure state |

## Architectural invariants

1. A fact is authored once; copied, rendered, indexed, and projected forms are
   not alternate writers.
2. A source-to-projection edge is directional. EOS, dashboards, reports, and
   documentation cannot write back to Governance, EMP, Zeus, or controlled
   records.
3. Every synchronization result is attributable to its source revision and
   target revision.
4. Missing, stale, conflicting, or unverifiable synchronization is `UNKNOWN`,
   `DIRTY`, or `BLOCKED`; it is never a favorable inference.
5. Reconciliation corrects the authoritative source only through its owner,
   then regenerates or re-synchronizes the target.
6. Synchronization failures are engineering events: EENS may persist/deliver
   them, EOS may record projection status, and Zeus may surface them. None of
   those roles changes the source owner or qualification decision.

## Lifecycle

```text
authoritative revision
  -> validate source metadata
  -> generate or synchronize target
  -> verify digest/provenance/semantics
  -> publish target with source revision
  -> monitor freshness and drift
  -> reconcile at source owner; replay/rebuild target when needed
```

The lifecycle applies continuously, including before admission and during
execution. Closeout verifies outstanding projections; it does not introduce
the synchronization requirement.
