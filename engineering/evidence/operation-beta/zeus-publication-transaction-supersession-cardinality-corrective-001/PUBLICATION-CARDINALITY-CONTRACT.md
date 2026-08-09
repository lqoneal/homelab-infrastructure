# Publication Cardinality Contract

For one repository-bound Mission/WOP, canonical resolution produces zero or
one current transaction. A single open lineage tip is current. If no open tip
exists, one qualified terminal tip may be returned as the completed-publication
fallback. Failed and aborted records are historical and do not retire another
transaction.

An open transaction outranks terminal-qualified history by lifecycle class,
not time. Multiple unrelated open tips or multiple open sibling successors are
ambiguous and fail closed. The resolver reports dispositions without changing
records: `CURRENT`, `CURRENT_QUALIFIED`, `SUPERSEDED`,
`HISTORICAL_QUALIFIED`, `HISTORICAL`, `FAILED`, or `ABORTED`.

Selection uses immutable identities, Mission/WOP/repository bindings,
supersession edges, terminal state, and receipt integrity. It explicitly
reports `timestamp_ordering_used=false`.
