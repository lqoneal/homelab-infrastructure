# Zeus Postpublication Verification Routing Corrective

Date: 2026-08-09

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`

WOP: `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`

Publication: `PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda`

## Root cause

The publication transaction contract already mapped `EOS_SYNCHRONIZED` to
`VERIFY_POSTPUBLICATION_STATE`, and `publication_transaction.verify()` already
implemented the postpublication branch with `postpublication=True`. The Zeus
parser omitted a postpublication action and the dispatch table routed both
`verify` and `verify-pre` to the prepublication branch. Consequently the
advertised next action had no executable canonical CLI mapping, while the
prepublication branch correctly rejected `EOS_SYNCHRONIZED`.

## Corrective

The canonical command is:

```text
scripts/zeus publication verify-post <PUBLICATION_ID> --json
```

It delegates to the existing publication transaction owner with
`postpublication=True`. `verify` and `verify-pre` remain prepublication-only;
no competing lifecycle mechanism was added.

## Regression evidence

Focused routing suite:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/tests/test-zeus-postpublication-verification-routing.py -v
Ran 4 tests in 1.080s
OK
```

The suite proves successful EOS-to-postpublication transition, receipt
persistence, next-action advancement, premature fail-closed behavior,
prepublication-route separation, idempotent replay, and qualification ordering.

Directly affected suites also passed:

- `test-zeus-publication-transaction.py`: 11 tests;
- `test-zeus-publication-transaction-cohort-revalidation.py`: 8 tests;
- `test-zeus-authorized-publication-transition-baseline.py`: 12 tests;
- `test-zeus-repository-projection.py`: 9 tests;
- `py_compile` and `git diff --check`;
- controlled-document semantic/conformance/assurance validation: 3,808 checks, 0 failures.

## Existing transaction recovery

The existing publication was advanced only through the repaired Zeus-native
CLI. No transaction file, receipt, Git ref, or EOS state was manually edited.

Command:

```text
scripts/zeus --runtime-root /home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57 publication verify-post PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda --json
```

Observed result:

```text
result=PASS
current_state=POSTPUBLICATION_VERIFIED
postpublication_result=PASS
next_authorized_action=QUALIFY_PUBLICATION
blockers=[]
transaction_integrity=PASS
```

The durable postpublication receipt is recorded by the transaction at:

```text
/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57/publication-receipts/PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda/POSTPUBLICATION_VERIFIED.json
```

Qualification was intentionally not run. The normal review/publication
boundary is therefore preserved, with `QUALIFY_PUBLICATION` as the next
authorized action.

## Worktree boundary

The repository had substantial unrelated tracked and untracked changes before
this corrective. They were inventoried and preserved. No reset, clean, stash,
overwrite, commit, push, or EOS synchronization was performed by this
corrective.
