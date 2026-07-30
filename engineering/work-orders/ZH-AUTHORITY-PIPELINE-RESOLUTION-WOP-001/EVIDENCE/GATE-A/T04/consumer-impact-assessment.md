# T04 Consumer Impact Assessment

| Consumer | Impact |
| --- | --- |
| Progressive CLI verification | Canonical verifier selection through `ProgressiveGateService`; existing authority prechecks preserved |
| Progressive CLI approval/rejection | Direct canonical decision façade consumption; JSON/replay compatibility preserved |
| `progressive_oa` | Remains a temporary compatibility adapter; not expanded or retired |
| PMCT / Agent Qualification | No migration |
| Carry-forward / Mission Contract / ARS / EWI | No migration |
| Execution runtime | No redesign |
| Gate-specific verifiers | Remain canonical implementations selected by Layer 1 |
| Legacy owners | Remain present |

The expected behavioral difference is architectural only: the CLI no longer
selects verifier implementations or reaches decision authority through a
compatibility adapter.

