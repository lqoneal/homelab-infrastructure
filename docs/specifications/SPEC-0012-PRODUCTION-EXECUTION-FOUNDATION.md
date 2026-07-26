---
document_id: SPEC-0012
title: Production Execution Foundation
document_type: Engineering Specification
version: 1.0
status: Active
effective_date: 2026-07-26
last_updated: 2026-07-26
owner: Lawrence O'Neal
authority_domain: Execution Authority
approval_authority: Lawrence O'Neal
approval_reference: ZEUS-P2-019
source_of_truth: true
persistence_status: Pending
predecessor: null
successor: null
declared_deferrals:
  - first-operational-wop-execution-qualification
  - automatic-authority-restoration-coordination
  - repository-baseline-closeout-publication-lifecycle
relations:
  governed_by: [CHAR-0001]
  conforms_to: [SPEC-0011, POL-0001, STD-0001, STD-0002]
  related_to: [EMP-0001, EOS-0001, PROC-0001, PROC-0008]
  indexed_by: [DOC-0001]
---

# Production Execution Foundation

## 1. Authority and scope

Lawrence O'Neal is the ultimate human authority and `loneal` is the
authenticated production principal. The Zeus CLI is the authoritative
instruction interface. Controlled documentation is the normal operational
source of execution authority. The dispatcher resolves and enforces that
authority; it cannot create, broaden, or repair authority by itself.

This specification provides a commissionable implementation foundation. It
does not commission a dispatcher, qualify a production agent, dispatch an
operational WOP, or prove operational WOP execution capability.

## 2. First-qualification authority model

First-time capability development uses an explicit lifecycle:

```text
PLANNED
  -> AUTHORIZED_FOR_IMPLEMENTATION
  -> IMPLEMENTED
  -> AUTHORIZED_FOR_QUALIFICATION
  -> QUALIFIED
  -> AUTHORIZED_FOR_COMMISSIONING
  -> COMMISSIONED
  -> OPERATIONALLY_ELIGIBLE
```

Implementation, qualification, commissioning, and operational execution are
distinct authority purposes. Each transition is sequential, provenance-bound,
digest-protected, and supported by its named authorization and evidence.
Qualification authorization permits bounded qualification using production
implementations and contracts, but it does not assert that qualification
succeeded. Operational authority resolution accepts only
`OPERATIONALLY_ELIGIBLE`; it shall not treat an earlier state as operational.

Insufficient authority produces an actionable safe-stop record identifying the
blocking record, required transition, and operational impact. Restoration
follows SPEC-0011 and never permits execution outside restored controlled
documentation.

## 3. Dispatcher policy and activation

The authoritative policy is
`engineering/dispatch/dispatcher-policy.yaml`. Dispatch defaults to denial and
requires valid authority, admission, immutable WOP, matching published
repository baseline, active dispatcher activation, a matching active qualified
agent, authenticated EENS, cryptographic evidence verification, and live
reconciliation dependencies.

Activation records are authenticated by a detached `loneal` SSH signature and
bind dispatcher identity, implementation and policy
versions, repository identity and baseline, activating authority and time,
supported mission and agent classes, EENS/evidence/reconciliation
configurations, and suspension/revocation state. Missing, prepared, stale,
invalid, suspended, revoked, or baseline-mismatched activation prohibits
dispatch.

Assignment selection is deterministic among eligible agents. The initial
policy permits no automatic retry. Interruption produces a resume token;
resumption revalidates authority, activation, agent trust, WOP integrity, and
idempotency. Timeout, cancellation, invocation rejection, terminal failure,
missing heartbeat, or unavailable control dependency stops safely and records
an actionable reason.

## 4. Production execution-agent registry

The version-2 registry is authenticated by a detached `loneal` SSH signature.
Its schema records stable identity, agent and host type,
service identity, mission and tool capabilities, repository scope,
constraints, qualification status and evidence, activation, last validation,
trust, EENS and evidence-signing identities, resume capability, and concurrency
limit. Fixture agents are prohibited from production selection. Assignment
requires a current qualification, valid trust binding, capability and access
match, EENS availability, and evidence-signing capability.

## 5. Invocation and supervision

An immutable assignment binds authority decision, WOP digest, repository
baseline, selected agent, evidence obligations, and idempotency identity. The
local authenticated transport implements the same contract intended for a
future remote transport: authenticate target, bind the invocation token to the
assignment, transmit the authoritative WOP, obtain acceptance, record
execution identity, establish EENS correlation and monitoring, return terminal
state and evidence locators, and return an identical result for a repeated
assignment.

EENS producers use detached SSH signatures, stable event identifiers,
mission/assignment correlation, append-only durable files, replay, and durable
consumer checkpoints. The normative lifecycle vocabulary is:
`mission.selected`, `authority.resolved`, `wop.resolved`,
`admission.accepted`, `dispatch.authorized`, `assignment.created`,
`agent.selected`, `agent.invocation.requested`,
`agent.invocation.accepted`, `execution.started`, `progress.reported`,
`approval.required`, `approval.resolved`, `execution.interrupted`,
`execution.resumed`, `execution.completed`, `execution.failed`,
`evidence.submitted`, `evidence.qualified`, `reconciliation.started`,
`reconciliation.completed`, and `mission.closed`. Events apply when their
corresponding lifecycle condition occurs; failure and approval branches are
not fabricated during a successful execution.

## 6. Evidence and independent qualification

Production evidence binds WOP, mission, assignment, agent, repository,
baseline, gate, action, timestamps, output locator and digest, and validation
result. The agent signs canonical evidence bytes under the production evidence
namespace. An independent qualifier—never the executing identity—verifies
signature, digest, identity, scope, gate, output, repository state, tests,
completeness, and contradiction absence. Fixture signatures and fixture
evidence cannot qualify production execution.

## 7. Live reconciliation and closeout

Scoped adapters cover mission, work item, WOP, assignment, execution, evidence,
approval, project, work registry, completion registry, operational resume,
controlled documentation, and EENS checkpoints. Every update is
optimistic-lock protected, idempotent, restartable, auditable, scoped,
validated, and interruption-safe. Mission closeout is prohibited until every
required adapter succeeds and the resulting records validate.

## 8. Commissioning boundary

P2-019 checks in a `PREPARED` activation record and an empty production agent
registry. After this implementation commit, normal operational dispatch
remains denied until the commit is published as the active repository
baseline, authentic activation and registration artifacts are signed, the
dispatcher is activated, and a production agent is independently qualified.
The first operational WOP execution qualification is separate deferred work.
