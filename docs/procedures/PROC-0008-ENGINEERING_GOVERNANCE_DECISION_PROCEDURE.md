---
document_id: PROC-0008
title: Engineering Governance Decision Procedure
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-22
last_updated: 2026-07-22
phase: Governance Decision Capability Development
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: null
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: false
information_scope: Governance decision evaluation, attributable issuance, disposition semantics, conditions, exceptions, authorization separation, audit, and routing
declared_deferrals:
  - authenticated-governance-identity-mechanism
  - governance-decision-envelope-automation
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
    target: SPEC-0001
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: EDR-0003
  - type: related_to
    target: PROC-0002
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROC-0007
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - decision
  - disposition
  - attribution
  - authorization-boundary
  - audit
---

# Engineering Governance Decision Procedure

## 1. Purpose

This procedure defines the common method by which Engineering Governance
evaluates a decision-ready package, selects a disposition, records an
attributable decision, and routes only the effects explicitly authorized by
that decision.

It closes the procedural interface between technical preparation or
qualification and controlled decision recording or execution. It does not
originate Governance authority, qualify its own subject, publish a controlled
record, execute engineering work, or activate a baseline.

## 2. Scope

This procedure applies when an authorized Governance decision is required for:

- a controlled-document publication proposal;
- a Governance Publication Disposition Record;
- a lifecycle proposal;
- an exception, deferral, residual risk, or condition;
- a Governance Resolution subject;
- a qualification or stabilization recommendation;
- a baseline eligibility or designation proposal; or
- an engineering-execution proposal reserved to Engineering Governance.

It governs decision evaluation and issuance. PROC-0002 continues to own EGR
construction, approval, activation, supersedence, and archival. PROC-0005 owns
controlled publication. PROC-0006 owns qualification. PROC-0007 owns
stabilization and routing. PROC-0001 owns EWO execution when applicable.

## 3. Governing Records

Apply the current valid revisions of:

- CHAR-0001 — Engineering Charter;
- POL-0001 — Engineering Governance Policy;
- STD-0000 — Engineering Governance Documentation Architecture;
- STD-0001 — Engineering Document Lifecycle Standard;
- STD-0002 — Engineering Document Persistence Standard;
- SPEC-0001 — Controlled Document Model;
- EDR-0002 — Engineering Authority Model;
- PROC-0002 — Engineering Governance Resolution Procedure;
- PROC-0005 — Controlled Document Publication Procedure;
- PROC-0006 — Governance Qualification Procedure; and
- PROC-0007 — Governance Stabilization Procedure.

EDR-0003 may define a transaction envelope and execution architecture for an
already-made decision. It does not replace the decision authority or this
procedure's human-governance decision controls.

## 4. Decision Principles

1. **Superior authority controls.** A decision shall remain within authority
   delegated through CHAR-0001 and applicable controlled records.
2. **Evidence informs; Governance decides.** Qualification, validation,
   recommendations, and repository access do not select a Governance
   disposition.
3. **One decision subject.** The decision shall bind to an exact subject,
   revision or fingerprint, scope, and requested effects.
4. **Attribution is mandatory.** The decision shall identify the natural
   person or controlled Governance body exercising authority, its role,
   authority reference, and decision timestamp.
5. **State domains remain separate.** Governance disposition, lifecycle
   state, publication outcome, qualification result, persistence state,
   baseline state, and implementation authority shall not be inferred from
   one another.
6. **Silence denies advancement.** Missing, ambiguous, or conflicting
   authority or evidence stops routing without creating a rejection.
7. **Historical meaning is preserved.** Later decisions supersede through
   controlled lineage and never rewrite prior decisions.

## 5. Roles and Authority

