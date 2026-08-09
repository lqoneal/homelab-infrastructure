# Controller Architecture

The controller is implemented in `scripts/lib/emp/publication_transaction.py`.
It owns publication identity, candidate authority, frozen classification,
transaction state, immutable milestone receipts, blockers, replay, resume,
abort disposition, and postpublication qualification.

Git commit/push and EOS synchronization remain subordinate transition adapters.
The controller does not manufacture authority, Mission Contracts, or lifecycle
receipts. It binds the transaction to live repository projection and the
submitted mission/WOP projection where available.

Runtime records live under the repository-bound Zeus runtime:

- `publication-transactions/<PUBLICATION_ID>.json`
- `publication-classifications/<MISSION_ID>.json`
- `publication-receipts/<PUBLICATION_ID>/<MILESTONE>.json`

Each milestone receipt is immutable and replay checks its digest before reuse.
