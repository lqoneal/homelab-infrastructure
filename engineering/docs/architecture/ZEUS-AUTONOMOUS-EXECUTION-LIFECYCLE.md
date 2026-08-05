# Zeus Autonomous Execution Lifecycle

Submission is the first lifecycle event. It hands Zeus an immutable Stage 1 transaction and its receipt chain; it does not require publication, merge, or EOS synchronization. The autonomous controller owns derived orchestration from that point until closeout, while Engineering Governance remains the authority source.

The controller is a reconciliation layer over Stage 1, runtime reconciliation, admission supersession, canonical mission activation, EOS validation, and closeout. It does not create authority, rewrite receipts, resubmit a WOP, or approve policy-gated publication.

Every command resolves the exact transaction, computes a deterministic plan, records a receipt-backed snapshot, and either applies lawful derived repairs or exposes a blocker and next action. Missing or stale projections are repairable; conflicting immutable identities fail closed.

Platform validation is lifecycle-aware. The shared repository-state classifier proves whether the checked-out state is published or a qualified prepublication candidate. Stage 2 and Stage 4 consume the same classification: candidate divergence from EOS is intentional only when EOS represents current published `main` and the candidate is clean, remote-aligned, and descended from it. Genuine drift remains fail-closed, and candidate branches cannot synchronize EOS.
