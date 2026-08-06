# P5-G6 Controlled Active Execution Foundation

Mission: `MISSION-BETA-562F443E16C69401`

Entry baseline: `05167c58b5b95342734d4bf5c77f5e4c8eb77cb4`

## Bounded implementation

Zeus now owns the normal Codex session boundary through
`scripts/zeus codex`. The adapter binds a deterministic Codex session to the
verified execution-start record, provider identity, repository identity,
published baseline, and Operation Beta authority chain. Session state,
process identity, logs, artifacts, and append-only lifecycle events are
recorded under the authoritative Zeus runtime.

Start, resume, and stop require explicit operator approval. Status, logs,
artifacts, and verification are read-only. Direct `engctl codex` remains a
recovery compatibility path; it is not the normal execution interface.

The adapter is bounded at the first controlled mission-work boundary. It
does not publish, synchronize EOS, close the mission, qualify completion, or
authorize work outside the verified repository and execution package.

## Authority and provenance

Authority is resolved from the published Operation Beta authority chain. This
repository session has no WOP provenance marker; the session is not treated
as an authority source. Execution-start verification remains the input
authority for the adapter. Invocation provenance is not aliased as
execution-start provenance.

## Validation evidence

- Entry repository, platform, authority, mission, execution-start, registry,
  and EOS checks passed at `05167c58b5b95342734d4bf5c77f5e4c8eb77cb4`.
- Codex adapter focused tests cover deterministic identity, approval gating,
  read-only status, CLI projection, and execution-start authority binding.
- Python syntax and `git diff --check` passed.
- The first Zeus `codex exec` launch attempt was durably recorded, then failed
  before a Codex session handshake because it used the wrong startup primitive
  and the default Codex state runtime was not writable. Zeus preserved that
  exact session and retried through the app-server broker. The corrected retry
  returned `initialize` with `app_server_handshake=PASS`; the provider process
  and broker remain alive as the same deterministic Zeus session. No thread,
  turn, prompt, Codex model work, mission output, or repository mutation was
  produced.

  The verified runtime projection is `state=READY`, `process_alive=true`,
  `provider_process=RUNNING`, `mission_work_started=false`,
  `repository_work_started=false`, `replay=IDEMPOTENT`, and
  `next_authorized_action=CONTINUE_CONTROLLED_MISSION_WORK`. Authority is
  resolved from the published Operation Beta chain; this repository session
  has no WOP provenance marker and is not treated as an authority source.

## Operator boundary

The provider handshake is now established. The next operator-controlled
entry point, which is intentionally not executed in this handoff, is:

```text
scripts/zeus codex start MISSION-BETA-562F443E16C69401 --approve
```

That command would be the explicit boundary at which the operator authorizes
the first controlled mission-work transition. No thread, turn, prompt,
publication, commit, push, EOS synchronization, or mission work is part of
this handoff.

## P5-G6 provider-runtime handshake reconciliation

The initial `codex exec` launch was the wrong startup primitive for this
boundary: it enters the model execution path and does not provide an idle
application-server session. The installed Codex CLI exposes a newline-delimited
JSON-RPC app-server. Zeus now launches that app-server through the durable
`codex_app_server_broker`, sends only the protocol `initialize` request, and
records the provider PID, handshake response, and sanitized environment
diagnostics. No thread, turn, prompt, WOP, or mission instruction is sent.

The broker uses a writable per-session `CODEX_HOME` under the authoritative
Zeus runtime and symlinks the existing local auth/config files without copying
credentials. This isolates Codex state from the damaged default memories
database while preserving provider configuration. The prior failure was
confirmed by `codex doctor`: the default memories database could not be opened,
and the earlier `exec` attempt exited before its application-server handshake.

The runtime handshake correction is limited to startup. It does not change
authority, mission binding, repository binding, execution sequencing, or
mission-work authorization. Provider and repository work remain false until a
later operator-authorized controlled-work transition.

Terminal state: `AWAITING_OPERATOR_REVIEW`.

## Interactive Codex reconciliation

The real-terminal lifecycle defect was isolated to the custom interactive
controller: it duplicated the official client's terminal, input, rendering,
and app-server conversation responsibilities. The correction minimizes Zeus
to a context/lifecycle launcher and invokes the installed official client as
`codex --remote <Zeus endpoint>`. The official client owns keyboard input,
multiline editing, paste, resize, rendering, thread creation, turn creation,
streaming, and return to the next prompt. Zeus records the remote endpoint,
client lifecycle, provider reuse, bindings, approvals, and cleanup.

