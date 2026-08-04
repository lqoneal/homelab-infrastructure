# Lifecycle Trace

`resume_transaction` now follows:

1. Locate the existing transaction.
2. Hydrate derived fields from receipts.
3. Verify repository identity, clean tree, protected baselines, and receipt chain.
4. Resolve the publication receipt and verify its published baseline is an ancestor of current `main`.
5. Permit only `docs/`, `engineering/docs/`, and `engineering/evidence/` descendants after that publication.
6. Bind the recovery baseline.
7. Migrate runtime schema.
8. Restore the authority snapshot when dispatch is pending.
9. Resolve the qualified provider and execution agent.
10. Persist provider-selection and dispatch receipts and continue lifecycle.

Before the corrective, step 4 failed on `f95b691 → b500329`. After the
corrective, disposable legacy pending-dispatch fixtures completed steps 6–10
without operator lifecycle commands.
