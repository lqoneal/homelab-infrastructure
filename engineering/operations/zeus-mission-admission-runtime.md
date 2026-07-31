# Zeus Mission Admission Runtime

Admission is a required Controlled Mission Authority input, not standing
execution authority. Every protected execution boundary independently
revalidates the integrity-bound admission receipt together with the current
Mission Contract, WOP, repository, predecessor receipt, and active gate.
Missing or invalid admission remains admitted only as a governance fact and
cannot dispatch execution or produce protected effects.

The production operator is Lawrence O'Neal, authenticated as `loneal`.
Operational admission verifies signed operator-owned authority records; it
does not seek a second human approver. Zeus remains unable to originate an
approval or bypass admission policy.

Under the current temporary Governance operating directive, Engineering
Governance is the sole Mission Admission Authority. Manual WOP submission by
Engineering Governance is intentional submission and admission. The runtime's
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

Qualification uses the same seven-stage coordinator and WOP interface. At the
authority stage it creates an explicitly non-operational placeholder context
inside the runtime. The WOP remains `review_required`, is never automatically
submitted, and ends with `QUALIFICATION_ONLY`, not operational admission.

```text
scripts/zeus admit-mission start \
  --mode qualification \
  --intent "Qualification intent" \
  --mission ZEUS-QUALIFICATION \
  --phase MISSION-ADMISSION \
  --repository /data/engineering/repositories/homelab
```

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
```

For a manually submitted Governance WOP, failed repository identity,
repository integrity, or package integrity produces a structured objective
execution blocker while Mission Status remains `ADMITTED`. Other
execution-authority facts are evaluated after admission during activation,
Mission Contract resolution, and execution verification. A later
execution-verification failure does not reverse the recorded admission.
For Operational Alpha, `dispatch_permitted` is resolved only from the published
convergence authority receipt: an exact EMM-bound Implementation WOP, applicable
Authority Record or allowlisted Manual-Governance Root WOP, and published
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
