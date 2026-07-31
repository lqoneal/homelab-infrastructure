---
document_id: STD-0003
title: Operational Alpha Work Authorization Standard
version: 2.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-30
phase: Engineering Execution Interface Standardization
domain: Engineering Governance
classification: Engineering Standard
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - POL-0001
  - PROC-0001
  - EWO-000012
  - EGR-000002
  - EWO-000018
tags:
  - governance
  - work-order
  - engineering-standard
  - execution
  - engineering-operating-system
mission_assurance_requirements:
  - id: MA-WOP-001
    language_version: '1.0'
    phase: preflight
    description: WOP applicability and supporting data resolve.
    assertion:
      any:
        - all:
            - selector: state.wop.applicability
              operator: equals
              value: applicable
            - selector: state.wop.references
              operator: not_empty
        - all:
            - selector: state.wop.applicability
              operator: equals
              value: not_applicable
            - selector: state.wop.reason
              operator: not_empty
---

# Operational Alpha Work Authorization Standard

## Operational Alpha convergence migration

For Operational Alpha, SPEC-0014 is the controlling execution-authority
model. The legacy Active Engineering Work Order / Work Registry Mission
Contract pair is retained only for historical traceability and shall not be
used to resolve a new Operational Alpha action. The current authority is the
version-pinned Authority Record and published Implementation WOP resolved from
EMM under SPEC-0014. A `READY` WOP is non-executing; only a resolver-confirmed
Authority Record may make a WOP `ACTIVE`.

## Purpose

This standard defines the mandatory requirements for all Engineering Work Orders activated under the Engineering Operating System.

It establishes what every Engineering Work Order shall contain, what authority it conveys, and the minimum requirements for engineering execution.

This standard defines what an Engineering Work Order must require.

It does not define operational execution procedures or document formatting.

---

## Scope

This standard applies to every Engineering Work Order executed within the Engineering Operating System.

---

## Engineering Work Order Principles

### Principle 1 — Explicit Authorization

Operational Alpha work shall be performed only under an `ACTIVE` Implementation
WOP whose specific action is resolved by a valid Authority Record.

---

### Principle 2 — Mission Specificity

Each Engineering Work Order shall authorize only one defined engineering mission or clearly bounded scope.

---

### Principle 3 — Defined Authority

Every Engineering Work Order shall explicitly define the authority granted to the implementation agent.

Authority not explicitly granted is prohibited.

---

### Principle 4 — Deterministic Execution

Every Engineering Work Order shall support deterministic execution and deterministic resume.

---

### Principle 5 — Evidence-Based Completion

Engineering Work Orders are completed through engineering evidence, not assumptions.

---

## Required Engineering Work Order Elements

Every Engineering Work Order shall include, at minimum:

* mission classification under PROC-0001;

* identifier;
* revision;
* status;
* title;
* mission;
* phase;
* scope;
* purpose;
* Engineering Governance intent;
* authority model;
* resume policy;
* communication contract;
* success criteria;
* stop conditions;
* Completion Report requirements;
* references.

---

## Governance Requirements

Every Engineering Work Order shall:

* identify the governing policy;
* identify applicable standards;
* identify applicable procedures;
* identify applicable templates.

The Engineering Work Order shall not redefine those documents.

---

## Authority Requirements

Every Engineering Work Order shall define:

* operational authority;
* engineering authority;
* prohibited actions;
* escalation requirements.

Authority shall be explicit.

---

## Resume Requirements

Every Engineering Work Order shall support deterministic resume.

Resume requirements shall include:

* verification of the governing work order revision;
* operational inventory;
* operational preparation;
* baseline verification;
* identification of the first incomplete engineering phase.

---

## Communication Requirements

Every Engineering Work Order shall require the implementation agent to report:

* observations;
* supporting evidence;
* mission impact;
* recommendations.

Implementation agents shall not infer Engineering Governance intent.

---

## Evidence Requirements

Every Engineering Work Order shall require production of sufficient engineering evidence to permit Engineering Governance to determine whether the mission objectives have been achieved.

---

## Completion Report Requirements

Every delivered report produced after execution of an Engineering Work Order
shall be a Completion Report and shall begin with exactly:

```text
# Completion Report
```

No preface, status, certification, alternate title, or other report content may
precede that heading. An Engineering Work Order shall not redefine the common
report structure or duplicate reusable reporting instructions owned by
TPL-0002.

### Execution and Results Separation

The Completion Report shall first identify the transaction and report what was
executed. Its execution record shall address repository state, relevant
commands or activities, artifacts reviewed, repository and runtime changes,
validation activities, deliverables, scope compliance, mission status,
completion criteria, and applicable evidence.

Only after the execution record is complete shall the report present, in this
order:

