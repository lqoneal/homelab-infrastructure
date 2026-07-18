---
document_id: PROC-0006
title: Governance Qualification Procedure
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Procedure Development
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: null
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
persistence_status: Persisted
source_of_truth: true
information_scope: Governance qualification invocation, evidence sufficiency, independent review, finding classification, bounded remediation, conformance requalification, recommendation, external decision routing, and closeout
declared_deferrals:
  - governance-qualification-automation
  - qualification-evidence-profile
  - governance-framework-reference-integration
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: STD-0003
  - type: conforms_to
    target: SPEC-0001
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0002
  - type: related_to
    target: PROC-0003
  - type: related_to
    target: PROC-0004
  - type: related_to
    target: PROC-0005
  - type: uses
    target: TPL-0002
  - type: uses
    target: TPL-0003
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - qualification
  - evidence
  - conformance
  - review
  - remediation
  - decision-separation
---

# Governance Qualification Procedure

## 1. Purpose

This procedure defines the reusable operational method for evaluating a
Governance subject, validating its evidence and conformance, classifying
findings, coordinating bounded remediation, and preparing a recommendation for
an external Engineering Governance decision.

Qualification evaluates and recommends. It does not approve, accept, reject,
activate, publish, establish a Governance Baseline, authorize implementation,
or expand authority.

## 2. Applicability and Scope

This procedure applies when an authorized transaction requires qualification
of a Governance Baseline, architecture, policy, standard, specification,
procedure, controlled-document revision, subsystem reconciliation, evidence
package, completed governance implementation, or publication candidate.

It may be invoked independently or as an external dependency of another
procedure. Domain-specific criteria may supplement this procedure but shall not
replace its state, evidence, authority, or decision-separation controls.

This procedure does not replace:

- PROC-0001 for bounded Engineering Work Order execution;
- PROC-0002 for recording an Engineering Governance decision in an EGR;
- PROC-0003 for specialized recovery execution and technical evidence;
- PROC-0004 for governed handoff construction; or
- PROC-0005 for controlled publication.

## 3. Governing References

- CHAR-0001 — Engineering Charter
- POL-0001 — Engineering Governance Policy
- STD-0000 — Engineering Governance Documentation Architecture
- STD-0001 — Engineering Document Lifecycle Standard
- STD-0002 — Engineering Document Persistence Standard
- STD-0003 — Engineering Work Order Standard
- SPEC-0001 — Controlled Document Model
- PROC-0001 — Engineering Work Order Execution Procedure
- PROC-0002 — Engineering Governance Resolution Procedure
- PROC-0003 — Engineering Recovery Runbook, when specialized evidence applies
- PROC-0004 — Engineering Handoff Construction Procedure
- PROC-0005 — Controlled Document Publication Procedure
- TPL-0002 — Completion Report Template
- TPL-0003 — Engineering Evidence Package Template

## 4. Authority Model

An Active Engineering Work Order or superior explicit authorization is required
to execute qualification. Holding a qualification role conveys no authority
assigned to another role.

| Role | Responsibilities | May determine | Shall not determine |
| --- | --- | --- | --- |
| Authorized Sponsor | Identify the subject, requested decision question, and governing authority | Whether to request or permissibly withdraw qualification | Qualification result or Governance disposition |
| Qualification Coordinator | Validate invocation, freeze the contract, coordinate stages, and preserve evidence | Workflow readiness and operational routing | Approval, acceptance, lifecycle, publication, or implementation authority |
| Evidence Custodian | Collect, identify, preserve, and verify evidence | Evidence inventory completeness as an observed fact | Qualification interpretation or Governance disposition |
| Technical Reviewer | Evaluate subject-matter completeness, correctness, risk, and findings | Assigned technical findings and recommendation | Governance disposition or lifecycle effect |
| Conformance Reviewer | Evaluate governing conformance, consistency, and traceability | PASS, PASS_WITH_FINDINGS, FAIL, or BLOCKED qualification result | Approval, activation, publication, baseline designation, or implementation |
| Remediation Executor | Correct authorized findings and provide regression evidence | Technical choices within existing remediation authority | Scope expansion, exception acceptance, risk acceptance, or approval |
| Engineering Governance | Review the recommendation and make the Governance decision | Acceptance, rejection, deferral, remediation authority, withdrawal, lifecycle and baseline effects | Technical evidence not actually produced |
| EGR Preparer | Record an already-made decision under PROC-0002 | Representation and validation within preparation authority | Selection of the decision or downstream execution |
| Publication Executor | Execute a separately authorized publication under PROC-0005 | Operational publication result | Qualification result, content approval, or lifecycle authority |

