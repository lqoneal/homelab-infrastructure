---
document_id: EWO-000017
title: Codex Stage 1 Completion Notification Integration
version: 1.1
revision: 2
status: Completed
owner: Engineering Governance
created: 2026-07-17
last_updated: 2026-07-17
classification: Engineering Work Order
predecessor_revision: EWO-000017@1.0
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: CODEX ENGINEERING HANDOFF — Stage 1 Codex Completion Notifications via ntfy
approval_date: 2026-07-17
persistence_status: Complete
phase: Shared Engineering Operations Notification Integration
domain: Homelab Infrastructure
source_of_truth: true
related_documents:
  - CHAR-0001
  - POL-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - STD-0003
  - PROC-0001
  - SPEC-0005
  - SERVICE-0001
  - INF-0001
  - DOC-0001
  - PROJ-0001
tags:
  - engineering-work-order
  - engineering-operations
  - codex
  - notifications
  - ntfy
---

# Engineering Work Order

## Engineering Governance Header

Engineering Operating System: Engineering Operating System (EOS)

Engineering Governance: Engineering Governance

Implementation Agent: Codex

Mission: Codex Stage 1 Completion Notification Integration

Phase: Shared Engineering Operations Notification Integration

Engineering Work Order: EWO-000017

Revision: 1

Title: Codex Stage 1 Completion Notification Integration

Classification: Engineering Work Order

Status: Completed

Execution Mode: Sequential implementation and controlled validation

## Governing References

This Work Order complies with CHAR-0001, POL-0001, STD-0000, STD-0001,
STD-0002, STD-0003, PROC-0001, SPEC-0005, SERVICE-0001, INF-0001, DOC-0001,
and PROJ-0001.

## Engineering Governance Intent

### Purpose

Implement a shared Engineering Operations capability that launches Codex
through `engctl` and sends bounded operational lifecycle notifications through
ntfy over HTTPS.

### Mission Scope

This Work Order authorizes:

- one reusable ntfy transport helper using configurable local settings;
- one interactive Codex lifecycle wrapper integrated with `engctl codex`;
- start, successful-exit, failed-exit, and interruption notifications;
- optional EWO context, repository identity, host identity, and elapsed time;
- secure placeholder configuration and ignored local configuration;
- static, controlled-process, signal, argument, delivery, and repository tests;
- applicable controlled-document and authoritative backlog revisions; and
- recording Stage 2 heartbeat and Stage 3 structured progress integration as
  deferred work.

### Ownership

Homelab Infrastructure owns this capability as shared Engineering Operations
infrastructure. Product repositories consume the global controller and shall
not duplicate the transport or lifecycle implementation.

### Constraints and Non-Goals

The implementation shall not add heartbeat notifications, progress estimates,
Codex-output parsing, dashboards, alternate transports, remote cancellation,
approval automation, persistent job storage, background daemon management, or
systemd deployment. It shall not transmit prompts, output, diffs, repository
contents, credentials, or the private ntfy topic.

## Authority Model

### Operational Authority

The implementation agent may inspect the Engineering Platform, create the
required local notification configuration with restrictive permissions, send
harmless notification tests, and execute controlled wrapper tests.

### Engineering Authority

The implementation agent may revise Homelab controller and service scripts,
tests, configuration examples, ignore rules, the authoritative backlog, and
applicable controlled records. Complete controlled-document revisions are
required.

### Prohibited Activities

No commit, push, product-specific implementation, daemon deployment,
production EWO smoke-test association, secret publication, or expansion into
Stage 2 or Stage 3 is authorized.

### Escalation Requirements

Stop if shared ownership becomes ambiguous, an existing competing architecture
is discovered, repository integrity fails, a private topic cannot be handled
without exposure, or validation would require unauthorized external effects.

## Execution Phases

1. Verify authority, ownership, repository state, and configuration patterns.
2. Implement ntfy transport, Codex lifecycle control, tests, and secure setup.
3. Validate syntax, exit behavior, signals, argument fidelity, delivery, and
   repository conformance.
4. Reconcile controlled documents and report evidence without committing.

## Resume Policy

After interruption, verify this Active Revision 1, repeat read-only Work
Initiation, inventory the working tree, and resume at the first incomplete
phase. Do not repeat completed external notification tests unnecessarily.

## Success Criteria

The mission succeeds when `engctl codex` preserves interactive execution,
arguments, signals, and the original Codex result; notification failures are
non-fatal; no secret is tracked or exposed; all controlled and repository
validation passes; and Stage 2 and Stage 3 remain explicitly deferred.

## Stop Conditions

Stop on authority ambiguity, secret exposure, repository-integrity failure,
unbounded network behavior, orphaned test processes, non-deterministic exit
status, or any need to exceed this Work Order.

## Completion Report Requirements

Report discovery and authority, implementation, validation and conformance,
files changed, runtime changes, notification-delivery evidence, unresolved
dependencies, repository status, and recommended follow-on work. Do not report
the private topic.

## Completion and Acceptance Record

Stage 1 was accepted on 2026-07-17 after the loader was corrected to reject
all published example topics and known placeholder topics before network
activity. Automated notification and Engineering Platform regressions passed.
Value-blind local configuration qualification confirmed correct ownership,
mode `0600`, required assignments, non-example values, and loader acceptance.
Controlled live transport and `engctl codex` completion delivery succeeded
within the configured latency bound without disclosing private configuration.

The associated Completion Report is `EWO-000017-COMPLETION`.

## Future Architecture Recommendation

A standalone `engctl notify` command would improve bounded operator testing,
transport diagnostics, and future non-Codex Engineering Operations reuse. It
is not required for Stage 1 and was not implemented. Any implementation
requires a successor Work Order with an explicit message-content trust
boundary, validation contract, and acceptance plan.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-17 | Created and activated Stage 1 shared Codex lifecycle notification integration. |
| 1.1 | 2026-07-17 | Accepted the qualified implementation, closed Stage 1, and recorded standalone notification control as future work. |
