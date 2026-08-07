# Managed Handoff Execution / Provider Authorization Convergence Assessment

Date: 2026-08-07
Mission context: `MISSION-BETA-562F443E16C69401`
Current boundary: P5-G6 accepted; publication/reconciliation pending
Assessment status: planning only; implementation not authorized

## 1. Executive finding

Zeus already owns most of the execution substrate required for managed handoff
execution: WOP intake, mission/WOP binding, provider selection, dispatch
artifacts, provider sessions, provider invocation, execution-start, managed
Codex session identity, runtime rematerialization, monitoring, verification,
replay, and evidence projection. The current P5-G6 active demonstration confirms
that the execution and monitoring layers can converge on one live execution.

The missing convergence is not a second execution system. Zeus has no canonical
handoff/work-request object or native submission boundary that packages an
authorized engineering request for an already-bound execution and translates
that authority into a provider action decision. `zeus submit <wop>` is the
canonical intake boundary, while `zeus codex ...` is the managed-session
boundary; neither is currently a general handoff submission contract.

The minimum future change is therefore a thin handoff envelope and provider-
authorization translation layer built on existing identities and projections.
It must derive authority from existing mission, WOP, gate, approval, execution,
provider, session, and next-action state. It must not introduce a second
acceptance database, a parallel authority model, or unrestricted host execution.

`P5-G6_IMPLEMENTED_CAPABILITY=controlled active execution foundation`
`FOLLOW_ON_PLANNED_CAPABILITY=Managed Handoff Execution / Provider Authorization Convergence`

This assessment does not implement the capability, mutate WOP packages, alter
roadmap state, or change the active execution.

## 2. Inspection boundary and sources

Repository initiation recorded:

| Item | Observation |
|---|---|
| Repository root | `/data/engineering/repositories/homelab` |
| Repository identity | `homelab-6bd83f9079d6fc57` (authoritative session binding) |
| Branch | `main` |
| HEAD / origin/main | `6efa815a10e80a79326339ca106f6f9e3503b664` / same |
| Working tree | Pre-existing Phase 5, roadmap, WOP, acceptance, and evidence changes present; preserved |
| Active execution | Preserved; no start, stop, supersession, or provider mutation performed |
| P5-G6 state | Accepted through existing manual decision and Zeus reconciliation; publication and P5-G7 remain unauthorized |

Inspected implementation and controlled sources included:

* `scripts/zeus` — parser, dispatch, `submit`, `dispatch`, provider-session,
  provider-invocation, execution-start, Codex, execution, gate, and acceptance
  command surfaces.
* `scripts/lib/emp/codex_adapter.py` — Zeus-owned Codex session identity,
  process binding, session history, rematerialization, liveness, events, and
  interruption/supersession controls.
* `scripts/lib/emp/provider_selection.py`, `provider_session.py`,
  `provider_invocation.py`, `execution_start.py`, `execution_monitoring.py`,
  and `execution_authorization.py` — Phase 5 provider and execution chain.
* `scripts/lib/emp/gate_approval.py` and the P5-G6 acceptance reconciliation
  tests — existing gate approval and acceptance-record behavior.
* `scripts/tests/test-zeus-p5-g1-provider-selection.py`, P5-G2/G3/G4/G5/G6
  tests, Codex interactive/adapter tests, WOP submission/dispatch tests, and
  authority/approval tests.
* `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md` and
  `ZEUS-WOP-SUBMISSION-PROCEDURE.md` — Stage 1 and submission ownership.
* `engineering/docs/cli/ZEUS-USER-GUIDE.md` — operator-facing dispatch,
  provider, execution-start, Codex, monitoring, and approval contracts.
* `engineering/operations/ZEUS-AUTONOMOUS-DISPATCH-PROCEDURE.md`,
  `zeus-mission-execution-runtime.md`, `zeus-operator-interface.md`, and
  `authority-ownership-specification.md` — authority and dispatch boundaries.
* `engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md` —
  canonical WOP identity, scope, authority distinction, and metadata rule.
* `engineering/evidence/operation-beta/p5-g6-controlled-active-execution-foundation-completion-report.md` —
  accepted P5-G6 active execution, managed Codex, monitoring, and acceptance
  evidence.
* `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` and the
  current `SPEC-0001` references resolved by the controlled documentation.

## 3. Current handoff architecture

### 3.1 Canonical concepts and ownership

