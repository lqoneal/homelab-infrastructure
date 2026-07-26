# Homelab Roadmap

Status: Active

---

## Current Mission — Zeus Operational Alpha

Zeus Operational Alpha is the current authoritative Homelab engineering
mission under PHASE-0001 and PROJ-0001.

The current authority establishes portfolio direction and a consistent resume
baseline only. No Zeus runtime implementation, production modification,
autonomous execution, feature development, or Work Package execution is
authorized.

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
immutable WOP finalization, explicit dual generation modes, and fail-closed
validation. The repository-fixed live source is deliberately unconfigured
until its designated owners publish operational records.

ZEUS-P2-004 implements and qualifies signed, owner-scoped staging, full-source
readiness verification, explicit atomic activation, rollback, revocation, and
recovery. Production trust roots and authority records remain unenrolled, so
the checked-in runtime continues to fail closed.

ZEUS-P2-005 commissioning preflight is blocked. No production owner principals
or signer keys are enrolled, no signed publication envelopes are present, and
no genuine ZEUS-P2-005 approval record has been supplied. Workstation SSH keys
are not treated as authority-owner keys. Both operational switches remain
false until the designated owners provide authentic inputs through the
publication framework.

ZEUS-P2-006 implements and qualifies the remaining software-side owner
enrollment toolkit: public-key inspection, externally authorized enrollment,
rotation, suspension, retirement, candidate trust compilation, unsigned
publication templates, Governance approval payload validation, and
blocker-specific commissioning diagnostics. It neither enrolls production
owners nor activates Zeus.

ZEUS-P2-007 implements and qualifies the unified Mission Admission Runtime.
Qualification and future operational admissions now traverse the same
persistent, digest-protected, restartable state machine through repository
verification, authority resolution, WOP generation, submission eligibility,
and admission decision. Production remains blocked at the authority gate
because authentic external owner artifacts are absent. The runtime never
self-enables, submits, dispatches, or executes.

ZEUS-P2-008 implements and qualifies the persistent Mission Execution Runtime:
typed gates, digest-bound state, immutable hash-chained evidence, checkpoints,
safe interruption/resume, explicit wait/suspend/cancel states, stable handler
idempotency keys, and an EENS append-only event adapter. Qualification performs
a complete non-mutating simulation. Operational execution stops at the
disabled dispatch boundary; no production handler or activation was added.

Remaining separately controlled work:

- controlled enrollment of authentic owner public keys;
- signed publication of live owner records;
- append-only ARB/WOP publication receipts;
- independent ARB provenance verification at admission; and
- operational activation after supervised live-source qualification.

The current `generate-wop` qualification workflow remains review-only. This
roadmap entry does not approve implementation, operational admission,
submission, dispatch, or execution.

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
