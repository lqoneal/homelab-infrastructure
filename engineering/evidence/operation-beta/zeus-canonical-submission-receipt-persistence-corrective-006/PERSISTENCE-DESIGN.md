# Persistence Design and Defect Classification

## Defect

Automatic canonicalization was executed with an explicitly selected temporary
runtime. P2 submission receipts and admission-request projections were valid,
but the temporary runtime was never promoted into the existing repository-bound
user-state runtime. Default Zeus discovery therefore saw no lifecycle mission.

## Existing architecture used

- Durable root: `/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57`
- Transaction root: the explicitly selected temporary runtime
- Adoption boundary: `scripts/zeus runtime adopt --source <TEMP_RUNTIME>`
- Implementation: `scripts/lib/emp/runtime_adoption.py`

Canonical adoption validates the runtime identity marker, repository identity,
each P2 receipt/request pair through the existing read-only P2 resolver, and
the Mission/WOP/source/package identity chain. It copies only the receipt and
request artifacts selected by that validation. The durable runtime retains
historical records and cannot use them to override the current canonical chain.

The adoption identity is content-bound to repository fingerprint and selected
receipt/request digests, not to the temporary directory name. A staged runtime
directory is atomically swapped into place under the existing adoption lock.
The manifest is adoption metadata; the P2 receipt remains the authoritative
lifecycle evidence.