There is no distinct canonical `HANDOFF` object, identity, store, status
projection, or verification interface. The current functions are distributed
as follows:

| Handoff function | Current canonical owner |
|---|---|
| Engineering instruction and scope | WOP contract and package |
| Mission and authority binding | Mission Contract / Operation Beta authority resolution |
| Intake | `scripts/zeus submit` and Stage 1 runtime |
| Provider choice | `provider_selection.py` and integrity-bound execution-agent registry |
| Dispatch | `provider_invocation.py` and dispatch artifacts |
| Provider session | `provider_session.py` |
| Execution identity/start | `execution_start.py` |
| Managed Codex identity/process | `codex_adapter.py` |
| Active execution projection | `execution_monitoring.py` |
| Gate acceptance | `gate_approval.py` and Zeus acceptance reconciliation |
| Human-readable evidence | controlled evidence reports and receipts |

Therefore:

```text
HANDOFF_CONCEPT_EXISTS=NO_DISTINCT_OBJECT
HANDOFF_CANONICAL_OBJECT=WOP_PLUS_BOUND_EXECUTION_CHAIN
HANDOFF_CANONICAL_OWNER=NO_SINGLE_OWNER; FUNCTIONS OWNED BY ZEUS SUBSYSTEMS
HANDOFF_IDENTITY_EXISTS=NO_HANDOFF_ID; EXISTING MISSION/WOP/EXECUTION/SESSION IDS EXIST
HANDOFF_PERSISTENCE_EXISTS=NO
HANDOFF_MISSION_BINDING=YES, THROUGH WOP/MISSION/EXECUTION ARTIFACTS
HANDOFF_WOP_BINDING=YES
HANDOFF_GATE_BINDING=YES WHERE WOP/ROADMAP CONTRACT RESOLVES IT
HANDOFF_EXECUTION_BINDING=YES AFTER EXECUTION-START
HANDOFF_PROVIDER_BINDING=YES AFTER PROVIDER SELECTION/DISPATCH
HANDOFF_SESSION_BINDING=YES AFTER PROVIDER/CODEX SESSION CREATION
HANDOFF_AUTHORITY_BINDING=YES AT LIFECYCLE BOUNDARIES; NOT A GENERAL ACTION ENVELOPE
HANDOFF_STATUS_PROJECTION=NO DISTINCT PROJECTION; EXISTING MISSION/EXECUTION/CODEX VIEWS
HANDOFF_HISTORY_PROJECTION=PARTIAL, THROUGH RECEIPTS/JOURNALS/EVENTS/SESSION HISTORY
HANDOFF_VERIFICATION_INTERFACE=NO DISTINCT INTERFACE; EXISTING VERIFY COMMANDS
```

### 3.2 Actual current submission and execution path

The supported governed path is:

```text
operator/orchestrator
  -> zeus submit <authorized WOP>
  -> Stage 1 validation and mission/WOP/authority resolution
  -> admission and dispatch-readiness projections
  -> provider selection
  -> dispatch transaction and provider authorization artifacts
  -> provider session
  -> provider invocation acknowledgement
  -> execution-start transaction/session
  -> zeus codex start/resume or bounded adapter path
  -> execution-start begin controlled mission work
  -> execution monitoring and Codex liveness projection
  -> evidence, verification, qualification, acceptance, publication boundaries
```

Concrete current entry points are `scripts/zeus submit`,
`scripts/zeus dispatch ...`, `scripts/zeus provider-session ...`,
`scripts/zeus provider-invocation ...`, `scripts/zeus execution-start ...`,
and `scripts/zeus codex ...`. There is no general `handoff submit` command.

The boundary that still depends on manual procedure is the conversion of a
new engineering request into a bounded, execution-bound request after the
WOP/mission chain exists, plus the return/classification of provider command
requests. Direct `engctl codex` remains a recovery/diagnostic path and bypasses
Zeus mission lifecycle projections; it is not a substitute for convergence.

### 3.3 Current handoff model maturity

```text
CURRENT_HANDOFF_MODEL=WOP_AND_EXECUTION_CHAIN_WITHOUT_CANONICAL_HANDOFF_ENVELOPE
CURRENT_HANDOFF_MATURITY=PARTIAL / PHASE-5 EXECUTION FOUNDATION
CANONICAL_HANDOFF_OWNER=NO_DISTINCT_OWNER; ZEUS SUBSYSTEMS OWN COMPONENTS
```

