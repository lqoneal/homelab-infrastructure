# Zeus Execution Lifecycle Procedure

This controlled procedure defines the prepublication Development lifecycle for a receipt-backed Zeus submission.

## Authority and persistence

Engineering Governance authorizes execution through submission. Stage 1 transactions and their receipts are immutable authority. Admission, execution, native-session, reconciliation, qualification, publication, synchronization, and closeout records are derived operational projections. A derived record may be created or repaired only from one validated Stage 1 transaction and must retain its transaction, WOP, package, source, authority, provider, dispatch, and repository bindings.

`zeus submit` may report `DISPATCHED` only after the dispatch receipt, admission projection, execution projection, and reconciliation receipt have been atomically installed and re-read successfully. Failure produces a durable `BLOCKED` checkpoint with the original transaction identity and a resumable next action.

## Canonical command path

`submit` is the first lifecycle event. `submit`, `execute-mission start`, `status`, `session`, `resume`, `suspend`, `cancel`, qualification, publication preparation, synchronization, and closeout resolve the exact requested transaction through the shared reconciliation transaction before consuming derived runtime state. Submission does not require publication, merge, or EOS synchronization. No command resubmits a WOP or creates authority.

## Recovery and closeout

Reconciliation acquires a transaction-scoped lock, discovers projections, classifies missing/partial/stale/duplicate/divergent/corrupt state, prepares and validates all writes, atomically promotes them, verifies the result, and emits a sealed reconciliation receipt. Interrupted work is resumed from the durable Stage 1 checkpoint or rolled back. Qualification, publication, EOS synchronization, and closeout remain gated by their receipts and parity checks.
