# Negative and Safety Tests

The focused convergence test proves:

1. A submitted WOP resolves without a second authority record.
2. Scope/action mismatch fails closed.
3. An explicitly failed admission fails closed.
4. An explicit WOP approval gate with no accepted approval returns
   `OPERATOR_APPROVAL_REQUIRED`.
5. Managed Codex packaging is `workspace-write` only after the execution
   safety boundary, with `read_only: false` and WOP provenance.
6. An immutable historical WOP digest remains unchanged.

Existing Codex interactive qualification also passes the intended split:
missionless operator-interactive sessions remain read-only, while
mission-bound interactive sessions retain their explicit session safety gate.
Provider qualification, identity/binding, repository baseline, lifecycle,
concurrency, replay/idempotency, and publication controls were retained.