Managed Codex maturity is higher than handoff maturity:

| Capability | State | Evidence/owner |
|---|---|---|
| Managed Codex session | Implemented | `codex_adapter.py`, `zeus codex start/status/resume/stop` |
| Provider selection | Implemented | `provider_selection.py` |
| Provider session | Implemented | `provider_session.py` |
| Provider invocation | Implemented at bounded acknowledgement boundary | `provider_invocation.py` |
| Execution start | Implemented at controlled foundation boundary | `execution_start.py` |
| Execution monitoring | Implemented and corrected | `execution_monitoring.py` |
| Runtime rematerialization | Implemented/part of adapter recovery | Codex adapter/runtime records |
| Session supersession | Implemented with preserved history | Codex adapter and P5-G6 evidence |
| Identity continuity | Implemented and verified | execution/provider/Codex bindings |
| Evidence return | Implemented as receipts, journals, events, logs, artifacts, and reports | Phase 5 components |
| Native handoff submission | Absent | no canonical object/command |
| Provider authorization convergence | Partial | lifecycle authorization exists; action-level translation absent |

## 4. Authority and provider permission boundary

Zeus resolves engineering authority from authenticated operator authority,
mission/WOP contracts, gate state, approvals/acceptance records, execution
state, provider/session bindings, and `next_authorized_action`. WOP content is
an execution instruction and scope contract, not an independent authority
source. Zeus does not invent approval.

Codex/provider permission is a separate technical boundary. The provider,
sandbox, runtime, host, and command approval surface determine whether a
process is technically permitted to execute a command. Existing documentation
already states that Zeus can report structured request decisions such as
`ALREADY_AUTHORIZED`, `OPERATOR_DECISION_REQUIRED`, or `PROHIBITED`, but the
current architecture does not yet provide a canonical handoff action-request
adapter that computes and transmits those decisions for all provider commands.

```text
ZEUS_ENGINEERING_AUTHORITY_MODEL=CANONICAL_STATE_RESOLUTION; FAIL CLOSED
CODEX_PROVIDER_PERMISSION_MODEL=PROVIDER/SANDBOX/RUNTIME PERMISSION; SEPARATE
DUPLICATE_OPERATOR_DECISION_RISK=MEDIUM; HIGHEST AT PROVIDER COMMAND PROMPTS
COMMAND_PREFIX_APPROVAL_DEPENDENCY=CURRENTLY PRESENT FOR SOME CODEX-ISSUED COMMANDS
AUTHORITY_TO_PROVIDER_TRANSLATION_EXISTS=PARTIAL, LIFECYCLE-BOUNDARY ONLY
PROVIDER_PERMISSION_PROFILE_EXISTS=PARTIAL; PROVIDER MODES AND SANDBOX CONTROLS EXIST, NO HANDOFF-DERIVED PROFILE
```

The target must not disable provider security prompts globally. It should make
the provider ask Zeus first for an engineering decision, then retain provider
permission checks. A Zeus `AUTHORIZED` result means “within the governed
engineering scope”; it does not mean unrestricted host execution.

## 5. Manual-process analysis

| Current manual step | Disposition | Reason |
|---|---|---|
| Prepare WOP and authority-bound scope | `KEEP_OPERATOR_CONTROL` | Human intent and authority remain authoritative |
| Select mission/WOP/gate/execution context | `AUTOMATE_IN_ZEUS` | Existing deterministic resolvers can bind it |
| Select provider and session | `AUTOMATE_IN_ZEUS` | Existing P5-G1 through P5-G4 artifacts already own this |
| Launch managed Codex | `AUTOMATE_IN_ZEUS` | Existing `zeus codex` path owns identity and process binding |
| Paste/transmit bounded work | `AUTOMATE_IN_ZEUS` after handoff-envelope implementation | Must be scoped, identity-bound, and replayable |
| Approve every already-authorized provider command | `REMOVE_AS_REDUNDANT` at engineering layer; retain provider technical checks | Zeus should answer from existing state first |
| Approve acceptance, publication, authority mutation, or scope expansion | `KEEP_OPERATOR_CONTROL` | These remain explicit authority boundaries |
| Inspect provider results and copy evidence | `AUTOMATE_IN_ZEUS` | Return structured result/event/evidence locators |
| Reconcile evidence and determine next action | `AUTOMATE_IN_ZEUS` | Reuse monitoring, verification, and next-action projections |
| Unknown, destructive, or out-of-scope action | `KEEP_OPERATOR_CONTROL` or fail closed | Escalate only when state cannot authorize |

