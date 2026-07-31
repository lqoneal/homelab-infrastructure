# Metadata Validation Framework

Status: `PROPOSED — NON-AUTHORITATIVE`

| Rule family | Automated qualification rule | Failure disposition |
|---|---|---|
| entity completeness | all envelope and entity-specific required fields resolve | `INVALID` |
| identifier uniqueness | IDs and `(type,id,revision)` keys are unique; lineage does not fork unless policy permits | `CONFLICT` |
| ownership | one authoritative owner per fact; consumer is not implicit writer | `AMBIGUOUS_OWNER` |
| relationship integrity | producer/consumer exist; type, direction, lifecycle constraints match | `BROKEN_RELATIONSHIP` |
| sync eligibility | source current; contract has trigger, owner, verification, recovery | `INELIGIBLE_SYNC` |
| projection consistency | target manifest/output digest match valid closure | `DRIFTED` |
| graph integrity | required dependency graph acyclic; entities/artifacts reachable | `CYCLE`, `ORPHAN`, `UNREACHABLE` |
| deterministic generation | repeated canonical input has same output digest | `NONDETERMINISTIC_OUTPUT` |
| provenance/qualification | output declares EMM/generator/source versions and applicable qualification | `UNQUALIFIED_PROJECTION` |

Validation precedes generated-artifact qualification. A generated-document failure traces to its entity, relationship, or manifest and is not fixed by editing the generated output.
