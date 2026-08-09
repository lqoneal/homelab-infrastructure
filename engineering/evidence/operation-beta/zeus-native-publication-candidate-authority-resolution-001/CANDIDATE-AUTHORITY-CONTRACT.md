# Candidate authority contract

The current source chain is:

`live Mission/WOP projection -> qualified work/evidence package -> publication
manifest -> source/path traceability -> current Git/EOS publication lineage`.

Each source is classified as `QUALIFIED_UNPUBLISHED`, `QUALIFIED_DEPENDENCY`,
`ALREADY_PUBLISHED`, `HISTORICAL_ONLY`, `SUPERSEDED`, `UNRELATED`,
`AMBIGUOUS`, `BLOCKED`, or `INVALID` as applicable. Only qualified unpublished
sources with a valid exact Mission/WOP binding can contribute current paths.

Multiple compatible sources are unioned and retained in path traceability.
Conflicting current identity/intent, missing dependencies, missing files, and
unresolved qualification fail closed. A path selected for publication always
has non-null authority and a source ID. Repeated resolution is deterministic.

The explicit-manifest fallback is bounded to isolated engineering/test flows.
It requires exact Mission and WOP identity and cannot override a contradictory
live projection.
