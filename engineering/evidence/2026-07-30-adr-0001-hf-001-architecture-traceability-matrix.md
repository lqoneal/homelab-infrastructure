# ADR-0001-HF-001 Architecture Traceability Matrix

Date: 2026-07-30

## Traceability Rule

The required forward lineage is:

```text
ARCH Finding
  -> Engineering Recommendation
  -> Decision Request
  -> ADR Decision and Resolution
  -> Canonical Architectural Component
  -> Future Implementation Unit
```

Reverse component-to-assessment lineage is recorded in ADR-0001 §20.4.

## Finding-to-Implementation Matrix

| Finding | Recommendation | Decision Request | ADR decision | Component | Future implementation |
|---|---|---|---|---|---|
| ARCH-F-001 | ARCH-REC-001 | ARCH-DR-004 | ADR-D-005 | ADR-C-007 | ADR-FI-004, ADR-FI-015 |
| ARCH-F-002 | ARCH-REC-001, ARCH-REC-007 | ARCH-DR-002 through ARCH-DR-004 | ADR-D-004 through ADR-D-006 | ADR-C-006 through ADR-C-008 | ADR-FI-003 through ADR-FI-005 |
| ARCH-F-003 | ARCH-REC-007 | ARCH-DR-002 through ARCH-DR-005; ARCH-DR-010; ARCH-DR-014; ARCH-DR-016, ARCH-DR-017, ARCH-DR-019 | ADR-D-003 through ADR-D-007, ADR-D-012, ADR-D-013, ADR-D-015 | ADR-C-002, ADR-C-006 through ADR-C-008, ADR-C-014 | ADR-FI-003 through ADR-FI-005, ADR-FI-010, ADR-FI-011, ADR-FI-016 |
| ARCH-F-004 | ARCH-REC-009 | ARCH-DR-001, ARCH-DR-008 | ADR-D-001, ADR-D-008, ADR-D-012 | ADR-C-001 through ADR-C-004, ADR-C-014 | ADR-FI-001, ADR-FI-008 |
| ARCH-F-005 | ARCH-REC-004 | ARCH-DR-005, ARCH-DR-012, ARCH-DR-015 | ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 |
| ARCH-F-006 | ARCH-REC-005, ARCH-REC-009 | ARCH-DR-006, ARCH-DR-018 through ARCH-DR-020 | ADR-D-008, ADR-D-014 through ADR-D-016 | ADR-C-001, ADR-C-003, ADR-C-008, ADR-C-009, ADR-C-011 | ADR-FI-006, ADR-FI-013, ADR-FI-014, ADR-FI-016 |
| ARCH-F-007 | ARCH-REC-002, ARCH-REC-003, ARCH-REC-008 | ARCH-DR-007, ARCH-DR-009, ARCH-DR-015 | ADR-D-010, ADR-D-012 | ADR-C-011, ADR-C-013, ADR-C-014 | ADR-FI-007, ADR-FI-009, ADR-FI-015 |
| ARCH-F-008 | ARCH-REC-003 | ARCH-DR-009, ARCH-DR-015, ARCH-DR-016 | ADR-D-002, ADR-D-004, ADR-D-006, ADR-D-012 | ADR-C-005, ADR-C-006, ADR-C-008, ADR-C-010, ADR-C-013 | ADR-FI-002, ADR-FI-009, ADR-FI-010, ADR-FI-015 |
| ARCH-F-009 | ARCH-REC-009 | ARCH-DR-006, ARCH-DR-019 | ADR-D-008, ADR-D-015 | ADR-C-001 through ADR-C-014 | ADR-FI-006, ADR-FI-016 |
| ARCH-F-010 | ARCH-REC-007 | ARCH-DR-013, ARCH-DR-019 | ADR-D-011, ADR-D-015 | ADR-C-012 | ADR-FI-012, ADR-FI-016 |
| ARCH-F-011 | ARCH-REC-007 | ARCH-DR-019, ARCH-DR-020 | ADR-D-007, ADR-D-015, ADR-D-016 | ADR-C-008 through ADR-C-012 | ADR-FI-014, ADR-FI-016 |
| ARCH-F-012 | ARCH-REC-002, ARCH-REC-003, ARCH-REC-008 | ARCH-DR-009, ARCH-DR-015 | ADR-D-003, ADR-D-004, ADR-D-006, ADR-D-012 | ADR-C-006, ADR-C-008, ADR-C-013, ADR-C-014 | ADR-FI-009, ADR-FI-015 |
| ARCH-F-013 | ARCH-REC-004, ARCH-REC-006 | ARCH-DR-005, ARCH-DR-015 | ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 |

## Coverage Audit

| Traceability class | Expected | Covered | Missing | Result |
|---|---:|---:|---:|---|
| ARCH findings | 13 | 13 | 0 | PASS |
| ARCH recommendations | 9 | 9 | 0 | PASS |
| ARCH Decision Requests | 20 | 20 | 0 | PASS |
| ARCH risks | 15 | 15 | 0 | PASS |
| ADR decisions | 16 | 16 | 0 | PASS |
| Canonical components | 14 | 14 | 0 | PASS |
| Future Implementation units | 16 | 16 | 0 | PASS |

`ARCH-RISK-012` is explicitly disposed as a non-architectural controlled
framework deferral because the missing semantic profile does not require an
architecture selection. Every other risk maps to one or more Decision
Requests and architecture decisions.

## Reverse Coverage

ADR-0001 §20.4 maps every `ADR-C-001` through `ADR-C-014` back to its ADR
decisions and ARCH Decision Requests, then forward to `ADR-FI-001` through
`ADR-FI-016`. The structural audit found:

- unresolved decision references: 0;
- unresolved component references: 0;
- unresolved Future Implementation references: 0;
- orphaned Decision Requests: 0;
- Future Implementation dependency cycles: 0.

Result: PASS.
