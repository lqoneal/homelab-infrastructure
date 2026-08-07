---
document_id: STD-0000
title: Engineering Documentation Standard
version: 1.7
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-19
phase: Engineering Knowledge Repository Foundation
domain: Engineering Governance
classification: Engineering Standard
predecessor_revision: STD-0000@1.6
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Mission 0 Engineering Knowledge Repository Foundation and Automated Evidence Persistence
approval_date: 2026-07-19
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: related_to
    target: EDR-0002
  - type: depends_on
    target: STD-0001
  - type: depends_on
    target: STD-0002
  - type: depends_on
    target: STD-0003
  - type: depends_on
    target: SPEC-0001
  - type: governs
    target: SPEC-0010
  - type: related_to
    target: GEN-0001
  - type: related_to
    target: PROC-0001
  - type: governs
    target: PROC-0002
  - type: implemented_by
    target: PROC-0005
  - type: governs
    target: TPL-0004
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - documentation
  - architecture
  - controlled-documents
  - engineering-work-orders
  - engineering-governance-resolutions
  - engineering-operating-system
---

# Engineering Documentation Standard

## Purpose

This standard defines the documentation architecture of the Engineering Operating System (EOS).

It establishes the mandatory organization, responsibilities, authority boundaries, relationships, and traceability rules for controlled engineering documents and execution records. It provides the structural blueprint from which subordinate documentation models, procedures, templates, and mission records are derived.

This standard operates within the authority delegated through CHAR-0001 — Engineering Charter and the policy direction established by POL-0001 — Engineering Governance Policy. It does not originate engineering authority, redefine superior governance, specify document lifecycle transitions, or prescribe operational execution procedures.

---

## Scope

This standard applies to all controlled engineering documentation produced within EOS, including:

* foundational governance records;
* repository governance and navigation records;
* policies;
* standards;
* specifications;
* procedures;
* templates;
* Engineering Decision Records;
* Engineering Work Orders;
* Engineering Governance Findings and Resolutions;
* engineering evidence;
* Engineering Completion Reports;
* project, infrastructure, service, asset, financial, milestone, and other controlled engineering records.

It governs documentation architecture and relationships. It does not govern source code, runtime systems, or implementation artifacts except where controlled engineering records explicitly identify or govern them.

---

## Governing Authority

### Origin of Engineering Authority

Production engineering authority originates solely with Lawrence O'Neal and is
exercised through authenticated principal `loneal` and the Zeus CLI.
Engineering Governance is the controlled governance function established
through CHAR-0001 and subordinate repository-controlled governance.

Neither this standard nor any repository, controlled record, database, service, interface, generated output, or implementation agent originates engineering authority.

### Charter Precedence

CHAR-0001 is the highest foundational governing record within EOS.

This standard is subordinate to CHAR-0001 and POL-0001. It shall be interpreted and applied consistently with both records. If this standard conflicts with a superior governing record, the superior record prevails and the conflict shall enter controlled reconciliation.

### Repository Authority

The repository is a governed, versioned publication of controlled engineering records and supporting artifacts.

Repository-controlled records become authoritative through the governance and lifecycle processes established by Engineering Governance. They operate only within the authority delegated to their document class, lifecycle state, and scope. Repository state alone does not create approval, authority, or permission to execute work.

### Governance Authority and Information Authority

Governance Authority is the delegated authority to establish governance direction, approve controlled records and lifecycle transitions, authorize bounded work, establish baselines, and accept engineering outcomes.

Information Authority identifies the controlled record that owns a defined engineering fact, decision, requirement, state, or evidence item within its delegated scope.

An Authoritative Engineering Record (AER) designation identifies Information Authority. It is not a document class, lifecycle state, governance tier, or authorization to execute work.

Governance Authority and Information Authority shall not be conflated. A record may own information without originating governance authority, and a derived view may present authoritative information without acquiring either form of authority.

---

## Architectural Principles

### Principle 1 — Delegated Authority

Every controlled record shall operate within an authority chain traceable to
Lawrence O'Neal, authenticated principal `loneal`, the Zeus CLI, CHAR-0001,
SPEC-0011, and applicable subordinate governance.

