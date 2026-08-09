# Recovery State Machine

| Transport | Persisted thread | Classification | Canonical action |
|---|---|---|---|
| Live | Valid | `ACTIVE_OR_ATTACHABLE` | `ATTACH_OR_CONTINUE` |
| Stopped | Valid/resumable | `TRANSPORT_STOPPED_THREAD_RESUMABLE` | `RESTART_CODEX_TRANSPORT_AND_RESUME_THREAD` |
| Any | Valid, explicit fork required | `THREAD_FORK_REQUIRED` | native `thread/fork` after ownership checks |
| Any | Missing, corrupt, mismatched, ambiguous, or concurrently owned | `THREAD_RECOVERY_BLOCKED` | `RECONCILE_CODEX_THREAD_RECOVERY` |
| Stopped | Never created | `TRANSPORT_STOPPED_THREAD_NOT_CREATED` | `RESTART_CODEX_TRANSPORT` only |

`scripts/zeus codex resume <MISSION_ID> --approve --json` is the canonical
managed recovery mutation. It performs preflight before launch, starts at most
one replacement transport, calls native `thread/read` then `thread/resume`, and
verifies the returned identity. On any post-launch failure it retires the
replacement transport and commits no recovered owner. It never calls
`thread/start` as fallback.

`--fork-thread` is explicit and calls native `thread/fork`; fork lineage must
validate. Wrapper supersession is limited to historical wrappers that never
acquired native thread identity. New conversation authority is otherwise
absent and fails closed.
