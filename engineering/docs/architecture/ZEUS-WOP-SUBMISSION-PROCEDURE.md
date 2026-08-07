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

The supported `<wop>` source set includes authored Markdown/DOCX, an existing
Stage 1 package directory, and a validated `canonical-wop-package/1` YAML
source. Canonical YAML is adapted deterministically into the existing Stage 1
package-directory model before the same submission, registration, authority,
and admission interfaces are used. Its canonical package digest is preserved
as source provenance and is not replaced by the raw-file or Stage 1 tree
digest. Validation, inspection, and verification of canonical YAML are
read-only and never create submission or authority state.

Zeus resolves the authorized WOP, verifies it through the existing Stage 1
validator, and records the submission. It does not infer approval or generate
a package without an authoritative contract. If no package exists, it returns
`WOP_PACKAGE_UNAVAILABLE` with the required publication action.

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

Engineering Governance establishes execution authority before submission. The
operator-visible sequence is:

```text
Develop WOP
    -> Engineering Governance authorizes execution
    -> scripts/zeus submit <wop>
    -> Zeus executes
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

Their meanings are stable. `submit` submits a Governance-authorized WOP to
Zeus; `resume` continues an interrupted mission from its last valid execution
state. Additional mandatory commands, manual receipt management, manual
publication or recovery reconciliation, or exposure of internal lifecycle
generations require an explicit Engineering Governance architecture decision.
