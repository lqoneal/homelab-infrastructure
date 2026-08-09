# Publication Candidate Manifest

Candidate: Zeus publication stage atomicity corrective

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`

WOP: `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`

Scope: separate candidate staging from staged-set verification, bind the
staged digest to index blobs, and add exact-index interruption recovery.

## Exact candidate paths

- `scripts/lib/emp/publication_transaction.py`
- `scripts/zeus`
- `scripts/tests/test-zeus-publication-transaction.py`
- `scripts/tests/test-zeus-postpublication-verification-routing.py`
- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/docs/operations/ZEUS-CANONICAL-MISSION-PUBLICATION-PROCEDURE.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/STARTING-STATE.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/ROOT-CAUSE-ANALYSIS.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/IMPLEMENTATION-REPORT.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/FAIL-CLOSED-VERIFICATION.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/TEST-RESULTS.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/LIVE-ACCEPTANCE.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/COMPLETION-REPORT.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/PUBLICATION-CANDIDATE-MANIFEST.md`
- `engineering/evidence/operation-beta/zeus-publication-stage-atomicity-corrective-001/QUALIFICATION-PUBLICATION-STATE.json`

## Boundary

This candidate is qualified for operator review and has not been staged,
committed, pushed, synchronized, or published. The pre-existing live staged
index is a separate frozen publication candidate and remains unchanged.
