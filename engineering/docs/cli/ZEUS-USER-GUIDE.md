# Zeus User Guide

## Runtime discovery

Normal commands require no runtime export. Zeus selects a repository-bound
user-state runtime automatically. Use `zeus --runtime-root /path submit <WOP>`
or `ZEUS_RUNTIME_ROOT=/path zeus ...` only for explicit isolation, testing, or
recovery. A rejected or foreign-bound path fails closed; read-only commands do
not initialize runtime state.

## CLI consistency and readiness

Use `zeus doctor` for component diagnosis and readiness classification. Use
`zeus platform verify` for the integrated read-only consistency check. The
governed `zeus verify <GATE>` and mission-scoped `zeus mission verify
<MISSION_ID>` commands retain their existing meanings. `zeus synchronize`
reports readiness only; EOS mutation remains under the established `engctl`
synchronization authority.

## Controlled Mission Authority

`zeus authority show`, `zeus authority resolve`, and `zeus authority validate`
expose the current mission authority source, exact Mission Contract, WOP,
repository, branch, HEAD, baseline, gate, lifecycle, admission, predecessor
receipt, checks, decision, blocker, and next authorized action. `validate`
returns nonzero unless every binding is present, structurally valid,
unambiguous, current, authorized, and mutually consistent.

Zeus revalidates this authority at OA-02 resume, implementation transition,
verification, marker validation, and operator-decision boundaries. A prior
successful result is not cached as authority. Missing, malformed, ambiguous,
inactive, unauthorized, revoked, stale, mismatched, incomplete, or conflicting
authority stops fail closed without dispatch, evidence qualification, approval,
next-gate activation, event publication, or another protected external effect.

`zeus resume` implements the sole active OA-02 gate and stops at
`AWAITING_OPERATOR_VERIFICATION`. `zeus verify OA-02` creates integrity-bound
verification evidence and `VERIFIED` but does not accept OA-02 or enable OA-03.

## OA-01 mission verification

OA-01 has a read-only, mission-centric verification surface. Run
`zeus mission list`, `zeus mission show`, `zeus mission state`,
`zeus mission readiness`, `zeus mission eligibility`,
`zeus mission blockers`, `zeus mission contract`,
`zeus mission authority`, and `zeus mission next`.

These commands compose the existing Work Registry, Mission Contract resolver,
Progressive WOP runtime, Project State, EOS authority matrix, and Git identity.
They do not accept a gate, execute a mission, dispatch an agent, or create a
second state store. The acceptance contract and capability mapping are in
`engineering/operations/zeus-oa01-mission-verification.md`.

When OA-01 reports `IMPLEMENTATION_REQUIRED`, `zeus resume` runs the bounded
implementation-completion assessment. On PASS it records integrity-bound
implementation evidence and changes the existing Progressive runtime to
`AWAITING_OPERATOR_VERIFICATION`. It does not create the formal `VERIFIED`
marker, accept OA-01, or enable OA-02. Follow the admitted OA-01 verification
guide for those separately controlled steps.

The generic mission list is not an OA-01 selector. `zeus mission list --json`
merges the Operation Beta planning view with missions whose immutable P2
submission receipt and admission-request projection resolve through the
canonical lifecycle chain. A submitted mission retains its WOP identity,
authority source, lifecycle state, blockers, and next action in that list.
If a requested current mission has no canonical receipt, Zeus returns an
explicit fail-closed result rather than falling through to OA-01 Mission
Knowledge or a planning selector. Historical OA records remain available only
through their historical/compatibility surfaces.

## Architecture and lifecycle role

`zeus` is the operator interface to the Zeus engineering platform. Its launcher
resolves the authoritative repository and invokes `scripts/zeus`. Zeus observes
authority publication, PMCT evidence, gate approval, Work Registry, EENS,
Engineering Work Orders, dispatch, and resume state without weakening their
separate contracts.

## Stage 1 mission submission

For normal Beta operation, submit the Governance-authorized WOP through the
canonical operator interface:

```text
scripts/zeus submit <wop>
```

Zeus resolves the mission and authoritative package from the submitted WOP.
If the package or its authority is missing, the command fails closed and
states the exact required action. It does not invent a package, approve work,
admit execution, or bypass the queue. `zeus mission submit <MISSION_ID>` is a
historical mission-oriented compatibility path, not an additional mandatory
operator lifecycle step.

Operators submit a WOP package through `scripts/zeus submit PATH`. `PATH` may be a
directory or a `.tar.gz`/`.tgz` archive. Zeus safely opens the package, verifies
its bootstrap, roadmap, mission metadata, gates, manifests, declared execution
files, and optional `SHA256SUMS`, then resolves the package mission through the
existing Mission Contract resolver. Mission metadata must carry the stable
mission and WOP identities, objective, scope, dependencies, priority, and
`CANDIDATE` state. The staged record preserves those values in an
integrity-bound `staging_contract`. These checks determine execution readiness,
not Mission Admission. The runtime also verifies repository root, identity,
branch, baseline ancestry, working-tree policy, and operator identity. A
failure records the historical runtime label `REJECTED` and exits 78; under the
governance lifecycle this means execution status `BLOCKED` while Mission Status
remains `ADMITTED`.

A Governance-admitted submission is projected through `VALIDATING`, `ADMITTED`,
and `STAGED`. These runtime labels do not authorize an execution agent to
admit, revoke, or activate a mission.

