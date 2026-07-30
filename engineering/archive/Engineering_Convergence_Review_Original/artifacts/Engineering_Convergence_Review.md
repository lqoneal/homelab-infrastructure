# Engineering Convergence Review

Review ID: `ENGINEERING-CONVERGENCE-REVIEW-001`  
Review date: 2026-07-30  
Repository: `/data/engineering/repositories/homelab`  
Remote: `git@github.com:lqoneal/homelab-infrastructure.git`  
Branch and reviewed HEAD: `main` at `d0861dc62b8199de03230152c4ed3cfb687dd9a7`  
Review type: read-only engineering assessment; this report is not execution authority

## Executive conclusion

The repository is functionally substantial but not yet converged or
publication-stable. Its strongest assets are a broad repository-local
engineering runtime, explicit schemas and fail-closed controls, extensive test
and evidence holdings, an operational EENS service, and a Progressive
Operational Alpha path that has accepted OA-01 through OA-05. Its principal
weakness is that much of the newest implementation, lifecycle state,
documentation, and qualification evidence exists only in a very large dirty
working tree at the reviewed HEAD. The repository therefore has more working
capability than its committed baseline proves.

Architectural convergence is underway, not complete. The intended direction is
clear: one repository Mission Contract, one immutable WOP and admission chain,
one Authority Resolution Service producing a resolved execution context,
Progressive Mission Authority only narrowing that context, and Engineering Work
Initiation making the single terminal initiation decision. The current code
still exposes overlapping legacy, compatibility, and Progressive paths.

Zeus Operational Alpha is not ready to declare. The authoritative Progressive
runtime state says:

- OA-01 through OA-05: `ACCEPTED`
- OA-06: `IMPLEMENTATION_REQUIRED`
- OA-07 through OA-30: `PENDING`
- operational dispatch: disabled in the current progress record
- Operational Alpha declaration and baseline freeze: not performed

The shortest verified path is not to implement the remaining 25 gates as
independent feature projects. It is to converge the authority path needed by
OA-06, eliminate live legacy authority dependencies, publish a reproducible
baseline, then use the already implemented execution, evidence,
qualification, reconciliation, EENS, and lifecycle components to qualify the
remaining gates cumulatively.

## Review basis and limitations

This assessment inspected implementation, controlled documents, architecture
and operations records, Mission Contracts, WOP packages, lifecycle state,
publication plans, tests, and evidence across the repository. Key evidence
includes:

- `docs/project/PROJ-0001-PROJECT_STATE.md`
- `docs/project/PHASE-0001-ZEUS-OPERATIONAL-ALPHA-AUTHORITY.md`
- `engineering/operations/zeus-operational-alpha-progress.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json`
- `engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml`
- `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/`
- `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/`
- the Python implementations under `scripts/lib/`
- EENS implementation and tests under `services/eens/`

The working tree was already extensively modified and untracked before this
review. The review did not stage, commit, reconcile, refactor, or modify any
implementation or controlled record. Only the five requested review artifacts
were added.

The environment does not provide the `pytest` executable. Native `unittest`
aggregate discovery was attempted with bytecode and cache writes disabled, but
did not complete within the review window and was interrupted. No aggregate
live test-pass claim is made. Static inventory found 76 script test modules
with approximately 716 test functions, 8 PMCT test modules with 22 test
functions, and 7 EENS test modules with 94 test functions. Existing focused
qualification evidence remains useful but does not replace a clean-checkout
aggregate qualification.

## Engineering maturity

| Dimension | Assessment | Evidence-based rationale |
|---|---|---|
| Functional breadth | High | EMP, EOS, Zeus, authority, admission, execution, evidence, qualification, reconciliation, EENS, WOP, and work-initiation code all exist. |
| Production maturity | Medium-low | Dispatch remains disabled and no real operational WOP has completed the OA-23–OA-28 chain. |
| Architectural maturity | Medium | Target topology is well described, but multiple current resolution and lifecycle paths remain. |
| Test maturity | Medium-high in breadth | Large unit-test inventory and focused qualifications exist; clean-baseline aggregate reproducibility is not presently established. |
| Documentation maturity | High volume, medium convergence | Controlled framework is extensive; current operational facts are duplicated across project, progress, WOP, evidence, and working-tree records. |
| Repository health | At risk | Large dirty tree, many core files untracked, generated caches present, and publication ordering remains incomplete. |
| Operational Alpha readiness | Partial | Five of thirty Progressive gates are accepted; OA-06 is the immediate blocker. |

## Major observations

1. **A canonical Progressive runtime exists.** `scripts/lib/emp/progressive_*`,
   the gate-specific OA-01–OA-05 modules, the canonical Progressive WOP, and
   its runtime state form the current execution path selected by `scripts/zeus`.

2. **The authority pipeline is still plural.** Production-reachable code
   includes Authority Graph evaluation, WOP compatibility evaluation,
   authorization-bundle resolution, operational Authority Resolution,
   Controlled Mission Authority, Progressive Mission Authority, and EOS
   Engineering Work Initiation. These components do not yet compose through
   one canonical resolved context.

