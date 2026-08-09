# Root-Cause Analysis

The defect crossed four layers:

1. `runtime_liveness` converted absent broker/provider PIDs into
   `STALE_ORPHANED_RUNTIME`.
2. history reconciliation interpreted “no work occurred” as both safe wrapper
   replacement and required wrapper supersession.
3. Codex status promoted that conflated value to `SUPERSEDE_CODEX_SESSION`.
4. `resume` only relaunched the broker; it never read or resumed a native Codex
   persisted thread. The controlled-work path then used `thread/start`.

Consequently, ephemeral process death became evidence that the durable
conversation was unusable. Mission next retained
`BEGIN_CONTROLLED_MISSION_WORK`, hiding the prerequisite repair.

The root cause was a missing first-class persisted-thread axis. Process/session
terms were overloaded across Zeus execution, provider transport, and native
Codex conversation state. Remote listener/client state used the same collapsed
model.

The corrective makes history evidence answer only whether work occurred,
transport evidence answer only whether a connection is live, and native
persistence evidence answer whether a particular Codex thread can be read,
resumed, or forked.
