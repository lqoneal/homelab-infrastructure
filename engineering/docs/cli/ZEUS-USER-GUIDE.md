# Zeus User Guide

## Architecture and lifecycle role

`zeus` is the operator interface to the Zeus engineering platform. Its launcher
resolves the authoritative repository and invokes `scripts/zeus`. Zeus observes
authority publication, PMCT evidence, gate approval, Work Registry, EENS,
Engineering Work Orders, dispatch, and resume state without weakening their
separate contracts.

## Commands and workflows

Use `zeus --help`, `zeus help`, or `zeus help <command>`. Common observational
commands are `zeus status`, `zeus next-action`, and `zeus dispatcher status`.
The governed gate workflow is `zeus verify OA-NN` followed later by
`zeus accept OA-NN`; verification never implies acceptance. Use
`zeus accept OA-NN --reject` for the alternate explicit decision. Operator
identity is derived from the authenticated account; no operator option exists.

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
