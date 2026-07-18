---
document_id: EWO-000023-PHASE-2-ALTERNATIVES
title: EWO-000023 Phase 2 Alternative Architecture Evaluation
version: 0.1
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Alternative Architecture Evaluation
domain: Engineering Governance
classification: Alternative Architecture Evaluation
source_of_truth: true
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Persisted
related_documents:
  - EWO-000023
  - EWO-000023-PHASE-1-INVESTIGATION
  - EWO-000023-PHASE-2-EVIDENCE
  - EWO-000023-PHASE-2-COMPARATIVE-ANALYSIS
  - EWO-000023-PHASE-2-OWNERSHIP
tags:
  - alternative-architecture
  - governance-authority
  - phase-2
  - draft
---

# Alternative Architecture Evaluation


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


## Evaluation Boundary

This Draft evaluates materially distinct corrective architectures under
EWO-000023 Revision 1 Phase 2. It does not select a preferred architecture,
prepare an EDR, recommend implementation sequencing, modify governance, grant
or exercise delegation, or implement any capability.

Phase 1 artifacts are preserved unchanged. All evidence identifiers resolve to
`EWO-000023-PHASE-2-EVIDENCE`. Ratings are comparative engineering judgments
for this investigation only:

- `Strong`: the alternative directly satisfies the criterion with bounded
  residual risk supported by current evidence;
- `Moderate`: the criterion can be satisfied but requires material new
  controls, qualification, or operating discipline;
- `Weak`: the criterion has substantial unresolved risk or does not fully
  close the Phase 1 discontinuity; and
- `Prohibited`: the architecture would conflict with current superior
  authority and is not eligible for evaluation as a corrective solution.

## Common Constraints

Every eligible alternative must preserve these non-negotiable boundaries:

1. Engineering Governance remains the ultimate Governance Authority (P2-E01,
   P2-E02, P2-E03).
2. Only an Active EWO conveys bounded implementation authority; registry,
   command, Git, metadata, service, and derived state cannot self-authorize
   (P2-E03 through P2-E07).
3. Lifecycle transitions require attributable approval evidence and preserve
   lifecycle, approval, and persistence as distinct states (P2-E04, P2-E05).
4. Operational projections remain traceable to one controlled information
   owner and cannot replace it (P2-E03, P2-E06, P2-E07).
5. Governance gaps cannot be silently corrected, and execution stops when a
   Governance disposition is required (P2-E08, P2-E09).
6. No alternative is implementable directly from this evaluation. Each would
   require later approved controlled decisions, specifications where
   applicable, Work Orders, validation, and qualification (P2-E04, P2-E10,
   P2-E11).

## Alternative A — Minimal-Change Governed Transition Protocol

### Architecture

Alternative A preserves the current decision and authority model. Engineering
Governance continues to make every approval, activation, acceptance,
supersedence, deferral, and successor-work decision. The corrective change is
a standardized, evidence-complete transition protocol that makes each
Governance decision consumable as one bounded repository publication
transaction.

The protocol would define a complete authorization transaction packet:

- authenticated approval reference supplied by Engineering Governance;
- exact disposition, controlled subjects, revisions, permitted effects, and
  expiry;
- explicit successor or no-successor disposition at mission closeout;
- deterministic change manifest for EGR/EWO, DOC-0001, Project State, Work
  Registry, evidence/report, Git, EOS, and checkpoint projections;
- preconditions, validation gates, idempotency key, failure journal, rollback
  or forward-recovery boundary, and completion receipt; and
- a mandatory stop when the approval payload is absent, ambiguous, or exceeds
  the protocol.

It eliminates avoidable publication ambiguity and orphaned next-action state,
but it does not eliminate the need for Engineering Governance to decide each
successor transition. This is consistent with the current model, where an
operator handoff is the approval act and a separate bounded transaction
publishes it (P2-E12, P2-E13).

### Identical-Criteria Evaluation

