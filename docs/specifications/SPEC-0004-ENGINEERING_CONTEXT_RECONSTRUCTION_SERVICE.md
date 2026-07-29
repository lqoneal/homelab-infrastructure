---
document_id: SPEC-0004
title: Engineering Context Reconstruction Service
version: 1.5
status: Draft
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-28
governed_by: EOS-0001
implements:
  - EDR-0002
depends_on:
  - SPEC-0001
  - SPEC-0007
conforms_to:
  - STD-0004
---

# Engineering Context Reconstruction Service

---

# 1. Purpose

The Engineering Context Reconstruction Service (ECRS) provides the capability to reconstruct the complete engineering context of an EOS-managed activity using only Authoritative Engineering Records.

The service exists to eliminate dependence upon human memory for engineering continuity.

---

# 2. Scope

The service reconstructs engineering context for:

- EOS Program
- Engineering projects
- Architecture sprints
- Implementation sprints
- Validation activities
- Long-running engineering efforts

---

# 3. Design Objectives

The service SHALL:

- reconstruct engineering context deterministically;
- consume only Authoritative Engineering Records;
- avoid manual state reconstruction;
- support automation;
- produce consistent engineering views.

---

# 4. Inputs

The service consumes Authoritative Engineering Records, including:

- EOS documents
- Project State
- Engineering Decision Records
- Specifications
- Milestones
- Validation records
- Persisted Qualification Reports and their current Engineering State references
- Engineering checkpoints

The service SHALL NOT depend upon derived views.

When inputs disagree, the service SHALL resolve each fact to its authoritative
owner. Reconciled Project State, Sprint State, current mission records, and
accepted milestone evidence take precedence over older checkpoint content.
A checkpoint is operational evidence and shall not override a newer supported
authoritative state record.

For checkpoint applicability, the service shall treat the recorded project
identifier, canonical repository root, and commit as one checkpoint identity.
The identity applies to a selected resume target only when the recorded project
resolves to the recorded canonical root and that root is the selected project
repository. A valid checkpoint for another repository is `not applicable`; it
is not aligned, drifted, or invalid for the selected target. An applicable
checkpoint is aligned or drifted only after strict verification proves that
its recorded commit exists as a commit object in that repository. Missing,
malformed, unresolved, or internally inconsistent applicable identity is
invalid.

---

# 5. Outputs

The service produces derived engineering views, including:

- Resume reports
- Status summaries
- AI engineering briefings
- Daily engineering reports
- Program summaries
- Mission Snapshots

Outputs remain non-authoritative.

A Mission Snapshot is the standard execution and resume view. It includes
repository identity, mission, phase, authority reference, objectives,
completion criteria, lifecycle state, next action, blockers, and authoritative
source locators. `engctl execution snapshot` is its canonical controller
surface.

---

# 6. Context Model

Engineering context consists of:

- Program
- Project
- Sprint
- Current phase
- Current task
- Current checkpoint
- Governing documents
- Active decisions
- Open issues
- Documentation impact
- Validation requirements
- Next approved action

---

# 7. Reconstruction Algorithm

The service SHALL:

1. Locate the authoritative scope.
2. Load governing records.
3. Resolve engineering relationships.
4. Determine active work.
5. Resolve applicable persisted asset-qualification state and its freshness.
6. Identify blockers.
7. Determine next approved action.
8. Generate a derived engineering context view.

For a Mission Snapshot, resolution fails closed unless exactly one current
repository Mission Contract matches the requested mission.

---

# 8. Service Requirements

The service SHALL:

- produce identical output for identical inputs;
- remain implementation independent;
- support future automation;
- preserve engineering traceability;
- evaluate Engineering State freshness under STD-0004;
- expose source records and the freshness result in resume output;
- expose the active checkpoint project, repository, applicability, and
  repository-scoped synchronization result;
- report checkpoint and authoritative-state conflicts; and
- consume current persisted qualification state when available rather than
  rediscovering unchanged engineering assets;
- require rediscovery or requalification when qualification identity,
  freshness, integrity, applicability, or governing requirements do not
  resolve; and
- refuse to present a known completed or superseded objective as current.

Qualification reports and qualification-state references are authoritative
inputs only within the ownership boundaries defined by STD-0005, STD-0004, and
SPEC-0007. ECRS produces no qualification decision, does not alter an asset
record, and does not make its derived resume output authoritative. Current
resume behavior remains unchanged until separately authorized persistence and
integration work is implemented and qualified.

Resume generation is qualified for implementation only when required
authoritative state resolves, no execution-significant conflict remains, and
freshness is `CURRENT` or validly `WITHIN THRESHOLD`. An indeterminate or
`RECONCILIATION REQUIRED` result blocks implementation resume.

---

# 9. Validation

The service is compliant when it reconstructs engineering context using only Authoritative Engineering Records without requiring undocumented human knowledge.

---

# Compliance

All Resume functionality within EOS SHALL conform to this specification.
All Resume functionality shall also consume the freshness threshold,
reconciliation triggers, and source precedence established by STD-0004.

---

# Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.1 | 2026-07-15 | Integrated STD-0004 freshness, source precedence, and stale-objective rejection. |
| 1.2 | 2026-07-15 | Defined repository-aware checkpoint identity, applicability, strict commit verification, and not-applicable resume semantics. |
| 1.3 | 2026-07-19 | Recorded future consumption of persisted Qualification Reports and qualification state, with freshness and rediscovery gates, without changing current resume implementation. |
| 1.4 | 2026-07-28 | Standardized the Mission Snapshot as the repository-only execution and resume view exposed through engctl. |
