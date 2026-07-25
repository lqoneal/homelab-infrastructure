# Authority Resolution Engine Design

Date: 2026-07-25  
Status: Offline implementation; not consumed by live authority  
Mission: Zeus Operational Alpha Mission D

## Boundary

The Authority Resolution Engine validates and resolves explicit offline
authority graphs. It does not discover, migrate, reinterpret, approve, activate
or enforce live Governance records. No existing controller imports it.

## Model

An authority graph contains typed nodes and child-to-parent edges. Each node
declares:

- stable identifier;
- authority kind;
- domain;
- non-negative rank;
- zero or more input parent identifiers;
- finite capability set.

The graph declares one root. A valid root has no parent. Every other authority
node has exactly one parent.

## Validation

Validation fails closed on:

- absent or multiple roots;
- duplicate identifiers or YAML keys;
- missing or multiple parents;
- unresolved parents;
- cycles;
- parent ranks greater than or equal to child ranks;
- cross-domain authority edges;
- child capabilities not contained by the parent capability set.

The monotonic rule is:

```text
EffectiveAuthority(child) ⊆ EffectiveAuthority(parent)
```

A child may restrict authority by removing capabilities. It cannot add them.

## Resolution

Resolution validates the entire graph before returning any result. It then
walks the one parent edge from the selected node to the root, rejecting an
unknown or repeated node. The result contains the deterministic child-to-root
path and the selected node's effective capability set.

## Acyclicity and termination

Every valid edge strictly decreases rank. A directed cycle would require rank
to strictly decrease and return to its starting value, which is impossible.
Parent uniqueness removes traversal ambiguity. A finite node set and strictly
decreasing rank guarantee termination.

## Serialization

The engine loads duplicate-key-safe YAML and emits canonical deterministic JSON
or YAML. Nodes and capability values are sorted during serialization. Both
formats round-trip through the typed model.

## Interfaces

Python:

```python
graph = AuthorityGraph.load(path)
graph.validate()
resolution = graph.resolve("session")
```

CLI:

```text
scripts/authorityctl validate GRAPH
scripts/authorityctl resolve GRAPH NODE_ID
scripts/authorityctl serialize GRAPH --format json|yaml
```

## Reuse and future integration

The package is intentionally isolated under `scripts/lib/authority`. Future
missions may adapt controlled records into this schema only after separately
approved migration and enforcement design. Until then, fixtures and explicitly
supplied offline graphs are its only inputs.

