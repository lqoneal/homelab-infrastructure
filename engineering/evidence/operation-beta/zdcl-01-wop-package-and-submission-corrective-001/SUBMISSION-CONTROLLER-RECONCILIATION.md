# Submission Controller Reconciliation

`zeus mission submit ZDCL-01` now uses the same `operational_beta.mission_state`
resolution used by `zeus mission explain ZDCL-01`. It reports complete resolved
mission metadata for both unavailable-package failures and successful package
reuse. The existing `Stage1Runtime` remains the only submission and queue
authority.

Unavailable, ambiguous, stale, or invalid package conditions return `result:
FAIL` and a nonzero exit status. Failed attempts are recorded as rejected audit
history by Stage 1 but never become active queue entries. Successful retries
reuse the existing package and Stage 1 idempotency prevents duplicate active
submissions.
