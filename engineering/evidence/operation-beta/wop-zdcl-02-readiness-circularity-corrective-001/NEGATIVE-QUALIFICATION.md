# Negative Qualification

Disposable qualification preserves blocking behavior for:

- invalid dispatch receipt;
- missing required authority-chain receipts;
- repository working-tree drift;
- invalid publication binding;
- protected-baseline mutation;
- corrupted receipt and identity conflicts.

Provider and agent records are consumed only by resume's automatic executor;
readiness does not fabricate or persist provider, agent, snapshot, or dispatch
state.
