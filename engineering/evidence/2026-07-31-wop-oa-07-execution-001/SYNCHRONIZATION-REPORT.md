# OA-07 Synchronization Report

Authoritative records reconciled: Mission Knowledge Model, Capability Registry,
OA-07 WOP, Authority Record, Gate Plan, Activation Record, lifecycle transition,
EOS projection, Registry, and EMM source digests.

Before publication, EOS reported drift for the newly reconciled authoritative
records. Synchronization is required before the publication commit; no acceptance
receipt is created until `scripts/engctl eos sync-validate` returns PASS.