For Development submissions, lifecycle phases are derived from immutable
receipts rather than projected milestones. If no qualified executor is
available, `scripts/zeus submit` stops at `AWAITING_EXECUTION_DISPATCH` and reports
`Dispatch to a qualified Development execution agent`. It does not report
execution, qualification, publication, synchronization, or closeout without
the corresponding receipts. This Development boundary does not require a
Mission Contract.

## Execution status and recovery

For one active execution, inspect the canonical recovery contract with:

```text
scripts/zeus mission recovery <mission> --json
```

The recovery projection resolves monitoring, interruption, checkpoint, and
resume eligibility without mutating state. A later authorized resume request
continues the existing checkpoint and never creates a duplicate execution;
the GAP-008 recovery contract does not itself invoke a provider or begin
mission work. Execution status and administrative controls are internal or
read-only compatibility interfaces. Ambiguous or unsafe state fails closed
with the exact diagnostic and next authorized action.
Submitting identical mission and package content again returns the existing
instance with `idempotent_replay: true`; it never creates a second active
mission. State is stored under `.zeus/runtime/stage1/missions/` with an
integrity digest and survives process restart. No Stage 1 command dispatches
an execution agent or executes package content.

Use `zeus list` for staged missions, `zeus show MISSION` for a mission's full
record and validation evidence, and `zeus status` for the
`mission_admission` summary alongside the existing operational status.
The summary is reconstructed from integrity-valid persisted mission records
on every call: `mission_count` is the record count and `states` groups those
same records by supported lifecycle state. Its `schema_version` versions the
summary response. Zero means the live mission store is empty; it is not a
placeholder. Any corrupt or inconsistent record makes status exit fail closed.

`zeus mission submit MISSION-ID` returns the same authoritative mission
resolution used by `zeus mission explain`, plus the durable submission ID,
WOP package path and digest, submitter, priority, queue state, admission
readiness, blockers, and the exact admission command. Repeating the same
submission returns that existing record with `idempotent_replay: true`.

Stage 1 publishes immutable, idempotent EENS projections under
`.zeus/runtime/stage1/eens/`: `mission.submitted`, `mission.validating`,
`mission.admitted`, `mission.rejected`, and `mission.staged`. Event identity
binds the mission instance, lifecycle state, WOP, and timestamp. A
`mission.rejected` projection reports failed execution qualification and shall
not be interpreted as revocation of Governance admission.

OA-05 qualifies this interface as the Mission Staging Contract. Its
implementation and verification execute candidate submission only in isolated
repositories, require the complete integrity-bound `staging_contract`, and
prove deterministic replay and restart recovery. The live gate stops at
`VERIFIED_AWAITING_OPERATOR_ACCEPTANCE`; qualification does not submit a
production mission, dispatch an agent, execute work, accept OA-05, or enable
OA-06.

## Commands and workflows

Use `zeus --help`, `zeus help`, or `zeus help <command>`. Common observational
commands are `zeus status`, `zeus next-action`, and `zeus dispatcher status`.
The governed gate workflow is `zeus verify OA-NN` followed later by
`zeus accept OA-NN`; verification never implies acceptance. Use
`zeus accept OA-NN --reject` for the alternate explicit decision. Operator
identity is derived from the authenticated account; no operator option exists.

The Progressive OA package instead exposes the explicit compatibility command
`zeus approve OA-NN --operator OPERATOR`. Approval creates a uniquely named,
append-only receipt bound to the current package manifest, gate, VERIFIED
marker bytes, marker digest, verification-evidence digest, and operator. Zeus
reports `idempotent_replay: true` only when the gate is already accepted and
runtime state points to that exact, integrity-valid, non-superseded receipt
with every current binding unchanged. Historical `accepted.json` files are
audit evidence, not current decisions. Use `zeus gate receipt OA-NN` to resolve
and validate only the receipt referenced by runtime state.

`zeus verify OA-02` performs the pre-execution readiness evaluation without
authorizing dispatch. Status and next-action resolve the integrity-protected
OA-02 record automatically. Current-binding PMCT qualification is reported
separately from OA-02-specific PMCT readiness; `NOT_READY` therefore identifies
the missing OA-02 demonstration or another ordered prerequisite without
invalidating the accepted OA-01 PMCT PASS.

Complete the separate OA-02 demonstration with `pmct run OA-02`. `zeus status`
and `zeus next-action` resolve its integrity-valid current-binding evidence
automatically. With no qualified production agent, a PASS advances only the
derived next action to `QUALIFY_PRODUCTION_AGENT`; the dispatcher remains
prepared and inactive and operational dispatch remains disabled.

`zeus authority status` and `zeus authority work-lifecycle` are observational
JSON surfaces used by PMCT to demonstrate publication and gate-lifecycle
resolution. They never publish authority or record a gate decision.

## Mission discovery and qualification

`zeus mission snapshot MISSION-ID` discovers the requested Mission Contract
and generates its canonical Engineering Execution Interface snapshot.
`zeus execution resolve MISSION-ID` exposes the same resolution pipeline.
`zeus mission qualify MISSION-ID` verifies that exactly one contract resolves
and reports lifecycle, implementation, acceptance, blockers, approvals, and
the next authorized action. Repeated qualification against unchanged
operational state produces identical JSON. These commands are observational;
they do not record acceptance, publish a baseline, or authorize dispatch.

## Mission assurance

`zeus assurance capabilities` identifies the independent read-only assurance
surface. `zeus mission requirements MISSION-ID` derives the applicable
requirements and Mission Contract cardinality from canonical discovery.
`zeus mission preflight MISSION-ID` verifies pre-mission readiness;
`zeus mission verify MISSION-ID` reports readiness, execution eligibility,
synchronization, and closeout eligibility together; and
`zeus mission synchronization MISSION-ID` verifies post-mission source,
registry, and completion-evidence reconciliation.