| Criterion | Rating | Advantages | Disadvantages / residual exposure | Evidence |
| --- | --- | --- | --- | --- |
| Preservation of Engineering Governance authority | Strong | All dispositions remain reserved to Governance; the protocol only represents supplied decisions | Manual Governance availability remains a prerequisite | P2-E01 through P2-E04, P2-E08 |
| Governance lifecycle integrity | Strong | Standardized approval payload and transaction receipt reinforce attributable transitions | Cannot prevent an incomplete or inconsistent Governance decision before protocol entry | P2-E04, P2-E05, P2-E09 |
| Repository lifecycle integrity | Strong | Explicit manifest covers all observed controlled and operational projections | Cross-store effects remain sequential unless a later persistence design supplies stronger transactions | P2-E12 through P2-E15 |
| Deterministic execution | Strong | Fixed inputs, preconditions, path manifest, idempotency, and validators bound the publication action | Novel decisions still require manual interpretation before the deterministic boundary | P2-E08, P2-E09, P2-E12, P2-E13 |
| Auditability | Strong | Approval reference, evidence manifest, journal, commit, and receipt form a reconstructable chain | Audit quality depends on the external approval act carrying adequate identity evidence | P2-E05, P2-E12, P2-E13, P2-E16 |
| Traceability | Strong | Uses existing EGR/EWO/evidence/index/checkpoint relationships | Fan-out remains verbose and can drift if protocol enforcement is incomplete | P2-E03, P2-E05, P2-E12 through P2-E15 |
| Qualification requirements | Moderate | Existing validators and platform qualification provide a substantial base | New transaction completeness, idempotency, partial-failure, and approval-authenticity tests are required | P2-E09, P2-E14, P2-E17 |
| Authority boundaries | Strong | Decision, publication, deterministic operation, and implementation remain explicitly separate | Human actors must consistently distinguish approval from publication execution | P2-E08, P2-E12, P2-E13 |
| Revocation capability | Moderate | Governance can supersede/revoke through existing controlled lifecycle | No immediate runtime revocation channel; revocation takes effect through another publication transaction | P2-E04, P2-E05, P2-E13 |
| Publication workflow | Strong | Directly targets the observed publication discontinuity with minimal new concepts | Still requires a separate publication action and subsequent wrapped implementation launch | P2-E12 through P2-E15 |
| Implementation complexity | Strong | Primarily controlled document, template, validator, and controller workflow changes | Robust partial-failure recovery across Git/EOS/registry is not trivial | P2-E09, P2-E14, P2-E17 |
| Autonomous engineering compatibility | Moderate | Agents can execute a complete supplied decision deterministically | Agents cannot proceed when Governance has not supplied a disposition, so unattended continuity remains limited | P2-E08, P2-E09, P2-E16 |
| Failure containment | Strong | Narrow transaction scope, explicit manifest, idempotency, and stop conditions constrain effects | A flawed approval packet may be faithfully propagated across many projections | P2-E12, P2-E13, P2-E15 |
| Backward compatibility | Strong | Retains EGR, EWO, lifecycle, Work Registry, EOS, and Git semantics | Legacy records may lack new packet fields and require compatibility rules | P2-E03 through P2-E07, P2-E12 |
| Operational maintainability | Moderate | Few new service components; existing operators and tools remain recognizable | Manual decision/publication coordination and multi-file fan-out remain recurring operating costs | P2-E12 through P2-E15 |

### Engineering Rationale

Alternative A is the lowest-change response to AG-02 through AG-04. It can
permanently standardize how a decision crosses into repository state, prevent
silent omission of successor disposition, and make recovery deterministic.
It only partially addresses AG-01 because a genuinely new Governance decision
still requires Governance participation. That limitation is a consequence of
preserving the present reservation of transition authority, not an unsupported
implementation defect (P2-E03 through P2-E05).

### Dependencies and Assumptions

- Governance can provide an attributable, machine-readable approval reference.
- Existing EGR/EWO lifecycle semantics remain unchanged.
- Existing validators can be extended without acquiring approval authority.
- Git, registry, EOS, and checkpoint effects can be made idempotent or safely
  recoverable even if they cannot be one atomic transaction.

## Alternative B — Bounded Delegated Operational Governance

### Architecture

