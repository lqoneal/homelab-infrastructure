# AQR-0001 HF-001 Architecture Qualification Matrix

Date: 2026-07-30

Repository: `/data/engineering/repositories/homelab`

Observed HEAD: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`

Readiness outcome: `NOT READY`

This matrix records a direct non-EWO technical review. It does not claim a
formal PROC-0006 qualification result, Engineering Governance disposition, or
lifecycle transition.

## Subject manifest

| Subject | Revision | SHA-256 | Path |
|---|---|---|---|
| ARCH-0001 | Draft 1.6 | `a3965a1797d049ca2dc5d8a1d408556ad187d7aa49c4645d73eb52163ac0d9dd` | `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md` |
| ADR-0001 | Draft 1.3 | `bc3749695802757f346ba8c144c7331dbc9cdac931d0a39157066c4df68997c3` | `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md` |
| SPEC-0002 | Draft 1.2 | `3e07355dda0c8f3f9d3951b98ffae8969b79a6dd397c9973233abc5e4fa39bd4` | `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md` |

## Criterion matrix

| Criterion | Applicability | Determination | ARCH evidence | ADR evidence | SPEC evidence | Finding |
|---|---|---|---|---|---|---|
| AQR-QC-001 Subject identity | All candidate records | PASS | front matter; revision history | front matter; revision history | front matter; revision history | none |
| AQR-QC-002 Architecture completeness | Assessment and decision | PASS | Section 23 completion criteria | Sections 14 and 21 | downstream only | AQR-F-001 |
| AQR-QC-003 Decision Request resolution | All 20 ARCH Decision Requests | PASS | `ARCH-DR-001`–`020` | Sections 14.1–14.20 | decision trace only | AQR-F-002 |
| AQR-QC-004 Traceability | Complete candidate | FAIL | 13 findings, 9 recommendations, 15 risks, 20 Decision Requests | Sections 20.1–20.5 cover assessment through Future Implementation | Section 23 maps only 16 ADR decisions | AQR-F-004 |
| AQR-QC-005 Ownership | All authoritative and derived facts | FAIL | Decision Requests and risks identify ambiguity | Sections 8 and 15 assign 14 canonical components and one-writer ownership | Sections 5.11 and 17 align semantically but do not map ADR-C-001–014 | AQR-F-003, AQR-F-004 |
| AQR-QC-006 Authority | Mission authority and initiation | PASS | DR-001–005, 010, 014, 017 | decisions, components, AUTH invariants, interfaces | Sections 3, 5, and 8 | none |
| AQR-QC-007 Lifecycle | All state domains | PASS | DR-006 and risks | Sections 16 and 18 | Sections 9–14 and 17 | none |
| AQR-QC-008 Invariants | 32 ADR invariants | FAIL | completion criteria require invariants | Section 16 defines 32 unique invariant IDs | equivalent requirements exist but no `ADR-INV-*` map | AQR-F-004 |
| AQR-QC-009 Interfaces | 13 ADR interfaces | FAIL | Decision Requests identify boundary questions | Section 17.1 defines 13 named contracts | Section 16 defines common envelopes but not the 13 named mappings | AQR-F-004 |
| AQR-QC-010 Specification conformance | Exact ADR/SPEC pair | FAIL | SPEC is required downstream | Section 20.5 requires Draft 1.3 reconciliation | revision history ends at 1.2 | AQR-F-003 |
| AQR-QC-011 Implementation readiness | Complete architecture candidate | FAIL | assessment criteria present | Section 19 defines 16 acyclic implementation units | no `ADR-FI-*` coverage | AQR-F-003, AQR-F-004 |
| AQR-QC-012 Internal consistency | Complete candidate | PASS | assessment preserves questions | ADR answers remain authority-acyclic and owner-separated | reviewed content does not contradict those answers | none |
| AQR-QC-013 Controlled-document conformance | All controlled records and AQR | PASS | general validator | general validator | general validator | AQR-F-006 observation |
| AQR-QC-014 Promotion evidence | Promotion candidate | FAIL | Draft/Pending | Draft/Pending | Draft/Pending | AQR-F-005, AQR-F-007 |

## Identifier coverage

| Domain | Expected | Observed | Coverage |
|---|---:|---:|---|
| ARCH findings | 13 | 13 | complete in ADR traceability |
| ARCH recommendations | 9 | 9 | complete in ADR traceability |
| ARCH risks | 15 | 15 | complete in ADR traceability |
| ARCH Decision Requests | 20 | 20 | complete in ADR resolutions |
| ADR decisions | 16 | 16 | present in SPEC Section 23 |
| ADR components | 14 | 0 exact SPEC mappings | blocking gap |
| ADR invariants | 32 | 0 exact SPEC mappings | blocking gap |
| ADR named interfaces | 13 | 0 exact SPEC mappings | blocking gap |
| ADR Future Implementation units | 16 | 0 exact SPEC mappings | blocking gap |

## Aggregate rule

Any `FAIL` or `BLOCKED` mandatory criterion produces `NOT READY`. Seven
criteria fail. The candidate is therefore `NOT READY`; passing criteria shall
not be averaged into a percentage or maturity estimate.