## 6. Capability maturity and gap matrix

| Capability | Current owner | Current implementation | Maturity | Defect/gap | Target owner | Recommended change | Dependency | P5-G6 relevance |
|---|---|---|---|---|---|---|---|---|
| Handoff identity | None | Existing related identities only | Absent | No stable request identity | Zeus execution layer | Deterministic handoff ID bound to request digest and existing identities | MH-01 | Follow-on |
| Handoff submission | Stage 1/WOP intake | `zeus submit <wop>` | Partial | No post-intake work-request boundary | Zeus CLI/controller | Extend existing submission model or add a thin subcommand, not a second system | MH-01/MH-02 | Follow-on |
| Mission/WOP/gate binding | Mission/WOP resolvers | WOP, mission, roadmap, execution artifacts | Implemented | Handoff envelope must consume, not duplicate | Existing resolvers | Reuse and snapshot references/digests | Existing | Direct reuse |
| Execution binding | Execution-start | `execution_start.py` | Implemented | Handoff action scope not attached | Execution-start | Bind handoff to one execution/session | MH-02 | Direct reuse |
| Provider selection/session | Provider modules | P5-G1/P5-G3 | Implemented | No handoff-derived permission profile | Provider modules | Reuse IDs and derive profile | MH-03/MH-04 | Direct reuse |
| Provider invocation | Provider invocation | P5-G4 bounded acknowledgement | Partial | No general action request/response | Provider adapter | Add thin request translation | MH-04/MH-05 | Direct reuse |
| Managed Codex session | Codex adapter | P5-G6 managed session | Implemented | Work delivery/authorization convergence absent | Codex adapter + Zeus | Add bounded handoff transport | MH-02/MH-05 | Direct reuse |
| Authority resolution | Zeus authority runtime | Mission/WOP/gate/approval state | Implemented at lifecycle boundaries | No unified action decision API | Existing authority runtime | Derive action decision from canonical state | MH-03/MH-05 | Direct reuse |
| Provider permission translation | None/thin docs | Provider modes/sandbox controls | Partial | Engineering decision not carried to provider | Zeus/provider adapter | Translate to profile plus action result | MH-04 | Follow-on |
| Operator escalation | Zeus CLI/provider prompt | Mixed/manual | Partial | Repeated ceremony; unclear escalation boundary | Zeus | Escalate only unknown/new authority boundary | MH-05 | Follow-on |
| Runtime control | Codex adapter | Start/resume/stop/reconcile | Implemented | Handoff scope not first-class | Codex adapter | Reuse and bind | Existing | Direct reuse |
| Monitoring | Execution monitoring | Read-only status/verify | Implemented | No handoff projection | Monitoring | Add handoff reference to existing projection | MH-06 | Direct reuse |
| Evidence | Receipts/events/logs/reports | Multiple canonical artifacts | Implemented | Result locators not unified | Existing evidence/projection owners | Add references/digests | MH-06 | Direct reuse |
| Replay | Stage/runtime controllers | Deterministic artifacts and idempotence | Implemented/partial | Handoff replay semantics absent | Zeus | Deterministic handoff/action identities | MH-07 | Follow-on |
| Interruption recovery | Codex adapter/runtime | Rematerialization/supersession/history | Implemented | Handoff recovery lineage absent | Zeus runtime | Preserve handoff and action lineage | MH-07 | Follow-on |
| Completion | Mission/execution lifecycle | Completion/qualification boundaries | Partial for handoff | No handoff completion contract | Existing lifecycle | Project result, do not invent closeout | MH-06/MH-08 | Follow-on |
| Verification | Multiple command-specific controllers | `verify` interfaces | Implemented/fragmented | No handoff verify surface | Zeus | Compose existing checks | MH-06 | Direct reuse |
| History | Journals/receipts/events/session records | Append-only component history | Implemented/partial | No unified handoff history | Zeus projections | Compose locators, do not duplicate records | MH-07 | Follow-on |

## 7. Required operational metadata

The handoff envelope should remain small and operationally justified.

### Required operational

