# Provider-Session Contract

Canonical command: scripts/zeus provider-session create <MISSION_ID> --json.

It consumes the current dispatch set and creates exactly five
Mission/WOP/dispatch/provider/repository-bound provider-session artifacts. It
stops before provider invocation and execution.

PROVIDER_SESSION_ID=PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1
SESSION_STATE=READY_FOR_PROVIDER_INVOCATION
PROVIDER_SESSION_REPLAY=IDEMPOTENT
DUPLICATE_PROVIDER_SESSION=NO
HISTORICAL_SESSION_REUSED=NO
PROVIDER_INVOKED=NO
EXECUTION_STARTED=NO

The canonical lifecycle state remains receipt-backed; subordinate session state
does not manufacture execution progress.