### Principle 2 — One Authoritative Information Owner

Every governed engineering fact, requirement, decision, state, or evidence item shall have one authoritative information owner. References, indexes, summaries, and derived views shall resolve to that owner rather than create a competing source.

### Principle 3 — Layered Governance

Higher-level governance constrains subordinate records. No subordinate controlled document shall contradict or redefine a superior governing record.

### Principle 4 — Separation of Responsibilities

Each controlled document class shall perform its assigned engineering responsibility. Documents shall reference rather than duplicate authority or requirements owned by another class.

### Principle 5 — Explicit Execution Authority

Repository modification and engineering execution shall occur only under
explicit, bounded authority. For the current Zeus submission protocol, the
operator-submitted WOP is the mission-specific work-authority boundary; its
scope and explicit gates remain hard limits.

During Transitional Engineering Handoff Governance, a Governance-issued
Engineering Handoff supplies constitutional initiation authority under
CHAR-0001. It is not an Engineering Work Order and does not authorize execution;
the applicable subordinate processes shall still construct, review, approve,
and activate an EWO before execution and shall retain all publication,
qualification, evidence, and repository controls.

### Principle 6 — Stable Execution

Engineering execution consumes an approved Governance Baseline. The baseline shall remain frozen during an active phase unless Engineering Governance approves correction of an execution-blocking defect.

### Principle 7 — Traceability

Every engineering decision, action, controlled record, implementation result, and validation outcome shall remain attributable and traceable to its governing authority and related records.

### Principle 8 — Deterministic Discovery and Recovery

A qualified engineer or implementation agent shall be able to reconstruct the governing policy, applicable standards, specifications, procedures, Work Order, mission, phase, execution state, evidence, and outcome without undocumented knowledge.

### Principle 9 — Historical Integrity

Controlled engineering history shall be preserved. Superseded decisions, revisions, Work Orders, evidence, and completion records shall remain discoverable and reconstructable under the applicable lifecycle and persistence controls.

### Principle 10 — Derived Views Do Not Govern

Reports, dashboards, summaries, AI responses, generated publications, cached representations, and command output are Derived Engineering Views unless established as controlled records through the authorized lifecycle.

Derived Engineering Views shall preserve source traceability and shall not possess Governance Authority, Information Authority, or authority to expand an Engineering Work Order.

---

## Governance and Documentation Hierarchy

Engineering authority and controlled execution follow the hierarchy established by CHAR-0001:

```text
Lawrence O'Neal
        ↓ represented by
Authenticated principal loneal
        ↓ instructs through
Zeus CLI
        ↓ resolves through
Authority Resolution Runtime
        ↓ governed through
CHAR-0001 — Engineering Charter
        ↓
Repository Governance
        ↓
Policies
        ↓
Standards
        ↓
Specifications
        ↓
Procedures
        ↓
Engineering Work Orders
        ↓
Engineering Execution
        ↓
Engineering Evidence
        ↓
Engineering Qualification
        ↓
Engineering Baselines
```

This hierarchy represents authority and governance precedence. Controlled
documentation is the normal operational source of execution authority and
derives its authority ultimately from Lawrence O'Neal. Authority-resolution
failures enter the restoration process in SPEC-0011 before execution. The
hierarchy does not require every relationship between controlled records to be
strictly linear.

Engineering Decision Records establish approved engineering decisions within their delegated scope. Templates provide reusable document structure. Repository indexes provide discovery. Findings and Resolutions support controlled improvement. These records participate in the architecture according to their assigned responsibilities without creating an alternative governance hierarchy.

---

## Controlled Document Responsibilities

### CHAR — Engineering Charter

Establishes the foundational authority chain, governance hierarchy, repository authority, and enduring engineering principles. Only Engineering Governance may amend the Charter.

### GEN — Genesis Governance Record

Preserves the historical and constitutional establishment of the initial Governance Baseline. A Genesis record documents bootstrap history and does not create a recurring bootstrap mechanism.

