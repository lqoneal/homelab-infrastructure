# Live Projection Audit

| Operand | Source | Result |
|---|---|---|
| repository identity | live repository identity resolver and remote | PASS |
| current HEAD | `git rev-parse HEAD` | `0e8138004629acd13757ad8189733633293aa99d` |
| origin baseline | `git rev-parse origin/main` | same as HEAD |
| EOS baseline | EOS state/manifest projection | same as HEAD |
| provenance baseline | immutable P3 admission receipt | `7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c` |
| mission/WOP/receipt identities | P2/P3/P4 canonical records | PASS |
| current lifecycle state | canonical P4 projection | `AWAITING_EXECUTION_DISPATCH` |

Current baseline is not supplied as a corrective literal. The only literal
commit values in tests are historical vectors used to prove ancestry; they are
not runtime authority. A live projection conflict overrides any fallback and
fails closed.
