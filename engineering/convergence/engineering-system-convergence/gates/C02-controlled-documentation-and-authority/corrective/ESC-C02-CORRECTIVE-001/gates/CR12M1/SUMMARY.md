# CR12M1 — Reconcile CR12 Historical Output Contract Divergence

## Result

**COMPLETE**

## Finding

CR12's frozen contract required an artifact named
`REPLAY-RECOVERY-SPEC.yaml`.

The completed historical CR12 execution instead created and recorded
`INTERRUPTION-REPLAY-SPEC.yaml`.

This discrepancy is recorded as **C02-F-028**.

## Historical Preservation

CR12 was not reopened.

No CR12 artifact was renamed, rewritten, replaced, or corrected in place.

CR13 was also left unchanged and unexecuted.

## Semantic Evaluation

The historical CR12 replay/recovery design was evaluated against the frozen
CR12 acceptance criteria.

The historical artifact successfully defines:

- deterministic exact replay;
- fail-closed conflicting replay;
- partial transaction-state detection;
- recovery without silently inventing operator authority;
- read-only lifecycle inspection; and
- explicit recovery mutation authority.

Therefore the historical defect is a **contract/output-name divergence**, not
a semantic design failure.

## Resolution

CR12M1 created the canonical maturity-owned reconciliation artifact:

`gates/CR12M1/REPLAY-RECOVERY-RECONCILIATION.yaml`

Future consumers must use this reconciliation record while retaining
`gates/CR12/INTERRUPTION-REPLAY-SPEC.yaml` as the true historical semantic
source.

No future consumer may claim that CR12 originally produced
`REPLAY-RECOVERY-SPEC.yaml`.

## C02-F-028 Disposition

**RESOLVED BY MATURITY RECONCILIATION**

Historical filename divergence remains visible as evidence.

Historical semantics were qualified as sufficient.

## Mutation Boundary

CR12 modified: **NO**

CR13 modified: **NO**

CR13 executed: **NO**

## Next Authorized Item

**CR13 — Define CLI Contract**