### DOC — Repository Governance and Navigation

Defines repository-controlled navigation and authoritative indexes. An index supports deterministic discovery but does not replace the records it indexes or acquire their Information Authority.

### POL — Policy

Defines governance objectives, constraints, principles, and intent within authority delegated through the Charter. Policy is the highest policy-level normative record; it is subordinate to the Charter.

### STD — Standard

Defines mandatory engineering rules and requirements. Standards state what shall be done, remain independent of specific implementations, and conform to superior governance.

### SPEC — Specification

Defines engineering models, architectures, interfaces, data structures, and technical requirements. Specifications implement applicable decisions and standards without redefining superior authority.

### PROC — Procedure

Defines an approved, repeatable operational method for satisfying governing requirements. Procedures state how work is performed and shall conform to applicable policies, standards, and specifications.

### TPL — Template

Defines reusable document structure. Templates standardize representation and shall not establish mission-specific authority or independently redefine requirements.

### EDR — Engineering Decision Record

Records an approved engineering or architectural decision, its context, alternatives, consequences, and relationships. An EDR operates within delegated governance and shall not create a competing authority hierarchy.

### EWO — Engineering Work Order

Authorizes bounded mission-specific engineering execution. An Engineering Work Order consumes the applicable Governance Baseline and defines mission, phase, scope, authority, success criteria, evidence, reporting, resume requirements, and stop conditions.

### EGF — Engineering Governance Finding

Records an evidence-based observation that may improve governance. A Finding does not change governance and enters controlled review.

### EGR — Engineering Governance Resolution

Records an Engineering Governance decision that accepts, rejects, defers, or supersedes a Finding or other governance proposal. A Resolution may authorize governance change within its stated scope.

### Evidence Package

Persists objective, reproducible, attributable, and traceable evidence produced by Work Order execution. Evidence records what occurred; it does not approve its own acceptance.

### Completion Report

Reports execution status, scope compliance, outcomes, validation, findings, observations, and recommendations for a governing Engineering Work Order. Engineering Governance determines acceptance.

### Engineering Knowledge Object

Persists validated historical engineering knowledge, evidence identity,
provenance, rationale, relationships, limitations, and reusable lessons under
SPEC-0010. A knowledge object may contain a report or supporting artifact, or
reference an authoritative controlled or domain record by immutable locator
and digest. It does not acquire the source record's Governance Authority,
Information Authority, lifecycle state, or current-state ownership.

The Engineering Knowledge Repository owns historical knowledge-object content,
integrity, indexing, retention, and discovery. EOS continues to own current
operational state. Controlled documents and domain records continue to own
their governing and domain facts.

### Domain and Project Records

Project, infrastructure, service, asset, financial, milestone, validation, and other domain records own engineering information within their defined scope. Their identifiers and responsibilities shall be registered by the authoritative repository index and governed by applicable records.

---

## Document Relationship Architecture

Controlled relationships shall preserve the following responsibilities:

* the Charter governs subordinate repository-controlled governance;
* policies establish governance objectives and constraints;
* standards define mandatory requirements;
* specifications define models and architectures consistent with applicable decisions and standards;
* procedures implement repeatable workflows consistent with policies, standards, and specifications;
* templates provide reusable structures for governed records;
* Engineering Decision Records preserve approved decisions and their consequences;
* Engineering Work Orders reference and consume the applicable Governance Baseline;
* Engineering Work Orders instantiate applicable templates and execute applicable procedures;
* Evidence Packages and Completion Reports are produced under and reference their Engineering Work Order;
* Engineering Work Orders remain traceable to their Evidence Packages and Completion Reports;
* Engineering Knowledge Objects preserve historical execution knowledge and
  relate missions, Work Orders, evidence, assets, repositories, controlled
  documents, decisions, lessons, and future missions without duplicating their
  authoritative owners;
* Findings inform controlled improvement;
* Resolutions record Engineering Governance disposition and authorize approved changes;
* indexes provide discovery without replacing authoritative information owners;
* derived views identify or resolve to their authoritative sources.

