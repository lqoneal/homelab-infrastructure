# Zeus Mission Admission Runtime

Admission is a required validation boundary, not a second work-authority
grant. Every protected execution boundary independently
revalidates the integrity-bound admission receipt together with the current
Mission Contract, WOP, repository, predecessor receipt, and active gate.
Missing or invalid admission remains admitted only as a governance fact and
cannot dispatch execution or produce protected effects.

The production operator is Lawrence O'Neal, authenticated as `loneal`.
Operational admission verifies the identity-bound submitted WOP and does not
seek a second generic human approver. Zeus remains unable to originate an
approval or bypass admission policy.

Under the current submission protocol, the operator-submitted WOP is the work
authority and admission is the lifecycle entry decision. Submission by the
operator is intentional submission; the runtime's
repository identity, repository integrity, package integrity, qualification,
and policy stages determine execution readiness only. Their failure records an
execution blocker; it does not reject, reverse, or invalidate Governance
admission.

## Purpose and boundary

ZEUS-P2-007 provides one supervised, repository-local coordinator for mission
admission. It composes existing validation, authority-resolution, WOP, and
admission services; it does not originate authority, approval, identity,
publication, submission, dispatch, or execution.

The persistent admission store is:

`<repository>/.zeus/runtime/mission-admissions/<admission-id>.json`

Each record is digest protected and written atomically. The store is
operational evidence, not an authority source.

## State machine

The ordered stages are:

1. `MISSION_VALIDATION`
2. `REPOSITORY_VERIFICATION`
3. `MISSION_QUALIFICATION`
4. `AUTHORITY_RESOLUTION`
5. `WOP_GENERATION`
6. `SUBMISSION_ELIGIBILITY`
7. `ADMISSION_DECISION`

Every completed stage records structured, digest-bound evidence. For a manual
Governance submission, `ADMISSION_DECISION` projects the Governance decision;
it does not create a new execution-agent decision. A transition occurs only
after the current stage completes. `BLOCKED` preserves the failed stage and
diagnostics while Governance status remains `ADMITTED`; `INTERRUPTED` preserves
the next stage. Resume skips completed stages, retries only the current
incomplete stage, and returns an
unchanged terminal record when a decided admission is replayed.

The stable runtime interfaces are repository verification, mission-record
selectors, owner-enrollment and publication readiness probes, the Authority
Resolution Runtime and sealed ARB, the WOP Service, and the Admission
Controller. Authority resolution is implemented only by the Authority
Resolution Runtime.

## Qualification workflow

Qualification uses the same seven-stage coordinator and the same canonical
mission-contract/WOP resolver as operational admission. For a published
mission such as `ZDCL-01`, the resolver binds the Mission Contract, published
WOP package, immutable manifest, package digest, repository/development
baseline, authority, approval reference, and existing submission record.
Qualification changes only the execution boundary: it ends with
`QUALIFICATION_ONLY` and `dispatch_permitted: false`. It never creates a
replacement WOP and never emits placeholder authority, approval, or manifest
values.

The historical synthetic qualification fixture remains available only for
legacy `ZEUS-*` test missions. Unknown published missions fail closed when no
Mission Contract or WOP package can be resolved.

```text
scripts/zeus admit-mission start \
  --mode qualification \
  --mission ZDCL-01 \
  --wop WOP-ZDCL-01-FOUNDATION-001 \
  --submitter loneal \
  --principal loneal \
  --submission-id ZEUS-MISSION-06a7fcf8-a8b3-54bd-8469-0f05f9d41e57
```

## Canonical admission binding

The admission artifact records the resolved operation, mission family, title,
purpose, expected outcome, scope, exclusions, dependencies, WOP revision,
package path and digest, immutable-manifest reference, repository and
baselines, submission, work-item declaration, submitter, principal, authority,
approval, lifecycle authorization, mode, dispatch permission, and next action.
The WOP package is validated in place and its published identity is preserved.
Missing contract, package, digest, WOP identity, or baseline binding fails
closed with the exact field-level diagnostic. A missing approval fails closed
only when the submitted WOP explicitly declares an approval gate.

## Operational workflow

Operational admission uses only mission, work-item, and principal selectors.
The production principal selector is `loneal`:

```text
scripts/zeus admit-mission start \
  --mode operational \
  --intent "Prepare a supervised operational WOP" \
  --mission EMP-MISSION-ID \
  --work-item EMP-WORK-ID \
  --principal loneal \
  --repository /data/engineering/repositories/homelab

For a published mission, qualification and operational admission consume the
same canonical binding. Mode changes only approval/dispatch eligibility; they
do not change mission identity, WOP identity, scope, authority, repository, or
baseline.
```

For a manually submitted Governance WOP, failed repository identity,
repository integrity, or package integrity produces a structured objective
execution blocker while Mission Status remains `ADMITTED`. Other
execution-safety facts are evaluated after admission during activation,
Mission Contract resolution, and execution verification. A later
execution-verification failure does not reverse the recorded admission or
recast those safety checks as a second operator authority grant.
For Operational Alpha, `dispatch_permitted` is resolved only from the published
convergence receipt: an exact EMM-bound submitted WOP and published
Operational Gate Plan. Progressive PMCT, legacy authority publication,
baseline-bound production dispatcher activation, and legacy agent qualification
remain compatibility or historical qualification capabilities; they are not
Operational Alpha admission inputs. Every failed convergence prerequisite is
retained as a reason-coded blocker.

Production authority was commissioned by ZEUS-P2-014 through the separate
publication interface. This admission implementation never changes any
`operationally_configured` switch.

## Interruption, resume, and diagnostics

```text
scripts/zeus admit-mission status --admission-id ADMISSION-ID
scripts/zeus admit-mission resume --admission-id ADMISSION-ID
```

The standalone `scripts/mission-admissionctl` exposes the same interface.
Repository and authority-source overrides are test-only and require
`ZEUS_TESTING=1`.

Failure categories distinguish request validation, repository verification,
package integrity, and later execution-verification blockers. Diagnostics
retain the underlying subsystem report. Execution agents do not perform
discretionary admission policy interpretation.

If a state digest fails, preserve the record for investigation and restore a
verified whole-record copy. Do not edit stages or digests by hand. Resume a
blocked admission only after its prerequisite changes.

## Controlled-document disposition

This guide records implemented repository behavior. It neither changes
controlled approval authority nor adopts a Governance procedure.
