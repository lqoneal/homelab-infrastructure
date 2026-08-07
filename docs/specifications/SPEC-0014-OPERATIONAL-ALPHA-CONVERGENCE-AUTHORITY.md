---
document_id: SPEC-0014
title: Operational Alpha Convergence Authority Model
version: 1.6
status: Active
owner: Homelab Infrastructure
created: 2026-07-30
last_updated: 2026-07-31
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
permission, or successful verification creates authority. The operator's
identity-bound WOP submission is the work-authority source for the WOP's
explicit scope. This specification defines admission and execution safety;
those controls do not grant authority a second time.

## Execution-First Engineering Philosophy

The primary objective of the Zeus Engineering Platform is successful execution
of engineering work. Architecture exists to enable that execution; it is not an
independent engineering objective.

When execution encounters a blocker, its resolution order is:

1. Reuse existing published capability.
2. Correct an implementation defect.
3. Remove obsolete or legacy behavior.
4. Simplify existing architecture.
5. Consolidate overlapping architecture.
6. Introduce new foundational architecture only after the preceding options
   have been demonstrated insufficient.

The default runtime decision is **execution before expansion**. Execution is
preferred whenever it preserves engineering authority, evidence integrity,
repository integrity, security, and controlled engineering records.

### Architectural burden of proof

A proposal introducing a controlled-document class, framework, authority
layer, lifecycle object, registry, runtime subsystem, execution interface, or
foundational capability must demonstrate that existing architecture was
evaluated; reuse, implementation correction, simplification, and
consolidation are insufficient; and the addition materially improves
execution. A legacy compatibility mechanism participates in authoritative
Operational Alpha execution only when this specification explicitly designates
it authoritative. Where legacy behavior conflicts with the convergence model,
removal or migration is preferred to preservation through an additional layer.

Every Operational Alpha WOP generated after OA-01 activation inherits this
section by reference unless its authorizing mission explicitly modifies or
supersedes it.

## Canonical authority chain

An Operational Alpha action is eligible only when the submitted WOP and its
downstream safety chain resolve:

```text
operator-submitted WOP → admission and identity binding → EMM/repository,
provider, prerequisite, lifecycle, and baseline checks → qualified capability
→ action
```

Each arrow is directional. A consumer may retain a receipt or projection but
may not overwrite its producer. A missing, duplicate, incompatible, stale, or
digest-mismatched input fails closed.

| Object | Single authoritative owner | Required identity and state |
| --- | --- | --- |
| WOP submission | operator through Zeus | immutable WOP identity, submission identity, scope, exclusions, and digest |
| Admission and safety resolution | Zeus and named control owners | derived validation, prerequisite, provider, lifecycle, and baseline predicates |
| Engineering metadata entity | named EMM entity owner | entity type/id/revision/schema/owner digest |
| Implementation WOP | assigned WOP owner | baseline-bound submitted revision whose scope remains the hard work boundary |
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
and expires with any bound source revision, baseline, or submitted-WOP
identity. A domain Authority Record may be included only when its owning
contract requires it as a safety or identity input; it is not a generic second
grant of operator work authority.

## Manual-governance WOP authority policy

`MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY` records the submission protocol. An
identity-bound submitted WOP is the authority boundary for its own bounded,
explicitly scoped actions. The resolver records the WOP and submission identity in
its receipt. Admission, provider qualification, dependencies, lifecycle,
baseline, and any explicit in-WOP approval gates remain required; none is a
second generic corrective, implementation, or execution grant. The runtime
never infers authority from a title, operator identity, or command alone.

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

## Controlled artifact framework

`OPERATIONAL-ALPHA-CONTROLLED-ARTIFACT-FRAMEWORK@1.0` defines the sole
publication model for Authority Records, Operational Gate Plans, and Activation
Records. Each source validates its controlled schema, binds the exact WOP and
baseline, and has one EMM entity carrying its exact source digest. The Metadata
Engine may produce deterministic `DRAFT` candidates, but candidates are
non-authoritative until controlled publication registers their source. The
framework never permits a candidate or resolver to advance OA lifecycle state.

## Lifecycle and activation

The controlled WOP lifecycle is `DRAFT → READY → ACTIVE → EXECUTING →
VERIFIED → QUALIFIED → ACCEPTED → CLOSED`, with `BLOCKED`, `SUPERSEDED`, and
`ARCHIVED` as explicit non-progress alternatives. The submitted WOP supplies
work authority within its scope. Lifecycle state still does not bypass
admission, provider, baseline, prerequisite, or explicit approval checks; an
execution capability may begin only after those safety predicates pass. A failure preserves the source facts, records an
event, and moves only the affected WOP or projection to `BLOCKED`.

There is one valid predecessor for each normal transition. A transition receipt
records before/after identity, triggering authority, correlation id, evidence
locator, and reconciliation result. No component may self-accept,
self-qualify, or advance its own governing authority.

### Immutable Implementation-WOP lifecycle projection

`OPERATIONAL-ALPHA-IMPLEMENTATION-WOP-LIFECYCLE-TRANSITION@1.0` defines the
only controlled mechanism for changing the effective lifecycle state of an
immutable Operational Alpha Implementation WOP. The immutable WOP source stays
unchanged. An EMM-registered, authoritative transition must bind exactly one
WOP identity and revision, reproduce the source's declared state, carry exact
authority lineage, and state an allowed `READY → ACTIVE` target with
`NOT_STARTED` execution. The runtime rejects absent, duplicate, stale,
digest-mismatched, or non-reconcilable transitions.

The transition is effective only after its controlled source and exact EMM
digest are published and project, progress, and EOS projections reconcile.
The lifecycle-transition specification and framework do not create a
transition, Authority Record, Operational Gate Plan, Activation Record, or
execution state.

## Runtime contracts

### Dispatcher admission simplification

Operational Alpha dispatcher admission resolves exclusively from a successful
convergence receipt for the requested WOP and action. The receipt binds the
EMM, exact identity-bound submitted WOP, and published Operational Gate Plan.
A domain Authority Record may be included only when its owning contract
requires it as a safety or identity input. Progressive
PMCT, legacy authority publications, production-dispatcher activation, and
legacy agent qualification may remain available for historical evidence or
compatibility diagnostics, but they shall not grant, deny, or modify an
Operational Alpha admission decision.

Superseded Progressive dispatcher authority is retired from Operational Alpha
execution. Its retained PMCT tooling is non-authoritative compatibility support
only, subject to the Execution-First Engineering Philosophy above.

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

Synchronization is a continuous operational responsibility, not a closeout
task. The synchronization owner evaluates source events immediately where an
event contract exists and also performs scheduled checkpoint verification.
Independent drift detection compares the authoritative repository source with
runtime and generated projections even when synchronization reports success.
It classifies a discrepancy by source, ownership, lifecycle impact, and
recoverability; retains the comparison evidence; assigns reconciliation to the
source owner; and invokes the Operator Resolution Protocol for a decision,
protected-state, or unresolved conflict. Drift detection cannot repair or
overwrite an authoritative fact.

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
and a submitted WOP that resolves for the specific WOP, action, and baseline.
Any additional Authority Record is validated only when a separate domain
contract requires it and is not treated as a second operator authorization.