3. **Two Mission Contract-like stores exist.**
   `engineering/mission-contracts/contracts/` is the intended authoritative
   store, while `engineering/execution/missions/` contains separately edited
   execution mission descriptions.

4. **Legacy gate authority remains reachable.** Repository evidence and source
   routing agree that `oa02_lifecycle.py` is dead in the current Progressive
   route, while `gate_approval.py` and the standalone PMCT harness remain
   transitional and externally coupled.

5. **Implementation and acceptance are appropriately distinct.** Many later
   capabilities already have reusable implementation primitives, but the
   Progressive gate sequence correctly does not infer acceptance from code or
   historical evidence.

6. **Documentation authority is structurally sophisticated but operationally
   diffuse.** Controlled records define clear document classes, yet current
   state is restated in PROJ-0001, progress records, registry data, WOP state,
   evidence reports, and publication records. Some of these are explicitly
   projections, but consumers and readers cannot always distinguish the owner.

7. **Publication is a blocking engineering concern, not clerical cleanup.**
   PU-01C is frozen and qualified, but its publication was correctly stopped
   because unpublished PU-01B owns prerequisite publication records. This
   leaves key current architecture in the untracked working tree.

## Principal risks

| Priority | Risk | Impact |
|---|---|---|
| Critical | Two or more paths can appear to resolve execution authority | Conflicting allow/deny outcomes or an unintended bypass |
| Critical | Most current capability is not represented by the committed HEAD | Loss, non-reproducibility, and invalid publication/qualification claims |
| Critical | Live tests and compatibility paths depend on a noncanonical external OA WOP tree | Hidden mutable dependency and inability to freeze/retire it |
| High | Mission Contract concepts are split across two stores | Ambiguous mission identity, scope, and dependency resolution |
| High | Publication order is incomplete | Current documentation and runtime declarations cannot form an authoritative baseline |
| High | State is repeated across controlled, operational, registry, WOP, and evidence locations | Drift and stale resume decisions |
| Medium | Historical evidence volume lacks a durable machine-readable catalogue | Expensive reconstruction and repeated rediscovery |
| Medium | Test execution depends on environment-specific tools and live state | Qualification results may not reproduce cleanly |
| Medium | Python cache artifacts are intermingled with source locations | Repository noise and unreliable organization scans |

## Architectural convergence assessment

The repository is converging toward a coherent layered architecture:

```text
operator intent
  -> authoritative Mission Contract
  -> immutable WOP + publication receipt + Admission Record
  -> owner publications and repository observation
  -> Authority Resolution Service / resolved execution context
  -> Progressive gate eligibility narrowing
  -> Engineering Work Initiation terminal decision
  -> supervised execution
  -> typed evidence, qualification, reconciliation, and EENS projection
```

This target reuses the best existing components and removes decision
duplication. It should be adopted as the canonical architecture. Compatibility
evaluators and the Authority Graph remain valuable as offline validation and
migration libraries, not parallel production decision makers.

## Documentation convergence assessment

| Class | Disposition |
|---|---|
| Approved/Active controlled documents under `docs/` and indexed by DOC-0001 | Authoritative within their declared scope and lifecycle |
| `PROJ-0001`, PHASE-0001, and canonical registry | Authoritative for their assigned project, phase, and management facts; references must not become execution authority |
| `engineering/operations/` | Operational reference; some files state authoritative operational ownership, but controlled adoption is incomplete |
| `engineering/docs/architecture/` and `engineering/architecture/` | Current engineering architecture/reference; several are untracked and not controlled publications |
| `engineering/planning/` | Proposal and implementation-planning material; non-authoritative unless separately adopted |
| `engineering/evidence/` and WOP evidence | Historical proof and findings; not current execution authority |
| completed EWO records and milestones | Historical |
| external Progressive OA WOP tree | Historical/obsolete compatibility package, not current authority |
| `engineering/execution/missions/` | Pending reconciliation as a derived projection or retirement |
| legacy PMCT approval documentation | Pending reconciliation with Progressive lifecycle |

DOC-0001 itself has a known semantic-validation discrepancy: direct validation
can report no semantic profile even though it is the repository document
index. That is a documentation/profile issue to retain as an unresolved
observation, not a reason to treat the index as absent.

## Runtime convergence assessment

| Runtime area | State | Assessment |
|---|---|---|
| Planner / next action | Partial | Deterministic next-action and project context exist; legacy and Progressive routing coexist. |
| Mission staging | Implemented and OA-05 accepted | Canonical staging behavior exists in the Progressive path. |
| Mission eligibility | Implemented components, OA-06 incomplete | `mission_eligibility.py` exists, but canonical authority integration and gate acceptance are unresolved. |
| Authority resolution | Partial, duplicated | Several capable resolvers exist; no single production REAC path. |
| Admission | Implemented | WOP admission and mission admission runtimes exist, with schema-backed records. |
| Approval | Implemented, duplicated lifecycle | Progressive decisions are canonical for current gates; legacy GateApprovalService remains reachable. |
| Execution | Implemented but not commissioned for live dispatch | Supervised dispatcher, production agent, execution runtime, and Stage 1 runtime exist. |
| Evidence | Implemented | Evidence packages, attestations, runtime evidence, checksums, and EENS projection exist. |
| Qualification | Implemented | Independent evidence qualification and gate qualification exist; aggregate clean-baseline proof is missing. |
| Reconciliation | Implemented | Generic reconciliation and repository–EOS synchronization exist. |
| Notification | Operational | EENS has source, CLI, persistent store, ntfy adapter, service files, and a substantial test suite. |
| Lifecycle management | Implemented but overlapping | WOP, gate, Progressive, execution, work-authority, publication, and registry lifecycles need one ownership map. |
| Policy engine | Partial | Deterministic policies exist across several modules, but there is no single named policy decision boundary. |

