# Conflict Classification Matrix

| Condition | Action |
|---|---|
| Missing/partial admission or execution | Atomic projection repair |
| Equivalent duplicate | Reuse canonical record; preserve evidence |
| Stale derived binding | Reconcile/rebind deterministically |
| Corrupt projection | Fail closed unless integrity-preserving repair is proven |
| Divergent immutable identity/digest | Fail closed |
| Interrupted transaction | Resume journal or rollback |
| Premature lifecycle advancement | Block until persistence verifies |
