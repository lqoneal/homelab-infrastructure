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

## P5-G6 session supersession corrective — 2026-08-07

The stale session-supersession mechanism is implemented but has not been
applied to the authoritative host runtime from this sandbox. The operation is
explicitly operator-approved and fail-closed: it requires the accepted
read-only reconciliation disposition `EVENTS_NON_AUTHORITATIVE`,
`MISSION_WORK_ACTUALLY_OCCURRED=NO`, `REPOSITORY_WORK_ACTUALLY_OCCURRED=NO`,
and `SESSION_REPLACEMENT_SAFE=YES`; it rejects active provider/session
processes, prior actual work, ambiguous history, and identity divergence.

The predecessor remains historical and its event directory is untouched. The
replacement is deterministic from the predecessor, mission, execution,
provider, and reason, records `supersedes_session` and
`supersession_reason`, carries the canonical execution package binding, and
is created at most once. Replaying resolves the same replacement without a
second session. Current-session resolution used by managed start, execution
start verification, and P5-G6 monitoring follows the replacement while the
immutable `EXECUTION_SESSION_ID` remains unchanged.

```text
MISSION_ID=MISSION-BETA-562F443E16C69401
WOP_ID=WOP-BETA-562F443E16C69401
EXECUTION_ID=EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e
OLD_SESSION_ID=EXECUTION-SESSION-0d35cea3-1232-58f7-b202-92d0bfc256a3
PROVIDER_ID=zeus-local-loneal-01
OLD_SESSION_DISPOSITION=SUPERSEDED
OLD_SESSION_HISTORY_PRESERVED=YES
NEW_SESSION_ID=DETERMINISTIC_CODEX_SESSION_REPLACEMENT
NEW_SESSION_CREATED_ONCE=YES
MISSION_ID_UNCHANGED=YES
WOP_ID_UNCHANGED=YES
EXECUTION_ID_UNCHANGED=YES
PROVIDER_ID_UNCHANGED=YES
SESSION_BINDING=PASS
SESSION_HISTORY_RECONCILED=PASS
CANONICAL_PACKAGE_BINDING=PASS
DUPLICATE_SESSION=NO
DUPLICATE_PROVIDER_RUNTIME=NO
EXECUTION_STATE=READY_FOR_CONTROLLED_EXECUTION
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
EXECUTION_LIVENESS=NOT_ACTIVE
NEXT_AUTHORIZED_ACTION=BEGIN_CONTROLLED_MISSION_WORK
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
HOST_ACCEPTANCE_REQUIRED=YES
```

The disposable corrective suite passed five tests: stale reconciled session
supersession, replay idempotence, active-session protection, prior-work and
ambiguous-history protection, identity mismatch protection, old-event
preservation, canonical package binding, and disposable begin-path
convergence. Existing adapter and monitoring suites passed (23 and 6 tests;
one broker test is sandbox-skipped because Unix-domain socket binding is
prohibited). Host-runtime provider-session tamper validation is
environment-limited because its configured runtime is read-only; the
authoritative host command was not invoked.

### Unresolved criteria and automation coverage

Unresolved criteria: authoritative host acceptance of the exact old-session
relationship remains outstanding because the sandbox cannot safely access or
mutate that host runtime. Automation coverage: the disposable supersession
suite covers positive, replay, duplicate, active, prior-work, ambiguous
history, binding, preservation, monitoring-resolution, execution-start
resolution, and begin-path convergence cases; host acceptance remains manual.

No mission, repository, authority, roadmap, EOS, commit, push, publication,
or true-active P5-G6 demonstration was performed. P5-G7 and P5-G8 remain
unimplemented.

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

## P5-G6 execution-monitoring foundation corrective

The canonical P5 capability reconciliation identified the remaining gap as
the absence of a Zeus-native execution-monitoring projection and verifier.
This corrective adds the read-only `execution_monitoring` controller and the
following interfaces:

```text
scripts/zeus execution status <EXECUTION_ID> --json
scripts/zeus execution verify <EXECUTION_ID> --json
```

The projection is source-bound to the canonical execution-start transaction,
the applicable roadmap digest, and optional execution-scoped EENS events. It
exposes mission/WOP/execution/provider/session identity, execution state,
provider and execution liveness, current work position, blockers, approvals,
progress, phase/gate orientation, source records/digests, next authorized
action, and replay state. It does not infer active execution from provider
process existence and does not mutate runtime state.

The verifier independently checks mission, WOP, execution, session, and
provider bindings; execution state; liveness vocabulary; current position;
blocker/approval projection; progress totals; source provenance; and
idempotence. Contradictory monitoring state fails closed as
`EXECUTION_STATE_CONFLICT` with `RECONCILE_EXECUTION_STATE`.

Current authoritative qualification remains bounded by the execution-start
adapter: the host runtime is `READY_FOR_CONTROLLED_EXECUTION`, with
`execution_monitoring_active=false`, mission work false, and repository work
false. Therefore this evidence establishes implementation and read-only
verification readiness; operator host acceptance is still required to prove
the active-execution liveness/progress path. P5-G7 pause/resume and P5-G8
failure recovery remain separate future gates.

## Active-execution acceptance mission disposition

The active acceptance preconditions were reverified through Zeus for
`MISSION-BETA-562F443E16C69401`,
`WOP-BETA-562F443E16C69401`, and
`EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e`. Mission, authority,
repository baseline, provider, session, and execution-start bindings passed;
the execution remained `READY_FOR_CONTROLLED_EXECUTION` with
`NEXT_AUTHORIZED_ACTION=BEGIN_CONTROLLED_MISSION_WORK`.

The bound execution-start adapter is explicitly a qualification/idle adapter.
Its canonical contract creates no command that crosses this specific
`EXECUTION-START-*` record into active mission work. The available
`execute-mission start` path resolves or creates a separate legacy
`MISSION-EXECUTION-*` transaction and is not an authorized substitute for the
bound execution. It was not invoked. No provider was started, no mission work
was begun, and no repository work occurred.

Accordingly:

```text
TRUE_ACTIVE_EXECUTION_DEMONSTRATED=NO
ACTIVE_ACCEPTANCE=BLOCKED
BLOCKER=BOUND_EXECUTION_ADAPTER_HAS_NO_AUTHORIZED_ACTIVE_WORK_TRANSITION
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
NEXT_AUTHORIZED_ACTION=IMPLEMENT_OR_AUTHORIZE_BOUND_ACTIVE_EXECUTION_TRANSITION
```

The existing qualification/evidence framework (`PROC-0006` with the
applicable `SPEC-0001` criteria) did not explicitly state the true-active
condition rule. Draft candidate revision `PROC-0006@1.6` adds that narrow rule:
runtime-dependent capabilities require active-condition demonstration and
authoritative verification before `FULLY_SATISFIED`; it creates no execution
or approval authority and remains pending the normal controlled-document
process. The invalid state `IMPLEMENTATION=PASS`, `INACTIVE_RUNTIME=PASS`,
`ACTIVE_DEMONSTRATION=NOT_PERFORMED`, `FULLY_SATISFIED=YES` is therefore
rejected. The corresponding active demonstration remains unavailable in this
execution.

Focused tests: `test-zeus-p5-g6-execution-monitoring.py` (6 passed), Codex
adapter (8 passed, 1 skipped), Codex interactive (21 passed, 3 skipped), and
reconciliation (22 passed). No roadmap, authority, mission, WOP, registry,
EOS, or runtime mutation was performed.

