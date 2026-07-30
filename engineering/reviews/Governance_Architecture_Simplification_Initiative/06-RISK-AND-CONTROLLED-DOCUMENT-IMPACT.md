# Risk and Controlled-Document Impact

Date: 2026-07-30

Status: Proposed planning input

## 1. Risk assessment

| ID | Risk | Likelihood | Impact | Control |
| --- | --- | --- | --- | --- |
| GAS-RISK-001 | Simplification accidentally weakens review or approval gates. | Medium | Critical | Encode review, dual-control, timing, and effect conditions in the Authority Record and WOP qualification policy; negative qualification. |
| GAS-RISK-002 | A direct root Governance decision is mistaken for unrestricted bootstrap authority. | Medium | Critical | Require attributable identity, one subject, exact effects, expiry, signature, authority parent/root role, and denied effects. |
| GAS-RISK-003 | Legacy and v2 resolvers disagree during migration. | High | High | Shadow comparison, reason-coded differences, no silent fallback, staged cutover. |
| GAS-RISK-004 | Import broadens a current legacy authorization. | Medium | Critical | Narrowing proof, human adoption decision, exact source digest, independent review. |
| GAS-RISK-005 | Resource claims or containment rules omit a real collision previously prevented by global exclusivity. | Medium | High | Conservative unknown-resource behavior, typed resource taxonomy, collision tests, and exclusive leases for high-risk claims. |
| GAS-RISK-006 | Removing exact HEAD from long-lived mission authority permits stale intent. | Medium | High | Bind repository policy revision to the Authority Record and exact HEAD to WOP qualification and the execution attempt. |
| GAS-RISK-007 | Asynchronous projections create operator-visible lag. | High | Medium | Cursor/digest status, retry, freshness SLO, direct canonical resolver for protected actions. |
| GAS-RISK-008 | Mutable legacy contracts and immutable v2 events become dual writers. | Medium | Critical | One writer per phase, compatibility projection only, cutover lock, dual-write prohibition. |
| GAS-RISK-009 | WOP demotion removes necessary effect boundaries. | Low | Critical | Preserve exact requested/prohibited effects and bind the Authority Record, derived Mission Contract, and WOP digests in the resolver. |
| GAS-RISK-010 | Planning selection is mistaken for dispatch. | Medium | High | Domain-qualified outputs; selection record explicitly `grants_authority: false`. |
| GAS-RISK-011 | Direct Governance repair decisions bypass controlled review. | Medium | Critical | Same decision package, review, signature, validation, expiry, and audit rules as ordinary Governance; only authority parent differs. |
| GAS-RISK-012 | Historical records are reinterpreted under new semantics. | Medium | High | Preserve original files; use import/mapping records; no retroactive editing. |
| GAS-RISK-013 | Mission closeout and execution completion collapse again. | Medium | High | Separate execution outcome from `CLOSED` Governance event and planning completion. |
| GAS-RISK-014 | Single-principal operation is incorrectly implemented as self-review. | Medium | High | Preserve role and temporal separation, evidence review gates, and explicit combined-role declaration where Governance permits. |
| GAS-RISK-015 | Consumer migration misses a hidden legacy authority read. | High | High | Repository-wide consumer inventory, instrumentation, shadow telemetry, zero-consumer retirement proof. |
| GAS-RISK-016 | Authority event storage becomes corrupt or forked. | Low | Critical | Hash chain, signatures, monotonic sequence, create-only records, conflict detection, backups, independent replay. |
| GAS-RISK-017 | Governance absorbs planning or orchestration behavior through convenience APIs. | Medium | Critical | Enforce subsystem contracts: Governance policy/approval/authority/audit only; dependency and import tests reject EMP, Zeus, WOP, EENS, or EOS ownership leakage. |
| GAS-RISK-018 | The reduced state model hides a necessary distinction. | Low | High | Require reason-coded transitions and evidence; add a state only after a concrete scenario cannot be represented without ambiguity. |

## 2. Unresolved architecture decisions

These questions require a controlled architecture decision before
implementation:

1. What identifier, schema namespace, and repository location are normative
   for the Authority Record?
2. Is every mission authorization rooted directly in a Governance Decision, or
   may an existing Governance baseline delegate bounded mission-issuance
   authority?
3. What demonstrated requirement and review threshold would justify a future
   exceptional delayed-execution extension?
4. What conservative compatibility rule applies when a resource type or
   containment relation is unknown?
5. Can multiple missions hold compatible resource authorization while Zeus
   leases serialize exclusive execution claims?
6. Which repository policy revision, rather than exact HEAD, binds long-lived
   mission authority?
7. What signature/enrollment mechanism is normative for Governance Decision
   and authority-event records?
8. What is the exact disposition of the currently active
   `MC-MISSION-CONTRACT-PUBLICATION-001` at cutover?
9. Does the current WOP record become a work package or is a new package type
   required?
10. Which state views remain in PROJ-0001 after current-mission authority is
    removed?
11. What projection freshness threshold blocks protected execution, if direct
    canonical resolution already passes?
12. How are same-person decision, review, and execution roles separated in the
    current single-principal Alpha environment?
13. What initial resource taxonomy, identity grammar, and containment rules are
    normative?
