# Execution Artifact Ownership Matrix

| Artifact | Classification | Authoritative owner | Lifecycle | Synchronization / generation | Consumer |
| --- | --- | --- | --- | --- | --- |
| Authority Record | Authoritative | Governance | controlled Authority Record lifecycle | EMM read-only resolution | Metadata Engine / Zeus |
| Implementation WOP | Authoritative | Assigned WOP owner | `DRAFT` through `CLOSED` | indexed by EMM | Convergence resolver |
| Operational Execution Contract | Authoritative | Homelab Infrastructure | `READY` contract availability | source → EMM identity → derived context | Metadata Engine / Zeus |
| Operational Gate Plan | Authoritative | Assigned WOP owner | `ACTIVE` only when eligible for resolution | published source → EMM entity → derived context | Zeus operational gate handler |
| Resolution receipt | Derived | Metadata Engine | expires with input | deterministic resolver output | Zeus, qualification, EOS/EENS projections |
| Handler context | Derived / ephemeral | Zeus | invocation only | assembled from receipt and plan; never persisted as source | `zeus.operational.artifact` |
| EOS/EENS/EMP projections | Derived / runtime | respective projection owner | projection lifecycle | directional from resolution receipt | operational observability |

There is one owner per authoritative artifact. The Operational Gate Plan is intentionally absent for OA-01; no fallback owner or compatibility projection is permitted.