## Bound active-execution transition corrective

Lifecycle inspection confirmed that `scripts/zeus execute-mission start` uses
the legacy `MISSION-EXECUTION-*` store and is not the canonical consumer of
this mission's `EXECUTION-START-*` record. It was not invoked. The bounded
corrective adds the Zeus operation:

```text
scripts/zeus execution-start begin MISSION-BETA-562F443E16C69401 --approve --json
```

The operation verifies the existing mission, WOP, invocation, provider,
session, execution-start state, and Operation Beta authority chain; reuses the
existing provider/session identity; requests one controlled provider thread
and turn through the bound broker; and then records an identity-preserving
`BOUND_ACTIVE_EXECUTION` transaction plus the P5-G6 monitoring projection.
The immutable P5-G5 execution-start artifacts are not rewritten. A repeated
begin against the same active transaction returns `REPLAY=IDEMPOTENT` and does
not create another execution, session, provider process, or active record.
Startup or provider acknowledgement failure occurs before active projection
commit and remains fail-closed.

Disposable transition tests cover valid transition, provider mismatch,
startup rejection without active-state commit, identity continuity, and
replay. Host active execution was not invoked during this corrective. The
operator must run the command only after reviewing the current authority and
the bounded payload; P5-G7 pause/resume and P5-G8 recovery remain out of
scope.

The draft qualification contract is now `PROC-0006@1.6` (front-matter draft,
approval pending). Its evidence rule explicitly distinguishes static from
operational criteria, requires true-active demonstration plus authoritative
verification for operational full satisfaction, rejects
`ACTIVE_DEMONSTRATION=NOT_PERFORMED` with `FULLY_SATISFIED=YES`, and preserves
historical qualification conclusions without rewriting them. No SPEC-0001
change was required.

```text
ACTIVE_TRANSITION_IMPLEMENTATION=PASS
EXECUTION_IDENTITY_CONTINUITY=PASS
SESSION_CONTINUITY=PASS
PROVIDER_CONTINUITY=PASS
TRANSACTIONAL_START=PASS
STARTUP_FAILURE_FAIL_CLOSED=PASS
REPLAY=IDEMPOTENT
P5_G6_MONITORING_INTEGRATION=PASS
TRUE_ACTIVE_HOST_DEMONSTRATION=DEFERRED_TO_OPERATOR_CONTROLLED_ZEUS_COMMAND
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_BOUND_ACTIVE_TRANSITION
```

Focused tests now include 13 Codex-adapter tests (one skipped), six
monitoring tests, 21 interactive tests (three skipped), and 22 reconciliation
tests. Controlled-document validation, registry, mission, execution-start,
platform, integrated Homelab, EOS, repository-EOS, Python compilation, and
`git diff --check` are required before host acceptance. No host runtime,
roadmap, authority, mission, WOP, registry, or EOS mutation was performed.

## Active-transition WOP-binding consumption corrective

The first operator-controlled active-transition attempt is preserved as
authoritative acceptance history:

```text
ACTIVE_TRANSITION_ATTEMPT=1
RESULT=FAIL
FAILURE_PHASE=PRE_ACTIVE_BINDING_VALIDATION
BLOCKER=WOP_BINDING_MISSING
ACTIVE_EXECUTION_STARTED=NO
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
```

The preserved outputs are `/tmp/p5g6-active-demo-20260807T085424Z/04-begin.json`
and its corresponding `04-begin.stderr`. The failed attempt produced no
applied active-transition receipt or active execution projection.

The source-path comparison identified the defect: the immutable
`execution-start-*` artifact chain stored the canonical top-level `wop_id`,
and `execution_monitoring` read that transaction directly, but
`execution_start._verify_set()` neither compared `wop_id` across the artifact
chain nor returned it in the verification projection. The bound begin path
correctly consumed `execution_start.verify()` and therefore received an
incomplete projection, despite monitoring displaying the valid transaction
binding.

The corrective adds `_canonical_wop_binding()` to the shared execution-start
verification path. It requires every execution-start artifact to contain the
same WOP identity, returns that identity from `execution_start.verify()`, and
fails closed with `WOP_BINDING_MISSING` or `WOP_BINDING_MISMATCH` for absent or
divergent artifacts. The begin path now consumes the same verified value as
execution-start verification and monitoring; no runtime receipt or authority
record was edited.

Verifier failures are propagated with their specific canonical blocker, so a
genuinely missing or divergent WOP remains `WOP_BINDING_MISSING` or
`WOP_BINDING_MISMATCH` at the begin boundary rather than being hidden behind a
generic execution-start failure.

Regression coverage proves:

```text
VERIFY_WOP_BINDING=PASS
MONITORING_WOP_BINDING=PASS
BEGIN_WOP_BINDING=PASS
ALL_THREE_RESOLVE_SAME_WOP=YES
BEGIN_WITH_MISSING_WOP=FAIL_CLOSED
BEGIN_WITH_MISMATCHED_WOP=FAIL_CLOSED
AMBIGUOUS_ARTIFACT_WOP=FAIL_CLOSED
FAILED_PRECONDITION_THEN_VALID_BEGIN=PASS
FAILED_ATTEMPT_NOT_APPLIED_REPLAY=PASS
```

The current host remains at `READY_FOR_CONTROLLED_EXECUTION`; the corrected
transition has not been retried. P5-G6 therefore remains:

```text
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
HOST_ACCEPTANCE_REQUIRED=YES
NEXT_AUTHORIZED_ACTION=OPERATOR_RETRY_TRUE_ACTIVE_DEMONSTRATION
```

## Authoritative stale Codex-session supersession attempt

The bounded supersession handoff independently verified the canonical
mission/WOP/execution/session binding and initially observed the stale Codex
managed session as stopped, with execution still ready and mission/repository
work unstarted. The first sandboxed mutation attempt did not reach the
runtime store because that store was read-only in the sandbox. An explicitly
authorized escalated retry then reached the canonical supersession path but
failed closed with `ACTIVE_SESSION_PROTECTION`:

```text
AUTHORITATIVE_SUPERSESSION_RESULT=FAIL
SUPERSESSION_TARGET_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
SUPERSESSION_TARGET_TYPE=CODEX_MANAGED_SESSION
SUPERSESSION_APPLIED=NO
RUNTIME_TERMINATION_REQUIRED=NO
ACTIVE_EXECUTION_PERFORMED=NO
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
```

The supersession implementation observed a live provider/session runtime at
the mutation boundary and correctly refused to supersede it. No process was
terminated and no replacement session was created by this handoff. A
subsequent read-only Zeus projection again reported the original session as
`STALE_ORPHANED_RUNTIME` with provider `STOPPED`, execution
`NOT_ACTIVE`, and next action `BEGIN_CONTROLLED_MISSION_WORK`; this
observation does not override the failed-closed mutation boundary and no
retry was attempted.

The previous runtime-liveness reconciliation, session-identity reconciliation,
and all three failed active-demonstration attempts remain historical. P5-G6
therefore remains partially satisfied. The next action requires a fresh
operator-controlled preflight that resolves the transient liveness discrepancy
before any supersession retry; active execution remains prohibited in this
handoff.

```text
SUPERSESSION_REPLAY=NOT_RUN_AFTER_FAIL_CLOSED
DUPLICATE_REPLACEMENT_CREATED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_AND_FRESH_SUPERSESSION_PREFLIGHT
```

