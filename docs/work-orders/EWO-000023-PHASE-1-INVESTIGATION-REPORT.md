---
document_id: EWO-000023-PHASE-1-INVESTIGATION
title: EWO-000023 Phase 1 Authority-Gap Characterization
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Authority-Gap Characterization
domain: Engineering Governance
classification: Engineering Investigation Report
source_of_truth: true
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Persisted
related_documents:
  - EWO-000023
  - EWO-000023-PHASE-1-EVIDENCE
  - EWO-000023-PHASE-1-AUTHORITY-BOUNDARY
  - CHAR-0001
  - POL-0001
  - PROC-0001
  - PROC-0002
  - EDR-0002
tags:
  - engineering-investigation
  - authority-gap
  - phase-1
  - draft
---

# Engineering Investigation Report


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


## Investigation Boundary

This Draft records only EWO-000023 Revision 1 Phase 1 authority-gap
characterization. It inventories observed failure patterns, affected
mechanisms, authority boundaries, evidence gaps, assumptions, risks, and
unresolved questions. It does not evaluate corrective architectures, select a
design, recommend a disposition, modify governance, or authorize execution.

The qualified Phase 0 baseline is preserved at Homelab `main` commit
`4e6ac19569e4d2f9b7aa65aec8e31eb0cebf0116`. Phase 1 began with a clean
working tree, aligned checkpoint, valid Work Registry, and passing Engineering
Platform qualification. No governing record was modified.

## Characterization Method

The investigation used repository-controlled records and Git history as
evidence. Findings are limited to statements directly supported by evidence
items in `EWO-000023-PHASE-1-EVIDENCE`. A repository record's own lifecycle
and authority claims are reported as observations, not independently endorsed
as a Governance disposition.

The unit of analysis is an authority-bearing workflow transition:

```text
governance decision
    -> controlled authorization publication
    -> operational projections and synchronization
    -> separately initiated implementation
    -> evidence and acceptance
    -> successor authority, when separately approved
```

## Authority-Gap Categories

### AG-01 — Successor-Authority Discontinuity

When a bounded mission completes, its authority does not authorize creation or
activation of its successor. If no separate successor authority already
exists, repository execution stops even when a next objective is known. The
gap is explicit after EWO-000019: EGR-000003 records that EWO-000019 was
complete, no Homelab work was active or planned, and historical EWOs supplied
no continuing execution authority. Engineering Governance then exercised a
bootstrap-deadlock correction to create EWO-000020.

This is an authority availability gap, not evidence that an implementation
agent should infer or create successor authority. The Charter and Work Order
procedure expressly prohibit such inference.

Source attribution: EV-01, EV-02, EV-06, EV-08, EV-10, EV-16, and EV-18.

### AG-02 — Decision-to-Publication Discontinuity

The observed authorization flow separates the external Governance approval act
from its repository-controlled, auditable representation. EGR-000003 and
EGR-000004 each state that an operator handoff is the approval act and the EGR
is its controlled repository record. A bounded transitional transaction must
then create, approve, register, activate, validate, commit, synchronize, and
checkpoint the successor authority before implementation can begin.

This is not a finding that the external approval is invalid. It is the observed
manual boundary between a Governance decision and the deterministic repository
operations needed to make that decision operationally discoverable.

Source attribution: EV-02, EV-03, EV-04, EV-05, EV-11, EV-12, and EV-18.

### AG-03 — Transitional-Authority / Execution-Authority Separation

Authorization-publication transactions possess narrowly scoped authority to
persist and project a Governance decision but expressly prohibit the
implementation authorized by the resulting EWO. Their authority expires when
the successor EWO becomes authoritative. Implementation must start in a
separate wrapped mission under the new EWO.

The separation is deliberate and protective, but it creates a recurring
handoff boundary where an agent must distinguish publication operations from
implementation execution. Confusing the two could either begin implementation
too early or incorrectly treat a completed publication transaction as ongoing
implementation authority.

Source attribution: EV-02, EV-03, EV-04, EV-05, EV-07, EV-13, and EV-18.

### AG-04 — Multi-Projection Lifecycle Synchronization Exposure

One Governance lifecycle decision is projected into multiple controlled and
operational mechanisms: EGR, EWO, DOC-0001, Project State, Work Registry,
Completion Report/evidence, EOS operational state, checkpoint, and Git commit.
EGR-000003 and EGR-000004 enumerate minimum synchronized effects. The
EWO-000021 authorization report notes that EOS and the checkpoint initially
projected EWO-000020 and had to project EWO-000021 at the final boundary.
EWO-000021 execution later characterized repository/EOS lag as an expected
transition requiring refresh after commit and checkpoint.

The exposure is the interval in which projections can disagree or appear
stale. Under STD-0004 and PROC-0001, this blocks or redirects execution rather
than transferring authority to a derived view.

Source attribution: EV-03, EV-04, EV-05, EV-09, EV-14, EV-15, EV-17, and
EV-18.

### AG-05 — Mission-Lifecycle / Agent-Process Mismatch

