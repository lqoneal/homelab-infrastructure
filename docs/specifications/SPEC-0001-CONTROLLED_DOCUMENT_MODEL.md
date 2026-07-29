---
document_id: SPEC-0001
title: Controlled Document Representation Specification
version: 1.6
status: Draft
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-28
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Specification
source_of_truth: true
predecessor_revision: SPEC-0001@1.5
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
persistence_status: Pending
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: implements
    target: EDR-0002
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: related_to
    target: GEN-0001
  - type: related_to
    target: STD-0001
  - type: related_to
    target: STD-0002
  - type: related_to
    target: STD-0003
  - type: related_to
    target: PROC-0001
  - type: indexed_by
    target: DOC-0001
  - type: authorized_by
    target: EWO-000011
  - type: authorized_by
    target: EWO-000012
  - type: authorized_by
    target: EWO-000014
declared_deferrals:
  - repository-wide-metadata-rollout
  - legacy-metadata-migration
  - historical-locator-backfill
  - repository-wide-persistence-remediation
tags:
  - controlled-documents
  - document-representation
  - engineering-records
  - engineering-work-orders
  - engineering-operating-system
---

# Controlled Document Representation Specification

## 1. Purpose

This specification defines the authoritative repository-wide representation model for controlled documents within the Engineering Operating System (EOS).

It defines controlled-document metadata, approval representation, typed relationships, lifecycle representation, revision identity, revision lineage, supersedence, version and title semantics, repository placement, historical persistence, deterministic reconstruction, and validation.

This specification implements the documentation architecture established by STD-0000. It does not originate engineering authority, approve documents, perform lifecycle transitions, prescribe operational procedures, or execute repository-wide migration.

---

## 2. Scope

This specification applies to every repository-controlled engineering document, including:

* Charters and Genesis Governance Records;
* repository governance and indexes;
* policies, standards, specifications, procedures, and templates;
* Engineering Decision Records;
* Engineering Work Orders;
* Engineering Governance Findings and Resolutions;
* Evidence Packages and Completion Reports;
* project, infrastructure, service, asset, financial, milestone, validation, and other domain records.

It governs the representation of those records. Document-class responsibilities and governance precedence remain defined by CHAR-0001, POL-0001, and STD-0000.

Repository-wide metadata rollout, legacy migration, historical-locator backfill, persistence remediation, commit-strategy changes, and dependent-document revisions require separately authorized Engineering Work Orders.

---

## 3. Governance Foundation

### 3.1 Origin and Delegation of Authority

Production engineering authority originates solely with Lawrence O'Neal and is
exercised through authenticated principal `loneal` and the Zeus CLI.
Engineering Governance is the controlled governance function expressed
through CHAR-0001 and subordinate repository-controlled governance.

This specification is subordinate to CHAR-0001 and POL-0001 and conforms to STD-0000. No metadata field, repository operation, Git object, service, interface, or controlled record originates engineering authority.

### 3.2 Charter and Policy Precedence

CHAR-0001 is the highest foundational governing record within EOS.

POL-0001 is the highest policy-level normative record and remains subordinate to the Charter. Standards define mandatory rules, Specifications define models and architectures, Procedures define repeatable workflows, and Active Engineering Work Orders authorize bounded execution.

When a represented relationship conflicts with superior governance, superior
governance prevails and the record enters the Authority Restoration Principle
defined by SPEC-0011. Execution remains ineligible until controlled
reconciliation, validation, and normal authority re-resolution succeed.

### 3.3 Repository Authority

The repository is a governed, versioned publication of controlled records and supporting artifacts. Repository state does not independently create approval, lifecycle authority, Information Authority, or permission to execute engineering work.

Repository-controlled records operate only within authority delegated to their document class, lifecycle state, approved revision, and scope.

### 3.4 Governance Authority and Information Authority

Governance Authority is the delegated authority to establish governance direction, approve controlled records and lifecycle transitions, authorize bounded work, establish baselines, and accept engineering outcomes.

Information Authority identifies the controlled record that owns a defined engineering fact, decision, requirement, state, or evidence item within its delegated scope.

An Authoritative Engineering Record (AER) designation identifies Information Authority. AER is not a document class, lifecycle state, governance tier, approval, or execution authorization.

Metadata represents authority and information ownership; it does not create them.

### 3.5 Derived Engineering Views

Reports, dashboards, summaries, generated publications, AI responses, cached representations, search results, and command output are Derived Engineering Views unless established as controlled records through an authorized lifecycle.

Derived views shall identify or resolve to their authoritative sources. They possess neither Governance Authority nor Information Authority and shall not replace controlled records, approve changes, or expand an Engineering Work Order.

---

## 4. Representation Principles

### Principle 1 — Explicit Meaning

Identity, approval, lifecycle, authority, relationships, revision lineage, persistence, and deferrals shall be represented explicitly whenever required by this specification.

### Principle 2 — One Information Owner

Each governed engineering fact shall have one authoritative information owner. References and derived views do not acquire ownership through repetition or use.

### Principle 3 — Separation of Concerns

Lifecycle status, approval status, persistence status, Information Authority, and Governance Authority are distinct properties and shall not be inferred from one another.

### Principle 4 — Deterministic Validation

Equivalent controlled-record inputs shall produce equivalent validation results.

### Principle 5 — Historical Integrity

Approved revision history shall remain attributable and reconstructable. Missing historical persistence shall be declared rather than fabricated.

### Principle 6 — Backward-Compatible Adoption

Legacy records remain valid when registered or explicitly classified. New requirements apply through authorized rollout, not by silently invalidating existing records.

---

## 5. Controlled Document Structure

