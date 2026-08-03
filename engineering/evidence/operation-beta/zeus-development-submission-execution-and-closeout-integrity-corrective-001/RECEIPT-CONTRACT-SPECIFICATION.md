# Receipt Contract Specification

Receipt-backed Development records use `lifecycle_integrity:
RECEIPT_BACKED_V1`. Each receipt is immutable, digest-bound, and keyed by a
deterministic receipt identity.

| Receipt | Minimum binding |
| --- | --- |
| validation | source/digest, validator, result, failures |
| packaging | package identity/digest, source digest, transactional result |
| registration | registration identity, WOP, package digest, repository baseline |
| authorization | authority, decision, effect profile, repository, protected baselines |
| admission | admission identity, WOP, execution mode, executor requirements |
| dispatch | qualified agent, execution contract, package identity |
| execution | execution identity, agent, timestamps, exit status, evidence |
| independent verification | authority, requirement results, evidence digests, result |
| publication | publication identity, reviewed boundary, reference, branch |
| synchronization | repository commit, EOS checkpoint/manifest, validation result |
| closeout | predecessor identities, final state, blockers, report digest |

The persisted phase list is validated against the receipt keys on load. A
receipt-backed state cannot claim `EXECUTING`, `QUALIFIED`, publication,
`SYNCHRONIZED`, or `CLOSED` without its required receipts.
