# Zeus User Guide

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

## Architecture and lifecycle role

`zeus` is the operator interface to the Zeus engineering platform. Its launcher
resolves the authoritative repository and invokes `scripts/zeus`. Zeus observes
authority publication, PMCT evidence, gate approval, Work Registry, EENS,
Engineering Work Orders, dispatch, and resume state without weakening their
separate contracts.

## Stage 1 mission submission

Operators submit a WOP package through `zeus submit PATH`. `PATH` may be a
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
