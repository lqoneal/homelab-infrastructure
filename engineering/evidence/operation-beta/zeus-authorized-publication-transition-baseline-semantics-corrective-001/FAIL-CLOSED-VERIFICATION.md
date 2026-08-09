# Fail-Closed Verification

Isolated fixtures prove rejection of:

- local HEAD ahead without a publication transaction;
- HEAD differing from the transaction commit;
- a missing `COMMIT_CREATED` or `REMOTE_PUBLISHED` receipt;
- invalid transaction state/next-action integrity;
- unrelated mission or WOP binding;
- wrong repository/runtime identity;
- EOS movement before the matching transaction milestone;
- remote or fully converged movement unsupported by the current receipt; and
- contradictory transaction cardinality or lineage.

The resolver requires authoritative state and receipt digests. Git ancestry is
necessary where applicable but never sufficient.