Relationships are controlled engineering information. They shall be explicit whenever they can reasonably be recorded and shall not transfer authority from a source record to a consumer.

---

## Engineering Work Order Record Architecture

### Authority

The submitted WOP is the ordinary single mission-specific work-authority
boundary. Conversational context, task notes, derived views, generated
instructions, and implementation-agent inference shall not expand its scope.
Admission and execution-safety predicates validate the WOP; they do not grant
authority a second time.

A Governance-issued Engineering Handoff may initiate EWO construction during
the Charter-defined transitional period, but the resulting EWO remains the
bounded execution authorization. Neither the Handoff nor its initiation effect
may be interpreted as EWO approval, activation, or permission to modify the
repository.

Only Engineering Governance may approve or activate an Engineering Work Order unless superior governance explicitly establishes another controlled authorization mechanism.

### Required Boundaries

An Engineering Work Order shall define its mission, phase, scope, operational authority, engineering authority, prohibited actions, escalation requirements, success criteria, evidence requirements, Completion Report requirements, resume policy, communication contract, and stop conditions in accordance with STD-0003.

Authority not explicitly granted remains prohibited.

### Persistence and Discovery

Repository-governed Engineering Work Orders shall be persisted under `docs/work-orders/`. Each filename shall begin with the permanent Work Order identifier, and the authoritative current revision shall be registered in DOC-0001.

### Lifecycle

Engineering Work Orders follow the common controlled-document lifecycle defined
by STD-0001 and represented by SPEC-0001. A submitted WOP conveys authority for
its explicit scope; lifecycle and execution-safety checks determine whether
that scoped work may proceed.

Engineering Governance controls activation, supersedence, and archival. Implementation agents report execution status but do not approve lifecycle transitions. Completion reporting does not create a separate lifecycle state.

### Evidence and Completion Relationships

Every Work Order that enters execution shall produce the evidence and completion reporting required by its terms. The Work Order, Evidence Package, Completion Report, and DOC-0001 registration shall support deterministic, bidirectional discovery of the execution record.

### Historical Preservation

Superseded and Archived Engineering Work Orders remain controlled records. Their authority during their effective period, executed revision, evidence, and outcome shall remain reconstructable under STD-0001, STD-0002, and SPEC-0001.

### Legacy Compatibility

Existing Work Orders outside `docs/work-orders/` shall not be moved, renamed, invalidated, or rewritten solely to conform to current placement. They shall remain discoverable through indexing or explicit legacy classification until separately migrated, superseded, or archived.

---

## Engineering Governance Resolution Record Architecture

### Purpose and Record Responsibility

An Engineering Governance Resolution is the authoritative controlled record of an Engineering Governance disposition concerning an Engineering Governance Finding or other governance proposal.

An EGR records the decision already made by Engineering Governance. It may authorize a governance change, lifecycle transition, baseline effect, deferral, rejection, or supersedence only within its explicit decision scope. It does not originate Governance Authority, replace the evidence considered, or authorize engineering execution.

### Approving Authority

Only Engineering Governance, acting within authority delegated through CHAR-0001 and POL-0001, may approve an EGR or authorize its lifecycle transitions.

An implementation agent may prepare, validate, persist, and index an EGR only within explicit authorization. The agent shall not select the governance disposition, expand the decision scope, infer approval, or treat record creation as evidence that approval occurred.

### Identifier Responsibility

Every EGR shall possess one permanent identifier beginning with the `EGR-` class prefix. The identifier shall be assigned before the record enters Review, shall not be reused, and shall remain stable across revisions and title changes.

The authoritative repository index owns EGR identifier registration, numbering coordination, canonical location, and current-revision discovery. The EGR record owns its decision content and revision history. A filename shall begin with the permanent EGR identifier after the canonical location and filename convention are registered.

### Required Record Elements

Every EGR shall be a complete controlled publication conforming to SPEC-0001 and shall contain, at minimum:

