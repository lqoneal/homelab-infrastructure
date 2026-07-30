# SPEC-0002 HF-001 Architecture Qualification Matrix

Date: 2026-07-30

Repository: `/data/engineering/repositories/homelab`

Observed HEAD: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`

Architecture content readiness: `READY`

Aggregate promotion readiness: `NOT READY`

Formal PROC-0006 result: not claimed

This matrix records direct non-EWO technical requalification. It does not
approve, activate, publish, persist, implement, or promote architecture.

## Subject manifest

| Subject | Revision | SHA-256 | Path |
|---|---|---|---|
| ARCH-0001 | Draft 1.6 | `a3965a1797d049ca2dc5d8a1d408556ad187d7aa49c4645d73eb52163ac0d9dd` | `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md` |
| ADR-0001 | Draft 1.3 | `bc3749695802757f346ba8c144c7331dbc9cdac931d0a39157066c4df68997c3` | `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md` |
| SPEC-0002 | Draft 1.3 | `0fa1f3153361f18e72be6e8500ce0fb96cfdc5ade2d41a7ab9462b2e7c574741` | `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md` |
| AQR-0001 | Draft 1.1 | `5d9f1d06baf0425adefa0c5e2f9559f42e017cf2f73ace4093cac00e20b15b35` | `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md` |

## Architecture criterion matrix

| Criterion | Determination | Primary evidence | Finding or disposition |
|---|---|---|---|
| AQR-QC-001 Subject identity | PASS | exact front matter, revision history, paths, and final digests | one exact successor candidate identified |
| AQR-QC-002 Architecture completeness | PASS | ARCH Section 23; ADR Sections 14 and 21 | no unanswered Operational Alpha architecture question |
| AQR-QC-003 Decision Request resolution | PASS | 20 unique ARCH Decision Requests; ADR Sections 14.1–14.20 | AQR-F-002 |
| AQR-QC-004 Traceability | PASS | ADR Sections 14 and 20; SPEC Sections 5.12, 16.5, 21.6, 22.1, and 23 | AQR-F-004 resolved |
| AQR-QC-005 Ownership | PASS | ADR Sections 8 and 15; SPEC Sections 5.11–5.12 and 17 | all 14 components and one-writer boundaries mapped |
| AQR-QC-006 Authority | PASS | ADR-D-001–006 and AUTH invariants; SPEC Sections 3, 5, 8, and 21.6 | no circular authority, derived authority, widening, or Execution Grant |
| AQR-QC-007 Lifecycle | PASS | ADR Sections 16 and 18; SPEC Sections 9–14, 17, and 21.6 | state domains remain orthogonal |
| AQR-QC-008 Invariants | PASS | ADR Section 16; SPEC Section 21.6 | 32/32 map to requirement, failure behavior, and evidence |
| AQR-QC-009 Interfaces | PASS | ADR Section 17.1; SPEC Section 16.5 | 13/13 map producer, consumer, binding, output, failure, and validation |
| AQR-QC-010 Specification conformance | PASS | SPEC Draft 1.3 Sections 5.12, 16.5, 21.6, 22.1, and 23 | AQR-F-003 resolved without changing ADR |
| AQR-QC-011 Implementation readiness | PASS | ADR Section 19; SPEC Section 22.1 | 16/16 units map prerequisites, scope, and exit evidence |
| AQR-QC-012 Internal consistency | PASS | authority, ownership, lifecycle, recovery, replay, compatibility, publication, synchronization semantic review | no contradiction or competing owner |
| AQR-QC-013 Controlled-document conformance | PASS | controlled validator, manual semantic review, repository verification, formatting and reference checks | AQR-F-006 remains a nonblocking profile observation |
| AQR-QC-014 Promotion evidence | FAIL | no frozen authorized PROC-0006 transaction; Pending persistence; dirty tree | AQR-F-005 and AQR-F-007 |

## Identifier coverage

| Domain | ADR-owned definitions | Exact SPEC mappings | Coverage |
|---|---:|---:|---|
| ADR decisions | 16 | 16 | complete |
| ADR canonical components | 14 | 14 | complete |
| ADR architectural invariants | 32 | 32 | complete |
| ADR named interfaces | 13 | 13 | complete |
| ADR Future Implementation units | 16 | 16 | complete |

The comparison uses unique exact identifiers from ADR and SPEC. No ADR-owned
identifier in these five domains is missing from SPEC, and SPEC introduces no
identifier outside the ADR-owned sets.

## Bidirectional chain

```text
ARCH finding / recommendation / risk
  -> ARCH Decision Request
  -> ADR decision and resolution
  -> ADR component / invariant / interface
  -> SPEC requirement and validation obligation
  -> ADR Future Implementation unit
  -> future exact-revision WOP and evidence
```

Forward and reverse resolution uses ADR Sections 14 and 20 and SPEC Sections
5.12, 16.5, 21.6, 22.1, and 23. A future WOP closes the final edge only when
separately authorized; this matrix does not authorize implementation.

## Aggregate rule

AQR-QC-001 through AQR-QC-013 pass, establishing architecture and
specification content readiness. AQR-QC-014 remains mandatory for the AQR
`READY` outcome. The aggregate promotion readiness therefore remains
`NOT READY`; passing content criteria are not averaged around the missing
promotion evidence.