Every result includes authoritative sources, observed values, unsatisfied
requirement identifiers, and a deterministic evidence digest. A failed
eligibility command exits 78. Assurance is observational: it does not perform
the execution procedure, synchronize records, record acceptance, or advance a
mission lifecycle.

The requirement list and language definition are not embedded in Zeus. The
canonical Engineering Execution Interface resolves structured declarations
from the exact controlled specification, standard, and procedure revisions
bound by the execution manifest. It separately resolves the exact `SPEC-0013`
Controlled Mission Assurance Language revision. Capability and mission results
report the resolved language version.

Every declaration binds `language_version`. The controlled language defines
the declaration schema, phases, selector grammar and roots, compound
expressions, operator field contracts, applicability, and phase-result rules.
Zeus implements named interpreter primitives but accepts them only when the
bound language definition enables them. Unsupported primitives, operators,
selectors, expression shapes, unknown fields, unsafe repository paths,
duplicate identifiers, missing phases, unavailable owner revisions, and
language-version mismatches fail closed.

Language revisions are independent of Zeus releases. A compatible revision
using existing interpreter primitives is adopted by updating the controlled
language owner and execution-interface binding, then migrating every
declaration's `language_version` atomically. A revision requiring a new
primitive also requires an interpreter compatibility update. Neither path
changes the read-only behavior or the Engineering Execution Interface's role
as canonical resolver.

## Comprehensive canonical mission verification

For a materialized Operation Beta mission, the sprint-level acceptance command is:

```text
scripts/zeus mission verify MISSION-ID
scripts/zeus mission verify MISSION-ID --json
```

`mission verify` resolves the authoritative runtime internally and verifies
repository identity and published baseline, Operation Beta authority and the
Operational Alpha exclusion, mission identity, WOP provenance, submission,
admission, bootstrap, execution-record and provider-readiness artifacts,
mission-scoped cardinality/integrity, replay determinism, and the downstream
provider/dispatch boundary. It is strictly read-only: it does not submit,
admit, bootstrap, replay, select a provider, dispatch, execute, mutate EOS, or
modify the repository. A failure exits nonzero and returns `result: FAIL` with
the causal blocker code and next authorized action. Legacy
`mission-executions` records and unrelated runtime records are excluded unless
they bind to the requested canonical mission chain. Operation Beta remains
authoritative; Operational Alpha is historical/superseded and cannot be a
fallback authority.

Baseline semantics are explicit. `current_baseline`/`published_baseline` are
resolved from the live repository (`HEAD` and `origin/main`) and EOS must
match them. `mission_provenance_baseline` remains the immutable commit stored
in the mission artifacts. It is valid after publication when it is reachable
and an ancestor of the current publication (or equal to it). Therefore a
compatible publication does not invalidate an already materialized mission.
The resolver fails closed with precise blockers such as
`PUBLICATION_PARITY_FAILURE`, `EOS_BASELINE_MISMATCH`,
`MISSION_PROVENANCE_BASELINE_MISSING`, `MISSION_PROVENANCE_NOT_ANCESTOR`,
`RUNTIME_REPOSITORY_BINDING_MISMATCH`, or `REPOSITORY_IDENTITY_MISMATCH`.
Platform and mission verification consume this same read-only resolver.

The supporting mission views `status`, `authority`, `lifecycle`, `evidence`,
`artifacts`, `replay`, `blockers`, `next`, and `snapshot` use the same
canonical projection for `MISSION-BETA-*` IDs. Capability or roadmap checks
are not substitutes for authoritative mission verification.

## Production agent qualification

`zeus agent status` and `zeus agent registry` display the integrity-validated
runtime registry. `zeus agent qualify` evaluates the authenticated local
agent's identity, repository access, current published baseline and authority,
OA-01 decision, OA-02 PMCT binding, runtime dependencies, security, EENS, and
execution capabilities. Successful qualification is append-only and
idempotent for the same binding. `zeus agent revoke AGENT-ID` appends a
revocation linked to the preserved qualification; it never overwrites history.

The tracked empty registry is the schema/bootstrap baseline. Mutable
qualification and effective-registry records live beneath
`.zeus/runtime/agents/` so qualification cannot change repository HEAD or
create a publication loop. A stale qualification remains historical evidence
but is ineligible when HEAD, published baseline, authority publication, or
PMCT run changes. Qualification does not authorize dispatch.

After OA-02 verification passes, `zeus status` and `zeus next-action` consume
the same OA-02 lifecycle projection. Before separate operator authorization
they report dispatcher `PREPARED`, operational dispatch `DISABLED`, PMCT
`PASS`, OA-02 verification `PASS`, next action `AUTHORIZE_DISPATCH`, and
result `READY`. `READY` means authorization may now be recorded; it does not
mean dispatch is enabled. Operational dispatch becomes `ENABLED` only after
the dispatcher activation records explicit authorization and every PMCT,
authority, publication, agent, and OA-02 binding remains valid. Any regression
fails closed and blocks authorization. Status inspection never records that
transition.

## Accepted-gate carry-forward

OA-01 acceptance is a durable mission milestone. After a successor baseline is
published and PMCT-qualified, `zeus gate carry-forward OA-01` performs an
automated impact assessment against the latest integrity-valid accepted
ancestor. It writes a checksummed runtime record binding both publications and
baselines, the prior receipt digest, successor PMCT evidence, changed paths,
affected acceptance criteria, and the carry-forward decision.

