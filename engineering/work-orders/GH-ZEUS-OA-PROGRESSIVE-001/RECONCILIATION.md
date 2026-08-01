# Progressive OA Reconciliation Procedure

At package preflight and after every gate, compare the repository HEAD and
working tree, active authority publication, Zeus mission/execution/gate state,
EMP lifecycle, PMCT state, EENS events, Project State, Work Registry, EOS
projection, controlled-document revisions, evidence manifests, and operator
receipts.

Each gate is independently completed and validated before publication. Under
the default Operational Alpha capability-pair policy, publication is deferred
until two consecutive authorized gates have completed. The local Engineering
Platform state, qualification evidence, reconciliation state, and lifecycle
receipts remain authoritative during that interval. Pair publication must
contain both complete gates and may not publish a partial bundle. Repeat the
full validation at the pair publication boundary.

There must be exactly one active gate; its predecessor (if any) must have a
valid acceptance receipt; no successor may show execution effects. Completion
and acceptance remain distinct. Stop on ambiguity or conflict, preserve both
observations, and create a recovery or corrective proposal. Synchronize EOS
only through `scripts/engctl eos synchronize`; never hand-edit EOS projections.
