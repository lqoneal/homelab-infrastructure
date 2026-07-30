# PU-01C Boundary Determinism Report

Date: 2026-07-29

Result: `PASS`

The inventory is ordered by repository-relative path. Every digest is SHA-256
over the current path bytes. The aggregate is SHA-256 over ordered UTF-8 lines
of the form `<sha256>  <path>\n`.

Two independent reads of all 140 included paths produced identical per-path
digests, identical path order, and identical aggregate digest:

`7c9b3ce14b8d6d864b8e3a8a149155995e52c3fcd2f867e2de0319a50d9048e5`

The current qualification fingerprint remains unchanged:

`b171bec8ae27eb25f2f4c10f5eb0bad88860b69aed11eed1f3d2087143e19d61`