An unaffected successor reports `OA01_REVALIDATION_REQUIRED=NO`; status,
next-action, PMCT, OA-02, and agent qualification then resolve OA-01 as
verified and accepted without duplicating human verification. A change to an
OA-01-controlled authority, PMCT, evidence, decision, or safety criterion
reports `OA01_REVALIDATION_REQUIRED=YES` with the affected criteria and cannot
carry acceptance forward. The command never records a new operator decision.

Authority baselines are managed by `scripts/authority-publishctl`. PMCT supplies
gate evidence. Work Registry records controlled engineering work. EENS and
dispatch remain unavailable until independently qualified. Resume commands
continue only from recorded lifecycle state.

## Troubleshooting and evidence

Exit `2` indicates invalid command syntax; `78` indicates a failed prerequisite or
governed-state error. Run `scripts/install-engineering-cli verify` when command
discovery fails. Runtime evidence is beneath `.zeus/runtime/`; PMCT evidence is
beneath `engineering/runtime/pmct/runs/`. See the PMCT User Guide and
Engineering CLI Standard in this directory.
Runtime recovery uses the transactional operator command:

```text
zeus runtime adopt --dry-run
zeus runtime adopt
zeus runtime adopt
```

The second invocation is idempotent. Do not edit runtime JSON or copy runtime
directories manually.

For a canonical P2 submission created in an explicitly selected temporary
transaction runtime, adoption is the durable boundary:

```text
scripts/zeus runtime adopt --source <TEMP_RUNTIME> --dry-run --json
scripts/zeus runtime adopt --source <TEMP_RUNTIME> --json
```

The command verifies the immutable submission receipt and admission-request
pair, repository binding, Mission/WOP identity, and receipt digests before
atomically promoting only those canonical submission artifacts into the
repository-bound user-state runtime. Temporary canonicalization directories
are transaction workspaces, not authoritative stores. Repeating adoption—or
replaying from an equivalent temporary directory—returns the same deterministic
adoption identity without creating a second receipt or mission. Historical
runtime records remain preserved and cannot override the current canonical P2
chain.
## P5-G1 provider selection

For a verified Operation Beta mission whose bootstrap state is
`READY_FOR_EXECUTION_PROVIDER`, Zeus exposes the bounded provider-selection
gate:

```text
scripts/zeus provider candidates <MISSION_ID> --json
scripts/zeus provider select <MISSION_ID>
scripts/zeus provider verify <MISSION_ID> --json
```

The selector consumes the published execution-agent registry and its existing
qualification records.  Eligibility requires an active, qualified,
repository-scoped candidate with the mission capability, declared tools,
trust/authentication identities, and compatible baseline.  Policy
`ZEUS-P5-G1-PROVIDER-SELECTION/v1` ranks eligible candidates by the explicit
`(provider_id, provider_type)` ordering and records every candidate and
exclusion reason.

Selection creates exactly one immutable mission-bound transaction, selected
provider, qualification, receipt, journal, and dispatch-readiness projection.
Replay reuses those records and reports `IDEMPOTENT`.  A partial or conflicting
chain fails closed.  `provider verify` is read-only and never creates a
provider session, invokes a provider, creates dispatch, or starts execution.

The selection terminal state is `READY_FOR_PROVIDER_DISPATCH`; the next action
is `EVALUATE_PROVIDER_DISPATCH`.  Provider dispatch is a later gate and is not
authorized by P5-G1.

## P5-G2 provider dispatch foundation

After provider selection verifies, the bounded dispatch gate is:

```text
scripts/zeus dispatch create <MISSION_ID>
scripts/zeus dispatch verify <MISSION_ID> --json
scripts/zeus dispatch status <MISSION_ID>
scripts/zeus dispatch artifacts <MISSION_ID> --json
scripts/zeus dispatch authorization <MISSION_ID> --json
scripts/zeus dispatch package <MISSION_ID> --json
```

Dispatch creation is deterministic and create-only. It provisions exactly one
dispatch transaction, package, authorization record, receipt, journal, and
provider-session-readiness projection in the authoritative runtime. Replaying
unchanged inputs reuses the immutable chain and reports `IDEMPOTENT`; partial,
forged, stale, or conflicting state fails closed. The package references the
canonical mission, execution record, execution package, Mission Contract,
execution authority, provider selection, repository identity, current
published baseline, and immutable mission provenance.

The terminal state is `READY_FOR_PROVIDER_SESSION`. This gate does not invoke
the provider, create a provider session, launch Codex, start execution, or
collect execution evidence. The next action is
`ESTABLISH_PROVIDER_SESSION`, which requires a later authorized gate.

## P5-G3 provider session foundation

The bounded provider-session gate is operator-driven:

```text
scripts/zeus provider-session create <MISSION_ID>
scripts/zeus provider-session verify <MISSION_ID> --json
scripts/zeus provider-session status <MISSION_ID>
scripts/zeus provider-session artifacts <MISSION_ID> --json
scripts/zeus provider-session authorization <MISSION_ID> --json
```

Creation derives one deterministic provider session from the published
dispatch and the unchanged provider selection. It provisions exactly one
provider session, receipt, journal, authorization, and readiness artifact.
Replay is idempotent. Verification rechecks the published mission, authority,
repository/runtime bindings, dispatch digests, provider-selection digests,
artifact integrity, and cardinality. Missing, malformed, cross-mission, stale,
substituted, or tampered state fails closed.

