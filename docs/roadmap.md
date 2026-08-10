# Homelab Roadmap

Status: Active

---

## Current Convergence Program

The canonical current rebuild/convergence planning authority is
`ENGINEERING-SYSTEM-CONVERGENCE`, roadmap `ESC-ROADMAP-001`, under
`engineering/convergence/engineering-system-convergence/`. Its machine-readable
`STATE.yaml` records C00 complete, C01 complete with findings, and C02 current.
The next authorized action is the read-only
`BEGIN_C02_CONTROLLED_DOCUMENTATION_AND_AUTHORITY_ASSESSMENT`.

Use `engctl roadmap validate`, `engctl roadmap status`, or `engctl resume` to
resolve the current position. Missing, malformed, drifted, or contradictory
roadmap/state/gate/result/evidence/Project-State inputs fail closed. This
planning roadmap does not authorize later implementation, publication, EOS
synchronization, provider invocation, or automatic execution of C20.

The Operation Beta and Operational Alpha material below is preserved as
historical and assessment input. It does not supersede the current convergence
program.

## Published Transition — Operation Beta

Operational Alpha is complete and frozen at `OA-v1.0.0` under `OA-OPERATIONAL-MILESTONE-006`. The active post-Alpha planning authority is Operation Beta, beginning with `BETA-00` Engineering Platform Assessment.

The Beta charter, authority model, and mission roadmap are:

- `engineering/docs/operations/OPERATION-BETA-CHARTER.md`
- `engineering/docs/architecture/OPERATION-BETA-AUTHORITY-MODEL.md`
- `engineering/docs/architecture/OPERATION-BETA-ROADMAP.md`

The remaining content in this document is historical or subsystem-specific roadmap material. It does not supersede the frozen Alpha milestone or the published Beta authority chain.

## Historical Mission — Zeus Operational Alpha

Zeus Operational Alpha is the current authoritative Homelab engineering
mission under PHASE-0001 and PROJ-0001.

The current authority establishes portfolio direction and a consistent resume
baseline only. No Zeus runtime implementation, production modification,
autonomous execution, feature development, or Work Package execution is
authorized.

OA-01 implementation readiness is owned by
`WOP-OA-01-IMPLEMENTATION-001@1`, bound to
`OA-IMPLEMENTATION-BASELINE-1.0` at
`5706307c1fdf9d4e0601c9cc578181f6d916e0a8`. Its state is `READY` and
`NOT_STARTED`; it is not an execution authorization. Historical Progressive
OA runtime records remain evidence only.

ZEUS-P2-013 establishes the production ownership model: Lawrence O'Neal is the
sole human owner of every operational authority domain and `loneal` is the
production principal. The authenticated Zeus CLI is the authoritative
interface through which Lawrence O'Neal exercises engineering authority.
Controlled documentation is the normal operational source of execution
authority. Zeus resolves, validates, reconciles, and executes that authority;
it is not an autonomous authority.

ZEUS-P2-015 establishes the Authority Restoration Principle. Zeus first
resolves controlled-document authority. A missing, stale, conflicting,
incomplete, or invalid authority chain stops execution safely and becomes
reconciliation work. Bootstrapping may authorize controlled-document
reconciliation, but never a bypass. Automated restoration coordination is
deferred runtime work.

The next eligible mission is Mission C — Zeus Operational Alpha Capability
Discovery. Mission C is read-only and may produce an implementation baseline
and Work Package architecture after separate initiation.

Historical roadmap items remain recorded for continuity. Their ordering or
unchecked state does not supersede PHASE-0001, establish current priority, or
authorize execution.

### ZEUS-P2-002 — Authority Resolution Architecture

The operational WOP authority-resolution architecture is documented and
architecturally qualified. It assigns exactly one originator to every authority
artifact and introduces a sealed Authority Resolution Bundle between Mission
Admission and WOP generation.

ZEUS-P2-003 implements and qualifies the repository-local runtime, sealed ARB,
immutable WOP finalization, explicit dual generation modes, and safe authority
validation. An unresolved authority condition blocks execution and enters the
restoration model defined by SPEC-0011.

ZEUS-P2-004 implements and qualifies signed, owner-scoped staging, full-source
readiness verification, explicit atomic activation, rollback, revocation, and
recovery. Historical pre-commissioning refusals remain evidence of safe
enforcement; current production trust and authority were commissioned by
ZEUS-P2-014.