Every controlled document shall contain:

1. machine-readable Engineering Metadata;
2. a complete Document Body;
3. explicit Relationship Information;
4. a Revision History;
5. lifecycle-transition history when a transition has occurred and the transition is not represented in another authoritative record.

Markdown with YAML front matter is the current repository representation. Future storage technologies may be used when they preserve identical engineering meaning, authority, relationships, validation, and deterministic reconstruction.

---

## 6. Metadata Model

### 6.1 Core Identity Metadata

Every controlled document shall contain:

```yaml
document_id:
title:
version:
status:
owner:
created:
last_updated:
classification:
```

Meanings:

* `document_id` is the permanent document identity;
* `title` is the approved current title for the represented revision;
* `version` identifies the controlled content revision;
* `status` identifies the lifecycle state;
* `owner` identifies accountable ownership;
* `created` identifies initial creation date;
* `last_updated` identifies the current revision date;
* `classification` identifies the controlled document class or registered subtype.

### 6.2 Revision Metadata

Every new or revised record shall contain:

```yaml
predecessor_revision:
successor_revision:
```

The first revision uses `predecessor_revision: null`. A current revision without an approved successor uses `successor_revision: null`.

A class-specific `revision` field may supplement but shall not replace `document_id` and `version`.

### 6.3 Approval Metadata

Every Approved, Active, Superseded, or Archived revision shall contain:

```yaml
approval_status:
approval_authority:
approval_reference:
approval_date:
```

Allowed `approval_status` values are:

* `Pending` for Draft or Review content awaiting disposition;
* `Approved` for content approved by Engineering Governance;
* `Rejected` for content rejected and retained as a historical proposal;
* `Withdrawn` for a proposal withdrawn through authorized disposition.

`approval_authority` identifies the approving governance authority. `approval_reference` identifies the controlled Work Order, Resolution, or explicitly approved transitional authority. `approval_date` records the disposition date.

Approval metadata records a decision already made through Governance Authority. It does not confer approval by its presence.

### 6.4 Persistence Metadata

Every controlled revision shall contain:

```yaml
persistence_status:
```

Allowed values are:

* `Pending` — the complete current revision exists in the governed working publication but has no immutable Git locator;
* `Persisted` — the revision has a verified immutable historical locator;
* `Legacy` — the record predates the persistence model and remains governed through explicit registration;
* `Remediation Required` — required persistence evidence is missing or invalid.

Lifecycle authority and persistence status are independent. An explicitly approved transitional authority may activate a complete working-tree revision while persistence remains `Pending` when the same authority prohibits committing. Such a revision is operationally Active but shall not be represented as historically persisted, superseded, or fully baseline-qualified until persistence is completed or explicitly deferred.

### 6.5 Optional Context Metadata

The following fields may be used when applicable:

```yaml
revision:
phase:
domain:
source_of_truth:
information_scope:
declared_deferrals:
tags:
```

`source_of_truth` identifies the intended controlled source location. It does not override lifecycle, approval, or persistence state.

`information_scope` may define the knowledge for which the record is the authoritative information owner.

`declared_deferrals` identifies approved requirements intentionally postponed to a future authorized mission. Deferral metadata shall not conceal a failed mandatory requirement.

### 6.6 Metadata Extensions

Document-class-specific standards may require additional fields. Extensions shall have one defined meaning, shall not conflict with this model, and shall remain machine-readable.

---

## 7. Identifier, Version, and Title Semantics

### 7.1 Document Identity

Every controlled document has one permanent `document_id`. Identifiers shall not be reused.

### 7.2 Revision Identity

A revision identity is the tuple `document_id` and `version`, rendered as `document_id@version` when a single value is required.

### 7.3 Version Semantics

Version numbers follow semantic engineering revisions:

* Major — significant architectural or responsibility change;
* Minor — compatible engineering enhancement;
* Patch — correction without changing engineering intent.

Every complete revision shall use a new version and update Revision History.

### 7.4 Title Semantics

The title is stable descriptive identity but may change through an explicitly approved complete revision when the document responsibility has materially clarified or changed.

A title change shall:

* retain the permanent `document_id`;
* identify the previous and new titles in Revision History;
* preserve revision lineage;
* update authoritative indexes and required references through separately authorized work;
* not imply creation of a new document.

This revision adopts **Controlled Document Representation Specification** because the document defines repository representation, while STD-0000 owns the higher-level Engineering Documentation Standard and documentation architecture.

---

## 8. Relationship Model

### 8.1 Canonical Representation

Relationships shall use one canonical metadata collection:

```yaml
relationships:
  - type:
    target:
```

Legacy fields including `governed_by`, `implements`, `depends_on`, `validated_by`, `supersedes`, `superseded_by`, `related_documents`, `related_to`, `produces`, and `consumes` remain valid pending authorized migration. New complete revisions shall use `relationships` unless a class-specific standard explicitly requires another representation.

`related_documents` and `related_to` are legacy synonyms for a non-normative association. They shall not both be introduced in a new revision and are replaced by `type: related_to` in the canonical model.

### 8.2 Relationship Types

Canonical types are:

| Type | Direction | Inverse | Cardinality | Authority meaning |
| --- | --- | --- | --- | --- |
| `governed_by` | subordinate → governor | `governs` | one or more; at least one for governed records | Identifies superior governing authority; does not transfer authority. |
| `governs` | governor → subordinate | `governed_by` | zero or more | Identifies records governed within scope. |
| `implements` | implementation/model → decision or requirement | `implemented_by` | zero or more | Declares implementation of approved intent. |
| `implemented_by` | decision/requirement → implementation/model | `implements` | zero or more | Identifies implementing records. |
| `conforms_to` | conforming record → requirement | `constrains` | one or more when applicable | Declares normative conformance. |
| `constrains` | requirement → conforming records | `conforms_to` | zero or more | Identifies downstream constraint. |
| `depends_on` | dependent → prerequisite | `required_by` | zero or more | Declares a prerequisite without transferring authority. |
| `required_by` | prerequisite → dependent | `depends_on` | zero or more | Identifies consumers requiring the source. |
| `validated_by` | subject → validation record | `validates` | zero or more | Links validation evidence; validation does not approve. |
| `validates` | validation record → subject | `validated_by` | one or more | Identifies validated subjects. |
| `authorized_by` | work/result → authority record | `authorizes` | one or more when execution or change requires authorization | Identifies bounded authorization. |
| `authorizes` | authority record → authorized scope | `authorized_by` | zero or more | Identifies explicitly authorized work or records. |
| `produces` | producer → output | `produced_by` | zero or more | Identifies controlled outputs. |
| `produced_by` | output → producer | `produces` | one or more for execution outputs | Identifies the producing record or execution. |
| `indexes` | index → record | `indexed_by` | zero or more | Provides discovery only. |
| `indexed_by` | record → index | `indexes` | one or more for current repository records | Identifies authoritative discovery. |
| `supersedes` | successor → predecessor | `superseded_by` | exactly one for a superseding revision | Identifies approved replacement. |
| `superseded_by` | predecessor → successor | `supersedes` | zero or one | Identifies the approved successor. |
| `related_to` | record ↔ record | `related_to` | zero or more | Non-normative association; conveys no authority or dependency. |

### 8.3 Direction and Inverses

Direction is evaluated from the record containing the relationship to `target`.

An inverse need not be written into an immutable historical record. It may be resolved from the current record, authoritative index, or relationship registry. When both directions are represented, they shall agree.

### 8.4 Lifecycle Effects

A relationship does not activate, approve, supersede, or archive a target by itself.

Normative relationships to Draft records may describe proposed architecture but shall not be used as operational authority. An Active record that depends normatively on Draft content shall identify the dependency as provisional or defer activation until the dependency is Active.

Supersedence relationships take effect only through an approved lifecycle transition.

### 8.5 Required and Optional Usage

Every governed record shall identify at least one `governed_by` relationship unless it is CHAR-0001 or an explicitly identified external authority.

Every current repository record shall identify an `indexed_by` relationship or be deterministically registered through an index-managed inverse.

Execution outputs shall identify `produced_by` and, when applicable, `authorized_by` relationships.

Other relationships are required when their engineering meaning applies and optional otherwise.

### 8.6 Relationship Validation

Validation shall verify:

* type is recognized;
* target identifier resolves or is explicitly external;
* cardinality is satisfied;
* direction is meaningful for both document classes;
* represented inverses do not conflict;
* normative dependencies do not silently rely on non-authoritative Draft content;
* no relationship creates a governance cycle or competing authority;
* supersedence is linear and agrees with revision lineage.

---

## 9. Lifecycle Representation

Every controlled document occupies exactly one lifecycle state defined by STD-0001:

```text
Draft
  ↓
Review
  ↓
Approved
  ↓
Active
  ↓
Superseded
  ↓
Archived
```

Lifecycle meaning:

* Draft architecture may define proposed models for review but does not govern operational execution;
* Review content is frozen for governance evaluation;
* Approved content has received governance approval but is not yet operationally authoritative;
* Active content is the current operational authority within its class and scope;
* Superseded content retains historical authority for its effective period;
* Archived content is retained but not operational.

Lifecycle status does not imply persistence status. Approval does not imply publication. Persistence does not imply approval. Git history does not independently establish lifecycle state.

Only Engineering Governance may authorize lifecycle transitions unless superior governance explicitly delegates that authority.

### 9.1 Engineering Work Order Authority

An Engineering Work Order authorizes execution only while Active. It shall identify its controlled revision, governing baseline, scope, authority, prohibitions, success criteria, stop conditions, evidence, reporting, and resume requirements.

Completion reporting describes execution outcome and does not independently change lifecycle state.

---

## 10. Revision Lineage

The first revision has no predecessor. Every later revision identifies exactly one immediate predecessor with the same `document_id`.

A revision has no more than one immediate successor. Branching the authoritative lineage is prohibited. Alternative proposals remain non-authoritative until Engineering Governance selects one successor.

Lineage shall be:

* complete;
* unique;
* contiguous;
* acyclic;
* consistent with Version, Revision History, supersedence, indexes, and historical locators.

`successor_revision` may remain null in an immutable predecessor because its successor can be resolved from the successor's `predecessor_revision` and the authoritative index.

---

## 11. Supersedence

Supersedence is the Engineering Governance-approved transition by which an approved successor replaces its immediate predecessor as the current Active revision.

Supersedence shall record:

* predecessor and successor revision identities;
* approval authority, reference, and date;
* lifecycle transition authority;
* successor repository path;
* predecessor persistence status;
* immutable historical locator when available;
* an explicit remediation or deferral record when legacy history lacks a locator.

Activation of a successor and supersedence of its predecessor form one controlled governance decision. Supersedence changes current authority without erasing the predecessor's historical meaning.

---

## 12. Historical Persistence

Every persisted approved revision shall remain independently reconstructable after supersedence or archival.

A persisted historical locator contains:

```yaml
revision_identity:
git_commit_oid:
repository_path:
git_blob_oid:
```

The commit identifier shall be the full immutable commit whose tree contains the revision at the recorded path. The blob identifier shall identify the exact bytes.

