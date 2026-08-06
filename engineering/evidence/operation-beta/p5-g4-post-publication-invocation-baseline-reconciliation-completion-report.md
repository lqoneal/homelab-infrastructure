# P5-G4 Post-Publication Invocation Baseline Reconciliation

## Completion report

The published P5-G4 invocation remained immutable and was reconciled without
recreating the provider invocation, contacting the provider, or changing the
execution boundary.

Root cause: invocation verification compared the immutable invocation
provenance baseline directly with the current publication and returned
`INVOCATION_STALE` after P5-G4 publication. The shared canonical baseline
resolver now distinguishes provenance, current publication, repository
identity, and their relationship. `IDENTICAL` and `ANCESTOR` are valid only
after repository/runtime parity and all invocation-critical bindings pass.

Authority is resolved from the published authority chain; provider-session or
invocation artifacts are not treated as authority sources. The runtime has no
WOP provenance marker.

## Baseline resolution

```text
PUBLISHED_BASELINE=ae0395e62a5409e245912eb979a924bb9cb08e8c
INVOCATION_PROVENANCE_BASELINE=b37a5fb2e11df8026afeff1bd231902cd54711ac
BASELINE_RELATIONSHIP=ANCESTOR
CANONICAL_BASELINE_RESOLUTION=PASS
REPOSITORY_IDENTITY=PASS
RUNTIME_IDENTITY=PASS
PUBLICATION_PARITY=PASS
EOS_PARITY=PASS
```

The invocation ID remains
`PROVIDER-INVOCATION-a02accc6-3ff0-50d2-a4b2-266ca5b51ff6`. Its seven
artifact digests are unchanged. Mission, provider session, provider,
dispatch, execution package, execution authority, Mission Contract,
repository/runtime identity, acknowledgement, and invocation contract
bindings all pass.

## Verification evidence

```text
P5_G4_POST_PUBLICATION_INVOCATION_BASELINE_RECONCILIATION_COMPLETE
P5_G4_PUBLICATION=PRESERVED
PUBLISHED_BASELINE=ae0395e62a5409e245912eb979a924bb9cb08e8c
INVOCATION_PROVENANCE_BASELINE=b37a5fb2e11df8026afeff1bd231902cd54711ac
BASELINE_RELATIONSHIP=ANCESTOR
CANONICAL_BASELINE_RESOLUTION=PASS
PROVIDER_INVOCATION_VERIFICATION=PASS
MISSION_VERIFICATION=PASS
PUBLICATION_VERIFICATION=PASS
INVOCATION_INTEGRITY=PASS
PROVIDER_INVOCATION_REPLAY=IDEMPOTENT
PROVIDER_CONTACTED_AGAIN=NO
EXECUTION_STARTED=NO
MISSION_WORK_STARTED=NO
BLOCKERS=[]
NEXT_ACTION=START_EXECUTION
PUBLICATION=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
STOP_BOUNDARY=REACHED
```

The read-only Zeus commands reported invocation and mission verification
`PASS`; the publication verifier reported candidate scope, platform,
registry, integrated validation, stage verification, and projection schemas
`PASS`. Because the corrective is intentionally uncommitted, publication
status is `READY_TO_PUBLISH`; the published baseline itself remains
`ae0395e…` and was not amended or republished.

Focused regressions passed for provider invocation, canonical baseline
resolution, mission verification, provider session, and runtime discovery.
No provider process was contacted, no execution artifact was created, and no
runtime invocation artifact was modified.

## Changed-file inventory

```text
engineering/docs/cli/ZEUS-USER-GUIDE.md
engineering/evidence/operation-beta/p5-g4-post-publication-invocation-baseline-reconciliation-completion-report.md
scripts/lib/emp/canonical_runtime_mission.py
scripts/lib/emp/mission_verification_controller.py
scripts/lib/emp/provider_invocation.py
scripts/lib/emp/publication_workflow.py
scripts/lib/eos/canonical_baseline.py
scripts/zeus
scripts/tests/test-zeus-canonical-baseline-resolution.py
scripts/tests/test-zeus-p5-g4-provider-invocation.py
```

No commit, push, publication, or EOS synchronization was performed.

Terminal state: `AWAITING_OPERATOR_REVIEW`.
