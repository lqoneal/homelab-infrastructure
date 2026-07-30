# PU-01C Publication Verification Report

Date: 2026-07-30

Result: `BLOCKED_FAIL_CLOSED`

Repository identity:

- root: `/data/engineering/repositories/homelab`
- remote: `git@github.com:lqoneal/homelab-infrastructure.git`
- branch: `main`
- upstream: `origin/main`
- HEAD: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`

The frozen 140-path boundary matches every recorded SHA-256 digest. Its
aggregate digest remains:

`7c9b3ce14b8d6d864b8e3a8a149155995e52c3fcd2f867e2de0319a50d9048e5`

The independent Governance Baseline qualification passed all 145 tests and
reproduced the accepted fingerprint:

`b171bec8ae27eb25f2f4c10f5eb0bad88860b69aed11eed1f3d2087143e19d61`

Publication cannot proceed because the authoritative Publication Plan 002
manifest remains `paused_after_PU-01A`. Its completed-unit ledger contains
only PU-01 and PU-01A. PU-01B is still `planned`, while PU-01C declares PU-01B
as its direct prerequisite.

PU-01B also owns the currently unpublished Publication Plan 002 and manifest.
Publishing PU-01C alone would therefore violate authoritative ordering and
would publish a baseline whose governing publication records are absent from
the committed prerequisite history.

No staging, publication commit, tag, push, or synchronization was performed.
