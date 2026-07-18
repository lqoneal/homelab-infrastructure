---
document_id: EWO-000023-PHASE-2-OWNERSHIP
title: EWO-000023 Phase 2 Repository Ownership Analysis
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Alternative Architecture Evaluation
domain: Engineering Governance
classification: Repository Ownership Analysis
source_of_truth: true
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Persisted
related_documents:
  - EWO-000023
  - EWO-000023-PHASE-2-ALTERNATIVES
  - EWO-000023-PHASE-2-COMPARATIVE-ANALYSIS
  - EWO-000023-PHASE-2-EVIDENCE
tags:
  - repository-ownership
  - information-authority
  - phase-2
  - draft
---

# Repository Ownership Analysis


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


## Ownership Principles

Repository placement must follow responsibility rather than convenience:
CHAR establishes the foundational authority chain; POL owns policy intent and
constraints; STD owns mandatory rules; SPEC owns architectures, interfaces,
and data models; PROC owns repeatable operations; EDR records an approved
choice; EWO authorizes bounded implementation; service and project records own
their assigned information; indexes only provide discovery (P2-E01 through
P2-E06).

This analysis proposes candidate information owners for each alternative. It
does not revise an owner, create a new class, or make a Governance disposition.

## Alternative A Ownership

| Concern | Candidate owner | Rationale | Existing/new |
| --- | --- | --- | --- |
| Governance remains sole transition decision maker | CHAR-0001 and POL-0001 | Existing foundational and policy authority already state this boundary | Existing; likely reference only unless Governance identifies ambiguity |
| Mandatory authorization transaction envelope, approval evidence, idempotency, failure handling, and receipt | Existing Governance Standard set, principally STD-0001/0002/0003 according to responsibility | These are mandatory lifecycle, persistence, and EWO rules; protocol requirements should not be hidden in a project specification | Existing controlled documents, revised only under future authority |
| Repeatable preparation/publication/closeout method | PROC-0001 and PROC-0002 | Procedures define how EWO execution and EGR decisions are operationally processed | Existing procedures |
| Reusable packet/report fields | TPL-0001, TPL-0002, TPL-0004 and potentially a separately approved transaction template | Templates standardize representation without granting authority | Existing templates preferred; new template only if the packet is a genuinely reusable distinct structure |
| Representation of approval and transition evidence | SPEC-0001 | It already owns metadata, relationships, identity, lineage, approval, and persistence representation | Existing specification |
| Controller and validation behavior | SPEC-0005 plus SERVICE-0001 responsibilities | Control framework routes commands; validation/document/checkpoint services own operational capabilities | Existing records, noting SPEC-0005 is Draft |

Alternative A does not justify a Charter amendment or new governance document
class on current evidence. Its behavior spans existing owners because the
problem crosses lifecycle, persistence, procedure, and representation. A
single monolithic owner would duplicate those responsibilities.

## Alternative B Ownership

| Concern | Candidate owner | Rationale | Existing/new |
| --- | --- | --- | --- |
| Whether transition authority may be delegated and which authority remains reserved | CHAR-0001 if the foundational delegation hierarchy changes; otherwise POL-0001 only if Charter is found already sufficient | Current lifecycle permits superior delegation, but reviewed records do not contain the required taxonomy; Governance must decide whether this is foundational | Existing superior governance; exact amendment need unresolved |
| Delegation objectives, prohibited categories, accountability, no-subdelegation, oversight, and revocation policy | POL-0001 | Policy owns governance objectives and constraints | Existing policy |
| Mandatory grant controls and lifecycle interaction | Existing Governance Standards or a dedicated delegation standard if requirements cannot coherently fit STD-0001/0003 | Standards own mandatory, implementation-independent rules | Existing preferred; new standard only with demonstrated non-overlap |
| Delegation grant schema, identity, predicates, limits, nonce, expiry, revocation, and relationships | New dedicated Governance Delegation Specification is potentially justified | No existing specification owns an authority-bearing grant model; SPEC-0001 can supply common representation but should not absorb domain semantics | Potential new specification, not new document class |
| Grant issuance, evaluation, use, revocation, audit, and escalation workflows | PROC-0002 and PROC-0001, or a dedicated subordinate procedure if operational scope becomes too large | Procedures own repeatable Governance and execution workflows | Existing procedures preferred; new procedure if separation of responsibility is demonstrable |
| Agent-facing policy evaluation | SPEC-0005 control routing plus a qualified authoritative service catalog entry | Commands cannot own logic; one service must own evaluation | Existing framework/catalog plus later service specification |

Alternative B may justify a new controlled specification but not a new
document class. The capability has a distinct model not currently owned by
SPEC-0001, SPEC-0005, EMP, or Work Registry. The grant itself could be a
controlled record instance; whether it needs a new record class is unresolved
and requires Phase 3/Governance disposition. Treating registry objects as
grants is rejected because EMP does not own Governance Authority (P2-E06,
P2-E07).

