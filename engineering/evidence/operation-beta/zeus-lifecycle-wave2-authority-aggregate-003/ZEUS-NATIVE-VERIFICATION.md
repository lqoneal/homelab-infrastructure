# Zeus-Native Verification

The supported command `zeus mission aggregate <MISSION_ID> --json` was run
against the authoritative target runtime. It independently exposed mission
identity, WOP identity, authority, lifecycle state, blockers, next action, and
the provider/session/process/monitor/evidence aggregate. All values agreed
with the canonical P2 resolver.

The command was repeated. Output was deterministic and runtime file digests
were unchanged. No admission, dispatch, provider invocation, session
creation, or execution command was run.
