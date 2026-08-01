# Validator Drift Matrix

| Rule | Before | Canonical result | Evidence |
|---|---|---|---|
| WOP identity | execution accepted UUID only | semantic published references plus legacy UUIDs | `WOP-ZDCL-01-FOUNDATION-001` validates |
| approval date | required and parsed as a mandatory string | optional; ISO-8601 when present | admission regression passes omitted-date case |
| approval authority | stage-specific generated fields | mission-contract-bound authority/reference | ZDCL-01 admission binding |
| execution status | explicit ID always required | one active execution auto-resolves; ambiguity fails closed | execution interface regression |
| historical waiting record | old failure text retained | immutable evidence preserved; current validation is a new projection | ZDCL-01 controller output |

No historical package, admission, or execution record was rewritten.
