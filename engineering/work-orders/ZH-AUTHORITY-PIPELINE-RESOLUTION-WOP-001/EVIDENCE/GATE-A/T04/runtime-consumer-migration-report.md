# T04 Runtime Consumer Migration Report

## Eligibility

The Progressive branches of `scripts/zeus` were eligible because they are
active consumers and duplicated canonical verification dispatch or routed
decisions through the temporary `progressive_oa` compatibility boundary.

| Consumer route | Before | After |
| --- | --- | --- |
| `verify OA-01`–`OA-05` | five direct gate-verifier calls | `ProgressiveGateService.verify()` |
| `approve OA-XX` | `progressive_oa.decide(..., ACCEPTED, ...)` | `ProgressiveGateService.approve()` |
| `decline OA-XX` | `progressive_oa.decide(..., REJECTED, ...)` | `ProgressiveGateService.decline()` |

The migration removes direct CLI ownership of verifier selection and removes
the compatibility hop for decisions. Unsupported gates retain the existing
`IMPLEMENTATION_REQUIRED` compatibility response.

Excluded consumers were left unchanged because the handoff explicitly assigns
PMCT, Agent Qualification, carry-forward, Mission Contract, ARS, EWI, and
legacy retirement to later transitions.

