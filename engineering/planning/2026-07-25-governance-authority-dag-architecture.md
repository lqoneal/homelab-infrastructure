# Governance Authority Analysis and Proposed DAG Architecture

Date: 2026-07-25  
Status: Proposed architecture — not published Governance  
Baseline: `e0d024a1e40a68b57422193c089ae560a495feed`

## Investigation boundary

This analysis does not revise Governance. It inventories the current controlled
relationship graph and proposes a replacement authority representation suitable
for later review. Historical records retain their original meaning.

## Current graph evidence

The repository contains 109 controlled identities and 504 declared
relationships:

| Type | Count | Type | Count |
| --- | ---: | --- | ---: |
| `related_to` | 185 | `conforms_to` | 108 |
| `indexes` | 46 | `governed_by` | 44 |
| `indexed_by` | 37 | `validates` | 18 |
| `authorized_by` | 11 | `authorizes` | 11 |
| `depends_on` | 9 | `implements` | 9 |
| `implemented_by` | 6 | `uses` | 5 |
| `governs` | 4 | `constrains` | 3 |
| `validated_by` | 3 | other | 5 |

If every relationship is traversed as authority, nearly the entire active
framework becomes one strongly connected component. This is expected for
bidirectional discovery and `related_to`, but proves that the general
relationship graph cannot safely answer “who authorizes this?”

When analysis is restricted to `governed_by`, `conforms_to`, `implements`,
`authorized_by`, reversed `authorizes`, and `supersedes`, one cyclic component
remains:

```text
EGR-000001
PROC-0002
SPEC-0001
STD-0000
STD-0001
STD-0002
```

Representative paths include:

```text
EGR-000001 -> STD-0000        conforms_to
STD-0000   -> EGR-000001      EGR authorizes STD-0000

EGR-000001 -> SPEC-0001       conforms_to
SPEC-0001  -> EGR-000001      EGR authorizes SPEC-0001

EGR-000001 -> PROC-0002       implements
PROC-0002  -> EGR-000001      EGR authorizes PROC-0002

STD-0002   -> SPEC-0001       conforms_to
SPEC-0001  -> STD-0000        conforms_to
STD-0000   -> EGR-000001      authorization
EGR-000001 -> STD-0002        conforms_to
```

The current normative projection also gives 32 records multiple apparent
parents. These are not necessarily policy defects: most are valid conformance,
representation, lifecycle or traceability dependencies. The defect is the
absence of a distinct authority-parent edge and graph domain.

## Circular Dependency Report

| Finding | Classification | Effect |
| --- | --- | --- |
| Reciprocal `authorizes` and `conforms_to` between EGR-000001 and its framework publications | Actual cycle if both are treated as authority | Bootstrap publication cannot be topologically ordered |
| PROC-0002 both implements/conforms to records whose publication it helps represent | Lifecycle/publication loop | Procedure can appear to validate its own authorization path |
| SPEC-0001 and STD-0000/1/2 cross-conformance | Recursive normative ownership | No unique parent can be derived |
| `indexes`/`indexed_by` and related links | Benign traceability cycles | Unsafe only if a generic graph traversal treats them as authority |
| Registry source references and resume consumption | Potential runtime recursion | Registry/resume could appear authoritative without explicit prohibition |
| Qualification returning to caller and stabilization invoking qualification | Workflow loop with terminating return contract | Must remain workflow state, never authority delegation |
| Publication requires authority whose representation is produced by publication | Bootstrap discontinuity | Requires an external/root decision envelope, not self-publication |
| Work Initiation consumes resume while resume recommends initiation | Recommendation loop | Must terminate in an independently resolved controlled authority |

No cycle was found in the existing validator’s narrow `governed_by` graph, but
that check is insufficient because authority-like meaning is distributed across
several relationship types.

## Root causes

1. One relationship field represents authority, conformance, implementation,
   discovery, evidence and navigation.
2. Bidirectional traceability edges are indistinguishable from delegation.
3. A document may have many valid dependencies but no singular authority parent.
4. Approval, activation, publication and persistence are separate in prose but
   not represented as independent typed effects.
5. Bootstrap resolutions both depend on and authorize their publication stack.
6. Derived operational consumers lack a schema-level prohibition against
   becoming authority parents.

## Proposed Governance Authority Architecture

### Four graph domains

1. **Authority DAG** — only delegation and bounded execution authority.
2. **Information ownership forest** — one owner for each governed fact.
3. **Workflow dependency graph** — invocation and publication ordering.
4. **Traceability graph** — indexes, evidence, validation and related records.

Only the Authority DAG may answer authorization questions. No edge is promoted
between domains by inference.

