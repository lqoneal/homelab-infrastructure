# Actual Runtime Lifecycle Map

| Stage | Current owner/artifact | Result |
|---|---|---|
| submit/canonicalize | `submission_boundary.py`, canonicalization, P2 receipt/request | Implemented and integrated through `ADMISSION_REQUESTED` |
| admission | `mission_admission_boundary.py`, admission/mission contract receipts | Implemented boundary; not exercised here |
| bootstrap/dispatch | bootstrap, Stage 1, provider/dispatched receipts | Split across boundaries; not end-to-end proven |
| provider/session | provider selection, launch, Codex/session modules | Component implementations; integration proof incomplete |
| execution start/work | execution-start/runtime/monitoring | Boundary exists; not exercised here |
| evidence/qualification | evidence capture/qualification modules | Component-tested; real mission chain unproven |
| publication/EOS | read-only publication workflow plus external `engctl` procedures | Mutation and receipt bridge not proven as one mission chain |
| closeout | reconciliation closeout plus legacy Beta closeout | Duplicate/compatibility paths; convergence incomplete |

The intended canonical authority is the receipt-backed lifecycle chain rooted in P2/P3 and the lifecycle procedure. In implementation, several subordinate stores/controllers still have independent expectations.

