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

The internal execution service accepts status, resume, suspend, and cancel
operations with an explicit execution identity. These are implementation or
read-only compatibility interfaces, not mandatory operator lifecycle steps.
The public recovery operation is `scripts/zeus resume <mission>`, which
resolves exactly one safe non-terminal execution, fails closed on ambiguity,
and reuses the existing checkpoint without creating a duplicate.

Queue, mission, and execution views project the same execution identity,
current gate, wait category, validation diagnostics, and next corrective
action. No view becomes an execution authority.

## Admission freshness and supersession

Admission identity includes the resolved submission ID and the current
repository baseline, in addition to mission, WOP/revision, package digest,
contract and authority bindings, principal, submitter, mode, and lifecycle
authorization. The submission ID is resolved before the request digest and
idempotency identity are calculated.

An admission is reusable only while those bindings remain compatible and its
admitted baseline equals the current repository `HEAD`. A baseline change
makes the admission stale for new execution; it does not mutate the old
record. The replacement admission records the prior admission, any cancelled
incompatible execution, both baselines, and the supersession reason. Stale,
superseded, rejected, or incompatible-cancelled admissions fail closed at the
execution boundary.

## Stable operator contract

The internal admission and execution mechanisms do not change the operator
workflow. After Engineering Governance has authorized the WOP, the operator
submits it with `scripts/zeus submit <wop>`. Zeus consumes and enforces the
resolved authority. If execution is interrupted, the operator invokes only
`scripts/zeus resume <mission>`.

Zeus performs publication reconciliation, admission supersession, receipt
binding, baseline migration, runtime hydration, and recovery internally. These
operations are not additional operator-visible lifecycle steps. Publication
receipts remain immutable evidence of publication state and are never treated
as execution authority.