* permanent document identity, title, version, owner, classification, and lifecycle state;
* revision lineage, approval metadata, persistence status, relationships, and declared deferrals when applicable;
* the governance question, Finding, proposal, completed revision, or other controlled subject presented for disposition;
* the evidence and controlled records considered by Engineering Governance;
* one explicit governance disposition;
* the decision scope and the exact affected records or revisions;
* the decision rationale;
* authorized governance changes, lifecycle transitions, baseline effects, execution prerequisites, or deferrals, as applicable;
* the decision date and approving Governance Authority;
* implementation, validation, persistence, indexing, or follow-up conditions;
* historical and supersedence effects; and
* a Revision History.

The decision subject, evidence, disposition, scope, and authorized effects are distinct information and shall not be inferred from one another.

### Governance Disposition

An EGR disposition shall be exactly one of:

* **Accepted** — Engineering Governance accepts the stated proposal or result within the recorded scope;
* **Rejected** — Engineering Governance rejects the stated proposal or result;
* **Deferred** — Engineering Governance postpones disposition or effect subject to recorded conditions; or
* **Superseded** — Engineering Governance replaces a prior governance disposition with the identified successor decision.

The disposition recorded about the decision subject is distinct from the EGR publication's own `approval_status`. An Approved or Active EGR may authoritatively record an Accepted, Rejected, Deferred, or Superseded disposition.

### Decision Scope and Effects

An EGR shall identify every controlled record and exact revision whose approval, lifecycle, authority, baseline eligibility, deferral, rejection, or supersedence is affected. Authority not explicitly recorded remains ungranted.

An EGR may authorize a governance change or lifecycle transition within its
scope. When engineering execution is required, the submitted WOP is the
bounded work-authority source; its admission and safety controls still apply.

Approval of an EGR does not by itself modify another controlled record. Authorized changes to affected records, indexes, baselines, or implementation artifacts shall occur only through separately authorized complete revisions or operations.

### Lifecycle Transition Responsibility

EGRs follow the common lifecycle defined by STD-0001 and represented by SPEC-0001.

* Draft records a proposed Resolution under preparation and possesses no operational authority.
* Review records a complete proposed Resolution under controlled governance evaluation and possesses no operational authority.
* Approved records content accepted by Engineering Governance but does not make the decision operational.
* Active records the current operational governance decision within its explicit scope.
* Superseded records a decision replaced by an identified approved and activated successor while preserving its historical effect.
* Archived records a retained historical Resolution removed from current operational use through an approved transition.

Approval of EGR content and activation of its decision are distinct governance actions. Every transition shall preserve attributable approval and transition evidence. An EGR with Pending persistence may become Active only when explicit Engineering Governance authority permits activation while deferring persistence, and the limitation shall remain visible.

### Relationship Requirements

Every EGR shall use the relationship model defined by SPEC-0001 and shall:

* identify superior governance through `governed_by`;
* identify its governing authorization through `authorized_by` when a separate controlled authorization exists;
* identify the Finding, proposal, Work Order, Completion Report, Evidence Package, and affected controlled revisions through the canonical relationship types whose engineering meanings apply;
* use `authorizes` for explicitly authorized work or changes without implying that the EGR itself performs execution;
* identify authoritative discovery through `indexed_by` or an index-managed inverse;
* use `supersedes` only when the Resolution replaces a prior EGR; and
* preserve non-authoritative associations through `related_to` only when no stronger canonical relationship applies.

Relationships support traceability but do not expand the EGR disposition, transfer Governance Authority, approve a target, or perform a lifecycle transition by themselves.

### Evidence, Work Order, and Completion Relationships

An EGR issued after engineering execution shall identify the governing EWO, applicable Completion Report, and material Evidence Package when those records exist. The Completion Report records execution outcomes and mission acceptance information; the EGR records the governance disposition within its decision scope.

An EGR issued without prior engineering execution shall identify the controlled Finding, proposal, review record, or other evidence supporting the decision. Missing evidence or unresolved subject identity is a stop condition and shall not be concealed through narrative assertion.

### Persistence, Discovery, and Historical Preservation

EGR persistence and discovery shall conform to STD-0002 and SPEC-0001. Every current EGR shall resolve through the authoritative repository index to one current controlled revision and one canonical repository location.

