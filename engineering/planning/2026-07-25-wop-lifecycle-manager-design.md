# EMP WOP Lifecycle Manager

Date: 2026-07-25
Status: Management layer implementation
Mission: Zeus Operational Alpha Mission I

## Boundary

The lifecycle manager consumes a Zeus-authorized WOP and ADR v2, then manages
planning state from `Draft` through `Ready`. `Ready` is terminal. No API,
transition or CLI command exists for dispatch, execution, monitoring, live
lease acquisition, evidence qualification or reconciliation performance.

## Lifecycle

The six legal transitions are:

`Draft → Staged → Eligible → Selected → Authorized → Reserved → Ready`

Every transition is append-only, ordered, hash chained and bound to the stored
Zeus authorization decision digest plus repository identity and baseline.
Skipping, reversing or advancing beyond `Ready` fails closed.

## Queue and selection

Queue order is deterministic by ascending priority, staging order, mission
identity and WOP identity. Blocked and deferred missions are excluded.
Dependencies must be complete before selection. Only one selected mission is
retained.

## Planning models

- Approval checkpoints are immutable status transitions ending in approval,
  rejection or supersession.
- Reservations are future-planning objects with `planning_only: true`,
  `grants_authority: false` and `is_execution_lease: false`.
- Resume replays the lifecycle hash chain and reports completed/pending
  transitions, approvals, reservation and evidence expectations.
- Evidence planning tracks required, produced and missing identifiers without
  qualification.
- Reconciliation planning lists expected Project State, Work Registry,
  controlled-document, mission-status and completion-evidence updates without
  performing them.

## Persistence

Canonical JSON is atomically replaced in a caller-selected repository path.
Reload validates inventory/queue agreement, transition legality, event digests,
reservation boundaries and reconstructed state.
