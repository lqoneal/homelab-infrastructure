# Hardcoding Audit

## Results

The affected runtime and documentation were searched for current mission IDs,
WOP IDs, repository baselines, runtime paths, lifecycle states, receipt
operands, provider/session identities, publication assumptions, and OA
selectors.

### Removed or replaced

- the strict admission/bootstrap comparison that treated the old receipt
  baseline as the current HEAD was replaced by live repository/EOS lineage;
- the hardcoded published baseline in
  `scripts/lib/emp/mission_verification_controller.py` was replaced by the
  live `origin/main` projection;
- current status routing no longer depends on a hardcoded OA selector or
  `active-publication.json`.

### Retained and justified

- lifecycle state labels such as `AWAITING_EXECUTION_DISPATCH` and
  `EVALUATE_EXECUTION_PROVIDER` are protocol enum values, not current-state
  authority;
- `/tmp` paths used for authoring/interface transaction workspaces are
  bounded workspace constants, not lifecycle runtime ownership;
- OA/Beta identifiers and protected baseline tags in planning/compatibility
  modules are historical or planning constants. They cannot override the
  canonical lifecycle resolver and are not used to generate the current
  reconciliation receipt.

Every retained fallback is documented as compatibility or protocol data and
must fail closed when it conflicts with a live canonical projection.

