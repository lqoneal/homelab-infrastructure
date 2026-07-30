# Bootstrap and Circular Authority Root-Cause Analysis

Date: 2026-07-30

Status: Assessment finding; no active governance change

## 1. Problem statement

Governance must be able to authorize a bounded mission without first requiring
that mission to have authority-dependent planning and execution records.
Governance must also be able to repair the authority framework without using
the defective framework as the sole source of permission to perform the
repair.

The current architecture does not satisfy either condition.

## 2. Reproduced bootstrap failure

The candidate Zeus Architecture Baseline Completion Mission Contract exposed
the loop:

```text
Mission Contract admission
  requires existing eligible Work Registry item
  requires Active WOP
  requires attributable approval
  requires no active competing contract

but

requested governance ordering
  prohibited Work Registry activation before admission
  left the WOP Draft before authority
  required the new contract to replace an active predecessor
```

The admission result was `DENY`, including:

- `APPROVAL_INVALID`;
- `REGISTRY_BINDING_UNRESOLVED`;
- `REGISTRY_LIFECYCLE_INELIGIBLE`;
- `SCOPE_MISMATCH`; and
- `WOP_LIFECYCLE_INELIGIBLE`.

The candidate itself was schema-valid. The failure was therefore architectural:
required companion state could not be lawfully established in the requested
order.

## 3. Circular dependency catalogue

### GAS-CYCLE-001 — Contract / Registry / WOP

```text
Mission authorization
  -> requires eligible Work Registry item
  -> requires authority reference for authority-dependent state
  -> requires Mission authorization

Mission authorization
  -> requires Active WOP
  -> WOP authority binding requires resolved authority
  -> requires Mission authorization
```

This is a real bootstrap cycle.

### GAS-CYCLE-002 — Active predecessor / successor

```text
successor activation
  -> requires zero other active contracts
  -> predecessor must leave Active first
  -> predecessor supersedence is supposed to derive from successor
  -> successor is not yet active
```

Suspending the predecessor first is reversible but is not the requested
supersedence. Marking it superseded first is terminal and creates an authority
gap if successor activation fails. The service lacks an atomic replacement
operation.

### GAS-CYCLE-003 — Authority / controlled repair

```text
normal authority fails
  -> bootstrap detection suspends execution
  -> Governance determines correction is needed
  -> controlled repair must use normal governance process
  -> normal process requires Mission Contract authority
  -> original authority failure remains
```

The current exception allows consultation and preparation, but it does not
define a permanent root decision record that can authorize the repair without
recursion.

### GAS-CYCLE-004 — Authority / synchronization

```text
activation
  -> must write Project State and Work Registry
  -> must synchronize EOS projection
  -> synchronization requires valid canonical sources
  -> any unrelated projection/source drift aborts authority creation
```

This is not a logical authority cycle, but it is a transactional dependency
cycle: a derived view can prevent the source decision from becoming
authoritative.

### GAS-CYCLE-005 — Resume / work initiation

```text
resume reconstructs current mission from repository state
  -> work initiation consumes current mission
  -> mission resolution requires synchronized resume/source agreement
```

The 2026-07-25 authority-DAG proposal already identified this risk. Resume
must consume an independently resolved authority result and may never serve as
its source.

## 4. Root causes

### Root cause 1 — One aggregate record crosses state domains and authority layers

The current Mission Contract tries to bind mission identity, registry
identity, WOP, repository baseline, scope, permissions, operational roles,
approvals, dirty-tree policy, lifecycle, activation, interruption, and
closeout. Several fields are useful, but the aggregate has become the joining
point for Governance, planning, execution, repository, and synchronization
facts. It is also treated as the governance authority rather than as a mission
representation derived from a separate Authority Record.

### Root cause 2 — Proposal, intent, authorization, readiness, and dispatch are not cleanly separated

“Admission” is used for:

- accepting a package shape;
- recording Governance intent;
- validating a candidate Mission Contract;
- deciding runtime admission; and
- admitting a Stage 1 package.

“Activation” is used both as a Governance authorization and as the start of
execution qualification. The architecture consequently needs repeated state
translations and cross-checks.

### Root cause 3 — Planning projections participate in authorization

The Work Registry is correctly specified as management-only, but the
activation implementation requires and mutates it. A projection cannot remain
non-authoritative when its absence prevents Governance from creating the
authority it is supposed to project.

### Root cause 4 — Repository-wide cardinality substitutes for conflict semantics

Exactly one active Mission Contract per repository is easy to validate but too
coarse. It prevents:

- an architecture mission and an unrelated bounded maintenance mission from
  both being authorized;
- a successor from atomically superseding a predecessor;
- standing read-only or incident-response authorities; and
- separation of “authorized” from “currently selected.”

### Root cause 5 — Mutable lifecycle is stored inside the authority payload

Changing a contract from candidate to active mutates the contract and its
digest. Suspension and completion mutate it again. This blurs immutable
authorization content with later events and makes history dependent on record
rewrites.

### Root cause 6 — Exact repository snapshot is applied at the wrong layer

Exact HEAD is appropriate for an execution attempt, publication transaction,
or reproducibility proof. Binding long-lived mission authority to exact HEAD
makes harmless repository evolution appear to destroy Governance intent and
encourages repeated contract revision.

### Root cause 7 — Relationship domains are not enforced

Authority, conformance, implementation, workflow, evidence, and discovery
relationships coexist. Prior analysis proved that generic traversal creates
cycles. Only an explicit authority-parent relation may convey authority.

### Root cause 8 — Derived views are transaction participants

Project State, Work Registry, and EOS should observe an authorization event.
Requiring them to be atomically rewritten with it increases failure modes,
expands rollback, and makes each projection a veto over the source decision.

## 5. Five-whys summary

1. Why was a valid candidate not admissible?

   Because required WOP and registry state did not exist or was not eligible.

2. Why could those records not be made eligible first?

   Because they require the authority the Mission Contract was intended to
   create, or the initiating scope prohibited premature state mutation.

3. Why does authorization require planning and package lifecycle state?

   Because the Mission Contract was designed as a repository-complete
   execution aggregate rather than a bounded Governance decision.

4. Why was an aggregate chosen?

   To achieve fail-closed, single-snapshot determinism.

5. Why did that produce bootstrapping?

   Determinism was implemented through cross-domain co-ownership rather than
   immutable source records plus deterministic projections.

## 6. Root corrective principle

Authority must be creatable from:

1. an existing superior authority parent;
2. an attributable Governance decision;
3. an exact subject and immutable scope;
4. policy/schema validation; and
5. an atomic append to the authority ledger.

It must not require a planning record, active WOP, Project State mutation, EOS
projection, execution attempt, or the authority it is creating.

## 7. Proof that the proposed direction terminates

The proposed authority chain is:

```text
Ultimate Engineering Authority
  -> controlled Governance baseline or direct root Governance decision
  -> immutable Authority Record
  -> derived Mission Contract v2
  -> qualified WOP
  -> execution attempt
```

Only the Governance Decision and Authority Record are authority-bearing in the
standard mission path. The Authority Record names exactly one already
effective authority parent. The Mission Contract and WOP bind their source
digests but do not become authority parents. Planning, workflow, evidence, and
projection records cannot convey authority.

Because the authority chain is finite and every authority parent predates its
child, no child is required to authorize its own creation. Root Governance
decisions are attributable exercises of already-existing human authority, not
products of a Mission Contract. Future Governance repair therefore uses the
same permanent root decision mechanism and requires no bootstrap exception.
