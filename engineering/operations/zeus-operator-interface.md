# Zeus Operator Interface

## Global launcher

The repository-controlled launcher manager installs a per-user symbolic link to
the authoritative executable. It never installs into a privileged path and
never replaces an unrelated entry.

```text
scripts/install-zeus-launcher install
scripts/install-zeus-launcher verify
command -v zeus
zeus --help
```

`~/.local/bin` must already be present in `PATH`. Repeated installation accepts
an exact existing link without rewriting it. A regular file, broken link, link
to another target, or other conflicting entry fails closed.

Rollback is:

```text
scripts/install-zeus-launcher remove
```

Removal is idempotent and removes only the exact link owned by this repository.
It refuses to remove a conflict.

## First-100-invocation orientation

The operator-interface record is separate from engineering orchestration:

`<repository>/.zeus/runtime/operator-interface-state.json`

Schema version 1 contains exactly `schema_version`, `invocation_count`, and
`orientation_limit`. The limit is 100. The store uses an exclusive file lock,
atomic replacement, deterministic JSON, mode `0600`, a mode-`0700` runtime
directory, strict field/type/version validation, and symbolic-link rejection.
It is intentionally separate because the orchestration schema is strict and
operator education is neither mission state nor an authority source.

A qualifying invocation is any normal invocation against the repository-
authoritative runtime, including bare invocation, `--help`, `intro`, `status`,
valid commands, invalid commands, and argument parse failures. Counting occurs
once before argument parsing or execution. Invocation 1 through invocation 100
display orientation; invocation 101 does not. Manual `zeus intro` is a genuine
invocation and therefore counts, but remains available after the limit.

Explicit engineering state overrides (`--state` or `ZEUS_STATE`) do not count
and do not initialize or modify operator-interface state. Tests use
`ZEUS_TESTING` plus `ZEUS_OPERATOR_STATE` to isolate their state; these are
engineering test controls, not supported alternate operational locations.
Normal automation counts because it is indistinguishable from a genuine
operator request at the CLI boundary. Use `ZEUS_NO_INTRO=1` to suppress text
for one invocation; suppression still increments the count and never resets it.

Orientation is emitted to `stderr` before help, parsing, or command execution.
Machine-readable command output remains exclusively on `stdout`, so
`zeus status | jq .` remains valid while orientation is active.

Review and inspect the interface with:

```text
zeus intro
zeus intro --status
ZEUS_NO_INTRO=1 zeus status
```

Bare `zeus` prints concise help and exits successfully without performing work.
Unsupported natural language does not become unrestricted engineering
instruction.

## Corruption recovery

Read, validation, lock, or write failure stops the invocation with exit 78.
Zeus never silently resets corrupt or incompatible state. Preserve the failed
file, investigate it, and restore a known-good whole-file backup while Zeus is
idle. If no trustworthy backup exists, move the corrupt record aside manually
under operator control, invoke Zeus to initialize a new empty interface record,
and retain the old record as incident evidence. This procedure affects only
orientation history; it does not alter orchestration state or authority.