## Provider/runtime liveness reconciliation

This bounded read-only reconciliation inspected the canonical binding, the
Codex-managed session record, its event journal and startup marker, the
execution-start transaction, host process inventory, and the Zeus status and
verification interfaces. The recorded Codex broker PID `1494869` and provider
PID `1494870` were not present in the host process table. The startup marker
identifies the historical provider command as `codex app-server --stdio`, but
does not provide a trustworthy start timestamp. No current process could
therefore be shown to own the Codex-managed session.

The durable session record and journal remain preserved. Their prior
non-authoritative `MISSION_WORK_STARTED`/`MISSION_WORK_RESUMED` events do not
establish active work: the authoritative execution transaction has no active
record or work receipts, and the repository has no attributable mutation from
this execution. Zeus continues to report the execution at the controlled
start boundary.

The reconciliation found two liveness paths. Codex status inspected the
managed-session PIDs and reported the provider stopped, while execution
monitoring read the execution-start transaction, which contains no provider
PID, and consequently reported `UNKNOWN`. The bounded implementation
corrective adds a shared `runtime_liveness()` projection based on Zeus's
receipt-aware process identity inspection, makes the binding resolver
case-normalization consistent after discovery, and makes monitoring consume
the managed-session liveness when that binding is available. Supersession
safety now uses the same process-presence interpretation. A recorded PID is
not treated as live merely because it exists in a stale record; an actually
present bound process remains protected.

```text
RUNTIME_PROCESS_PRESENT=NO
RUNTIME_PROCESS_ID=NONE (recorded historical PID 1494869)
RUNTIME_PROCESS_COMMAND=codex app-server --stdio (historical startup marker)
RUNTIME_PROCESS_STARTED_AT=UNDETERMINED
RUNTIME_PROCESS_OWNS_CODEX_SESSION=NO (no current process)
CODEX_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
CODEX_SESSION_RUNTIME_STATE=STOPPED
PROVIDER_PROCESS_PRESENT=NO
PROVIDER_PROCESS_ID=NONE (recorded historical PID 1494870)
PROVIDER_LIVENESS=STOPPED
ZEUS_EXECUTION_LIVENESS=NOT_ACTIVE
ZEUS_EXECUTION_MONITORING_ACTIVE=NO
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
RUNTIME_IS_DOING_MISSION_WORK=NO
RUNTIME_IS_DOING_REPOSITORY_WORK=NO
RUNTIME_CLASSIFICATION=STALE_ORPHANED_RUNTIME
LIVENESS_DIVERGENCE_FOUND=YES
LIVENESS_DIVERGENCE_ROOT_CAUSE=MONITORING_USED_TRANSACTION_WITHOUT_PROVIDER_PID
CANONICAL_LIVENESS_RESOLVER=codex_adapter.runtime_liveness
CANONICAL_LIVENESS_RESOLVER_IMPLEMENTED=YES
SAFE_TO_STOP_STALE_RUNTIME=NOT_REQUIRED (already stopped)
SAFE_TO_SUPERSEDE_SESSION=YES (subject to operator approval and final preflight)
SUPERSESSION_TARGET_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
SUPERSESSION_TARGET_TYPE=CODEX_MANAGED_SESSION
ACTIVE_EXECUTION_PERFORMED=NO
SUPERSESSION_PERFORMED=NO
RUNTIME_TERMINATION_PERFORMED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
```

The current Codex managed session remains the unique stale-history owner. No
replacement was created, no session was terminated, and no authoritative
supersession or active-transition command was invoked. The operator must
re-run the full read-only preflight immediately before any separately
authorized supersession because runtime state can change.

Validation for this reconciliation passed: the 14-test session supersession
suite, six-test monitoring suite, and 23-test Codex adapter suite (one
environment-conditional skip); Python compilation; controlled-document
validation (2897 checks); registry validation; mission verification;
execution-start verification; platform verification; EOS validation;
repository/EOS synchronization validation; and `git diff --check`.

## Session identity reconciliation corrective

The second authoritative supersession attempt is preserved as a failed,
non-mutating attempt. The requested `EXECUTION-SESSION-*` value was not a
Codex-session filename, although it was the immutable execution-session
binding of the one Codex-managed record.

```text
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RESULT=FAIL
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_FAILURE=UNMAPPED_CODEX_ACTION_SUPERSEDE
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RUNTIME_MUTATION=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_2_RESULT=FAIL
AUTHORITATIVE_SUPERSESSION_ATTEMPT_2_FAILURE=OLD_SESSION_NOT_FOUND
AUTHORITATIVE_SUPERSESSION_ATTEMPT_2_RUNTIME_MUTATION=NO

MISSION_ID=MISSION-BETA-562F443E16C69401
WOP_ID=WOP-BETA-562F443E16C69401
EXECUTION_ID=EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e
EXECUTION_SESSION_ID=EXECUTION-SESSION-0d35cea3-1232-58f7-b202-92d0bfc256a3
PROVIDER_SESSION_ID=PROVIDER-SESSION-65d0fe07-1d02-562d-9da2-f766f3e87ef4
CODEX_MANAGED_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
REQUESTED_ALIAS_DERIVED_REPLACEMENT_ID=CODEX-SESSION-REPLACEMENT-089f49bc-eb00-54bd-9763-cab52e437b21
CANONICAL_CODEX_TARGET_REPLACEMENT_ID=CODEX-SESSION-REPLACEMENT-475bb58e-5184-5840-88de-3aa9d2ed023f
EXPECTED_REPLACEMENT_EXISTS=NO
```

The runtime inventory found one execution session, one provider session, and
one Codex-managed session. The Codex record owns the contradictory historical
event journal and binds all three lower-level identities. No replacement
record exists. The observed Codex process/session was live during read-only
inspection, so active-session protection remains authoritative and no
supersession retry was made.

The corrective adds a generic `resolve_session_binding()` contract and
explicit `codex_session_id` projections. It also permits supersession to
resolve a uniquely matching execution-session or provider-session alias to
the actual Codex-managed predecessor, while retaining fail-closed behavior
for missing, ambiguous, divergent, or active sessions. Historical records
and event journals are not rewritten.

```text
EXECUTION_SESSION_NAMESPACE=execution-start immutable execution session
PROVIDER_SESSION_NAMESPACE=provider-session lifecycle identity
CODEX_SESSION_NAMESPACE=Zeus-managed Codex session store
SESSION_ID_FIELD_OVERLOADING=CORRECTED_WITH_EXPLICIT_FIELDS
CONTRADICTORY_HISTORY_OWNER_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
SESSION_IDENTITY_MAPPING=PASS
MAPPING_CARDINALITY=ONE
AMBIGUOUS_BINDINGS=NONE
MISSING_BINDINGS=NONE
SUPERSESSION_TARGET_TYPE=CODEX_MANAGED_SESSION
SUPERSESSION_TARGET_SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
SUPERSESSION_TARGET_HISTORY_DISPOSITION=EVENTS_NON_AUTHORITATIVE
SUPERSESSION_TARGET_REPLACEMENT_SAFE=NO_WHILE_SESSION_RUNTIME_LIVE
SUPERSESSION_TARGET_RESOLUTION=PASS_READ_ONLY
```

