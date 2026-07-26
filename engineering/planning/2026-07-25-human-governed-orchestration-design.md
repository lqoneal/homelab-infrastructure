# Human-Governed Orchestration Design

Mission N adds deterministic coordination above existing EMP services. An
Admission Record is the sole queue entry credential. Eligibility evaluates
admission, approvals, dependencies, repository and baseline identity,
resources, blockers, and state. Selection is disabled until an operator has
configured a named policy.

The configured policy orders eligible missions by descending priority, staging
order, queue timestamp, and mission identity. Selection emits an immutable
checksum-protected Selection Decision Record explaining every eligible and
rejected candidate. It creates a pending approval request but grants nothing.

Exactly `APPROVE` and `DECLINE` are accepted. Approval produces a handoff to
the existing Engineering Work Initiation interface; it does not bypass Zeus
authorization or dispatch directly. Decline remains non-authorizing. Existing
EMP lifecycle, dispatch, oversight, qualification, reconciliation, and resume
services retain their business logic.

`scripts/zeus` is a minimal deterministic adapter. It exposes status,
submission, mission list/select/show, approve/decline, execution status,
evidence/qualification/completion lookup, and resume. Monitoring lookup
commands are explicitly delegated to the corresponding existing EMP service.

No natural-language reasoning, WOP generation, automatic planning, automatic
approval, execution, or dispatch capability exists in this layer.
