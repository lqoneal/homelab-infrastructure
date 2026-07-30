# Execution Order

1. Gate A — inventory roots, state, writers, consumers, divergence, and
   recovery; freeze by control design where external mutation is unavailable.
2. Gate B — implement ownership, precedence, layer API, and terminal-emitter
   contracts.
3. Gate C — reconcile REAC, receipt, index, authority-input, and EWI decision
   schemas with cross-type rejection.
4. Gate D — implement canonical-root and one-way projection controls; prepare
   external OA-tree quarantine without deleting it.
5. Gate E — implement ARS REAC production/validation, PMA narrowing, EWI
   orchestration, shadow-only compatibility, and read-only preflight.
6. Gate F — qualify in isolated repositories with deterministic inputs.
7. Gate G — run read-only preflight and explicitly non-dispatching EWI
   qualification; reconcile without OA transition.

Each gate follows: verify condition, capture pre-state, define rollback, apply
the smallest change, run focused negatives and positives, capture post-state,
reconcile affected records, second-window verify, checkpoint.

