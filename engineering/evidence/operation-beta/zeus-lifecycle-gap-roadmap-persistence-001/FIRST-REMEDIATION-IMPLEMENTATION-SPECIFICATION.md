# First Remediation Implementation Specification

## Objective

Implement a canonical, receipt-backed, read-only mission lifecycle resolver
that discovers P2/P3/P4 state consistently and derives one deterministic next
authorized action. Preserve existing source bytes, identities, historical
receipts, and explicit legacy compatibility.

## Scope

Included: `GAP-001`, `GAP-006`.

Excluded: `GAP-002` transition mutation, provider/session dispatch, execution,
monitoring, recovery, evidence qualification, publication, EOS
synchronization, closeout, CAGF-01, and lifecycle admission.

## Expected implementation boundary

Likely affected runtime areas (confirm before mutation):

- `scripts/lib/emp/canonical_runtime_mission.py`
- `scripts/lib/emp/mission_verification_controller.py`
- `scripts/zeus` mission read-only command surfaces
- shared receipt/projection helpers discovered during implementation

No schema change is expected unless an existing receipt contract cannot
represent the already-persisted identity without ambiguity. Any schema change
must be separately justified and tested. Controlled documentation should be
updated only where the current command contract is made truthful.

## Required behavior

1. Resolve the mission from authoritative P2/P3/P4 receipt inputs rather than
   a selected runtime root alone.
2. Preserve and expose mission ID, WOP ID, submission ID, source digest,
   lifecycle state, authority, blockers, and next action.
3. Return the same result for exact replay and redundant repository-resolution
   inputs.
4. Fail closed for zero candidates, multiple candidates, identity conflict,
   invalid WOP/gate, missing receipt, stale digest, and terminal-state/action
   contradiction.
5. Make older verification/projection views consume or explicitly label the
   canonical resolver; no second transition authority is introduced.
6. Preserve legacy and historical records as read-only compatibility data.

## Qualification

Positive: current P2 target discovery, mission-only/WOP-only/tuple resolution,
snapshot, state, authority, blockers, next action, exact replay.

Negative: zero candidate, ambiguity, conflicting mission/WOP identity, invalid
gate/WOP, missing receipt, stale digest, terminal mission exposing executable
action, historical alias resolution.

Replay: repeated resolution and equivalent invocation produce one canonical
identity and no mutation or duplicate receipt.

## Completion evidence

- focused unit and component tests;
- native command transcript for show/state/authority/blockers/next/snapshot;
- receipt and digest verification;
- negative/fail-closed test output;
- exact diff and worktree-preservation report;
- no lifecycle admission or execution side effect.

## Stop and rollback boundary

Stop at qualified read-only resolution. If identity or receipt ownership is
ambiguous, stop fail-closed and return a design blocker. Rollback consists of
excluding the unqualified candidate from publication; historical records and
the parent mission state remain unchanged.