The normal operator-facing entry point is now `scripts/zeus codex shell`.
It selects `DIRECT_INTERACTIVE`: the shared native launcher inherits the
operator terminal and replaces itself with the ordinary Codex CLI. Explicit
remote mode is selected only with `--remote`; it resolves a controlled remote
endpoint and launches `codex --remote <endpoint>`. The provider is never
attached directly to a Zeus-owned PTY. The official client captures terminal
input, dimensions, rendering, and exact bracketed-paste behavior.
A mission-bound shell requires explicit `--approve` and consumes the same
published Operation Beta authority, repository, execution, provider, and
session bindings as managed mode. A non-mission shell is explicitly unbound
and does not imply a WOP or Mission Contract.

The interactive controller preserves the managed commands (`start`, `resume`,
`stop`, `status`, `logs`, and `artifacts`). It prevents duplicate live
interactive sessions, records `REMOTE_CLIENT_RESOLVED` without storing
terminal text, and keeps `mission_work_started` and `repository_work_started`
false when a
session is merely opened or used conversationally. Structured provider
request decisions are append-only and classified as
`ALREADY_AUTHORIZED`, `OPERATOR_DECISION_REQUIRED`, or `PROHIBITED`.
Terminal text is not treated as an authority protocol.

The bounded acceptance tests cover direct command construction, explicit remote
command construction, clean
stopped state, append-only decision capture, mission/repository work remaining
false, and deterministic session selection. The adapter suite covers explicit
controller routing,
read-only managed status, authority-bound identity, and startup diagnostics.
The broker control-socket reuse test is skipped only in this restricted API
sandbox because Unix-domain socket bind is prohibited; it is intended for the
operator host. A real
operator acceptance run was not initiated from the non-interactive API
session: doing so would require taking over the operator's terminal and
contacting Codex. The documented commands are ready for operator review:

```text
scripts/zeus codex shell
scripts/zeus codex shell MISSION-BETA-562F443E16C69401 --approve
scripts/zeus codex shell --remote --diagnose
scripts/zeus codex shell --remote
scripts/zeus codex status --session <SESSION_ID> --json
scripts/zeus codex logs --session <SESSION_ID>
scripts/zeus codex artifacts --session <SESSION_ID>
```

Validation evidence: Registry validation passed; integrated
`scripts/engctl validate homelab` passed; `scripts/zeus platform verify --json`
passed; syntax compilation and `git diff --check` passed. The published
authority chain remains the source of authority; no session-local WOP marker
was used.

`engctl codex` remains available only as a recovery/diagnostic fallback and
was not removed or wrapped through a second launch implementation. The
Zeus–Codex authority boundary remains explicit: published authority is the
source, and this repository session's absence of a WOP marker is not treated
as authorization.

The observed bundled-bubblewrap warning is recorded as
`SYSTEM_BUBBLEWRAP=PREFERRED` and `BUNDLED_BUBBLEWRAP=SUPPORTED`; no host
package change is required and no evidence links it to the terminal defect.

## Remote endpoint establishment reconciliation

The installed binary reports `codex-cli 0.146.1`; its help exposes
`codex --remote ws://host:port` and `codex app-server --listen ws://IP:PORT`.
The previous candidate incorrectly treated a raw broker control socket in
front of `codex app-server --stdio` as a remote endpoint. That process could
be alive while the official remote client could not perform its WebSocket
handshake. The corrective is explicit:

```text
MANAGED_STDIO.remote_capable=false
INTERACTIVE_REMOTE.remote_capable=true
INTERACTIVE_REMOTE.transport=WEBSOCKET
```

Zeus selects a free `127.0.0.1` port, starts the official listener form, and
requires a WebSocket/JSON-RPC `initialize` probe before publishing the
endpoint receipt or launching `codex --remote`. Receipts preserve provider
mode, endpoint URI, listener PID, socket/listener state, readiness result,
remote client PID/state, failure phase, and cleanup reason. Failed listener
transactions terminate only the listener they created; an existing stdio
provider is preserved and is not falsely reused.

