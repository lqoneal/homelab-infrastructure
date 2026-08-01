# OA-17 Implementation Procedure

Implement only the work necessary to satisfy: Prove controlled execution authorization immediately follows durable execution start and is identity-bound, lease-validated, receipt-backed, replay-safe, recoverable, timeout-aware, and fail closed.

Follow package preflight, preserve historical evidence, execute the specified positive/negative/replay/recovery tests, capture append-only evidence, reconcile affected records, publish only where repository procedures permit, then set `AWAITING_OPERATOR_VERIFICATION`. Do not record acceptance or begin the next gate.
