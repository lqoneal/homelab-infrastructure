# Governance Architecture Assessment

Date: 2026-07-30

Assessment status: Complete

Architecture status: Proposed only

Repository: `git@github.com:lqoneal/homelab-infrastructure.git`

Assessed branch and HEAD: `main` at
`d0861dc62b8199de03230152c4ed3cfb687dd9a7`

## 1. Assessment charter

This assessment evaluates the repository governance architecture for mission
authority, Mission Contracts, admission, activation, planning, Work Registry,
WOPs, execution, Project State, synchronization, lifecycle state, dependency
management, prioritization, and authority restoration.

It is based on repository evidence and does not modify technical behavior,
runtime implementation, Project State, Work Registry, Mission Contracts,
active mission state, Progressive state, or EOS state. The follow-on
Architecture Review Incorporation revised only the Draft architecture
documents and review/evidence artifacts identified in its completion report.

The review distinguishes:

- **Governance facts** — attributable decisions that grant, withhold, suspend,
  revoke, supersede, or close authority;
- **planning facts** — priority, sequence, dependency, deferral, and selected
  focus;
- **execution facts** — readiness, attempt state, checkpoints, outcomes, and
  blockers;
- **technical project facts** — current technical condition and accepted
  project baseline;
- **evidence facts** — immutable observations and receipts; and
- **projections** — reproducible views of facts owned elsewhere.

## 2. Evidence basis

The principal evidence reviewed was:

