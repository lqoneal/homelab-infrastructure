# Zeus Operation Beta Controller Integration

Status: published controller integration for `OB-PLAN-v1.0.0`
Operation: `OPERATION-BETA`
Production baseline: `OA-v1.0.0` (immutable)
Development baseline: `OB-PLAN-v1.0.0`

## Authority and projection boundary

Zeus provides read-only projections for Operation Beta. The published Beta
roadmap is the planning source; the Mission Knowledge Model, Capability
Registry, EMM, PMCT/gate authority, EOS, Engineering Governance, EMP, and EENS
retain the ownership assigned by the Beta authority model. This controller
does not persist mission state, allocate capability identifiers, or advance a
lifecycle.

The controller recognizes the `ZDCL`, `CAGF`, and `EPE` mission families and
exposes operation, family, and mission views. Derived metrics carry the
source baseline and are recomputed on every request.

## Required integrity checks

Beta verification fails closed when a controlled source is absent, the
roadmap order or root is invalid, either `OA-v1.0.0` or `OB-PLAN-v1.0.0` is
missing, the pillar model is incomplete, or production/development identity
cannot be distinguished. Unknown mission families and orphan mission IDs are
errors, not empty projections.

## CLI contract

```text
zeus operation show BETA
zeus operation status BETA
zeus operation roadmap BETA
zeus operation metrics BETA
zeus operation health BETA
zeus operation verify BETA
zeus operation next-action BETA

zeus mission list
zeus mission completed
zeus mission history
zeus mission archive
zeus mission roadmap ZDCL
zeus mission roadmap CAGF
zeus mission roadmap EPE
zeus mission status <MISSION_ID>
zeus mission readiness <MISSION_ID>
zeus mission blockers <MISSION_ID>
zeus mission prerequisites <MISSION_ID>
zeus mission dependencies <MISSION_ID>
zeus mission metrics <MISSION_ID>
zeus mission verify <MISSION_ID>
zeus mission next
zeus mission recommend
zeus mission health
zeus mission authority <MISSION_ID>
zeus mission contract <MISSION_ID>
zeus mission snapshot <MISSION_ID>
```

Alpha inspection commands remain available through their existing
Mission Knowledge Model projections. Beta output never substitutes for Alpha
production state, and Alpha history is not treated as Beta authority.

The default mission list is the active Beta development view. Completed Alpha
missions are historical projections and are exposed only by the completed,
history, or archive views.

Mission queue inspection remains on the existing EMP/Zeus orchestration and
Beta selection path. `list`, `queue`, `next`, `recommend`, and `health` share
one canonical Beta planning selector; it identifies `CAGF-01` as the future
recommended mission. Current execution is resolved separately from the
receipt-backed lifecycle chain and currently identifies
`ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`. They are read-only projections and do not create
a parallel queue, scheduler, admission store, or lifecycle authority. See
`ZEUS-MISSION-QUEUE-AND-SCHEDULING.md` for the ownership and fail-closed
contract.

## Metrics

Operation and mission metrics are derived from the roadmap cards and current
published baselines. They include lifecycle counts, progress views, critical
path, dependency/authority/controller/roadmap health, promotion readiness,
unresolved recommendations, and production/development divergence. The
metrics are not stored as authority and cannot repair a source conflict.

## Next action

The completed ZDCL-01 predecessor makes `CAGF-01` the future Beta
recommendation. The controller reports that recommendation separately from
the current executable lifecycle mission; the existing CAGF WOP remains
unsubmitted and deferred behind lifecycle completion.

The Beta authority, contract, and snapshot views for a mission are read-only
inspection projections. They expose roadmap scope, dependencies, authority,
readiness, and the canonical next action without creating a Mission Contract,
admission, execution, or lifecycle transition.

## Mission-oriented WOP projection and compatibility

The canonical submission workflow is `scripts/zeus submit <wop>` after
Engineering Governance authorization. `zeus mission submit <MISSION_ID>` is a
historical mission-oriented compatibility/projection path, not an additional
mandatory lifecycle command. Both paths resolve the same authoritative WOP
and never fabricate a package or approval. Interrupted work is resumed only
through `scripts/zeus resume <mission>`; admission, receipt, publication, and
recovery reconciliation remain internal Zeus mechanisms.

## Codex interactive provider boundary

P5-G6 has three explicit execution modes. Direct interactive is the default:
Zeus resolves context and launches the native Codex CLI with inherited terminal
streams. Explicit remote interactive resolves the mission/repository/execution
context, starts or reuses a verified remote-capable app-server endpoint, and
launches `codex --remote <endpoint>` under the recorded session identity. The official Codex client owns terminal
rendering, keyboard input, paste, resize, thread, and turn presentation.
Zeus remains the lifecycle, authority, approval, evidence, replay, and
recovery controller; `engctl codex` remains the emergency recovery path and
is not a Zeus-managed authority bypass.

