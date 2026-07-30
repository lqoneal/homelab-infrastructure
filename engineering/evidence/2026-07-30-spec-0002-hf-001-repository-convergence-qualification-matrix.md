# SPEC-0002 HF-001 Repository Convergence Qualification Matrix

Date: 2026-07-30

Repository: `/data/engineering/repositories/homelab`

HEAD: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`

Branch/upstream: `main` / `origin/main`, ahead 2, behind 0

Repository determination: `NOT CONVERGED`

This is an observational direct non-EWO qualification. It performs no
cleanup, deletion, staging, commit, publication, synchronization, or
promotion.

## Criterion matrix

| Criterion | Determination | Objective evidence | Required next disposition |
|---|---|---|---|
| AQR-RCQ-001 Inventory completeness | PASS | complete file-level porcelain inventory and status cardinality at exact cutoff | regenerate after any working-tree change |
| AQR-RCQ-002 Classification completeness | PASS | every path has content class, reconciliation state, risk, owner route, and required treatment | owner confirmation remains required; uncertainty is explicit |
| AQR-RCQ-003 Controlled-document reconciliation | BLOCKED | this architecture group and DOC-0001 reconcile; other pre-existing changed controlled records coexist | owners bind exact revision groups and publication treatment |
| AQR-RCQ-004 Evidence reconciliation | BLOCKED | untracked central, WOP-local, Runtime, review, and archive evidence spans multiple subjects | producers verify subject, provenance, retention, and candidate membership |
| AQR-RCQ-005 Registry and state reconciliation | BLOCKED | Project State, Work Registry, mission/WOP, Progressive Runtime, decision, evidence, and projection records coexist | declared owners compare sources/projections and record direction |
| AQR-RCQ-006 Cross-document consistency | BLOCKED | structural validation passes; repository-wide semantic consistency is not proven across all concurrent groups | validate after grouping and owner reconciliation |
| AQR-RCQ-007 Artifact disposition safety | PASS | generated/temporary, archive/history, superseded-name, duplicate/compatibility-candidate, and unknown classes are explicit | preserve until consumer and retention evidence authorizes disposition |
| AQR-RCQ-008 Backlog completeness | PASS | prioritized backlog covers every blocked/failed class | execute only under separate authority |
| AQR-RCQ-009 Clean candidate boundary | FAIL | tracked and untracked deviations remain intermixed | isolate exact include/exclude groups and reach zero unexplained deviation |
| AQR-RCQ-010 Reconstruction readiness | FAIL | candidate is mutable and Pending persistence | establish immutable locator and clean-checkout reproduction |

## Inventory cardinality

| Status | Count |
|---|---:|
| Staged paths | 0 |
| Tracked modifications | 37 |
| Tracked deletions | 0 |
| Tracked renames/copies | 0 |
| Other tracked states | 0 |
| File-level untracked artifacts | 398 |
| Total deviations | 435 |

The complete path inventory is:

`engineering/evidence/2026-07-30-spec-0002-hf-001-repository-convergence-inventory.md`

## Controlled-document status

- ARCH-0001 Draft 1.6 and ADR-0001 Draft 1.3 are unchanged.
- SPEC-0002 Draft 1.3 and AQR-0001 Draft 1.1 form the current successor
  architecture qualification group.
- DOC-0001 Draft-independent Active index metadata advances to Version 2.74
  to record those Draft revisions without approving them.
- General controlled-document structure validates.
- Other pre-existing modified controlled records are not assigned to this
  architecture group and require their information owners to reconcile them.

## Evidence status

- architecture reconciliation evidence created by this work is grouped and
  cross-referenced;
- historical convergence archive content remains archival evidence;
- numerous other central, WOP-local, and Runtime evidence artifacts are
  untracked and cannot be promoted, discarded, or merged by path/name alone;
  and
- evidence reconciliation remains blocked until subject, provenance,
  retention, and exact candidate boundaries are owner-confirmed.

## Registry and state status

- Project State and Work Registry are tracked modifications outside this
  documentation scope;
- Progressive Runtime state and accepted/superseded decision artifacts are
  present;
- mission-contract, activation-request, execution-mission, WOP, publication,
  and EOS-related candidates coexist; and
- this qualification identifies the overlap but does not select authority,
  reverse-synchronize, or reconcile any state.

## Qualification conclusion

The repository has a complete observational inventory and an actionable
backlog, but its controlled, evidence, registry, state, implementation, and
publication groups are not yet owner-isolated. It is therefore
`NOT CONVERGED`, and no Active Baseline recommendation is permitted.