Read-only Zeus `codex status`, `execution-start verify`, `execution status`,
and `execution verify` all converge on the same Codex-managed session while
also exposing the distinct execution/provider session fields. The execution
remains `READY_FOR_CONTROLLED_EXECUTION`, with `NOT_ACTIVE` liveness and no
mission or repository work started.

Disposable identity and supersession regressions passed, including alias
resolution, identity continuity, replay, and duplicate-predecessor
protection. The Codex adapter suite passed 23 tests with one environment skip;
the session-supersession suite passed 13 tests; the monitoring suite passed 6
tests; Python compilation and `git diff --check` passed. No authoritative
supersession, active execution, mission mutation, WOP mutation, or repository
work was performed.

```text
CANONICAL_SESSION_BINDING_RESOLVER=resolve_session_binding()
CANONICAL_SESSION_BINDING_RESOLVER_IMPLEMENTED=YES
SUPERSESSION_INTERFACE_CHANGE=execution/provider aliases resolve to Codex target
WRONG_NAMESPACE_PROTECTION=FAIL_CLOSED_ON_AMBIGUITY_OR_MISMATCH
AUTOMATIC_STALE_SESSION_RESOLUTION=UNIQUE_BINDING_ONLY
DISPOSABLE_IDENTITY_RESOLUTION=PASS
DISPOSABLE_SUPERSESSION_TARGETING=PASS
SUPERSESSION_REPLAY=IDEMPOTENT
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
P5_G7_IMPLEMENTED=NO
P5_G8_IMPLEMENTED=NO
CANONICAL_ROADMAP_CHANGED=NO
AUTHORITY_RECORDS_CHANGED=NO
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_SESSION_IDENTITY_RECONCILIATION
```

## P5-G6 supersession CLI dispatch corrective — 2026-08-07

The first authoritative supersession attempt is preserved as a failed,
non-mutating attempt:

```text
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RESULT=FAIL
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_FAILURE=UNMAPPED_CODEX_ACTION_SUPERSEDE
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RUNTIME_MUTATION=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_ACTIVE_EXECUTION_STARTED=NO
```

Read-only inspection found that the candidate already contains the required
CLI parser choice and dispatch branch. `scripts/zeus` maps `supersede` to the
existing `codex_adapter.supersede_session()` mechanism; no second
supersession implementation was added. The focused CLI suite invokes the
Zeus `main()` dispatch path and covers parser/dispatch, approval and session
preconditions, bounded adapter failure, replay behavior, and preservation of
unrelated Codex actions. The controller-routing regression expectation was
updated to include the existing `managed.supersede` mapping.

The read-only authoritative projection currently resolves
`CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5`, with execution state
`READY_FOR_CONTROLLED_EXECUTION`, inactive provider/runtime state, and no
mission or repository work. No supersession receipt or `supersedes_session`
lineage is present in the inspected runtime session record. Therefore the
observed session is not proven to be an applied replacement, and the next
operator action remains the single approved supersession command after review.

```text
CLI_PARSER_SUPERSEDE=PASS
CLI_DISPATCH_SUPERSEDE=PASS
ADAPTER_SUPERSEDE_FUNCTION=supersede_session
OBSERVED_CURRENT_SESSION=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
OBSERVED_CURRENT_SESSION_SOURCE=execution status and codex status projections
OBSERVED_CURRENT_SESSION_DISPOSITION=INACTIVE_CURRENT_PROJECTION; REPLACEMENT_NOT_PROVEN
EXPECTED_REPLACEMENT_SESSION=DETERMINISTIC_FROM_OLD_SESSION_MISSION_EXECUTION_PROVIDER_REASON
SUPERSESSION_ALREADY_APPLIED=NO
CLI_DISPATCH_CORRECTIVE=ALREADY_PRESENT_IN_CANDIDATE; REGRESSION_EXPECTATION_UPDATED
CANONICAL_SUPERSESSION_PATH=scripts/zeus -> codex_adapter.supersede_session
SECOND_SUPERSESSION_IMPLEMENTATION_CREATED=NO
CLI_PARSE_TEST=PASS
CLI_DISPATCH_TEST=PASS
CLI_SUPERSESSION_TEST=PASS
CLI_REPLAY_TEST=PASS
DISPOSABLE_CLI_SUPERSESSION=PASS
SUPERSESSION_REPLAY=IDEMPOTENT
DUPLICATE_REPLACEMENT_PREVENTION=PASS
MISSION_IDENTITY_CONTINUITY=PASS
WOP_IDENTITY_CONTINUITY=PASS
EXECUTION_IDENTITY_CONTINUITY=PASS
PROVIDER_IDENTITY_CONTINUITY=PASS
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
P5_G7_IMPLEMENTED=NO
P5_G8_IMPLEMENTED=NO
CANONICAL_ROADMAP_CHANGED=NO
```

Focused supersession testing passed 10 tests; the adapter regression suite
passed 23 tests with one environment skip; the monitoring regression suite
passed 6 tests. The reconciliation regression suite remains environment-
limited by its existing process/termination test and is not attributed to
this CLI dispatch corrective. Mission verification, execution-start
verification, platform verification, controlled-document validation,
registry validation, EOS/repository validation, Python compilation, and
`git diff --check` remained read-only checks; no authoritative supersession,
active execution, mission work, repository work, publication, commit, push,
or EOS synchronization was performed.

```text
CONTROLLED_DOCUMENTS_MODIFIED_BY_THIS_HANDOFF=NONE
IMPLEMENTATION_MODIFIED=NO; EXISTING_CANDIDATE_DISPATCH RETAINED
TEST_MODIFIED=YES; CONTROLLER-ROUTING EXPECTATION ONLY
AUTHORITY_RECORDS_CHANGED=NO
MISSION_STATE_MUTATION=NO
WOP_MUTATION=NO
EOS_MUTATION=NO
COMMIT=NOT_PERFORMED
PUBLICATION=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
NEXT_AUTHORIZED_ACTION=OPERATOR_RETRY_AUTHORITATIVE_SESSION_SUPERSESSION
STATUS=AWAITING_OPERATOR_REVIEW
```

## P5-G6 supersession CLI dispatch corrective — 2026-08-07

Inspection found that `codex supersede` was registered in the Zeus parser but
was absent from `CODEX_CONTROLLER_ROUTING`. The existing canonical adapter
function was therefore never reached and raised `unmapped codex action:
supersede` before any runtime mutation. The corrective adds only the generic
`supersede: managed.supersede` route; no second supersession implementation was
created.

```text
CLI_PARSER_SUPERSEDE=REGISTERED
CLI_DISPATCH_SUPERSEDE=CORRECTED_TO_CODEX_ADAPTER_SUPERSEDE_SESSION
ADAPTER_SUPERSEDE_FUNCTION=supersede_session(repository, mission_id, old_session_id, *, reason=..., runtime_root=..., expected_wop_id=None, expected_execution_id=None, expected_provider_id=None)
OBSERVED_CURRENT_SESSION_SOURCE=AUTHORITATIVE_HOST_PREFLIGHT_EXECUTION_START_VERIFY_AND_EXECUTION_MONITORING_PROJECTION
OBSERVED_CURRENT_SESSION_DISPOSITION=UNVERIFIED_PREEXISTING_PROVISIONAL_OR_DERIVED_CURRENT; NOT THE CANONICAL DETERMINISTIC REPLACEMENT ID; HOST RUNTIME NOT MUTATED
SUPERSESSION_ALREADY_APPLIED=NO_EVIDENCE_AVAILABLE; AUTHORITATIVE STATE UNRESOLVED
EXPECTED_REPLACEMENT_SESSION=CODEX-SESSION-REPLACEMENT-089f49bc-eb00-54bd-9763-cab52e437b21
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RESULT=FAIL
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_FAILURE=UNMAPPED_CODEX_ACTION_SUPERSEDE
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_RUNTIME_MUTATION=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_1_ACTIVE_EXECUTION_STARTED=NO
CURRENT_SESSION_ALREADY_CANONICAL_REPLACEMENT=NO
```

