# Hydration Classification Matrix

| Condition | Classification | Action |
|---|---|---|
| Missing derived field with one valid receipt source | `DERIVABLE_FROM_RECEIPT` | Hydrate and record provenance. |
| Missing source/package field with no receipt value | `HISTORICAL_EVIDENCE_UNAVAILABLE` | Leave unresolved; fail closed if required. |
| Conflicting stored and receipt values | `CONFLICTING_AUTHORITATIVE_VALUES` | Stop with authority-chain failure. |
| Missing provider/agent binding | `HISTORICAL_EVIDENCE_UNAVAILABLE` | Never invent active binding. |
