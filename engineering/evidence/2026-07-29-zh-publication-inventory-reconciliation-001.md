# ZH Publication Inventory Reconciliation 001

Date: 2026-07-29
Handoff: `ZH-PUBLICATION-INVENTORY-RECONCILIATION-001`
Disposition: `INVENTORY RECONCILED — PUBLICATION REMAINS PAUSED`

## 1. Engineering Work Initiation

| Check | Result |
| --- | --- |
| Repository identity and root | `/data/engineering/repositories/homelab` |
| Remote | `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch / HEAD | `main`; `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Upstream | `origin/main`; ahead 2, behind 0 |
| Repository health | PASS: discovery, integrity, and active branch |
| Registry validity | PASS: 85 objects; schema, hierarchy, ordering, states, deferrals, dependencies, and authority boundary |
| Publication status | Paused after PU-01A |
| PU-01 | Preserved at `a85893930e83c2a0579e465f4951499965441f11` |
| PU-01A | Preserved at `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Existing plan | `engineering/evidence/2026-07-29-zh-publication-plan-001.json` |
| Existing manifest | `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json` |
| Qualification correction | PROC-0001 1.18, PROC-0005 1.6, PROC-0006 1.4, and both required correction deliverables present |
| Index | Empty |

No publication execution, staging, commit, history rewrite, synchronization,
push, gate transition, or Operational Alpha declaration occurred.

## 2. Repository and Publication Baseline

PU-01 and PU-01A are immutable completed publication units. The former
authoritative manifest described 117 remaining paths after PU-01A. Subsequent
procedure correction, failure/recovery evidence, and this reconciliation add
11 publication candidates, producing a replacement unpublished candidate
inventory of 128 paths.

The complete path-level inventory and disposition appears in:

- `engineering/evidence/2026-07-29-zh-publication-inventory-reconciliation-001-change-matrix.md`; and
- `engineering/evidence/2026-07-29-zh-publication-plan-002-manifest.json`.

## 3. Publication Inventory

| Unit | State | Candidate paths | Objective |
| --- | --- | ---: | --- |
| PU-01 | Completed | 15 published paths | Governance baseline |
| PU-01A | Completed | 14 published paths | Corrected EOS publication protocol and Plan 001 |
| PU-01B | Planned | 11 | Qualification recovery protocol and replacement inventory |
| PU-01C | Planned | Frozen by execution handoff | Progressive Runtime Governance Baseline v1.0 |
| PU-02 | Planned | 49 | Cumulative OA-01 through OA-05 runtime |
| PU-03 | Planned | 12 | OA-01 acceptance evidence |
| PU-04 | Planned | 8 | OA-02 acceptance evidence |
| PU-05 | Planned | 7 | OA-03 acceptance evidence |
| PU-06 | Planned | 23 | OA-04 corrected acceptance chain |
| PU-07 | Planned | 10 | OA-05 staging acceptance evidence |
| PU-08 | Planned | 6 | OA-06 pending state projection |
| PU-09 | Planned | 2 | Historical working-tree reconciliation audit |

All 128 candidates captured by this reconciliation remain assigned exactly
once. PU-01C was subsequently inserted by
`ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/PU-01C`; its exact T04-T15 path and
digest boundary must be frozen by its execution handoff before staging. No
existing candidate assignment or PU-02 through PU-09 path membership changed.

## 4. Inventory Delta

The 11 paths added after the prior manifest are:

| Origin | Paths | Delta classification | Required timing |
| --- | ---: | --- | --- |
| ZH-QUALIFICATION-POLICY-CORRECTION-001 | 5 | Prerequisite publication unit | Before any recovered publication-boundary decision or PU-02 |
| ZH-PUBLICATION-EXECUTION-003 | 1 | Prerequisite publication unit | With the correction that disposes its incident |
| ZH-PUBLICATION-RECOVERY-EXECUTION-001 | 1 | Prerequisite publication unit | With the replacement inventory that resolves its blocker |
| ZH-PUBLICATION-INVENTORY-RECONCILIATION-001 | 4 | Prerequisite publication unit | As the authoritative plan, manifest, analysis, and inventory matrix |

The correction procedures cannot join PU-02 because PU-02 is an indivisible
runtime implementation unit. Deferring them until PU-09 would leave the
qualification policy and authoritative inventory unpublished while they govern
earlier units. Leaving them outside publication would prevent deterministic
recovery. They therefore form PU-01B.

## 5. Publication-Unit Reconciliation

PU-01B is a new prerequisite unit with one objective: publish the qualification
recovery protocol and its authoritative replacement inventory. Its 11 paths
are:

1. PROC-0001 Version 1.18 candidate;
2. PROC-0005 Version 1.6 candidate;
3. PROC-0006 Version 1.4 candidate;
4. ZH-PUBLICATION-EXECUTION-003 evidence;
5. ZH-QUALIFICATION-POLICY-CORRECTION-001 report;
6. ZH-QUALIFICATION-POLICY-CORRECTION-001 change matrix;
7. ZH-PUBLICATION-RECOVERY-EXECUTION-001 evidence;
8. this reconciliation report;
9. this reconciliation change matrix;
10. Publication Plan 002; and
11. Publication Plan 002 manifest.

PU-01B does not modify the content or history of PU-01A. The post-PU-01A
procedure deltas are new successor bytes assigned only to PU-01B.

## 6. Dependency Reconciliation

```text
PU-01 (completed)
  -> PU-01A (completed)
    -> PU-01B qualification recovery prerequisite
      -> Recovery Boundary
        -> PU-01C Runtime governance baseline
          -> PU-02 -> PU-03 -> PU-04 -> PU-05 -> PU-06 -> PU-07
          -> PU-08
            -> Synchronization Boundary
              -> PU-09
                -> Final Validation Boundary
                  -> Push and Remote Verification
