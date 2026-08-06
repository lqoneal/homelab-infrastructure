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
one canonical Beta selector; on the current roadmap they identify `CAGF-01` as
the recommended eligible mission. They are read-only projections and do not create
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

The completed ZDCL-01 predecessor makes `CAGF-01` the current Beta
recommendation. The controller reports that recommendation as a projection
only; a separately authorized and resolved WOP remains required.

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