The terminal state is `READY_FOR_PROVIDER_INVOCATION`. This gate does not
invoke the provider, start invocation, start execution, create an execution
session or record, mutate dispatch/provider selection, or collect execution
evidence. The next action is `INVOKE_PROVIDER`, which requires a later
operator-authorized gate.

## Publication workflow stabilization

Publication verification is exposed through the stable Zeus contract:

```text
scripts/zeus publication status
scripts/zeus publication verify <MISSION_ID>
scripts/zeus publication verify <MISSION_ID> --json
```

The read-only controller uses `scripts/zeus platform verify`,
`scripts/zeus authority validate`, `scripts/zeus mission verify`, and
`scripts/zeus provider verify`, together with the supported engctl contracts
`registry validate`, `validate homelab`, `eos validate homelab`, and
`eos sync-validate homelab`. It never calls an internal Python implementation
path such as the nonexistent `scripts/validate-engineering-platform.py`.

Publication mutation and EOS synchronization remain owned by the governed
publication procedure and engctl. The controller distinguishes candidate,
publication, reconciliation, and harness failures; a completed publication
replays as `PUBLICATION_RECONCILED`/`IDEMPOTENT`. An uncommitted candidate is
reported as `CANDIDATE_SCOPE_FAILURE` rather than being silently accepted.

Provider-invocation verification preserves the invocation's immutable
provenance baseline across later publications. The canonical baseline
resolver reports `IDENTICAL` or `ANCESTOR` only when repository/runtime parity
and invocation-critical bindings remain valid; unrelated, missing, invalid,
or repository-mismatched baselines fail closed. The verification output
separates `invocation_provenance_baseline` from
`current_published_baseline`.
The repository-native focused-test launcher must be module-based so the
repository root is on Python's import path. Use:

```text
python3 -m pytest -q scripts/tests/test-zeus-p5-g3-provider-session.py scripts/tests/test-zeus-mission-verification-controller.py

## Mission-native provider/session aggregate

For a canonical submitted mission, inspect the one receipt-backed lifecycle
position and its subordinate provider/session/process/monitor/evidence
observations with:

```bash
scripts/zeus mission aggregate <MISSION_ID> --json
```

This surface is read-only. It reports missing downstream records as
`NOT_STARTED` or `NOT_AVAILABLE`, preserves historical sessions as history,
and cannot advance the mission or override the canonical next action.

### GAP-008 monitoring and recovery

Inspect monitoring and recovery state with:

```bash
scripts/zeus mission recovery <MISSION_ID> --json
```

This is a read-only projection owned by the canonical lifecycle chain. Before
execution it reports `recovery_state=NOT_STARTED` and does not create provider,
session, process, heartbeat, checkpoint, or evidence records. After an
execution interruption, the `ZEUS-CANONICAL-RECOVERY/1` contract binds one
checkpoint and interruption receipt to the mission, WOP, execution, provider,
session, repository baseline, source digest, lifecycle position, and evidence
position. Process/session liveness is observational only.

Resume is permitted only from exactly one current, identity-valid, non-stale
checkpoint. Missing, conflicting, stale, forged, or digest-invalid recovery
evidence fails closed. A resume request preserves the existing execution ID,
skips completed work, and replays idempotently; it never creates a second
execution or invokes a provider from a read-only inspection surface.
```

Running `pytest -q scripts/tests/...` directly is not the supported publication
harness invocation because it can fail before collection with
`ModuleNotFoundError: No module named 'scripts'`.

## P5-G4 provider invocation foundation

Provider invocation means that Zeus resolved the canonical invocation package
and received a provider-bound acknowledgement. It is distinct from execution:
the P5-G4 terminal state is `READY_FOR_EXECUTION_START`, while execution and
mission work remain false.

```text
scripts/zeus provider-invocation create <MISSION_ID> --json
scripts/zeus provider-invocation verify <MISSION_ID> --json
scripts/zeus provider-invocation status <MISSION_ID> --json
scripts/zeus provider-invocation authorization <MISSION_ID> --json
scripts/zeus provider-invocation package <MISSION_ID> --json
scripts/zeus provider-invocation acknowledgement <MISSION_ID> --json
scripts/zeus provider-invocation artifacts <MISSION_ID> --json
```

The package is resolved from the authoritative mission, dispatch, provider
session, Mission Contract, execution authority/package, repository identity,
published baseline, mission provenance, and published Operation Beta authority
chain. Its identity is deterministic and excludes timestamps, process IDs,
terminal IDs, and transient credentials. Zeus owns authorization, binding,
replay, and verification; `engctl codex` remains a low-level compatibility
launcher and is not called by P5-G4.

This implementation uses `invocation_mode=QUALIFICATION_ADAPTER`. The adapter
exercises the complete package boundary and returns a deterministic provider
acknowledgement without starting a provider process, execution, or mission
work. A real `engctl codex` integration is deferred until a separately
authorized cutover defines credentials, launch supervision, acknowledgement,
interruption, and resume behavior.

Replay returns the unchanged invocation and artifact digests as
`IDEMPOTENT`. Partial, forged, stale, substituted, cross-mission, conflicting,
or path-escaping state fails closed. No invocation projection may claim
`READY_FOR_EXECUTION_START` without a valid acknowledgement and all seven
canonical artifacts.

Publication final-projection checks are schema-specific: status checks
stage-state fields, lifecycle checks its lifecycle object, next checks only its
next action, snapshot checks identities, and verify checks
`mission_verification=PASS`. Every structured Python assertion in a publication
procedure must be fail-closed, for example:

```bash
python3 -m pytest -q scripts/tests/test-zeus-p5-g4-provider-invocation.py || exit 1
scripts/zeus mission verify <MISSION_ID> --json || exit 1
```

### Execution-start foundation

`scripts/zeus execution-start create <MISSION_ID>` establishes one
deterministic Zeus execution-start transaction only after the acknowledged
provider invocation verifies. The current bounded adapter is explicitly
`execution_adapter_mode=QUALIFICATION_ADAPTER`: it creates a provider-bound,
idle execution session projection and acknowledgement, but does not launch
Codex, deliver the WOP, monitor a process, begin mission work, mutate the
repository, or report completion. A future real adapter must satisfy the
separate `REAL_CODEX` process/session and acknowledgement contract.

Use `execution-start verify`, `status`, `authorization`, `package`, `session`,
and `artifacts` for read-only inspection. Replay is idempotent and preserves
the execution identity and all eight canonical artifact digests. Partial,
orphaned, forged, stale, duplicate, or conflicting execution-start state
fails closed. Execution start is not mission work; the next boundary is
`BEGIN_CONTROLLED_MISSION_WORK`.

After operator review of the bound authority, the canonical consumer of that
boundary is:

```text
scripts/zeus execution-start begin <MISSION_ID> --approve --json
```

`begin` does not create a second execution lifecycle. It verifies the existing
execution-start record, reuses its mission/WOP/provider/invocation/session
bindings, asks the same provider broker for one controlled thread/turn, and
then records an identity-preserving active-execution and monitoring
projection. A provider/session startup or acknowledgement failure is
fail-closed before active projection commit. Repeating `begin` against the
same active transition returns `REPLAY=IDEMPOTENT`; it does not start another
execution, provider process, session, or turn.

### P5-G6 controlled Codex sessions

The normal operator entry point is direct native Codex launched under the Zeus
lifecycle wrapper:

```text
scripts/zeus codex shell
scripts/zeus codex shell <MISSION_ID> --approve
scripts/zeus codex attach <MISSION_ID>
```

`status`, `logs`, and `artifacts` are read-only managed projections. They use
one explicit controller, never allocate a PTY, launch a provider, consume
stdin, or change terminal mode. `status --json` writes exactly one JSON
document to stdout; diagnostics belong on stderr. `shell` resolves the Zeus
context and launches the ordinary Codex CLI directly with inherited terminal
streams through the shared native launcher; Zeus does not emulate the Codex
terminal or parse its keyboard input. Opening a shell is only
`INTERACTIVE_SESSION_OPEN`; it does not mean mission or repository work
started. The official client owns thread/turn presentation and remains open
until the operator exits or Zeus records a controlled failure.
Mission-bound shells use the published authority chain and execution
package. Non-mission shells are explicitly unbound and do not imply a WOP or
Mission Contract.

The official Codex client owns terminal settings, multiline editing, resize,
Unicode, ANSI, and bracketed-paste behavior. Zeus owns process lifecycle and
records metadata only; it does not rewrite or store pasted instruction text.

Zeus lifecycle around the selected native or remote client is recorded as:

```text
CREATED -> ATTACHING -> ATTACHED -> REMOTE_CLIENT_ACTIVE
                                      |
                         client exit/signal -> STOPPING -> STOPPED
                         provider failure   -> FAILED
```

Zeus-local inspection and lifecycle commands remain outside Codex prompts.
The official client’s own commands govern conversation presentation; exiting
the client performs a controlled Zeus stop. `attach` reconnects to a compatible
Zeus remote endpoint without creating a provider.
For exact interactive inspection, select the record explicitly:

```text
scripts/zeus codex status --session <SESSION_ID> --json
scripts/zeus codex logs --session <SESSION_ID>
scripts/zeus codex artifacts --session <SESSION_ID>
scripts/zeus codex status --mode OPERATOR_INTERACTIVE --latest --json
scripts/zeus codex status --mode OPERATOR_INTERACTIVE --active --json
```

The managed adapter's durable broker is not silently replaced by an ordinary
interactive launch. If its provider cannot expose a compatible remote
endpoint, `attach` fails closed with the provider and recovery action instead
of creating a duplicate provider. `resume` is identity-checked managed
recovery and is never an implicit fresh session.

The remote contract is verified only for explicit remote launch. For Codex CLI
`0.146.1`, Zeus requires `codex --remote ws://127.0.0.1:<port>` and starts an
authorized separate `codex app-server --listen ws://127.0.0.1:<port>` provider
when the managed provider is `MANAGED_STDIO`. The listener is loopback-only and
is not ready until a WebSocket JSON-RPC `initialize` probe succeeds. Diagnose
without opening the client with:

```text
scripts/zeus codex shell --remote --diagnose
```

The diagnostic form is explicitly remote-only:

```text
scripts/zeus codex shell --remote --diagnose
```

Direct launcher preflight is redirect-safe and never opens Codex:

```text
scripts/zeus codex shell --preflight
```

It resolves the canonical repository-relative launcher
`scripts/lib/eos/codex-direct-launch.sh`, verifies its file, executable, and
repository-boundary properties, checks the Codex binary and authentication
configuration, and reports `TTY_REQUIRED_FOR_LAUNCH=YES`. A real direct shell
still requires an attached terminal and inherited streams. Zeus and
`engctl codex` resolve the same launcher; defects are reported as
`DIRECT_LAUNCHER_MISSING`, `DIRECT_LAUNCHER_NOT_EXECUTABLE`, or
`DIRECT_LAUNCHER_PATH_ESCAPE`, never as a raw filesystem exception.

