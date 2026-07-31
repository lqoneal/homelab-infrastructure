---
document_id: SPEC-0014
title: Operational Alpha Convergence Authority Model
version: 1.2
status: Active
owner: Homelab Infrastructure
created: 2026-07-30
last_updated: 2026-07-30
domain: Operational Alpha
classification: Engineering Specification
source_of_truth: true
baseline_binding: OA-IMPLEMENTATION-BASELINE-1.0@5706307c1fdf9d4e0601c9cc578181f6d916e0a8
supersedes_execution_semantics:
  - STD-0003@1.5
  - PROC-0001@1.19
  - SPEC-0005@1.2
---

# Operational Alpha Convergence Authority Model

## Purpose and precedence

This specification makes the adopted Operational Alpha convergence baseline
the controlled runtime authority model. It governs Operational Alpha only. It
supersedes the listed documents' legacy requirement that an Active Engineering
Work Order and a Work Registry record, by themselves, resolve execution
authority. Historical records remain retained evidence; they are not a current
authority source for an Operational Alpha action.

No planning document, generated projection, command output, workspace
permission, or successful verification grants authority. This specification
does not authorize implementation, dispatch, acceptance, publication, or a
lifecycle transition.

## Canonical authority chain

An Operational Alpha action is eligible only when this exact, version-pinned
chain resolves:

```text
Governance Decision → Authority Record → Engineering Metadata Model (EMM)
→ published Implementation WOP → canonical resolution receipt
→ qualified capability → action
```

Each arrow is directional. A consumer may retain a receipt or projection but
may not overwrite its producer. A missing, duplicate, incompatible, stale, or
digest-mismatched input fails closed.

| Object | Single authoritative owner | Required identity and state |
| --- | --- | --- |
| Governance Decision | Governance | immutable decision id, scope, target, and digest |
| Authority Record | Governance | one decision binding, baseline, permitted action, lifecycle and expiry |
| Engineering metadata entity | named EMM entity owner | entity type/id/revision/schema/owner digest |
| Implementation WOP | assigned WOP owner | baseline-bound revision in `READY`; `ACTIVE` only after a resolved Authority Record permits activation |
| Resolution receipt | Metadata Engine | exact input manifest, compatibility result, source digests, outcome |
| Qualification result | Qualification Engine | sealed criteria, evidence, result, and digest |
| Operational Gate Plan | assigned WOP owner | exact WOP/baseline binding, lifecycle, source digest, and handler-compatible actions |

## Deterministic resolver requirements

The resolver accepts `entity_type`, `entity_id`, exact `revision` or an
explicit compatibility range, repository baseline, requested action, and
correlation identifier. It resolves exact revision first, then one uniquely
compatible published revision; it never selects an implicit latest revision.
It returns a provenance-bearing receipt containing source identities, owners,
schema versions, compatibility decision, qualification binding, digests, and
one outcome: `RESOLVED`, `NOT_FOUND`, `AMBIGUOUS_RESOLUTION`,
`INTEGRITY_FAILURE`, `INCOMPATIBLE_VERSION`, or `PRECONDITION_FAILED`.

Only `RESOLVED` permits the next lifecycle operation. The receipt is derived
and expires with any bound source revision, baseline, or Authority Record.

## Manual-governance WOP authority policy

While `MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY@1.0` remains `ACTIVE`, an
explicitly submitted Engineering Governance WOP may be the root authority for
its own bounded, allowlisted actions. It is not an inferred exception: the WOP
must be EMM-registered and contain an exact governance-submission attestation,
an active delegation state, the governing policy identity, and its permitted
action list. The resolver records that mode and submission identity in its
receipt.

This temporary path admits only the root WOP actions needed to create or
validate the subordinate artifacts it explicitly delegates. Those artifacts
must bind back to that exact WOP, revision, policy, and submission identity.
An autonomous WOP, or a WOP with an incomplete or inactive attestation,
continues to require the normal Authority Record contract. The runtime never
infers manual authority from a title, operator identity, or command.

## Operational execution contract