Approved decision history shall not be rewritten. Superseded and Archived EGRs shall preserve their original decision scope, authority, disposition, effective period, relationships, and historical meaning. Corrections or changed decisions require a new complete revision or successor Resolution through the controlled lifecycle.

No EGR may claim persistence, registration, lifecycle effect, approval-reference readiness, or deterministic reconstruction that is not supported by observed repository evidence.

---

## Governance Baseline

Every engineering phase shall identify an approved Governance Baseline.

The applicable baseline may include:

* CHAR-0001;
* Active policies;
* Active standards;
* Active specifications;
* Active procedures;
* Active templates;
* applicable Active Engineering Decision Records;
* applicable Active Engineering Work Orders;
* other Active governing records required by the mission.

The baseline shall identify the records actually governing execution. Inclusion does not flatten their distinct authority, responsibilities, or information ownership.

---

## Phase Execution Model

```text
Engineering Governance approves the Governance Baseline
        ↓
Engineering Governance activates an Engineering Work Order
        ↓
Implementation agents execute within bounded authority
        ↓
Engineering evidence is collected
        ↓
An Engineering Completion Report is produced
        ↓
Engineering Governance reviews evidence and outcomes
        ↓
Engineering Governance accepts, rejects, or requires revision
        ↓
Phase closeout, qualification, and controlled improvement proceed
```

Implementation agents collect and report evidence. Engineering Governance interprets evidence, controls governance, and determines acceptance.

---

## Improvement Management

Governance improvements discovered during Mission Execution shall be recorded rather than implemented immediately unless Engineering Governance authorizes correction of an execution-blocking defect.

```text
Observation
        ↓
Engineering Governance Finding
        ↓
Phase Improvement Queue
        ↓
Engineering Governance Review
        ↓
Engineering Governance Resolution
        ↓
Governance Stabilization
        ↓
Future Governance Baseline
```

Ordinary governance evolution occurs through authorized Governance Stabilization. This process does not constrain the Charter amendment authority reserved to Engineering Governance.

---

## Lifecycle, Persistence, and Representation Boundaries

STD-0001 defines the common controlled-document lifecycle and lifecycle-transition controls.

STD-0002 defines operational persistence, indexing, discovery, integrity, and relationship requirements.

SPEC-0001 defines controlled-document representation, revision identity, lineage, supersedence, and historical reconstruction.

STD-0003 defines mandatory Engineering Work Order content.

PROC-0001 defines the approved method for executing an Active Engineering Work Order.

This standard defines the relationships among those records. It shall not duplicate or redefine their assigned lifecycle, persistence, representation, content, or execution requirements.

---

## Repository Discovery and Navigation

An engineer or implementation agent shall determine current governing execution context by traversing:

1. the canonical repository and DOC-0001;
2. the current mission, phase, and project state;
3. CHAR-0001 and the applicable Governance Baseline;
4. applicable decisions, standards, specifications, and procedures;
5. one authoritative Active Engineering Work Order for the task;
6. its Evidence Package and Completion Report when produced.

Navigation for an active task shall terminate at one authoritative Work Order revision. Navigation shall also permit reconstruction of historical authority, execution, evidence, qualification, and outcomes.

Indexes, search results, resume output, dashboards, and generated navigation are discovery mechanisms or derived views. They do not replace the controlled records to which they resolve.

---

## Traceability Requirements

Controlled engineering documentation shall support traceability among, as applicable:

* Lawrence O'Neal, authenticated principal `loneal`, the Zeus CLI, and controlled Engineering Governance;
* Charter, policies, standards, specifications, procedures, and templates;
* Engineering Decision Records;
* missions, phases, sprints, recovery plans, and recovery units;
* Engineering Work Orders and executed revisions;
* Findings and Resolutions;
* Evidence Packages and Completion Reports;
* Engineering Knowledge Objects and their authoritative source locators;
* engineering assets, services, repositories, and implementations;
* validation, qualification, acceptance, and baselines.