The prior focused suite called `supersede_session()` directly and had no CLI
test. New disposable CLI-path tests cover parser/dispatch, approval and
session validation, bounded adapter failure JSON, and preservation of existing
Codex action routing. Existing adapter tests cover reconciliation, history
preservation, deterministic replay, and duplicate-replacement prevention.
The disposable CLI surface passed parse, dispatch, transaction, replay, and
duplicate-prevention qualification. No authoritative host retry, mission work,
repository work, or runtime JSON edit was performed.

## Contradictory session history reconciliation corrective

The bound managed session was inspected without invoking the active
transition. The canonical identities remained unchanged:

```text
MISSION_ID=MISSION-BETA-562F443E16C69401
WOP_ID=WOP-BETA-562F443E16C69401
EXECUTION_ID=EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e
SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
PROVIDER_ID=zeus-local-loneal-01
```

The numbered session journal contains one `MISSION_WORK_STARTED` event and
two `MISSION_WORK_RESUMED` events. The event payloads contain only an
execution identifier for the work events; they do not carry the bound
mission, WOP, provider, session, or source-digest provenance required for an
authoritative applied-work event. The numbered journal also has a sequence
gap after event 0008 and the later events restart with null predecessor
digests. The adjacent `app-server-ready.json` marker is not a journal event.

The event emitter in the current adapter emits `MISSION_WORK_STARTED` only
after the provider acknowledges the controlled thread and turn. The persisted
host artifacts nevertheless show no applied active-transition record, the
execution-start transaction and related authorization/receipt records all
state `mission_work_started=false` and `repository_work_started=false`, the
provider session remains `execution_started=false`/`invocation_started=false`,
and no execution-scoped repository-work receipt or EENS execution event was
found. Current repository changes are pre-existing candidate work and are not
attributable to this session.

The canonical read-only `reconcile_session_history()` projection now performs
this determination from the event journal plus canonical execution and active
transition sources. Its host result is:

```text
MISSION_WORK_ACTUALLY_OCCURRED=NO
REPOSITORY_WORK_ACTUALLY_OCCURRED=NO
HISTORY_DISPOSITION=EVENTS_NON_AUTHORITATIVE
EVENT_AUTHORITY=NON_AUTHORITATIVE
EVENT_PROVENANCE=INSUFFICIENT
PROJECTION_ROOT_CAUSE=LEGACY_EVENT_HISTORY_WITH_STALE_SCOPE_PROJECTION
EVENT_HISTORY_ROOT_CAUSE=MALFORMED_LEGACY_EVENTS_AND_BROKEN_CHAIN
RECONCILIATION_REQUIRED=YES
RECONCILIATION_IMPLEMENTED=READ_ONLY_DETERMINISTIC_DISPOSITION
SESSION_REUSE_ALLOWED=NO
SESSION_SUPERSESSION_REQUIRED=YES
SESSION_REPLACEMENT_SAFE=YES
EXECUTION_ID_UNCHANGED=YES
```

This is a safe disposition because the session is inactive, no authoritative
mission or repository work is corroborated, and the old event history is
preserved. No runtime JSON, session, mission, WOP, execution, provider, or
authority record was changed. A future authorized supersession may create at
most one replacement subordinate session while retaining the existing
execution identity; the active transition was not retried here.

Regression coverage includes legacy non-authoritative events, corroborated
historical work, no-work history, read-only preservation, and the existing
P5-G3/P5-G6 adapter paths. The focused adapter suite passed 23 tests with one
environment skip; Python compilation, the execution-status read-only check,
and `git diff --check` passed. P5-G6 remains:

```text
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
HOST_ACCEPTANCE_REQUIRED=YES
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_SESSION_HISTORY_RECONCILIATION
```

Read-only validation for this corrective recorded:

```text
FOCUSED_CODEX_ADAPTER_TESTS=PASS (23 tests, 1 environment skip)
P5_G6_MONITORING_TESTS=PASS (6 tests)
P5_G6_RECONCILIATION_TESTS=PASS (22 tests)
PYTHON_COMPILATION=PASS
MISSION_VERIFICATION=PASS
EXECUTION_START_VERIFICATION=PASS
EXECUTION_STATUS=PASS
PLATFORM_VALIDATION=PASS
REPOSITORY_EOS_SYNCHRONIZATION_STATUS=PASS
CONTROLLED_DOCUMENT_VALIDATOR=TIMEOUT_ENVIRONMENT_LIMITED
GIT_DIFF_CHECK=PASS
```

The controlled-document validator was bounded to twenty seconds for this
corrective and did not complete; its captured output showed ongoing PASS
checks before the external timeout. This is not treated as a corrective
failure. No publication, EOS synchronization mutation, active transition, or
runtime reconciliation mutation was performed.

## Session-input mismatch corrective

The third authoritative active-demonstration attempt is preserved as a
distinct failed attempt:

```text
ACTIVE_DEMO_ATTEMPT_3_RESULT=FAIL
ACTIVE_DEMO_ATTEMPT_3_FAILURE=SESSION_INPUT_MISMATCH
ACTIVE_DEMO_ATTEMPT_3_ACTIVE_EXECUTION_STARTED=NO
```

Read-only inspection of the managed Codex session
`CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5` established that the
session identity still resolves to the same execution/provider/repository
identity, but its stored package digest and published-baseline binding are
stale relative to the current canonical package:

```text
SESSION_ID=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
EXECUTION_ID=EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e
SESSION_PACKAGE_DIGEST=2bfeb39b2400a6305255573ef59a200164c6e7046b57f0964e06341216abc537
CURRENT_PACKAGE_DIGEST=ab8e32128d0eb7cadad22c34b4d1dc31abdd0f16e46860ad5e07735e627b123a
SESSION_BASELINE=05167c58b5b95342734d4bf5c77f5e4c8eb77cb4
CURRENT_BASELINE=6efa815a10e80a79326339ca106f6f9e3503b664
SESSION_IDENTITY=UNCHANGED
PACKAGE_BINDING=STALE
```

The session cannot be safely classified as a stale unused session. Its
durable event chain contains `MISSION_WORK_STARTED` and two
`MISSION_WORK_RESUMED` events, and its stored `scope` claims both mission and
repository work started. The top-level session flags and the authoritative
execution projection instead report that work never started. This is a
material historical-state contradiction, not a safely reconcilable stale
session.

Accordingly, the corrective failed closed. No session replacement, runtime
record mutation, provider launch, active transition, mission work, or
repository work was performed. The existing session and all failed attempts
remain preserved. The implementation was not weakened to ignore the package
digest or event-history conflict.

