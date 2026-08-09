# Remote Compatibility Verification

Remote reconciliation now exposes transport liveness/replacement separately
from thread identity/persistence/resume eligibility. A stopped listener with a
persisted native thread resolves to
`RESTART_REMOTE_TRANSPORT_AND_RESUME_THREAD`; it does not set thread replacement
required. A live detached listener retains its existing `ATTACH_OR_STOP`
operator path.

The remote model continues to require Zeus endpoint ownership and never starts
an unmanaged Codex process. Local STDIO and remote websocket mechanics differ,
but both require persisted-thread validation, single authoritative ownership,
native resume, and no implicit new-thread fallback. Focused remote regression
coverage passes.