Reviewer overlap is permitted only when the invocation records proportional
tailoring, rationale, risk, and authority. Technical and conformance evidence
shall remain distinct even when one actor performs both roles.

## 5. Invocation Contract

Before qualification begins, record:

1. transaction identity and unique invocation identity;
2. parent invocation, caller, capability profile, and purpose, when applicable;
3. qualification subject and exact revision, fingerprint, or immutable locator;
4. sponsor, execution authority, and qualification authority;
5. governing criteria and requested decision question;
6. scope, exclusions, applicability, and evidence cutoff;
7. reviewer assignments and independence requirements;
8. evidence sources and integrity requirements;
9. permitted remediation boundary and regression criteria;
10. expected outputs and decision recipient;
11. required PROC-0001, PROC-0002, PROC-0003, PROC-0004, or PROC-0005 interactions;
12. stop, resume, withdrawal, and closeout conditions; and
13. Completion Report and evidence-package requirements.

Missing subject identity, governing criteria, execution authority,
qualification authority, or decision route is a fail-closed invocation defect.
Child scope shall be equal to or narrower than its parent authority.

The tuple of capability, profile, subject fingerprint, and purpose shall not
repeat in one active invocation chain. Qualification returns its result and
routing recommendation to its caller; it shall not recursively invoke itself,
PROC-0002, or PROC-0005.

## 6. Inputs and Outputs

### Required Inputs

- valid invocation contract;
- exact qualification subject;
- governing requirements and acceptance criteria;
- initial evidence inventory;
- known findings, exceptions, risks, and deferrals; and
- identified external decision authority and route.

### Conditional Inputs

- prior review or qualification evidence;
- remediation history;
- architecture or risk analysis;
- publication candidate fingerprint;
- proposed lifecycle or Governance Baseline effects; and
- specialized technical evidence produced under PROC-0003 or another owner.

### Required Outputs

- frozen qualification contract;
- evidence sufficiency result;
- review record;
- finding catalog;
- remediation trace, when applicable;
- conformance result;
- qualification result;
- recommendation package;
- external decision locator, when available;
- closeout record; and
- TPL-0002 Completion Report supported by TPL-0003 evidence.

No output of this procedure independently conveys Governance, lifecycle,
publication, repository, baseline, or implementation authority.

## 7. Independent State Domains

### Qualification Workflow State

```text
INVOKED
  -> INTAKE
  -> REVIEW
  -> FINDINGS_CLASSIFIED
  -> REMEDIATION
  -> REQUALIFICATION
  -> RECOMMENDATION_READY
  -> DECISION_PENDING
  -> CLOSED
```

Permitted terminal alternatives are `BLOCKED` and `WITHDRAWN`. Remediation may
loop only through an attributable iteration under valid authority.

### Qualification Result

- `NOT_EVALUATED` — no final evaluation exists;
- `PASS` — all mandatory criteria are satisfied;
- `PASS_WITH_FINDINGS` — mandatory criteria are satisfied and only
  non-blocking findings remain;
- `FAIL` — one or more blocking criteria remain unsatisfied;
- `BLOCKED` — authority, identity, evidence, or deterministic evaluation is
  insufficient; or
- `WITHDRAWN` — the authorized sponsor or Engineering Governance removed the
  subject from consideration.

### Governance Disposition

Governance dispositions are externally owned and include `PENDING`,
`ACCEPTED`, `REJECTED`, `DEFERRED`, `REMEDIATION_AUTHORIZED`, and `WITHDRAWN`
as applicable to the governing decision process.

### Publication Outcome

Publication outcomes remain owned by PROC-0005 and include `NOT_ATTEMPTED`,
`COMPLETED`, `PUBLICATION_FAILED`, `PUBLICATION_INCIDENT`, `DENIED`, or
`WITHDRAWN` as applicable.

### Overall Transaction Status

An orchestrator may derive `IN_PROGRESS`, `PASS`, `PASS_WITH_FINDINGS`, `FAIL`,
`BLOCKED`, `WITHDRAWN`, or `INCIDENT`. A derived status shall not overwrite an
authoritative state in another domain.

A qualification PASS is not Governance acceptance. Acceptance is not
activation. Activation is not publication. Publication does not authorize
implementation.

## 8. Nine-Stage Workflow

No stage may be removed. Proportionality may combine assigned reviewers or
scale evidence depth only when the invocation records the tailoring and all
stage criteria and evidence remain distinct.

### Stage 1 — Invocation and Contract Freeze

#### Purpose

