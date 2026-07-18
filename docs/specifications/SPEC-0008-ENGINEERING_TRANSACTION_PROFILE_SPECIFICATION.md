---
document_id: SPEC-0008
title: Engineering Transaction Profile Specification
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Engineering Transaction Profile Institutionalization
domain: Engineering Governance
classification: Engineering Specification
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Engineering Governance Authorization - Engineering Transaction Profile Implementation
approval_date: 2026-07-18
persistence_status: Persisted
source_of_truth: true
information_scope: Engineering Transaction Profile architecture, representation, compatibility, deterministic resolution, lifecycle, and baseline profile
declared_deferrals:
  - runtime-profile-resolution
  - additional-transaction-profiles
  - transaction-profile-registry
  - transaction-profile-document-class
  - egas-ekrs-emls-orchestration-integration
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
  - type: depends_on
    target: PROC-0004
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: STD-0004
  - type: related_to
    target: TPL-0001
  - type: related_to
    target: TPL-0002
  - type: related_to
    target: SPEC-0007
  - type: indexed_by
    target: DOC-0001
tags:
  - engineering-transaction-profile
  - compatibility
  - deterministic-resolution
  - authority-preservation
  - baseline-profile
---

# Engineering Transaction Profile Specification

## Purpose

This specification defines the architecture and representation of Engineering
Transaction Profiles. An Engineering Transaction Profile coordinates a
compatible, versioned set of references to authoritative engineering behavior.
It does not own, duplicate, or redefine the semantics of those behaviors.

This revision defines exactly one conservative baseline profile representing
the qualified repository-controlled publication behavior already exercised by
governed Engineering transactions.

## Scope

This specification owns:

- the ETP model and representation;
- component hierarchy;
- selection and resolution semantics;
- compatibility and override constraints;
- lifecycle and qualification requirements;
- resolved-manifest requirements; and
- the baseline Transaction Profile.

It does not implement runtime resolution, create a profile registry or new
document class, authorize execution, or implement additional profiles.

## Authority Boundary

Engineering Governance selects an ETP explicitly through the Engineering
Authorization Kernel or authorizes use of one unambiguous controlled default.
An ETP cannot grant authority, expand scope, approve exceptions, accept risk,
activate an Engineering Work Order, or issue certification.

PROC-0004 owns handoff construction and consumes ETPs. PROC-0001 owns execution
after activation. STD-0003 owns normative Engineering Work Order semantics.
TPL-0001 owns structure, and TPL-0002 owns Completion Report structure.

## Profile Hierarchy

Every ETP coordinates these components:

1. construction;
2. execution;
3. handoff structure;
4. completion-report structure;
5. lifecycle;
6. persistence;
7. normative EWO semantics;
8. validation;
9. publication;
10. synchronization;
11. resume;
12. qualification;
13. notification; and
14. automation.

A component is a versioned reference or a bounded data definition. Component
semantics remain with the referenced controlled owner.

## Profile Representation

An ETP shall contain:

- stable `profile_id` and monotonic `revision`;
- lifecycle `status`;
- owner and approval reference;
- supported mission classifications and transaction effects;
- a versioned `components` map;
- compatibility constraints;
- permitted transaction additions;
- prohibited overrides;
- qualification requirements; and
- explicit deferrals.

Profile identifiers are specification-internal governed identities in Version
1.0. They are not a new controlled-document class or prefix.

## Selection Rules

Profile selection precedence is:

1. superior Governance authority;
2. explicit ETP selection in the Authorization Kernel;
3. an approved deterministic default mapping authorized by the Kernel; and
4. no selection.

Exactly one Active compatible profile shall resolve. No match, multiple
matches, an inactive profile, or an indeterminate match fails closed and
requires Engineering Governance disposition.

## Deterministic Resolution Algorithm

1. Read the authoritative Authorization Kernel.
2. Resolve the selected profile identity or authorized default mapping.
3. Require exactly one candidate.
4. Resolve its Active revision.
5. Resolve each controlled component identity and version.
6. Verify mission-classification and transaction-effect compatibility.
7. Verify required and prohibited components.
8. Apply transaction additions only when both the Kernel and profile permit
   them.
9. Reject prohibited overrides and any change to Governance-owned content.
10. Apply the most restrictive compatible additive requirement.
11. execute PROC-0004 Authority Preservation Validation.
12. Produce and freeze the resolved manifest for the submitted EWO revision.

Resolution shall be identical for identical authoritative inputs. Derived
state, conversation history, prior Work Orders, or generated views shall not
override a controlled profile or component owner.

## Compatibility Rules

Compatibility shall validate:

- profile and component lifecycle state;
- exact or minimum component revisions;
- mission classification;
- repository interaction and publication effects;
- validation and qualification requirements;
- synchronization and checkpoint requirements;
- mutually exclusive selections;
- explicit deferrals; and
- permitted additions and prohibited overrides.

Compatibility failure is terminal for construction until the inputs or
Governance disposition change.

## Inheritance and Overrides

An ETP may inherit only from an explicitly identified Active base profile.
Inheritance shall be acyclic and shall preserve the base profile's
prohibitions, authority boundary, and minimum qualification requirements.

