# P2-028A Qualification Ordering Analysis

## Finding

The P2-028 stop was correct under its stated ordering, but the ordering treated
three publication-dependent observations as implementation-only qualification.
Immediately after a commit, `HEAD != PUBLISHED_BASELINE` is the required
transitional condition. At that point Zeus must return
`PUBLISH_SIGNED_REPOSITORY_BASELINE`, and OA-01 must not be READY or PASS.

No Zeus operational implementation defect was found.

## Classification

| Test or category | Classification | Required phase |
| --- | --- | --- |
| Next-action fixture transition tests | Implementation-only | Before commit and after commit |
| `test_current_cli_reports_lifecycle_phase_and_does_not_modify_worktree` | Live lifecycle observation | After commit and after publication, with phase-specific result |
| PMCT state-protection fixture tests | Implementation-only | Before commit and after commit |
| `test_oa01_adapter_satisfies_current_observable_contract` | Live publication-dependent observation | After commit and after publication, with phase-specific result |
| `test_completed_run_atomically_updates_capability_state` | Implementation-only isolated persistence | Before commit and after commit |
| Fresh production `pmct run OA-01` | Publication-dependent qualification | Only after activation |
| Authority publication and gate-approval fixture tests | Implementation-only | Before commit and after commit |
| Work Registry and controlled-document validation | Repository qualification | Every repository boundary |
| WOP manifest verification | External package integrity | Every lifecycle boundary |

## Correction

- The live next-action test derives its expected action from whether the active
  published baseline equals HEAD.
- The live PMCT state-protection test requires `NOT_READY/MISMATCHED` during the
  publication gap and `READY/ABSENT` after activation.
- The atomic persistence test supplies an isolated current-binding state, so it
  tests persistence rather than inheriting production publication timing.
- `QUALIFICATION-PHASES.md` defines the sequencing contract.

Existing negative tests continue to prove that a failed mandatory assertion
cannot produce PMCT PASS. Publication signatures, candidate readiness,
create-only activation, evidence integrity, gate approval, and operator
boundaries are unchanged.