Alternative B establishes controlled delegation grants by which Engineering
Governance pre-authorizes a narrowly defined class of operational governance
decisions. A qualified delegate—human role or deterministic agent—may perform
only transitions matching the grant's predicates. Novel, ambiguous, high-risk,
foundational, baseline-changing, or out-of-policy decisions remain reserved to
Engineering Governance.

A delegation grant would require a controlled identity, delegator, delegate,
decision class, subject scope, allowed transition, required evidence,
preconditions, quantitative limits, start/expiry, use count or nonce,
revocation state, escalation rules, audit obligations, and prohibition on
subdelegation. The delegate's output would still be an attributable controlled
EGR/EWO lifecycle transaction; the grant would not make Work Registry or agent
state authoritative.

Current governance permits lifecycle delegation only when superior governance
explicitly delegates it, while STD-0000 says only Engineering Governance may
approve or activate an EWO unless superior governance establishes another
controlled authorization mechanism (P2-E03, P2-E04). Therefore Alternative B
is architecturally possible only after explicit superior-governance change; it
cannot be inferred from current procedure or implemented under EWO-000023.

### Identical-Criteria Evaluation

| Criterion | Rating | Advantages | Disadvantages / residual exposure | Evidence |
| --- | --- | --- | --- | --- |
| Preservation of Engineering Governance authority | Moderate | Governance defines, limits, audits, and revokes each delegation; ultimate authority remains with Governance | Delegate performs decisions currently reserved to Governance; an incomplete superior delegation would violate current rules | P2-E01 through P2-E04 |
| Governance lifecycle integrity | Moderate | Formal grants can make routine transitions explicit and attributable | Adds grant lifecycle plus target lifecycle, increasing invalid-state and precedence combinations | P2-E04, P2-E05 |
| Repository lifecycle integrity | Moderate | Delegate can execute the same controlled transaction manifest as A | More actors and grant checks increase concurrency, stale-grant, and replay risks | P2-E05, P2-E09, P2-E12 through P2-E15 |
| Deterministic execution | Strong for bounded classes | Predicate-matched decisions can be reproducible without waiting for case-by-case Governance action | Natural-language scope or incomplete predicates would make delegation nondeterministic and require escalation | P2-E08, P2-E09, P2-E16 |
| Auditability | Strong | Grant identity, decision inputs, evaluation result, delegate identity, and receipt can be recorded | Audit volume and correlation increase; audit cannot cure an overbroad grant | P2-E05, P2-E10, P2-E16 |
| Traceability | Strong | Every delegated action can cite both superior grant and resulting EGR/EWO | Requires new relationships and one authoritative owner for grant state | P2-E03 through P2-E05 |
| Qualification requirements | Weak to Moderate | Deterministic policy tests can cover authorized classes | Requires exhaustive boundary, negative, expiry, revocation, replay, concurrency, compromise, and escalation qualification | P2-E04, P2-E10, P2-E11 |
| Authority boundaries | Moderate | Explicit reserved/delegated taxonomy can clarify boundaries | Taxonomy is currently incomplete; boundary errors directly risk authority expansion | P2-E03, P2-E04, P2-E16 |
| Revocation capability | Moderate | Grants can include immediate expiry, explicit revocation, and no-subdelegation | Repository-only revocation may not reach an offline or already-running delegate before use | P2-E04, P2-E05, P2-E10 |
| Publication workflow | Strong | Qualified routine transitions can be decided and published without a new manual Governance handoff | Exceptional cases still return to manual Governance; grant publication itself needs controlled approval | P2-E12, P2-E13, P2-E16 |
| Implementation complexity | Weak | No mandatory always-on broker is required | Policy evaluator, grant model, cryptographic identity, revocation, audit, validators, and migration are substantial | P2-E10, P2-E11, P2-E17 |
| Autonomous engineering compatibility | Strong | Qualified agents can advance bounded routine lifecycles from controlled inputs | Autonomous misuse or policy drift has direct Governance consequences | P2-E06, P2-E07, P2-E10, P2-E16 |
| Failure containment | Moderate | Scope, limits, expiry, and no-subdelegation can bound blast radius | Overbroad grants, stale caches, replay, or compromised delegates may create multiple invalid transitions | P2-E04, P2-E05, P2-E10 |
| Backward compatibility | Moderate | Resulting EGR/EWO records can retain existing forms | Current rule that Governance controls transitions must be explicitly revised; legacy consumers will not understand grants | P2-E03 through P2-E05 |
| Operational maintainability | Weak to Moderate | Reduces repetitive case-by-case decisions once mature | Grant issuance, rotation, revocation, exception handling, audit review, and policy versioning create a new governance operation | P2-E04, P2-E10, P2-E16 |