Version 1.0 defines no inherited or derived profiles. Transaction-specific
additions may strengthen validation, evidence, synchronization, or stop
conditions when the Kernel authorizes them. They shall not broaden authority,
enlarge scope, remove a prohibition, weaken qualification, approve an
exception, or enlarge publication effects.

## Resolved Profile Manifest

Every ETP-driven handoff shall record a frozen manifest containing:

- profile identity and revision;
- selection authority locator;
- every resolved component identity and revision;
- transaction-specific additions;
- compatibility result;
- Authority Preservation result;
- unresolved ambiguity, which shall be empty for approval eligibility; and
- a deterministic manifest fingerprint or authoritative locator.

The manifest is attributable construction evidence. It is not a source of
Governance Authority and cannot change after submission without a new EWO
revision and renewed Governance review.

## Lifecycle and Evolution

Profiles use the lifecycle established by STD-0001. Only an Active profile may
govern new handoff construction. A successor affects future construction only;
historical EWOs preserve their original explicit behavior or frozen manifest.

Profile activation requires:

- metadata and reference validation;
- compatibility and resolution validation;
- Authority Preservation fixtures;
- behavioral equivalence to the behavior it claims to represent;
- controlled-document and aggregate platform validation; and
- Engineering Governance approval.

Adding a profile, expanding applicability, or changing transaction effects
requires separate authority and qualification.

## Baseline Transaction Profile

The following YAML block is the sole authoritative baseline profile definition
in this revision. Validation tooling consumes this block as a controlled test
input. It is not a runtime registry.

```yaml etp-profile
profile_id: ETP-BASELINE-CONTROLLED-PUBLICATION
revision: 1.0
status: Active
owner: Engineering Governance
approval_reference: Engineering Governance Authorization - Engineering Transaction Profile Implementation
mission_classifications:
  - Category A
transaction_effects:
  repository_changes: required
  controlled_document_publication: permitted-when-kernel-authorized
components:
  construction: PROC-0004@1.1
  execution: PROC-0001@1.8
  handoff_structure: TPL-0001@1.6
  completion_report_structure: TPL-0002@1.2
  lifecycle: STD-0001
  persistence: STD-0002
  normative_ewo_semantics: STD-0003@1.3
  state_and_resume: STD-0004
  validation: complete-repository-and-aggregate-platform
  publication: one-objective-atomic-repository-commit
  synchronization: directly-affected-controlled-and-operational-projections
  qualification: prepublication-and-clean-tree-postpublication
  notification: existing-qualified-behavior-only
  automation: deferred
compatibility:
  requires_clean_tree: true
  dirty_tree_exception: explicit-governance-authorization-required
  requires_authority_preservation: true
  requires_terminal_validator_status: true
  requires_postpublication_checkpoint: true
permitted_additions:
  - stronger-validation
  - additional-evidence
  - additional-synchronization
  - narrower-scope
  - additional-stop-condition
prohibited_overrides:
  - broaden-authority
  - enlarge-scope
  - remove-prohibition
  - weaken-validation
  - add-unapproved-exception
  - enlarge-publication-authority
qualification_requirements:
  - etp-schema-validation
  - deterministic-resolution-fixtures
  - authority-preservation-validation
  - historical-handoff-compatibility
  - controlled-document-validation
  - aggregate-engineering-platform-validation
deferrals:
  - runtime-resolution
  - additional-profiles
  - profile-registry
  - new-document-class
```

## Baseline Applicability

The baseline profile applies only to Category A repository transactions whose
Kernel authorizes repository modification and, where applicable, controlled
publication. It does not independently authorize publication or make itself a
default. The Kernel shall explicitly select it during the initial pilot.

Historical Engineering Work Orders remain valid without an ETP reference and
shall not be rewritten.

## Validation Requirements

Validation shall prove:

- schema completeness;
- unique profile identity;
- exact component ownership and resolvability;
- deterministic unique resolution;
- fail-closed absent, ambiguous, inactive, and incompatible selection;
- prohibited-override rejection;
- Authority Preservation enforcement;
- frozen-manifest completeness;
- historical compatibility; and
- behavioral equivalence with the qualified manual baseline.

## Automation Boundary

Future qualified services may resolve documents, compare compatibility,
populate structural fields, and generate a manifest. Automation shall not
select authority absent a controlled rule, approve scope, accept risk, approve
exceptions, activate an EWO, or issue certification.

Runtime EGAS, EKRS, EMLS, notification, and orchestration integration is
deferred.

## References

- CHAR-0001 — Engineering Charter
- POL-0001 — Engineering Governance Policy
- STD-0000 — Engineering Governance Documentation Architecture
- STD-0001 — Engineering Document Lifecycle Standard
- STD-0002 — Engineering Document Persistence Standard
- STD-0003 — Engineering Work Order Standard
- STD-0004 — Engineering State Freshness Standard
- PROC-0001 — Engineering Work Order Execution Procedure
- PROC-0004 — Engineering Handoff Construction Procedure
- TPL-0001 — Engineering Work Order Template
- TPL-0002 — Completion Report Template
- SPEC-0007 — Engineering Platform Construction Specification

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-18 | Established the ETP coordination model, deterministic fail-closed resolution, compatibility and lifecycle rules, frozen manifest, and one conservative baseline profile without creating a new document class or runtime service. |
