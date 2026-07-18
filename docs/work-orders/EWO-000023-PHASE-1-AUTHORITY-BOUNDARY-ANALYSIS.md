---
document_id: EWO-000023-PHASE-1-AUTHORITY-BOUNDARY
title: EWO-000023 Phase 1 Authority Boundary Analysis
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Authority-Gap Characterization
domain: Engineering Governance
classification: Authority Boundary Analysis
source_of_truth: true
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Persisted
related_documents:
  - EWO-000023
  - EWO-000023-PHASE-1-INVESTIGATION
  - EWO-000023-PHASE-1-EVIDENCE
  - CHAR-0001
  - POL-0001
  - PROC-0001
  - PROC-0002
  - EDR-0002
tags:
  - authority-boundary
  - phase-1
  - investigation
  - draft
---

# Authority Boundary Analysis


## Historical Approval Package Synchronization Declaration

The following declaration preserves the synchronized pre-disposition review
snapshot; current lifecycle and persistence state is authoritative in the YAML
header and the historical evidence persistence report.

Controlled Architecture:

- EDR-0003 Version 0.3

Repository Baseline:

- `4e6ac19`

Validation Baseline:

- 731 controlled-document validations passed
- zero failures
- Aggregate Engineering Platform validation PASS

Lifecycle State:

- Draft
- Pending Engineering Governance approval
- Persisted by the EWO-000023 historical evidence boundary
- Unregistered
- Non-operational
- Unimplemented

Repository State:

- no tracked modifications
- no staged modifications

Approval Package Inventory:

- exactly 14 authorized Draft artifacts


## Scope

This Draft classifies observed actions and lifecycle effects for EWO-000023
Phase 1. It does not decide whether an action should be reserved or delegated,
evaluate an architecture, or recommend a corrective mechanism.

## Action-Class Definitions

### Engineering Governance Decision

A disposition or exercise of Governance Authority that cannot be inferred from
evidence or performed merely because its repository representation is
deterministic. Observed examples include approval, activation, acceptance,
supersedence, deferral, scope selection, and authorization of successor work.

Governing sources: EV-01, EV-02, EV-08, EV-10, and EV-16.

### Operational Governance Action

Preparation, review support, publication, registration, projection,
synchronization, and audit work performed under an already-made Governance
decision. These actions affect governance records or their operational
representation but do not choose the disposition.

Governing sources: EV-02, EV-03, EV-04, EV-05, EV-10, and EV-11.

### Deterministic Repository Action

A reproducible repository or EOS operation whose permitted inputs and expected
effects are already bounded by authority: validation, serialization, registry
mutation, relationship checking, Git integrity/status, explicit-path staging,
commit, state refresh, checkpoint creation, or context generation. A
deterministic action may have governance significance without possessing
Governance Authority.

Governing sources: EV-03, EV-04, EV-05, EV-09, EV-11, EV-14, EV-15, and EV-17.

### Implementation Execution

Technical or documentation implementation of the objective authorized by an
Approved Active EWO. It begins only after the applicable initiation gates and
does not include the prior transitional transaction that makes the EWO
operationally authoritative.

Governing sources: EV-01, EV-03, EV-04, EV-06, EV-07, EV-13, and EV-16.

## Observed Action Classification

| Observed action | Class | Authority owner or executor | Source attribution | Boundary condition |
| --- | --- | --- | --- | --- |
| Decide that a proposal is Approved, Rejected, Deferred, or Superseded | Engineering Governance decision | Engineering Governance | EV-02, EV-10 | Preparer and agent may not select disposition |
| Approve or activate an EGR/EWO | Engineering Governance decision | Engineering Governance | EV-02, EV-03, EV-04, EV-10 | Metadata and registry state do not self-authorize |
| Accept completed execution | Engineering Governance decision | Engineering Governance | EV-12, EV-16 | Completion evidence does not approve itself |
| Supersede unstarted EWO-000020 | Engineering Governance decision | Engineering Governance through EGR-000004 | EV-04, EV-05 | Notification scope did not transfer to EWO-000021 |
| Authorize creation of a successor EWO | Engineering Governance decision | Engineering Governance | EV-02, EV-04, EV-16 | Predecessor mission and implementation agent cannot create it |
| Determine exact decision scope and authorized effects | Engineering Governance decision | Engineering Governance | EV-10 | Repository automation may enforce but not choose the scope |
| Prepare a complete Draft EGR from supplied disposition | Operational governance action | Authorized resolution preparer | EV-10 | Draft remains proposed pending Governance review |
| Create and populate an already authorized EGR/EWO publication | Operational governance action | Authorization-publication agent | EV-02, EV-03, EV-04 | Limited to the explicit transitional transaction |
| Register canonical paths in DOC-0001 | Operational governance action | Repository index owner/authorized publication agent | EV-03, EV-04, EV-10 | Registration provides discovery, not authority |
| Reconcile Project State to the decided lifecycle | Operational governance action | Authorized publication agent | EV-03, EV-04, EV-05 | Must not invent or broaden the decision |
| Project lifecycle into Work Registry | Operational governance action and deterministic repository action | EMP registry service under an authorized actor/reference | EV-05, EV-09, EV-15 | Registry state is not controlled-document lifecycle authority |
| Validate controlled-document structure and relationships | Deterministic repository action | Validator | EV-05, EV-11, EV-18 | PASS does not approve content or lifecycle |
| Validate registry schema, dependencies, and authority boundary | Deterministic repository action | Registry validator | EV-05, EV-09, EV-18 | Detects projection defects; chooses no disposition |
| Inspect Git identity, status, integrity, and active operations | Deterministic repository action | Git/controller | EV-11, EV-18 | Evidence for initiation only |
| Commit an explicitly authorized publication set | Deterministic repository action | Authorized publication agent | EV-03, EV-04, EV-11, EV-12 | Commit identity does not originate Governance Authority |
| Refresh EOS operational state and repository inventory | Deterministic repository action | EOS service | EV-05, EV-14, EV-18 | Derived state must follow authoritative repository state |
| Create/select an append-only checkpoint | Deterministic repository action | EOS checkpoint service | EV-03, EV-04, EV-05, EV-14, EV-18 | Checkpoint supports resume but cannot expand authority |
| Launch `engctl codex --ewo ...` and perform initiation | Deterministic repository action preceding execution | Operator/implementation agent/controller | EV-06, EV-07, EV-13, EV-18 | Marker proves wrapper path, not Governance intent |
| Modify runtime services or governing documents for mission objectives | Implementation execution | Implementation agent under applicable EWO | EV-06, EV-07, EV-13, EV-16 | Requires separately Approved Active execution scope |

