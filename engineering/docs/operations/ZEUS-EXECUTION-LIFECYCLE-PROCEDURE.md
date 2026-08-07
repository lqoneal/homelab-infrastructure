# Zeus Execution Lifecycle Procedure

This controlled procedure defines the prepublication Development lifecycle for a receipt-backed Zeus submission.

## Authority and persistence

Authoritative Zeus submission establishes the submitted WOP's work authority
for its declared scope. Stage 1 transactions and their receipts are immutable
submission/provenance records. Admission, identity and integrity validation,
prerequisites, provider qualification, session safety, lifecycle, baseline,
explicit in-WOP approval gates, publication, synchronization, and closeout
remain separate downstream controls; they do not constitute another grant of
operator work authority. A derived record may be created or repaired only
from one validated Stage 1 transaction and must retain its transaction, WOP,
package, source, authority source, provider, dispatch, and repository
bindings.

`zeus submit` may report `DISPATCHED` only after the dispatch receipt, admission projection, execution projection, and reconciliation receipt have been atomically installed and re-read successfully. Failure produces a durable `BLOCKED` checkpoint with the original transaction identity and a resumable next action.

## Entry conditions and evidence

Entry requires one validated Stage 1 transaction, its receipt chain, resolved
repository and baseline bindings, and the applicable downstream authority
state. Each lifecycle transition emits evidence-backed receipts and remains
subject to reconciliation before the next transition is accepted.

## Canonical command path

`submit`, `execute-mission start`, `status`, `session`, `resume`, `suspend`, `cancel`, qualification, publication preparation, synchronization, and closeout resolve the exact requested transaction through the shared reconciliation transaction before consuming derived runtime state. No command resubmits a WOP or creates authority.

## Recovery and closeout

Reconciliation acquires a transaction-scoped lock, discovers projections, classifies missing/partial/stale/duplicate/divergent/corrupt state, prepares and validates all writes, atomically promotes them, verifies the result, and emits a sealed reconciliation receipt. Interrupted work is resumed from the durable Stage 1 checkpoint or rolled back. Qualification, publication, EOS synchronization, and closeout remain gated by their receipts and parity checks.