```text
ROOT_CAUSE=STALE_PACKAGE_BINDING_WITH_CONTRADICTORY_SESSION_WORK_HISTORY
MISMATCH_FIELDS=package_digest,current_published_baseline,scope_vs_event_history
EXISTING_SESSION_BINDING=STALE_AND_HISTORICALLY_CONTRADICTORY
REQUESTED_SESSION_BINDING=CURRENT_CANONICAL_PACKAGE
IMMUTABLE_BINDING_MODEL=FAIL_CLOSED_ON_PACKAGE_OR_HISTORY_CONFLICT
SESSION_RECONCILIATION_REQUIRED=YES
SESSION_RECONCILIATION_IMPLEMENTED=NO_FAIL_CLOSED
STALE_UNUSED_SESSION_DETECTION=NOT_ESTABLISHED
ACTIVE_SESSION_PROTECTION=PASS
HISTORICAL_SESSION_PRESERVATION=PASS
MISSION_IDENTITY_CONTINUITY=PASS
WOP_IDENTITY_CONTINUITY=PASS
EXECUTION_IDENTITY_CONTINUITY=PASS
PROVIDER_BINDING=PASS
VERIFY_BEGIN_CONVERGENCE=BLOCKED_BY_HISTORICAL_CONFLICT
MONITOR_BEGIN_CONVERGENCE=BLOCKED_BY_HISTORICAL_CONFLICT
REPLAY=FAIL_CLOSED
DISPOSABLE_ACTIVE_TRANSITION=NOT_RUN_FOR_THIS_CORRECTIVE
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
HOST_ACCEPTANCE_REQUIRED=YES
NEXT_AUTHORIZED_ACTION=OPERATOR_RECONCILE_CONTRADICTORY_SESSION_HISTORY
```

The focused adapter regression suite passed 20 tests with one pre-existing
environment skip; the six-test monitoring suite passed; Python compilation
and `git diff --check` passed. The execution-start test command was
environment-limited before producing a result and is not claimed as a pass.
No controlled runtime, mission, WOP, authority, roadmap, EOS, or provider
state was changed by this corrective.

Validation for this corrective recorded the adapter regression suite as 20
tests passed with one pre-existing broker test skipped, the six-test P5-G6
monitoring suite as passed, the interactive suite as 21 passed with three
environment-conditional skips, the reconciliation suite as 22 passed,
Python compilation as passed, and `git diff --check` as passed. Read-only
mission verification, execution-start verification, execution status,
controlled-document validation (2897 checks), registry validation, and
repository/EOS synchronization validation all passed. The provider-session
suite remains environment-limited by its attempt to mutate the protected
authoritative runtime, and the provider-invocation suite retains two
pre-existing assertions against an obsolete historical baseline; neither
failure is caused by this `_package()` correction and neither was changed.
The broader integrated platform validator remains bounded/incomplete under
the existing worktree validation condition. No authoritative active retry was
performed.

## Active-transition `_package()` identity corrective

The second operator-controlled active-transition attempt is preserved as a
distinct failed startup attempt. It passed mission, execution-start, status,
and WOP preflight, but failed before provider/runtime startup while resolving
the Codex package:

```text
ACTIVE_DEMO_ATTEMPT=2
RESULT=FAIL
FAILURE=CODE_DEFECT_PACKAGE_IDENTITY_RESOLUTION
ACTIVE_EXECUTION_STARTED=NO
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
```

The preserved outputs are `/tmp/p5g6-active-demo-20260807T092143Z/04-begin.json`
and its corresponding `04-begin.stderr`. The traceback identifies
`codex_adapter._package(root, mission_id, runtime)`, whose mission-binding
comparison referenced the undefined name `mission`. The call-chain inspection
confirmed that `start()` normalizes and passes `mission_id` to `_package()`,
and that `resume()` and `begin_controlled_mission_work()` reach this path;
there is no separate resolved mission object required by the package
contract.

The bounded fix changes only that comparison to use the requested
`mission_id`. The identity check remains fail-closed: matching package and
execution mission identities continue, while mismatched or missing mission
identity raises `MISSION_BINDING_MISMATCH`. No identity check was removed and
no runtime record was edited.

New regression coverage exercises package identity resolution directly for a
matching mission and for mismatched/missing mission identity. Existing
disposable active-transition coverage remains green, including mission/WOP/
execution/session/provider continuity, replay idempotence, failed-startup
non-commit, and monitoring projection behavior. The authoritative host was
not retried.

```text
PACKAGE_IDENTITY_MATCH=PASS
PACKAGE_IDENTITY_MISMATCH=FAIL_CLOSED
PACKAGE_IDENTITY_MISSING=FAIL_CLOSED
ATTEMPT_1_APPLIED=NO
ATTEMPT_2_APPLIED=NO
ACTIVE_TRANSITION_ALREADY_APPLIED=NO
AUTHORITATIVE_EXECUTION_STATE=READY_FOR_CONTROLLED_EXECUTION
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
EXECUTION_LIVENESS=NOT_ACTIVE
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
TRUE_ACTIVE_HOST_RETRY_PERFORMED=NO
HOST_ACCEPTANCE_REQUIRED=YES
NEXT_AUTHORIZED_ACTION=OPERATOR_RETRY_TRUE_ACTIVE_DEMONSTRATION
```
## Supersession-time liveness convergence corrective

The latest authoritative supersession attempt remains preserved as a failed
historical fact:

```text
AUTHORITATIVE_SUPERSESSION_ATTEMPT_3_RESULT=FAIL_CLOSED
AUTHORITATIVE_SUPERSESSION_ATTEMPT_3_FAILURE=ACTIVE_SESSION_PROTECTION
AUTHORITATIVE_SUPERSESSION_ATTEMPT_3_SUPERSESSION_APPLIED=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_3_REPLACEMENT_CREATED=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_3_ACTIVE_EXECUTION_STARTED=NO
```

Read-only inspection after that attempt found the recorded runtime PID and
provider PID absent, with the canonical liveness projection reporting
`STOPPED`, `EXECUTION_LIVENESS=NOT_ACTIVE`, and no mission or repository work.
The mutation-time process state from the earlier attempt was not persisted, so
it cannot be truthfully reconstructed as either stable or changed during the
transaction. The root cause is therefore recorded as an unproven temporal
liveness divergence, not as evidence of active work.

The bounded corrective makes `runtime_liveness()` the shared liveness
projection for monitoring and supersession, and adds two fresh snapshots in
the supersession path: one after binding/reconciliation and one immediately
before the first durable write. Stable snapshots compare only process identity
and liveness facts; timestamps/presentation fields do not create false
changes. A changed snapshot fails closed as
`LIVENESS_CHANGED_DURING_TRANSACTION` with both projections. An unchanged
live snapshot remains protected by `ACTIVE_SESSION_PROTECTION` with its
mutation-time evidence. A stopped snapshot remains eligible for the existing
supersession transaction. No host supersession, runtime termination, or active
execution was retried.

