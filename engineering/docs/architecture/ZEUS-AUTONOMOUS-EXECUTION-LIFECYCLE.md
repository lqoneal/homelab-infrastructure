# Zeus Autonomous Execution Lifecycle

Submission hands Zeus an immutable Stage 1 transaction and its receipt chain. The autonomous controller owns derived orchestration from that point until closeout, while Engineering Governance remains the authority source.

The controller is a reconciliation layer over Stage 1, runtime reconciliation, admission supersession, canonical mission activation, EOS validation, and closeout. It does not create authority, rewrite receipts, resubmit a WOP, or approve policy-gated publication.

Every command resolves the exact transaction, computes a deterministic plan, records a receipt-backed snapshot, and either applies lawful derived repairs or exposes a blocker and next action. Missing or stale projections are repairable; conflicting immutable identities fail closed.
