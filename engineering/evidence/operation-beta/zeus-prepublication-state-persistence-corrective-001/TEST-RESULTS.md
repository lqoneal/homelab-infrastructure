# Test Results

Focused isolated qualification covers durable PASS persistence, receipt and
transaction binding, fresh reload, authority ordering before/after persistence,
failure, simulated persistence failure, orphan receipt behavior, forged
receipt behavior, idempotent replay, status/mission agreement, cohort and
candidate preservation, unrelated-file isolation, and zero index mutation.

Recorded results:

- directly affected publication/mission/repository/Beta suites: PASS, 48 tests;
- publication transaction plus cohort-revalidation focused suites: PASS, 19 tests;
- controlled-document semantic-all/conformance/assurance validation: PASS;
- registry validation: PASS;
- integrated `engctl validate homelab`: PASS;
- Python compilation: PASS;
- `git diff --check`: PASS;
- repository/EOS sync validation: PASS;
- Zeus platform validation: PASS.

The broader pre-existing controlled-document semantic unit suite reports 56
PASS and one unrelated FAIL. Its dirty-tree test expects
`GH-ZEUS-OA-PROGRESSIVE-001/ROADMAP.md` to remain a current scan target, while
the separately pre-existing dirty implementation in
`scripts/validate_controlled_documents.py` classifies every work-order
`roadmap.md` as generated/historical. This corrective did not modify either
path. The canonical semantic-all validation itself passes.

All mutation-bearing tests use temporary repositories and runtime roots. They
do not stage, commit, push, synchronize, qualify, or execute the live mission.