1. Findings;
2. Analysis;
3. Recommendations;
4. Final Certification; and
5. Follow-on Work.

The Governance Conformance Review shall follow these sections and remains a
mandatory part of mission completion. TPL-0002 is the authoritative reusable
structure and terminology for the complete report.

### Final Certification

When a mission requires a certification answer, the exact transaction-specific
question and allowed answer set shall be supplied by its Engineering Work
Order. The answer shall appear only within `Final Certification`. Findings,
analysis, recommendations, validation results, and ordinary status values are
not final certification.

Mandatory sections that do not apply shall state `Not Applicable` with a short
rationale; they shall not be silently omitted.

The Governance Conformance Review is mandatory for every Codex engineering
mission and shall contain:

* Authority Verification;
* Mission Scope Compliance;
* Trust Boundary Verification;
* Controlled Document Compliance;
* Authority Circumvention Assessment;
* Governance Gap Assessment;
* Documentation Requirement; and
* Overall Governance Status.

Authority Circumvention Assessment shall use exactly one of:

* `No circumvention detected`;
* `Potential circumvention identified`; or
* `Confirmed authority violation`.

Mission completion shall not be reported until this review is complete.

## Mission Classification Requirements

Every Engineering Work Order shall identify exactly one primary mission
classification defined by PROC-0001:

* Category A — Repository Engineering Work;
* Category B — Local Engineering Environment Work; or
* Category C — Operational / Diagnostic Work.

The classification determines risk-proportional initiation gates but never
creates or expands authority. Mixed-scope work uses the most restrictive
applicable category unless the Work Order explicitly separates independently
gated phases.

---

## Stop Conditions

Every Engineering Work Order shall define explicit stop conditions.

Execution shall stop when:

* authority is exceeded;
* Engineering Governance authorization is required;
* repository integrity is compromised;
* deterministic execution can no longer be maintained;
* approved stop conditions are encountered.

---

## Lifecycle Requirements

Engineering Work Orders shall comply with:

* Engineering Document Lifecycle Standard;
* Engineering Document Persistence Standard.

Implementation agents verify that the Implementation WOP is `ACTIVE` and that
the applicable SPEC-0014 Authority Record resolves before execution. Neither
the WOP alone nor its `READY` state conveys execution authority.

Lifecycle state transitions remain the responsibility of Engineering Governance.

## Repository Mission Contract

Every mission shall have exactly one current Work Registry work item identifying
its stable mission ID, objective, lifecycle state, owner, authority reference,
project, phase, completion criteria, relationships, and transition history.
When bounded effects require a WOP, that WOP augments the work item with
explicit authority, prohibitions, dependencies, validation additions, and stop
conditions.

Together these records form the repository Mission Contract. They shall let an
execution agent determine current mission, phase, authority, outstanding
objective, completion criteria, and remaining lifecycle work without prompt
history. Duplicated or conflicting current contracts fail closed. The derived
Mission Snapshot exposes the contract but is not an authority record.

---

## Compliance

Engineering Work Orders shall comply with:

* Engineering Governance Policy;
* Engineering Governance Documentation Architecture;
* Engineering Document Lifecycle Standard;
* Engineering Document Persistence Standard.

---

## References

This standard references:

* GEN-0001 — Engineering Operating System Genesis Record
* STD-0000 — Engineering Governance Documentation Architecture
* STD-0001 — Engineering Document Lifecycle Standard
* STD-0002 — Engineering Document Persistence Standard
* POL-0001 — Engineering Governance Policy
* PROC-0001 — Engineering Work Order Execution Procedure

---

## Success Criteria

This standard is complete when every Engineering Work Order activated under the Engineering Operating System:

* conveys explicit authority;
* defines mission scope;
* supports deterministic execution;
* supports deterministic resume;
* requires sufficient engineering evidence;
* provides explicit completion requirements;
* defines explicit stop conditions;
* complies with the Engineering Governance framework.

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Work Order Standard established. |
| 1.1 | 2026-07-10 | Established Active as the Engineering Work Order execution-authority lifecycle state under EWO-000012. |
| 1.2 | 2026-07-17 | Required repository-governed mission classification, the exact Completion Report title, and mandatory Governance Conformance Review under EGR-000002 and EWO-000018. |
| 1.3 | 2026-07-18 | Institutionalized execution-first Completion Reports, mandatory execution/results separation, ordered findings through follow-on work, Final Certification placement, and TPL-0002 structural ownership. |
| 1.4 | 2026-07-28 | Standardized the repository Mission Contract and its Work Registry/WOP composition for deterministic discovery, execution, and resume. |
| 2.0 | 2026-07-30 | Migrated Operational Alpha authority to SPEC-0014's EMM-resolved Authority Record and Implementation WOP model; legacy EWO/Work Registry resolution is historical only for Operational Alpha. |