| Role | Responsibility | May decide | Shall not infer |
| --- | --- | --- | --- |
| Engineering Governance Decision Maker | Review the complete decision package and exercise delegated Governance authority. | Disposition, accepted conditions or exceptions, requested lifecycle effects within authority, and explicitly bounded delegations. | Technical facts absent from evidence, publication success, or execution completion. |
| Decision Secretary | Verify package completeness and faithfully record the decision made. | Administrative completeness only. | Disposition, rationale, authority, exceptions, or downstream permission. |
| Technical or Qualification Reviewer | Supply findings, validation, qualification, risk, and recommendations. | Technical gate results within assigned authority. | Governance disposition, lifecycle approval, publication authorization, or implementation authority. |
| Decision Subject Owner | Provide the exact subject, requested effects, alternatives, and impact analysis. | Subject content within preparation authority. | Approval or acceptance. |
| Publication Authority or Executor | Consume an Approved decision only when separately named and authorized. | Operational execution within the exact publication boundary. | Governance approval, lifecycle approval, or implementation authority. |
| Engineering Executor | Consume the identity-bound submitted WOP within its exact scope. | Bounded execution choices under that scope. | Scope expansion or authority from a derived approval/publication record. |
| Auditor | Reconstruct authority, inputs, decision, routing, and outcomes. | Audit findings. | Modification or ratification of the decision. |

One actor may hold multiple roles only when the applicable authority permits it
and the decision record declares the combination. Repository credentials,
authorship, ownership metadata, or session identity alone do not prove
Governance decision authority.

## 6. Decision Identity and Attribution

Every issued decision shall contain:

- a unique decision identifier;
- decision type and exact subject identity;
- exact subject revision, fingerprint, or immutable review locator;
- decision maker's attributable identity;
- Governance role or body represented;
- authority reference and applicable delegation limits;
- decision timestamp in ISO 8601 with offset or `Z`;
- decision-effective time when different from the decision timestamp;
- disposition and rationale;
- evidence reviewed and evidence version or locator;
- conditions, exceptions, deferrals, and residual risks;
- explicitly authorized and denied effects;
- expiry, revocation, or supersedence rules when applicable; and
- required downstream route.

An approval identity shall resolve to a natural person or a controlled
Governance body whose authorized membership and decision rule are
reconstructable. A tool name, generic agent, repository account, document
owner, or unverified free-text label is insufficient by itself.

The timestamp records when the decision was actually made. It shall not be
backdated to a review, preparation, or qualification event. Automation may
capture a timestamp after the decision but shall preserve the distinction and
record the capture time separately when material.

## 7. Required Decision Package

Before deliberation, the Decision Secretary shall verify:

1. the question requiring decision;
2. the exact subject and frozen fingerprint or locator;
3. superior authority and decision-maker authority;
4. requested disposition and all alternatives;
5. constitutional, architectural, lifecycle, and repository impact;
6. validation and qualification evidence;
7. findings, blockers, residual risks, and unresolved disagreements;
8. requested conditions, exceptions, and deferrals;
9. affected controlled records and downstream consumers;
10. exact requested lifecycle, publication, baseline, and execution effects;
11. proposed publication boundary when publication is requested;
12. rollback, expiry, revocation, and supersedence considerations; and
13. the authoritative record and route that will preserve the decision.

The package shall identify missing evidence rather than substitute assumptions.
A materially changed subject invalidates the package and requires renewed
technical review as applicable.

## 8. Decision Criteria

Engineering Governance shall evaluate:

- jurisdiction and delegated authority;
- constitutional and subordinate-governance consistency;
- evidence sufficiency, integrity, attribution, and currency;
- technical qualification and any divergence from recommendations;
- complete-publication or complete-effect scope;
- lifecycle and historical-integrity effects;
- repository identity, boundary, and persistence expectations;
- risks, alternatives, conditions, exceptions, and deferrals;
- operational and implementation consequences;
- auditability and deterministic reconstruction; and
- whether the requested effects can be safely separated and authorized.

Governance shall document rationale for material divergence from a technical
recommendation. It shall not convert an unperformed validation or repository
transaction into evidence by accepting its expected result.

## 9. Dispositions

### 9.1 Approved

Use `Approved` only when the exact subject and all mandatory requested effects
are acceptable without unresolved pre-execution Governance conditions.

The decision shall state which lifecycle effects are approved and whether any
publication or engineering execution authorization is also granted. Approval
alone grants neither unless the same decision explicitly contains the required
separate authorization fields and the governing framework permits that
combination.

### 9.2 Approved with Conditions

Use `Approved with Conditions` only when Governance accepts the subject but
requires explicit conditions that are objectively verifiable.