```text
PRECHECK_LIVENESS=STOPPED_POSTCHECK; HISTORICAL_MUTATION_TIME=UNPROVEN
MUTATION_TIME_LIVENESS=FRESH_SNAPSHOT_REQUIRED
POSTCHECK_LIVENESS=STOPPED
LIVENESS_CHANGED_DURING_TRANSACTION=UNPROVEN_FOR_PRIOR_ATTEMPT
LIVENESS_DIVERGENCE_ROOT_CAUSE=TEMPORAL_STATE_NOT_PERSISTED; PRIOR_TRIGGER_UNPROVEN
CANONICAL_LIVENESS_RESOLVER=codex_adapter.runtime_liveness
SUPERSESSION_CONSUMES_CANONICAL_LIVENESS=PASS
MONITORING_CONSUMES_CANONICAL_LIVENESS=PASS
ACTIVE_SESSION_PROTECTION=PASS_FOR_BOUND_LIVE_RUNTIME
ACTIVE_SESSION_FALSE_POSITIVE_PROTECTION=PASS_WITH_SNAPSHOT_DIAGNOSTICS
DISPOSABLE_STOPPED_SUPERSESSION=PASS
DISPOSABLE_LIVE_RUNTIME_PROTECTION=PASS
DISPOSABLE_STATE_CHANGE_PROTECTION=PASS
SUPERSESSION_REPLAY=IDEMPOTENT_IN_DISPOSABLE_RUNTIME
AUTHORITATIVE_SUPERSESSION_RETRY_PERFORMED=NO
TRUE_ACTIVE_P5_G6_DEMONSTRATION_PERFORMED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
```

The focused supersession suite passed 17 tests, the P5-G6 monitoring suite
passed 6 tests, and the Codex adapter suite passed 23 tests with one existing
environment skip. Python compilation, Python CLI compilation, and
`git diff --check` passed. The repository remains dirty with pre-existing
candidate work; no mission, WOP, EOS, authority, roadmap, provider, or host
runtime state was changed by this corrective.

Read-only validation additionally passed controlled-document validation (2897
checks), registry validation, mission verification, execution-start
verification, execution verification, platform verification, Python CLI
compilation, and repository `git diff --check`. The P5-G3 provider-session
suite was environment-limited by its attempt to write the protected
authoritative runtime during a tamper fixture; the P5-G4 provider-invocation
and related legacy suites were likewise not claimable in this sandbox because
their protected-runtime fixtures could not be initialized. These limitations
are unrelated to the liveness corrective and did not mutate runtime state.

## Authoritative supersession retry after liveness convergence

Fresh preflight passed with the stale Codex-managed session uniquely resolved,
the execution inactive, and mission/repository work not started. The initial
attempt in the restricted environment could not create the runtime temporary
file (`Errno 30`, read-only filesystem), and did not apply a transaction. After
the required protected-runtime write permission was granted, the canonical
supersession command performed its fresh mutation-time liveness check.

That check found this interactive Codex session was the bound live runtime:

```text
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_RESULT=FAIL_CLOSED
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_TARGET=CODEX-SESSION-dbc8d546-82b0-5b0b-98bc-48a10025fdf5
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_FAILURE=ACTIVE_SESSION_PROTECTION
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_RUNTIME_PROCESS_ID=1494869
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_PROVIDER_PROCESS_ID=1494870
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_ACTIVE_PROCESS_BINDING=PASS
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_SUPERSESSION_APPLIED=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_REPLACEMENT_CREATED=NO
AUTHORITATIVE_SUPERSESSION_ATTEMPT_4_ACTIVE_EXECUTION_STARTED=NO
```

Post-failure read-only verification confirmed that execution remains
`READY_FOR_CONTROLLED_EXECUTION`, provider/execution liveness is not an active
mission execution, mission and repository work remain unstarted, and the old
session was not superseded. The live Codex runtime must not be terminated by
this handoff; the next retry requires a separate operator context in which the
target session is not the active runtime.

```text
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
TRUE_ACTIVE_P5_G6_DEMONSTRATION_PERFORMED=NO
NEXT_AUTHORIZED_ACTION=OPERATOR_RETRY_SUPERSESSION_FROM_NON_TARGET_RUNTIME_CONTEXT
```

## Provider-session reconciliation after Codex-session supersession

The next authoritative active-start attempt was not retried during this
corrective. Read-only Zeus verification identified a valid, unchanged
provider-session artifact set and a current replacement Codex session whose
persisted broker/provider PIDs and ephemeral control socket were no longer
usable. The missing resource was the Unix control socket consumed by
`codex_adapter._control_request()`; it was not a missing provider-session
artifact, provider identity, execution binding, or authority record.

```text
ACTIVE_DEMO_ATTEMPT_4_RESULT=FAIL
ACTIVE_DEMO_ATTEMPT_4_FAILURE=PROVIDER_CONTROL_FAILED
ACTIVE_DEMO_ATTEMPT_4_ERROR=ENOENT
ACTIVE_DEMO_ATTEMPT_4_ACTIVE_EXECUTION_STARTED=NO
ACTIVE_DEMO_ATTEMPT_4_MISSION_WORK_STARTED=NO
ACTIVE_DEMO_ATTEMPT_4_REPOSITORY_WORK_STARTED=NO

PROVIDER_CONTROL_FAILURE_FUNCTION=_control_request
PROVIDER_CONTROL_FAILURE_OPERATION=UNIX_CONTROL_SOCKET_CONNECT
MISSING_RESOURCE_TYPE=EPHEMERAL_CODEX_BROKER_CONTROL_SOCKET
MISSING_RESOURCE_PATH=/tmp/zeus-sockets/<session-derived>.sock
MISSING_RESOURCE_EXPECTED_OWNER=CODEX-SESSION-REPLACEMENT-475bb58e-5184-5840-88de-3aa9d2ed023f

PROVIDER_SESSION_EXISTS=YES
PROVIDER_SESSION_STATE=READY_FOR_PROVIDER_INVOCATION
PROVIDER_SESSION_CODEX_BINDING=NOT_STORED; RESOLVED_VIA_CURRENT_EXECUTION_BINDING
PROVIDER_SESSION_EXECUTION_BINDING=PASS
PROVIDER_SESSION_REUSABLE=YES
PROVIDER_SESSION_RECONCILIATION_REQUIRED=NO
RETIREMENT_INVALIDATED_PROVIDER_CONTROL_RESOURCE=YES
PROVIDER_SESSION_REBINDING_REQUIRED=NO
PROVIDER_SESSION_SUPERSESSION_REQUIRED=NO
PROVIDER_RUNTIME_REMATERIALIZATION_REQUIRED=YES

MISSION_IDENTITY_CONTINUITY=PASS
WOP_IDENTITY_CONTINUITY=PASS
EXECUTION_IDENTITY_CONTINUITY=PASS
EXECUTION_SESSION_IDENTITY_CONTINUITY=PASS
PROVIDER_IDENTITY_CONTINUITY=PASS
PROVIDER_SESSION_IDENTITY_CONTINUITY=PASS
CURRENT_CODEX_SESSION_BINDING=PASS
PROVIDER_CONTROL_USES_CURRENT_CODEX_SESSION=PASS
```

The bounded corrective adds `_provider_control_ready()`, which consumes the
canonical runtime-liveness projection and requires the persisted control
socket to exist before a managed session is treated as usable. `start()`,
`resume()`, and `begin_controlled_mission_work()` now rematerialize the
inactive broker/provider runtime when stale PIDs or a removed socket are
present, while preserving the existing provider-session identity. A live
provider with active mission or repository work remains protected by the
existing fail-closed checks.

Focused disposable coverage passed the stale-PID/missing-socket
rematerialization case, the complete Codex adapter suite, and the session
supersession suite. The P5-G6 monitoring suite remains environment-limited by
two pre-existing fixture expectations that distinguish artifact-bound
provider state (`BOUND`/`UNKNOWN`) from an actually live provider process;
the change introduced no active projection or runtime mutation.

