# ZH Publication Resume 002

Date: 2026-07-29  
Handoff: `ZH-PUBLICATION-RESUME-002`  
Disposition: `STOPPED AT BASELINE VERIFICATION — PUBLICATION NOT RESUMED`

## 1. Engineering Work Initiation

Engineering Work Initiation was limited to the mandatory read-only publication
resume stop-gate. No auto-repairing resume or qualification command was used.
No repository or EOS mutation was invoked.

| Check | Result |
| --- | --- |
| Repository root | `/data/engineering/repositories/homelab` |
| Branch | `main` |
| HEAD | `a85893930e83c2a0579e465f4951499965441f11` |
| Upstream comparison | `origin/main...HEAD`: ahead 1, behind 0 |
| Index | Empty |
| EOS comparison | `EOS-STATE.md` and `EOS-MANIFEST.md` differ; classified `EXPECTED_PUBLICATION_DRIFT` |
| Resume disposition | STOP before PU-02 because exact working-tree membership does not match PU-02 through PU-09 |

## 2. Baseline verification

| Required condition | Observed evidence | Disposition |
| --- | --- | --- |
| PU-01 commit exists | Git object type `commit`; HEAD equals required full commit | PASS |
| One commit ahead of `origin/main` | `0 1` from `git rev-list --left-right --count origin/main...HEAD` | PASS |
| No later publication unit committed | `origin/main..HEAD` contains only PU-01 | PASS |
| Empty staging area | `git diff --cached --name-only` returned no paths | PASS |
| Working tree matches approved plan | 127 changed paths observed; all 119 remaining approved paths are present, plus 8 unplanned protocol-correction paths | **FAIL** |
| EOS is expected publication drift | Read-only comparison reports only `EOS-STATE.md` and `EOS-MANIFEST.md` drift after PU-01 | PASS |

The eight paths outside approved PU-02 through PU-09 membership are:

1. `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
2. `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md`
3. `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
4. `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md`
5. `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md`
6. `engineering/evidence/2026-07-29-zh-publication-protocol-correction-001-change-matrix.md`
7. `engineering/evidence/2026-07-29-zh-publication-protocol-correction-001.md`
8. `engineering/operations/repository-eos-synchronization.md`

The first and third paths are members of completed PU-01 but now contain
post-PU-01 protocol-correction modifications. The other six paths are not
members of any approved publication unit. This resume evidence file was
created only after the stop decision as required by the handoff and is likewise
not assigned to a publication unit.

## 3. Publication sequence executed

No publication unit was executed. PU-02 was not staged or validated as an
active publication unit because the mandatory pre-publication baseline failed.
PU-03 through PU-09 were not entered.

## 4. Commit summary

| Unit | Commit | Status |
| --- | --- | --- |
| PU-01 | `a85893930e83c2a0579e465f4951499965441f11` | Preserved; completed before this handoff |
| PU-02 through PU-09 | None | Not executed |

No commit was created, amended, reset, rebased, or otherwise rewritten.

## 5. Boundary validation summary

The Initial Validation Boundary failed at exact publication-set membership.
The governing requirement is PROC-0005 Version 1.5 sections 4.1, 13, 14, and
20: establish the exact boundary, exclude unrelated paths, and stop when the
transaction set differs from the publication boundary.

Observed failure: the corrected governing documents required by this handoff
exist only as uncommitted changes outside the unchanged PU-02 through PU-09
boundaries. Executing the approved units would leave their governing protocol
unpublished, while including those changes would violate the prohibition on
modifying publication-unit membership.

Recommended recovery point: preserve HEAD at PU-01 and obtain an explicit
publication disposition for the eight protocol-correction paths plus this
resume evidence. The disposition must reconcile them without changing approved
PU-02 through PU-09 membership or messages—for example, by authorizing a
separate prerequisite protocol publication unit and then issuing a new resume
handoff. This report does not select or authorize that recovery.

## 6. Synchronization evidence

Synchronization was not performed. Read-only
`scripts/engctl eos sync-validate homelab` reported:

```text
DRIFT: /data/engineering/eos/state/EOS-STATE.md
DRIFT: /data/engineering/eos/state/EOS-MANIFEST.md
```

Because the declared Synchronization Boundary after PU-08 was not reached,
this remains `EXPECTED_PUBLICATION_DRIFT`.

## 7. Push verification

No push was attempted. Local `main` remains one commit ahead of
`origin/main`, containing PU-01 only.

## 8. Final repository state

- HEAD: `a85893930e83c2a0579e465f4951499965441f11`
- Staging area: empty
- Completed publication commits preserved: PU-01 only
- Working tree: preserved without unstage, discard, rewrite, or cleanup
- EOS state: unchanged
- Remote state: unchanged by this handoff

## 9. EOS validation disposition

`EXPECTED_PUBLICATION_DRIFT`. The result is supported by the verified PU-01
HEAD, the absence of later commits, and the fact that the Synchronization
Boundary follows PU-08. It is not a synchronization failure and creates no
authority to synchronize early.

## 10. Final recommendation

Keep publication paused at PU-01. Do not resume PU-02 until a new authority
reconciles the protocol-correction artifacts with an explicit publication
boundary while preserving the already approved PU-02 through PU-09 units.

The current handoff cannot both execute only the unchanged approved units and
publish the uncommitted procedures it requires as governing authority. Per its
conflict rule, execution stopped and the conflict was preserved rather than
reinterpreted.
