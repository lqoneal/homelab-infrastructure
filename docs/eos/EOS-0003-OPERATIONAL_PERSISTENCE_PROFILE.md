---
document_id: EOS-0003
title: EOS Operational Persistence Profile
version: 1.4
status: Draft
owner: Homelab Infrastructure
created: 2026-07-13
last_updated: 2026-07-28
phase: Repository–EOS State Integration
classification: EOS Operational Record
predecessor_revision: EOS-0003@1.3
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering State Freshness Standard Implementation
approval_date: null
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: governed_by
    target: EOS-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: STD-0004
  - type: related_to
    target: PROJ-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - eos
  - operational-state
  - persistence
  - checkpoint
  - mission-0
---

# EOS Operational Persistence Profile

## Purpose

This operational profile records the persistence treatment implemented by the Engineering Platform for repository-authoritative EOS projections, runtime views, checkpoint selection, retention configuration, and checkpoint evidence.

It applies the existing EOS architecture and Engineering Document Persistence Standard. It introduces no governance authority and does not change the controlled-document persistence model.

---

# Persistence Model

| Record | Source of Truth | Persistence Policy | Regeneration | Synchronization | Repository Publication |
| ------ | --------------- | ------------------ | ------------ | --------------- | ---------------------- |
| `EOS-ID.md` | Repository identity and canonical locator | Deterministic derived projection under `/data/engineering/eos/state` | Fully regenerable with `engctl eos synchronize` | Repository to EOS only; exact-byte drift is replaced automatically | Not published and never an independent authority |
| `EOS-STATE.md` | `PROJ-0001`, Work Registry revision, Engineering Execution Interface schema, and repository identity | Deterministic derived projection under `/data/engineering/eos/state` | Fully regenerable with `engctl eos synchronize` | Repository to EOS only; exact-byte drift is replaced automatically | Not published and never an independent engineering-state authority |
| `EOS-MANIFEST.md` | Repository–EOS Authority Matrix and exact canonical-source bytes | Deterministic digest manifest under `/data/engineering/eos/state` | Fully regenerable with `engctl eos synchronize` | Repository to EOS only; validation compares exact source and projection digests | Not published; records synchronization evidence only |
| `operational-state.json` | The referenced project state, projected EOS state, active checkpoint, and observed Git state | Atomic derived runtime view under `/data/engineering/eos/runtime` | Fully regenerable with `engctl eos refresh` | Refresh after repository publication, synchronization, checkpoint restoration, or material repository-state change | Not published; repository records may cite its qualification result |
| `repositories.tsv` | Registered infrastructure facts plus observed directories and Git repositories | Atomic derived inventory view under `/data/engineering/eos/runtime` | Fully regenerable with `engctl repository refresh` or `engctl eos refresh` | Refresh when repository presence or Git state changes | Not published; factual repository inventory remains controlled by `INF-0001` |
| `ACTIVE-CHECKPOINT` | The operator-selected current resume checkpoint | Single-line mutable operational pointer under `/data/engineering/eos/state` | May fall back to the latest checkpoint, but a deliberate historical selection cannot be inferred after loss | Update atomically through `engctl checkpoint restore`; the target must resolve inside the checkpoint store | Not published; the selected closeout checkpoint is summarized in project and EOS state |
| `CHECKPOINT-RETENTION` | The configured recent-set size | Single-line mutable operational configuration under `/data/engineering/eos/state`; valid range is 1 through 1000 | Defaults to 10 when absent, but the previously selected value cannot be inferred after loss | Update atomically through `engctl checkpoint retention`; validation rejects malformed persisted values | Not published; the append-only preservation rule is documented here |
| Checkpoint metadata | The checkpoint file captured at the time of the engineering event; canonical identity is the recorded project, repository root, and commit tuple | Append-only operational evidence under `/data/engineering/eos/checkpoints`; overwrite and deletion are prohibited | Historical working-tree context is not fully regenerable and shall be backed up | Applicable commits must resolve through strict commit-object verification in their recorded repository; a valid checkpoint for another selected repository is `not applicable` | Checkpoint files remain in EOS; material publication checkpoints are summarized in `PROJ-0001` and milestone records |

---

# Durability and Recovery

The EOS state and checkpoint directories are durable operational data and shall be included in Engineering Workspace backup and recovery operations. The runtime directory is a cache and may be rebuilt after recovery.

Recovery and synchronization order is:

1. restore or discover project repositories;
2. restore append-only checkpoint metadata and runtime configuration when
   available;
3. run `engctl eos synchronize` to regenerate EOS projections;
4. verify `ACTIVE-CHECKPOINT` and `CHECKPOINT-RETENTION`;
5. run `engctl eos persistence` and `engctl validate`.

