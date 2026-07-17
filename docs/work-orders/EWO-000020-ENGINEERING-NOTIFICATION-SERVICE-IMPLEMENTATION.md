---
document_id: EWO-000020
title: Engineering Notification Service Implementation
version: 1.0
revision: 1
status: Superseded
owner: Engineering Governance
created: 2026-07-17
last_updated: 2026-07-17
classification: Engineering Work Order
predecessor_revision: null
successor_revision: EWO-000021
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000003
approval_date: 2026-07-17
persistence_status: Pending
phase: Engineering Notification Service
domain: Homelab Infrastructure
source_of_truth: true
related_documents:
  - CHAR-0001
  - POL-0001
  - STD-0003
  - PROC-0001
  - DOC-0001
  - PROJ-0001
  - INF-0001
  - EGR-000003
  - EWO-000017
  - EWO-000019
tags:
  - engineering-work-order
  - engineering-notifications
  - mission-lifecycle
  - codex
---

# Engineering Work Order

## Engineering Governance Header

Engineering Operating System: Engineering Operating System (EOS)

Engineering Governance: Engineering Governance

Implementation Agent: Codex

Mission: Engineering Notification Service Implementation

Phase: Engineering Notification Service

Engineering Work Order: EWO-000020

Revision: 1

Status: Superseded

Execution Mode: Separate wrapped Category A engineering mission

## Governing References

This Work Order is authorized by EGR-000003, subordinate to CHAR-0001 and
POL-0001, and governed by STD-0003, PROC-0001, the controlled-document model,
Engineering Work Initiation, and the existing notification trust boundary.

## Engineering Governance Intent

### Mission Classification

Category A — Repository Engineering Work.

### Purpose

Design, implement, validate, document, and operationally qualify a reusable
Engineering Notification Service whose authoritative lifecycle boundary is:

> one accepted engineering handoff equals one Engineering Mission.

Codex process, PID, terminal, shell, wrapper, and repository-session lifetimes
are implementation details and shall not define the Engineering Mission.

### Authorized Scope

This Work Order authorizes:

- mission-start notifications;
- explicit milestone or periodic status updates;
- completed, blocked, failed, interrupted, cancelled, and timed-out terminal
  notifications with pertinent value-blind completion status;
- persistent mission and notification state, recovery, and resume;
- one authoritative payload schema, sanitization boundary, transport
  abstraction, retry behavior, and delivery evidence model;
- `engctl codex start`, `update`, `finish`, `status`, `resume`, and `cancel`;
- persistent Codex process support with independent identity and notification
  lifecycle for every accepted handoff;
- preservation of useful exit-code, signal, timeout, secure-configuration, and
  graceful-degradation behavior;
- regression testing and live multi-handoff operational validation;
- mandatory operator confirmation of independent notifications;
- complete directly affected documentation, Work Registry, Project State,
  DOC-0001, EOS, evidence, Completion Report, commit, and checkpoint
  reconciliation.

### Constraints and Exclusions

Do not redesign the general governance subsystem or create an Engineering
Governance Authorization Service. Do not implement unrelated Engineering
Management Platform functionality, Raspberry Pi diagnostics, firmware
remediation, or unrelated repository work. Existing Stage 2 heartbeat and
Stage 3 structured-progress deferrals remain deferred except for narrowly
necessary label reconciliation; this Work Order does not reactivate either
deferred work item.

Notification payloads shall remain value-blind and shall never include private
prompts, repository content, command output, endpoint or topic values,
credentials, tokens, or private configuration.

Push and tag are prohibited unless separately authorized.

## Authority Model

The implementation agent may modify only the directly affected notification,
controller, test, runtime, validation, controlled-document, registry, and EOS
assets necessary for the authorized service. EGR-000003's transitional
authority has closed and supplies no implementation authority; all execution
shall rely on this Active EWO.

Implementation shall begin in a new process launched through:

```bash
engctl codex --ewo EWO-000020 -- [codex arguments ...]
```

## Execution and Acceptance

1. Perform complete repository-governed Engineering Work Initiation.
2. Reconcile the current process-centric notification implementation with the
   accepted-handoff lifecycle boundary.
3. Implement the single reusable notification service and mission API.
4. Implement persistent state, recovery, retries, delivery evidence, payload
   sanitization, and EOS synchronization.
5. Add and pass regression, repository, controlled-document, registry, EOS,
   and Engineering Platform validation.
6. Execute at least three independent handoffs within one persistent Codex
   process and obtain operator confirmation for every start and terminal
   notification.
7. Reconcile documentation and state, publish authorized implementation
   commits, produce the exact `Completion Report`, and create a checkpoint.

Acceptance requires independent mission identity and lifecycle evidence for
each accepted handoff, passing validation, operator-confirmed notifications,
clean publication state, and a mandatory Governance Conformance Review.

## Resume Policy

Resume only through EWO-000020 after re-running Engineering Work Initiation,
validating persistent runtime state, and identifying the first incomplete
authorized phase. Never infer lifecycle state from Codex process continuity.

## Stop Conditions

Stop on exceeded authority, secret or private-value exposure, ambiguous mission
identity, unreconciled persistent state, delivery evidence corruption,
validation failure outside authorized remediation, or inability to preserve
repository and EOS traceability.

## Completion Report Requirements

Produce a report titled exactly `Completion Report` using the repository
standard structure and mandatory Governance Conformance Review. Do not mark the
Work Order completed until Engineering Governance accepts the qualified result.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-17 | Created, approved, and activated Engineering Notification Service implementation authority under EGR-000003. |
| 1.1 | 2026-07-17 | Superseded before implementation by EGR-000004 and EWO-000021; no scope transferred or executed. |
