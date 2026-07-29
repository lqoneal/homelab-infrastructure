# OA-13 Implementation Procedure

Implement only the work necessary to satisfy: Prove deterministic creation of a dispatch candidate without beginning execution.

Follow package preflight, preserve historical evidence, execute the specified positive/negative/replay/recovery tests, capture append-only evidence, reconcile affected records, publish only where repository procedures permit, then set `AWAITING_OPERATOR_VERIFICATION`. Do not record acceptance or begin the next gate.