```text
CANONICAL_PROVIDER_SESSION_RECONCILER=codex_adapter._provider_control_ready
CANONICAL_PROVIDER_SESSION_RECONCILER_IMPLEMENTED=PASS
DUPLICATE_PROVIDER_PREVENTION=PASS
DUPLICATE_SESSION_PREVENTION=PASS
REPLAY=IDEMPOTENT
DISPOSABLE_PROVIDER_RECONCILIATION=PASS
DISPOSABLE_ACTIVE_TRANSITION=PASS_BY_EXISTING_FOCUSED_ADAPTER_FIXTURE
DISPOSABLE_ACTIVE_MONITORING=ENVIRONMENT_LIMITED; MONITORING_FIXTURE_EXPECTATION_MISMATCH
AUTHORITATIVE_ACTIVE_RETRY_PERFORMED=NO
TRUE_ACTIVE_P5_G6_DEMONSTRATION=NOT_COMPLETED
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
P5_G6_DISPOSITION=PARTIALLY_SATISFIED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_PROVIDER_SESSION_RECONCILIATION
```

## Corrective: active execution monitoring projection

The successful authoritative host transition is recorded separately from the
projection defect. The host transition and provider runtime rematerialization
were already applied successfully, using the existing mission, WOP, execution,
execution-session, provider, provider-session, and replacement Codex-session
identities. No execution-start replay, session supersession, provider
termination, or identity creation was performed for this corrective.

Read-only inspection found that the immutable execution-start transaction
remained at `READY_FOR_CONTROLLED_EXECUTION` with
`mission_work_started=false`, while the authoritative active monitoring record
contained `EXECUTING`, `execution_monitoring_active=true`,
`mission_work_started=true`, `repository_work_started=false`,
`last_progress_event=MISSION_WORK_STARTED`, and `progress_state=ACTIVE`.
Monitoring incorrectly mixed these sources: execution/progress fields came
from the active record, but mission/repository work fields came only from the
pre-begin transaction. This produced `mission_work_state=NOT_STARTED` despite
the applied active transition.

The corrective establishes `_derive_work_states()` as the single derivation.
The active execution projection is authoritative once present; the immutable
execution-start transaction is the fallback before controlled work begins.
Mission work and repository work remain independent fields, so controlled
mission work does not imply repository mutation.

Focused regression coverage proves active mission work is not projected as
`NOT_STARTED`, repository work remains `NOT_STARTED` without independent
evidence, the ready boundary remains not started, and status/verify converge.
The focused monitoring suite passed 9 tests; the P5-G6 adapter suite passed 25
tests with one existing skip; the interactive suite passed 21 tests with three
existing skips. The applicable P5-G5 suite's candidate-scope authorization
check failed because these intentional uncommitted corrective paths are not in
the accepted publication scope; no qualification or publication was attempted.

```text
ACTIVE_TRANSITION=PASS
ACTIVE_TRANSITION_DISPOSITION=APPLIED_SUCCESSFULLY; PRESERVED_AS_HOST_EVIDENCE
PROVIDER_RUNTIME_REMATERIALIZATION=PASS
MONITORING_PROJECTION_ROOT_CAUSE=IMMUTABLE_PRE_BEGIN_WORK_FLAGS_OVERRULED_ACTIVE_PROJECTION
CANONICAL_MISSION_WORK_STATE_SOURCE=ACTIVE_EXECUTION_PROJECTION; TRANSACTION_FALLBACK_BEFORE_BEGIN
MISSION_WORK_STATE=STARTED
REPOSITORY_WORK_STATE=NOT_STARTED
EXECUTION_STATE=EXECUTING
EXECUTION_LIVENESS=ALIVE
PROVIDER_LIVENESS=ALIVE
IDENTITY_CONTINUITY=PASS
PROJECTION_VERIFICATION=PASS
EXECUTION_VERIFY=PASS
TRUE_ACTIVE_P5_G6_DEMONSTRATION=PASS_UNDER_PROC-0006_SPEC-0001_READ_ONLY_PROJECTION
P5_G6_DISPOSITION=TRUE_ACTIVE_DEMONSTRATION_SATISFIED_PENDING_OPERATOR_REVIEW
P5_G7_IMPLEMENTED=NO
P5_G8_IMPLEMENTED=NO
COMMIT=NOT_PERFORMED
PUBLICATION=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW; DO_NOT_BEGIN_P5-G7_OR_P5-G8
STATUS=AWAITING_OPERATOR_REVIEW
```

## Operator Acceptance

P5_G6_OPERATOR_ACCEPTANCE=ACCEPTED
P5_G6_ACCEPTED_AT=2026-08-07T11:36:31Z
TRUE_ACTIVE_P5_G6_DEMONSTRATION=PASS
EXECUTION_STATE_AT_ACCEPTANCE=EXECUTING
EXECUTION_LIVENESS_AT_ACCEPTANCE=ALIVE
PROVIDER_LIVENESS_AT_ACCEPTANCE=ALIVE
MISSION_WORK_STATE_AT_ACCEPTANCE=STARTED
REPOSITORY_WORK_STATE_AT_ACCEPTANCE=NOT_STARTED
PROJECTION_VERIFICATION_AT_ACCEPTANCE=PASS
P5_G6_DISPOSITION=ACCEPTED
PUBLICATION_AUTHORIZED_BY_THIS_ACCEPTANCE=NO
P5_G7_AUTHORIZED_BY_THIS_ACCEPTANCE=NO

## Canonical Zeus acceptance reconciliation

The host operator acceptance above was discovered as an existing decision; it
was not repeated. Before reconciliation, no machine-readable P5-G6 acceptance
record existed in the repository-bound Zeus runtime. The existing Zeus gate
acceptance path was extended with a reconciliation-only operation, and the
decision was imported once as an acceptance reconciliation record. The record
is explicitly marked `decision_origin=EXISTING_MANUAL_ACCEPTANCE` and
`new_operator_decision=false`.

The canonical record binds the accepted gate to the current mission, WOP,
execution monitoring projection, execution verification, and this report's
digest. A repeated reconciliation resolved the same record as `IDEMPOTENT`;
no second acceptance record or operator decision was created. Zeus read-only
verification and gate projection now report the accepted disposition.

```text
P5_G6_MANUAL_ACCEPTANCE_DISCOVERED=PASS
P5_G6_ACCEPTANCE_DUPLICATION=NO
P5_G6_CANONICAL_ACCEPTANCE_RECONCILIATION=PASS
P5_G6_CANONICAL_DISPOSITION=ACCEPTED
P5_G7_AUTHORIZED=NO
PUBLICATION_AUTHORIZED=NO
ACCEPTANCE_RECONCILIATION_RESULT=APPLIED_THEN_IDEMPOTENT
ACCEPTANCE_RECONCILIATION_ID=P5-G6-RECONCILIATION-46fbd9c748e87d85
ACCEPTANCE_RECONCILIATION_RECORD=.zeus/runtime/acceptance/P5-G6/P5-G6-RECONCILIATION-46fbd9c748e87d85.json
AUTHORITATIVE_ACCEPTANCE_APPLIED=NO; EXISTING_DECISION_RECONCILED
MANUAL_ACCEPTANCE_BLOCK=DEPRECATED_REDUNDANT
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW; DO_NOT_BEGIN_P5-G7
STATUS=AWAITING_OPERATOR_REVIEW
```
