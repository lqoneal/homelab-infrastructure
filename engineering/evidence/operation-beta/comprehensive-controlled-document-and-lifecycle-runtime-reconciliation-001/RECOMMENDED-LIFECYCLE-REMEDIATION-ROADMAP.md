# Recommended Lifecycle Remediation Roadmap

1. Before admission: define the canonical receipt/identity resolver and make native mission discovery expose P2/P3 state consistently. Prove duplicate, ambiguity, conflict, and replay behavior.
2. Before dispatch: reconcile Stage 1, P3, P4, provider qualification, launch, and session receipts. Require real execution-session identity for `EXECUTION_STARTED`.
3. Before mission work: unify process/session liveness, monitoring, checkpoint, interruption, and resume semantics; prove failure ordering.
4. Before qualification: bind evidence manifests and requirement traceability to independently corroborated mission-work receipts.
5. Before publication: isolate candidate hunks, create mission-bound publication/EOS receipts, and fail closed on repository/EOS divergence.
6. Before closeout: retire duplicate terminal paths to compatibility-only and prove one terminal predicate with `NEXT_AUTHORIZED_ACTION=NONE`.
7. Finish with a real filesystem/Git/EOS/provider end-to-end qualification mission; use no historical or simulated receipt as proof of completion.

Runtime remediation is recommended only and was not implemented here.