### Engineering Rationale

Alternative B most directly reduces AG-01 for routine, fully classifiable
transitions because the required Governance decision is made in advance as a
bounded delegation. It also addresses AG-02/AG-03 when paired with a
deterministic publication protocol. Its central disadvantage is that the
delegation model itself changes the current transition-authority boundary and
requires a presently missing reserved/delegable decision taxonomy (P2-E16).

### Dependencies and Assumptions

- Superior governance explicitly permits each delegated transition class.
- An authoritative delegation-grant owner and common lifecycle are defined.
- Delegate identity, authentication, non-replay, expiry, revocation, and audit
  evidence can be qualified.
- Every input predicate is machine-evaluable; ambiguity escalates without
  action.
- Delegates cannot subdelegate or enlarge their own grants.

## Alternative C — Governance Authority Broker / EGAS

### Architecture

Alternative C introduces a Governance Authority Broker, consistent in concept
with the developing EGAS Authorization Layer in SPEC-0007. The broker accepts
authenticated authorization requests, resolves current controlled authority,
routes reserved decisions to Engineering Governance, captures the attributable
decision, validates allowed effects, and coordinates durable publication of
the resulting EGR/EWO lifecycle transaction. Implementation agents consume
only broker-issued, repository-verifiable Active EWOs.

In the conservative form evaluated here, the broker does not originate or
choose Governance dispositions. It mediates them. If later configured to
execute delegated rules, that portion inherits Alternative B's superior
authorization, revocation, and qualification requirements.

The broker requires explicit service contracts for identity/authentication,
authorization request schema, authority resolution, policy versioning,
decision capture, audit ledger, idempotency, consistency, recovery,
revocation, availability, fail-closed behavior, repository publication, EOS
projection, and client interfaces. SPEC-0007 itself marks Authorization
Architecture as Developing and Platform Services as Planning and requires
dedicated controlled specifications before implementation (P2-E10).

### Identical-Criteria Evaluation

