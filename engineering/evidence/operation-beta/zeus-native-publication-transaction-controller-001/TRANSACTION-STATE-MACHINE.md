# Transaction State Machine

The durable milestone sequence is:

`PUBLICATION_DISCOVERED` → `WORKTREE_CLASSIFIED` → `CANDIDATE_RESOLVED` →
`CANDIDATE_ISOLATED` → `PREPUBLICATION_VERIFIED` → `CANDIDATE_STAGED` →
`STAGED_SET_VERIFIED` → `COMMIT_CREATED` → `REMOTE_PUBLISHED` →
`EOS_SYNCHRONIZED` → `POSTPUBLICATION_VERIFIED` → `PUBLICATION_QUALIFIED`.

Resume selects the next action from the last durable milestone. Commit, push,
and synchronization are not repeated after their receipts are valid. Abort
before remote publication preserves the transaction and worktree; abort never
rewrites published Git history.