Establish exactly what will be evaluated, under which authority, against which
criteria, for which external decision.

#### Activities

1. Validate the invocation fields in section 5.
2. Verify subject identity, authority, scope, and decision route.
3. Record criteria applicability and explicit exclusions.
4. Record reviewer assignments, independence, and permitted overlap.
5. Freeze the subject fingerprint and evidence cutoff.

#### Evidence and Exit Criteria

Produce the frozen contract, subject locator, authority evidence, applicability
record, actor matrix, and initial state. Exit to Stage 2 only when the contract
is complete. Otherwise report `BLOCKED`.

### Stage 2 — Evidence Intake and Sufficiency

#### Purpose

Determine whether objective evidence is complete enough for review.

#### Activities

Inventory evidence; verify provenance, integrity, freshness, reproducibility,
traceability, scope, and access; identify missing or contradictory evidence;
and distinguish observed facts from assertions or recommendations.

#### Evidence and Exit Criteria

Record every evidence identifier, source, timestamp, locator, integrity method,
and criterion mapping using TPL-0003. Exit to Stage 3 when evidence is
sufficient. Missing evidence that can be supplied remains in Stage 2; missing
authority, subject identity, or determinism returns `BLOCKED`.

### Stage 3 — Independent Review

#### Purpose

Evaluate the exact subject against the frozen technical, architectural,
security, operational, and Governance-boundary criteria.

#### Activities

Review the complete subject and its dependencies; evaluate correctness,
coherence, ownership, trust boundaries, risk, implementation independence,
historical integrity, and disclosed exceptions or deferrals. Reviewers shall
record evidence, not inferred authority.

#### Evidence and Exit Criteria

Produce a criterion-by-criterion review record with observations and evidence.
Exit when every applicable criterion is evaluated or report `BLOCKED` when a
deterministic evaluation cannot be completed.

### Stage 4 — Finding Classification

#### Purpose

Create a stable, actionable finding set.

#### Activities

For each finding record identity, violated or satisfied criterion, evidence,
severity, impact, affected scope, rationale, and recommended route. Classify
findings as blocking, non-blocking, or observational. Duplicate findings shall
be consolidated without losing provenance.

#### Evidence and Exit Criteria

Produce the frozen finding catalog and preliminary qualification assessment.
No blocking finding may be silently downgraded. Route correctable blocking
findings to Stage 5; otherwise proceed to Stage 6.

### Stage 5 — Bounded Remediation

#### Purpose

Correct authorized findings without expanding scope or changing an external
decision.

#### Activities

1. Map each finding to a correction or unresolved disposition.
2. Verify remediation authority before modification.
3. Preserve unaffected conclusions, ownership, and historical meaning.
4. Record a revised subject fingerprint and finding-to-correction trace.
5. Run affected regression checks.

Changes to authority, scope, ownership, risk acceptance, lifecycle effect,
decision subject, or baseline effect require external Governance disposition
and a new or amended invocation before work resumes.

#### Evidence and Exit Criteria

Produce the remediation iteration, correction trace, revised locator, and
regression evidence. Return material changes to Stage 3. Bounded changes may
proceed to Stage 6. Repeated unchanged failure shall report remediation
exhaustion rather than loop indefinitely.

### Stage 6 — Conformance Requalification

#### Purpose

Establish the final qualification result for the complete current subject.

#### Activities

Verify all applicable criteria, correction coverage, internal consistency,
authority preservation, metadata and relationships where applicable,
deterministic validation, exception treatment, deferrals, and regression
results.

#### Evidence and Exit Criteria

Produce the exact qualified subject fingerprint, complete validation record,
remaining-finding inventory, and one qualification result from section 7.
`PASS` or `PASS_WITH_FINDINGS` proceeds to Stage 7. `FAIL` proceeds to Stage 7
with a failure recommendation. `BLOCKED` stops pending resolution.

### Stage 7 — Recommendation Package

#### Purpose

Prepare a decision-ready package without making the Governance decision.

#### Activities

Summarize the subject, criteria, evidence sufficiency, findings, remediation,
qualification result, residual risk, exceptions, deferrals, alternatives,
recommended disposition, proposed downstream routing, and required authority.

#### Evidence and Exit Criteria

The package shall trace every recommendation to evidence and identify the
exact frozen subject. Recommendations do not authorize their own adoption.
Exit to Stage 8 when the package is independently reconstructable.

### Stage 8 — External Decision Routing

#### Purpose

Submit the recommendation to Engineering Governance without exercising its
decision authority.

#### Activities

Return the package to the caller and route it to the identified decision
authority. The caller invokes PROC-0002 when an EGR is required. Record the
external decision locator and any divergence between qualification result,
recommendation, and decision.

