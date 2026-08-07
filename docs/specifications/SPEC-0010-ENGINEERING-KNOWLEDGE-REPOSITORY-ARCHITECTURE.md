---
document_id: SPEC-0010
title: Engineering Knowledge Repository Architecture
version: 1.0
status: Active
owner: Engineering Platform
created: 2026-07-19
last_updated: 2026-07-19
phase: Engineering Knowledge Repository Foundation
domain: Engineering Knowledge
classification: Engineering Specification
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Mission 0 Engineering Knowledge Repository Foundation and Automated Evidence Persistence
approval_date: 2026-07-19
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - ekr-production-implementation
  - automated-mission-capture
  - knowledge-graph-service
  - cross-repository-synchronization
  - legacy-evidence-backfill
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
  - type: related_to
    target: STD-0004
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: EOS-0003
  - type: related_to
    target: SPEC-0004
  - type: related_to
    target: SPEC-0006
  - type: indexed_by
    target: DOC-0001
tags:
  - engineering-knowledge
  - evidence
  - traceability
  - persistence
  - architecture
  - automation
---

# Engineering Knowledge Repository Architecture

## Purpose

This specification establishes the Engineering Knowledge Repository (EKR) as
the authoritative historical knowledge base for the Engineering Portfolio. It
defines the ownership boundary, artifact model, lifecycle, organization,
metadata, relationships, retrieval, retention, synchronization, and future
automation contract required to make engineering knowledge permanently
discoverable and reusable.

EKR complements EOS. EOS owns current operational state, active lifecycle,
synchronization status, and resumability. EKR owns persisted historical
knowledge, evidence, rationale, investigation history, lessons learned, and
qualified outcomes. Neither may duplicate the other's authority.

This specification authorizes documentation and architecture only. It does not
authorize a repository deployment, service, migration, automated capture,
runtime hook, EOS modification, or project-repository mutation.

## Scope

EKR shall support knowledge produced across Homelab, Engineering Platform,
EOS, Engineering Management Platform, infrastructure, and product projects.
Knowledge classes include:

- Investigation, Qualification, Validation, and Completion Reports;
- Evidence Packages and supporting artifacts;
- Work Orders and mission records by reference;
- Lessons Learned and design rationale;
- Architecture and Engineering Decision Records by reference;
- incident timelines and recovery history;
- infrastructure and asset qualification history;
- performance baselines and engineering metrics; and
- automation execution history.

Controlled documents retain their existing authoritative repositories and
document-class owners. EKR indexes and relates them; it does not copy them into
a competing authority.

## Current Engineering Workflow

The current workflow is:

```text
Mission Planning
      ↓
Codex Handoff
      ↓
Mission Execution
      ↓
Completion Report
      ↓
Documentation Update
      ↓
Validation
      ↓
Engineering Review
      ↓
Repository Update
      ↓
Future Mission
```

Current artifacts include handoffs, planning records, Work Orders, terminal
output, investigation notes, evidence packages, validation output, controlled
document revisions, completion reports, Git diffs and commits, EOS state, Work
Registry entries, asset records, and conversation history.

The process duplicates mission identity, scope, commands, findings, validation
results, and changed paths across conversations, handoffs, reports, controlled
documents, planning files, and registry state. Information is lost when
terminal output and conversation-only findings are not persisted, when a
Completion Report is returned but not published, when validation output is
summarized without an immutable locator, or when later work cannot discover a
prior investigation by asset, symptom, mission, or decision.

The transitional manual process shall treat the Completion Report as the
mission knowledge manifest: publish it once, retain supporting evidence at
stable locators, and register relationships rather than rewriting the same
facts in multiple records.

## Mission 0 Lessons Learned

| Lesson | Why it became necessary | EKR treatment |
| --- | --- | --- |
| Evidence Identity Verification | Device paths, mount points, labels, and conversation assumptions can identify the wrong subject. | Require identity evidence and stable subject relationships before accepting knowledge. |
| Preservation Before Recovery | Repair can destroy the original symptom and decision basis. | Preserve pre-action evidence and link successor recovery evidence without replacing it. |
| Hardware Isolation | A media symptom may originate in readers, controllers, hosts, power, adapters, or cables. | Record tested variables, configurations, comparisons, and unresolved causal limits. |
| Asset-Oriented Qualification | Infrastructure qualification must remain reusable and independent of project appropriation. | Relate knowledge to assets and later assignments separately. |
| Incidental Asset Qualification | Independently identifiable assets discovered during work otherwise become invisible context. | Register bounded incidental discoveries and their own evidence lineage. |
| Qualification Before Recovery | Readability or backup existence does not establish fitness or recovery authority. | Store acquisition, qualification, recovery, restoration, and deployment as distinct outcomes. |
| Execution Environment Verification | A sandbox read-only bind was initially mistaken for a host filesystem failure. | Record host, sandbox/container, namespace, privileges, mounts, constraints, and corroborating host evidence. |
| Host versus Sandbox | Infrastructure state must be determined from the Engineering host. | Preserve observation context and prevent constrained views from silently becoming host facts. |
| Storage Qualification | Successful reads and backups did not resolve filesystem, media, or interface risk. | Require identity-linked evidence, limitations, and explicit qualification disposition. |
| Persistent Engineering Evidence | Later investigation could not retrieve detailed prior microSD reports from repositories. | Require durable capture, indexing, immutable locators, and asset/symptom retrieval. |
| Documentation Closure Verification | Approved lessons can remain in conversations or partial revisions. | Record affected authorities, reconciled revisions, deferrals, validation, and closure status. |

