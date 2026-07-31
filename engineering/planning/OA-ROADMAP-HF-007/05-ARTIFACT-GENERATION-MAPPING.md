# Artifact Generation Mapping

Status: `PROPOSED — NON-AUTHORITATIVE`

| Generated artifact | EMM inputs | Process / trigger | Publication criteria | Verification |
|---|---|---|---|---|
| Gate Catalog generated sections | gate/artifact/relationship metadata, receipts | deterministic template; metadata revision | valid graph and source manifest | digest, links, owner coverage |
| Capability Matrix | objectives, capability metadata, qualification | matrix projection; source change | complete/current coverage | IDs and qualification applicability |
| Lifecycle Graph | state/transition/relationship metadata | directed graph build; model change | graph validates | acyclic/reachable |
| Dependency Matrix | gate/state prerequisite metadata | topological projection; dependency change | inputs/outputs declared | no orphan/ambiguous edge |
| Verification Guide index | verification metadata, canonical interface | command projection; interface change | all commands resolve | read-only contract check |
| Qualification Reports | evidence, criteria, qualification | render; sealed result | frozen independent subject | receipt/criterion completeness |
| Information Dependency Graph | artifact/synchronization metadata | graph build; metadata change | one source owner per fact | direction/trigger/verification coverage |
| Engineering Dashboards | runtime state, receipts, status metadata | view projection; event/checkpoint | freshness/provenance | source revision/drift status |

The generator receives a sorted canonical input manifest. Identical inputs and generator version produce identical outputs. Missing, stale, unqualified, or graph-invalid input blocks publication.
