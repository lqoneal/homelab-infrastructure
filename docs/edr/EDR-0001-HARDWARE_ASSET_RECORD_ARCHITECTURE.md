---
document_id: EDR-0001
title: Hardware Asset Record Architecture
version: 1.0
status: Approved
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-08
phase: Mission 0 / Phase 0.1
domain: Hardware
classification: Engineering Decision Record
source_of_truth: true
related_documents:
  - DOC-0001
  - PROJ-0001
  - HW-0001
---

# Engineering Decision Record (EDR-0001)

## Title

Hardware Asset Record Architecture

---

# 1. Purpose

This Engineering Decision Record defines the architecture used by the Homelab Infrastructure hardware domain to represent managed engineering assets.

It restores the decision record referenced by `HW-0001` and preserves the already implemented hardware asset model without introducing new architecture.

---

# 2. Context

The Homelab repository contains a Master Hardware Register and individual engineering asset records.

The Master Hardware Register provides portfolio-level hardware reporting.

Individual `AST-*` records preserve detailed asset identity, configuration, lifecycle, ownership, assignment, and relationship information.

---

# 3. Decision

Homelab Infrastructure uses a two-level hardware record architecture.

1. `HW-0001` is the authoritative portfolio hardware register.
2. `AST-*` records are the authoritative detailed records for individual hardware assets.

The register summarizes hardware state and relationships.

The individual asset records own detailed asset facts.

---

# 4. Rationale

This architecture prevents the Master Hardware Register from duplicating detailed configuration that belongs in individual asset records.

It preserves a stable portfolio summary while allowing detailed records to evolve independently.

It also supports traceability from procurement and transaction records to accepted engineering assets.

---

# 5. Consequences

- Hardware reporting is centralized in `HW-0001`.
- Detailed asset configuration remains in `AST-*` records.
- Parent-child relationships are summarized in `HW-0001` and detailed in asset records where applicable.
- Procurement and transaction relationships may reference individual asset records.

---

# 6. Status

Approved as the implemented hardware-domain decision for Mission 0 / Phase 0.1.

This record reconciles a zero-byte legacy file with existing repository evidence.

---

# Revision History

| Version | Date       | Description |
| ------- | ---------- | ----------- |
| 1.0     | 2026-07-08 | Restored hardware asset record architecture decision from existing repository evidence. |
