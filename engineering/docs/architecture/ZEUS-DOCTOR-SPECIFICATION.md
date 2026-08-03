# Zeus Doctor Specification

`zeus doctor` is a read-only readiness projection. It reports repository
identity and cleanliness, deterministic runtime selection, Registry presence,
Development authority, controller domains, and the next authorized action.
It never initializes a runtime or synchronizes external state. A rejected
runtime includes the candidate and corrective action; a passing report points
to `zeus submit <SOURCE>`.

Doctor classifications are `READY`, `READY_FOR_REVIEW`,
`READY_FOR_PUBLICATION`, `BLOCKED`, and `FAIL`. On an unpublished recovery
branch with repository, runtime, Registry, authority, controller, and WOP
checks passing, the result is `READY_FOR_REVIEW`; EOS and synchronization are
reported as `DEFERRED`, publication is blocked only by the branch boundary,
and the next action is review and publication followed by EOS synchronization.

`zeus platform verify` is a separate read-only integrated consistency check.
It consumes the same repository and runtime projections, reports the Doctor
classification, and never performs adoption, initialization, packaging,
submission, or synchronization.

When an unbound but verifiable legacy runtime is present, the runtime check is
`BLOCKED` with reason `LEGACY_RUNTIME_REQUIRES_ADOPTION` and exact next action
`zeus runtime adopt`. Doctor never performs adoption implicitly.
