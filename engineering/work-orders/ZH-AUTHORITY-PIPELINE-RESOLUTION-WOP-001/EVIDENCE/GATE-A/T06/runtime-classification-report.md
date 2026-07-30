# T06 Runtime Classification Report

| Classification | Repository members | Runtime layer |
| --- | --- | --- |
| Layer 1 — Progressive Authority Primitives | `scripts.lib.emp.progressive_gate` | Yes |
| Layer 2 — Progressive Decision Authority | `scripts.lib.emp.progressive_gate` | Yes |
| Layer 3 — Progressive Lifecycle Projection | `scripts.lib.emp.progressive_lifecycle` | Yes |
| Foundational shared utility | `scripts.lib.emp.progressive_runtime_support` | No |
| Compatibility adapters | `scripts.lib.emp.progressive_oa`, `scripts.lib.emp.oa02_lifecycle` | No |
| Qualification infrastructure | dependency validator and its qualification suite | No |

Repository validation returns `runtime_layer_count: 3` and the ordered
canonical layer identities. Classification sets are mutually exclusive at the
module/category boundary, except for the accepted Layer 1/Layer 2 co-location
inside the runtime category.