```

Dependency changes:

- PU-01B depends on immutable PU-01A.
- PU-01C depends on PU-01B.
- PU-02 depends on PU-01C.
- PU-08 records PU-01A, PU-01B, and PU-01C among its complete prerequisite set.
- PU-03 through PU-07 and PU-09 retain their direct dependencies.
- The Synchronization Boundary remains after PU-08 and before PU-09.
- The Final Validation Boundary remains after PU-09 and before push.
- The Recovery Boundary is after PU-01B and before PU-02.
- Publication completion remains after successful push and remote
  verification.

## 7. Replacement Plan and Manifest

Replacement authoritative plan:

`engineering/evidence/2026-07-29-zh-publication-plan-002.json`

Replacement authoritative manifest:

`engineering/evidence/2026-07-29-zh-publication-plan-002-manifest.json`

The plan preserves the exact commit messages and membership of PU-02 through
PU-09. It marks PU-01 and PU-01A completed at their immutable commit locators
and adds only PU-01B and the dependency changes described above.

The manifest records every current candidate's path, Git status,
classification, publication status, authority, lifecycle, dependency,
publication unit, rationale, and SHA-256 digest. Its own SHA-256 field is null
because a file cannot contain a stable digest of itself.

## 8. Recovery Assessment

Publication may resume under a new execution handoff after this reconciliation
is accepted.

| Recovery fact | Value |
| --- | --- |
| Recovery commit | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| First executable post-PU-01A unit | PU-01B |
| First runtime publication unit after recovery | PU-01C |
| Updated unpublished candidate count | 128 |
| Ordering | PU-01B, PU-01C, PU-02, PU-03, PU-04, PU-05, PU-06, PU-07, PU-08, Synchronization Boundary, PU-09, Final Validation Boundary, push |
| Governing manifest | `2026-07-29-zh-publication-plan-002-manifest.json` |

No remaining inventory, assignment, or dependency blocker exists at this
candidate baseline. Execution authority is outside this handoff.

## 9. Validation Results

The reconciliation validation verifies:

- complete Git candidate inventory;
- exactly one publication-unit assignment for every candidate;
- zero duplicate assignments;
- zero orphaned or excluded candidate paths;
- byte-for-byte preservation of PU-02 through PU-09 membership;
- immutable PU-01 and PU-01A locators;
- acyclic dependency order;
- unchanged Synchronization and Final Validation Boundaries;
- manifest/file digest agreement for every non-self entry;
- JSON serialization;
- controlled-document integrity;
- cross-reference integrity;
- whitespace and terminology consistency; and
- empty index and unchanged HEAD.

## 10. Risks

- PU-01B contains controlled procedure corrections and must complete before
  any recovered boundary decision uses them.
- The manifest self-entry necessarily has a null digest and must be bound by
  the future immutable PU-01B commit.
- The replacement plan is authoritative only as a complete four-file
  reconciliation package; partial use would recreate inventory ambiguity.
- EOS remains intentionally unsynchronized until the boundary after PU-08.
- Any content change after validation invalidates the affected recorded digest.

## 11. Final Recommendation

Accept Publication Plan 002 and its manifest as the replacement authoritative
inventory. Keep publication paused after PU-01A. A future execution handoff
should begin with PU-01B, validate its boundary under PROC-0005 Version 1.6,
then reassess recovery before advancing to PU-02.
