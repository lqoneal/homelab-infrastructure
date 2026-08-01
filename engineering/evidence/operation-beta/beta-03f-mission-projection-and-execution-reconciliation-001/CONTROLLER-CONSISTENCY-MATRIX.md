# Controller Consistency Matrix

| Controller | Resolver | Current/history separation | Status |
|---|---|---|---|
| mission explain/status/show | canonical Beta mission projection | yes | PASS |
| mission queue | canonical projection per mission | yes | PASS |
| mission history/archive | explicit historical projection | yes | PASS |
| next-action | canonical projection for selected mission | yes | PASS |
| operation roadmap/status | authoritative Beta operation model | roadmap context only | PASS |

Human-readable output is rendered from the same object emitted as JSON.