ZEUS-P2-014 resolves the commissioning preflight: the explicitly designated
production key enrolls principal `loneal`, registry-bound production trust is
compiled, ten operator-signed authority records pass readiness, and the
repository-fixed authority source is explicitly activated. Commissioning now
reports `READY`.

ZEUS-P2-006 implements and qualifies the remaining software-side owner
enrollment toolkit: public-key inspection, externally authorized enrollment,
rotation, suspension, retirement, candidate trust compilation, unsigned
publication templates, operator approval payload validation, and
blocker-specific commissioning diagnostics. It neither enrolls production
owners nor activates Zeus.

ZEUS-P2-007 implements and qualifies the unified Mission Admission Runtime.
Qualification and future operational admissions now traverse the same
persistent, digest-protected, restartable state machine through repository
verification, authority resolution, WOP generation, submission eligibility,
and admission decision. Production remains blocked at the authority gate
because authentic operator-owned artifacts are absent. The runtime never
self-enables, submits, dispatches, or executes.

ZEUS-P2-008 implements and qualifies the persistent Mission Execution Runtime:
typed gates, digest-bound state, immutable hash-chained evidence, checkpoints,
safe interruption/resume, explicit wait/suspend/cancel states, stable handler
idempotency keys, and an EENS append-only event adapter. Qualification performs
a complete non-mutating simulation. Operational execution stops at the
disabled dispatch boundary; no production handler or activation was added.

ZEUS-P2-009 first publishes P2-002 through P2-008 as four verified commits at
qualified baseline `3497d29067530c32fbdc52e245191f05b3a8bd63`. It then adds a
manifest-discovered gate-handler registry, stable API and capability
negotiation, verification-first lifecycle, deterministic skip semantics,
subprocess timeout/failure isolation, and a non-mutating qualification
handler. No operational handler or dispatcher is included.

ZEUS-P2-010 adds and qualifies the first operational-only handler: immutable
execution context, safe declarative artifact creation/verification, exact
repository and WOP binding, dependency checks, action-level checkpoints,
between-action cancellation, deterministic resume, post-action verification,
structured evidence, and EENS projection. Qualification uses isolated
temporary workspaces and simulated accepted admission; production dispatch
remains disabled and unavailable from the CLI.

Remaining separately controlled work:

- append-only ARB/WOP publication receipts;
- independent ARB provenance verification at admission; and
- production dispatcher commissioning. The first operational WOP was accepted
  for admission, but execution remains prohibited while
  `dispatch_permitted: false`.

ZEUS-P2-019 implements the minimum production execution foundation under
SPEC-0012: purpose-scoped first-qualification authority, policy-derived
admission readiness, baseline-bound dispatcher activation, a production agent
registry, authenticated local invocation, signed EENS lifecycle events,
cryptographically verifiable execution evidence, independent qualification,
and scoped live reconciliation adapters. The checked-in activation is
`PREPARED` and the production registry is empty. This implementation does not
commission the dispatcher or claim operational WOP execution capability.

The next controlled sequence is implementation-baseline republication,
authentic dispatcher activation, authentic production-agent registration and
qualification, then a separate first operational WOP execution qualification.

ZEUS-P2-020 establishes the Progressive Manual Capability Test as the
acceptance mechanism for the locked OA-01 through OA-30 sequence. Every gate is
cumulative and requires observable CLI behavior, safe negative behavior,
idempotency, applicable interruption/resume, durable evidence, and regression.
The initial result remains `NOT_READY`; implementation completion reports do
not imply a gate pass. Missing production CLI surfaces remain backlog work and
are not stubbed by the PMCT.

ZEUS-P2-021 implements `zeus next-action` as the first production-facing,
authoritative-state-observation PMCT decision surface. The resolver evaluates authoritative
repository, publication, authority, dispatcher, agent, PMCT, gate, mode, work
authority, and blocker state and selects the earliest unmet prerequisite.
Current mode is BETA and current action is signed baseline republication.
OA-01 implementation and Codex PMCT validation are complete with a `PASS`
demonstration result. Independent operator verification is pending, operator
acceptance is not recorded, and OA-01 gate status is
`AWAITING_OPERATOR_VERIFICATION`. OA-02 is blocked by
`OA-01_OPERATOR_ACCEPTANCE_REQUIRED`; OA-02 through OA-30 remain unaccepted.

ZEUS-P2-022 clarifies that inspection commands preserve authoritative
engineering, tracked repository, and operational decision state while
explicitly documented bounded runtime presentation telemetry may advance.
PMCT now supports exact run-ID inspection and reporting for reproducible
second-window verification. This correction does not resume the Progressive
WOP or advance any OA gate.

