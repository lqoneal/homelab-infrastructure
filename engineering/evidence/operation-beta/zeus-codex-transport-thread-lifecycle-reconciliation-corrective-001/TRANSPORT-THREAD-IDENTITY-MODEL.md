# Transport / Thread Identity Model

## Zeus execution identity

Mission, WOP, execution, execution-session, provider, provider-session,
provider-invocation, repository, and `CODEX-SESSION-*` wrapper identities are
durable Zeus bindings. Mutable publication/authority digests are revalidated
but do not change those identities.

## Codex transport identity

Broker PID, app-server/provider PID, control socket, STDIO channel, websocket
listener, and remote endpoint are ephemeral. They can be replaced only after
ownership and authority checks. Transport replacement does not imply thread
replacement and does not start work.

## Codex persisted-thread identity

`native_thread_id`, native root `sessionId`, rollout path, `cwd`, `CODEX_HOME`,
history mode, status, and fork lineage describe durable Codex state. Zeus
validates the rollout under the bound `CODEX_HOME`, checks readability and
identity content, consults the native SQLite thread index read-only, and then
asks the installed app-server to `thread/read` and `thread/resume`.

The Zeus wrapper remains stable across transport replacement. Native resume
must preserve `native_thread_id`. Native fork creates a new native thread ID
but preserves the parent in `forkedFromId`; it does not create a new Zeus
execution lifecycle.
