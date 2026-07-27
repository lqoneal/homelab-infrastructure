# P2-029 PMCT Runtime-State Architecture Analysis

## Finding

The prior contract was internally inconsistent. The PMCT Contract called
`engineering/runtime/pmct/capability-state.yaml` authoritative controlled PMCT
metadata and required each completed run to update it. Gate approval separately
required an entirely clean tracked worktree. Both requirements were explicit,
so the file could neither remain dirty nor be committed without changing HEAD
and invalidating its own PMCT binding.

## Ownership and role

| Question | Finding |
| --- | --- |
| Owner | PMCT runtime owns completed-run reconciliation; repository review owns committed baseline reconciliation |
| Authoritative runtime state | Yes, for PMCT result metadata only |
| Publication evidence | No; the sealed run directory and signed authority publication are the evidence bindings |
| Operational cache | No; next-action and gate lifecycle consume it |
| Controlled engineering evidence | It is a controlled ledger, while each run remains immutable evidence |
| Repository identity participant | The committed ledger participates in Git identity; a later authenticated run delta does not redefine HEAD |
| Clean-worktree participant | Yes; it must be clean or exactly reconstructable as the sole unstaged current-run delta |
| Publication input/output | The committed baseline is an input; the current-run reconciliation is post-publication output |

## Selected model

`VERSIONED_BASELINE_PLUS_AUTHENTICATED_RUNTIME_RECONCILIATION`

Gate approval reconstructs the expected working ledger from:

1. the committed capability-state blob;
2. the selected PMCT result and reasons;
3. the selected run manifest identity and completion time;
4. the existing PMCT state-transition algorithm.

It then requires structural equality with the working file. Git porcelain must
contain only that unstaged path. This keeps arbitrary tracked modifications,
staged content, evidence tampering, stale runs, publication mismatches, and
repository-identity mismatches fail-closed.

## Publication impact

Authority publication semantics and trust are unchanged. The corrective
implementation itself requires normal commit and successor baseline
publication before production use.
