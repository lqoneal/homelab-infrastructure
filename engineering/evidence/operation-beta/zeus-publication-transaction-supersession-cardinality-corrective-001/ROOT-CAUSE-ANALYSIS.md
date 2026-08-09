# Root Cause Analysis

The canonical owner was split inside the publication transaction model.
`publication_transaction.prepare()` discarded `PUBLICATION_QUALIFIED` records
before selecting a predecessor. Mission lookup called
`publication_authority.active_transactions()` with qualified records included.
The two paths therefore used different definitions of current authority.

At the live baseline, qualified
`PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda` and fresh
`PUBLICATION-bd7546d2-377f-569a-9530-f07999ba12b2` both linked to
`PUBLICATION-35b59c05-31bb-5d45-a7fc-4934c33b6496`. Prepare had selected the
nonterminal predecessor after filtering out the qualified tip. The former
resolver then treated the qualified transaction and fresh transaction as two
unsuperseded tips and stopped at cardinality conflict.

The defect was not CLI routing, candidate/cohort authority, transaction-file
persistence, receipt persistence, or timestamp ordering. It was inconsistent
terminal-state filtering and predecessor/current selection, compounded by a
shared resolver that did not validate missing/cross-scope targets, cycles,
duplicate identities, or incompatible sibling successors.

The corrective centralizes selection in
`publication_authority.resolve_transaction_lineage()`. Qualified publication is
terminal history while an open transaction exists and is only the completed
publication fallback when no open transaction exists. Prepare and mission
status now consume that same graph authority.
