# Repository Qualification Report

## Scope

ZEUS-P2-027 was qualified from branch `main` at starting HEAD
`787367bf82976e28cf929878cd30eacfffcba7ff`. The qualified implementation is
identified non-self-referentially as the intentional P2-027 commit containing
this report. Preserved ZEUS-P2-019 artifacts and production authority runtime
content are outside the change set.

## Exact validation commands

```bash
python3 scripts/tests/test-mission-admission-runtime.py
python3 scripts/tests/test-zeus-next-action.py
python3 engineering/tests/zeus-operational-alpha/tests/test-state-protection.py
python3 engineering/tests/zeus-operational-alpha/tests/test-result-model.py
python3 scripts/tests/test-authority-publication.py
python3 scripts/tests/test-zeus-gate-approval.py
```

Results: PASS — respectively 6, 5, 6, 4, 19, and 30 tests.

```bash
for test_file in scripts/tests/test-*.py; do
  python3 "$test_file" || exit 1
done
```

Result: PASS — 29 Python test files, zero failures.

```bash
engineering/tests/zeus-operational-alpha/tests/run-tests.sh
scripts/engctl registry validate
python3 scripts/validate_controlled_documents.py
git diff --check
```

Results:

```text
PMCT_SELF_TEST_RESULT=PASS
WORK_REGISTRY=PASS objects=76
CONTROLLED_DOCUMENTS=PASS checks=2578 failures=0
GIT_DIFF_CHECK=PASS
```

The external Progressive WOP is verification-only for this corrective change:

```bash
cd /data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP
sha256sum -c MANIFEST.sha256
```

Result: PASS — every listed WOP file verified `OK`.

## Authority and lifecycle preservation

Qualification must retain:

```text
ACTIVE_PUBLICATION_ID=AUTHORITY-PUBLICATION-50d661ec-2776-4d7c-8ea4-f34db35367d5
PUBLISHED_BASELINE=787367bf82976e28cf929878cd30eacfffcba7ff
HISTORICAL_OA01_RECEIPT_SHA256=63034bf8bdd19d12b481e3848846d4b84310242ff86f7bdaf30ddc58fc4e99df
OPERATIONAL_DISPATCH=DISABLED
OA-02_ELIGIBILITY=BLOCKED
PROGRESSIVE_WOP=PAUSED
```

The active publication, pointer, historical receipt, prior transactions,
external WOP, and P2-019 artifacts are not modified by P2-027.
