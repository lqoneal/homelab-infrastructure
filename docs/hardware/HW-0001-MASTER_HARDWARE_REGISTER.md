---
document_id: HW-0001
title: Master Hardware Register
version: 1.6
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-16
phase: AST-000005 Engineering Disposition Reconciliation
domain: Hardware
classification: Master Hardware Register
source_of_truth: true
related_documents:
  - DOC-0001
  - INF-0001
  - FIN-0001
  - FIN-0002
  - PROJ-0001
  - EDR-0001
  - STD-0005
tags:
  - hardware
  - assets
  - cmdb
  - inventory
  - engineering
  - portfolio
---

# Master Hardware Register

## Purpose

The Master Hardware Register is the authoritative register for all managed physical engineering assets within the engineering portfolio.

Its purpose is to maintain a portfolio-level view of engineering hardware while delegating detailed asset information to individual Asset Records (`AST-*`).

This register summarizes the hardware domain and provides engineering reporting, ownership, assignment, lifecycle, and relationship information.

---

# Authority

This document owns:

- Hardware asset index
- Asset identifier registry
- Portfolio hardware reporting
- Hardware ownership summary
- Hardware assignment summary
- Parent-child asset relationships
- Hardware lifecycle summary

Individual `AST-*` records remain the authoritative source for detailed asset information.

---

# Hardware Governance

Engineering hardware shall comply with the following governance principles.

STD-0005 — Engineering Hardware Lifecycle Standard is the single governing
authority for discovery, identity, qualification, content and preservation
assessment, registration, financial reconciliation, role assignment,
integration, lifecycle management, retirement, and disposal. This register
owns identifier and portfolio state; it does not duplicate that procedure.

## Evidence-Based Records

Every managed hardware asset shall be supported by engineering evidence.

Examples include:

- Physical inspection
- Manufacturer identification
- Purchase documentation
- Serial number verification
- Operating system inventory
- Engineering acceptance

---

## Permanent Asset Identifiers

Every managed hardware asset receives one permanent identifier.

Example:

```text
AST-000001
```

Identifiers are never reused.

Retired assets remain permanently recorded.

---

## Immutable Asset Identity

The engineering identity of an asset remains constant throughout its lifecycle.

Examples:

```
Engineering Workstation
Engineering Terminal 01
Primary Internal NVMe SSD
```

Manufacturers or hardware revisions may change over time without changing the engineering identity.

---

## Ownership

Every managed asset shall have exactly one engineering owner.

Ownership represents long-term responsibility for the asset.

Current owner:

```
Homelab Infrastructure
```

---

## Assignment

Assets may be assigned to projects independently of ownership.

Example:

```
Owner

Homelab Infrastructure

Assignment

SprinterOS
```

Assignments may change without changing ownership.

---

## Lifecycle Management

Every asset shall maintain a lifecycle state.

Current supported lifecycle states:

- Planned
- Procured
- Operational
- Retired
- Disposed

Lifecycle history belongs in the individual Asset Record.

---

## Parent-Child Relationships

Hardware assets may contain or depend upon other managed assets.

Example:

```
Engineering Workstation

├── Primary NVMe SSD
└── Secondary Intel RST Device
```

Relationships are summarized in this register and documented in detail within the associated Asset Records.

---

## Register Philosophy

This register summarizes the Hardware Domain.

Detailed engineering information shall remain within the corresponding `AST-*` records.

The register shall never duplicate detailed engineering configuration that belongs within individual asset records.

---

# Asset Identifier Standard

All managed hardware assets shall be assigned permanent engineering asset identifiers.

| Prefix | Description |
|---------|-------------|
| AST | Engineering Hardware Asset |

Identifiers are sequential, unique, and permanent.

Example:

| Identifier | Description |
|------------|-------------|
| AST-000001 | Engineering Workstation |
| AST-000008 | Engineering Terminal 01 |

Asset identifiers shall never be reused.

---

# Hardware Statistics

## Portfolio Summary

| Metric | Value |
|--------|------:|
| Total Managed Assets | 10 |
| Operational Assets | 8 |
| Available Assets | 2 |
| Planned Assets | 0 |
| Procured (Pending Acceptance) | 0 |
| Retired Assets | 0 |
| Disposed Assets | 0 |

---

## Asset Categories

| Category | Count |
|----------|------:|
| Compute | 3 |
| Storage | 5 |
| Recovery Media | 1 |
| Removable Storage | 1 |

---

## Project Assignment Summary

| Project | Assigned Assets |
|---------|----------------:|
| Homelab Infrastructure | 7 |
| SprinterOS | 2 |
| AI Assistant | 0 |
| Unassigned | 1 |

---

# Managed Asset Register

| Asset ID | Engineering Name | Category | Status | Assigned To |
|----------|------------------|----------|--------|-------------|
| AST-000001 | Engineering Workstation | Compute | Operational | Homelab Infrastructure |
| AST-000002 | Primary Internal NVMe SSD | Storage | Operational | AST-000001 |
| AST-000003 | Secondary Intel RST Device | Storage | Operational | AST-000001 |
| AST-000004 | WD My Passport Backup Drive | Storage | Operational — qualification limitation | Homelab Infrastructure |
| AST-000005 | Seagate Backup Plus Ultra Touch | Storage | Engineering Reprovisioning Authorized — pending requalification | Homelab Infrastructure |
| AST-000006 | SanDisk Recovery USB | Recovery Media | Operational | Homelab Infrastructure |
| AST-000007 | Raspberry Pi 5 | Compute | Operational | SprinterOS |
| AST-000008 | Engineering Terminal 01 | Compute | Operational | SprinterOS |
| AST-000009 | Engineering Spare microSD Card 01 | Removable Storage | Available | Unassigned |
| AST-000010 | WD 500 GB External HDD | Storage | Available — preservation hold | Homelab Infrastructure — Engineering preservation storage |