Each condition shall identify its owner, required evidence, due or expiry
rule, whether it is precedent or subsequent, and the effect of failure. A
condition precedent blocks the affected downstream action until verified. A
condition subsequent shall not be used to waive a mandatory precondition.

The decision shall state whether publication is authorized immediately,
authorized only after independent condition verification, or not authorized.

### 9.3 Revision Required

Use `Revision Required` when correctable changes or missing evidence prevent
approval of the exact subject. The decision shall list every blocking finding,
required correction, governing authority, permitted remediation scope,
required revalidation, and resubmission route.

Revision Required authorizes no publication, lifecycle transition, baseline
effect, or implementation. Bounded preparation may continue only under valid
preparation or remediation authority.

### 9.4 Rejected

Use `Rejected` when Governance determines that the proposal shall not proceed
within its present identity and authority. The decision shall state rationale,
scope, historical treatment, and whether a materially different future
proposal is permitted.

Rejected terminates the current decision subject. It does not authorize
removal of history, reversal of already-completed effects, or corrective work.

## 10. Accepted Exceptions and Deferrals

An accepted exception shall identify:

- the exact requirement and governing record;
- why the exception is within Governance authority;
- evidence and alternatives considered;
- bounded subject, duration, and expiry;
- risk owner and residual risk;
- compensating controls;
- monitoring and closure evidence; and
- effects that remain prohibited.

Governance shall not accept an exception to superior authority it does not
possess, fabricate missing evidence, declare an unperformed transaction
complete, or use an exception to merge Governance, publication, and execution
authority.

A deferral records future work and preserves the current limitation. It does
not satisfy a condition precedent or authorize the deferred work.

## 11. Publication Authorization

A decision concerning controlled publication shall explicitly state one of:

- `PUBLICATION_AUTHORIZED`;
- `PUBLICATION_AUTHORIZED_AFTER_CONDITIONS`; or
- `PUBLICATION_NOT_AUTHORIZED`.

Authorization shall identify:

- exact approved fingerprints or immutable locators;
- included and excluded paths;
- lifecycle and metadata effects already approved;
- index and relationship effects;
- authorized repository baseline and executor;
- commit, tag, push, and external-publication permissions individually;
- accepted exceptions and conditions;
- termination or expiry criteria; and
- required PROC-0005 evidence and post-publication verification.

Publication authorization permits only the named repository transaction. It
does not certify that publication occurred and does not authorize engineering
implementation.

## 12. Engineering Execution Authorization

Engineering execution conditions are a WOP scope and safety concern, not a
mandatory second operator grant. The submitted WOP shall identify exact scope,
executor or eligible role, environment, constraints, evidence, validation,
expiry, and stop conditions. Any approval boundary it explicitly declares
remains a separate gate within that WOP.

A GPDR, published procedure, lifecycle approval, publication commit, baseline
eligibility decision, or successful qualification does not by itself authorize
engineering execution. When an Active EWO or another controlled execution
record is required, the decision routes to that mechanism and does not replace
it.

## 13. Decision Workflow

```text
Decision Package Intake
        ↓
Identity and Authority Verification
        ↓
Evidence Sufficiency Review
        ↓
Governance Deliberation
        ↓
Disposition Selection
        ↓
Attributable Decision Capture
        ↓
Independent Completeness Check
        ↓
Controlled Recording and Routing
        ↓
Outcome Reconciliation and Audit
```

### Stage 1 — Intake

Assign or verify the decision identity, register the question, preserve the
received package, and verify that no competing decision is active.

### Stage 2 — Authority Verification

Resolve the decision maker, authority chain, jurisdiction, delegation limits,
and conflicts of interest. Stop if any element is missing or ambiguous.

### Stage 3 — Evidence Sufficiency

Verify the package against section 7. Missing mandatory evidence routes to a
non-decision `DECISION_BLOCKED` intake outcome. That outcome is not Revision
Required or Rejected because Governance has not selected a disposition.

### Stage 4 — Deliberation

Review the criteria in section 8, alternatives, dissent, and requested effects.
The record shall distinguish evidence, inference, recommendation, and decision.