The diagnostic command is `scripts/zeus codex shell --remote --diagnose`. It establishes
and probes the endpoint, reports capability/readiness fields, and stops before
opening the official client. Real endpoint and client acceptance remain
operator work and are not claimed by this API session.

### Corrective status: direct locator and remote lifecycle

The direct-launch failure was a deterministic locator defect: Zeus looked for
`scripts/eos/codex-direct-launch.sh` while the shared launcher is
`scripts/lib/eos/codex-direct-launch.sh`. The locator is now derived from the
verified repository root, and `engctl codex` resolves the same canonical
relative path. Missing, non-executable, and repository-escaping launchers are
structured as `DIRECT_LAUNCHER_MISSING`,
`DIRECT_LAUNCHER_NOT_EXECUTABLE`, and `DIRECT_LAUNCHER_PATH_ESCAPE`.

The remote failure was an endpoint receipt mismatch: the broker reported
`endpoint_uri`, while operational launch required `remote_endpoint`, and the
diagnostic state was not persisted as an owned endpoint transaction. The
shared transaction now establishes and verifies the loopback WebSocket/JSON-RPC
endpoint for both `--diagnose` and normal `--remote`, persists ownership and
transaction identity, and only then diverges into diagnostic cleanup or
official-client launch. Normal operational launch no longer requires a
pre-existing endpoint.

The short Unix control-socket root remains `/tmp/zeus-sockets`; generated
paths are length-checked and report `AF_UNIX_PATH_TOO_LONG` explicitly.

Automated corrective validation: 21 focused interactive tests passed, 3 were
skipped by existing test policy; Python and shell syntax validation plus
`git diff --check` passed. No operator TTY acceptance was performed here.

## Required operator review

## Runtime reconciliation boundary

### Post-publication corrective

The published controller initially replayed a pre-correction receipt and did
not expose listener inventory. The post-publication correction versions new
receipts, scans loopback Codex listeners, returns complete session/listener and
orphan details, derives multidimensional lifecycle state, requires verified
ownership for mutation, preserves unknown listeners, and supports explicit
`--dry-run` plus approval-gated reconciliation. Historical runtime records are
not rewritten by this handoff. The current sandbox read-only inventory observed
the two historical remote records but no live listener PIDs in its process
view; host-terminal acceptance remains required.

The Codex sandbox is prohibited from writing authoritative Zeus runtime state.
The reconciliation controller is repository code executed by Zeus; it accepts
an explicit runtime root, supports read-only inventory/dry-run and
operator-approved mutation, validates Linux process identity before signaling,
emits termination receipts, and replays approved receipts idempotently.
Focused tests use disposable `mktemp -d /tmp/p5g6-runtime-test.XXXXXX`
runtimes only. Host runtime reconciliation remains deferred to the operator's
Zeus command and no current Atreides listener was terminated.

```text
CODEX_SANDBOX_AUTHORITATIVE_RUNTIME_WRITE=DENIED_BY_DESIGN
DISPOSABLE_TEST_RUNTIME=USED
HOST_RUNTIME_RECONCILIATION=DEFERRED_TO_OPERATOR_CONTROLLED_ZEUS_COMMAND
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
PUBLICATION=NOT_PERFORMED
COMMIT=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
```

Operator review commands, using the controller-owned runtime selected by Zeus:

```bash
# Read-only inventory and dry-run disposition review.
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --dry-run --json

# Review listener/session dispositions, including process identity checks.
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --dry-run --json | jq '.matching_sessions, .live_listeners, .orphan_listeners'

# Explicitly approve controlled reconciliation and receipt-backed termination.
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --approve --json

# Re-run read-only inventory; verify listener shutdown and socket closure.
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --dry-run --json | jq '{sessions: .matching_sessions, listeners: .live_listeners, terminations: .reconciliation.termination_receipts, unreconciled_orphans: .unreconciled_orphans}'

# Attach or stop a retained detached session after reviewing its exact ID.
scripts/zeus codex attach --session <SESSION_ID>
scripts/zeus codex stop --session <SESSION_ID> --approve --json

# Confirm zero unreconciled orphans and idempotent replay.
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --dry-run --json | jq '.unreconciled_orphans'
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --approve --json | jq '{replayed: .replayed, unreconciled_orphans: .unreconciled_orphans}'
```