## Operational Alpha readiness

### Completed prerequisites

- Repository-local Zeus launcher and operator interface
- Controlled Mission Authority through OA-02
- Dispatcher policy resolution through OA-03
- Project and operational context reconstruction through OA-04
- Mission staging contract through OA-05
- Canonical Progressive WOP and accepted receipt lineage for OA-01–OA-05
- Admission, dispatcher, execution-agent, evidence, qualification,
  reconciliation, and EENS implementation primitives
- Governance baseline independence qualification for PU-01C
- Frozen exact-path PU-01C boundary

### Critical blockers

1. Converge authority inputs and decisions for OA-06.
2. Remove or isolate the external legacy WOP dependency.
3. Designate one Mission Contract store and one terminal execution decision.
4. Complete publication prerequisites in dependency order, including PU-01B
   before PU-01C.
5. Establish a committed, reproducible, clean candidate baseline.

### Medium-risk remaining work

- Isolate all tests from live runtime and external trees.
- Reconcile state ownership and projection rules.
- Qualify remote freshness and repository-policy behavior.
- Map later OA gates to existing implementations to prevent duplicate builds.
- Catalogue evidence and historical records.

### Low-risk/deferable work

- Broader documentation relocation
- Removal of preserved historical artifacts
- Generalized topology registry
- Richer diagnostics and continuous duplicate-tree monitoring
- HNS expansion for EENS
- Cosmetic repository reorganization

## Engineering debt by Operational Alpha impact

| Category | P0 | P1 | P2 |
|---|---|---|---|
| Architecture | Single REAC and terminal decision; one contract store | Explicit component ownership map | Generic topology registry |
| Implementation | Retire live legacy gate paths; integrate OA-06 | Narrow PMCT to current duties | Remove residual compatibility helpers |
| Documentation | Reconcile current authority/projection labels | Resolve DOC-0001 semantic profile | Relocate reference documents |
| Testing | Isolated authority pipeline and clean-checkout qualification | Deterministic clocks/keys and live-state removal | Tooling ergonomics |
| Repository organization | Commit/publish bounded current baseline | Evidence catalogue and cache hygiene | Historical archive layout |
| Mission framework | Bind Mission Contract, WOP, admission, REAC, gate, and EWI | Consolidate receipt schemas/discovery | Generalize beyond Progressive OA |
| Process | Publication dependency discipline | One state-owner matrix | Automated drift reporting |

## Repository organization findings

- `docs/` is the controlled-document domain and should remain distinct from
  engineering reference material.
- `engineering/operations`, `engineering/docs/architecture`, and
  `engineering/architecture` overlap in architectural explanation.
- `engineering/mission-contracts/contracts` and
  `engineering/execution/missions` duplicate mission-description concepts.
- `engineering/evidence` and per-WOP `EVIDENCE` trees are both legitimate but
  need a common catalogue.
- `.zeus`, WOP runtime directories, and repository state records contain
  different classes of runtime/projection data; ownership must be explicit.
- `__pycache__` directories are historical/generated accumulation and should
  not be treated as implementation.
- The external `/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP` is a duplicate
  historical package with remaining transitional consumers.

No reorganization is recommended before OA-06 convergence and baseline
publication. Moving files now would enlarge the qualification boundary and
obscure the more important authority cutover.

## Immediate recommendation

The immediate next engineering mission should be a bounded **OA-06 Authority
Path Convergence and Qualification** mission. Its purpose should be to:

1. approve the existing single-path authority topology;
2. make `engineering/mission-contracts/contracts/` the sole Mission Contract
   authority;
3. evolve the current authority-resolution bundle into one resolved execution
   context;
4. make Progressive Mission Authority consume and only narrow that context;
5. make EWI the only terminal initiation decision;
6. remove external legacy WOP consumers and isolate their tests;
7. qualify OA-06 without dispatch;
8. publish the resulting candidate in the already defined publication order.

This avoids rebuilding admission, dispatch, evidence, qualification,
reconciliation, or EENS capabilities that already exist.

## Overall disposition

**Engineering maturity:** substantial pre-alpha platform  
**Architectural convergence:** directional but incomplete  
**Repository health:** recoverable, presently high-risk due to unpublished
working-tree state  
**Zeus Operational Alpha readiness:** not ready; five of thirty gates accepted  
**Shortest path:** converge and qualify OA-06, establish a reproducible
published baseline, then certify existing downstream capabilities in sequence

