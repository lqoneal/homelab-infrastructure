# Zeus Codex Session Timing — Focused Evidence

## Repository provenance

- Repository: `/data/engineering/repositories/homelab`
- Branch: `main`
- Verification baseline HEAD: `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1`
- Local `HEAD...origin/main`: `0 0`
- Existing worktree changes: preserved; the active lifecycle corrective was
  not modified, advanced, reconciled, resumed, launched, attached to, or
  otherwise interacted with.

## Architecture decision

Timing observation is a separate `TimingStore` concern. Direct `codex timed`
owns only a child wait and timing observation. Persistent records are outside
the Zeus runtime at `/data/engineering/logs/codex-session-timed`; summary and
latest are derived views. Future managed observation is a timestamp/event API
that accepts identities from the lifecycle owner and performs no process,
transport, runtime, or lifecycle operation.

## Files changed

- `scripts/lib/emp/codex_session_timing.py` — record API, direct wrapper,
  atomic persistence, locking, aggregate, passive managed seam.
- `scripts/zeus` — isolated `codex timed` and `codex timing summary` dispatch
  plus help namespace choices; existing managed branches remain unchanged.
- `scripts/tests/test-zeus-codex-session-timing.py` — focused unit, CLI,
  concurrency, signal, and noninterference tests.
- `engineering/docs/cli/ZEUS-CODEX-TIMING.md` — operator and architecture
  contract.

## CLI examples

```text
scripts/zeus codex timed exec --sandbox workspace-write "PROMPT"
scripts/zeus codex timing summary --json
```

Exact harmless operator-review smoke command (Codex help only; not a mission
prompt):

```text
scripts/zeus codex timed exec --help
```

## Sample timing record

```json
{
  "schema_version": "zeus-codex-session-timing/1",
  "record_status": "COMPLETED",
  "record_id": "2d7f2c9e-6f71-4a53-b8a1-4a8fb8e2bd4d",
  "start_timestamp_utc": "2026-08-09T10:00:00.000Z",
  "end_timestamp_utc": "2026-08-09T10:01:35.000Z",
  "elapsed_seconds": 95,
  "elapsed_formatted": "01:35",
  "child_exit_code": 0,
  "termination_classification": null,
  "repository_root": "/data/engineering/repositories/homelab",
  "working_directory": "/data/engineering/repositories/homelab",
  "invocation_mode": "DIRECT_CODEX_CLI",
  "command_surface": ["codex", "exec", "--sandbox", "workspace-write", "PROMPT"],
  "mission_id": null,
  "execution_id": null,
  "codex_session_id": null,
  "zeus_managed": false,
  "execution_classification": "DIRECT",
  "log_sequence": null,
  "replay_identity": "2d7f2c9e-6f71-4a53-b8a1-4a8fb8e2bd4d"
}
```

## Sample aggregate summary

```json
{
  "schema_version": "zeus-codex-session-timing/1",
  "summary_type": "RUNNING_AVERAGE",
  "sample_count": 8,
  "average_seconds": 742.5,
  "average_formatted": "12:23"
}
```

## Tests and results

Passed:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q scripts/tests/test-zeus-codex-session-timing.py` — 10 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/tests/test-engineering-cli-standard.py -v` — 2 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_controlled_documents.py` — 2,897 passed, 0 failed.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/zeus platform verify --json` — `result=PASS`.
- `git diff --check` and new-file whitespace check — clean.
- `scripts/zeus codex timed --help` and `scripts/zeus codex timing summary --help` — passed.

The repository validator's full scan covers the affected controlled-document
set. The new CLI guide is an existing unprofiled CLI-guide information class,
so forcing it through `--semantic-path` correctly reports that no semantic
profile resolves; no validator or unrelated profile was changed.

The focused CLI tests use a temporary fake Codex executable and isolated
timing root. No active lifecycle mission is used as a test child.

## Managed-session noninterference verification

The timing dispatch occurs before Zeus operator/runtime stores are
constructed. Direct mode calls only `subprocess.Popen` with inherited streams
and does not import or call a managed adapter operation. The passive managed
API accepts supplied timestamps and identity values only. Tests assert that a
timed direct invocation does not create a Zeus runtime identity or mutate a
managed-runtime path.

## Deferred work

Do not activate managed timing by wrapping a provider or changing a lifecycle
controller. A future Zeus-owned lifecycle event may call the passive API after
the lifecycle owner has terminal timestamps and replay identity. That hook,
its event schema, and its acceptance tests remain deferred.

## Stop boundary

This task stops at `OPERATOR_REVIEW`. It does not run a lifecycle mission or
`BEGIN_CONTROLLED_MISSION_WORK`.
