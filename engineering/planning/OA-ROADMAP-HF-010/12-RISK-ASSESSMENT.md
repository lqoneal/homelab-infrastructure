# Risk Assessment

Status: `INDEPENDENT ASSESSMENT — NON-AUTHORITATIVE`

| Risk | Likelihood | Impact | Evidence / mitigation |
|---|---|---|---|
| Multiple incompatible fact stores emerge | high | high | F-001; adopt canonical registry/store contract before implementation |
| Subsystems interpret metadata differently | high | high | F-002/F-004; publish versioned payload/error schemas and fixtures |
| Ownership cannot be reconciled | medium | high | F-003; establish owner directory/delegation policy |
| Stale or duplicate projections persist | medium | high | F-005; define idempotency, checkpoints, replay, discrepancy lifecycle |
| Qualification results vary by implementation | medium | high | F-006; implement executable criteria and retained evidence |
| Current planning artifact is mistaken for generated evidence | medium | moderate | F-007; embed/verify provenance only after generator exists |
| Terminology diverges across future implementations | medium | moderate | canonical vocabulary work in HF-009 milestone 1 |
