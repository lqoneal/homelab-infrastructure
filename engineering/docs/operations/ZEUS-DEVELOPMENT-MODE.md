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
binds `/data/engineering/repositories/homelab`, names Engineering Governance,
and carries a bounded effect profile. Submission validates the package and
repository first. Acceptance then generates registration and provenance in the
existing Stage 1 runtime record and advances the persisted, idempotent
lifecycle through authorization, admission, execution, qualification,
publication preparation, synchronization, and closeout.

For a canonical authored WOP with an adjacent immutable traceability record,
`zeus submit <WOP>` uses the P2-G1 submission boundary. It verifies
`ADMISSION_READY`, Operation Beta, Mission/WOP identity, repository identity,
and source/output provenance, then writes one deterministic submission receipt
and one admission-request projection with state `ADMISSION_REQUESTED`. A
replay is `IDEMPOTENT`; it does not invoke Mission Admission or execution.
The authoritative next action is `EVALUATE_MISSION_ADMISSION`. Legacy package
submissions retain the Stage 1 lifecycle described below.

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
