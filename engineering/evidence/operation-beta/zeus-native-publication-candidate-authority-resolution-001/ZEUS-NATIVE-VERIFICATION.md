# Zeus-native verification

The read-only `zeus publication inspect` surface now exposes the live
Mission/WOP-bound candidate authority, source records, exact paths, digests,
exclusions, and next action. `classify` and `prepare` use the same resolver;
they do not infer candidates independently.

Final actual-mission sequence:

- `publication inspect`: RC 0, authority PASS;
- `publication classify`: RC 0, authority PASS, 19 sources, 113 paths;
- `publication prepare`: RC 0, one durable publication transaction resolved;
- `publication status`: RC 0, `CANDIDATE_ISOLATED`, next
  `VERIFY_PREPUBLICATION`;
- `mission snapshot`: RC 0, Mission/WOP identity preserved, lifecycle state
  `AWAITING_EXECUTION_DISPATCH`, no blockers, publication state
  `CANDIDATE_ISOLATED`.

No staging, commit, push, EOS synchronization, or mission work is part of this
verification.
