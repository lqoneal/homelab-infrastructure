# Implementation Report

The canonical transaction owner now:

- derives staged paths directly from the index delta;
- derives the staged digest from stage-zero index blob bytes;
- requires exact candidate paths and the frozen candidate digest;
- records only `CANDIDATE_STAGED` from `publication stage`;
- exposes `publication verify-staged` as the distinct transition to
  `STAGED_SET_VERIFIED`;
- permits replay from `PREPUBLICATION_VERIFIED` only when the already-staged
  index exactly reproduces the frozen candidate;
- rejects partial, extra, changed, conflicting, or ambiguous recovery state;
- revalidates staged-state status and commit authority against the index rather
  than mutable worktree bytes;
- validates transaction integrity before stage replay, staged verification,
  and commit.

`publication run` and approved `publication resume` route through the explicit
staged verification transition. The CLI guide and canonical publication
procedure document the same boundary and digest semantics.
