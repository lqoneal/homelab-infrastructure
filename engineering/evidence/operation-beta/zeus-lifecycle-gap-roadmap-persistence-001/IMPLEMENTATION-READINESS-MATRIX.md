# Implementation Readiness Matrix

| Gap | Readiness | Required runtime/test/doc/schema work | Focused proof | Native acceptance |
|---|---|---|---|---|
| `GAP-001` | `READY_NOW` | Runtime resolver; discovery integration tests; no schema change expected | P2/P3/P4 discovery, zero/multiple/conflict/replay tests | `zeus mission show/state/snapshot/verify` resolves the target from canonical receipts |
| `GAP-002` | `BLOCKED_BY_GAP-001; BLOCKED_BY_GAP-006` | Unified transition resolver and adapters; integration harness | Receipt chain and duplicate-transition rejection | Mission state and next action come from one resolver |
| `GAP-003` | `BLOCKED_BY_GAP-002; BLOCKED_BY_GAP-009; BLOCKED_BY_GAP-011` | Publication/EOS receipt bridge; exact candidate verifier | Divergence and replay tests | Publication/sync/mission snapshot agree |
| `GAP-004` | `BLOCKED_BY_GAP-001; BLOCKED_BY_GAP-002` | Authority receipt adapter; compatibility tests | Missing/conflicting/stale receipt fail closed | Authority and provider/session readiness agree |
| `GAP-005` | `BLOCKED_BY_GAP-002; BLOCKED_BY_GAP-003; BLOCKED_BY_GAP-009` | One terminal predicate; legacy read-only adapter | Closeout replay and false-terminal negatives | `zeus mission next` returns `NONE` only at `CLOSED` |
| `GAP-006` | `READY_NOW` | Canonical next-action resolver; migration tests | Conflicting projection and terminal-state negatives | `zeus mission next` is authoritative and deterministic |
| `GAP-007` | `BLOCKED_BY_GAP-002` | Read-only aggregate view; command tests | Provider/session/process lookup ambiguity tests | Mission view exposes provider/session/monitor/evidence together |
| `GAP-008` | `BLOCKED_BY_GAP-002; BLOCKED_BY_GAP-004` | Checkpoint/recovery harness; no schema change until contract settles | Process/provider/session/EOS/repo interruption tests | Native state shows checkpoint, blocker, and resume action |
| `GAP-009` | `BLOCKED_BY_GAP-002; BLOCKED_BY_GAP-008` | Evidence manifest binding and qualification adapter | Missing/stale/forged evidence and requirement-level replay | Native evidence/qualification view binds to mission work |
| `GAP-010` | `DEFERRED_BY_DEPENDENCY` | Legacy fallback classification; focused compatibility test | New mission cannot resolve historical identity | Native commands label fallback legacy-only |
| `GAP-011` | `READY_NOW` | Candidate isolation procedure/verifier; no runtime lifecycle change | Dirty unrelated work and exact-hunk negatives | Publication readiness exposes exact candidate blockers |
| `GAP-012` | `READY_NOW` | Validator/reporting fingerprint handling; regression tests | Candidate drift is explicit and baseline remains immutable | Sync validation distinguishes candidate drift from published parity |

Every row requires integration proof, receipt/evidence locator, deterministic
replay proof, and fail-closed negative proof before it can advance beyond
`OPEN`.
