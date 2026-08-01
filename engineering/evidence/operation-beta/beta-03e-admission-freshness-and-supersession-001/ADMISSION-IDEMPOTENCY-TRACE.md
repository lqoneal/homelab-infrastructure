# Admission Idempotency Trace

The prior admission identity was computed from an incomplete request: it had
`submission_id: null` and no repository baseline. The corrected path resolves
the active Stage 1 submission and current `HEAD` before calculating the
request digest and admission UUID.

Compatibility now includes mission, submission, WOP/revision, package and
contract authority, repository, baseline, principal, submitter, mode,
approval, lifecycle, and execution eligibility.
