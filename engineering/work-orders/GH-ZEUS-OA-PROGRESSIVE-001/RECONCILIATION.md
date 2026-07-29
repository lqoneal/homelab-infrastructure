# Progressive OA Reconciliation Procedure

At package preflight and after every gate, compare the repository HEAD and
working tree, active authority publication, Zeus mission/execution/gate state,
EMP lifecycle, PMCT state, EENS events, Project State, Work Registry, EOS
projection, controlled-document revisions, evidence manifests, and operator
receipts.

There must be exactly one active gate; its predecessor (if any) must have a
valid acceptance receipt; no successor may show execution effects. Completion
and acceptance remain distinct. Stop on ambiguity or conflict, preserve both
observations, and create a recovery or corrective proposal. Synchronize EOS
only through `scripts/engctl eos synchronize`; never hand-edit EOS projections.
