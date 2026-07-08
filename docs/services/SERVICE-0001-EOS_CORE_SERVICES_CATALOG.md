---
document_id: SERVICE-0001
title: EOS Core Services Catalog
version: 1.0
status: Draft
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-08
governed_by: EOS-0001
implements:
  - EOS-0002
depends_on:
  - SPEC-0004
  - SPEC-0005
source_of_truth: true
---

# EOS Core Services Catalog

---

# 1. Purpose

This document defines the authoritative catalog of Engineering Operating System (EOS) Core Services.

A Core Service is a reusable engineering capability that provides functionality to one or more engineering programs while remaining independent of any individual project.

The catalog establishes service responsibilities, boundaries, and relationships. It does not define implementation details.

---

# 2. Service Architecture

EOS services consume Authoritative Engineering Records and produce engineering capabilities or derived engineering views.

Services SHALL remain implementation independent and SHALL conform to the Engineering Authority Model.

---

# 3. Core Services

## Engineering Context Reconstruction Service (ECRS)

**Specification:** SPEC-0004

Purpose:

Reconstruct complete engineering context from Authoritative Engineering Records.

Primary consumers:

- engctl
- Project wrappers
- AI assistants
- Future user interfaces

---

## Engineering Control Service (ECS)

**Specification:** SPEC-0005

Purpose:

Provide a unified control interface to EOS Core Services.

Responsibilities:

- Command routing
- Project context resolution
- Service dispatch

---

## Documentation Service

Purpose:

Manage controlled engineering documents throughout their lifecycle.

Responsibilities:

- Controlled document creation
- Metadata validation
- Relationship management
- Publication support

---

## Validation Service

Purpose:

Verify compliance with governing specifications and engineering standards.

Responsibilities:

- Specification validation
- Relationship validation
- Engineering rule validation
- Acceptance reporting

---

## Checkpoint Service

Purpose:

Capture engineering checkpoints that enable reliable engineering continuity.

Responsibilities:

- Checkpoint creation
- Checkpoint restoration
- Session continuity

---

## Inventory Service

Purpose:

Maintain awareness of engineering assets and capabilities.

Responsibilities:

- Repository inventory
- Document inventory
- Hardware inventory
- Service inventory

---

## Publishing Service

Purpose:

Generate derived engineering publications from Authoritative Engineering Records.

Responsibilities:

- Reports
- Dashboards
- Navigation
- Documentation views

Published outputs remain derived views.

---

## Journal Service

Purpose:

Capture chronological engineering activity while preserving traceability.

Responsibilities:

- Engineering journal entries
- Session history
- Activity timeline

Journal entries SHALL reference Authoritative Engineering Records where applicable.

---

# 4. Service Relationships

Core Services cooperate through well-defined responsibilities.

```
                Engineering Control Service
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Context           Validation        Documentation
Reconstruction          Service            Service
        │                  │                  │
        ├──────────────┬───┘                  │
        ▼              ▼                      ▼
 Inventory        Checkpoint            Publishing
        │              │                      │
        └──────────────┴──────────────┬───────┘
                                      ▼
                             Authoritative
                          Engineering Records
```

No service shall duplicate the responsibilities of another service.

---

# 5. Service Design Principles

Every EOS Core Service SHALL:

- provide a single well-defined responsibility;
- consume Authoritative Engineering Records where applicable;
- produce deterministic results;
- remain independently testable;
- expose reusable interfaces;
- support multiple user interfaces.

---

# 6. Future Expansion

Additional services MAY be introduced through Engineering Decision Records and approved specifications.

New services SHALL:

- define a unique responsibility;
- avoid overlapping existing services;
- preserve architectural separation of concerns.

---

# Compliance

This catalog is the authoritative inventory of EOS Core Services.

All future EOS services SHALL be represented within this catalog before implementation.