`handoff_id`, `mission_id`, `wop_id`, `gate_id` when gate-scoped,
`execution_id` once execution-bound, `requested_work`, bounded `scope`,
`authority_context_digest`, `request_digest`, `status`, `created_at`, and
the canonical next-action/decision result. Provider and session IDs become
required when dispatch is requested or execution is already bound.

### Reconcilable operational

`provider_id`, `provider_session_id`, `managed_session_id`, execution-session
ID, repository identity, current baseline, gate contract digest, evidence and
result locators, replay status, interruption lineage, and source record paths.
These should be resolved from canonical artifacts and recorded with digests,
not typed again by an operator or provider.

### Advisory

Human title, operator-facing summary, rationale, display labels, estimated
duration, preferred provider mode, and non-authoritative tags. These can improve
efficiency but must not authorize work.

### Unnecessary

Duplicate mission/WOP authority copies, a second acceptance decision, a second
provider registry, arbitrary command-prefix allowlists as governance, enterprise
RBAC/ACL structures, or metadata required solely for administrative symmetry.

## 8. Target architecture

The bounded target is:

```text
Zeus-native submission or existing Zeus submission extension
        ↓
resolve mission / WOP / gate / authority / scope
        ↓
create deterministic handoff envelope bound to existing execution chain
        ↓
derive provider permission profile and action decision
        ↓
AUTHORIZED | OPERATOR_APPROVAL_REQUIRED | BLOCKED
        ↓
managed Codex/provider session
        ↓
provider technical permission and execution
        ↓
existing events, logs, receipts, monitoring, and evidence
        ↓
Zeus verification, replay status, and next authorized action
```

Reuse is mandatory for mission/WOP resolution, provider selection, dispatch,
provider sessions, execution-start, Codex session identity, liveness,
monitoring, evidence, and next-action projection. The only new conceptual
pieces are a thin handoff envelope, a composition/readiness controller, and a
provider authorization translation adapter. They may be implemented as
extensions of existing modules rather than new subsystems.

### Recommended interface

The exact noun is subject to implementation inspection at MH-01. The preferred
shape is a Zeus-native command equivalent to:

```text
zeus handoff submit <request-or-wop> [--mission ...] [--wop ...] [--gate ...]
zeus handoff status <HANDOFF_ID> --json
zeus handoff verify <HANDOFF_ID> --json
zeus handoff resume <HANDOFF_ID> --approve
```

If `zeus submit` can safely own the envelope without changing its stable
meaning, extending that command is preferable. The implementation must not
create a second WOP identity or mandatory manual receipt workflow.

## 9. Provider authorization and escalation model

For each provider action request, Zeus should resolve canonical state in this
order:

1. verify handoff, mission, WOP, gate, execution, provider, session, and
   repository bindings;
2. determine whether the requested action is inside the frozen handoff scope
   and current execution boundary;
3. resolve the current gate/approval/acceptance/next-action state;
4. classify the action as `AUTHORIZED`, `OPERATOR_APPROVAL_REQUIRED`, or
   `BLOCKED`;
5. pass the engineering result plus a minimal provider permission profile to
   the provider; the provider still enforces its own technical policy.

Recommended classification:

| Operation | Decision |
|---|---|
| Read-only inspection within bound repository/scope | `AUTO_AUTHORIZE_FROM_EXISTING_STATE` |
| Repository-local write within current authorized execution scope | `AUTO_AUTHORIZE_FROM_EXISTING_STATE`, subject to provider write profile |
| Runtime process control already covered by the active execution envelope | `AUTO_AUTHORIZE_FROM_EXISTING_STATE`, subject to provider runtime profile |
| Acceptance decision | `REQUIRE_OPERATOR_APPROVAL` |
| Publication, EOS synchronization, authority mutation, or gate advancement | `REQUIRE_OPERATOR_APPROVAL` and applicable separate authority |
| Scope expansion, identity change, new provider/session, or new execution | `REQUIRE_OPERATOR_APPROVAL`; do not mutate implicitly |
| Destructive action, unclassified action, binding mismatch, stale state | `BLOCK_FAIL_CLOSED` unless a fresh explicit authority path resolves it |

Provider profiles should be minimal and derived, not a generalized security
product:

```text
READ_ONLY
REPOSITORY_WRITE
RUNTIME_CONTROL
PUBLICATION
```