ZEUS-P2-023 adds verification-first gate acceptance. Operators use
`zeus approve OA-XX`, `zeus verify OA-XX`, then `zeus approve OA-XX`; Zeus
resolves the run, evidence, baseline, WOP, and receipt identifiers. Isolated
qualification covers refusal, stale bindings, cancellation, duplicate
receipts, and conditional next-gate output. It does not execute OA-02 or
resume the Progressive WOP.

ZEUS-P2-025 resolves the publication/HEAD fixed point with create-only,
read-only-after-publication runtime artifacts and an integrity-bound active pointer. Gate
acceptance is now append-only and versioned: a successor receipt binds the
digest of the preserved predecessor. Eligibility requires an integrity-valid
receipt for the current HEAD, so the historical OA-01 receipt no longer makes
OA-02 conditionally eligible after implementation changes.

ZEUS-P2-026 reconciles the resulting post-publication decision boundary. The
published baseline now matches implementation HEAD, but no current-binding
OA-01 verification or successor acceptance exists. The authoritative next
action is therefore `RUN_OA-01_VERIFICATION`; dispatcher commissioning and
OA-02 execution remain prohibited. After verification passes, explicit OA-01
acceptance is next. Only then may OA-02 pre-execution eligibility be evaluated
through the Progressive WOP. Mission admission `DECIDED` means that baseline
admission reached a decision, not that dispatch or a capability gate is
authorized.

ZEUS-P2-027 corrects the implementation deadlock at that boundary. Completed
PMCT runs now reconcile the capability-state ledger, OA-01 prerequisites with
absent evidence resolve `READY`, and historical PASS runs remain audit evidence
but are ineligible unless repository HEAD, implementation baseline, published
baseline, and active authority publication all match. The fresh current-binding
Codex PMCT run is `PMCT-20260727T034015Z-cf24ac087e20`; independent operator
verification and acceptance have not occurred.

ZEUS-P2-036 implements the distinct OA-02 PMCT demonstration. It preserves
the current-binding PMCT PASS, evaluates OA-02 repository, authority,
lifecycle, configuration, runtime, and safety inputs, and publishes a stable
semantic decision digest. A PASS does not verify OA-02 or authorize dispatch.
With the production registry still empty, Zeus derives
`QUALIFY_PRODUCTION_AGENT` as the next unmet prerequisite.

ZEUS-P2-037 establishes append-only, binding-aware production-agent
qualification beneath the runtime state boundary. The tracked empty registry
remains the schema baseline; effective eligibility is derived from
integrity-valid records matching repository HEAD, published baseline, active
publication, and PMCT evidence. Qualification enables OA-02 verification but
does not activate or authorize dispatch.

The reconciled post-verification state is dispatcher `PREPARED`, operational
dispatch `DISABLED`, PMCT `PASS`, OA-02 verification `PASS`, and
`AUTHORIZE_DISPATCH` / `READY`. Authorization remains an explicit later
operator transition. Invalid PMCT, authority, publication, agent, or OA-02
bindings disable dispatch and block that transition.

Prior accepted gates are durable mission milestones. Successor publications
for later gates inherit OA-01 only when repository provenance and PMCT are
valid and an integrity-protected automated impact assessment finds no changed
OA-01 acceptance criterion. Material changes reopen OA-01 and identify the
exact criteria; a HEAD change alone does not require repeated human approval.

The current `generate-wop` qualification workflow remains review-only. This
roadmap entry does not approve implementation, operational admission,
submission, dispatch, or execution.

P2-038 establishes the repository-authoritative Engineering Execution
Interface. Future missions register one Mission Contract, invoke PROC-0001
through a minimal handoff, consume a Mission Snapshot through
`engctl execution`, and produce a mission-delta Completion Report. Command
authority is classified by SPEC-0005; explicit operator transitions remain
separate.

The original P2-038 completion was premature and was not operator acceptance.
P2-038-CORRECTIVE retains that implementation as unaccepted working-tree work
while correcting semantic ownership, review gates, discovery, snapshot, and
handoff enforcement. Candidate controlled-document revisions are not active or
published.

---

## Engineering Event and Notification System

### Completed — EENS Operational Alpha Foundation

The Engineering Event and Notification System Operational Alpha foundation is
implemented and qualified.

Completed work includes:

