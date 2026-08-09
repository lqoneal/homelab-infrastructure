# Root Cause Analysis

## Confirmed defect

The live invocation eventually persisted both staging receipts, but code and
focused interruption testing proved a canonical staging defect.

`publication_transaction.stage()` crossed two lifecycle milestones in one
call. After `git add`, it compared only path names, calculated
`staged_tree_digest` from worktree files, wrote `CANDIDATE_STAGED`, and
immediately wrote `STAGED_SET_VERIFIED`. A successful stage therefore returned
`STAGED_SET_VERIFIED -> COMMIT_PUBLICATION`, not the authoritative
`CANDIDATE_STAGED -> VERIFY_STAGED_SET` boundary.

The external mutation/persistence failure boundary was between `git add` and
the first milestone persistence. If interrupted there, the index contained the
exact candidate while the transaction remained `PREPUBLICATION_VERIFIED`.
Replay rejected every non-empty index before proving whether it was the exact
authorized mutation, so safe recovery was impossible.

The old digest also read worktree bytes after staging. It did not establish
that the bytes represented by the Git index matched the frozen candidate.

## Digest distinction

The raw Git tree is a Git SHA-1 object identifier over Git tree encoding. Zeus
uses SHA-256 over canonical JSON. The canonical staged representation is the
sorted array of `{path, sha256}` records, where the inner SHA-256 is computed
from each stage-zero index blob. The outer SHA-256 is computed over compact,
key-sorted UTF-8 JSON. These digests are intentionally not comparable as object
identifiers.