Zeus should select an existing provider mode/profile where available and derive
the narrowest profile from the handoff scope. Individual action decisions are
needed for unknown, destructive, authority-mutating, publication, or scope-
changing actions; routine in-scope actions should not require repeated human
engineering decisions. Provider sandbox/host controls remain provider-owned.

## 10. Evidence, monitoring, replay, and recovery

Handoff state should be a composed projection over existing canonical records,
not a duplicate mutable lifecycle. It should expose:

```text
HANDOFF_STATUS_VISIBLE=YES
HANDOFF_CURRENT_ACTION_VISIBLE=YES
HANDOFF_BLOCKERS_VISIBLE=YES
HANDOFF_APPROVALS_VISIBLE=YES
HANDOFF_PROVIDER_VISIBLE=YES
HANDOFF_SESSION_VISIBLE=YES
HANDOFF_RESULT_VISIBLE=YES
HANDOFF_EVIDENCE_VISIBLE=YES
HANDOFF_HISTORY_VISIBLE=YES
HANDOFF_REPLAY_STATUS_VISIBLE=YES
```

The projection should reference the execution-start transaction, provider
session/invocation artifacts, Codex session/events/logs, monitoring projection,
execution verification, and result/evidence digests. Existing command-specific
verification remains independently authoritative for its domain. A handoff
verify command should compose those results and fail closed on binding,
cardinality, digest, liveness, scope, or authority conflicts.

Handoff identity and action identity must be deterministic. Replaying the same
request against unchanged authority should return `IDEMPOTENT`; a changed
request, scope, authority digest, provider/session binding, or execution
lineage must produce a conflict or a new explicitly authorized revision, never
silently overwrite the existing handoff.

Interruption recovery should reuse Codex adapter rematerialization,
supersession, event history, and execution monitoring. It must preserve the
handoff ID and predecessor lineage while requiring fresh resolution when the
execution, provider, or authority state is no longer valid.

## 11. Deferred WOP integration requirements

WOP development is outside this handoff. Future implementation must work
against current WOP interfaces and may not modify WOP schemas/packages as part
of MH-01 through MH-08. Record only these future requirements:

```text
DEFERRED_WOP_INTEGRATION_REQUIREMENT=
  resolve handoff scope and gate criteria from the existing normalized WOP;
  preserve WOP identity/revision/package immutability;
  consume WOP authority references without treating WOP content as authority;
  bind handoff revisions to WOP/package digests;
  reconcile future WOP revisions explicitly rather than mutating a bound handoff.
```

No WOP schema, package, validator, lifecycle, or roadmap was changed.

## 12. Bounded development sequence (planning only)

These are proposed future gates, not active roadmap mutations.

### MH-01 — Current-path convergence and canonical ownership

Objective: document exact owners and choose whether to extend `zeus submit` or
add a thin handoff command. Reuse existing identity and authority resolvers.

Prerequisites: this assessment and operator review. Scope excludes coding,
WOP changes, and roadmap changes. Acceptance requires an approved ownership
map, no duplicate authority/identity store, and fail-closed conflict rules.
Zeus verification must show all source bindings and a read-only plan. Rollback
is no state mutation; unresolved ownership blocks the gate.

### MH-02 — Zeus-native handoff submission and binding

Objective: persist one deterministic handoff envelope bound to current
mission/WOP/gate/execution/session identities. Reuse Stage 1, execution-start,
and Codex session records. Exclude new WOP semantics and provider execution.
Acceptance requires create/replay/conflict tests and stable status/verify.
Rollback is create-only isolation or removal through the existing governed
runtime recovery path; no in-place overwrite.

### MH-03 — Authority-envelope derivation

Objective: compose mission, WOP, gate, approval, execution, scope, and
next-action state into a read-only authority envelope. Reuse authority
resolution and existing acceptance records. Exclude new approval owners.
Acceptance requires valid state to resolve deterministically, stale/mismatch
state to block, and P5-G6 acceptance to remain non-publication/non-P5-G7
authority.

### MH-04 — Managed provider permission translation

Objective: derive the narrowest provider profile from the authorized handoff
and preserve provider sandbox controls. Reuse provider selection/session and
Codex adapter modes. Exclude global prompt disabling and enterprise policy.
Acceptance requires profile binding, provider technical denial preservation,
and no host-scope expansion. Rollback is fail-closed to no provider action.

### MH-05 — Provider authorization and escalation

