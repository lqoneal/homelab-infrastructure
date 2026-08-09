# Codex Native Lifecycle Verification

Installed implementation: `codex-cli 0.147.0`, package `@openai/codex`
`0.147.0`.

The installed app-server generated schema was inspected from a temporary
directory. It defines `ThreadReadParams`, `ThreadResumeParams`, and
`ThreadForkParams`, each keyed by required `threadId` where applicable.
`thread/resume` returns a `Thread` whose `id` is the resumed persisted identity.
`thread/fork` returns a new `id` and native lineage through `forkedFromId`; the
thread object also exposes root `sessionId`, `path`, `cwd`, and status.

The installed CLI exposes `codex resume SESSION_ID` and `codex fork SESSION_ID`.
Official contracts independently describe application-server initialization as
a transport concern and `thread/start`, `thread/read`, `thread/resume`, and
`thread/fork` as thread operations. See the official
[Codex app-server documentation](https://developers.openai.com/codex/app-server)
and [Codex CLI reference](https://developers.openai.com/codex/cli/reference).

Zeus `CODEX-SESSION-*` is a deterministic Zeus wrapper ID, not the native Codex
thread ID. The legacy provider log established native thread
`019fe4e4-26c2-7462-a4b6-197f7183dae0`; the implementation now persists that
identity separately after native responses.
