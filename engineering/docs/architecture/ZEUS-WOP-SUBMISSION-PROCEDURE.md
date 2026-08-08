# Zeus WOP Submission Procedure

The shared semantic WOP contract is owned by
`WOP-SCHEMA-AND-EXECUTION-INTERFACE.md`. This procedure owns the submission
boundary only. It must consume the canonical normalized WOP projection and
must not define a competing identity, revision, package, or legacy-resolution
model.

## Authoritative sequence

```text
Mission authority
-> WOP resolution or generation
-> WOP qualification
-> Submission
-> Queue projection
-> Admission
-> Execution
```

The canonical operator-facing execution entry point is:

```text
scripts/zeus submit <wop>
```

When a machine-readable `canonical-wop-package/1` package is available, it is
the preferred CLI submission artifact because its identity, package digest,
requirements, and provenance are already explicit and independently
verifiable. The human-readable/source WOP remains the authoring and review
representation. Zeus may automatically canonicalize a valid supported source
WOP during submission when the package form is not supplied; that convenience
path preserves source bytes, WOP/Mission identity, and source digest and does
not create a second authority grant.

The supported `<wop>` source set includes authored Markdown/DOCX, a valid
promotable Development source, an existing Stage 1 package directory, and a
validated `canonical-wop-package/1` YAML source. Canonical authored and
promotable Development sources are classified first and enter the common P2
submission boundary. For a promotable source, automatic canonicalization
derives the required Phase-1 provenance while preserving source bytes, source
digest, WOP ID, and Mission ID; an existing sidecar is verified, never blindly
regenerated. Canonical YAML is adapted deterministically into the existing
Stage 1 package-directory model before the same compatibility interfaces are
used. Its canonical package digest is preserved as source provenance and is
not replaced by the raw-file or Stage 1 tree digest. Validation, inspection,
and verification remain read-only unless the operator invokes `submit`.

Zeus resolves and classifies the WOP before considering optional CLI context.
`--repository` is repository binding, not a legacy-route selector. A current
source with generic `--approval` fails closed rather than entering the legacy
admission-record contract. Submission authority is the operator-submitted
WOP; only an approval gate declared in that WOP requires approval. Existing
Stage 1 package directories and historical admission records remain an
explicit compatibility class and are not silently reinterpreted. If no
package or promotable source exists, Zeus returns a fail-closed result with
the required corrective action.

For canonical P2 submission, the receipt state is `ADMISSION_REQUESTED`, the
next action is `EVALUATE_MISSION_ADMISSION`, and no admission, provider,
session, or execution identity is created. Replay is deterministic and
idempotent.

Read-only mission views use the same receipt-backed resolver after submission:
when a verified P3 admission transaction exists it projects `ADMITTED`, and
when a verified P4 bootstrap transaction exists it projects
`AWAITING_EXECUTION_DISPATCH`. Each projection is subordinate to the
contiguous P2 identity chain; duplicate, orphaned, or conflicting canonical
transactions fail closed. Stage 1 and historical/provider projections remain
compatibility evidence and do not advance current state.

Mission-oriented selection and projection commands are compatibility views;
they are not additional mandatory execution lifecycle steps. The historical
command form is:

```text
zeus mission submit <MISSION_ID>
```

`zeus mission queue` is read-only. The admission and execution boundaries are
internal Zeus services; their historical command names are retained only for
compatibility and are not mandatory operator actions.

For an available package, the mission-oriented result includes the resolved
operation, family, title, lifecycle, classification, readiness, authority
source, selection rationale, WOP ID, package path and digest, submission ID,
submitter, priority, repository, development and production baselines, queue
state, admission readiness, blockers, and exact next authorized command. A missing,
ambiguous, stale, or invalid package returns `FAIL` with a nonzero exit status
and does not create an active queue entry; rejected validation attempts remain
available only in the append-only Stage 1 history.

## Help and boundaries

Use `scripts/zeus submit --help`, `zeus mission submit --help`,
`zeus submit --help`,
`zeus mission queue --help`, `zeus generate-wop --help`,
`zeus admit-mission --help`, and `zeus execute-mission --help` for the
published command contracts. Submission does not approve, admit, or execute.

## Admission contract binding

Admission resolves the published Mission Contract and its referenced WOP
package before constructing the admission artifact. The package is reused,
not regenerated. The artifact is bound to the immutable manifest, package
tree digest, repository, development baseline, existing Stage 1 submission,
authority, approval reference, lifecycle mode, and dispatch boundary.

Qualification and operational admission use the same resolver. Qualification
sets `QUALIFICATION_ONLY` and denies dispatch; operational admission may
permit dispatch only after its explicit approval boundary is satisfied. Mode
does not alter mission identity, scope, WOP identity, authority, or baseline.

An unresolved contract, package, digest, authority, approval, repository, or
baseline is a nonzero fail-closed result. Placeholder, generic, or fabricated
values are never valid successful admission metadata.

## Stable operator boundary

The authoritative Zeus submission interface carries submission authority. The
operator-visible sequence is:

```text
Develop WOP
    -> scripts/zeus submit <wop>
    -> validate/register/provenance
    -> resolve mission/WOP authority and admission
    -> execution authorization and applicable approvals
    -> Zeus may execute only when downstream gates pass
```

When interrupted, `scripts/zeus resume <mission>` is the sole recovery entry
point. Zeus automatically resolves publication receipts, verifies repository
lineage, reconciles admissions and receipts, migrates runtime state, and
continues from the last safe lifecycle position. Operators shall not manually
repair, bind, finalize, supersede, or migrate those records.

Publication receipts are immutable publication evidence. They bind a
qualified implementation to its verified publication state but do not create,
revoke, or extend execution authority. Authority remains owned by Engineering
Governance and is consumed and enforced by Zeus.

## Normative compatibility contract

The public execution interface consists only of:

```text
scripts/zeus submit <wop>
scripts/zeus resume <mission>
```

Their meanings are stable. `submit` is the canonical governance submission
act. It does not itself authorize execution, production effects, acceptance,
publication, synchronization, or closeout; those remain downstream controlled
acts. `resume` continues an interrupted mission from its last valid execution
state. Additional mandatory commands, manual receipt management, manual
publication or recovery reconciliation, or exposure of internal lifecycle
generations require an explicit Engineering Governance architecture decision.

The invariant is `AUTHORITATIVE_SUBMISSION_IS_SUBMISSION_ACT=YES`,
`SECOND_GOVERNANCE_SUBMISSION_DECLARATION_REQUIRED=NO`, and
`DEVELOPMENT_PRODUCTION_SUBMISSION_PROTOCOL_DISTINCTION=NONE`.

## Outputs and evidence

The procedure produces a validated submission receipt, registration and
provenance projection, downstream admission readiness, and a deterministic
next action. These outputs and their reconciliation evidence are inspected
before any downstream lifecycle transition is accepted.
