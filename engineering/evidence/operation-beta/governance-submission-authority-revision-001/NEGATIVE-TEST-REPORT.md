# Negative-Test Report

The managed-controller tests assert that handoff metadata is validated rather
than authoritative, prose cannot create authority, ambiguity and contradiction
fail closed, admission is required, historical managed sessions are preserved
and not reused, duplicate compatible sessions block, and invocation does not
remove downstream protected approvals. The governance tests continue to cover
malformed packages, repository and baseline mismatch, identity mismatch,
provenance/digest mismatch, admission prerequisites, protected effects, and
idempotent replay.

Managed-controller and semantic negative/positive qualification: 19/19 passed.
The active-tree recovery negative remains environmental; its clean isolated
qualification is recorded as 13/13 PASS. No failure was suppressed and no
protected lifecycle transition was invoked.
