# EMP Execution Oversight

Date: 2026-07-25
Status: Supervised execution oversight implementation
Mission: Zeus Operational Alpha Mission K

## Boundary

Execution Oversight consumes a Mission J Execution Assignment and its validated
dispatch event. It creates exactly one Execution Session for that assignment
and supervises events without invoking, controlling or modifying the execution
agent.

There is no execution, dispatch, mission selection, retry, automatic recovery,
evidence qualification, WOP completion, Project State update, Work Registry
update, controlled-document reconciliation or engineering reconciliation API.

## Execution Session

An immutable session identity binds the assignment, mission, WOP, repository,
baseline, execution agent and creation timestamp. Current runtime fields are an
authoritative projection of the immutable event ledger rather than independent
mutable authority:

- current execution state and checkpoint;
- last received event;
- approval status;
- completed and pending milestones;
- interruption history;
- resume eligibility and expected restart point;
- deterministic session digest.

Assignment-to-session mapping is one-to-one.

## State machine

The implementation supports ten states:

`Dispatched`, `Accepted`, `Initializing`, `Running`, `Waiting Approval`,
`Paused`, `Resuming`, `Completed`, `Failed`, and `Cancelled`.

Legal edges are explicit. Terminal states are immutable. Waiting Approval can
enter Resuming only after an explicit approved EENS event. Rejected and expired
approvals prevent resume eligibility. Invalid events are rolled back from
memory and never reach persistent state.

## EENS ingestion

EENS is the only accepted source for execution-agent events. Every envelope
must:

- authenticate through the configured verification interface;
- identify `EENS` as producing component;
- bind exactly to assignment, session, repository, baseline and execution
  agent;
- carry a unique event identifier and nondecreasing timestamp.

Oversight-generated interruption events identify `EMP-OVERSIGHT` as their
component and are not represented as execution-agent events.

## Ledger and replay

Each event records its sequence, identifier, timestamp, component, agent,
state, payload digest, previous hash and current hash. Payloads are persisted
alongside the ledger and verified by digest. Replay validates the chain,
transition graph, ordering, approval semantics and payload binding before
producing the session projection.

Canonical JSON persistence is atomically replaced. Restart replay produces a
byte-equivalent projection and session digest.

## Interruption and recovery planning

Oversight detects agent disconnect, heartbeat timeout, unexpected termination,
repository mismatch and assignment mismatch. Detection records the cause,
pauses or fails closed according to the legal state graph, and derives an
expected restart checkpoint. No recovery or resume action is performed.
