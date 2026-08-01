# Existing Submission Workflow Assessment

The published Beta baseline already supplies the authoritative workflow:

```text
WOP package -> Stage1Runtime.validate -> mission authority resolution
-> ADMITTED/STAGED state -> queue projection -> mission admission -> execution
```

The existing operator entry point is `zeus submit <WOP_PACKAGE>`. It validates
the package, resolves the Mission Contract, persists an integrity-protected
Stage 1 record, emits EENS projections, and is idempotent for identical active
submissions. `zeus admit-mission` and `zeus execute-mission` remain separate
protected boundaries.

The confirmed gap was package resolution from a canonical Beta mission ID.
`zeus mission submit <MISSION_ID>` now resolves the published Beta roadmap,
searches only deterministic canonical package locations, and delegates an
existing package to `Stage1Runtime`. It does not create a second queue,
authority, admission store, or execution path.

At the current baseline `ZDCL-01` is eligible but its roadmap dependency,
“approved ZDCL contract,” has no published package. The mission-ID command
therefore fails closed with `WOP_PACKAGE_UNAVAILABLE` and names the exact
publication action required. This is an authority boundary, not a CLI defect.
