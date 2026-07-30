# Second-Window Verification

From a fresh shell in the canonical root:

1. verify WOP manifest;
2. verify root/common-dir/remote/branch/worktree identity;
3. run schema and receipt-substitution tests;
4. run ARS/REAC, PMA, EWI, repository-topology, and projection tests;
5. run read-only authority preflight;
6. run non-dispatching EWI qualification only if all required legitimate
   inputs exist;
7. verify OA-06 did not transition and OA-07 remains ineligible;
8. compare evidence manifests and check `git diff --check`.

Do not fetch, push, activate authority, dispatch, or accept a gate as part of
second-window verification.

