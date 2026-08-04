# Admission Supersession Contract

Supersession is internal baseline reconciliation, not a new authority decision, WOP submission, transaction, approval, or operator step. The successor ID is deterministic from transaction ID, current baseline, package digest, and authority snapshot digest.

The predecessor is marked `SUPERSEDED` with `superseded_by`; the successor records `supersedes`, the stable transaction, current baseline, package/source digests, authority snapshot, and one immutable supersession receipt.
