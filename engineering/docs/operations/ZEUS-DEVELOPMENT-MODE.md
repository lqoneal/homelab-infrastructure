# Zeus Development Mode

Status: recovery publication candidate; bounded to `ZEUS-DEVELOPMENT-MODE-RECOVERY-001`

Development Mode is the supported operator path for bounded development work:

```text
scripts/zeus submit <wop>
```

Source authoring is discoverable through `zeus wop format`,
`zeus wop template`, and optional read-only inspection commands. The
operator supplies only Markdown or DOCX source; Zeus owns canonical package
construction, validation, registration, provenance, lifecycle, and runtime
discovery.

Zeus runtime discovery is automatic. Operators shall not be required to export
`ZEUS_RUNTIME_ROOT` during normal Development Mode operation. Zeus selects a
repository-bound user-state runtime and initializes it on the first mutating
command. Use `zeus --runtime-root <PATH> submit <WOP_ID_OR_PACKAGE>` for an
isolated runtime; read-only controllers do not initialize or write runtime
state.

A valid Development WOP explicitly declares `execution_mode: DEVELOPMENT`,
binds `/data/engineering/repositories/homelab`, and carries a bounded effect
profile. Submission through the authoritative Zeus interface is the governance
submission act; a second Engineering Governance declaration is not required.
Submission validates the package and
repository first. Acceptance then generates registration and provenance in the
existing Stage 1 runtime record and advances the persisted, idempotent
lifecycle through authority resolution, admission, execution, qualification,
publication preparation, synchronization, and closeout.

For a canonical authored WOP with an adjacent immutable traceability record,
`zeus submit <WOP>` uses the P2-G1 submission boundary. It verifies
`ADMISSION_READY`, Operation Beta, Mission/WOP identity, repository identity,
and source/output provenance, then writes one deterministic submission receipt
and one admission-request projection with state `ADMISSION_REQUESTED`. A
replay is `IDEMPOTENT`; it does not invoke Mission Admission or execution.
The authoritative next action is `EVALUATE_MISSION_ADMISSION`. Legacy package
submissions retain the Stage 1 lifecycle described below.

When submission is intentionally performed with an explicit temporary runtime,
that runtime is only the canonicalization transaction workspace. Before live
mission discovery, the operator must use `zeus runtime adopt --source
<TEMP_RUNTIME>` to promote the validated P2 submission receipt and its
admission-request projection into the repository-bound user-state runtime.
Adoption verifies repository identity, source/WOP/package digests, Mission/WOP
binding, and the immutable receipt chain, then installs the selected artifacts
atomically. It is content-bound and idempotent; replay from the same or an
equivalent temporary path cannot create a second mission or receipt. Temporary
workspace cleanup therefore cannot remove authoritative state, while legacy
Stage 1 runtime adoption remains a separate compatibility path.

`zeus submit` classifies the resolved input before considering optional
repository, baseline, impact, resource, or affected-repository arguments. A
valid Development Markdown/TXT source without a sidecar is an
`DEVELOPMENT_SOURCE_PROMOTABLE` input: Zeus derives the Phase-1 provenance
envelope deterministically, preserves the source bytes, WOP ID, Mission ID,
and source digest, then uses the same P2 boundary. Existing provenance is
verified rather than regenerated. A current source cannot be diverted to the
legacy path by `--repository`, and generic `--approval` is not a substitute
for submitted-WOP authority. An approval gate declared inside the WOP remains
enforced downstream. Existing package directories and other explicitly
classified historical inputs retain the compatibility route; ambiguous or
conflicting inputs fail closed.

For an accepted published submission, the bounded P3-G1 admission command is:

```text
scripts/zeus --runtime-root <RUNTIME> admit <SUBMISSION_RECEIPT> --wop <AUTHORED_WOP> --json
```

It verifies the immutable submission receipt, authored-WOP provenance,
Operation Beta, Mission/WOP identity, repository identity, and the
`ADMISSION_REQUESTED` request projection before provisioning exactly one
immutable execution package, Mission Contract, execution-safety projection,
admission receipt, and admission journal. The execution-safety projection is
not a second operator work-authority grant. The resulting state is
`ADMISSION_COMPLETE` with `bootstrap_eligible: true`; it creates no execution
or bootstrap artifact. Repeating the same request returns the same immutable
identities with `duplicate_admission: IDEMPOTENT`.

The P3-G1 operator verification procedure replays that canonical command
twice using the `receipt_path` returned by `zeus submit`:

```text
scripts/zeus --runtime-root <RUNTIME> admit <RECEIPT_PATH> --wop <WOP_PATH> --json
scripts/zeus --runtime-root <RUNTIME> admit <RECEIPT_PATH> --wop <WOP_PATH> --json
```

Verification treats the digest-backed response transaction as Mission
Admission authority evidence when `transaction_type` is `mission-admission`,
the transaction digest verifies, and admission is complete/pass. The canonical
bootstrap boundary is `bootstrap_eligible: true` with
`next_action: EVALUATE_BOOTSTRAP_ELIGIBILITY`; verification does not rename
that action or start bootstrap. Artifact checks use the returned canonical
paths and digests under `packages/`, `mission-contracts/`,
`execution-authority/`, `receipts/`, and `journals/`, with exactly one artifact
of each required class.

Bootstrap has two explicit, non-interchangeable modes. For a verified P3-G1
admission, the canonical P4-G1 bootstrap command is:

