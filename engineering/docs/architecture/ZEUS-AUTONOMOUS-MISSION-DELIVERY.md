# Zeus Autonomous Mission Delivery Architecture

## Status

Prepublication Development candidate. This document defines the Zeus-owned
derived lifecycle projection; the published Operational Alpha authority chain
remains the only authority source.

## Contract

`zeus submit <wop>` validates and persists the immutable Stage 1 transaction,
then atomically reconciles admission and execution projections. The
autonomous lifecycle ledger records the resolved phase, protected identities,
blockers, and next action. `zeus mission status|blockers|next|snapshot` reads
that ledger by exact transaction, mission, or WOP identity.

Stage 1 receipts outrank all derived records. Derived admission, execution,
session, publication, synchronization, and closeout projections may be
repaired only when identity, authority, and provenance are unambiguous.

## Authority boundaries

Zeus may diagnose and repair bounded derived runtime state, retry an authorized
receipt-backed phase, preserve evidence, and resume. It must stop for new
governance authority, required publication approval, destructive effects,
missing credentials, physical actions, ambiguous state, or failed atomicity.
EOS synchronization and publication remain governed transactions; they are not
silently simulated by the lifecycle ledger.

## Invariants

Every successful phase has a durable verified representation, one transaction
identity, no duplicate admission or execution identities, and a deterministic
replay result. A blocker includes evidence and the next governed action.