## Lifecycle-Transition Classification

| Transition | Decision component | Operational/deterministic component | Implementation consequence | Evidence |
| --- | --- | --- | --- | --- |
| Proposed/Draft to Approved | Governance approves exact content and scope | Persist metadata, validate, commit, index | None unless activation and execution authority also exist | EV-02, EV-10 |
| Approved to Active | Governance authorizes activation | Project into EWO, registry, Project State, EOS, checkpoint | New mission may initiate after transaction completion | EV-02 through EV-05 |
| Active to Completed/Accepted | Governance accepts result where required | Reconcile report, EWO, registry, state, evidence | Predecessor execution ends; no successor implied | EV-01, EV-12, EV-16 |
| Active to Superseded | Governance decides supersedence and successor | Update lineage, cancel/project registry state, reconcile state | Prior scope ends and transfers only if explicitly stated | EV-04, EV-05, EV-13 |
| Transitional authority to Closed/Expired | Boundary is fixed by the approval act | Finish publication, validation, commit, EOS/checkpoint reconciliation | Implementation must use the new EWO, not the transaction | EV-02 through EV-05 |
| Repository commit to aligned EOS/checkpoint | No new disposition | Refresh derivative state and select checkpoint | Resume becomes current; no new implementation authority | EV-05, EV-14, EV-18 |

## Gap-to-Boundary Mapping

| Gap | Governance boundary | Operational governance boundary | Deterministic action boundary | Implementation boundary |
| --- | --- | --- | --- | --- |
| AG-01 successor discontinuity | Only Governance can approve successor work | No transaction exists until Governance supplies it | Discovery can prove absence but cannot create authority | Must stop after predecessor authority ends |
| AG-02 decision-to-publication | External approval act supplies disposition | Preparer must faithfully persist it | Validation/commit make it discoverable | Prohibited during publication transaction |
| AG-03 transitional/execution split | Governance defines both bounded scopes | Transaction ends at activation/publication | State reconciliation closes the transaction | Begins separately under the successor EWO |
| AG-04 projection exposure | One decision controls all projections | Owners reconcile their assigned records | Validators detect disagreement; refresh aligns views | Blocked while current authority cannot be proven |
| AG-05 mission/process mismatch | EWO authorizes the mission, not arbitrary process continuation | Initiation represents current authority operationally | Wrapper marker and gates detect known bypass | New handoff must not inherit old mission identity |
| AG-06 registry confusion risk | Controlled approval/EWO remains authoritative | Registry projects supplied authority reference | Schema/validator enforce non-governing boundary | Registry active state alone cannot authorize execution |

## Affected Agents and Services

- Engineering Governance/operator: supplies reserved decisions and approval
  acts; external handoff evidence is incomplete in this repository.
- Resolution preparer/authorization-publication agent: translates a supplied
  decision into controlled Draft/publication records; cannot select a
  disposition or use transitional authority for implementation.
- Codex implementation agent: verifies current authority, performs bounded
  execution, records evidence, and stops when Governance judgment is required.
- Repository index owner: assigns or verifies permanent identifiers and
  canonical locations; the reviewed process is documented but its concrete
  automated assignment mechanism is not evidenced.
- Work Registry services: serialize and validate management projections and
  attribution; do not own controlled lifecycle.
- EOS context, state, and checkpoint services: reconstruct and project current
  engineering state; do not originate authority.
- Git and validators: provide integrity, history, and deterministic checks;
  they do not approve or accept engineering work.

## Non-Findings

- No evidence shows Work Registry, EOS, Git, or a validator actually making a
  Governance decision.
- No evidence shows that a successful commit, checkpoint, or validation grants
  execution authority by itself.
- No finding determines that bootstrap-deadlock correction should be expanded,
  automated, delegated, or removed.
- No finding evaluates or selects a corrective architecture.

## Open Boundary Questions

The unresolved questions in `EWO-000023-PHASE-1-INVESTIGATION` apply. Most
materially, Phase 1 cannot determine from current evidence: the complete
reserved/delegable decision taxonomy; the identity and authentication model of
external approval acts; the mechanism for permanent identifier assignment;
the cross-store transaction boundary; or the authoritative persistent-process
mission event model.