### Stage 5 — Decision Capture

Engineering Governance selects one section 9 disposition and records all
section 6 fields. Conditions, exceptions, publication authorization, and
execution authorization shall be explicit; omission means not authorized.

### Stage 6 — Completeness Check

An authorized secretary or independent checker verifies faithful capture,
attribution, timestamp, subject fingerprint, internal consistency, and routing.
The checker does not change the decision. A capture defect returns for
correction by the decision maker without silently altering meaning.

### Stage 7 — Controlled Recording

Use PROC-0002 when the decision requires an EGR. A GPDR may carry the decision
only when the applicable controlled architecture establishes it as an
authoritative decision record or an existing authoritative decision is
unambiguously incorporated by reference. Until then, a GPDR is a decision
package or evidence view and shall not self-approve.

Any controlled decision record follows STD-0001, STD-0002, SPEC-0001, and
PROC-0005 for lifecycle and publication. The decision may exist before its
repository publication only when the authority model permits an attributable
external Governance decision; pending persistence shall remain explicit.

### Stage 8 — Routing

Route only explicitly authorized effects. Publication routes to PROC-0005.
Qualification routes to PROC-0006. Stabilization routes to PROC-0007.
Engineering work routes to the applicable controlled execution mechanism.

### Stage 9 — Outcome Reconciliation

Record downstream outcomes without changing the Governance decision:
publication success or failure, qualification result, lifecycle status,
baseline designation, implementation status, conditions, exceptions, expiry,
and incidents. A failed transaction does not retroactively change Approved to
Rejected.

## 14. Audit and Traceability

The audit trail shall preserve:

- received and final package identities;
- subject fingerprints and repository baseline;
- authority and identity verification evidence;
- reviewed evidence and qualification state;
- participants, roles, conflicts, and recusals;
- deliberation rationale and material dissent;
- decision identity, disposition, timestamp, and effective time;
- conditions, exceptions, deferrals, and authorizations;
- completeness-check result;
- controlled decision locator and publication status;
- every downstream route and observed outcome; and
- supersedence, revocation, expiry, or incident evidence.

Audit evidence shall be attributable, immutable where required, minimally
sufficient, and free of secrets or personal data not required for
accountability. Derived summaries shall resolve to authoritative evidence.

## 15. Stop Conditions

Stop without issuing or routing a decision when:

- decision authority or attributable identity cannot be verified;
- the subject, fingerprint, question, or requested effects are ambiguous;
- required evidence is missing, stale, contradictory, or materially changed;
- the requested effect exceeds delegated authority;
- a competing decision or successor exists;
- conditions or exceptions cannot be objectively verified;
- publication or execution authority would be implied rather than explicit;
- the decision record would falsely claim lifecycle or persistence state;
- required audit evidence cannot be preserved; or
- constitutional, lifecycle, repository, or authority consistency fails.

Record `DECISION_BLOCKED`, the evidence, and the exact resumption requirement.
This operational status is not a Governance disposition.

## 16. Supersedence, Revocation, and Expiry

Only an attributable Governance decision under valid authority may supersede,
revoke, or extend a decision. Preserve the prior decision, effective interval,
completed downstream effects, and new decision locator. Do not rewrite history
or assume that revocation reverses completed repository or engineering work.

## 17. Validation and Success Criteria

This procedure is satisfied for a decision when:

- authority and identity are verified;
- one exact subject and evidence package are bound to the decision;
- one disposition is explicit;
- conditions, exceptions, deferrals, and authorizations are unambiguous;
- publication and engineering execution remain separately controlled;
- the decision is faithfully recorded and routed;
- every state domain remains truthful;
- the audit trail reconstructs the decision; and
- no unauthorized effect occurs.

## 18. Draft Adoption Boundary

Version 0.1 is a Draft design produced for review. It is not Active, Approved,
published, or operational authority. It shall not be used to issue the pending
GPDR decision until it has completed controlled review, approval, lifecycle,
index, publication, and qualification processes under existing authority.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 0.1 | 2026-07-22 | Initial Draft defining the common attributable Engineering Governance decision procedure and preserving qualification, publication, lifecycle, baseline, and execution boundaries. |
