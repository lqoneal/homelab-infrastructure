# Next Codex Handoff — Zeus Lifecycle Foundation Resolver

## Mission

Implement and qualify only the bounded read-only foundation for
`GAP-001` and `GAP-006` from
`engineering/planning/ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001.md`.

Proposed mission: `ZEUS-LIFECYCLE-FOUNDATION-CONVERGENCE-01`.

Proposed WOP: `WOP-ZEUS-LIFECYCLE-FOUNDATION-CONVERGENCE-001`.

Parent lifecycle mission:
`ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` remains
`ADMISSION_REQUESTED`; do not advance it.

## Verification-first start

Verify repository root, remote, branch, `HEAD == origin/main`, EOS parity,
empty index, dirty-path inventory, lifecycle source SHA
`460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9`, parent
mission state, and CAGF-01 non-execution. Read the source gap register, this
specification, the P2/P3/P4 receipt contracts, and current command tests.

Preserve all unrelated worktree changes. Do not reset, stash, clean,
checkout/restore, delete, stage unrelated work, publish, push, synchronize
EOS, admit, dispatch, invoke a provider, create an execution session, or
execute the parent lifecycle WOP.

## Authorized implementation scope

Implement a single canonical read-only resolver for mission discovery and
next-action calculation. Reuse existing P2/P3/P4 receipt and identity
components. The resolver must be deterministic, identity-preserving,
replay-safe, and fail closed on ambiguity/conflict/stale or missing evidence.

Potential runtime files are listed in
`FIRST-REMEDIATION-IMPLEMENTATION-SPECIFICATION.md`; confirm actual overlap
before editing. Do not implement `GAP-002` or later waves in this handoff.

## Required qualification

Run focused resolver, mission command, P2/P3/P4, authority, replay, and
negative tests. Verify native `zeus mission show`, `state`, `authority`,
`blockers`, `next`, `snapshot`, and `verify` independently expose the same
identity and state. Prove no duplicate receipts or mission identity on
replay. Record an evidence package and exact publication candidate manifest.

## Acceptance

The resolver must expose the existing target identity and
`ADMISSION_REQUESTED` without admitting or executing it. It must not claim
provider, session, execution, publication, synchronization, or closeout
state. `GAP-001` and `GAP-006` may advance only when all positive, negative,
replay, identity, and native verification proofs pass.

## Stop boundary

Stop after qualification of the resolver. Parent lifecycle state remains
`ADMISSION_REQUESTED`; `LIFECYCLE_MISSION_ADMITTED=NO`,
`LIFECYCLE_EXECUTION_STARTED=NO`, and `CAGF01_EXECUTION_STARTED=NO`.
Publication remains a separate operator-authorized transaction.
