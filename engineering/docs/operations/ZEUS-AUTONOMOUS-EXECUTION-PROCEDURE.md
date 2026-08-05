# Zeus Autonomous Execution Procedure

The operator workflow is `zeus submit <wop>`. Zeus then validates, packages, admits, dispatches, reconciles runtime, diagnoses recoverable defects, qualifies, prepares publication, requests only policy-required approvals, synchronizes EOS after publication, activates canonical mission state, and closes out.

Read-only verification may inspect mission status, blockers, next action, and snapshot. Runtime repair, registry reconciliation, package binding, replay, and interruption recovery are Zeus-owned operations and must not be performed by manual file edits or replacement submission.
