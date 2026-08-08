# Monitoring and Interruption Qualification

Monitoring owner: `RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN`.

Monitoring state is exposed as `NOT_STARTED`, `CHECKPOINTED`, `INTERRUPTED`,
or `HISTORICAL`. Provider, session, process, and heartbeat state cannot create
a mission transition.

Covered failure classifications include provider/Codex process death,
heartbeat expiry, an unbound process, a session without a process,
mutation-before-receipt and receipt-before-mutation ordering, stale
checkpoints, and historical/reconciled non-reuse. The real lifecycle mission
had no execution, provider, session, monitoring, checkpoint, or evidence
records. All failure scenarios used disposable test runtimes.