## Authority and Ownership Model

- EOS owns current engineering state and operational synchronization.
- The Work Registry owns operational coordination state within SPEC-0006.
- Controlled documents own current governing requirements and approved facts.
- Asset, infrastructure, project, finance, and service records own their domain
  facts.
- EKR owns historical knowledge objects, their immutable content identity,
  provenance, relationships, validation status, retention, and discovery index.
- Git owns repository revision history but is not by itself a semantic
  knowledge index.
- Conversation history and generated summaries are candidate capture sources,
  not authoritative knowledge until validated and persisted.

EKR references an authoritative source whenever that source already owns the
artifact. It stores a manifest, immutable locator, digest, and relationships;
it shall not create a second controlled copy.

## Engineering Knowledge Object Model

Every EKR knowledge object shall have a permanent identifier using:

```text
EKO-YYYY-NNNNNN
```

`YYYY` is the UTC creation year and `NNNNNN` is a zero-padded sequence allocated
atomically by the EKR index. Identifiers are never reused. Artifact-specific
controlled identifiers such as EWO, EDR, AST, SPEC, and MILESTONE remain
unchanged and are related to, not replaced by, the EKO identifier.

Minimum metadata:

- EKO identifier, title, artifact class, schema version, and lifecycle state;
- UTC creation, validation, publication, and last-indexed timestamps;
- producer, mission, execution environment, repository, branch, and commit or
  working-tree locator where applicable;
- governing authority and Work Order or bounded mission reference;
- source artifact locator, media type, byte size, and cryptographic digest;
- subjects including assets, services, repositories, controlled documents,
  symptoms, decisions, and projects;
- validation disposition, validator, method, and evidence locator;
- confidentiality, sensitivity, retention class, and legal hold;
- predecessor, successor, derived-from, supports, contradicts, supersedes,
  validates, qualifies, affects, produced-by, and informs relationships;
- limitations, deferrals, known gaps, and closure status.

Free-form content shall not be required to reconstruct identity, authority,
validation, or relationships. Secrets, credentials, unnecessary personal
content, and uncontrolled sensitive payloads shall be excluded or stored in an
approved protected evidence store referenced by the object.

## Repository Organization

The target logical organization is:

```text
ekr/
├── objects/YYYY/MM/EKO-YYYY-NNNNNN/
│   ├── manifest.yaml
│   ├── report.md
│   └── artifacts/
├── indexes/
│   ├── objects.yaml
│   ├── relationships.yaml
│   └── subjects.yaml
├── schemas/
├── retention/
└── migrations/
```

This is a logical architecture, not authorization to create these paths.
Large, sensitive, or externally owned artifacts may remain in qualified object
storage or source repositories; the EKR manifest stores a stable locator,
digest, retention rule, and availability state.

Indexes shall be reproducible from object manifests. Search databases,
embeddings, knowledge graphs, caches, and dashboards are derived views and may
be rebuilt without changing authoritative knowledge.

## Engineering Knowledge Graph

EKR shall support traversal across:

```text
Mission → Work Order → Evidence → Asset → Controlled Document
        → Repository → Engineering Decision → Lesson Learned → Future Mission
```

Relationships are directed, typed, attributable, and independently
validatable. Every relationship records source object, target identifier,
relationship type, provenance, and creation time. Dangling controlled-record
relationships fail validation. A graph edge conveys traceability, not
authority or lifecycle transition.

Required retrieval paths include identifier, mission, Work Order, asset,
repository, controlled document, decision, symptom, date range, artifact
class, qualification disposition, and lesson learned. Cold-start discovery
shall work without conversation history or a preexisting search index.

## Engineering Knowledge Lifecycle

The EKR lifecycle is:

```text
Creation → Validation → Publication → Indexing → Traceability
         → Synchronization → Reuse → Historical Reference → Archival → Retirement
```

- **Creation** captures a candidate object and source artifacts without
  claiming acceptance.
