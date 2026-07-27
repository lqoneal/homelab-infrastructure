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
| Owner | PMCT runtime owns completed-run values; repository engineering owns only the committed schema/baseline form |
| Authoritative runtime state | Yes, for PMCT result metadata only |
| Publication evidence | No; the sealed run directory and signed authority publication are the evidence bindings |
| Operational cache | No; next-action and gate lifecycle consume it |
| Controlled engineering evidence | The working file is an authoritative runtime ledger; the sealed run, not a ledger commit, is durable evidence |
| Repository identity participant | The committed ledger participates in Git identity; a later authenticated run delta does not redefine HEAD |
| Clean-worktree participant | Yes; it must be clean or exactly reconstructable as the sole unstaged current-run delta |
| Publication input/output | The schema/baseline form is a versioned input; current-run values are mutable runtime output and are not publication material |

## Selected model

`VERSIONED_BASELINE_PLUS_AUTHENTICATED_RUNTIME_RECONCILIATION`

The current `last_run_id`, `updated_at`, result, and gate values are not
committed merely to obtain cleanliness. They remain an unstaged authenticated
runtime reconciliation. A commit is appropriate only for an intentional schema
or controlled baseline migration, never for routine PMCT execution. Therefore
the live `PMCT-20260727T052115Z-6358c02c2fa6` delta is explicitly excluded
from the P2-029 corrective commit.

Gate approval reconstructs the expected working ledger from:

1. the committed capability-state blob;
2. the selected PMCT result and reasons;
3. the selected run manifest identity and completion time;
4. the existing PMCT state-transition algorithm.

Authority activation is also a consumer of this policy. In the publication-gap
phase, the PMCT run necessarily observes the predecessor publication while
binding its implementation baseline to the candidate HEAD. Activation accepts
only that exact sealed reconstruction, verifies the predecessor binding, and
still rejects every other tracked or staged change.
It then requires structural equality with the working file. Git porcelain must
contain only that unstaged path. This keeps arbitrary tracked modifications,
staged content, evidence tampering, stale runs, publication mismatches, and
repository-identity mismatches fail-closed.

## Publication impact

Authority publication semantics and trust are unchanged. The corrective
implementation itself requires normal commit and successor baseline
publication before production use.
