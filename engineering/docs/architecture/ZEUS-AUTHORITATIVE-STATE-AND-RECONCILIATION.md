# Zeus Authoritative State and Reconciliation

## Precedence

1. Immutable Stage 1 transaction and receipt chain.
2. Canonical WOP package and immutable manifest.
3. Durable admission and supersession lineage.
4. Durable execution projection bound to the admission and Stage 1 transaction.
5. Provider and dispatch receipts.
6. Native session, gate checkpoints, qualification, publication, synchronization, and closeout records.

Paths and filenames are discovery hints, not authority. A requested transaction is matched by exact semantic identity. Package, source, submission, authority, provider, dispatch, repository, and transaction mismatches fail closed. Equivalent derived records are reused; missing or partial projections are repaired; stale derived bindings are reconciled; non-equivalent immutable divergence is never selected silently.

## Atomic reconciliation

The shared reconciliation transaction locks by Stage 1 transaction, discovers all candidate projections, computes a conflict classification, prepares admission and execution writes, validates their digests and bindings, atomically promotes both files with rollback, verifies persisted state, and emits an idempotent reconciliation receipt. `submit_development()` invokes this transaction before returning a successful dispatched response, and replay invokes it again without creating lifecycle identities.

## Operator-visible evidence

Zeus status and session output expose the transaction, canonical execution identity and operands, admission, execution, reconciliation classification, blockers, and next action. The operator workflow remains `zeus submit`, `zeus resume`, and `zeus stop`; no repair or authority command is added.
