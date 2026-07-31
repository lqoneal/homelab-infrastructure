---
document_id: TPL-0002
title: Completion Report Template
version: 2.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-30
phase: Engineering Execution Interface Standardization
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0003
  - PROC-0001
  - TPL-0001
  - EGR-000002
  - EWO-000018
tags:
  - governance
  - template
  - completion-report
  - evidence
  - engineering-operating-system
---

# Completion Report Template

## Instantiation Rule

Every instantiated report shall begin with exactly the following heading. No
preface, status, certification, alternate title, or other report content may
precede it.

```text
# Completion Report
```

Complete sections in the order defined below. Use `Not Applicable` with a
short rationale where a mandatory section does not apply. Do not omit the
section. Historical Completion Reports remain valid under their originating
template revision.

The report contains mission delta only. Reference governing procedures and
unchanged baselines; do not reproduce them. Include only the starting context
needed to explain the delta, actions performed, artifacts changed or reviewed,
terminal verification, reconciliation, remaining work, and disposition.

## Transaction Identification

Engineering Operating System:

`<Engineering Operating System>`

Engineering Work Order or Authority:

`<Identifier and revision>`

Operational Alpha Baseline / Authority Record / Resolution Receipt:

`<Baseline identifier and immutable locator; exact Authority Record; EMM receipt digest, or Not Applicable>`

Mission and Phase:

`<Mission and phase identifiers>`

Mission Classification:

`<Category A | Category B | Category C>`

Execution Date:

`<Date>`

Execution Agent:

`<Agent>`

## Execution Summary

Purpose:

`<Authorized purpose>`

Authorized Scope:

`<Authorized scope>`

Executed Scope:

`<Scope actually executed>`

Mission Status:

`<PASS | WARNING | FAIL | BLOCKED>`

Execution Status:

`<PASS | WARNING | FAIL>`

Scope Compliance:

`<Authorized activities, unauthorized activities, and deviations>`

Definition of Done and Acceptance Criteria:

`<MET | PARTIALLY MET | NOT MET, with assessment>`

Stop Conditions Encountered:

`<None or description>`

## Repository State

Starting Repository State:

`<Repository, branch, commit, working tree, index, upstream, or Not Applicable>`

Ending Repository State:

`<Repository, branch, commit, working tree, index, upstream, or Not Applicable>`

Repository Integrity:

`<Result and evidence or Not Applicable>`

Runtime State:

`<Starting and ending runtime state or Not Applicable>`

## Commands Executed

`<Relevant non-sensitive command and activity summary, or Not Applicable>`

Record terminal status where it affects conclusions. Do not expose secrets or
replace evidence with unnecessary transcript volume.

## Artifacts Reviewed

Controlled Records:

`<Identifiers and revisions>`

Evidence and Other Authorized Inputs:

`<Authoritative locators or Not Applicable>`

## Repository Changes

Files Added, Modified, or Removed:

`<List or None>`

Commits or Tags Created:

`<Locators or None>`

Runtime Changes:

`<Summary or None>`

Historical Records Preserved:

`<Summary>`

## Validation Activities

For each validation activity record:

- validator identity or version;
- scope;
- whether output is partial or terminal;
- terminal exit status when available;
- duration when available;
- individual results; and
- complete aggregate result.

Never infer validator success from partial output or from a pipeline or later
command that masks the validator's terminal status.

## Deliverables Produced

`<Deliverable identity, status, and authoritative locator>`

## Findings

For each finding record identifier, description, supporting evidence, and
impact. Use `None` when the execution produced no findings.

## Analysis

`<Evidence-based interpretation of findings, limitations, and impact>`

## Recommendations

`<Recommendations and supporting rationale, or None>`

Recommendations do not authorize their own implementation.

## Final Certification

Certification Question:

`<Exact transaction-specific question or Not Applicable>`

Certification Answer:

`<One allowed answer or Not Applicable>`

Supporting Rationale:

`<Objective evidence>`

No final certification may appear before this section.

## Follow-on Work

`<Separately authorized work, deferred evaluation, authority limitations, or None>`

## Governance Conformance Review

### Authority Verification

`<PASS, FAIL, or BLOCKED with governing authority evidence>`

### Mission Scope Compliance

`<Assessment against authorized scope and prohibitions>`

### Trust Boundary Verification

`<Assessment of repository, runtime, secret, network, host, and external boundaries>`

### Controlled Document Compliance

`<Assessment of lifecycle, ownership, relationships, whole-document revision, and traceability>`

### Authority Circumvention Assessment

`<No circumvention detected | Potential circumvention identified | Confirmed authority violation>`

For potential or confirmed circumvention, record the affected authority or
control, condition or action, provenance, impact, recommendation, and required
follow-up authority.

### Governance Gap Assessment

`<Identified gaps, exceptions, ambiguities, or None>`

### Documentation Requirement

`<Required | Not required, with disposition evidence>`

### Overall Governance Status

`<CONFORMANT | CONFORMANT WITH FOLLOW-UP REQUIRED | NONCONFORMANT | BLOCKED>`

Mission completion shall not be reported until every Governance Conformance
Review item is complete.

## Engineering Governance Notes

To be completed by Engineering Governance.

Disposition:

`<Disposition>`

Acceptance:

`<Accepted | Rejected | Requires Revision>`

Governance Comments:

`<Comments>`

## References

Governing Engineering Work Order or Authority:

`<Reference>`

Applicable Engineering Evidence:

`<References>`

Applicable Engineering Records:

`<References>`

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-09 | Initial Engineering Completion Report Template established. |
| 1.1 | 2026-07-17 | Standardized the exact Completion Report title and mandatory Governance Conformance Review under EGR-000002 and EWO-000018. |
| 1.2 | 2026-07-18 | Institutionalized the execution-first report structure, ordered results and certification sections, repository and validation evidence capture, applicability handling, and authoritative reusable reporting terminology. |
| 1.3 | 2026-07-28 | Required mission-delta-only reports that reference rather than duplicate reusable repository execution knowledge. |