Managed execution remains `MANAGED_STDIO` and is never advertised as remotely
attachable. Interactive use is an explicitly bound `INTERACTIVE_REMOTE`
provider started with the installed listener syntax:
`codex app-server --listen ws://127.0.0.1:<port>`. Zeus selects a free
loopback port, records the endpoint receipt, and performs a WebSocket plus
JSON-RPC initialize readiness probe before launching the official client.
Process existence alone is not readiness; stale, non-loopback, wrong-scheme,
or non-responding endpoints fail closed with diagnostics.

### P5-G6 corrective convergence

Post-publication reconciliation is Zeus-owned. `codex reconcile` inventories
remote session records and loopback `app-server --listen` processes, exposes
ownership and cardinality details, and derives independent session, client,
listener, attachment, and provider states. The default and `--dry-run` forms
are read-only. `--approve` permits only ownership-verified listener stops,
records append-only termination receipts, updates the authoritative session
projection through Zeus, and replays idempotently. Diagnostic listeners are
stopped after a successful readiness receipt; an operational client exit
retains one verified listener as a detached reusable session. Unknown or
partial orphans are preserved and surfaced for operator review. Managed stdio
providers are outside the remote reconciliation target set.

Process ownership uses one canonical Linux identity tuple:
`boot_id`, `pid`, `process_start_ticks` (the `/proc` clock-tick value),
executable, command digest, and process group. Wall-clock receipt timestamps
are never compared to `/proc` ticks. Legacy receipts are recoverable only
when immutable endpoint, transaction, command, group, and boot evidence
agrees; otherwise ownership remains partial or unknown. Codex home resolution
prefers the session, endpoint/ready receipt environment, then the broker
command line. Broker, Node, and native children are aggregated into one
endpoint termination unit, with all member PIDs and process groups
revalidated immediately before signaling.

The endpoint unit is the canonical contract consumed by inventory, diagnostic
and orphan classification, retained-session projection, action generation,
pre-signal validation, and status output. Its stable fields include the unit
ID, endpoint, roots, members, groups, socket owner, process-tree digest,
ownership evidence digest, classification, and required disposition. The
reviewed plan exports these units at top level and computes a SHA-256 digest
over the stable unit/action set. Approval requires that digest; missing or
changed digests fail before mutation.

The direct launcher locator is repository-root-derived and canonical:
`scripts/lib/eos/codex-direct-launch.sh`. Both Zeus and `engctl codex` resolve
that same regular executable, and pre-launch validation rejects missing,
non-executable, or repository-escaping paths with structured blocker codes.
`scripts/zeus codex shell --preflight` is redirect-safe and does not launch
Codex; native TUI acceptance remains a separate attached-terminal operation.

Remote diagnosis and remote operation consume the same endpoint transaction.
The transaction records loopback allocation, listener startup, WebSocket and
JSON-RPC readiness, endpoint identity, and a durable receipt containing
`endpoint_owner_session_id`, `endpoint_creation_transaction_id`, listener PID,
and endpoint URI. Diagnostic receipts are ephemeral and cleaned up after the
probe. Operational receipts remain owned by the interactive session until
client exit reconciliation. An endpoint created by `shell --remote` is never
required to pre-exist; `REMOTE_ENDPOINT_MISSING` applies only to explicit
attach/reuse.

Reconciliation result state is separate from cardinality state. `PASS`
requires strict terminal convergence; `PARTIAL` means at least one mutation
was applied while safely preserved targets remain; and `FAIL` means no
authorized mutation was applied or an attempted mutation failed. Cardinality
separately reports active sessions, detached sessions, diagnostic listeners,
preserved orphans, and verified-owned orphans. A completed diagnostic receipt
is consumed by inventory and status, so replay does not recreate the action or
resend its signal.

When cardinality is healthy and all remaining actions are non-executable
`PRESERVE_TARGET` dispositions, terminal review is not represented as a
mutation failure: the read-only result is `PASS`, while
`reconciliation_required=false` and `reconciliation_fully_converged=false`
make the strict-convergence boundary explicit. The next action is
`REVIEW_PRESERVED_TARGETS`. Application state is split into
`reconciliation_applied_this_invocation` and
`reconciliation_already_applied`; replay reports `IDEMPOTENT`, and a normal
non-replay response reports `NOT_REQUIRED` rather than a null replay value.

Completed-plan replay is receipt-backed and current-plan-independent. Zeus
matches the requested historical digest only to an approved successful
reconciliation receipt, then overlays that historical application result on
the fresh canonical inventory. The response keeps
`requested_plan_digest`, `matched_completed_plan_digest`, and
`current_plan_digest` separate in `replay_context`; it does not execute the
current preserved-target plan. Missing or conflicting receipt matches are
explicit replay failures.
