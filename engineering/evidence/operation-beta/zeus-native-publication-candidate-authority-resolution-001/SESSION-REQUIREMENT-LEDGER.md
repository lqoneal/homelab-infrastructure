# Session requirement ledger

| Requirement | Status | Owner | Verification |
|---|---|---|---|
| Resolve candidates from live Mission/WOP projection | SATISFIED | `publication_candidate_authority.py` | actual `inspect`/resolver JSON |
| Use qualified multi-source manifests and dependencies | SATISFIED | candidate authority resolver | focused authority tests and source digest |
| Preserve historical/unrelated/dirty work | SATISFIED | resolver/controller | classification and repository projection |
| Exclude already-published paths | SATISFIED | candidate authority resolver | Git tree/diff projection test |
| Fail closed on ambiguity, missing paths, missing dependencies | SATISFIED | candidate authority resolver | focused negative tests |
| Preserve canonical repository projection | SATISFIED | repository projection consumer | repository projection regression |
| Integrate inspect/classify/prepare/status without a second controller | SATISFIED | publication transaction controller | CLI and transaction tests |
| Do not stage, commit, push, synchronize EOS, or start mission work | SATISFIED | operator boundary | index/EOS/native checks |
| Record lifecycle aggregate/managed-runtime divergence for follow-on work | SATISFIED | evidence package | `FOLLOW-ON-LIFECYCLE-DIVERGENCE.md` |
| Create durable transaction through shared runtime | SATISFIED | existing runtime owner | final `prepare`/`status` resolved one durable transaction through the repository-bound runtime |

Final ledger assertions:

```text
UNMAPPED_ACTIVE_REQUIREMENTS=0
UNEXPLAINED_SKIPPED_REQUIREMENTS=0
ALL_OPERATOR_SUBMISSIONS_ACCOUNTED_FOR=YES
```
