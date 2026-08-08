# Publication Candidate Manifest

Do not publish, stage, commit, push, or synchronize EOS from this handoff.

Wave-specific candidate paths:

1. `scripts/lib/emp/canonical_lifecycle_resolver.py` — new canonical
   receipt-chain read-only resolver.
2. `scripts/tests/test-zeus-wave1-canonical-lifecycle-resolver.py` — focused
   GAP-002 positive, negative, replay, identity, and compatibility tests.
3. `scripts/zeus` — route canonical mission read surfaces through the common
   resolver; preserve pre-existing unrelated hunks.
4. `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md` —
   current P2/P3/P4 projection contract; preserve pre-existing hunks.
5. `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md` — current
   package preference and chain documentation; preserve pre-existing hunks.
6. `engineering/docs/operations/ZEUS-WOP-AUTHORING-GUIDE.md` — current CLI
   artifact guidance; preserve pre-existing hunks.
7. `engineering/planning/ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001.md` — GAP-002
   status advancement and bounded continuation note; preserve other planning
   content.
8. This evidence directory.

Pre-existing dirty runtime, documentation, CAGF-01, submission-canonicalization,
and evidence artifacts remain preserved and are not part of this exact
candidate unless separately isolated by the operator.