- preservation and import of the qualified standalone EENS history without
  squashing;
- preservation of imported namespaced EENS tags;
- establishment of `services/eens` as the canonical Homelab repository source;
- qualification of LOpi as the current operational EENS host;
- append-only SQLite engineering-event persistence;
- SQLite write-ahead logging;
- idempotent event acceptance;
- ordered event replay;
- durable independent consumer checkpoints;
- engineering handoff lifecycle event production;
- wrapped-command lifecycle event production;
- ntfy notification delivery;
- continuous notification-consumer runtime; and
- systemd user-service supervision.

The canonical repository source is:

`/data/engineering/repositories/homelab/services/eens`

The current qualified LOpi deployment is:

`/home/loneal/data/engineering/eens`

The repository source and operational deployment are intentionally separate.

### Future — Full HNS Expansion

EENS Operational Alpha is the completed event and notification foundation. It
does not represent completion of the broader Homelab Notification Service
architecture.

Future HNS expansion includes:

- authenticated WebSocket Tier 1 transport;
- the reference workstation client;
- subscription registration and management;
- delivery-obligation records;
- delivery-attempt evidence and ledgers;
- producer registration, authentication, and authorization;
- a provider registry;
- multiple notification and presentation adapters;
- advanced routing and retry policy;
- Remote Approval;
- dashboard, metrics, observability, and automation consumers; and
- complete HNS operational qualification.

These expansion items remain future engineering work and require separately
authorized implementation.

---

# Governance Framework Modernization ✅

Completed under EGR-000002 and EWO-000018.

- [x] Mission Classification Gate
- [x] Category A, B, and C risk-proportional initiation
- [x] Repository-standard Completion Report
- [x] Mandatory Governance Conformance Review
- [x] Holistic governance-subsystem reconciliation
- [x] Governance architecture and future-mission validation
- [x] Repository-governed workflow behavior independent of handoff wording

---

# Phase 0 — Assessment ✅

Completed

- [x] Linux workstation audit
- [x] Storage inventory
- [x] Partition analysis
- [x] Backup strategy
- [x] Git planning
- [x] Created dedicated /data partition
- [x] Established persistent storage architecture

---

# Phase 1 — Infrastructure Foundation

Status: In Progress

## Repository

- [ ] Complete documentation
- [ ] Hardware inventory
- [ ] Software inventory
- [ ] Network inventory
- [ ] Services inventory

## Automation

- [ ] bootstrap.sh
- [ ] doctor.sh
- [ ] verify.sh
- [ ] update.sh
- [ ] backup.sh improvements

## Configuration

- [ ] Git configuration
- [ ] SSH configuration
- [ ] Bash configuration
- [ ] Docker configuration

---

# Phase 2 — Development Environment

- [ ] Create ~/Development workspace
- [ ] AI Assistant repository
- [ ] SprinterOS repository
- [ ] Business Tools repository
- [ ] Web Scrapers repository
- [ ] Shared utilities repository

---

# Phase 3 — Container Platform

- [ ] Install Docker Engine
- [ ] Docker Compose
- [ ] Local Registry
- [ ] Volume management
- [ ] Network design

---

# Phase 4 — AI Platform

- [ ] Ollama
- [ ] Open WebUI
- [ ] Model management
- [ ] Embedding database
- [ ] Vector storage
- [ ] Local inference APIs

---

# Phase 5 — Data Platform

- [ ] PostgreSQL
- [ ] Redis
- [ ] Data archival
- [ ] Telemetry storage
- [ ] Logging infrastructure

---

# Phase 6 — SprinterOS Platform

- [ ] ECU logging
- [ ] CAN bus utilities
- [ ] Flashing toolkit
- [ ] Telemetry ingestion
- [ ] Performance dashboards

---

# Phase 7 — Business Automation

- [ ] Permit scraper
- [ ] Contractor lead pipeline
- [ ] Product research system
- [ ] AI-assisted reporting

---

# Phase 8 — Infrastructure Automation

- [ ] Ansible
- [ ] Configuration management
- [ ] System validation
- [ ] Automated provisioning

---

# Phase 9 — Dedicated Hardware

- [ ] Development workstation
- [ ] AI server
- [ ] NAS
- [ ] UPS integration
- [ ] Monitoring

---

# Guiding Principles

Every infrastructure change must:

1. Be documented.
2. Be backed up.
3. Be version controlled.
4. Be tested.
5. Include a rollback plan.
6. Be committed to Git.