---

# Ownership Summary

## Current Hardware Owner

| Owner | Assets |
|-------|-------:|
| Homelab Infrastructure | 10 |

Engineering ownership represents long-term responsibility for hardware lifecycle management.

---

# Assignment Summary

| Assignment | Assets |
|-----------|-------:|
| Homelab Infrastructure | 7 |
| SprinterOS | 2 |
| Unassigned | 1 |

Assignments indicate which engineering project currently utilizes an asset.

Ownership and assignment are intentionally maintained as independent engineering concepts.

---

# Relationship Summary

## Parent-Child Relationships

```text
AST-000001 Engineering Workstation
├── AST-000002 Primary Internal NVMe SSD
└── AST-000003 Secondary Intel RST Device
```

---

## Procurement Relationships

```text
PROC-000001
└── AST-000008 Engineering Terminal 01

PROC-000002
└── AST-000009 Engineering Spare microSD Card 01
```

---

## Project Relationships

```text
SprinterOS
├── AST-000007 Raspberry Pi 5
└── AST-000008 Engineering Terminal 01
```

---

# Hardware Reporting

## Current Engineering Hardware Inventory

| Type | Count |
|------|------:|
| Engineering Workstations | 1 |
| Engineering Terminals | 1 |
| Single Board Computers | 1 |
| Storage Devices | 5 |
| Recovery Media | 1 |
| Removable Storage | 1 |

---

## Engineering Portfolio Snapshot

The engineering portfolio currently manages ten hardware assets: eight are
operational and two are available and unassigned. AST-000010 remains under a
preservation hold pending backup review and filesystem-limitation disposition.

All managed hardware assets have individual engineering asset records.

All managed assets are operational or available for controlled engineering use.

No assets are currently planned, retired, or disposed.

---

# Related Controlled Documents

## Portfolio Governance

| Document | Purpose |
|----------|---------|
| DOC-0001 | Repository Document Index |
| PROJ-0001 | Project State |
| EDR-0001 | Hardware Asset Record Architecture |
| STD-0005 | Engineering Hardware Lifecycle Standard |

---

## Infrastructure

| Document | Purpose |
|----------|---------|
| INF-0001 | Engineering Infrastructure Baseline |

---

## Finance

| Document | Purpose |
|----------|---------|
| FIN-0001 | Master Financial Ledger |
| FIN-0002 | Master Procurement Register |
| PROC-* | Procurement Records |
| TRX-* | Financial Transaction Records |

---

## Hardware Records

Individual hardware assets are documented in the following controlled records.

| Asset Record | Description |
|-------------|-------------|
| AST-000001 | Engineering Workstation |
| AST-000002 | Primary Internal NVMe SSD |
| AST-000003 | Secondary Intel RST Device |
| AST-000004 | WD My Passport Backup Drive |
| AST-000005 | Seagate Backup Plus Ultra Touch |
| AST-000006 | SanDisk Recovery USB |
| AST-000007 | Raspberry Pi 5 |
| AST-000008 | Engineering Terminal 01 |
| AST-000009 | Engineering Spare microSD Card 01 |
| AST-000010 | WD 500 GB External HDD |

---

# Engineering Reporting Policy

The Master Hardware Register provides a portfolio-level summary of managed engineering hardware.

It is not intended to duplicate the detailed technical information contained within individual Asset Records.

Engineering reports, dashboards, and future Engineering Management Platform services shall derive hardware portfolio information from this register and the associated `AST-*` records.

---

# Engineering Notes

The Hardware Domain is the first completed engineering asset domain within the portfolio.

It establishes the portfolio standards for:

- Evidence-backed asset management
- Permanent engineering identifiers
- Ownership versus assignment
- Parent-child asset relationships
- Lifecycle management
- Portfolio reporting
- Cross-domain traceability

Future engineering domains should follow this same register-and-record architecture.

---

# Future Engineering Direction

Planned enhancements include:

- Hardware Asset Classification Standard (`HW-0002`)
- Automated hardware discovery
- Relationship validation tooling
- Asset lifecycle automation
- Asset depreciation and valuation integration
- Engineering Management Platform synchronization

These enhancements shall build upon the governance established by this register without altering its fundamental architecture.

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | 2026-07-06 | Initial Master Hardware Register established and integrated with AST-000001 through AST-000008. |
| 1.1 | 2026-07-15 | Registered AST-000009 as available, unassigned engineering spare removable storage. |
| 1.2 | 2026-07-16 | Registered AST-000010 as qualified hardware, available and unassigned under preservation hold with an explicit exFAT label limitation. |
| 1.3 | 2026-07-16 | Integrated STD-0005 as the single governing hardware-lifecycle authority while preserving this register's identifier and portfolio-reporting ownership. |
| 1.4 | 2026-07-16 | Recorded AST-000005 qualification hold after enclosure-boundary failure isolation. |
| 1.5 | 2026-07-16 | Assigned AST-000010 to Engineering preservation storage and recorded AST-000004 qualification limitations without approving either proposed operational role. |
| 1.6 | 2026-07-16 | Recorded owner-authorized AST-000005 secure reprovisioning disposition and pending-requalification lifecycle without assigning an operational role. |
