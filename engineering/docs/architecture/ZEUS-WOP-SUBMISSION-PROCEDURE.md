# Zeus WOP Submission Procedure

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

The operator-facing entry point is:

```text
zeus mission submit <MISSION_ID>
```

Zeus resolves the published Beta mission, locates a deterministic existing
package, verifies it through the existing Stage 1 validator, and records the
submission. It does not infer approval or generate a package without an
authoritative contract. If no package exists, it returns
`WOP_PACKAGE_UNAVAILABLE` with the required publication action.

The lower-level compatibility path is:

```text
zeus submit <WOP_PACKAGE>
```

`zeus mission queue` is read-only. `zeus admit-mission` and
`zeus execute-mission` are separate protected boundaries.

For an available package, the mission-oriented result includes the resolved
operation, family, title, lifecycle, classification, readiness, authority
source, selection rationale, WOP ID, package path and digest, submission ID,
submitter, priority, repository, development and production baselines, queue
state, admission readiness, blockers, and exact next authorized command. A missing,
ambiguous, stale, or invalid package returns `FAIL` with a nonzero exit status
and does not create an active queue entry; rejected validation attempts remain
available only in the append-only Stage 1 history.

## Help and boundaries

Use `zeus mission submit --help`, `zeus submit --help`,
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
