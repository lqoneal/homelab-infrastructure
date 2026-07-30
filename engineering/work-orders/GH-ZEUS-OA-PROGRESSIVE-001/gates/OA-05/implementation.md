# OA-05 Implementation Procedure

Implement only the work necessary to satisfy: Prove candidate missions are staged with stable identity, objective, scope, dependencies, priority, and state.

Use the production `zeus submit`, `zeus list`, and `zeus show` interfaces and
the owning Stage 1 runtime. The persisted staged contract must bind mission and
WOP identity, objective, scope, normalized dependencies, priority, candidate
state, and its digest. Missing, malformed, stale, mismatched, unauthorized, or
incomplete input must create no staged candidate or protected execution effect.

Follow package preflight, preserve historical evidence, execute the specified
positive, negative, replay, interruption, recovery, and cumulative tests,
capture append-only evidence, reconcile affected records, publish only where
repository procedures permit, then set `AWAITING_OPERATOR_VERIFICATION`. Do
not record acceptance or begin the next gate.
