# Zeus Mission Admission Runtime

The production operator is Lawrence O'Neal, authenticated as `loneal`.
Operational admission verifies signed operator-owned authority records; it
does not seek a second human approver. Zeus remains unable to originate an
approval or bypass admission policy.

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

Every completed stage records structured, digest-bound evidence. A transition
occurs only after the current stage completes. `BLOCKED` preserves the failed
stage and diagnostics; `INTERRUPTED` preserves the next stage. Resume skips
completed stages, retries only the current incomplete stage, and returns an
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

Before resolving authority, the coordinator reads publication commissioning
and owner-enrollment assessments, then invokes the Authority Resolution
Runtime against the repository-fixed source. Missing enrollment, publication,
operator approval, identity, baseline, or authority state produces a structured blocker
and no WOP. An accepted result means only eligibility for separately
controlled submission; `automatically_submitted` and `dispatch_permitted`
remain false.

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
mission qualification, enrollment, publication readiness, authority
resolution, WOP generation, and admission policy. Diagnostics retain the
underlying subsystem report.

If a state digest fails, preserve the record for investigation and restore a
verified whole-record copy. Do not edit stages or digests by hand. Resume a
blocked admission only after its prerequisite changes.

## Controlled-document disposition

This guide records implemented repository behavior. It neither changes
controlled approval authority nor adopts a Governance procedure.
