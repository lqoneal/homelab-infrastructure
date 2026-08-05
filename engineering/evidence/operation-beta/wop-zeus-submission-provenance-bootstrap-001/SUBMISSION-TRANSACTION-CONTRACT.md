# Submission Transaction Contract

The transaction is deterministic over WOP identity, mission identity, source digest, repository, branch, baseline, execution mode, and effect profile. The transaction envelope is persisted with the existing receipt-backed Stage-1 record. Invalid source, authority, repository, baseline, or digest fails closed.
