# Runtime Integration Certification Report

| Integration | Certified behavior |
| --- | --- |
| EMP | Produces read-only planning projection and convergence-derived admission/WOP artifacts only after resolved authority. |
| EOS | Receives an idempotent, authoritative-to-derived synchronization plan; no synchronization was performed in this certification. |
| EENS | Receives a deterministic append-by-event-identity event contract; no event was appended in this certification. |
| Generated artifacts | Receipts and artifacts are derived and digest-bearing; source facts remain unchanged. |
| Qualification | Qualification envelope is `PASS` only for a resolved receipt, otherwise `NOT_READY`. |
| Reporting | Receipts, digests, source locators, and this evidence package preserve traceability. |

Each integration is represented in the convergence flow before dispatch. No
integration can convert an unresolved flow into authorization.
