# BETA-02 Human/Machine Output Comparison

Human-readable output is rendered from the same dictionary emitted by JSON
mode. The reconciled surfaces include operation/list, Beta mission explain,
and Beta queue list/next/blockers/history.

| Invariant | Human | JSON |
| --- | --- | --- |
| active list | Beta missions only | same mission IDs and states |
| explain | mission, lifecycle, readiness, blockers, rationale, baselines | same fields |
| queue | scope, entries, metrics, integrity | same fields |
| history | completed missions only | same completed mission IDs |

Presentation does not query or mutate state independently.
