# Publication Candidate Manifest

Publication, commit, push, and EOS synchronization were not performed.

Candidate files:

1. `scripts/lib/emp/submission_boundary.py` — only the Wave 1 `mission_view`
   receipt-validation and common-projection hunks; preserve all unrelated
   pre-existing modifications.
2. `scripts/zeus` — only the P2 mission action-set hunk adding `readiness` and
   `eligibility`; preserve all unrelated modifications.
3. `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`.
4. `scripts/tests/test-zeus-wave1-canonical-read-model.py`.
5. `engineering/planning/ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001.md` — only
   GAP-001/GAP-006 status changes.
6. All files in this evidence directory.

The prior submission-canonicalization and CAGF-01 candidates require separate
operator review. All other dirty paths remain excluded.

`PUBLICATION_CANDIDATE=WAVE1_READY_FOR_OPERATOR_REVIEW`
