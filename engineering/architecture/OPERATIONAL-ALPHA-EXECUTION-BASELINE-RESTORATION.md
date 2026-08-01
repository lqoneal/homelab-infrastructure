---
document_id: OA-EXECUTION-BASELINE-RESTORATION
title: Operational Alpha Execution Baseline Restoration
version: '1.0'
status: Active
owner: Homelab Infrastructure
classification: Controlled Architecture
---

# Operational Alpha Execution Baseline Restoration

Operational Alpha uses the stable repository-local admission and dispatch
execution model until Operational Alpha completion. Convergence bindings,
bootstrap admission, immutable package enforcement, ZDCL implementation, and
CAGF implementation are post-Operational-Alpha engineering platform work.

Convergence remains an explicit, fail-closed mode when a valid `--wop` binding
is supplied. It is not an implicit prerequisite for Operational Alpha gate
verification or mission execution. This baseline remains active through OA-30
acceptance; post-OA-30 evolution is governed by
`engineering/docs/architecture/ENGINEERING-PLATFORM-EVOLUTION-PHASE-1.md`.

The ZDCL and CAGF architecture, roadmaps, specifications, and recommendations
remain preserved as post-Operational Alpha direction. The Phase 1 standards
become active only after successful OA-30 acceptance, and each implementation
requires a separately authorized work order. No implementation is authorized
by this document.
