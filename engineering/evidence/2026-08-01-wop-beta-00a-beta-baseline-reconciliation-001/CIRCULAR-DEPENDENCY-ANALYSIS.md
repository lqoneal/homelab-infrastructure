# Circular Dependency Analysis

The planning graph is acyclic after reconciliation:

```text
Alpha baseline -> BETA-00A -> ZDCL-01 / CAGF-01 -> EPE-01
```

ZDCL-01 and CAGF-01 may run in parallel only when their mission contracts
prove published independent inputs. CAGF never generates its own authority,
ZDCL never supplies mission authority, and EPE never invents either. Runtime
event feedback is permitted but is not an authority edge.