| Criterion | Rating | Advantages | Disadvantages / residual exposure | Evidence |
| --- | --- | --- | --- | --- |
| Preservation of Engineering Governance authority | Strong in broker-only mode | Governance remains decision maker; broker authenticates, records, and enforces supplied decisions | Service wording that it “authorizes” could be misread as originating authority unless superior boundaries are explicit | P2-E01 through P2-E04, P2-E10 |
| Governance lifecycle integrity | Strong | Central mediation can enforce common lifecycle, approval, evidence, and transition rules | Broker defects or policy-version drift could affect every transition | P2-E04, P2-E05, P2-E10 |
| Repository lifecycle integrity | Strong | One coordinator can journal and recover multi-projection publication | True atomicity across Git, EOS, registry, and external audit storage is unresolved | P2-E10, P2-E12 through P2-E15 |
| Deterministic execution | Strong | Versioned request schemas, policy inputs, idempotency, and fail-closed state machines support reproducibility | Reserved human decisions remain nondeterministic inputs until captured; distributed consistency requires specification | P2-E09, P2-E10, P2-E17 |
| Auditability | Strong | Central decision/event ledger can correlate request, identity, policy, decision, effects, and receipt | Ledger becomes sensitive critical infrastructure requiring integrity, retention, and independent verification | P2-E05, P2-E10, P2-E16 |
| Traceability | Strong | Broker can enforce end-to-end identifiers and relationships across request, decision, EWO, execution, and evidence | Central correlation failure could impair all consumers; controlled records must remain authoritative | P2-E03, P2-E06, P2-E10 |
| Qualification requirements | Weak initially | Service boundary makes systematic conformance testing possible | Requires security, identity, authorization, consistency, recovery, availability, failover, revocation, replay, and end-to-end qualification | P2-E10, P2-E11, P2-E17 |
| Authority boundaries | Strong if specified | Distinct request, Governance decision, broker enforcement, publication, and execution roles can be technically enforced | An overly capable broker could become a de facto competing Governance Authority | P2-E01 through P2-E04, P2-E10 |
| Revocation capability | Strong | Broker can deny new uses immediately and publish revocation events centrally | Offline agents and already-started work still need repository-verifiable revocation semantics and safe interruption rules | P2-E04, P2-E10 |
| Publication workflow | Strong | Broker directly mediates decision capture and coordinated repository publication | Broker availability becomes part of every governed transition; manual break-glass path is required but risky | P2-E10, P2-E12 through P2-E15 |
| Implementation complexity | Weak | Consolidates fragmented lifecycle logic behind one contract | Highest design, security, persistence, deployment, operations, and migration complexity | P2-E10, P2-E11, P2-E17 |
| Autonomous engineering compatibility | Strong | Stable request/status/receipt APIs can support multiple agents without granting them Governance Authority | Agents depend on broker availability and correct identity/policy resolution | P2-E06, P2-E07, P2-E10 |
| Failure containment | Moderate | Fail-closed broker, scoped transactions, and central revocation can contain invalid actions | Centralized broker and policy defects have platform-wide blast radius; availability failure can halt all new work | P2-E10, P2-E11 |
| Backward compatibility | Moderate | Broker can emit current EGR/EWO and registry forms and support existing clients through adapters | New service, request objects, identity, and event contracts are absent from current operational baseline | P2-E03, P2-E05, P2-E10, P2-E11 |
| Operational maintainability | Moderate | Centralizes duplicated transition logic, audit, and recovery | Requires continuous security maintenance, monitoring, backups, schema evolution, incident response, and break-glass governance | P2-E10, P2-E11, P2-E17 |

### Engineering Rationale

Alternative C directly addresses AG-02 through AG-05 by giving approval
capture, mission identity, publication, recovery, and audit a single mediated
contract while leaving controlled records authoritative. It can also host
Alternative B-style delegation later, but broker mediation and delegation are
separate architectural choices. Its main costs are critical-service
complexity, systemic blast radius, and incomplete current specifications.

### Dependencies and Assumptions

- Governance decisions can be authenticated and represented without the
  broker selecting them.
- Controlled repository records remain authoritative; the service database or
  ledger does not silently replace them.
- Dedicated identity, authorization, audit, security, persistence,
  qualification, and service-interface specifications are approved first.
- The broker fails closed and supplies a separately governed break-glass path.
- Existing EGR/EWO consumers can be supported during migration.

## Cross-Alternative Tradeoffs

| Tradeoff axis | Alternative A | Alternative B | Alternative C |
| --- | --- | --- | --- |
| Where decision latency remains | Human Governance for every transition | Only reserved/exception transitions | Human Governance for reserved decisions; broker removes publication latency |
| New authority semantics | None | Material: controlled delegation grants | None in broker-only form; material if delegation added |
| New critical runtime | No | Policy/grant evaluator may be local | Yes, authority broker and audit/persistence dependencies |
| Primary discontinuity closed | Publication and projection consistency | Routine successor decision plus publication | Decision mediation, publication, identity, and coordinated lifecycle |
| Principal risk | Manual bottleneck persists | Delegation overreach or revocation failure | Central critical-service defect or outage |
| Compatibility | Highest | Medium | Medium |
| Initial qualification burden | Lowest | High | Highest |

## Implementation Impact Comparison

These are impact areas, not sequencing recommendations.

- Alternative A affects governance procedures/templates, transition evidence,
  validators, controller publication commands, and recovery rules. It need not
  add a daemon or new authority object.
- Alternative B affects superior governance, lifecycle standards, delegation
  representation, identity, policy evaluation, validators, audit, revocation,
  procedures, and agent clients. It adds a new authority-bearing controlled
  mechanism even if implemented without a service.
