---
document_id: EOS-0003
title: EOS Operational Persistence Profile
version: 1.1
status: Active
owner: Homelab Infrastructure
created: 2026-07-13
last_updated: 2026-07-15
phase: Mission 0.4 - Engineering Platform Persistence and Mission 0 Closeout
classification: EOS Operational Record
predecessor_revision: EOS-0003@1.0
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering State Freshness Standard Implementation
approval_date: 2026-07-15
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

This operational profile records the persistence treatment implemented by the Engineering Platform for EOS runtime views, checkpoint selection, retention configuration, and checkpoint evidence.

It applies the existing EOS architecture and Engineering Document Persistence Standard. It introduces no governance authority and does not change the controlled-document persistence model.

---

# Persistence Model

| Record | Source of Truth | Persistence Policy | Regeneration | Synchronization | Repository Publication |
| ------ | --------------- | ------------------ | ------------ | --------------- | ---------------------- |
| `operational-state.json` | The referenced project state, EOS state, active checkpoint, and observed Git state | Atomic derived runtime view under `/data/engineering/eos/runtime` | Fully regenerable with `engctl eos refresh` | Refresh after repository publication, checkpoint restoration, or material repository-state change | Not published; repository records may cite its qualification result |
| `repositories.tsv` | Registered infrastructure facts plus observed directories and Git repositories | Atomic derived inventory view under `/data/engineering/eos/runtime` | Fully regenerable with `engctl repository refresh` or `engctl eos refresh` | Refresh when repository presence or Git state changes | Not published; factual repository inventory remains controlled by `INF-0001` |
| `ACTIVE-CHECKPOINT` | The operator-selected current resume checkpoint | Single-line mutable operational pointer under `/data/engineering/eos/state` | May fall back to the latest checkpoint, but a deliberate historical selection cannot be inferred after loss | Update atomically through `engctl checkpoint restore`; the target must resolve inside the checkpoint store | Not published; the selected closeout checkpoint is summarized in project and EOS state |
| `CHECKPOINT-RETENTION` | The configured recent-set size | Single-line mutable operational configuration under `/data/engineering/eos/state`; valid range is 1 through 1000 | Defaults to 10 when absent, but the previously selected value cannot be inferred after loss | Update atomically through `engctl checkpoint retention`; validation rejects malformed persisted values | Not published; the append-only preservation rule is documented here |
| Checkpoint metadata | The checkpoint file captured at the time of the engineering event | Append-only operational evidence under `/data/engineering/eos/checkpoints`; overwrite and deletion are prohibited | Historical working-tree context is not fully regenerable and shall be backed up | Each recorded commit must resolve; the active pointer and operational view shall agree | Checkpoint files remain in EOS; material publication checkpoints are summarized in `PROJ-0001` and milestone records |

---

# Durability and Recovery

The EOS state and checkpoint directories are durable operational data and shall be included in Engineering Workspace backup and recovery operations. The runtime directory is a cache and may be rebuilt after recovery.

Recovery order is:

1. restore EOS state and append-only checkpoint metadata;
2. verify `ACTIVE-CHECKPOINT` and `CHECKPOINT-RETENTION`;
3. restore or discover project repositories;
4. run `engctl eos refresh`;
5. run `engctl eos persistence` and `engctl validate`.

No derived runtime view may override a controlled record, observed repository fact, or checkpoint record.

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

---

# Qualification Control

`engctl eos persistence` validates:

- runtime-view schemas and current repository/checkpoint synchronization;
- the repository-inventory schema;
- the single-line active-checkpoint pointer and its target;
- the persisted retention setting without silently accepting a fallback; and
- append-only checkpoint metadata and recorded Git commit resolution.

The aggregate Engineering Platform validator invokes this control.

---

# Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-13 | Established the Mission 0 closeout persistence treatment for EOS runtime and checkpoint records. |
| 1.1 | 2026-07-15 | Applied STD-0004 freshness, authoritative-state precedence, reconciliation-before-checkpoint, and resume-conflict requirements. |
