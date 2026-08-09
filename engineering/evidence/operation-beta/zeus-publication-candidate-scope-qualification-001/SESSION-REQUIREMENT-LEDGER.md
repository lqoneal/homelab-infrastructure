# Session Requirement Ledger

| Requirement | Status | Evidence |
|---|---|---|
| Re-establish native transaction and digest invariants | SATISFIED | Native status/inspect and `CANDIDATE-PROVENANCE-AUDIT.json` |
| Enumerate every frozen path exactly once | SATISFIED | 113 rows; invariant PASS |
| Resolve Mission/WOP/authority provenance | SATISFIED | All 19 source manifests bind to the live Mission/WOP |
| Classify Wave 1/2/infrastructure/historical/Wave 3/divergent/ambiguous | SATISFIED | Per-path audit and summary |
| Determine valid convergence vs contamination vs ambiguity | SATISFIED | Determination `AUTHORITY_AMBIGUOUS` |
| Assess resolver boundary policy | SATISFIED | `SELECTION-POLICY-ASSESSMENT.md` |
| Preserve transaction and avoid publication mutation | SATISFIED | Native reverification; index remains clean |
| Implement corrective only if safe authority exists | SATISFIED | Bounded fail-closed overlap guard implemented; no cohort was invented and no replacement transaction was created |
| Native reverification and stop before staging | SATISFIED | `NATIVE-REVERIFICATION.md` |