## Alternative C Ownership

| Concern | Candidate owner | Rationale | Existing/new |
| --- | --- | --- | --- |
| Governance decision ownership and broker non-originating boundary | CHAR-0001 and POL-0001 | The service must remain subordinate to foundational Governance Authority | Existing superior governance; revision only if later decision requires it |
| Mandatory lifecycle, evidence, persistence, and EWO issuance constraints | STD-0001/0002/0003 and applicable security/audit standards | Services implement but do not redefine mandatory lifecycle rules | Existing standards plus any separately justified security/audit standards |
| High-level Authorization Layer relationship | SPEC-0007 | It already places EGAS between authorization requests and Active EWOs, but explicitly leaves contracts incomplete | Existing high-level construction specification; not sufficient as sole implementation owner |
| Broker/EGAS service contract, request/response model, state machine, decision capture, idempotency, consistency, recovery, and failure semantics | New dedicated Governance Authority Broker or EGAS Specification | SPEC-0007 requires dedicated controlled specifications; no existing specification defines these interfaces | New specification justified; existing SPEC class, not a new document class |
| Identity and authorization | Dedicated Authentication and Identity Specification | SPEC-0007 explicitly identifies this future cross-cutting specification | New specification already anticipated by SPEC-0007 |
| Immutable audit and engineering evidence | Dedicated Audit and Engineering Evidence Specification | Cross-cutting responsibility is distinct from broker business logic | New specification already anticipated by SPEC-0007 |
| Service inventory and responsibility | SERVICE-0001 or a future Engineering Platform service catalog with one authoritative service owner | All EOS services must be cataloged before implementation; no service may duplicate another | Existing catalog architecture, exact catalog owner unresolved |
| Command/API client routing | SPEC-0005 | It owns global control routing and prohibits commands from becoming authoritative | Existing Draft specification requiring lifecycle qualification before use |
| Work Registry projection | EMP-0001, SPEC-0006, SERVICE-0002 | EMP owns only management projection and must consume broker outcomes without becoming authority | Existing EMP owners; no authority expansion |
| EOS/checkpoint projection | EOS state/checkpoint service owners | EOS persists operational state and continuity views; it must not own the decision | Existing EOS service owners |

Alternative C should not be wholly owned by SPEC-0007. That document is a
high-level construction architecture, marks Authorization Architecture as
Developing and Platform Services as Planning, and explicitly requires
dedicated specifications. A dedicated EGAS/broker specification is therefore
the evidence-supported candidate architectural owner, subordinate to existing
Governance records and accompanied by separate cross-cutting identity and
audit specifications (P2-E10, P2-E11).

## Cross-Alternative Owner Matrix

| Owner class | A | B | C |
| --- | --- | --- | --- |
| CHAR-0001 | Preserve/reference | Possible amendment if foundational transition authority changes | Preserve broker subordination; amendment not shown necessary in broker-only form |
| POL-0001 | Preserve existing decision reservation | Own reserved/delegated policy and accountability | Own broker constraints and Governance decision boundary |
| Existing Standards | Transaction, lifecycle, persistence, evidence requirements | Grant controls and lifecycle interaction | Broker lifecycle, evidence, persistence, security requirements |
| Existing Specifications | SPEC-0001 representation; SPEC-0005 routing | SPEC-0001 common representation; SPEC-0005 routing | SPEC-0007 high-level layer; SPEC-0005 routing |
| New Specification | Not currently justified | Potential delegation-grant model | Dedicated EGAS/broker plus identity and audit specifications justified |
| Procedures | Primary operational owner | Grant issuance/use/revocation operations | Governance review, broker operations, break-glass, recovery |
| Existing domain/service records | Validators, EOS, registry remain bounded consumers | Add qualified policy-evaluation service without EMP authority expansion | Catalog broker and adapters; EMP/EOS remain projections |
| New document class | Not justified | Unresolved; not justified merely by need for a new specification | Not justified; SPEC and service records cover the architecture |

## Ownership Risks and Questions

- Placing all behavior in SPEC-0007 would conflate high-level platform
  construction with detailed Governance authority semantics.
- Placing delegation in Work Registry would transfer authority to an EMP-owned
  management record contrary to current ownership.
- Placing business rules in `engctl` would violate the control framework's
  command/service separation.
- Placing lifecycle rules only in a service specification would allow runtime
  design to redefine superior Standards.
- Creating a new document class before demonstrating that Charter, Policy,
  Standard, Specification, Procedure, EDR, and service records are inadequate
  would violate the EWO-000023 constraint.

Unresolved ownership questions include whether delegation changes CHAR-0001,
which service catalog owns a future EGAS, whether a grant needs a distinct
record class rather than a specification-defined instance, and which record
owns the authoritative transaction receipt across repository and runtime
stores.
