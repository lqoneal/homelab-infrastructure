# Baseline State Matrix

| State | HEAD | origin/main | EOS | Required receipt | Result |
| --- | --- | --- | --- | --- | --- |
| steady | published | published | published | none | PASS |
| arbitrary local ahead | unrelated commit | prior | prior | none | FAIL |
| COMMIT_CREATED | transaction commit | starting baseline | starting baseline | COMMIT_CREATED | PASS |
| REMOTE_PUBLISHED | transaction commit | transaction commit | starting baseline | REMOTE_PUBLISHED | PASS |
| EOS_SYNCHRONIZED | transaction commit | transaction commit | transaction commit | EOS_SYNCHRONIZED | PASS |
| wrong commit/identity/mission/WOP | any | any | any | contradictory | FAIL |
| missing or invalid current receipt | any divergent topology | any | any | missing/invalid | FAIL |

Raw parity remains observable. Transitional `repository_valid=true` does not
change `head_origin_parity` or `eos_parity` to values that have not yet been
achieved.

