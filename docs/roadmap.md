# Homelab Roadmap

Status: Active

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
