# Zeus Codex Session Timing

This interface is an observability facility for direct Codex CLI use. It does
not create execution authority, own a managed provider, or advance any Zeus
mission lifecycle.

## Operator usage

Run a direct Codex CLI operation through the Zeus timing surface:

```text
scripts/zeus codex timed exec --sandbox workspace-write "PROMPT"
```

Every argument after `timed` is passed to the selected Codex executable in the
same order. The executable is `codex` by default; `ZEUS_CODEX_BIN` may select a
compatible executable for testing or an explicitly configured operator
installation. The current working directory and inherited environment,
stdin, stdout, stderr, and terminal characteristics are preserved. No shell,
detached process, PTY, Codex HOME override, or transport proxy is introduced.

The wrapper prints timing lines after the child exits without replacing child
output. The child result is preserved. If timing persistence fails, the
wrapper reports `CODEX_TIMING_LOG_FAILURE` on stderr and still returns the
child result. A signal-terminated child is recorded with its raw negative
return code and the wrapper terminates from the same signal.

When explicitly available, direct-session metadata can be supplied without
changing the Codex argument vector through
`ZEUS_CODEX_TIMING_MISSION_ID`, `ZEUS_CODEX_TIMING_EXECUTION_ID`,
`ZEUS_CODEX_TIMING_CODEX_SESSION_ID`, and
`ZEUS_CODEX_TIMING_LOG_SEQUENCE`.

Inspect the derived running average:

```text
scripts/zeus codex timing summary --json
```

`ZEUS_CODEX_TIMING_ROOT` is an explicit isolation/testing override. The
operator default is `/data/engineering/logs/codex-session-timed`.

## Persistent record model

The log root contains append-only session records and atomically derived
views:

```text
/data/engineering/logs/codex-session-timed/
  sessions/<record-id>.json
  summary.json
  latest.json
  .timing.lock
```

Each completed record has schema `zeus-codex-session-timing/1`, a UUID record
identity, UTC start/end timestamps, precise elapsed seconds, a formatted
duration, child exit code, signal classification when applicable, repository
and working-directory metadata, invocation mode, command surface, optional
mission/execution/Codex-session identities, direct/managed classification,
optional log sequence, and replay identity. Incomplete or malformed JSON is
not eligible for aggregation.

Duration formatting rounds to the nearest whole second using half-up rounding:
`MM:SS` below one hour and `HH:MM:SS` at one hour or more. The running average
is recalculated from all eligible canonical session records after each
successful finalization; it is never calculated from a prior rounded average.
`average_seconds` is retained to six decimal places, while
`average_formatted` uses the unrounded mathematical average and the same
half-up duration rule.

## Concurrency and replay

Writers take an advisory `flock` on `.timing.lock`. A record is atomically
promoted with a same-directory temporary file, `fsync`, and `os.replace`; the
summary and latest views use the same atomic write pattern. Each writer
rebuilds the summary while holding the lock, so concurrent shells cannot lose
records or publish a partial aggregate. A completed record ID is idempotent:
repeated finalization returns the existing record and does not increase
`sample_count`. A same-ID incomplete artifact is safely replaced by its
completed finalization and is never counted while incomplete.

## Zeus-managed integration seam

Direct timing is the only process-launching mode. The module also exposes a
passive record API for a future Zeus lifecycle owner to supply terminal event
timestamps and already-authoritative identities. That API writes only a
timing record and never discovers runtime state, reads a provider socket,
wraps a managed process, changes STDIO, starts a thread or turn, changes
identity, signals a process, or participates in reconciliation, supersession,
resume, checkpoint, recovery, approval, sandbox, or liveness decisions.

Activation of that seam is deferred until the Zeus lifecycle owner explicitly
publishes a supported timing hook. The timing layer remains subordinate to
Zeus-managed ownership and cannot become a second controller.
