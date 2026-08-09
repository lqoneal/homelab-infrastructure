# Implementation Report

The controller now validates canonical receipt paths, receipt digests,
transaction-side digest references, identity bindings, milestone ordering,
pending/completed complements, prepublication PASS state, and persisted next
action. One `_resolve_next_action()` function derives publication action from
that durable projection and permits candidate/cohort revalidation only to
invalidate it.

Milestone persistence is explicitly ordered: generate/reuse receipt, update
the transaction, atomically persist it, reload it, validate full integrity,
then return the derived next action. Persistence and reload failures are typed
fail-closed errors. Existing valid orphan receipts are reusable, while forged
or conflicting receipts fail.

`verify-pre` is now an explicit CLI spelling, with `verify` retained for
compatibility. Successful preverification reports `read_only=false` because it
persists authority state. Replay reports `replayed=true`. JSON errors expose a
typed blocker and recovery action.

`stage()` no longer accepts `CANDIDATE_ISOLATED`; it requires and validates
durable `PREPUBLICATION_VERIFIED` before cohort revalidation or `git add`.
Status, inspect, resume, and mission projection all use the transaction-owned
resolver.