Remote diagnosis and operational launch share one endpoint-establishment
transaction. Both establish and verify the loopback WebSocket/JSON-RPC
listener and persist its endpoint receipt. Diagnostic mode then cleans up
without launching the official client; operational mode passes the verified
URI to `codex --remote`, records the client PID, monitors exit, and cleans up
the listener it owns. `REMOTE_ENDPOINT_MISSING` is reserved for explicit
attach/reuse; normal `shell --remote` creates its endpoint.

Direct mode is `DIRECT_INTERACTIVE` (`CODEX_CLI`, `DIRECT_TERMINAL`) and does
not create a listener or select a provider session. Remote mode is
`REMOTE_INTERACTIVE` (`APP_SERVER_REMOTE`, `WEBSOCKET`) and never silently
falls back to direct or stdio. Managed mode is `ZEUS_MANAGED`
(`APP_SERVER_MANAGED`, `STDIO`).

Provider records distinguish `MANAGED_STDIO` (`remote_capable=false`) from
`INTERACTIVE_REMOTE` (`remote_capable=true`). A live stdio-only provider is not
selected for remote attach; Zeus either reuses a verified remote-capable
provider or establishes one separate, explicitly identified interactive
provider. Endpoint receipts include the URI, listener PID, transport,
readiness result, and failure phase.

The managed execution interface remains Zeus:

```text
scripts/zeus codex start <MISSION_ID> --approve
scripts/zeus codex status <MISSION_ID>
scripts/zeus codex resume <MISSION_ID> --approve
scripts/zeus codex stop <MISSION_ID> --approve
scripts/zeus codex logs <MISSION_ID>
scripts/zeus codex artifacts <MISSION_ID>
```

`codex start` first verifies the canonical execution-start chain, then binds
one deterministic session to the mission, execution, provider, repository,
and published baseline before launching the idle Codex application server.
Operator approval is
required for start, resume, and stop. Zeus owns the session identity, process
identity, working directory, logs, append-only events, interruption state,
and replay; the Codex process does not own lifecycle authority. `codex start`
remains provider/session preparation and does not consume
`BEGIN_CONTROLLED_MISSION_WORK`; use `execution-start begin` for the bound
active transition.
`codex shell --help`, `start --help`, `attach --help`, `resume --help`,
`stop --help`, `status --help`, `logs --help`, and `artifacts --help` provide
command-specific guidance. `--approve` is required for mission-bound shell,
managed start/resume, and stop.

Zeus records structured request decisions supplied by a provider request
surface as `ALREADY_AUTHORIZED`, `OPERATOR_DECISION_REQUIRED`, or
`PROHIBITED`. Opaque terminal prompts are never parsed as authority and are
not silently approved. Direct `engctl codex` remains a recovery and
diagnostic path; it bypasses Zeus mission lifecycle projections and is not a
Zeus-managed session.

The observed `Codex could not find bubblewrap on PATH` warning is an
environment diagnostic, not a terminal-rendering failure. The supported
disposition is `SYSTEM_BUBBLEWRAP=PREFERRED`; the bundled provider fallback is
`BUNDLED_BUBBLEWRAP=SUPPORTED`. No host package was installed or changed.

The runtime handshake sends only the newline-delimited JSON-RPC `initialize`
request through a durable Zeus broker. A `READY` session proves that the
provider process and application server initialized; the official remote
client then performs the documented initialize/thread/turn lifecycle. Zeus
does not infer protocol completion from process readiness.
Codex state uses a writable per-session `CODEX_HOME`; local auth/configuration
are referenced without copying credentials. Startup diagnostics are sanitized
and available through `codex status` and `codex logs`.

The adapter starts only the first controlled mission-work boundary. It does
not authorize publication, EOS synchronization, mission closeout, completion,
or work outside the verified repository/execution binding. Status, logs, and
artifacts are read-only projections. An interrupted process is reported as
`INTERRUPTED` and must be resumed through Zeus after reconciliation.

Publication verification owns only summarized publication and stage state.
Detailed provenance belongs to `provider-invocation verify`, and execution
identity, adapter mode, session binding, replay, and mission-work boundaries
belong to `execution-start verify`. These command-specific schemas prevent a
summary projection from being treated as a complete nested controller
record. Structured verification commands must stop on failure with `|| exit 1`.

### P5-G6 post-publication runtime reconciliation

`codex reconcile` is a controller-owned runtime inventory. The canonical
read-only form is:

```bash
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --dry-run
```

Omitting `--dry-run` is also read-only unless `--approve` is present. Approved
mutation is explicit:

```bash
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --approve
```

The structured result includes matching sessions, live/owned/orphan listeners,
stale and detached sessions, proposed actions, ownership checks, cardinality,
and multidimensional `session_state`, `client_state`, `listener_state`,
`attachment_state`, and `provider_state`. Each endpoint is normalized to one
termination unit; broker, Node, and native child processes are not separate
actions. Only `OWNERSHIP_VERIFIED` or `OWNERSHIP_RECOVERED_VERIFIED` listeners
may be stopped. Unknown, partial, mismatched, or ambiguous ownership remains untouched and is reported
as an actionable orphan.

The JSON response exposes `termination_units`, `plan_schema_version`,
`plan_digest`, `required_action_count`, `executable_action_count`, and an
ownership summary. An approved command must include the exact digest returned
by the reviewed dry run:

```bash
scripts/zeus codex reconcile --mode REMOTE_INTERACTIVE --approve \
  --plan-digest <REVIEWED_PLAN_DIGEST>
```

