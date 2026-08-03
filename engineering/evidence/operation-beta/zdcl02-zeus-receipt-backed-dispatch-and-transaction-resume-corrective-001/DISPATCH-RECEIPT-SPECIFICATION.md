# Dispatch Receipt Specification

Dispatch receipts require receipt identity and digest, transaction/WOP/package identity, repository, provider, agent, qualification ID, registry digest, selection policy, dispatch-plan digest, predecessor, and authority-snapshot digest. The lifecycle guard validates these fields before exposing `DISPATCHED`.