- **Validation** verifies identity, authority, completeness, integrity,
  sensitivity, and required relationships.
- **Publication** persists the accepted immutable object and digest.
- **Indexing** makes it deterministically discoverable.
- **Traceability** validates required inbound and outbound relationships.
- **Synchronization** publishes only owned references or summaries to EOS and
  project repositories.
- **Reuse** records consumption by later engineering work.
- **Historical Reference** retains a stable completed object for normal query.
- **Archival** moves infrequently used content while preserving discovery and
  integrity verification.
- **Retirement** removes a service representation or permitted payload, never
  the permanent identifier, provenance, disposition, or required audit record.

Publication and indexing are a single completion boundary: failure of either
leaves the object unaccepted. Published content is immutable. Corrections use
a successor object and explicit lineage. Retention expiration never overrides
legal hold, controlled-record persistence, incident evidence, or the only
support for an engineering decision.

## Automated Knowledge Persistence Design

The target record-once flow is:

```text
Engineering work
      ↓
Mission completion event
      ↓
Capture adapter collects declared outputs and validation manifests
      ↓
Normalizer creates candidate EKO manifest
      ↓
Identity, authority, integrity, sensitivity, and schema validation
      ↓
Immutable publication and digest
      ↓
Transactional index and relationship update
      ↓
EOS receives current-state references only
      ↓
Project repositories receive owned references or approved publications only
```

Capture sources may include Completion, Validation, Qualification, and
Investigation Reports; Evidence Packages; declared command logs; repository
validation; metrics; lessons; supporting artifacts; and Work Order linkage.
Automation shall consume explicit mission outputs and structured validator
results, not scrape unrestricted terminal or conversation content by default.

The mission manifest shall be the idempotency boundary. Reprocessing the same
mission and artifact digest shall not create a duplicate object. Publication,
indexing, and relationship updates shall be transactional or recoverably
journaled. Partial capture shall remain visibly incomplete and retryable.

Automation shall stop safely on identity ambiguity, missing authority,
unresolved secrets, digest mismatch, invalid schema, missing required output,
broken relationships, retention ambiguity, or unavailable authoritative
destination. Automation creates no approval, acceptance, execution authority,
controlled-document lifecycle transition, asset qualification, or EOS state
change beyond an already authorized transaction.

Missing or invalid authority shall enter the Authority Restoration Principle in
SPEC-0011. The affected records must be reconciled and normal authority
resolution must succeed before automation resumes.

## EOS and Repository Synchronization

EOS shall store only the current pointer needed for active work: latest
applicable knowledge identifiers, synchronization status, unresolved evidence
gaps, and resume context. EKR stores the historical objects behind those
pointers. Project repositories retain project-controlled truth and may publish
approved reports or references; they shall not mirror the EKR corpus.

Synchronization uses identifier, digest, source owner, source revision,
timestamp, and conflict status. Ownership wins over recency. Conflicts stop
automatic synchronization and preserve both observations until the owning
record is reconciled. Deleting or archiving a derived cache cannot delete an
EKR object or controlled source.

SPEC-0004 may consume EKR results for historical context reconstruction, but
retrieval output remains a derived view with source citations. SPEC-0006 may
relate current work to EKO identifiers without owning their historical content.

## Validation and Acceptance

An EKR architecture or implementation is acceptable only when it demonstrates:

- unique identity and immutable content verification;
- deterministic cold-start discovery;
- complete authority and provenance linkage;
- bidirectional relationship integrity;
- explicit EOS/EKR/domain ownership separation;
- idempotent mission capture and safe retry;
- atomic or recoverable publication and indexing;
- sensitivity and retention enforcement;
- reconstruction from manifests without a search service;
- query by mission, asset, repository, controlled record, decision, symptom,
  and lesson;
- no duplicate controlled-document or current-state authority; and
- failure tests for partial capture, broken relationships, conflicts, and
  unavailable destinations.

## Documentation Closure Verification

This foundation incorporates the approved EKR scope, current workflow, Mission
0 lessons, lifecycle, architecture, automation design, EOS boundary,
traceability, retention, and roadmap requirements. No known approved in-scope
documentation change is intentionally omitted.

Production implementation, automated mission capture, a query/graph service,
cross-repository synchronization, and legacy evidence backfill are deferred
because this mission authorizes architecture and documentation only. Each
requires a separately submitted WOP whose scope contains the implementation,
plus threat modeling, acceptance criteria, migration design, and operational
qualification; that WOP is the work-authority boundary and its safety controls
remain separately enforced.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-19 | Established EKR as the authoritative historical engineering knowledge architecture, defined the EOS ownership boundary, knowledge objects and graph, lifecycle, repository organization, automated persistence contract, Mission 0 lessons, validation, retention, and implementation deferrals. |