The authoritative execution contract is the EMM-registered
`OperationalExecutionContract` artifact. It defines the resolution boundary
for an `OperationalGatePlan`; it is not itself a gate plan and it cannot
authorize an action. An Operational Gate Plan is an authoritative,
Implementation-WOP-bound artifact owned by the assigned WOP owner. It alone
supplies the concrete gate actions consumed by an operational gate handler.

The resolver selects a plan only by the exact Implementation WOP identity and
revision specified in the resolution receipt. The plan must bind the same
baseline, identify the same WOP and revision, be represented by exactly one
EMM entity, be in `ACTIVE` lifecycle state, and validate against the handler
contract. Missing plan, duplicate identity, stale lifecycle, mismatched
binding, or invalid payload fails closed. The runtime may assemble an
ephemeral execution context from this authoritative plan and the resolved
receipt, but it shall never synthesize actions, scope, content, dependencies,
or a plan from a WOP, a generated artifact, or a runtime assumption.

## Lifecycle and activation

The controlled WOP lifecycle is `DRAFT → READY → ACTIVE → EXECUTING →
VERIFIED → QUALIFIED → ACCEPTED → CLOSED`, with `BLOCKED`, `SUPERSEDED`, and
`ARCHIVED` as explicit non-progress alternatives. `READY` is not authority to
execute. A resolver-confirmed Authority Record is the only admission to
`ACTIVE`; an execution capability may begin only from `ACTIVE` with a passing
preflight qualification. A failure preserves the source facts, records an
event, and moves only the affected WOP or projection to `BLOCKED`.

There is one valid predecessor for each normal transition. A transition receipt
records before/after identity, triggering authority, correlation id, evidence
locator, and reconciliation result. No component may self-accept,
self-qualify, or advance its own governing authority.

## Runtime contracts

All interfaces carry contract version, correlation id, producer/consumer
owners, exact input manifest, output digest, and a durable receipt.

| Interface | Producer → consumer | Deterministic rule |
| --- | --- | --- |
| Governance → EMP | decision → planning applicability | reject absent or incompatible baseline |
| EMP → Zeus | sealed plan → mission projection | pin plan revision and issue receipt |
| Zeus → Metadata Engine | resolution request → resolution receipt | request is read-only; source owner retains facts |
| Metadata Engine → Generator | published manifest → derived artifact | topological dependency resolution; source never overwritten |
| Generator → Qualification Engine | output manifest → sealed result | failed qualification blocks publication |
| Zeus/Qualification → EOS | event/result → runtime projection | idempotent projection; EOS is derived |
| Zeus → EENS | event → append receipt | append-only, retry by event identity |

## Synchronization, generation, and qualification

Synchronization starts only from a published source revision, explicit
regeneration request, scheduled reconciliation checkpoint, or recovery replay.
It validates source, ownership, schema, qualification, and target contract;
resolves dependencies in topological order; writes the target atomically with
its receipt; verifies digest/provenance/freshness; and on non-retryable failure
quarantines the target and emits a discrepancy. Derived representations never
write to authoritative facts.

Generated artifacts are reproducible projections of authoritative metadata and
embed source entities, metadata version, generator version, timestamp,
synchronization status, and qualification status. Qualification consumes a
sealed subject manifest, exact criteria and validators, and evidence. It
validates identity, lineage, schema, ownership, compatibility, lifecycle,
graphs, synchronization, and projections before producing a sealed `PASS`,
`FAIL`, or `NOT_READY` result. It does not grant approval.

## Completion report requirements

A controlled migration or implementation Completion Report uses TPL-0002 and
binds the report to the resolved WOP, Authority Record, baseline, input/output
manifests, transition receipts, qualification result, synchronization receipts,
and retained evidence. Completion is a reported fact, not an authorization for
acceptance or later execution.

## Validation

Conformance requires exactly one owner for every authoritative fact; exact
baseline and version resolution; no authority or synchronization cycles;
directional synchronization; reproducible projections; sealed qualification;
and either an Authority Record that resolves for the specific WOP, action, and
baseline or an active, EMM-resolved manual-governance WOP policy with an exact
allowlisted submission.