Objective: implement the thin action decision boundary with the three outcomes
`AUTHORIZED`, `OPERATOR_APPROVAL_REQUIRED`, and `BLOCKED`. Reuse canonical
approval and next-action projections. Exclude a new governance database.
Acceptance requires routine in-scope actions to avoid duplicate operator
decisions, unknown/destructive/publication actions to escalate or block, and
no implicit acceptance/publication/execution transition.

### MH-06 — Handoff monitoring and evidence projection

Objective: compose existing monitoring, Codex events/logs, execution verify,
receipts, and evidence into handoff status/result/history. Exclude a duplicate
execution monitor. Acceptance requires convergent read-only status/verify and
stable evidence locators/digests. Rollback is projection removal; canonical
execution records remain unchanged.

### MH-07 — Replay, interruption, and recovery

Objective: preserve deterministic handoff/action identity across replay,
provider interruption, rematerialization, and session supersession. Reuse
Codex adapter history and runtime reconciliation. Exclude automatic scope or
authority repair. Acceptance requires idempotent replay, conflict detection,
lineage preservation, and fail-closed recovery.

### MH-08 — True managed handoff end-to-end demonstration

Objective: demonstrate one future handoff from Zeus submission through provider
decision, managed execution, monitoring, evidence, and verification.

Prerequisites: MH-01 through MH-07 independently accepted. Exclude P5-G7/G8,
publication, EOS synchronization, and WOP development. Acceptance requires
identity continuity, provider technical-boundary preservation, authorization
decision correctness, result/evidence return, replay idempotence, and explicit
operator review. Any ambiguity blocks the demonstration.

## 13. P5-G6 publication recommendation

The pending P5-G6 publication set may include this artifact as planning
provenance and a follow-on development objective. It should state:

* P5-G6 delivered the controlled active execution foundation, including
  provider/session identity, execution-start, managed Codex, and monitoring
  convergence.
* Managed Handoff Execution / Provider Authorization Convergence is a planned
  follow-on capability, not an implemented P5-G6 capability.
* The plan reuses Phase 5 components and addresses the missing handoff envelope
  and provider action-authorization translation.
* WOP development/package convergence is explicitly deferred.
* P5-G6 acceptance does not authorize P5-G7, publication, EOS synchronization,
  or unrelated execution.

This artifact is evidence/planning provenance. It is not an acceptance record,
provider authorization, publication authorization, or roadmap mutation.

## 14. Risks and unresolved questions

1. The exact stable CLI noun (`handoff` versus an extension of `submit`) should
   be selected at MH-01 after a full compatibility review of the public CLI
   contract.
2. The provider protocol surface for structured action requests must be
   confirmed before implementation; opaque terminal prompts must remain
   non-authoritative.
3. The boundary between repository-local write and runtime control needs a
   concrete scope vocabulary before MH-04/MH-05.
4. Existing qualification-adapter versus real-provider execution modes must be
   explicit in any true managed handoff demonstration.
5. Handoff result/evidence projection must not become a competing completion or
   acceptance authority.

## 15. Required summary

