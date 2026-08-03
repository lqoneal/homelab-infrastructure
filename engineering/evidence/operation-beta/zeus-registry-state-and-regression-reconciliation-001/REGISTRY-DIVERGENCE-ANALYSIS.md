# Registry Divergence Analysis

| Mismatch | Evidence | Disposition |
|---|---|---|
| OA-06 vs OA-08 | live resolver returns OA-08; test expected OA-06 | stale fixture |
| 5 vs 30 capabilities | live registry lists 30; test expected 5 | stale fixture |
| registry digest | candidate digest recomputes exactly | no divergence |
| execution-agent registry | one qualified candidate selected deterministically | candidate-only publication gap |

No valid current state was altered.
