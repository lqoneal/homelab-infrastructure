# BETA-01 Functional Gap Analysis

| Requirement | Result | Evidence/disposition |
| --- | --- | --- |
| authorized submission | existing | `zeus submit`, EMP orchestration state |
| staging/priority | existing | orchestration record and policy selection |
| queue inspection | extended | MKM-backed `zeus mission queue` views |
| admission | existing | `admit-mission`, WOP admission controller |
| scheduling/selection | existing | dependency/readiness-aware orchestration |
| bound execution context | existing | mission admission and execution runtimes |
| lifecycle/history | existing | hash-bound lifecycle and execution records |
| EENS events | planned integration boundary | no duplicate event authority introduced |
| persistent queue metrics | intentionally absent | derived per request; never stored as authority |

No missing requirement justified a new subsystem. EENS event emission remains a
documented integration boundary rather than a second event store in Zeus.
