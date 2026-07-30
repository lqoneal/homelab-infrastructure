# T06 Runtime Extension Analysis

The accepted architecture contains three logical layers:

1. Progressive Authority Primitives;
2. Progressive Decision Authority; and
3. Progressive Lifecycle Projection.

Layers 1 and 2 remain intentionally co-located in
`scripts.lib.emp.progressive_gate`; logical layer count is therefore distinct
from implementation-module count. T06 preserves that accepted topology.

The classification manifest is an implementation input, not a new controlled
document. The validator compares it to the frozen model rather than trusting
arbitrary labels. A fourth entry, renamed responsibility, module reassignment,
missing input, invalid JSON, or category mismatch is rejected before dependency
analysis. Existing downward-only dependency, cycle, compatibility-leakage, and
duplicate-authority checks remain in force.

Changes to the model require a separately approved architectural decision
before implementation; editing the classification manifest alone cannot expand
the accepted model.