Post-publication verification completed with mission verification, execution
start verification, platform verification, registry validation, integrated
validation, EOS validation, and `git diff --check` all passing. `HEAD` and
`origin/main` remain `07d7294a071d1121a65807cf8e5b3d77d17820c9`; the local
corrective is intentionally uncommitted for operator review. No approved host
mutation was executed from the Codex sandbox, and no managed stdio provider
was targeted.

The ownership qualification corrective normalizes `/proc` start ticks with
boot identity, preserves legacy receipt fields without comparing epoch time to
ticks, resolves Codex home from authoritative nested receipts, and aggregates
broker/Node/native process trees into one endpoint termination unit. A unit is
executable only for `OWNERSHIP_VERIFIED` or
`OWNERSHIP_RECOVERED_VERIFIED`; partial, unknown, mismatched, or ambiguous
identity remains fail-closed. The reviewed plan therefore has stable unit and
action identifiers and records all member identities before mutation.

This corrective also exports the canonical `termination_units` collection at
top level. Diagnostic, historical orphan, and retained detached endpoints are
all represented; only the first two can carry required actions. The plan has a
stable SHA-256 `plan_digest` and approval requires the exact digest from the
read-only review. Missing legacy start ticks or transaction IDs are recovered
only from non-conflicting receipt evidence; they are not treated as immutable
mismatches. A complete live `/proc` identity reports `VERIFIED`, while an
unreadable identity reports `UNAVAILABLE`.

Automated verification stops here. From a real operator terminal, run:

```bash
scripts/zeus codex status --json
scripts/zeus codex shell --preflight
scripts/zeus codex shell
scripts/zeus codex shell MISSION-BETA-562F443E16C69401 --approve
```

The first command must emit one JSON document and return immediately. The
two shell checks must show readable complete-line output, no literal paste
markers, clean terminal restoration, and `MISSION_WORK_STARTED=NO` /
`REPOSITORY_WORK_STARTED=NO`. This handoff remains
`STATUS=AWAITING_OPERATOR_REVIEW`; no real-terminal acceptance was performed
from the non-interactive API session.

The final ownership qualification update adds a unit-level report with boot,
start-tick, transaction, command, Codex-home, endpoint, process-tree,
process-identity, and session-binding results, plus missing evidence,
recoverable evidence, immutable conflicts, and promotion reasons. Legacy
receipt omissions are promoted only when the live immutable identity and
receipt-backed ownership chain agree; unknown or conflicting listeners remain
preserved and non-executable. Remote status consumes the same canonical
multidimensional projection, preserving the retained detached session's
`DETACHED`/`EXITED`/`READY`/`ATTACH_OR_STOP` lifecycle.

The partial-reconciliation corrective establishes strict result semantics:
completed work plus safely preserved partial-ownership listeners is `PARTIAL`,
not `RECONCILIATION_NOT_APPLIED` or `FAIL`. The response records
`reconciliation_applied`, `reconciliation_fully_converged`, preserved-target
dispositions, separate orphan/cardinality counts, and the next action
`RECONCILE_REMAINING_ORPHAN_OWNERSHIP`. Completed receipts are consumed by
canonical inventory and status; replay is idempotent with zero new signals,
process exits, socket closures, or mutation receipts. Host reconciliation
remains deferred to the operator-controlled Zeus command.

The final terminal-semantics corrective distinguishes preserved targets from
failed reconciliation. A healthy read-only inventory with zero executable
actions and only partial-ownership `PRESERVE_TARGET` dispositions returns
`PASS` with `reconciliation_required=false`, while retaining
`reconciliation_fully_converged=false` under the strict convergence policy.
The next action is `REVIEW_PRESERVED_TARGETS`. Application history is exposed
as `reconciliation_already_applied`; mutation in the current invocation is
`reconciliation_applied_this_invocation`; and replay state is always explicit
(`IDEMPOTENT` or `NOT_REQUIRED`). No authoritative runtime mutation was
performed by Codex.

## Completed-plan replay projection corrective

The completed diagnostic plan is replayable only through its existing
authoritative successful receipt. Replay lookup now distinguishes the
requested historical digest from the fresh current plan digest, reports
`replay_result=IDEMPOTENT`, and projects
`reconciliation_already_applied=true` with zero new mutation counters. The
current preserved orphan dispositions and retained detached session determine
the replay next action. Missing or conflicting receipt matches fail closed;
the historical mutation receipt is not rewritten and no authoritative runtime
mutation is performed by Codex.
