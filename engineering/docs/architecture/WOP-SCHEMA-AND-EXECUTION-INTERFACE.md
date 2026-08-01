# Canonical WOP Schema and Execution Interface

## Authority

All WOP lifecycle stages consume the mission-contract-bound submission shape
and the published package resolver. The semantic WOP reference is canonical
for published Beta packages, for example
`WOP-ZDCL-01-FOUNDATION-001`. Legacy UUID WOP references remain valid for
standalone historical packages. A validator may not replace a published
semantic reference with a UUID or derive a second identity.

Approval authority and reference are resolved from the mission contract or
authoritative approval record. `approval.date` is optional when the authority
does not publish one; when present it must be ISO-8601. Missing optional dates
are omitted, never serialized as `None`.

## Validation contract

Package qualification, submission, admission, and execution share these
rules. Execution rechecks integrity, authority, repository, baseline, and
approval freshness, but does not introduce additional required fields. A WOP
that passed qualification, submission, and admission remains execution-valid
unless its package or authoritative state changed after admission.

The canonical sources are:

1. the mission contract;
2. the published WOP package and immutable manifest;
3. the submission and admission records;
4. the execution record and append-only evidence.

Generated and presentation projections do not own WOP identity or policy.

## Execution interface

`zeus execute-mission status`, `resume`, `suspend`, and `cancel` accept an
explicit `--execution-id`. If omitted, Zeus resolves exactly one non-terminal
execution. With none it fails closed and gives the start/ID requirement; with
more than one it fails closed and lists the IDs to choose from. `start` always
returns the deterministic execution ID. Resume reuses the existing execution
and checkpoint; it never creates a duplicate.

Queue, mission, and execution views project the same execution identity,
current gate, wait category, validation diagnostics, and next corrective
action. No view becomes an execution authority.