Branches, tags, abbreviated identifiers, reflogs, working-tree paths, conversations, remote services, archive filenames, and derived reports are not substitutes for immutable object identity.

Missing legacy locators shall be classified as `Legacy` or `Remediation Required` and addressed through authorized backfill. Locators shall never be invented.

---

## 13. Git and Persistence State

Git supplies immutable content-addressed commit, tree, and blob objects. This specification supplies engineering identity, approval, authority, lifecycle, relationships, and lineage.

Git commit order, author data, branches, tags, and filenames do not independently establish engineering approval or lifecycle transition.

A persistence operation shall:

1. include the complete revision in a commit;
2. preserve required predecessor objects;
3. record or resolve the full commit, path, and blob locator;
4. verify object connectivity and blob identity;
5. update authoritative discovery consistently;
6. change `persistence_status` only through authorized repository work.

An uncommitted complete revision with `persistence_status: Pending` is not historically persisted. When explicitly approved and activated under authority that prohibits commits, it may govern operationally within its lifecycle scope, but its pending persistence shall remain visible and shall block any claim of completed historical persistence or baseline persistence qualification.

---

## 14. Deterministic Historical Reconstruction

Given a revision identity:

1. resolve it through an authoritative index or lineage registry;
2. obtain its full commit identifier, repository path, and expected blob identifier;
3. verify the commit and blob objects exist;
4. resolve the path in the commit tree;
5. verify the resolved blob equals the expected blob;
6. inspect or materialize content from the commit rather than the working tree;
7. verify reconstructed `document_id` and `version`;
8. verify approval, lifecycle, and relationship evidence required for the historical claim.

Reconstruction is deterministic only when the same revision identity resolves to one commit, one path, one blob, and identical bytes.

---

## 15. Repository Placement and Discovery

Every current controlled document shall have one authoritative repository location registered in DOC-0001 or another authoritative index referenced by DOC-0001.

Indexes provide discovery and relationship resolution. They do not replace controlled records or acquire their Information Authority.

Engineering Work Orders activated for this repository shall be placed under:

```text
docs/work-orders/
```

Their filenames shall begin with the permanent EWO identifier. Historical and legacy locations remain discoverable until separately migrated or archived.

---

## 16. Publication and Derived Views

Publication may transform format, reorganize presentation, generate navigation, or create summaries without changing controlled engineering meaning.

Published outputs remain Derived Engineering Views unless separately established as controlled records. Publication shall preserve source identity, version, lifecycle, currency, and transformation traceability sufficient to prevent misinterpretation.

---

## 17. Validation Model

### 17.1 Metadata Validation

Verify required fields, allowed values, types, dates, identifier uniqueness, title, version, owner, classification, lifecycle, approval, persistence, lineage, and declared deferrals.

### 17.2 Approval Validation

Verify:

* approval fields are present when required;
* approval authority is authorized by superior governance;
* approval reference resolves or identifies an explicitly approved transitional authority;
* approval date is consistent with lifecycle history;
* Draft and Review records do not claim operational authority;
* rejected or withdrawn content is not Active;
* approval metadata does not fabricate authority.

### 17.3 Relationship Validation

Apply Section 8.6 to every relationship and verify governing, normative, execution, evidence, discovery, and supersedence chains.

### 17.4 Lifecycle Validation

Verify exactly one allowed state, permitted transition order, transition authority, transition date, approval consistency, and current-index agreement.

### 17.5 Persistence Validation

Verify persistence status agrees with observed Git state. `Persisted` requires a valid locator. `Pending` shall not claim a historical locator. Legacy and remediation states require an explicit classification or deferral.

### 17.6 Reconstruction Validation

Verify each persisted superseded revision reconstructs to the expected bytes and metadata using Section 14.

### 17.7 Whole-Document Validation

Verify the complete publication for internal consistency, governing conformance, Markdown integrity, normative terminology, decision coverage, relationship integrity, repository discovery, scope compliance, and absence of conflicting requirements.

---

## 18. Semantic Completeness Validation

### 18.1 Ownership and Additive Operation

Semantic validation is part of this existing controlled-document
representation and validation model. It supplements, and does not replace or
reinterpret, structural validation. STD-0000 continues to own document-class
responsibilities; STD-0001 continues to own lifecycle; STD-0002 continues to
own persistence; PROC-0005 continues to own publication workflow; and
PROC-0006 continues to own independent qualification workflow.

The machine-readable catalog at
`engineering/validation/controlled-document-semantic-profiles.yaml` is the
executable representation incorporated by this specification. It is not a
controlled-document class, standard, lifecycle authority, publication
authority, or competing information owner. Criterion meaning is owned here;
the catalog binds identifiers to deterministic implementation data.

Legacy controlled revisions remain structurally admissible under Principle 6.
Semantic validation applies when a revision declares
`semantic_validation_profile`, when a caller selects an explicit semantic
target, or when a repository path has a profile mapping registered by this
specification. Absence of an applicable profile fails closed for an explicitly
requested semantic validation.

### 18.2 Reusable Profile Contract

Every profile shall identify:

1. required semantic sections or fields;
2. required engineering content;
3. governing and artifact traceability;
4. required evidence;
5. command-documentation applicability;
6. validation criteria; and
7. acceptance criteria.

The reusable profiles are:

| Profile | Class-specific semantic responsibility |
| --- | --- |
| Standard | Purpose, scope, normative requirements, validation, and compliance |
| Specification | Purpose, scope, engineering model, validation, and compliance |
| Procedure | Entry, execution sequence, stop, recovery, outputs, reconciliation, and evidence |
| Policy | Purpose, scope, policy direction, validation, and compliance |
| Template | Required prompts for purpose, engineering content, traceability, evidence, validation, and acceptance |
| WOP | Objectives, prerequisites, implementation boundary, verification, evidence, acceptance, recovery, and completion |
| Roadmap | Objectives, sequencing, dependencies, completion definition, and traceability |
| Gate Specification | Objective, capability, rationale, implementation, verification, commands, results, failure interpretation, evidence, acceptance, recovery, and next gate |
| Operator Verification Guide | Purpose, engineering and operator explanations, prerequisites, steps, outputs, evidence inspection, PASS, FAIL, acceptance, rejection, and resume |
| Completion Report | Scope, implementation outcome, evidence, validation, unresolved criteria, coverage, reconciliation, and disposition |

Profiles shall reuse criteria and shall not import class-specific requirements
into unrelated classes. A profile may be extended only by revising this model
and its incorporated catalog together.

### 18.3 Criterion Contract

Completeness criterion identifiers use the permanent form `DOC-COMP-NNN`.
Every catalog entry shall contain:

- identifier;
- description;
- applicability;
- validation method;
- automation state;
- required evidence;
- fail condition; and
- remediation guidance.

The identifier is the authoritative repository reference. Prose observations
may explain a finding but shall not replace its criterion identifier.
Criterion references in every profile shall resolve to exactly one catalog
entry.

### 18.4 Criterion Catalog

The incorporated catalog defines `DOC-COMP-001` through `DOC-COMP-018`:

| Range | Owned concern |
| --- | --- |
| DOC-COMP-001–008 | Profile resolution, semantic content, traceability, evidence, commands, validation, and acceptance |
| DOC-COMP-009–013 | Entry, sequence, stop, recovery, outputs, and reconciliation |
| DOC-COMP-014 | Roadmap dependencies and completion |
| DOC-COMP-015 | Gate-specific capability and verification completeness |
| DOC-COMP-016 | Operator explanation and disposition completeness |
| DOC-COMP-017 | WOP boundary and completion completeness |
| DOC-COMP-018 | Completion-report closeout completeness |

Automation coverage is one of `automated`, `manual`,
`partially_automated`, or `not_automated`. Automated presence checks do not
claim engineering correctness or evidence sufficiency. Manual criteria remain
mandatory and fail publication when unresolved.

### 18.5 Command Verification

Where a profile declares executable commands, validation shall:

- resolve the executable or repository interface;
- verify the documented invocation shape against the exposed interface;
- require a help reference or help output;
- require documented success and non-success exit behavior; and
- record whether validation inspected the interface or safely executed it.

Unsafe, privileged, destructive, environment-dependent, or side-effecting
commands shall not be executed by semantic validation. Their interface,
syntax, help, and documented exit contract shall be inspected only.

### 18.6 Coverage and Traceability Output

Machine-readable coverage output shall identify, for every criterion:

- automation state;
- validation implementation;
- PROC-0005 and PROC-0006 procedure references; and
- required evidence reference.

Per-document semantic results shall identify the resolved profile, each
criterion, its result, and unresolved manual review. A generated report is a
Derived Engineering View and does not approve content, change lifecycle, or
replace qualification evidence.

---

## 19. Self-Conformance of SPEC-0001 Version 1.6

This revision conforms to its representation model as follows:

* core identity, revision, approval, persistence, relationship, and deferral metadata are present;
* `document_id` remains permanent while the approved title changes;
* Charter governance, policy conformance, EDR implementation, STD-0000 conformance, indexing, and historical authorizations use canonical typed relationships;
* lifecycle status is truthfully Draft and makes no operational claim;
* approval status is Pending and no approval authority is fabricated;
* persistence status is truthfully `Pending`;
* no immutable locator is claimed for Version 1.6;
* missing historical locators for Versions 1.1–1.3 are explicitly deferred rather than fabricated;
* repository-wide rollout and dependent updates are explicitly deferred;
* Revision History preserves Versions 1.0–1.5 and records this Draft successor.

This Version 1.6 successor is a Draft candidate. It does not alter the
approval, lifecycle, or persistence facts of the published Version 1.5
revision and does not become operational authority without the existing
review, approval, publication, and persistence workflow.

---

## 20. Backward Compatibility and Adoption

Existing controlled records remain valid under their approved representation until separately revised.

Legacy metadata fields, identifiers, paths, and lifecycle records shall not be rewritten merely to conform to Version 1.6. Their next authorized complete revision shall adopt the canonical model unless Engineering Governance approves an exception.

Repository-wide rollout shall inventory affected records, preserve unrelated work, identify authority, validate each complete revision, and avoid fabricated historical data.

---

## 21. Implementation Synchronization Model

Implementation synchronization is an additive validation capability of this
specification. It is not a documentation class, lifecycle, publication
workflow, qualification authority, or competing validation framework.

The model separates four concerns:

| Concern | Representation | Ownership boundary |
| --- | --- | --- |
| Documentation | Controlled identity and repository locator | Its existing Information Authority |
| Implementation | Repository artifact and object type | The implementation owner named by the declaration |
| Derived evidence | Fingerprints, graph, drift status, and impact analysis | Evidence producer; evidence makes no approval decision |
| Synchronization metadata | Relationship, scope, strategy, and prior fingerprints | Relationship metadata only; it owns neither endpoint |

Documentation never owns implementation through synchronization metadata, and
implementation never owns documentation. Existing section 8 relationship types
remain the controlled-document relationship vocabulary. A synchronization
declaration binds those existing identities to implementation locators without
creating another dependency mechanism.

### 21.1 Reusable Artifact Declaration

