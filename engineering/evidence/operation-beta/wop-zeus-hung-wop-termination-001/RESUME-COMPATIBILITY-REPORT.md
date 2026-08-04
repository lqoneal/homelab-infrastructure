# Resume Compatibility Report

Interrupted execution state is non-terminal and is accepted by the existing
resume path. Provider output cannot advance an interrupted execution because
`run` returns the persisted interrupted state until an explicit canonical
resume occurs. Resume preserves transaction and admission identity.