- Alternative C affects controlled service specifications, identity/security,
  authorization request representation, EGAS interfaces, audit/persistence,
  controllers, registry/EOS adapters, monitoring, recovery, and operational
  support. It adds a critical runtime service but need not delegate decisions.

## Risks Common to All Eligible Alternatives

| Risk | Consequence | Evidence basis |
| --- | --- | --- |
| Approval identity is insufficient | Invalid decision may be faithfully published | Phase 1 external handoff evidence gap; P2-E12, P2-E13, P2-E16 |
| Lifecycle and persistence are conflated | Commit or metadata could be mistaken for activation | P2-E04, P2-E05 |
| Registry/EOS projection is elevated | Derived state could be mistaken for Governance Authority | P2-E03, P2-E06, P2-E07 |
| Cross-store partial failure | Resume may see conflicting authority projections | P2-E12 through P2-E15 |
| Revocation is not observed | Stale agent may act under expired authority | P2-E04, P2-E10 |
| Autonomous client retries replay an action | Duplicate or conflicting transitions | P2-E09, P2-E10 |
| Break-glass mechanism becomes normal path | Governance controls are bypassed | P2-E01, P2-E08, P2-E12 |
| New mechanism lacks one information owner | Competing authority records emerge | P2-E03, P2-E06 |

## Rejected or Ineligible Candidates

### Work Registry as Governance Authority

Rejected as ineligible. EMP and its Work Registry explicitly do not authorize
execution or manage controlled-document lifecycle. Elevating registry state
would create a competing authority source and violate current information
ownership (P2-E06, P2-E07).

### Implementation-Agent Self-Authorization

Rejected as prohibited. Agents may prepare evidence and Drafts but cannot
infer Governance intent, select a disposition, approve, activate, or create
their own execution authority (P2-E01 through P2-E04, P2-E08, P2-E09).

### Git-Commit or Metadata Activation

Rejected as ineligible. Lifecycle, approval, and persistence are independent;
neither a commit nor a metadata edit may independently perform a lifecycle
transition (P2-E04, P2-E05).

### Unconstrained Autonomous Governance Agent

Rejected as prohibited. No reviewed authority delegates ultimate Governance
Authority to an autonomous agent, and derived or implementation systems do not
acquire authority by processing controlled information (P2-E01 through
P2-E03).

These candidates were screened out before comparative scoring because they do
not satisfy the non-negotiable authority boundary. They are not fourth
alternatives and were not used to bias selection among A, B, and C.

## Unresolved Questions

1. Which exact transition decisions must remain reserved to Engineering
   Governance, and can any be delegated by Policy or Standard without a Charter
   amendment?
2. What authenticates the external Governance decision and binds its identity,
   scope, content, and date to the repository transaction?
3. Is cross-store atomicity required, or is a durable journal with deterministic
   forward recovery sufficient?
4. How does revocation affect already-started work versus unused authority?
5. What availability and recovery objective is acceptable for a broker that can
   halt new engineering execution?
6. Does a delegation grant fit an existing controlled class, or does its unique
   authority, lifecycle, and revocation state justify a new class?
7. Should EGAS be purely a broker of Governance decisions, a delegated policy
   decision point, or two separately qualified components?
8. What independent audit mechanism verifies the broker or delegate that
   produces the primary audit record?
9. How are legacy Active EWOs and pending persistence metadata handled without
   retroactive authority or history rewriting?
10. What is the canonical engineering mission identity across persistent agent
    processes and multiple handoffs?

## Phase 2 Non-Selection Statement

All three required alternatives have been fully evaluated. No preferred
architecture is selected in this document. Relative ratings and tradeoffs are
inputs to later Phase 3 decision work only if Engineering Governance separately
authorizes Phase 3.

Phase 2 completion criteria are satisfied: all alternatives received the same
15-criterion evaluation with advantages, disadvantages, authority and
lifecycle implications, ownership, impacts, risks, dependencies, assumptions,
unresolved questions, rejected-candidate rationale, and attributable evidence.
Validation passed. Phase 3 is sequentially ready but has not begun and is not
authorized by this completion statement.
