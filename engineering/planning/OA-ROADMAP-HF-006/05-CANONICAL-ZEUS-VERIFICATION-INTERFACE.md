# Canonical Zeus Verification Interface Specification

Status: `PROPOSED LONG-TERM PUBLIC INTERFACE — NON-AUTHORITATIVE`

| Interface family | Stable operator intent | Transitional implementation examples |
|---|---|---|
| `zeus gate` | show objective, status, receipt, evidence, and predecessor/successor state | per-gate files and `zeus gate show` |
| `zeus mission` | inspect selection, contract, WOP, attempt, and closeout | `scripts/engctl mission contract` |
| `zeus lifecycle` | show state, legal transitions, reachability, recovery route | runtime JSON and HF-005 matrices |
| `zeus verify` | run/inspect functional and lifecycle verification | gate shell tests and per-gate guides |
| `zeus capabilities` | show declared and qualified capability evolution | capability matrices/reports |
| `zeus authority` | resolve Authority Record, scope, freshness, revocation | authority owner/resolution tools |
| `zeus state` | inspect owner-bound operational and projection state | EOS/EENS/runtime views |
| `zeus health` | report freshness, drift, synchronization, and blockers | `scripts/engctl` health/validate commands |

Each procedure must state the intended canonical command, even while a
transitional command is required. A stable command returns machine-readable
identity, source revision, classification, owner, freshness, verification
result, predecessor/successor availability, and reason codes. It must not
alter authority or accept a gate merely by inspection.

Backward compatibility means the canonical command can call an existing
adapter while preserving the documented result contract; it does not preserve
implementation-specific semantics as the public interface.