#### Evidence and Exit Criteria

Qualification never issues `ACCEPTED`, `REJECTED`, `DEFERRED`, or
`REMEDIATION_AUTHORIZED`. Exit when the package has been routed and the result
is recorded as `PENDING`, or when an external decision locator is available.

### Stage 9 — Closeout and Routing

#### Purpose

Preserve the independent state domains and identify the next authorized action.

#### Activities

Record final workflow state, qualification result, external decision if
available, divergence, unresolved findings, accepted risks or deferrals,
publication outcome, baseline-effect status, implementation-authority status,
and immutable evidence locators. Route authorized remediation back through the
applicable stage. Return publication recommendations to the caller for any
PROC-0005 invocation.

#### Evidence and Exit Criteria

Produce the TPL-0002 Completion Report and complete TPL-0003 evidence package.
Closeout is complete only when every state domain is truthful and follow-on
work is explicitly unauthorized unless supported by separate authority.

## 9. Decision and Routing Matrix

| Qualification result | Permitted qualification action | External route |
| --- | --- | --- |
| PASS | Recommend acceptance or the transaction-specific disposition | Engineering Governance |
| PASS_WITH_FINDINGS | Recommend with residual findings and treatment | Engineering Governance |
| FAIL | Recommend remediation, rejection, or deferral | Engineering Governance |
| BLOCKED | Report missing authority, identity, evidence, or determinism | Sponsor or Engineering Governance |
| WITHDRAWN | Preserve evidence and close | No downstream execution |

An external decision contrary to the recommendation does not alter the
qualification result. The decision and its rationale are recorded separately.

## 10. Evidence Requirements

Use TPL-0003 without redesign. The evidence package or supporting artifacts
shall permit reconstruction of:

1. invocation and authority;
2. exact subject and fingerprint at every material stage;
3. governing criteria and applicability;
4. evidence inventory, provenance, integrity, and freshness;
5. reviewer identity, role, and independence treatment;
6. criterion-to-evidence traceability;
7. findings, severity, impact, and rationale;
8. remediation iterations and correction trace;
9. validation and regression results;
10. qualification result and recommendation;
11. external decision and divergence, when available;
12. publication and baseline-effect status;
13. final repository or subject state; and
14. Completion Report certification.

Evidence shall be attributable, reproducible, traceable, value-preserving, and
truthful. Partial output is not terminal evidence. A report about an operation
is not a substitute for its required retained evidence.

## 11. Stop and Resume Conditions

Stop when authority, subject identity, criteria, evidence integrity, reviewer
assignment, deterministic validation, or decision routing cannot be
established; remediation exceeds authority; a repeated invocation tuple is
detected; historical evidence would be overwritten; or a prohibited downstream
effect is required.

Resume only after recording the blocking condition, authoritative resolution,
current subject fingerprint, affected stage, invalidated evidence, and first
permitted next action. A material subject change requires re-entry at Stage 1
or Stage 3 according to the updated authority and review impact.

## 12. Compatibility and Ownership

- PROC-0001 remains the execution owner and Completion Report workflow owner.
- PROC-0002 remains the EGR preparation and decision-recording owner.
- PROC-0003 remains the recovery and specialized technical-evidence owner.
- PROC-0004 remains the handoff-construction and authority-preservation owner.
- PROC-0005 remains the controlled-publication owner.
- TPL-0003 remains the approved evidence-package representation.
- Engineering Governance remains the sole decision authority unless superior
  governance records an explicit valid delegation.

This procedure may be profiled by another procedure, but its result shall
return to the caller. It shall not become a hidden authorization or recursive
orchestration mechanism.

## 13. Completion Criteria

Qualification is operationally complete when the nine stages are accounted
for; the subject, authority, evidence, findings, remediation, result,
recommendation, routing, and state domains reconstruct deterministically; the
Completion Report is complete; and no prohibited authority was exercised.

A `FAIL` or `BLOCKED` result may be a valid completed qualification outcome.
Execution success is not restricted to a PASS result; success means the
procedure produced a truthful qualified outcome within authority.

## 14. Future Considerations

The following remain Deferred Execution and require separate authorization:

- qualification workflow automation;
- a TPL-0003 enhancement or companion qualification evidence profile;
- machine-readable invocation and state schemas; and
- reference-based integration throughout the Governance framework.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 0.1 | 2026-07-18 | Developed the Draft reusable Governance Qualification Procedure from the qualified nine-stage capability and integrated authority contract without approving, activating, publishing, or automating it. |
