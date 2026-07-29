# OA-24 Implementation Procedure

Implement only the work necessary to satisfy: Prove reconstruction from durable state and continuation from the first incomplete operation.

Follow package preflight, preserve historical evidence, execute the specified positive/negative/replay/recovery tests, capture append-only evidence, reconcile affected records, publish only where repository procedures permit, then set `AWAITING_OPERATOR_VERIFICATION`. Do not record acceptance or begin the next gate.
