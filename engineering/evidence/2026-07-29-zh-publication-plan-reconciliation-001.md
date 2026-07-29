# ZH Publication Plan Reconciliation 001

Date: 2026-07-29  
Handoff: `ZH-PUBLICATION-PLAN-RECONCILIATION-001`  
Disposition: `PLAN RECONCILED — PUBLICATION REMAINS PAUSED`

## 1. Engineering Work Initiation

| Check | Result |
| --- | --- |
| Repository identity | `/data/engineering/repositories/homelab`; `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch / HEAD | `main`; `a85893930e83c2a0579e465f4951499965441f11` |
| Upstream | `origin/main`; ahead 1, behind 0 |
| Published units | PU-01 only |
| Index | Empty |
| Repository health | PASS: discovery, integrity, and active branch |
| Registry | PASS: revision 85, 85 objects, authority boundary valid |
| Corrected protocol | PROC-0005 1.5, PROC-0001 1.17, STD-0004 1.4, EOS-0003 1.4 present as uncommitted candidate revisions |
| EOS comparison | `EXPECTED_PUBLICATION_DRIFT`: `EOS-STATE.md` and `EOS-MANIFEST.md` differ after PU-01 |
| Publication status | Paused after PU-01 |

No staging, commit, reset, rebase, synchronization, push, gate transition, or
publication execution occurred.

## 2. Repository baseline

PU-01 is preserved at
`a85893930e83c2a0579e465f4951499965441f11`. No later publication commit
exists. The pre-reconciliation working tree contained all 119 paths assigned
to the remaining original units plus eight protocol-correction paths and the
publication-resume stop report. This reconciliation adds its two required
Markdown deliverables and one machine-readable manifest.

The reconciled candidate therefore contains 131 modified or untracked paths.
The manifest records exact SHA-256 digests for every non-self path. The
manifest's own digest is null because a self-digest is recursive.

## 3. Complete modified-path inventory

The complete path-level inventory is recorded in:

- `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-change-matrix.md`; and
- `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json`.

Every observed path records its prior assignment, recommended assignment,
governing authority, dependency chain, assignment status, Git status, and
digest. No path is unclassified.

## 4. Current publication-unit inventory

| Unit | Prior state | Paths | Reconciliation |
| --- | --- | ---: | --- |
| PU-01 | Completed | 15 | Preserve immutable commit; post-commit deltas to DOC-0001 and PROC-0001 move to PU-01A |
| PU-02 | Planned | 49 | Unchanged |
| PU-03 | Planned | 12 | Unchanged |
| PU-04 | Planned | 8 | Unchanged |
| PU-05 | Planned | 7 | Unchanged |
| PU-06 | Planned | 23 | Unchanged |
| PU-07 | Planned | 10 | Unchanged |
| PU-08 | Planned | 6 | Unchanged |
| PU-09 | Planned | 4 | Split: authoritative plan files move to PU-01A; historical inventory/report remain PU-09 |
| Unassigned correction/evidence | Unassigned | 9 before this handoff | Assigned to PU-01A |

## 5. Boundary analysis

The protocol-correction artifacts shall be a dedicated prerequisite
publication unit, `PU-01A`.

Incorporating them into PU-02 would mix controlled governance procedures with
runtime implementation and violate one-objective isolation. Incorporating them
into PU-09 would publish the governing contract only after the work it must
govern. Deferral would leave the corrected procedure unavailable as a
published prerequisite and repeat the resume conflict.

PU-01A preserves PU-01 and does not alter PU-02 through PU-08 membership or
commit messages. It combines the coordinated protocol revisions, their
correction/stop/reconciliation evidence, and the authoritative regenerated plan
and manifest because those records jointly establish one reviewable
publication-resume prerequisite.

## 6. Dependency analysis

```text
PU-01 (completed)
  -> PU-01A corrected protocol and authoritative reconciled plan
    -> PU-02 cumulative runtime
      -> PU-03 -> PU-04 -> PU-05 -> PU-06 -> PU-07
        -> PU-08 authoritative state projection
          -> Synchronization Boundary
            -> PU-09 historical planning audit
              -> Final Validation Boundary
                -> Push