### Authority nodes

```text
rank 0  Engineering Organization       root
rank 1  Engineering Charter            parent: Organization
rank 2  Engineering Governance         parent: Charter
rank 3  Frozen Governance Baseline     parent: Governance decision
rank 4  Mission Authority              parent: Governance Baseline
rank 5  Work Package                   parent: Mission Authority
rank 6  Execution Session              parent: Work Package
```

Each authority-bearing instance has exactly one `authority_parent`. Additional
standards, specifications and procedures are baseline constituents or
non-authoritative dependencies, not extra parents.

### Responsibility separation

| Responsibility | Owner | Cannot do |
| --- | --- | --- |
| Governance decision | Engineering Governance | Execute or fabricate evidence |
| Baseline assembly | Baseline registrar | Approve its own content |
| Lifecycle registration | Lifecycle registrar | Originate disposition |
| Publication | Publication executor | Approve or activate |
| Mission sponsorship | Mission authority | Expand superior baseline |
| Work packaging | Work-package issuer | Self-activate or choose its parent |
| Execution | Implementation agent | Approve, publish or change authority |
| Evidence custody | Evidence service | Accept its own evidence |
| Qualification | Independent qualifier | Create Governance disposition |
| Registry projection | EMP | Change controlled lifecycle |
| Resume | EOS derived view | Recommend through disagreement |
| Event persistence | EENS | Turn events into authority |

### Decision and publication sequence

```text
external/root decision
  -> signed decision envelope
    -> authorized effect manifest
      -> validation
        -> publication transaction
          -> immutable receipt
            -> lifecycle/registry/EOS projections
```

Failure at any step leaves the prior authority effective. A receipt proves
publication, not approval. Projections may be retried idempotently and never
feed back into the decision envelope.

### Resume and Work Initiation termination

1. Resolve exactly one active mission authority.
2. Resolve exactly one work package beneath it.
3. Walk `authority_parent` until the root is reached.
4. Reject missing parents, repeated nodes, rank violations, inactive nodes,
   stale revisions, expired grants or source disagreement.
5. Render resume only after resolution.
6. Work Initiation consumes the resolved decision; it never consumes a resume
   recommendation as authority.

Traversal is bounded by the number of authority nodes and therefore terminates.

## Authority Dependency Graph

The machine-readable proposed graph is
`engineering/planning/2026-07-25-governance-authority-dag.yaml`.

For every edge `child -> parent`, the model requires:

```text
rank(parent) < rank(child)
```

It also requires one root, one parent per non-root authority node, parent
resolution, and exclusion of all derived domains from the parent set.

## Acyclicity proof

Assume a directed cycle exists:

```text
n0 -> n1 -> ... -> nk -> n0
```

Every edge points from child to parent and strictly decreases rank. Therefore:

```text
rank(n0) > rank(n1) > ... > rank(nk) > rank(n0)
```

No integer can be strictly greater than itself. The assumption is
contradictory, so no cycle exists. Single-parent cardinality additionally makes
authority resolution deterministic. The finite rank set makes traversal
terminating.

This proof applies only to the proposed Authority DAG. Traceability graphs may
remain reciprocal because they cannot convey authority.

## Publication-order proof

Authority publication is ordered by rank, then immutable identity, then
revision. A child cannot enter Active state until its parent revision is already
Active and persisted. Publication never changes a parent in the same
transaction. Therefore no child publication is a prerequisite for its own
parent and bootstrap recursion is excluded.

## Migration design

1. Add `authority_parent` and `authority_rank` to authority-bearing records.
2. Classify every existing relationship into one of the four graph domains.
3. Treat existing relationships as traceability-only during migration unless
   explicitly mapped.
4. Establish the Charter-rooted parent chain through a separately approved
   Governance revision.
5. Add cardinality, rank, lifecycle and cycle checks to offline validation.
6. Reconcile each active mission and Work Package to one parent.
7. Update Work Initiation to consume only the validated authority DAG.
8. Preserve historical records without retroactively rewriting their original
   semantics; use compatibility mappings.

## Design risks

- A single parent may oversimplify legitimate multiple normative dependencies;
  those dependencies must remain in the non-authority graphs.
- Incorrect relationship classification can silently remove a required
  constraint; migration requires complete inventories and fixtures.
- Root identity and signature trust are external security decisions.
- Revocation and concurrent publication require monotonic version and lease
  semantics.
- Legacy records may require explicit compatibility exceptions.

## Recommendation

Mission D should implement only the offline authority graph schema and
validator with fixtures. Governance publications and live Work Initiation
enforcement must remain later, separately approved work.

