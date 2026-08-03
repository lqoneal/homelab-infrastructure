# Identity Field Semantic Mapping

| WOP value | Resolution | Consumer |
|---|---|---|
| `homelab` | path-derived alias | authoring/validation/Stage 1 |
| canonical path | exact resolved path | all lifecycle consumers |
| remote locator | normalized comparison | validation/diagnostics |
| repository ID | exact runtime binding value | validation/diagnostics |
| fingerprint | exact runtime binding value | validation/diagnostics |

All accepted forms converge to one canonical path; no duplicate authority is
created.
