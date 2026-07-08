---
document_id: FIN-0002
title: Master Procurement Register
version: 1.0
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-06
phase: Mission 0 / Phase 0.1
domain: Finance
classification: Master Procurement Register
source_of_truth: true
related_documents:
  - FIN-0001
  - HW-0001
  - PROJ-0001
tags:
  - finance
  - procurement
  - purchasing
  - engineering
---

# Master Procurement Register

## Purpose

This document is the authoritative register for all engineering procurement activities within the portfolio.

It indexes procurement records while providing portfolio-level procurement reporting.

Individual procurement records are maintained as immutable `PROC-*` records.

---

# Authority

This document owns:

- Procurement register
- Procurement summary reporting
- Procurement status reporting
- Cross-references to engineering assets
- Cross-references to financial transactions

Detailed procurement history belongs exclusively to individual procurement records.

---

# Procurement Governance

Engineering procurements shall:

1. Be evidence-backed.
2. Be assigned permanent Procurement IDs.
3. Reference affected engineering assets where applicable.
4. Reference associated financial transactions.
5. Remain immutable after approval.

Corrections shall be recorded by creating additional procurement records rather than rewriting history.

---

# Procurement Status Summary

| Status | Count |
|---------|------:|
| Requested | 0 |
| Approved | 0 |
| Ordered | 0 |
| Received | 0 |
| Closed | 0 |

---

# Procurement Register

| Procurement ID | Project | Description | Status | Asset | Transaction |
|----------------|---------|-------------|--------|-------|-------------|
| None | — | No procurement records currently registered. | — | — | — |

---

# Procurement Policy

Every engineering procurement shall answer the following questions:

- What was purchased?
- Why was it purchased?
- Which project benefits?
- Which engineering assets are affected?
- Which transaction paid for it?
- What evidence supports the purchase?

---

# Related Controlled Documents

| Document | Relationship |
|----------|--------------|
| FIN-0001 | Portfolio financial summary |
| HW-0001 | Hardware asset register |
| PROJ-0001 | Project state |
| PROC-* | Individual procurement records |
| TRX-* | Individual financial transactions |

---

# Engineering Notes

The Master Procurement Register summarizes procurement activity while delegating historical detail to immutable procurement records.

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | 2026-07-06 | Initial Master Procurement Register established. |
