# Zeus Stage 1 Runtime Architecture

## Purpose and boundary

### Runtime storage boundary

Repository content, submitted WOPs, and evidence are immutable inputs. Zeus
runtime discovery is automatic and shared by every runtime consumer. It
resolves command-line `--runtime-root`, `ZEUS_RUNTIME_ROOT`, repository
`.zeus/config.yaml` (`runtime.root`), the repository-bound user-state default
`~/.local/state/zeus-runtime/<repository-id>`, and an explicitly configured
system root in that order. Repository-local, protected, read-only, and
foreign-bound candidates are rejected; explicit overrides fail closed.

The repository ID binds canonical path and origin identity, not just the
directory basename. Mutating commands initialize the selected root
idempotently and write `runtime-identity.json`; read-only controllers resolve
without creating state. Existing runtime state is not moved or merged
automatically. `ZEUS_RUNTIME_ROOT` remains an explicit testing, recovery, and
isolated-execution override.

Stage 1 is the first package-intake and execution-qualification boundary for
Governance-authorized engineering WOP packages. Publication is not an entry
condition:

```text
Engineering Governance -> WOP submission -> Mission Admission
                       -> Zeus CLI -> package validation
                       -> repository verification -> Mission Activation
                       -> Mission Contract resolution -> execution verification
                       -> staged queue -> qualification -> publication (later)
```

The runtime does not dispatch agents, interpret execution files, or publish
execution lifecycle events. Existing later-stage and qualification commands
remain separate.

## Components

`scripts/zeus` is the operator facade. The Stage 1 runtime in
`scripts/lib/emp/stage1_runtime.py` owns package intake, execution
qualification, staging, and the admission-event projection. It consumes
`scripts/lib/eos/mission_contract.py::Resolver`; it does not reproduce Mission
Contract validity or contextual authorization rules.

Directory and gzip-tar sources share one package validator. Archives reject
path traversal and links before extraction. A package contains:

- `bootstrap.md|yaml|yml`
- `roadmap.md|yaml|yml`
- `mission.yaml|yml|json` with stable `mission_id` and `wop_id`, non-empty
  `objective` and `scope`, a dependency list, non-negative integer `priority`,
  `candidate_state: CANDIDATE`, and a non-empty `required_execution_files` list
- `gates.yaml|yml|json`
- one root manifest or a manifest beneath `manifests/`
- every declared execution file
- optional `SHA256SUMS`, which is validated when present

Validation produces structured component failures. Successful validation
derives a package tree digest and deterministic mission-instance identity.
The staged record also persists those contract fields together as one
`staging_contract` and protects them with `staging_contract_digest`.

OA-05 consumes this runtime as the authoritative Mission Staging Contract.
Gate qualification uses isolated candidate repositories to demonstrate the
production `submit`, `list`, and `show` path. It does not populate the live
Stage 1 mission store. The gate may publish implementation and verification
evidence and then stops before operator acceptance, OA-06 eligibility,
dispatch, or mission execution.

## Status count authority

`zeus status` does not persist a separate count record. On every invocation,
`Stage1Runtime.status()` reloads the integrity-protected
`.zeus/runtime/stage1/missions/*.json` records in deterministic path order.
`mission_count` is the number of validated records; each per-state count is
derived from the record's `state`, and their sum must equal `mission_count`.
The status `schema_version: 1` identifies this derived response contract, not a
stored admission record.

Every record must have a valid digest, supported lifecycle state, non-empty
instance/mission/WOP identities, and an `instance_id` matching its filename.
Corruption, an unknown state, identity/path disagreement, or unreconciled
counts stops status fail closed. An absent `missions` directory is the
authoritative empty store and deterministically reports zero missions.

## Admission lifecycle and idempotency

Every Governance submission establishes Governance state `ADMITTED`. The
runtime label `VALIDATING` represents execution state `Pending Verification`.
A package, authorization, or repository verification failure historically
recorded as `REJECTED` shall be interpreted as execution state `Verification
Failed` and execution status `BLOCKED`; it does not reverse admission.
Successful verification establishes execution state `Ready` and may produce a
`STAGED` projection. Atomic replacement and a state digest protect each record.
The deterministic identity binds mission ID, WOP ID, and package content. An
identical active submission is an idempotent replay; a conflicting package is
blocked without invalidating the existing Governance admission.

The store is reconstructed by reading and verifying the records beneath
`.zeus/runtime/stage1/missions/`. A corrupt record fails closed. Stage 1 has no
execution state and takes no execution lock; therefore a staged record cannot
create concurrent execution.

## Verification and evidence

The Mission Contract resolver must return `AUTHORIZED` for execution to become
ready. Its evidence and selected contract are preserved in the qualification
record. Repository evidence records canonical root, repository identity,
branch, HEAD, working-tree state, and contract baseline provenance. Baseline
must be an ancestor of HEAD and the contract's dirty-tree policy is enforced.
Any failure blocks execution while the mission remains admitted.

The EENS adapter writes one immutable JSON record per required lifecycle event
under `.zeus/runtime/stage1/eens/`. Event IDs are deterministic and collisions
fail closed. This append-only local adapter follows the configured durable and
idempotent production EENS policy while keeping Stage 1 independent of
execution publication.

## Operator workflow

1. Prepare a complete WOP directory or `.tar.gz`.
2. Run `zeus submit PATH`.
3. Inspect `zeus show MISSION-ID` if validation or authority fails.
4. Use `zeus list` to see the staged queue.
5. Use `zeus status` to see aggregate admission state.

After admission, Zeus resolves the controlled execution-agent registry and
dispatches automatically when an active, qualified, repository-compatible
Development agent is published. An empty, stale, revoked, or incompatible
registry remains fail-closed at `AWAITING_EXECUTION_DISPATCH`; it never
fabricates dispatch or execution evidence. Agent qualification records are
produced by the existing qualification subsystem and the effective registry is
published only after its integrity and repository binding validate.

## Development lifecycle integrity

Development submission records use receipt-backed lifecycle projection. Source
validation, transactional packaging, registration, authorization, and
admission each require a corresponding receipt. Downstream phases are never
simulated by submission: `EXECUTING` requires dispatch and execution
identities, `QUALIFIED` requires independent-verification evidence, publication
and synchronization require their respective records, and `CLOSED` requires a
completion receipt referencing its predecessors.

When no qualified Development executor is available, the truthful terminal
projection is `AWAITING_EXECUTION_DISPATCH` with next action `Dispatch to a
qualified Development execution agent`. Development does not acquire a
Mission Contract prerequisite through this boundary. Historical false-closure
records remain immutable defect evidence.

Before provider selection, Zeus freezes one authority snapshot containing the
WOP/package identity, repository and protected baselines, Development effect
profile, governance resolution, and provider-qualification requirement. The
snapshot digest is bound into provider-selection and dispatch receipts;
providers cannot re-resolve mutable authority or advance lifecycle state.
`zeus mission status|authority|contract|snapshot ZDCL-02` projects the same
Stage 1 transaction identity and receipt-integrity result without mutating the
runtime. An incomplete dispatch receipt is recovered to
`AWAITING_EXECUTION_DISPATCH` rather than presented as authoritative
`DISPATCHED`.