Every supported controlled-document profile may optionally declare one or more
implementation dependencies in its front matter or in the repository
synchronization catalog. Central catalog declarations are appropriate when
domain artifacts do not use controlled-document front matter. Each declaration
shall contain:

```yaml
synchronization_id: SYNC-SPEC-0001-VALIDATOR
documentation:
  document_id: SPEC-0001
  repository_locator: docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md
  fingerprint: {strategy: sha256, value: "<qualified fingerprint>"}
implementation:
  repository_locator: scripts/validate_controlled_documents.py
  object_type: script
  fingerprints:
    - {strategy: sha256, value: "<qualified fingerprint>"}
ownership:
  documentation: EOS Program
  implementation: "<existing implementation owner>"
validation_scope: synchronization validation
synchronization_strategy: exact_content
qualification_policy: {}
```

`object_type` supports `file`, `directory`, `executable`, `script`, `library`,
`service`, `configuration`, and `generated_artifact`. A repository locator is
repository-relative and shall not escape the repository. The declaration may
identify downstream documentation and supersedence. Ownership fields record
existing owners; they do not assign or transfer ownership.

### 21.2 Fingerprints and Identity

Supported fingerprint strategies are SHA-256 content or deterministic directory
tree hashes, Git repository-inventory hashes that exclude ignored generated
content, Git object identifiers, repository commit identity, and immutable
locator identity. A declaration may record multiple strategies. Strategy names
and repository-relative locators are portable; the validator resolves them
against the repository supplied at execution time.

A comparison requires an expected qualified fingerprint and a newly derived
actual fingerprint for both documentation and implementation. Missing
comparison evidence produces `UNKNOWN`, never an inferred PASS.

### 21.3 Drift Classification

The synchronization layer shall emit exactly one status per declaration:

| Status | Meaning |
| --- | --- |
| `PASS` | Both endpoints exist and both match their recorded fingerprints |
| `OUT_OF_SYNC` | Documentation and implementation both changed |
| `IMPLEMENTATION_CHANGED` | Only implementation changed |
| `DOCUMENT_CHANGED` | Only documentation changed |
| `MISSING_ARTIFACT` | A declared endpoint does not resolve |
| `SUPERSEDED` | The declaration identifies a successor |
| `UNKNOWN` | Evidence is insufficient for deterministic comparison |

The report shall separately state artifact existence, endpoint changes,
synchronization requirement, and requalification requirement. `SUPERSEDED`
preserves traceability and does not silently redirect an old declaration.

### 21.4 Dependency Graph and Traversal

The graph reuses controlled identities and repository locators as nodes.
`synchronizes_with` is a derived evidence edge between a document and an
artifact, not a new controlled relationship type. Existing `depends_on`,
`required_by`, `implements`, `implemented_by`, `validated_by`, and `validates`
relationships retain their section 8 meanings. Deterministic reverse traversal
from a changed implementation node identifies every directly and transitively
affected downstream document.

The generic graph supports Specifications, Procedures, Standards, WOPs,
Roadmaps, Gate Specifications, Verification Guides, Completion Reports, source
files, executables, and scripts. Domain integrations, including Zeus, supply
ordinary declarations and do not alter the generic graph algorithm.

### 21.5 Qualification Impact Analysis

Each drift result maps to one or more evidence-based impact assessments:
`qualification_still_valid`, `manual_review_required`,
`automatic_revalidation_sufficient`, `independent_qualification_required`, or
`publication_required`. A declaration may select stricter mappings.

Impact analysis recommends required actions only. It shall set no approval,
acceptance, rejection, lifecycle, publication, or qualification decision.

### 21.6 Additive Validation and Reporting

Structural and semantic validation remain unchanged. Synchronization runs only
as an additional requested layer. Its deterministic JSON report contains
synchronized artifacts, implementation and documentation fingerprints,
dependency graph, drift status, affected documentation, qualification impact,
and required actions. The same repository bytes, metadata, and Git identity
shall produce byte-identical report content.

### 21.7 Repository-Wide Implementation Coverage

Coverage validation is the fourth and final additive validation layer after
structural, semantic, and synchronization validation. Synchronization continues
to answer whether declared endpoints agree. Coverage separately answers which
discoverable implementation artifacts should have been declared but were not.
The coverage layer shall be independently selectable and shall not alter a
synchronization drift result.

Repository discovery shall reuse the repository inventory, including tracked
and non-ignored untracked files, under explicitly configured implementation
roots. Ordered classification rules shall assign exactly one of these
repository-independent categories: Engineering Controller, Verification
Component, User Interface, Execution Engine, Library, Configuration,
Infrastructure Component, Generated Artifact, Internal Helper, or External
Dependency. Each category shall state that synchronization documentation is
`mandatory`, `optional`, or `prohibited`. An unmatched artifact is an unknown
classification and fails closed.

A synchronization declaration covers its exact implementation locator. A
directory declaration may cover descendants only when it explicitly sets
`coverage_scope: recursive`; directory containment shall not be inferred.
This permits repository metadata to represent a documented implementation
surface without duplicating the repository discovery mechanism.

### 21.8 Coverage Determinations and Orphans

For each discovered artifact, the coverage layer shall deterministically emit
one state:

| State | Determination |
| --- | --- |
| `synchronized` | A mandatory artifact is reached by a declaration whose documentation exists |
| `undocumented` | A mandatory artifact has no covering declaration |
| `orphaned_declaration` | A declaration endpoint cannot be reached |
| `obsolete_declaration` | A covering declaration identifies a successor |
| `excluded_by_policy` | Optional or prohibited synchronization policy applies |
| `external_dependency` | The artifact is classified as externally owned |
| `unknown_classification` | No classification rule applies |

