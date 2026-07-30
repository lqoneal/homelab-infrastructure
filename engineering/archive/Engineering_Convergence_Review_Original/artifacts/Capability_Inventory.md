# Capability Inventory

Review ID: `ENGINEERING-CONVERGENCE-REVIEW-001`  
Assessment date: 2026-07-30  
Completion estimates are engineering estimates of implemented behavior, not
governance, publication, or acceptance percentages.

## Status scale

- **Implemented:** working implementation and meaningful tests/evidence exist.
- **Partial:** important behavior exists, but a required integration,
  lifecycle, or production boundary is missing.
- **Prototype:** bounded or fixture-oriented implementation exists but is not
  a current production path.
- **Planned:** architecture or contract exists without sufficient
  implementation.

## Major subsystem inventory

| Subsystem | Purpose | Status / estimate | Canonical implementation | Dependencies | Maturity |
|---|---|---:|---|---|---|
| EMP management | Registry-backed portfolio, project, mission, phase, sprint, milestone, dependency, and work coordination | Implemented / 90% | `scripts/lib/emp/registry.py`, `management.py`; `engineering/registry/work-registry.yaml` | Controlled project records, YAML schema | Mature repository-local management; not execution authority |
| Zeus operator interface | Human-facing status, next action, verify, approve, mission, and runtime commands | Implemented / 80% | `scripts/zeus`, `scripts/lib/emp/operator_interface.py`, Progressive routing | EMP, Progressive state, Git | Broad but contains legacy branches |
| Progressive OA controller | Locked cumulative OA-01–OA-30 lifecycle | Partial / 45% | `scripts/lib/emp/progressive_gate.py`, `progressive_runtime_support.py`, `progressive_lifecycle.py`, `progressive_oa.py` | Canonical WOP, gate specs, receipts | Current canonical gate path; 5/30 accepted |
| Gate-specific OA implementation | Implements and verifies early OA capabilities | Partial / 50% | `oa01_*` through `oa05_*`; OA-06 eligibility module | Progressive controller, repository state | OA-01–OA-05 accepted; OA-06 integration incomplete |
| Project context reconstruction | Deterministic project/phase/work/authority reconstruction | Implemented / 85% | `project_operational_context.py`, EOS context/runtime integration | PROJ-0001, registry, repository | OA-04 accepted |
| Mission staging | Stable candidate mission identity, scope, dependencies, and state | Implemented / 80% | `mission_contract_discovery.py`, `mission_resolution.py`, `oa05_implementation.py` | Mission Contract store, authority context | OA-05 accepted; store duplication remains |
| Mission eligibility | Classify eligible, blocked, deferred, and ineligible missions | Partial / 65% | `scripts/lib/emp/mission_eligibility.py` | Staged contracts, dependency and authority facts | Core exists; OA-06 not accepted |
| Mission Contracts | Typed authoritative mission intent and lifecycle | Partial / 65% | Intended owner: `engineering/mission-contracts/contracts/`, schema, `scripts/lib/eos/mission_contract.py` | Approval/activation transactions | Duplicated by execution mission store |
| WOP framework | Immutable work package, publication, admission, lifecycle, dispatch boundary | Implemented / 80% | `scripts/lib/wop/contract.py`; EMP WOP service/admission/lifecycle/dispatch | Mission Contract, receipts, authority | Strong primitives; several WOP generations coexist |
| Authority Graph | Validate delegated authority topology | Implemented offline / 75% | `scripts/lib/authority/engine.py` | Node/edge declarations | Useful validation library; not canonical production resolver |
| Authority publication | Owner enrollment, signing, publication, activation, trust | Implemented / 85% | `authority_publication.py`, `owner_enrollment.py`, `authority_resolution.py` | Owner keys, trust policy, active pointer | Production-capable; current applicability lifecycle needs convergence |
| Controlled Mission Authority | Resolve exact mission/repository/WOP authority | Implemented / 75% | `controlled_mission_authority.py` | Mission Contract, repository, WOP | OA-02 accepted; overlaps generic authority resolution |
| Authorization Bundle | Normalize canonical or legacy authority inputs | Partial compatibility / 60% | `work_initiation/authorization_bundle.py`, bundle schema and architecture doc | Mission/WOP/admission locators | No complete producer/selector lifecycle; legacy inputs remain |
| Engineering Work Initiation | Compose assurance and issue terminal initiation decision | Partial / 70% | `scripts/lib/eos/execution_interface.py`, `work_initiation/shadow.py` | Contract, WOP, authority, repository, policy | Correct target terminal boundary; not yet integrated through one REAC |
| Mission admission | Validate and admit mission/WOP packages | Implemented / 85% | `mission_admission_runtime.py`, `wop_admission.py` | Contract, WOP, authority and repository bindings | Schema-backed and fail-closed |
| Dispatcher | Assign admitted work to qualified agents under approval | Implemented, disabled / 70% | `wop_dispatch.py`, `production_execution.py` | Admission, agent registry, approval, authority | Prepared, not commissioned for live OA execution |
| Mission execution | Supervised stateful execution and evidence emission | Implemented, non-live / 70% | `mission_execution_runtime.py`, `stage1_runtime.py`, `gate_handlers.py`, `operational_gate_handler.py` | Dispatcher, handlers, EENS, evidence | Qualified in isolated/non-mutating modes |
| Gate approval | Human verification and receipt lifecycle | Duplicated | Canonical current: `progressive_gate.py`; transitional: `gate_approval.py` | Gate verification, receipts, Git binding | Progressive path is current; legacy remains reachable |
| Evidence pipeline | Typed packages, attestations, integrity, execution events | Implemented / 85% | `evidence_qualification.py`, `execution_oversight.py`, runtime evidence trees | Execution IDs, digests, clocks/signatures | Broad and well tested in focused evidence |
| Qualification | Independent evidence and gate qualification | Implemented / 80% | `evidence_qualification.py`, PMCT assets, gate verifiers, `scripts/verify.sh` | Stable candidate and isolated environment | Strong focused evidence; clean aggregate proof missing |
| Reconciliation | Compare and update authoritative state with receipts | Implemented / 80% | `reconciliation.py`, `document_synchronization.py` | Typed owners and current records | Generic engine exists; ownership duplication complicates use |
| Repository–EOS sync | One-way projection of repository authority to EOS | Implemented / 85% | `scripts/lib/eos/state_sync.py`, `repository-eos-synchronization.md` | Canonical repository records, EOS target | Explicit repository-as-authority model |
| EOS runtime | Context, checkpoint, state, operations, synchronization | Implemented / 80% | `scripts/lib/eos/*.sh`, Python assurance/activation/sync modules | Repository and runtime filesystem | Mature foundation; shell/Python split adds complexity |
| Mission assurance language | Read-only controlled assurance evaluation | Implemented / 85% | `assurance_language.py`, `mission_assurance.py` | Controlled declarations | Reconciled baseline, controlled publication status varies |
| EENS | Durable events, idempotent store, consumers, ntfy notifications, service | Implemented / 90% | `services/eens/src/eens/` | SQLite/runtime path, optional ntfy/systemd | Canonical source; 94 static test functions |
| Notification integration | Send operational events and handoffs | Implemented / 80% | EENS notifier/runtime plus `scripts/lib/notifications/ntfy.sh` | EENS, ntfy configuration | Core operational; future HNS expansion deferred |
| engctl | Global engineering control routing and EOS entry | Implemented / 80% | `scripts/engctl`, EMP management CLI, EOS helpers | Repository context, registry | Established control surface; overlaps Zeus only by presentation/orchestration role |
| Controlled documentation | Document classes, lifecycle, publication, qualification, index | Implemented framework / 90% | `docs/`, DOC-0001, STD/PROC/SPEC set | Governance lifecycle, Git persistence | Rich framework; operational/reference reconciliation pending |
| Authority Pipeline governance declarations | Canonical capabilities, policies, states, transitions, outcomes, dependencies | Implemented and qualified / 90% | `engineering/architecture/progressive-runtime-*.json`, validators | SPEC-0012 and independent qualification | Qualified independent family; publication incomplete |
| Publication pipeline | Exact publication inventory, qualification fingerprint, boundary freeze | Partial / 70% | Publication Plan 002, manifest, PU evidence | Ordered publication units | PU-01C frozen; blocked by unpublished PU-01B |
| Repository policy | Canonical root/branch/worktree observation | Partial / 70% | `authority_pipeline/repository.py`, working-tree baseline, EOS repository helpers | Git and remote freshness | Root checks exist; phase-specific freshness/candidate policy incomplete |

