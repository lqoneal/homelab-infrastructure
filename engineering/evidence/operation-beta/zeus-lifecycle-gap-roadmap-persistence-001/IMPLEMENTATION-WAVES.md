# Implementation Waves

| Wave | Scope | Gap IDs | Entry condition | Exit proof |
|---:|---|---|---|---|
| 1 | Canonical discovery, next action, and lifecycle ownership | `GAP-001`, `GAP-006`, then `GAP-002` | Existing P2 receipt identity; first unit starts with 001/006 | One resolver exposes identity, state, blockers, and next action; transition tests are receipt-backed |
| 2 | Dispatch, provider, session, execution start | `GAP-004`, `GAP-007` | Wave 1 qualified | Real identity-bound dispatch/session/start receipts and native aggregate view |
| 3 | Monitoring, interruption, checkpoint, recovery | `GAP-008` | Waves 1–2 qualified | Process/provider/session failure and deterministic resume proof |
| 4 | Evidence and independent qualification | `GAP-009` | Mission work and recovery are authoritative | Requirement-level evidence manifest and independent qualification proof |
| 5 | Publication and repository/EOS synchronization | `GAP-011`, `GAP-012`, `GAP-003` | Evidence qualification and exact candidate isolation | Mission-bound publication/sync receipts and fail-closed divergence |
| 6 | Canonical closeout | `GAP-005` | Publication, synchronization, evidence, and execution convergence | One terminal predicate, immutable closeout receipt, no next action |
| 7 | Native lifecycle verification | `GAP-007` acceptance expansion and all native surfaces | Underlying transitions qualified | Zeus commands independently expose every lifecycle stage |
| 8 | Sacrificial end-to-end mission | All `GAP-001..012` | Waves 1–7 qualified | Real filesystem/Git/EOS/provider mission reaches `CLOSED` |

The original investigation roadmap's order is preserved. Wave 1 is refined
into a smaller first mission so the broad `GAP-002` transition convergence is
not implemented without its resolution prerequisites.