Orphan analysis shall report undocumented implementation, documentation without
implementation, obsolete declarations, unreachable implementation, unreachable
documentation, and stale dependency declarations. Every finding shall retain
the matched rule, declaration identifiers, endpoint existence, or inventory
evidence that caused the determination. Documentation identity, kind, and
ownership shall come only from declarations; the coverage engine shall not
infer documentation ownership from names or paths.

### 21.9 Metrics, Debt, and Coverage Report

The deterministic JSON report shall include discovered, synchronized,
undocumented, orphaned, obsolete, excluded, external, and unknown artifacts; a
coverage graph; synchronization gaps; documentation debt; and recommended
review actions. It shall report total implementation artifacts, synchronized
artifacts, undocumented artifacts, orphan declarations, excluded artifacts,
documentation coverage percentage, synchronization coverage percentage, and
documentation debt.

Documentation coverage is the percentage of mandatory artifacts with reachable
authoritative documentation. Synchronization coverage is the percentage of all
discovered artifacts reached by a declaration. Documentation debt is the count
of undocumented mandatory artifacts plus unreachable declared documentation.
Counts and percentages are derived from sorted repository inventory and
declarations, so identical repository content and policy produce identical
metrics and byte-identical JSON.

`engineering/validation/implementation-coverage.yaml` is the incorporated
discovery and classification policy. It implements this model only and creates
no governance, documentation, publication, qualification, or lifecycle
authority. Domain integrations such as Zeus are ordinary paths and
declarations; no domain-specific branch is permitted in the generic engine.

### 21.10 Engineering Contract Model

An Engineering Contract is a repository-independent, machine-readable
representation of an explicitly documented and verifiable implementation
expectation. It describes required observable behavior without prescribing
implementation design. Supported categories are Command Interface, API,
Configuration, Data Schema, File Format, Service Interface, Workflow, State
Transition, Exit Behavior, and Observable Output.

A contract has a permanent `contract_id`, category, authoritative documented
source, discovery declaration, and one or more expectations. Supported
expectation elements are command names, arguments, options, environment
variables, configuration keys, file locations, schemas, return values, exit
codes, generated artifacts, expected side effects, invariants, preconditions,
and postconditions. Extraction shall reject duplicate identifiers, unknown
categories, unknown elements, absent sources, and empty expectations. Sorted
catalog input and canonical serialization make extraction reproducible.

`engineering/validation/engineering-contracts.yaml` is the incorporated
executable representation. It assigns no authority or ownership. A contract
exists only when an authoritative document explicitly declares the
expectation; validators shall not infer engineering intent or undocumented
contracts from implementation.

### 21.11 Contract Discovery and Conformance

Discovery may inspect CLI help, schemas, configuration, metadata, API
signatures, service descriptors, and manifests. It shall use repository
locators and static inspection wherever possible. Help inspection may execute
only the non-operational help interface. Operational workflows, mutating
commands, privileged actions, and side-effecting probes shall not be executed
without separate explicit authorization.

For every contract, comparison shall emit exactly one determination:
`conformant`, `partially_conformant`, `undocumented_capability`,
`undocumented_behavior`, `missing_implementation`, `obsolete_contract`,
`incompatible_implementation`, or `ambiguous_contract`. Every determination
shall retain the documented expectation, discovered value, discovery
mechanism, locator, and content fingerprint or error evidence.

Engineering invariants are evaluated and reported independently from the
overall determination. Compatibility analysis identifies removed, renamed,
deprecated, or incompatible interfaces and undocumented breaking behavior.
Compatibility results are advisory derived evidence and make no acceptance,
approval, publication, qualification, or lifecycle decision.

### 21.12 Conformance Layer and Canonical Report

Conformance is the fifth additive validation layer:

1. structural validation;
2. semantic validation;
3. synchronization validation;
4. implementation coverage validation; and
5. engineering contract conformance validation.

Each layer remains independently selectable. Conformance verifies documented
engineering agreement and does not replace functional, integration,
qualification, publication, or approval activity. The generic engine shall
contain no repository- or Zeus-specific branch. Zeus and other domains
integrate through ordinary contracts.

The canonical JSON report includes validated and discovered contracts,
conformant interfaces, partial conformance, undocumented behavior,
incompatible implementation, invariant failures, advisory compatibility
findings, and recommended engineering actions. Identical repository content
and contract declarations shall produce byte-identical output.

All findings are `derived_engineering_evidence`. The layer shall not infer
governance, publication, qualification, lifecycle, ownership, engineering
intent, or undocumented contracts.

## 22. Compliance

A controlled revision conforms when:

* authority is traceable to superior governance;
* core, revision, approval, persistence, and required relationship metadata are complete;
* identifier and revision identity are unique;
* lifecycle, approval, and persistence states are individually valid and mutually consistent;
* relationship types, targets, direction, cardinality, inverses, and authority meanings validate;
* Revision History identifies the current revision;
* lineage is complete, unique, contiguous, and acyclic or an authorized legacy remediation is declared;
* repository placement and discovery are deterministic;
* persisted history has valid immutable locators;
* derived views remain non-authoritative;
* declared deferrals are explicit and authorized;
* whole-document validation passes.

No metadata field may be used to conceal missing authority, approval, persistence, or traceability.

---

## 23. Success Criteria

This specification is complete when repository-controlled documents can be represented, approved, related, lifecycle-controlled, persisted, discovered, validated, and reconstructed deterministically without conflating governance authority, information ownership, lifecycle status, or Git state.

---

## Engineering Property and Assurance Model