```text
scripts/zeus --runtime-root <RUNTIME> bootstrap admission <ADMISSION_TRANSACTION_OR_RECEIPT> --json
```

The separate legacy repository-operational lifecycle must be selected explicitly:

```text
scripts/zeus --runtime-root <RUNTIME> bootstrap operational --json
```

`zeus bootstrap` without a mode fails with `BOOTSTRAP_MODE_REQUIRED`; an
admission parse failure never falls through to operational bootstrap. Admission
mode consumes only the `P3_G1_ADMISSION` contract and stops before provider
selection or execution. Operational mode consumes no P3-G1 admission artifact
and is not a Phase 4 bootstrap result. Use `zeus bootstrap --help`,
`zeus bootstrap admission --help`, and `zeus bootstrap operational --help` for
the mode-specific contracts.

Bootstrap validates the admission transaction and all five admission artifacts
against the published repository baseline before provisioning exactly one
bootstrap transaction, canonical execution record, bootstrap receipt, bootstrap
journal, and provider-readiness projection. The terminal state is
`READY_FOR_EXECUTION_PROVIDER` with `provider_ready: true` and next action
`EVALUATE_EXECUTION_PROVIDER`. Replay is `IDEMPOTENT`; provider selection,
provider sessions, dispatch, and execution remain outside this gate. Bootstrap
artifact verification is read-only and rejects altered, missing, conflicting,
or partially unrecoverable state.

Zeus is also responsible for automatic WOP packaging. The operator may submit
an existing canonical package directory, a repository-resolved WOP identity, or
a Markdown/DOCX source document. Zeus preserves the source document, resolves
only explicit metadata, constructs the schema-shaped package, validates it,
and only then enters Stage 1. Missing or conflicting authority, scope,
dependency, effect, baseline, gate, qualification, or completion metadata fails
closed before runtime state mutation. Packaging identity is deterministic;
repeated packaging reuses the same package, while a changed source requires
explicit supersession after an accepted package.

Packaging is transactional. Zeus parses and normalizes the complete source in
memory, generates and validates the full package in an isolated staging
directory, verifies source preservation and immutable-manifest digests, and
atomically promotes the package into `engineering/work-orders` only after all
checks pass. Failed parsing, metadata resolution, manifest validation, or
promotion removes staging and creates no package directory, Stage 1 state,
registration, or provenance.

Development Mode does not require a prior mission activation, Mission Contract,
EMM registration, or published provenance. Those are outputs of accepted
submission. It never authorizes production changes, mutates `OA-v1.0.0` or
`OB-PLAN-v1.0.0`, bypasses effect-profile checks, or implements CAGF-01.

Invalid packages fail before runtime state is written. Repository drift,
protected-baseline drift, publication failure, and synchronization failure are
recorded as blocked states. Repeated submission resolves the deterministic
instance identity and resumes or returns the existing result.

If a stored `DISPATCHED` projection has no valid dispatch receipt or its
authority binding is incomplete, recovery does not treat process presence as
proof of dispatch. In an isolated, baseline-valid repository it preserves the
historical invalid dispatch as evidence, removes it from the current receipt
chain, returns the transaction to `AWAITING_EXECUTION_DISPATCH`, and requires a
fresh authority snapshot before redispatch. A dirty repository, baseline
drift, or conflicting identity is reported first as its own fail-closed
recovery blocker; it must not be classified as receiptless-dispatch behavior.
The canonical operator execution entry points are:

```text
scripts/zeus submit <wop>
scripts/zeus resume <mission>
scripts/zeus stop <mission>
```

`stop` is exceptional execution control for an active or plausibly hung WOP,
not a routine lifecycle step. Zeus targets only the exact recorded execution
process group, requests graceful termination before bounded escalation, writes
an immutable termination receipt, and preserves the mission as `INTERRUPTED`
for the existing `scripts/zeus resume <mission>` path. It does not revoke
authority, cancel the mission, or create a replacement transaction.

The following are authoring, diagnosis, or read-only inspection interfaces;
they are not additional mandatory lifecycle steps:

```text
zeus doctor
zeus platform verify
zeus wop format
zeus wop template | zeus wop init
zeus wop lint <SOURCE>
scripts/zeus submit <wop>
```

`zeus doctor` diagnoses components and reports `READY_FOR_REVIEW` for a
healthy unpublished recovery branch. `zeus platform verify` is an integrated,
read-only consistency check over repository identity, published baseline,
canonical EOS projections, baseline parity, and checkpoint provenance. After a
published baseline is synchronized it reports `EOS: PASS` and
`Synchronization: PASS`; stale or mismatched EOS state fails closed with the
specific blocker. Neither command initializes runtime, adopts legacy state,
packages a source, authorizes work, or synchronizes EOS.

The WOP source document is the sole operator-authored engineering artifact;
all package, manifest, registration, provenance, runtime, lifecycle,
publication, and synchronization records are Zeus-owned outputs.

Legacy runtime state is reconciled only with `zeus runtime adopt`; read-only
status, identity, and doctor commands never adopt implicitly.

Transactions, admissions, publication receipts, receipt reconciliation,
repository lineage, baseline transitions, runtime migration, provider
selection, and execution recovery remain internal Zeus mechanisms. Publication
receipts are immutable engineering evidence, not execution authority.