```

PU-01A must precede all resumed execution. PU-02 through PU-08 retain their
existing linear dependencies. PU-09 depends on PU-08 and the successful
Synchronization Boundary; its two remaining paths are historical audit
artifacts and are independently reviewable.

## 7. Recommended publication structure

| Order | Unit | Objective | Paths | Risk |
| ---: | --- | --- | ---: | --- |
| 1 | PU-01 | Completed governance baseline | 15 | completed |
| 2 | PU-01A | Publish corrected protocol and authoritative reconciled plan | 14 | high |
| 3 | PU-02 | Cumulative OA-01 through OA-05 runtime | 49 | high |
| 4 | PU-03 | OA-01 acceptance evidence | 12 | medium |
| 5 | PU-04 | OA-02 acceptance evidence | 8 | medium |
| 6 | PU-05 | OA-03 acceptance evidence | 7 | medium |
| 7 | PU-06 | OA-04 corrected acceptance chain | 23 | high |
| 8 | PU-07 | OA-05 staging acceptance evidence | 10 | medium |
| 9 | PU-08 | OA-06 pending state projection | 6 | high |
| 10 | Synchronization Boundary | Repository-to-EOS projection | 0 repository paths | controlled |
| 11 | PU-09 | Preserve historical reconciliation audit | 2 | low |

## 8. Regenerated publication-unit assignments

The regenerated authoritative membership appears in both
`2026-07-29-zh-publication-plan-001.json` and the reconciliation manifest.
PU-02 through PU-08 are byte-for-byte membership-preserved from the prior plan.
PU-01A owns all protocol and current planning artifacts. PU-09 owns only the
historical working-tree reconciliation report and its historical inventory.

The change matrix provides the complete 131-row assignment table.

## 9. Publication manifest summary

Manifest:
`engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json`

| Metric | Value |
| --- | ---: |
| Candidate paths | 131 |
| Assigned candidate paths | 131 |
| Duplicate assignments | 0 |
| Orphaned paths | 0 |
| Publication units containing candidate paths | 9 |
| Completed historical unit | PU-01 |
| New prerequisite unit | PU-01A |
| Synchronization point | After PU-08, before PU-09 |

## 10. Validation results

| Validation | Result |
| --- | --- |
| Complete Git path inventory | PASS |
| Exactly one assignment per candidate path | PASS |
| Duplicate ownership | PASS: none |
| Orphan detection | PASS: none |
| PU-02 through PU-08 membership preservation | PASS |
| Dependency topological order | PASS |
| Commit-message preservation for PU-02 through PU-08 | PASS |
| Protocol-before-runtime ordering | PASS |
| Publication isolation | PASS |
| Manifest/file digest consistency | PASS for every non-self entry |
| JSON serialization | PASS |
| Markdown/change-matrix consistency | PASS |
| Repository health and registry validity | PASS |
| Whitespace validation | PASS |
| Index remains empty / HEAD unchanged | PASS |
| EOS state | `EXPECTED_PUBLICATION_DRIFT`; no synchronization performed |

## 11. Risks

- PU-01A is a high-authority controlled-document unit and requires the
  applicable document-owner and publication review before execution.
- The manifest self-entry cannot carry its own SHA-256 digest; it is explicitly
  null and must be verified by immutable commit identity after publication.
- PU-02 remains oversized but atomic; its original subsystem review sequence
  remains necessary.
- PU-06 retains immutable original, corrected, and supersedence evidence.
- PU-08 remains the only repository state-projection unit and must complete
  before the Synchronization Boundary.
- Any content change after this reconciliation invalidates recorded digests and
  requires re-initiation.

## 12. Final recommendation

Approve the reconciled plan for a new publication execution handoff beginning
with PU-01A. That handoff may proceed to PU-02 only after PU-01A is committed
and its controlled-document validation passes.

No additional publication-planning work is required at this baseline. The
repository is ready for a new publication execution handoff, but publication
remains paused pending explicit approval. Synchronization remains prohibited
until the declared boundary after PU-08.
