# Synchronization Execution Model

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

Synchronization starts on a published source revision, an explicit regenerate request, a scheduled reconciliation checkpoint, or recovery replay. The source event carries a unique idempotency key, source manifest, dependency version set, target contract, and correlation identifier.

1. Resolve and validate the source manifest, owner, schema, qualification/adoption status, and target contract.
2. Resolve dependencies in topological order; reject cycles, unavailable predecessors, and incompatible versions before target execution.
3. Create or resume the target projection transaction using the idempotency key. The target write is atomic with its receipt/checkpoint; source data is never in the transaction.
4. Verify target digest, provenance, freshness, and expected dependency set; mark complete only after the verification receipt is durable.
5. On retryable failure, retry with bounded policy using the same key. On non-retryable failure, quarantine the target, emit a discrepancy, and do not publish it.
6. Reconciliation compares source and target manifests/digests, rebuilds the target when possible, and closes only with a matching completion receipt.

Completion is therefore deterministic: one source revision, one target contract, one idempotency key, a verified target digest, and a durable receipt. EENS records failure events; EOS checkpoints target state; neither may alter the source owner’s fact.