EWO-000019 reconstructed two post-acceptance missions executed as additional
turns inside a directly launched Codex process. No wrapper marker or lifecycle
notification existed. The accepted wrapper implementation defines a governed
initiation gate, but its Completion Report also records that external host
launch cannot be cryptographically forced. EWO-000020 later states that one
accepted handoff, rather than a process, PID, terminal, shell, wrapper, or
repository session, is the engineering mission boundary.

This is a recurring authority-boundary failure because process continuity can
obscure the need for a new mission identity, current EWO verification, and
fresh initiation. It is distinct from AG-01: an applicable EWO may exist while
the mission still bypasses its required initiation mechanism.

Source attribution: EV-01, EV-06, EV-07, EV-13, and EV-18.

### AG-06 — Management-State / Governance-Authority Confusion Risk

The Work Registry projects active, completed, deferred, and cancelled work,
but its schema and runtime output explicitly state that registry state is not
Governance or controlled-document lifecycle authority. The registry recorded
successive EWO-000020, EWO-000021, EWO-000022, and EWO-000023 transitions, yet
each transition cites a separate authority reference.

No evidence reviewed shows the registry actually originating Governance
Authority. The characterized gap is a boundary risk: operational consumers
could mistake a current management projection for approval or execution
authority if source references and controlled EWO lifecycle are not checked.

Source attribution: EV-09, EV-15, EV-17, and EV-18.

## Recurring Failure Patterns

| Pattern | Observed sequence | Recurrence evidence | Operational consequence |
| --- | --- | --- | --- |
| FP-01 successor dead end | Mission completes; no successor EWO exists; Governance must separately authorize publication of one | EWO-000019 to EGR-000003/EWO-000020; EWO-000022 to EWO-000023 | Execution stops despite a known next objective |
| FP-02 external approval capture | Operator handoff makes decision; EGR/EWO transaction records and projects it | EGR-000003 and EGR-000004; EWO-000023 authorization-publication reference | Manual Governance intervention and a separate persistence transaction are required |
| FP-03 split mission boundary | Authorization publication ends; implementation must launch separately | EGR-000003/EWO-000020 and EGR-000004/EWO-000021 | Risk of early implementation or reuse of expired transitional authority |
| FP-04 synchronized projection fan-out | One transition updates multiple records, registry state, EOS, checkpoint, tests, and Git | EGR-000003 and EGR-000004 transaction scopes; EWO-000021 authorization report | Partial or stale projections block deterministic resume |
| FP-05 process reuse bypass | A new mission continues inside an old direct Codex process without governed launch/initiation | EWO-000019 incident reconstruction | Missing mission marker and lifecycle notification; initiation authority not requalified |
| FP-06 supersession before execution | A newly active but unstarted EWO is explicitly superseded to establish a different sole authority | EWO-000020 to EWO-000021 under EGR-000004 | Additional Governance decision and lifecycle reconciliation required; scope must not transfer implicitly |

## Affected Workflows, Records, Procedures, Agents, and Transitions

| Area | Affected elements | Characterized involvement |
| --- | --- | --- |
| Governance decision | Engineering Governance; operator handoff; EGR preparation/review | Selects disposition and authorizes lifecycle effects; external approval act must be represented in controlled records |
| Work authorization | EWO creation, approval, activation, supersedence, acceptance | Establishes bounded execution authority; predecessor authority does not create a successor |
| Repository publication | DOC-0001, Project State, EGR/EWO/evidence/report files, Git commit | Persists and makes the decision discoverable without originating it |
| Operational management | Work Registry objects, transition history, dependencies, deferrals | Projects management state and attribution; does not approve work |
| EOS continuity | operational state, repository inventory, active checkpoint, resume/context output | Projects and reconstructs current state; stale projection triggers reconciliation rather than becoming authority |
| Initiation | PROC-0001, DOC-0001 ritual, `engctl codex`, `engctl resume`, `engctl platform qualify` | Verifies mission identity and current authority before execution |
| Validation | controlled-document validator, registry validator/regressions, EOS and checkpoint validation, repository health | Detects identity, relationship, projection, and integrity defects; does not choose a Governance disposition |
| Human actor | Engineering Governance/operator | Makes reserved decisions and supplies approvals not inferable from repository data |
| Implementation agent | Codex | May prepare authorized records and execute deterministic operations; must stop at unresolved disposition or authority |
| Repository/EOS services | `engctl`, registry service, context reconstruction, Git | Execute or report bounded deterministic actions; possess no Governance Authority |

Affected lifecycle transitions observed are Draft/Prepared to Approved,
Approved to Active, Active to Completed or Superseded, registry ready/active to
completed/cancelled, transitional authority to expired/closed, and checkpoint
or operational projection from prior to current repository commit.

## Authority-Boundary Summary

- Engineering Governance alone determines dispositions, approvals,
  activations, acceptance, supersedence, deferrals, and permission to create a
  successor implementation EWO.
