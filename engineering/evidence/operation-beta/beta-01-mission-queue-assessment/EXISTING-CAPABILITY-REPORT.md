# BETA-01 Existing Capability Report

## Determination

Result B: the existing authoritative framework requires a projection
extension, not a new queue or scheduler.

## Evidence-backed inventory

| Function | Existing implementation | Disposition |
| --- | --- | --- |
| submission | `scripts/zeus submit` → `MissionOrchestrator.submit` | retain; document |
| staging and priority | EMP orchestration state and `missions list` | retain; document |
| queue state | `WopLifecycleManager` plus MKM mission projections | retain; expose richer projection |
| eligibility | `mission_eligibility.py`, MKM readiness | retain |
| selection | `MissionOrchestrator.select` and MKM recommendation | retain; preserve authority order |
| admission | `mission_admission_runtime.py`, `wop_admission.py` | retain; document boundary |
| execution context | admission and execution runtimes | retain |
| lifecycle | WOP lifecycle manager and execution runtime | retain |
| history/recovery | hash-bound lifecycle/admission records | retain |
| events | EENS integration contract and evidence records | document boundary; no duplicate emitter |

The prior `zeus mission queue` surface exposed only eligible IDs. It now
projects entries, blockers, history, counts, and deterministic next mission
from the same Mission Knowledge Model. This is a read-only interface
extension, not a new authority store.
