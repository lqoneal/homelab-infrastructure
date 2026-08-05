# Zeus Autonomous Execution Procedure

The operator workflow is `zeus submit <wop>`. Submission is the first lifecycle event and does not require publication. Zeus then validates, packages, admits, dispatches, reconciles runtime, diagnoses recoverable defects, qualifies, prepares publication, requests only policy-required approvals, synchronizes EOS after publication, activates canonical mission state, and closes out.

Read-only verification may inspect mission status, blockers, next action, and snapshot. Runtime repair, registry reconciliation, package binding, replay, and interruption recovery are Zeus-owned operations and must not be performed by manual file edits or replacement submission.

## Lifecycle-aware platform validation

Published `main` requires strict repository, EOS, checkpoint, and operational-state parity. A clean remote-aligned `prepublication/*` candidate is valid only when it descends from current published `main` and EOS remains aligned to that published baseline; it is reported as `UNPUBLISHED_CANDIDATE`. EOS must never be synchronized from the candidate branch. Dirty, detached, rewound, unrelated, divergent, ambiguous, or stale-EOS states fail closed.