- A resolution preparer may assemble evidence and a Draft but may not select a
  disposition, infer intent, approve, activate, or execute downstream work.
- An authorization-publication agent may perform only the repository effects
  explicitly enumerated by the approval act and transitional authority.
- Repository and EOS services may perform deterministic validation,
  serialization, projection, synchronization, checkpoint, and Git operations
  within granted authority; their successful output does not originate
  authority.
- An implementation agent executes only the bounded scope of an Approved
  Active EWO after initiation; it cannot inherit expired transitional
  authority or create its successor.
- Evidence, reports, registry state, checkpoints, context output, and Git
  identity support traceability and reconstruction but do not approve their
  own lifecycle or execution.

The detailed classification appears in
`EWO-000023-PHASE-1-AUTHORITY-BOUNDARY`.

## Assumptions

1. Repository-controlled records and reachable Git history are the complete
   evidence boundary available to this phase unless a record explicitly cites
   an external approval act.
2. The operator handoffs cited by EGR-000003 and EGR-000004 occurred as the
   records state; their full external content was not available and is not
   reconstructed.
3. Repetition means a materially similar boundary occurred at least twice; it
   does not assert a statistical failure rate.
4. A protective stop or deliberate authority separation is characterized as
   an operational gap only where it repeatedly requires manual bridging or
   creates a documented discontinuity. This does not classify the control
   itself as defective.
5. `source_of_truth: true` on a Draft identifies its repository source but does
   not activate the Draft, consistent with EDR-0002.

## Risks

| Risk | Evidence basis | Phase 1 treatment |
| --- | --- | --- |
| Unauthorized authority inference | CHAR-0001, PROC-0001, PROC-0002, EDR-0002 prohibit it | Preserve as a stop boundary; do not fill gaps by inference |
| Transitional authority leakage | EGR-000003/000004 explicitly expire transitional authority | Separate publication actions from implementation in every finding |
| Partial lifecycle projection | Authorization transactions touch multiple owners; observed EOS lag | Record all projections and their authoritative owners |
| Derived-view elevation | Registry and context are useful operational views | Explicitly classify them as non-governing projections |
| Process identity mistaken for mission identity | EWO-000019 incident; EWO-000020 mission model | Treat every accepted handoff as requiring independently verified mission authority |
| Evidence overreach | External handoff bodies are absent | Attribute only the repository records' statements about those acts |
| Premature solution bias | Phase 2 is not authorized in this phase | Exclude alternatives, selection criteria, recommendations, and roadmap content |

## Unresolved Questions and Evidence Gaps

1. What exact decision payload, identity proof, authentication, and audit data
   existed in each external operator handoff? The repository records name the
   approval acts but do not preserve their full content.
2. Which Governance decisions are categorically reserved, and which bounded
   decisions could ever be delegated? Current records state examples and role
   constraints but do not contain a complete decision taxonomy.
3. What controlled mechanism, if any, assigns permanent identifiers before an
   EGR or EDR exists? PROC-0002 requires the repository index's registered
   numbering process and prohibits inference, but the reviewed repository does
   not expose an automated assignment transaction.
4. Is there an authoritative transaction boundary spanning Git, Work Registry,
   Project State, EOS state, and checkpoint selection, or only validated
   sequential reconciliation? The reviewed evidence demonstrates sequencing,
   not atomicity across all stores.
5. What is the authoritative lifecycle event for one accepted handoff when a
   persistent Codex process handles multiple turns? EWO-000020 proposed a
   mission model but was superseded before implementation.
6. Which observed interventions are unavoidable reserved Governance acts and
   which are operational publication work? This phase classifies the observed
   actions but does not decide delegability.
7. Are EGR-000003 and EGR-000004 `persistence_status: Pending` values current
   controlled truth or unreconciled metadata despite their committed Git
   publications? Resolving that question would require governing-record edits
   or a Governance disposition and is outside Phase 1.
8. EWO-000015 remains `Active` while later Project State names EWO-000023 as the
   primary authority. The evidence reviewed does not establish whether this is
   intended domain coexistence, historical lifecycle debt, or a conflicting
   active authority. No lifecycle change is inferred.

## Phase 1 Completion Assessment

Phase 1 completion requires an attributable inventory of recurring failures;
separation of Governance decisions, operational governance actions,
deterministic repository actions, and implementation execution; identification
of affected mechanisms and transitions; explicit unresolved questions, risks,
assumptions, and evidence gaps; and passing validation of the Phase 1 Drafts.

No architecture alternative, preferred design, recommendation, Draft EDR, or
implementation content is included. Phase 2 readiness is a sequencing result
only and does not itself authorize Phase 2 execution.

All Phase 1 completion criteria are met. Controlled-document, Work Registry,
repository, EOS, regression, checkpoint, persistence, context, and aggregate
Engineering Platform validation passed. Phase 1 is complete at the Draft
artifact boundary. Phase 2 is sequentially ready to begin only after an
explicit instruction to proceed under the still-Active EWO-000023; this
statement does not execute or independently authorize Phase 2.
