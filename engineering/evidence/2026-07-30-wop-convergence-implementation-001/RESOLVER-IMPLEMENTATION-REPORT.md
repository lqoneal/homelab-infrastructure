# Resolver Implementation Report

The resolver accepts an exact WOP identifier/revision, requested action,
correlation identifier, and optional Authority Record identifier. It validates
the EMM schema and baseline, unique entity selection, source bounds and
digests, WOP identity/baseline/lifecycle, and Authority Record applicability.
It emits only `RESOLVED`, `NOT_FOUND`, `INTEGRITY_FAILURE`, or
`PRECONDITION_FAILED` outcomes with a deterministic receipt digest.

The only production OA-01 result tested is non-authorizing:
`READY + no Authority Record → PRECONDITION_FAILED`.