No derived EOS projection or runtime view may override a controlled record,
Project State, Work Registry record, execution-interface binding, observed
repository fact, or checkpoint record. Independently authored EOS engineering
state is obsolete and prohibited.

# Repository–EOS Synchronization

The Repository–EOS Authority Matrix at
`engineering/eos/repository-eos-authority.yaml` assigns one classification,
owner, direction, and lifecycle to every integrated record.

Synchronization is one-way from repository authority to EOS derived
projections. It is version-aware, idempotent, resumable, and interruption-safe.
Temporary sibling files are fully rendered and flushed before atomic
replacement. Unsupported schemas and missing or ambiguous sources fail before
mutation.

Outside a declared publication sequence, derived and cache drift may be
repaired automatically only through an invocation carrying the established
operational synchronization authority. Runtime checkpoint records are
validated and preserved. Any attempted EOS-to-repository authority flow fails
closed.

A repository commit or publication does not automatically synchronize EOS.
Publication and synchronization are distinct authorized operations. The
publication procedure shall declare its Initial Validation, Publication,
Synchronization, and Final Validation Boundaries before execution. Until the
declared Synchronization Boundary is reached, an exact comparison failure
caused solely by an advancing authorized repository publication is
`EXPECTED_PUBLICATION_DRIFT`; it is not an EOS failure and shall not trigger
automatic repair.

The projection terms are:

- working-tree projection: the render implied by current working-tree sources;
- committed projection: the render implied by the selected local commit;
- published projection: the render implied by the completed published
  repository baseline; and
- synchronized EOS projection: the bytes persisted in EOS by a separately
  authorized synchronization and verified against its selected baseline.

Only an operator or automation identity holding explicit EOS synchronization
authority may invoke `engctl eos synchronize`. Publication, commit, push,
repository write, or validation authority does not imply that authority.
Required prerequisites and post-synchronization checks are defined by
`engineering/operations/repository-eos-synchronization.md` and PROC-0005.

# Engineering State Freshness

STD-0004 governs freshness. Before checkpoint creation, session termination,
handoff, sprint or phase completion, and any resume that would otherwise use
obsolete state, the authoritative Engineering State shall be reconciled. EOS
runtime views shall be refreshed only after their authoritative sources are
current.

The active checkpoint is a resume aid and historical operational record, not
the owner of current project truth. When it conflicts with a newer reconciled
Project State, the Project State prevails, EOS shall report the conflict, and
implementation resume remains blocked until reconciliation and validation
complete. A new checkpoint shall identify the reconciled boundary and source
Project State.

The checkpoint pointer remains global. Resume and synchronization views shall
evaluate its checkpoint identity against the selected project repository. When
the recorded project and canonical repository root consistently identify a
different repository, the checkpoint is `not applicable` to the selected
project and shall not be compared with that project's HEAD. When applicable,
the recorded commit shall be verified as an existing commit object before an
aligned or drifted result is produced. Project State, Sprint State, accepted
milestone evidence, and live repository facts retain their established
precedence regardless of checkpoint applicability.

---

# Qualification Control

`engctl eos persistence` validates:

- runtime-view schemas and current repository/checkpoint synchronization;
- the repository-inventory schema;
- the single-line active-checkpoint pointer and its target;
- the persisted retention setting without silently accepting a fallback; and
- append-only checkpoint metadata and recorded Git commit resolution.

The aggregate Engineering Platform validator invokes this control.

The integrated validator executes repository validation, synchronization
validation, EOS runtime validation, and integrated platform validation in that
order. Outside a declared publication sequence, resume may perform
synchronization under its established operational authority and then execute
the same verification chain before rendering mission context. A publication
boundary uses the read-only validation route and shall not use resume to repair
expected drift.

---

# Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-13 | Established the Mission 0 closeout persistence treatment for EOS runtime and checkpoint records. |
| 1.1 | 2026-07-15 | Applied STD-0004 freshness, authoritative-state precedence, reconciliation-before-checkpoint, and resume-conflict requirements. |
| 1.2 | 2026-07-15 | Defined checkpoint identity, selected-repository applicability, strict commit verification, and not-applicable multi-repository resume behavior. |
| 1.3 | 2026-07-28 | Established repository-authoritative deterministic EOS projections, the authority matrix, one-way atomic synchronization, layered validation, and integrated resume while retaining checkpoints as runtime evidence. |
| 1.4 | 2026-07-29 | Separated repository publication from explicitly authorized EOS synchronization; defined projection semantics, publication synchronization boundaries, and expected intermediate publication drift. |
