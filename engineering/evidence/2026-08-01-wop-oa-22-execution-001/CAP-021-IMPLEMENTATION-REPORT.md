# CAP-021 Implementation Report

## Scope

Implemented `ZEUS-OA-CAP-021 — Corrective-Work Authorization` as a bounded,
fail-closed authorization boundary. The implementation validates mission, WOP,
repository, baseline, authority, operator, lease, expiry, and explicit scope
bindings. Durable receipts use canonical digests and atomic replacement.

The implementation stops at authorization. It does not generate, queue, or
execute corrective work; those effects remain the separately controlled
`ZEUS-OA-CAP-022` outcome.

## Implementation

`scripts/lib/emp/corrective_work_authorization.py`

The module provides deterministic request creation, operator decision receipts,
binding validation, bounded scope validation, idempotent durable persistence,
tamper detection, expiry rejection, and restart recovery.