| Domain | Evidence |
| --- | --- |
| Governance policy | `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md` |
| Work execution | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` |
| Governance resolution | `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md` |
| Handoff construction | `docs/procedures/PROC-0004-ENGINEERING_HANDOFF_CONSTRUCTION_PROCEDURE.md` |
| Governance decisions | `docs/procedures/PROC-0008-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md` |
| Control framework | `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md` |
| Work Registry | `docs/specifications/SPEC-0006-ENGINEERING_WORK_REGISTRY_MODEL.md` |
| Authority restoration | `docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md` |
| Runtime governance | `docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md` |
| Project state | `docs/project/PROJ-0001-PROJECT_STATE.md` |
| Contract schemas and records | `engineering/mission-contracts/` |
| Registry schema and state | `engineering/registry/` |
| Operational documentation | `engineering/operations/` |
| Execution routing | `engineering/execution/execution-interface.yaml` |
| Mission authority code | `scripts/lib/eos/mission_contract.py`, `scripts/lib/eos/mission_activation.py`, `scripts/lib/emp/controlled_mission_authority.py` |
| Planning and WOP code | `scripts/lib/emp/wop_admission.py`, `scripts/lib/emp/wop_lifecycle.py`, `scripts/lib/emp/work_authority_lifecycle.py` |
| Execution and synchronization code | `scripts/lib/emp/mission_admission_runtime.py`, `scripts/lib/emp/mission_resolution.py`, `scripts/lib/eos/state_sync.py` |
| Prior convergence evidence | `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md`, `engineering/reviews/`, and 2026-07-25 authority-planning records |
| Architecture Review Incorporation | Chief Engineer review recommendations incorporated on 2026-07-30; recorded as supplemental engineering synthesis rather than historical repository evidence |

The worktree was materially dirty before this initiative. Existing changes
were treated as protected observations, not as changes belonging to this
assessment.

## 3. Current architecture

### 3.1 Authority origin

The repository consistently identifies Lawrence O'Neal, acting through the
authenticated `loneal` principal, as the ultimate engineering authority.
Engineering Governance makes decisions; Zeus resolves and enforces them but
does not originate authority.

This root model is conceptually sound. The principal defect is not the identity
of the authority owner. It is the route by which a bounded decision becomes
usable mission authority.

### 3.2 Mission authority representation

At least three representations participate in a mission-authority decision:

1. a YAML Mission Contract under `engineering/mission-contracts/contracts/`;
2. a Work Registry work item with an `authority_reference`; and
3. an immutable WOP with its own identity, lifecycle, authority binding,
   scope, and admission record.

PROC-0001 additionally describes “the Mission Contract” as the current Work
Registry work item plus any applicable WOP. The Mission Contract runtime,
however, treats the YAML record as the unique contract. These are competing
definitions of the same architectural term.

### 3.3 Admission

The repository contains multiple admission layers:

- manual Governance submission/admission in POL-0001 and PROC-0001;
- WOP syntax/package admission in `wop_admission.py`;
- Mission Contract admission inside `mission_activation.py`;
- supervised Mission Admission Runtime orchestration; and
- Stage 1 mission package admission.

The layers perform different jobs, but their names and results overlap.
Package validity, intentional Governance intake, authority validity, and
execution readiness are therefore easily mistaken for one another.

### 3.4 Activation

The Mission Activation Service requires:

- a candidate Mission Contract;
- an exact attributable approval;
- an already `Active` WOP;
- an existing Work Registry work item in `ready` or `active`;
- matching mission, registry, WOP, repository, branch, and exact HEAD;
- no unresolved registry dependency;
- no other active Mission Contract in the repository.

It then atomically rewrites:

- the Mission Contract;
- the Work Registry work item;
- PROJ-0001;
- activation evidence; and
- the derived EOS projection.

This makes one governance decision depend on pre-existing planning and WOP
lifecycle states and makes those non-authority records members of the
authority-creation transaction.

### 3.5 Planning and prioritization

SPEC-0006 correctly defines the Work Registry as the owner of operational
management facts and explicitly denies it execution-authority ownership.
Nevertheless, Mission Contract admission requires an eligible registry item,
and activation mutates that item. The registry is consequently non-authority
in its specification but a mandatory co-owner of authority availability in the
implementation.

The registry also uses `authorized` as a Mission management state. Although
the specification calls this a projection, the label is difficult to
distinguish operationally from actual authorization.

### 3.6 Execution

The repository has mature fail-closed execution primitives:

- immutable and digest-bound packages;
- repository and baseline verification;
- explicit requested and prohibited effects;
- append-only decision and evidence records;
- checkpointed execution;
- idempotency;
- independent qualification;
- explicit operator decisions; and
- separation of runtime state from authority.

These controls should be preserved. The simplification target is the authority
composition around them, not removal of execution safety.

### 3.7 Synchronization

`state_sync.py` correctly describes EOS as a deterministic projection.
Activation nevertheless requires EOS synchronization within the activation
transaction. This turns a derived view into a commit prerequisite for
authority creation and expands the rollback boundary outside the authority
record itself.

Project State, Work Registry, WOP Runtime, `.zeus`, Progressive state, central
evidence, WOP-local evidence, and EOS all contain legitimate facts. The
remaining problem is repeated current-mission or lifecycle data without one
enforced direction of derivation.

### 3.8 Authority restoration

SPEC-0011 detects missing normal authority, suspends execution, and requests
Governance verification. It then requires a controlled-document correction to
pass through the same normal authority path that is defective. This protects
against self-authorization but does not provide a durable, non-circular root
path for Governance to repair Governance.

The one-time authorization for this initiative proves the practical need for
such a path.

## 4. Architectural findings

| ID | Finding | Evidence | Confidence | Impact |
| --- | --- | --- | --- | --- |
| GAS-F-001 | The root human authority is clear, but the mechanism that records a mission decision is circular. | POL-0001; SPEC-0011; Mission Contract activation service | Verified | Critical |
| GAS-F-002 | “Mission Contract” has two authoritative-looking definitions: a YAML record and Work Registry item plus WOP. | PROC-0001; `mission_contract.py` | Verified | Critical |
| GAS-F-003 | Admission requires planning and WOP lifecycle facts that the new mission may not lawfully create before admission. | `Admission.decide` in `mission_activation.py` | Verified | Critical |
| GAS-F-004 | Replacement of an active mission is unsupported as one transaction because activation rejects every pre-existing active contract. | `ActivationService.activate` | Verified | Critical |
| GAS-F-005 | The contract schema exposes `superseded`, but the activation transaction does not atomically apply successor supersedence. | Mission Contract schema; activation code | Verified | High |
| GAS-F-006 | One-active-contract-per-repository conflates authority conflict, current planning focus, and execution concurrency. | Mission Contract schema; resolver and activation code | Verified | High |
| GAS-F-007 | Project State and Work Registry are drawn into authority activation despite owning different fact domains. | SPEC-0006; activation mutations | Verified | High |
| GAS-F-008 | EOS is defined as derived but its synchronization is an activation completion prerequisite. | SPEC-0005; `state_sync.py`; activation service | Verified | High |
| GAS-F-009 | Multiple admission layers reuse similar names for package acceptance, Governance intent, authority, and readiness. | PROC-0001; WOP, mission, and Stage 1 admission implementations | Verified | High |
| GAS-F-010 | Mission, WOP, gate, execution, registry, publication, Progressive, and Governance lifecycles overlap without a shared domain qualifier. | schemas, PROC-0001, runtime documentation | Strongly Supported | High |
| GAS-F-011 | Exact HEAD binding is applied at Mission Contract admission even when mission authority should survive harmless repository advancement. | `Admission.decide`; resolver | Verified | Medium |
| GAS-F-012 | Mission Contracts contain broad operational roles and closeout/synchronization data that do not all define authority. | Mission Contract schema and instances | Verified | Medium |
| GAS-F-013 | Existing append-only evidence, signatures, exact effect boundaries, idempotency, and independent qualification provide strong reusable controls. | authority publication, WOP, execution, and Progressive records | Verified | Positive |
| GAS-F-014 | The 2026-07-25 four-graph-domain proposal already provides a valid basis for separating authority from workflow and traceability. | `2026-07-25-governance-authority-dag-architecture.md` | Verified | Positive |
| GAS-F-015 | Draft PROC-0008 contains a suitable generic attributable-decision pattern but is not Active authority. | PROC-0008 | Verified | High |
| GAS-F-016 | Treating the Mission Contract as the authorization conflates the authoritative Governance grant with the execution-facing mission representation derived from it. | Mission Contract schema, activation service, and Architecture Review Incorporation | Strongly Supported | Critical |
| GAS-F-017 | Repository-scoped conflict keys cannot describe exclusive or shared use of infrastructure, services, hardware, environments, documents, and future governed resources without type-specific additions. | Mission Contract schema, activation service, and Architecture Review Incorporation | Strongly Supported | High |
| GAS-F-018 | Governance responsibilities remain vulnerable to orchestration creep unless policy, approval, authority, and audit are explicitly separated from EMP planning, Zeus orchestration, WOP packaging, EENS observation, and EOS synchronization. | current admission/activation composition and Architecture Review Incorporation | Strongly Supported | High |
| GAS-F-019 | Composite lifecycle vocabularies create avoidable coupling; Governance disposition, execution progress, and synchronization condition can be represented as small orthogonal state models. | schemas, procedures, runtime documentation, and Architecture Review Incorporation | Strongly Supported | High |

## 5. Complexity inventory

The architecture currently distributes one mission-start decision across:

| Concern | Current owner or participant | Assessment |
| --- | --- | --- |
| Governance intent | Governance submission, approval record | legitimate authority fact |
| Mission scope and permissions | YAML Mission Contract, WOP, registry | duplicated |
| Admission | policy, WOP admission, Mission Contract admission, mission runtime, Stage 1 | overloaded term |
| Activation | Governance state plus multi-record repository transaction | unnecessary second authorization |
| Priority | Work Registry and WOP lifecycle queue | legitimate planning fact |
| Dependencies | Work Registry, WOP prerequisites, gate prerequisites | legitimate at distinct layers; names need qualification |
| Current mission | Mission Contract resolver, Project State, Work Registry, EOS, Progressive package | duplicated projection |
| Readiness | activation admission checks, mission qualification, WOP lifecycle, gate eligibility | repeated |
| Synchronization | activation, EOS sync, closeout reconciliation | derived view treated as authority prerequisite |
| Completion | Governance, execution, registry, WOP, gate, document, and publication state | domain qualification required |

The problem is architectural coupling, not the number of safety checks. Most
checks remain useful when assigned to one domain and evaluated at the correct
boundary.

## 6. What should be preserved

The redesign should preserve:

- ultimate human Governance authority and authenticated attribution;
- explicit scope and denied effects;
- immutable digests and signed decisions;
- one authority parent per authority-bearing record;
- fail-closed resolution;
- review separation;
- independent qualification;
- append-only history;
- idempotent transactions;
- repository identity validation;
- exact baseline binding for execution attempts and publications;
- evidence lineage;
- suspension, revocation, supersedence, and expiry;
- deterministic projections; and
- compatibility evidence until consumers are proven migrated.

## 7. What should be eliminated

The redesign should eliminate:

- the need for a pre-existing mission to authorize creation of its own
  authority;
- separate Governance Admission and Activation decisions for the same scope;
- the Work Registry and Project State as co-owners of mission authority;
- an `Active` WOP as a prerequisite for creating mission authority;
- the global one-active-contract rule;
- exact HEAD as the long-lived mission-authority identity;
- synchronous projection writes inside authority creation;
- editable duplicate mission descriptions;
- generic traversal of traceability relationships as authority;
- reverse synchronization from projections; and
- bootstrap consultation that cannot itself produce a durable root decision.

## 8. Assessment conclusion

The repository has strong safety primitives but an over-coupled mission
authority composition. The shortest safe simplification is not to remove
validation. It is to establish one immutable, directly attributable Authority
Record from a Governance Decision, derive the Mission Contract from that
record, demote every planning and runtime record to its proper domain, and
evaluate readiness only after authority exists. Standard execution requires a
qualified WOP, not a second Execution Grant. Concurrency is governed through a
resource-type-neutral conflict model, and Governance remains limited to
policy, approval, authority, and audit.
