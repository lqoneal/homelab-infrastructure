---
document_id: EGR-000003
title: EWO-000020 Notification Service Authorization
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-17
last_updated: 2026-07-17
phase: Notification Service Authorization
domain: Engineering Governance
classification: Engineering Governance Resolution
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000003
approval_date: 2026-07-17
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: governed_by
    target: POL-0001
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0003
  - type: indexed_by
    target: DOC-0001
  - type: authorizes
    target: EWO-000020
  - type: related_to
    target: EWO-000019
tags:
  - engineering-governance-resolution
  - bootstrap-deadlock-correction
  - notification-service
  - work-authorization
---

# Engineering Governance Resolution

## Engineering Governance Resolution Header

Resolution: EGR-000003

Decision: Establish EWO-000020 Notification Service Authority

Owner: Engineering Governance

Status: Active

Disposition: Approved

## Purpose

Record Engineering Governance's bounded exercise of the bootstrap-deadlock
correction authority in CHAR-0001 solely to create, approve, register, publish,
and activate EWO-000020 as the successor implementation authority.

This Resolution does not authorize implementation of the Engineering
Notification Service.

## Governing Authority

CHAR-0001 establishes Engineering Governance's authority independent of
repository state, including authority to correct a repository bootstrap
deadlock and publish the authority necessary to begin controlled execution.
POL-0001 reserves approval and activation of Engineering Work Orders to
Engineering Governance. GEN-0001 requires the resulting operational authority
to be represented by controlled records. EDR-0002 preserves the separation
between Governance Authority, controlled information, and implementation
authority.

Engineering Governance approved this bounded transaction through the operator
handoff titled `Establish EWO-000020 Notification Service Authority` on
2026-07-17. The handoff is the approval act; this Resolution is its controlled,
auditable repository record.

This is a correction of a post-bootstrap authorization deadlock under
CHAR-0001. It is not a repetition of the one-time Genesis Governance Bootstrap
and does not reuse the expired EWO-000019 wrapper exception.

## Evidence Considered

The repository inventory ends at EWO-000019 and contains no EWO-000020.
Project State, Work Registry revision 23, EOS state, and the active checkpoint
agree that EWO-000019 is completed, no Homelab work is active or planned, and
notification Stage 2 and Stage 3 remain deferred. EWO-000018 and EWO-000019
provide historical context but no continuing execution authority.

## Engineering Governance Disposition

Disposition: **Approved**

Engineering Governance approves creation and activation of exactly one
successor Work Order, EWO-000020 — Engineering Notification Service
Implementation.

EWO-000020 becomes the sole authority for its bounded implementation scope only
after this transaction is validated and published. Implementation shall begin
in a separate repository-governed engineering mission carrying EWO-000020.

## Transitional Authority Boundary

This transitional authority permits only:

1. create and approve EGR-000003 and EWO-000020;
2. register and activate one corresponding Work Registry item;
3. reconcile Project State and DOC-0001;
4. validate and commit the authorization publication;
5. reconcile EOS and create an append-only checkpoint; and
6. report the transaction outcome.

It does not permit notification-service implementation, source-code or wrapper
changes, mission-lifecycle implementation, Raspberry Pi diagnostics, firmware
remediation, deferred Stage 2 or Stage 3 activation, unrelated governance
revision, or creation of another successor EWO.

The transitional authority expires immediately when EWO-000020 is activated or
if this transaction becomes blocked, fails, or is interrupted. It cannot be
inherited by the EWO-000020 implementation mission.

## Authorized Governance Effects

- approve and activate EWO-000020;
- register `EMP-WORK-ENGINEERING-NOTIFICATION-SERVICE` as the single Active
  Homelab work item;
- revise Project State to identify EWO-000020 as Approved Active without
  claiming implementation has begun;
- register EGR-000003 and EWO-000020 in DOC-0001; and
- publish and reconcile the bounded authorization state with EOS.

No deferred work is resumed and no completed work is reopened.

## Lifecycle Decision

Resolution Content Approval: Approved

Approved By: Engineering Governance

Approval Date: 2026-07-17

EWO-000020 Activation Decision: Authorized

Transitional Authority State: Closed upon EWO-000020 activation

## Validation Record

Publication requires controlled-document validation, Work Registry validation,
Project State and EOS alignment, repository integrity, exactly one Active
Homelab work item, and confirmation that no implementation files changed.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-17 | Authorized and activated exactly one successor Work Order, EWO-000020, and closed the bounded bootstrap-deadlock correction transaction. |
