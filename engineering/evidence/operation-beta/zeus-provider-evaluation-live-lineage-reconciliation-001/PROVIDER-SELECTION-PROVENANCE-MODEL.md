# Provider-Selection Provenance Model

| Operand | Authority | Meaning |
|---|---|---|
| `mission_provenance_baseline` | immutable P2/P3/P4 chain | Original lifecycle provenance baseline |
| provider `current_published_baseline` | immutable provider-selection receipt | Published baseline observed when selection was created |
| current published baseline | live Git/EOS projection | Current `HEAD == origin/main == EOS` baseline |
| provider identity | live execution-agent registry plus immutable selection | Selected provider and point-in-time selection evidence |

Validity is:

```text
repository identity PASS
+ mission/WOP/receipt bindings PASS
+ provider-selection receipt integrity PASS
+ provenance baseline -> recorded selection baseline ancestry PASS
+ recorded selection baseline -> live current baseline ancestry PASS
+ live HEAD/origin/EOS parity PASS
= provider selection remains current
```

Historical provider-selection receipts are not rewritten. A later dispatch
boundary must independently revalidate live provider availability and
qualification; repository publication alone does not require provider
reselection.