```text
ASSESSMENT_RESULT=PASS_PLANNING_ONLY
CURRENT_HANDOFF_MODEL=WOP_AND_EXECUTION_CHAIN_WITHOUT_CANONICAL_HANDOFF_ENVELOPE
CURRENT_HANDOFF_MATURITY=PARTIAL_PHASE_5_EXECUTION_FOUNDATION
CANONICAL_HANDOFF_OWNER=NO_DISTINCT_OWNER; ZEUS SUBSYSTEMS OWN COMPONENTS
ZEUS_NATIVE_HANDOFF_SUBMISSION_EXISTS=NO
MANAGED_CODEX_EXECUTION_EXISTS=YES
PROVIDER_AUTHORIZATION_CONVERGENCE_EXISTS=PARTIAL_LIFECYCLE_ONLY
ENGINEERING_AUTHORITY_MODEL=ZEUS_RESOLVES_CANONICAL_MISSION_WOP_GATE_APPROVAL_EXECUTION_STATE
PROVIDER_PERMISSION_MODEL=PROVIDER_SANDBOX_RUNTIME_SECURITY_SEPARATE_FROM_ZEUS_AUTHORITY
DUPLICATE_OPERATOR_APPROVAL_RISK=MEDIUM
EXISTING_COMPONENTS_REUSABLE=STAGE1; WOP/MISSION RESOLUTION; PROVIDER SELECTION/DISPATCH; PROVIDER SESSION/INVOCATION; EXECUTION-START; CODEX ADAPTER; MONITORING; EVIDENCE; REPLAY
NEW_COMPONENTS_REQUIRED=THIN_HANDOFF_ENVELOPE; AUTHORITY-ENVELOPE COMPOSER; PROVIDER-ACTION TRANSLATION; COMPOSED HANDOFF PROJECTION
DUPLICATE_COMPONENTS_AVOIDED=SECOND_WOP_STORE; SECOND_AUTHORITY_DB; SECOND_ACCEPTANCE_SYSTEM; SECOND_PROVIDER_REGISTRY; SECOND_MONITOR; GENERALIZED_RBAC
RECOMMENDED_HANDOFF_INTERFACE=EXTEND_ZEUS_SUBMIT_OR_ADD_THIN_ZEUS_HANDOFF_SUBMIT_AFTER MH-01
RECOMMENDED_AUTHORIZATION_MODEL=DERIVE_AUTHORIZED_OR_OPERATOR_APPROVAL_REQUIRED_OR_BLOCKED_FROM_CANONICAL_STATE
RECOMMENDED_OPERATOR_ESCALATION_MODEL=ESCALATE_ONLY_NEW_AUTHORITY_BOUNDARY; UNKNOWN/DESTRUCTIVE FAIL CLOSED
RECOMMENDED_PROVIDER_PERMISSION_MODEL=DERIVED_MINIMAL_PROFILE_WITH_PROVIDER-OWNED_SANDBOX/TECHNICAL CONTROLS
REQUIRED_OPERATIONAL_METADATA=HANDOFF_ID; MISSION_ID; WOP_ID; GATE_ID WHEN SCOPED; REQUEST/SCOPE/AUTHORITY DIGESTS; STATUS; EXECUTION BINDING
RECONCILABLE_OPERATIONAL_METADATA=PROVIDER/SESSION IDS; BASELINE; EVIDENCE/RESULT LOCATORS; REPLAY/INTERRUPTION LINEAGE
ADVISORY_METADATA=TITLE; SUMMARY; RATIONALE; ESTIMATE; PREFERRED MODE; TAGS
UNNECESSARY_METADATA=DUPLICATE AUTHORITY COPIES; DUPLICATE ACCEPTANCE; ARBITRARY PREFIX GOVERNANCE; ENTERPRISE RBAC
MANUAL_STEPS_AUTOMATABLE=CONTEXT RESOLUTION; SESSION/DISPATCH BINDING; WORK DELIVERY; ROUTINE ACTION DECISION; RESULT/EVIDENCE RETURN; NEXT ACTION
MANUAL_STEPS_TO_RETAIN=INTENT/AUTHORITY; ACCEPTANCE; PUBLICATION; AUTHORITY MUTATION; SCOPE EXPANSION; UNKNOWN/DESTRUCTIVE ACTION REVIEW
DEFERRED_WOP_INTEGRATION_REQUIREMENTS=USE CURRENT NORMALIZED WOP; PRESERVE IDENTITY/REVISION/IMMUTABILITY; NO WOP DEVELOPMENT IN THIS PLAN
PROPOSED_DEVELOPMENT_GATES=MH-01 THROUGH MH-08
P5_G6_PUBLICATION_RECOMMENDATION=INCLUDE AS PLANNING PROVENANCE AND FOLLOW-ON OBJECTIVE; DO NOT CLAIM IMPLEMENTATION
ZEUS_IMPLEMENTATION_MODIFIED=NO
WOP_IMPLEMENTATION_MODIFIED=NO
WOP_PACKAGES_MODIFIED=NO
MISSION_STATE_MUTATION=NO
EXECUTION_STATE_MUTATION=NO
AUTHORITY_MUTATION=NO
ROADMAP_MUTATION=NO
EOS_MUTATION=NO
FILES_CREATED=engineering/evidence/operation-beta/managed-handoff-execution-provider-authorization-convergence-assessment.md
FILES_MODIFIED=NONE_BY_THIS_HANDOFF
COMMIT=NOT_PERFORMED
PUBLICATION=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_MANAGED_HANDOFF_CONVERGENCE_PLAN
STATUS=AWAITING_OPERATOR_REVIEW
```