## Runtime capability-to-OA mapping

| OA range | Capability | Current evidence | Reuse assessment |
|---|---|---|---|
| OA-01 | Assessment recognition and transition | Accepted | Complete |
| OA-02 | Controlled Mission Authority | Accepted | Complete |
| OA-03 | Dispatcher policy | Accepted | Complete |
| OA-04 | Context reconstruction | Accepted | Complete |
| OA-05 | Mission staging | Accepted | Complete |
| OA-06 | Mission eligibility | Implementation required | Integrate existing eligibility and authority components; do not rebuild |
| OA-07–OA-10 | Agent invocation, admission dispatch, CLI execution, EENS lifecycle | Pending gates; implementations exist | Primarily integration and qualification |
| OA-11–OA-13 | Signed evidence, independent qualification, live reconciliation | Pending gates; implementations exist | Primarily integration, key management, and qualification |
| OA-14 | Authority restoration | Planned/partial | Coordinator remains a genuine missing capability |
| OA-15 | Integrated production execution foundation | Pending; components exist | Commission and qualify combined path |
| OA-16–OA-18 | Documentation reconciliation, commit, republication | Pending; publication work exists | Publication sequencing and reproducibility, not new runtime |
| OA-19–OA-23 | Commissioning, agent activation, mission authorization, WOP, dispatch admission | Pending; major primitives exist | Controlled operational qualification required |
| OA-24–OA-28 | Real dispatch through mission close | Pending | First protected operational execution remains unperformed |
| OA-29–OA-30 | Alpha qualification and declaration | Pending | Evidence synthesis and separate declaration authority |