An Engineering Property is a permanent, repository-independent declaration of
a verifiable system condition required by authoritative engineering
documentation. It states a required engineering outcome, not an implementation
choice. A property exists only when its `authoritative_source` resolves to
documentation that establishes that intent; implementation inspection shall
not create, expand, or infer a property.

The supported categories are Safety Invariant, Authorization Boundary,
Approval Boundary, State-Transition Rule, Idempotence Requirement, Recovery
Guarantee, Failure-Containment Rule, Dependency Requirement, Evidence
Requirement, Lifecycle Constraint, Integrity Requirement, Availability
Requirement, Determinism Requirement, Auditability Requirement, and Mission
Correctness Requirement.

The machine-readable Engineering Assurance Catalog shall provide a permanent
property identifier, authoritative source, category, objective, subject,
preconditions, required invariant, prohibited condition, applicable states and
transitions, dependency assumptions, validation strategy, required evidence,
failure classification, assurance impact, review owner, and authority
boundary. Declarations are ordinary data and may describe any system without
service-specific validator logic.

Reusable strategies are Static Inspection, State-Machine Analysis,
Dependency-Graph Analysis, Policy Evaluation, Manifest Validation, Schema
Validation, Control-Flow Inspection, Read-Only Command Inspection,
Deterministic Simulation, Non-Mutating Test Harness, Existing Regression
Evidence Evaluation, and Evidence Traceability Analysis. They shall not
execute operational workflows, privileged or destructive actions, approvals,
publications, or production transitions without separate explicit authority.

Assurance evaluates invariants, transitions, authority boundaries,
idempotence, failure and recovery paths, and evidence sufficiency independently
of interface conformance. Every property receives exactly one of `ASSURED`,
`PARTIALLY_ASSURED`, `NOT_ASSURED`, `VIOLATED`,
`INSUFFICIENT_EVIDENCE`, `AMBIGUOUS_PROPERTY`, `OBSOLETE_PROPERTY`, or
`NOT_APPLICABLE`. Impact is advisory and is limited to engineering review,
implementation correction, documentation correction, contract correction,
synchronization update, revalidation, independent qualification, publication
review, operational-hold recommendation, or no action.

Canonical assurance JSON shall be stable for identical repository content,
declarations, and evidence. Assurance reports are derived engineering evidence
only. They create no intent or ownership, grant no authority, make no approval,
qualification, publication, lifecycle, operational, implementation, or hold
decision, and do not replace testing or independent engineering judgment.

## Workflow Governance Representation

Repository-governed workflow requirements shall be represented by the active
records assigned Information Authority for their class. Mission classification
is an EWO and Completion Report attribute governed by STD-0003 and PROC-0001.
The current report class and visible title are `Completion Report`; legacy
filenames or historical metadata remain locators and do not define a competing
current class.

Every current or future Completion Report shall represent its Governance
Conformance Review as a required section before mission completion. Derived
views, prompts, and handoffs may reference these records but cannot originate
or override the represented behavior.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |

| 1.0 | 2026-07-08 | Initial Controlled Document Model established. |
| 1.1 | 2026-07-09 | Established Engineering Work Orders as first-class controlled records and defined their classification, lifecycle, placement, discovery, traceability, and backward compatibility under EWO-000011 Revision 1. |
| 1.2 | 2026-07-10 | Removed the separate Engineering Work Order lifecycle and established Active as the common execution-authority state under EWO-000012. |
| 1.3 | 2026-07-10 | Defined revision identity, linear lineage, deterministic supersedence, historical persistence, immutable Git locators, and deterministic reconstruction under EWO-000011 Revision 2. |
| 1.4 | 2026-07-11 | Renamed the document from Controlled Document Model to Controlled Document Representation Specification to distinguish representation responsibility from STD-0000 architecture; reconciled Charter, Governance Authority, Information Authority, AER, approval, relationship, lifecycle, persistence-state, title, validation, and self-conformance semantics. |
| 1.5 | 2026-07-17 | Defined repository representation for mission classification, Completion Reports, Governance Conformance Reviews, and non-authoritative handoff references under EGR-000002 and EWO-000018. |
| 1.6 | 2026-07-28 | Draft successor adds reusable semantic validation profiles, permanent completeness criteria, command-interface validation, criterion traceability, machine-readable automation coverage, additive implementation synchronization, deterministic repository-wide implementation coverage, and repository-independent engineering contract conformance with invariant, compatibility, and canonical JSON evidence without changing class, lifecycle, persistence, publication, implementation, or qualification ownership. |

---

## Lifecycle Transition History

| Revision | Date | Previous State | New State | Authority |
| --- | --- | --- | --- | --- |
| SPEC-0001@1.3 | 2026-07-10 | Draft | Review | EWO-000014 Revision 1 |
| SPEC-0001@1.3 | 2026-07-10 | Review | Approved | EWO-000014 Revision 1 |
| SPEC-0001@1.3 | 2026-07-10 | Approved | Active | EWO-000014 Revision 1 |
| SPEC-0001@1.4 | 2026-07-11 | Draft | Review | EGR-000001 — current ratification of the completed transitional revision |
| SPEC-0001@1.4 | 2026-07-13 | Review | Approved | EGR-000001 |
| SPEC-0001@1.4 | 2026-07-13 | Approved | Active | EGR-000001 |
| SPEC-0001@1.5 | 2026-07-17 | Draft | Review | EWO-000018 |
| SPEC-0001@1.5 | 2026-07-17 | Review | Approved | EGR-000002 |
| SPEC-0001@1.5 | 2026-07-17 | Approved | Active | EGR-000002 |
