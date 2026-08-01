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
source, WOP ID, package path and digest, submission ID, repository, development
and production baselines, queue state, and next authorized action. A missing,
ambiguous, stale, or invalid package returns `FAIL` with a nonzero exit status
and does not create an active queue entry.

## Help and boundaries

Use `zeus mission submit --help`, `zeus submit --help`,
`zeus mission queue --help`, `zeus generate-wop --help`,
`zeus admit-mission --help`, and `zeus execute-mission --help` for the
published command contracts. Submission does not approve, admit, or execute.