Missing or changed digests are rejected before signaling. A read-only plan
with no executable actions returns `FAIL` and
`RECONCILE_PROCESS_IDENTITY_AND_OWNERSHIP`; an executable plan returns
`BLOCKED_PENDING_APPROVAL` until explicitly approved.

Diagnostic sessions are proposed for cleanup after readiness succeeds and the
client was never launched. A remote client exit leaves its verified listener as
`DETACHED/EXITED/READY/DETACHED/READY`, with next action `ATTACH_OR_STOP`.
Attach reuses the recorded endpoint and session identity:

```bash
scripts/zeus codex attach --session <SESSION_ID> --approve
scripts/zeus codex stop --session <SESSION_ID> --approve
```

Stop is receipt-backed, verifies process identity and socket closure, and is
idempotent. The managed stdio provider is a separate lifecycle and is not a
remote reconciliation target.

Remote reconciliation exposes a flattened ownership qualification report for
every termination unit. It distinguishes immutable conflicts from recoverable
legacy omissions; a receipt-backed live process tree may therefore be
`OWNERSHIP_RECOVERED_VERIFIED`, while ambiguous evidence remains
`OWNERSHIP_PARTIAL` and conflicts remain `OWNERSHIP_MISMATCH`. Remote status
uses the same canonical projection, so a retained listener is shown as
`DETACHED`/`EXITED`/`READY` with `ATTACH_OR_STOP`.

An approved run that completes some actions while preserving non-executable
targets returns `PARTIAL`, with `reconciliation_applied=true` and
`reconciliation_fully_converged=false`. Preserved targets include their
endpoint, ownership result, missing evidence, immutable conflicts, and next
operator action; they are not reported as failed mutations. The strict
default policy keeps `TERMINAL_STATE=false` until remaining orphan ownership
is resolved. Replaying a completed plan by its prior `--plan-digest` is
idempotent and sends no new signals or receipts.

When no executable action remains and only explicitly preserved partial-
ownership targets are present, a read-only review returns `PASS` with
`reconciliation_required=false`, `reconciliation_fully_converged=false`, and
`next_authorized_action=REVIEW_PRESERVED_TARGETS`. This is a reviewable safe
disposition, not a failed mutation. The response separates
`reconciliation_applied_this_invocation` from
`reconciliation_already_applied`; `replay_result` is always explicit
(`IDEMPOTENT` or `NOT_REQUIRED`).

When `--approve --plan-digest` names a previously completed plan, Zeus looks
up its authoritative completed receipt and projects it against a fresh current
inventory. The response exposes `replay_context` with the requested,
completed-historical, and current plan digests. Historical application is
reported as `reconciliation_already_applied=true`; no current mutation is
performed, and the next action reflects the current disposition (for example
`REVIEW_PRESERVED_TARGETS`). Missing or conflicting completed receipts return
`NOT_FOUND` or `CONFLICT` and fail closed.

### P5-G5 canonical projection reconciliation

For the authoritative `MISSION-BETA-*` runtime, `mission verify`, `status`,
`state`, `readiness`, `next`, `snapshot`, `lifecycle`, `health`, `brief`, and
`roadmap` consume the same read-only canonical runtime discovery. Execution
start owns `execution_id`, `execution_session_id`,
`execution_start_provenance_baseline`, `current_published_baseline`,
`execution_start_baseline_relationship`, integrity, replay, and the mission
work boundary. Provider invocation continues to own the distinct
`invocation_provenance_baseline`; it is never reused as execution-start
provenance. Every projection therefore reports the same execution state and
next action while retaining command-specific schemas.

### P5-G6 execution monitoring

The read-only execution monitor is distinct from provider/session status. It
resolves the canonical execution-start transaction, mission/WOP/provider/
session bindings, execution state, provider and execution liveness, current
work position, blockers, approvals, roadmap position, source digests, and
next authorized action. Provider process existence alone never projects active
execution.

Use the Zeus-native interfaces:

```text
scripts/zeus execution status <EXECUTION_ID> --json
scripts/zeus execution verify <EXECUTION_ID> --json
```

`execution verify` independently checks identity, bindings, state, liveness,
position, blocker/approval projection, progress, provenance, and idempotent
replay. The projection reports `PHASE_CURRENT/PHASE_TOTAL` and
`GATE_CURRENT/GATE_TOTAL` from the source-bound canonical roadmap revision;
these are structural orientation metrics, not completion percentages.

Monitoring is read-only. It does not start mission or repository work, grant
approval, advance lifecycle state, or create execution records. Contradictory
execution and monitoring state fails closed with
`RECONCILE_EXECUTION_STATE`. Optional execution-scoped EENS events are read as
source evidence when present; EENS remains a projection/transport layer and
not an independent execution authority.

### P5-G6 acceptance reconciliation

When a host operator has already recorded P5-G6 acceptance in the controlled
completion evidence, Zeus discovers that decision through the existing gate
acceptance path. Readiness and the canonical disposition are read-only:

```text
scripts/zeus verify P5-G6 --json
scripts/zeus gate show P5-G6 --json
```

If no machine-readable record exists, the one-time import is explicitly marked
as reconciliation of the existing decision and does not request or create a
new operator decision:

```text
scripts/zeus accept P5-G6 --reconcile-existing --yes --json
```

Replay is idempotent. The resulting record is Zeus-owned acceptance state,
bound to the active execution projection, execution verification, and the
completion report digest. P5-G6 acceptance does not authorize publication or
P5-G7 execution. The manual shell acceptance block is therefore redundant for
future gates; use the canonical Zeus path and retain the report as evidence.
