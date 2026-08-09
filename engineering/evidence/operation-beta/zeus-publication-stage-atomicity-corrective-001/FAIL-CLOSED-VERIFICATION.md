# Fail-Closed Verification

Focused tests prove rejection of:

- extra staged paths: `UNEXPECTED_STAGED_PATH`;
- missing candidate paths: `STAGED_CANDIDATE_PATH_MISSING`;
- changed staged blob bytes: `STAGED_CONTENT_MISMATCH`;
- persisted/receipt digest conflict: `STAGED_TREE_DIGEST_MISMATCH`;
- noncanonical digest semantics:
  `STAGED_TREE_DIGEST_SEMANTICS_MISMATCH`;
- invalid transaction/receipt authority:
  `PUBLICATION_TRANSACTION_INTEGRITY_FAILURE` or the bounded
  `PREPUBLICATION_AUTHORITY_NOT_DURABLE` prepublication spelling;
- persistence evidence without the exact staged index:
  `AMBIGUOUS_STAGE_RECOVERY_STATE`;
- nonunique stage-zero entries: `AMBIGUOUS_STAGED_ENTRY`.

The interruption test forces transaction persistence failure after the exact
index mutation. The transaction remains `PREPUBLICATION_VERIFIED`; replay
reuses the immutable orphan receipt only after the index path/content digest
reproduces exactly, then stops at `CANDIDATE_STAGED -> VERIFY_STAGED_SET`.