Traceability shall be attributable, discoverable, and sufficient for deterministic recovery. Referencing an authoritative record permits reliance on its information within scope; it does not transfer Governance Authority or Information Authority.

---

## Compliance

A controlled documentation architecture is compliant with this standard when:

* its authority chain conforms to CHAR-0001;
* its policy direction conforms to POL-0001;
* Governance Authority and Information Authority remain distinct;
* document responsibilities are explicit and non-conflicting;
* every governed fact has one authoritative information owner;
* relationships and governing references are traceable;
* only Active records govern execution within their assigned scope;
* Engineering Work Orders remain bounded, persisted, discoverable, and linked to execution records;
* derived views do not become competing authorities;
* historical integrity and deterministic recovery are preserved;
* repository-controlled records remain discoverable through authoritative indexes.

Any conflict, missing authority, ambiguous ownership, or broken relationship shall be reported and reconciled through authorized governance.

---

## Success Criteria

This standard is complete when it provides a coherent documentation architecture that:

* preserves the Charter-established authority chain;
* assigns clear responsibilities to controlled document classes;
* distinguishes governance authority from information ownership;
* supports bounded and traceable execution;
* supports evidence-based acceptance;
* preserves historical integrity;
* enables deterministic repository discovery and engineering recovery;
* prevents subordinate records and derived views from creating competing authority.

Future controlled documents shall conform to this standard or record an explicit Engineering Governance-approved exception.

## Repository-Governed Workflow Publications

The active repository publications assigned Information Authority for Work
Initiation, mission classification, mission lifecycle, Completion Reports, and
Governance Conformance Reviews are the sole operational source for those
behaviors. Handoffs and conversation history may reference these publications
but shall not redefine them.

The standard report class is `Completion Report`, and the visible title of each
current or future report shall be exactly `Completion Report`. Historical
filenames and superseded metadata remain preserved as locators and historical
evidence; they do not establish an alternate current report class or title.

PROC-0005 is the single reusable operational procedure for controlled document
publication. It executes applicable requirements owned by STD-0001, STD-0002,
and SPEC-0001 without acquiring their normative or representation authority.
Class-specific procedures supplement PROC-0005 and retain their specialized
responsibilities. Publication authority and successful repository execution do
not originate Governance Authority or implementation authority.

Governance-framework revisions shall reconcile the complete directly affected
documentation subsystem, including standards, specifications, procedures,
templates, indexes, lifecycle relationships, planning, and derived operational
views. Partial publication is prohibited unless Engineering Governance records
an explicit bounded deferral and follow-up authority.

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Governance documentation architecture established. |
| 1.1 | 2026-07-09 | Established Engineering Work Orders as first-class controlled records with explicit hierarchy, authority, placement, lifecycle, evidence linkage, navigation, historical preservation, and legacy compatibility under EWO-000011 Revision 1. |
| 1.2 | 2026-07-10 | Removed Issued lifecycle authority and established Active as the execution-authority state for Engineering Work Orders and all controlled engineering documents under EWO-000012. |
| 1.3 | 2026-07-11 | Reconciled the complete standard with CHAR-0001, GEN-0001, POL-0001, and EDR-0002; established delegated authority, Charter precedence, document-class responsibilities, repository authority, Information Authority, AER, derived-view, and traceability semantics. |
| 1.4 | 2026-07-13 | Established the minimum normative Engineering Governance Resolution record architecture, including authority, identity, required content, disposition, scope, lifecycle, relationships, execution boundaries, discovery, and historical-preservation requirements. |
| 1.5 | 2026-07-17 | Established repository-governed workflow publications, the Completion Report class and exact title, and holistic governance-subsystem reconciliation under EGR-000002 and EWO-000018. |
| 1.6 | 2026-07-18 | Integrated PROC-0005 as the single reusable operational controlled-document publication procedure while preserving normative standards, representation ownership, specialized procedures, and Governance authority. |
| 1.7 | 2026-07-19 | Established Engineering Knowledge Objects and EKR responsibility within the documentation architecture while preserving EOS current-state ownership and existing controlled and domain information authorities. |
