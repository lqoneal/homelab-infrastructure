# Zeus Autonomous Execution Procedure

The operator workflow is `zeus submit <wop>`. Zeus then validates, packages, admits, dispatches, reconciles runtime, diagnoses recoverable defects, qualifies, prepares publication, requests only policy-required approvals, synchronizes EOS after publication, activates canonical mission state, and closes out.

Read-only verification may inspect mission status, blockers, next action, and snapshot. Runtime repair, registry reconciliation, package binding, replay, and interruption recovery are Zeus-owned operations and must not be performed by manual file edits or replacement submission.

## Autonomous continuation

One authorized submission is a bounded work envelope, not an implicit
single-gate stop. Zeus may continue through multiple deterministic roadmap
gates and lifecycle transactions while resolved authority, entry conditions,
qualification, and protected-operation boundaries remain valid. After every
material transition Zeus re-resolves canonical state and the successor action.
A completed gate alone does not require a new handoff.

Continuation stops for a policy-required operator or higher-authority decision,
unresolved authority, failed qualification or entry conditions, an execution
blocker, an explicit authority ceiling, a protected operation such as
publication or EOS synchronization, or terminal state. A provider session may
span bounded transitions, but it never selects successors, qualifies its own
work, or receives Zeus publication, Git, or EOS authority.
