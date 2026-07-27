# Zeus Qualification Lifecycle Phases

This matrix separates implementation correctness from conditions that can only
be true after the committed repository baseline is published. A publication
gap is an expected transitional state, not an implementation PASS and not an
implementation failure.

| Qualification category | Before commit | After commit, before publication | After activation |
| --- | --- | --- | --- |
| Isolated implementation unit tests | Required PASS | Required PASS | Required PASS |
| Mission-admission fixture tests | Required PASS | Required PASS | Required PASS |
| Next-action fixture transitions | Required PASS | Required PASS | Required PASS |
| PMCT persistence with isolated current-binding state | Required PASS | Required PASS | Required PASS |
| Authority-publication fixture tests | Required PASS | Required PASS | Required PASS |
| Gate-approval current-binding fixture tests | Required PASS | Required PASS | Required PASS |
| Work Registry, controlled documents, and diff checks | Required PASS | Required PASS | Required PASS |
| Live next-action state | Observe current phase | Must report `PUBLISH_SIGNED_REPOSITORY_BASELINE` | Must report the governed post-publication action |
| Live PMCT OA-01 readiness | May be READY if baseline current | Must be `NOT_READY` while baselines differ | Must be READY before independent verification |
| Fresh production OA-01 PMCT | Not final evidence | Prohibited | Required PASS |
| Current-binding PMCT candidate count | Informational | Must be zero for the new HEAD | Must be exactly one after fresh PMCT |

Implementation qualification fails on any isolated functional regression,
integrity failure, repository-validation failure, or unexpected operational
transition. The expected publication-gap observations do not authorize
activation; signed candidate verification and the create-only publication
procedure remain mandatory.