14. What conformance checks prevent Governance APIs from acquiring EMP, Zeus,
    WOP, EENS, or EOS responsibilities?

## 3. Controlled-document change recommendations

Architecture Review Incorporation revised Draft `ARCH-0001`, `ADR-0001`, and
`SPEC-0002`. The remaining records in this table are recommended future
changes only and were not modified.

| Record | Recommended evolution |
| --- | --- |
| CHAR-0001 | Verify that direct attributable Chief Engineer decisions are already within ultimate authority; amend only if the root decision mechanism is not explicit. |
| POL-0001 | Replace Governance Bootstrap Continuity and the Temporary Mission Admission/Activation Directive with the permanent direct Governance Decision, Mission Authorization, and domain-state principles. |
| STD-0000 | Register Governance Decision, Authority Record, and derived Mission Contract roles without confusing decision, authority, contract, and evidence. |
| STD-0001 | Define immutable authority payloads plus append-only lifecycle events; domain-qualify lifecycle state. |
| STD-0002 | Define persistence and create-only event requirements for the authority ledger. |
| STD-0003 | Reconcile work-package authority references with Authority Records and derived Mission Contracts; eliminate duplicate authority definitions. |
| SPEC-0001 | Add typed authority-parent relationships and prohibit traceability relationships from conveying authority. |
| SPEC-0005 | Replace the current Mission Activation Service with `authorize-mission`, Authority Records, generalized resource conflicts, direct resolution, and nonblocking projections. |
| SPEC-0006 | Keep Work Registry planning-only; remove editable `authorized` management state and define read-only authority projection. |
| SPEC-0011 | Replace bootstrap exception semantics with permanent root Governance repair decisions, Authority Records, and derived Mission Contracts. |
| SPEC-0012 | Preserve runtime layers and gates but bind them to Authority Records and qualified WOPs; prohibit Progressive compatibility code from owning authority. |
| SPEC-0013 | Add assurance predicates for authority parent, event chain, effect narrowing, generalized resource leases, subsystem boundaries, and projection non-authority. |
| PROC-0001 | Establish the domain-separated workflow and stop defining Mission Contract as registry plus WOP. |
| PROC-0002 | Route Governance correction through the permanent decision mechanism; preserve EGR responsibilities where still applicable. |
| PROC-0004 | Make handoffs identify proposals or existing authority but never substitute for a Governance Decision or Authority Record. |
| PROC-0008 | Mature and approve the common Governance Decision procedure; add Authority Record issuance, Mission Contract derivation, and authority-ledger routing. |
| TPL-0001 | Recast WOP as immutable execution plan and remove authority-lifecycle terms. |
| TPL-0002 | Domain-qualify completion and distinguish proposed closeout from Governance closeout. |
| EDR-0002 | Record the ranked authority DAG, single-parent rule, narrowing, and root authority. |
| EDR-0003 | Define authority-ledger transaction, successor supersedence, idempotency, rollback, and receipt semantics. |
| PROJ-0001 | Retain technical project truth; render current mission/authority only as sourced projections or move it to a derived status view. |
| DOC-0001 | Register approved revisions and relationship classes after controlled adoption. |

## 4. Repository implementation impact

Future implementation will likely affect:

- `engineering/mission-contracts/` schemas, records, and transactions;
- `engineering/registry/` schema and projections;
- `engineering/execution/execution-interface.yaml`;
- WOP schemas and templates;
- `scripts/lib/eos/mission_contract.py`;
- `scripts/lib/eos/mission_activation.py`;
- `scripts/lib/eos/state_sync.py`;
- `scripts/lib/emp/controlled_mission_authority.py`;
- mission discovery, resolution, eligibility, admission, WOP lifecycle,
  dispatch, execution, qualification, reconciliation, and closeout consumers;
- Zeus and engctl status/CLI terminology;
- assurance declarations and validators;
- Progressive authority compatibility;
- operational documentation; and
- tests and qualification evidence.

This impact list is not implementation authorization.

## 5. Controlled adoption package

The next controlled review package should contain:

- this assessment and root-cause analysis;
- a proposed ADR answering section 2;
- an exact v1-to-v2 semantic mapping;
- Governance Decision, Authority Record, and derived Mission Contract examples;
- lifecycle diagrams;
- generalized resource taxonomy and conflict policy;
- document-by-document redline plan;
- implementation/qualification boundary;
- current active authority disposition; and
- migration rollback criteria.

## 6. Residual observations

- PROC-0001 and SPEC-0005 are Draft while runtime behavior already implements
  parts of their candidate architecture. Adoption must establish which
  revision is authoritative before implementation.
- PROC-0008 is a strong proposed decision foundation but remains Draft,
  Pending, and non-authoritative.
- SPEC-0006 is Active but its persistence metadata is Pending; the controlled
  baseline must reconcile lifecycle and persistence truth before depending on
  a revision.
- The working tree contains extensive pre-existing changes across controlled
  documentation and runtime. Any implementation mission needs an exact
  classified boundary or isolated worktree.
- ARCH-0001, ADR-0001, and SPEC-0002 remain Draft. Architecture Review
  Incorporation revised their Draft content only; it did not approve, activate,
  publish, or implement them.