## Implemented capability summary

Fully or substantially implemented capabilities include registry management,
operator status/navigation, Progressive lifecycle primitives, OA-01–OA-05,
project context, mission staging, WOP validation/admission/lifecycle,
authority publication and owner enrollment, dispatcher and execution-agent
primitives, supervised mission execution, evidence packages, qualification,
reconciliation, repository–EOS synchronization, controlled assurance
language, EENS, and controlled-document tooling.

## Planned or incomplete capability summary

The material remaining capability gaps are:

1. one integrated ARS → resolved context → Progressive narrowing → EWI path;
2. a complete Authorization Bundle producer/selector/supersedence lifecycle;
3. authoritative OA-06 mission eligibility integration;
4. automated authority-restoration coordination;
5. removal of external WOP and legacy gate dependencies;
6. production commissioning and the first real operational WOP;
7. publication of the current reproducible baseline;
8. cumulative OA-06–OA-30 qualification and declaration.

## Canonical implementation decisions

- Current OA gate lifecycle: Progressive runtime and canonical Progressive WOP.
- Project/work management: EMP registry and controlled project records.
- Mission intent: `engineering/mission-contracts/contracts/`.
- WOP contract: `scripts/lib/wop/contract.py` plus immutable repository WOP.
- Generic authority resolution: converge on
  `scripts/lib/emp/authority_resolution.py` and evolve its bundle into the
  resolved execution context.
- Terminal initiation decision: EOS Engineering Execution Interface.
- Events/notifications: `services/eens`.
- Repository authority: repository records; EOS is a projection.
- Controlled documents: `docs/` plus DOC-0001 lifecycle/index rules.

