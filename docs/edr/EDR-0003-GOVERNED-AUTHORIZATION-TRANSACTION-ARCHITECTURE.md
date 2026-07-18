---
document_id: EDR-0003
title: Governed Authorization Transaction Architecture
version: 0.3
status: Approved
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Selected Architecture Refinement
domain: Engineering Governance
classification: Engineering Decision Record
source_of_truth: true
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Engineering Governance Authorization - Historical Evidence Persistence Transaction for EWO-000023
approval_date: 2026-07-18
persistence_status: Persisted
declared_deferrals:
  - governance-authority-broker-evolution
  - implementation
  - governing-record-revision
  - repository-index-registration
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: authorized_by
    target: EWO-000023
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: EWO-000023-PHASE-1-INVESTIGATION
  - type: related_to
    target: EWO-000023-PHASE-2-ALTERNATIVES
  - type: related_to
    target: EWO-000023-PHASE-3-RECOMMENDATION
tags:
  - engineering-decision-record
  - governance-authority
  - authorization-transaction
  - alternative-a
  - approved
---

# Governed Authorization Transaction Architecture


## Historical Approval Package Synchronization Declaration

The following declaration preserves the synchronized pre-disposition review
snapshot; current lifecycle and persistence state is authoritative in the YAML
header and the historical evidence persistence report.

Controlled Architecture:

- EDR-0003 Version 0.3

Repository Baseline:

- `4e6ac19`

Validation Baseline:

- 731 controlled-document validations passed
- zero failures
- Aggregate Engineering Platform validation PASS

Lifecycle State:

- Draft
- Pending Engineering Governance approval
- Persisted by the EWO-000023 historical evidence boundary
- Unregistered
- Non-operational
- Unimplemented

Repository State:

- no tracked modifications
- no staged modifications

Approval Package Inventory:

- exactly 14 authorized Draft artifacts


## Status and Authority Notice

Status: **Approved**

Engineering Governance assigned `EDR-0003` exclusively to this decision record under
EWO-000023 Revision 1. Engineering Governance selected Alternative A as the
architectural direction for Phase 3 refinement. Neither identifier assignment
nor direction selection approves or activates this EDR. This Draft possesses
no operational authority, changes no governing rule, and authorizes no
implementation.

DOC-0001 registration is pending a separately authorized governing-record
revision. The stable Draft identifier and canonical candidate path do not make
the record Active.

## Context

Phase 1 identified six recurring authority discontinuities:

- AG-01: successor-authority discontinuity after bounded work ends;
- AG-02: discontinuity between a Governance decision and its controlled
  repository publication;
- AG-03: ambiguity risk at the boundary between transitional publication
  authority and implementation authority;
- AG-04: inconsistent or stale lifecycle projections across controlled records,
  Work Registry, EOS, checkpoints, and Git;
- AG-05: mismatch between an engineering mission and a persistent agent
  process; and
- AG-06: risk that management or derived state is mistaken for Governance
  Authority.

Phase 2 evaluated three materially distinct responses. Alternative A retained
all current Governance decision authority and standardized the operational
transaction. Alternative B introduced bounded delegated decision authority.
Alternative C introduced a Governance Authority Broker/EGAS. Engineering
Governance selected A for refinement and designated C as a future evolution
target only.

The current model already separates Governance approval from repository
publication and implementation. EGR-000003 and EGR-000004 demonstrate bounded
authorization-publication transactions, but their transaction inputs,
manifests, state machine, idempotency, recovery, and completion receipts are
mission-specific. The selected architecture makes that separation explicit,
repeatable, attributable, and deterministically recoverable without delegating
Governance decisions.

## Engineering Governance Decisions Incorporated

This revision records the post-review Governance dispositions without treating
them as approval of this Draft:

- Alternative A is the selected architectural direction.
- Alternative C is the long-term evolution path and is limited to the extension
  relationship defined in this EDR.
- Alternative B is not adopted.
- Controlled identifier allocation is an operational repository function within
  an already-authorized engineering mission. Engineering Governance authorizes
  the work; it does not normally assign each sequential identifier.
- The manual assignment of `EDR-0003` was an exceptional Governance action and
  is not the normal allocation model.
- A repository-wide controlled identifier allocation capability is part of the
  selected architecture and must be qualified before operational use.

## Decision Proposed for Engineering Governance Review

Adopt a **Governed Authorization Transaction (GAT)** as the standard
architecture for converting an already-made, attributable Engineering
Governance decision into a complete, validated, repository-controlled
authorization publication and aligned operational projections.

The GAT:

1. consumes a Governance Decision Envelope; it never creates or chooses the
   decision;
2. prepares an exact Authorized Effect Manifest over controlled and operational
   targets;
3. validates authority, identity, lifecycle, relationships, scope, repository
   baseline, and projected effects before publication;
4. publishes controlled records through one explicit Git publication boundary;
5. reconciles Work Registry, EOS, checkpoint, and context projections after the
   controlled publication;
6. produces an attributable Transaction Receipt only after all required
   qualification gates pass; and
7. leaves implementation blocked until a separately verified Active EWO is
   launched through current Engineering Work Initiation.

The architecture does not delegate approval, activation, acceptance,
supersedence, deferral, revocation, baseline designation, or successor-work
selection. Engineering Governance retains all current decision authority.

## Decision Drivers

- Preserve Engineering Governance as the ultimate and current lifecycle
  authority.
- Remove avoidable manual interpretation after a decision has already been
  made.
- Prevent successor/no-successor disposition from being omitted at mission
  closure.
- Preserve distinct Governance, publication, projection, and implementation
  boundaries.
- Make multi-record publication deterministic, attributable, resumable, and
  idempotent.
- Preserve EGR/EWO and controlled records as authoritative rather than
  elevating registry, EOS, Git, commands, or services.
- Support autonomous implementation agents without permitting them to infer or
  originate authority.
- Provide stable extension points for a future Authority Broker without
  redesigning the Governance model.

## Architecture

### Conceptual Flow

```text
Engineering Governance decision
        |
        v
Governance Decision Envelope
        |
        v
GAT preflight and Authorized Effect Manifest
        |
        v
Draft controlled publication set
        |
        v
whole-set validation and publication authorization check
        |
        v
Git controlled-publication boundary
        |
        v
Work Registry / EOS / checkpoint / context reconciliation
        |
        v
qualification and Transaction Receipt
        |
        v
separate Active-EWO initiation gate
        |
        v
implementation execution, if independently authorized
```

### Governance Decision Envelope

The envelope is an attributable transaction input, not a new Governance
Authority or independent lifecycle record. Its required semantic fields are:

- stable decision identifier and decision date;
- Engineering Governance identity and approval reference;
- exact disposition and controlled subject identities/revisions;
- authorized lifecycle effects;
- authorized repository and operational projection effects;
- prohibited effects;
- successor, no-successor, or explicit unresolved/escalation disposition;
- transaction validity interval and single-use/idempotency identity;
- evidence considered and required evidence outputs;
- required validation and qualification gates;
- interruption, expiry, and failure behavior; and
- implementation boundary stating whether a resulting Active EWO may be
  initiated only after transaction qualification.

An incomplete, ambiguous, expired, conflicting, or non-attributable envelope
causes a no-change stop. The GAT does not repair or interpret it.

The authoritative Governance decision record owns decision meaning. A
transaction-specific **GAT Evidence Package** owns the canonical normalized
envelope, its signature, and source locator. The envelope is an immutable,
content-addressed derivative and cannot override its source.

### Governance Identity Trust Architecture

Engineering Governance owns a controlled Governance Identity Trust Root. Its
approved specification must define role identities, public verification keys,
key validity, rotation, compromise, revocation, and decision-signing policy.
Private credentials remain outside the repository and must never enter the
envelope or evidence package.

The canonical envelope is signed over its complete serialization, including
decision identity and source digest, repository identity, pinned baseline,
scope, effects, prohibitions, nonce, validity interval, and transaction
protocol version. `IdentityVerifier` must fail closed unless it proves the
signature, signer role at decision time, trust-root status, scope, validity,
non-revocation, and non-replay. A bootstrap or break-glass act is valid only
under CHAR-0001 authority, must be explicitly identified and evidenced, and is
not a normal GAT trust path.

### Authorized Effect Manifest

The manifest enumerates every permitted target and expected effect before any
publication mutation:

- EGR, EWO, evidence, Completion Report, and other authorized controlled
  records;
- DOC-0001 and Project State only when the envelope explicitly authorizes their
  complete revision;
- Work Registry transition inputs and expected resulting revision/state;
- Git branch, baseline commit, explicit path set, and publication message;
- EOS state and repository inventory projections;
- append-only checkpoint identity and applicability;
- context/resume expectations;
- validators and expected invariant results; and
- paths and domains expressly excluded from the transaction.

Every effect must trace to one envelope clause and one information owner.
Unlisted effects are prohibited.

The GAT Evidence Package owns the canonical manifest. Each effect has a stable
effect identifier, target owner, expected prior revision, expected result,
adapter version, and source-envelope clause. Its digest is signed into the
prepublication journal entry and final receipt.

### Transaction State Model

| State | Permitted next state | Required exit evidence |
| --- | --- | --- |
| Received | Authenticated, Rejected, Expired | Durable receipt of unique transaction/envelope identity |
| Authenticated | PreflightQualified, Rejected, Expired | Identity, authority-source, validity, and replay proofs |
| PreflightQualified | Prepared, BlockedNoChange, Cancelled | Pinned baselines, acquired lease, resolved owners and identifiers |
| Prepared | PrepublicationValidated, BlockedNoChange, Cancelled | Canonical manifest and exact prepared-set digest |
| PrepublicationValidated | AuthorityPublished, BlockedNoChange, Cancelled, Expired | Whole-set validation and refreshed compare-and-swap proofs |
| AuthorityPublished | ProjectionsReconciling, RecoveryRequired | Authority publication commit and durable postcommit journal entry |
| ProjectionsReconciling | ProjectionsAligned, RecoveryRequired | Idempotent effect receipts for every required projection |
| RecoveryRequired | ProjectionsReconciling, GovernanceDispositionRequired | First incomplete effect, retry evidence, and bounded-recovery reason |
| ProjectionsAligned | EvidencePersisting, RecoveryRequired | Cross-owner convergence proof |
| EvidencePersisting | Qualified, RecoveryRequired | Immutable evidence closeout commit containing receipt and journal |
| Qualified | Closed | Independent qualification report and executable-work gate proof |
| Closed | none | Final receipt and termination record |

`Rejected`, `Expired`, `Cancelled`, and `BlockedNoChange` are terminal before
publication and guarantee no authoritative effect.
`GovernanceDispositionRequired` is a durable postpublication stop:
implementation remains blocked and only a new Governance decision can change
the required outcome. Every transition is journaled before and after its
effects. A retry uses the same transaction and effect identities; it cannot
skip an entry criterion or produce a second effect.

The **authority publication commit** is the point after which forward recovery
is mandatory. The later **evidence closeout commit** makes the finalized journal
and Transaction Receipt historically immutable. A newly Active EWO remains
execution-blocked by its GAT qualification reference until that closeout is
persisted and independently qualified.

### Restart Semantics

A restart after `Rejected`, `Expired`, `Cancelled`, or `BlockedNoChange` is a
**new transaction**, never a transition out of the terminal transaction. It
receives a new transaction identity and new single-use nonce. The prior
transaction identity, nonce, journal, terminal receipt, validation evidence,
and failure reason remain immutable and are referenced by the replacement
transaction through `restarts_transaction` lineage.

Restart rules are:

- `Rejected` may restart only after corrected, newly signed decision-envelope
  input is supplied; the decision source may remain the same if still valid.
- `Expired` requires a newly signed envelope and validity interval.
- `Cancelled` requires a new attributable Governance decision or envelope;
  the cancelled envelope cannot be revived.
- `BlockedNoChange` may restart from the same signed envelope only when that
  envelope remains valid and permits another attempt; otherwise a new envelope
  is required.
- `GovernanceDispositionRequired`, `Qualified`, and `Closed` cannot restart.
  Postpublication continuation uses forward recovery under the original
  transaction, or a new Governance decision and transaction where disposition
  is required.

Every prepublication restart releases unconsumed reservations through an
attributable reservation-release receipt. An identifier already persisted or
made non-reusable by namespace rules remains consumed. The replacement pins a
fresh repository, registry, EOS, checkpoint, and reservation baseline; creates
a new manifest; and never reuses the prior manifest as executable input. The
prior manifest and journal remain retained evidence. The terminal transaction
receives a no-effect receipt; the replacement later receives its own distinct
receipt. A retry, in contrast, remains within a nonterminal transaction or
`RecoveryRequired`, keeps its identity and nonce, and may repeat only an
idempotent effect using the same effect identity.

No state in this transaction model is a controlled-document lifecycle state.
It must not be represented as approval or activation metadata.

## Authority Boundaries

| Actor or component | Permitted responsibility | Explicit prohibition |
| --- | --- | --- |
| Engineering Governance | Make the decision; define scope, disposition, lifecycle effects, successor disposition, constraints, and qualification | Governance responsibility is not transferred to the transaction executor |
| Decision-envelope preparer | Faithfully represent the already-made decision and evidence | May not infer intent, select a disposition, or add authorized effects |
| GAT executor | Validate inputs, prepare manifested Drafts, run deterministic publication/reconciliation actions, and produce evidence | May not approve, activate, accept, supersede, defer, revoke, expand scope, or implement the resulting work |
| Controlled Identifier Allocator | Reserve and allocate deterministic identities within the authorized mission and class namespace | Allocation does not approve, activate, or expand work |
| Validators | Verify structure, identity, relationships, scope, lifecycle invariants, and projections | PASS does not approve content or perform a Governance transition |
| Git | Persist the controlled publication boundary and history | Commit identity does not approve or activate a record |
| Work Registry | Project attributable EMP management state | Registry state does not govern controlled lifecycle or execution |
| EOS/checkpoint/context services | Reconcile operational continuity and derived views to authoritative sources | Derived state does not originate or expand authority |
| Implementation agent | Initiate and execute the separately verified Active EWO | May not inherit GAT transitional authority or use the receipt as execution authority |

## Lifecycle Ownership

| Lifecycle concern | Authoritative owner | GAT role |
| --- | --- | --- |
| Governance disposition | Engineering Governance through applicable controlled authority | Consume exact supplied decision |
| Controlled-document lifecycle | STD-0001 and the owning controlled record under Governance approval | Validate and publish only authorized effects |
| Approval representation, identity, lineage, relationships | SPEC-0001 | Produce conforming representations |
| Persistence, index, discovery, integrity | STD-0002 and repository owners | Persist and validate explicit publication set |
| EWO mission scope and execution authority | Active EWO under STD-0003/PROC-0001 | Create/revise only when authorized; never execute it within GAT |
| Work management state | EMP Work Registry | Submit attributed projection after controlled publication |
| Project State facts | Project State controlled record | Own project identity, governing references, and controlled project facts; consumers derive views |
| EOS operational facts | EOS authoritative operational state record under STD-0004 | Own current operational lifecycle, repository inventory, and convergence facts |
| Checkpoint State facts | Append-only EOS checkpoint record | Own the recorded point-in-time continuity snapshot and applicability identity |
| Context State facts | EOS Context Projection record | Own the current generated context projection; content remains derived from cited controlled/EOS sources and conveys no authority |
| Resume State facts | EOS Resume Projection record | Own the current computed resume-readiness projection; Active EWO remains the execution-authority source |
| In-flight transaction execution state | EOS GAT operational journal | Durable write-ahead progress; never replace controlled lifecycle |
| Canonical envelope, manifest, finalized journal, receipt | GAT Evidence Package under STD-0002 retention | Immutable historical transaction evidence; decision meaning remains with its Governance source |
| Identifier namespace and reservations | DOC-0001 namespace catalog plus Controlled Identifier Allocation Specification | Coordinate uniqueness; allocation never creates lifecycle authority |

## Transaction Boundaries

### Boundary 1 — Decision

The Governance decision occurs before GAT execution. GAT acceptance proves
only that the envelope is complete and attributable; it does not review or
approve the decision's merits.

### Boundary 2 — Prepublication Workspace

Draft preparation and validation occur against a pinned repository baseline.
No Draft or staged content is authoritative. Concurrent baseline change,
identifier conflict, overlapping Git operation, stale envelope, or scope drift
invalidates preflight and requires restart or Governance disposition.

A repository-scoped exclusive lease serializes GAT publication preparation but
does not confer authority. Immediately before publication the coordinator must
compare-and-swap the pinned Git ref, controlled baselines, Work Registry
revision, EOS generation, checkpoint pointer, and identifier reservation
ledger. Any mismatch before the publication commit enters `BlockedNoChange`.
The final tree diff and manifest digest must be byte-for-byte equal.

### Boundary 3 — Controlled Publication

One authorized Git commit is the durable repository boundary for the complete
controlled publication set. The commit does not itself approve or activate;
those effects must already be present in the Governance decision and correctly
represented in the controlled records.

### Boundary 4 — Operational Reconciliation

Registry, EOS, checkpoint, and context are reconciled from the persisted
controlled publication. They may be sequential and temporarily behind, but the
transaction journal must expose the incomplete state and block implementation
initiation until all required projections qualify.

### Boundary 5 — Implementation

The GAT ends with a receipt. Implementation is a separate mission boundary and
requires current Active-EWO verification, current Engineering State, and the
classification-specific Work Initiation gates. The GAT executor carries no
implementation authority across this boundary.

## Publication Flow

1. Verify EWO or superior authority to execute the GAT.
2. Validate envelope identity, attribution, scope, date, expiry, single-use
   identity, evidence, and decision completeness.
3. Pin repository, branch, commit, working tree, active operations, controlled
   baseline, EOS state, checkpoint, and registry revision.
4. Resolve authoritative information owners and identifiers without inference.
5. Produce the Authorized Effect Manifest and excluded-path inventory.
6. Prepare complete Draft or lifecycle-transition publications.
7. Validate every document, relationship, lifecycle effect, registry mutation,
   Project State projection, Git path, and authority boundary as a whole.
8. Verify that the final diff equals the manifest and contains no
   implementation path unless the envelope separately and explicitly permits
   it; GAT itself never supplies that permission.
9. Create the authorized controlled-publication commit without push or tag
   unless separately authorized.
10. Apply attributable registry transition(s) from the persisted controlled
    authority.
11. Refresh EOS operational state and repository inventory.
12. Create/select the append-only checkpoint and verify context/resume output.
13. Run final controlled-document, registry, repository, EOS, checkpoint,
    persistence, context, and aggregate qualification.
14. Emit the Transaction Receipt and close the transaction.
15. Terminate. Any implementation starts separately through the applicable
    Active EWO.

## Controlled Identifier Allocation

The Controlled Identifier Allocator is a deterministic repository adapter, not
a Governance decision maker. It may execute only for document classes and
quantities present in an authenticated envelope or Active EWO scope. DOC-0001
owns the namespace catalog and canonical discovery rules; SPEC-0001 owns the
identifier representation; the Controlled Identifier Allocation Specification
owns allocation and reservation behavior.

For each request the allocator scans the namespace catalog, tracked history,
current tree, staged, unstaged, untracked, and durable reservation entries;
selects the lowest available sequential identifier under the class rule;
acquires the repository lease; and compare-and-swaps the reservation ledger.
It emits an attributable reservation receipt bound to mission, transaction,
class, candidate path, baseline, and expiry. Allocated identifiers are unique,
never silently reused, and acquire no approval or lifecycle status through
allocation. Conflicts stop without mutation. Hardware namespaces and other
nonstandard schemes use class-specific adapters under the same contract.

## Concurrency and Publication-Race Controls

The transaction coordinator combines an exclusive repository lease with
optimistic compare-and-swap checks. Lease loss stops new effects. A Git update
must use the expected prior object identity; registry, EOS, checkpoint, and
reservation updates must use expected revisions or generations. Each adapter
is idempotent on transaction/effect identity and returns the prior receipt on
replay. Overlapping manifests, competing lifecycle operations, an altered work
tree, or changed owner revision block before publication. After publication,
unrelated work may continue only if it does not overlap the manifest and every
projection compare-and-swap remains valid.

## Recovery Architecture

The EOS GAT operational journal is hash-chained and write-ahead: intent is
durably recorded before an external effect and its result immediately after.
Recovery derives truth in this order: authority publication commit, Work
Registry, EOS, checkpoint, context/resume, then evidence closeout. It resumes
at the first missing effect using the original transaction/effect identities.

The authenticated envelope authorizes bounded recovery needed to complete only
its listed effects; recovery cannot add effects or perform implementation. A
prepublication failure has no authoritative change. A postpublication failure
cannot roll back or rewrite controlled history. An irreconcilable owner
conflict enters `GovernanceDispositionRequired`, preserves all evidence, and
blocks affected implementation until a new Governance decision is published.

## Logical Interface Contracts

Every interface carries protocol and schema versions, transaction identity,
source digests, structured error category, and evidence locator. Unsupported
major versions fail closed; backward-compatible minor versions may be accepted
only when declared by both parties and recorded in the journal. Alternative C
may replace implementations behind these contracts only through a future
approved architecture; it may not change their authority invariants.

### DecisionEnvelopeProvider Contract

- **Purpose:** normalize an already-made Governance decision for GAT input.
- **Authoritative owner:** Engineering Governance owns decision meaning through
  its controlled decision record; the GAT Evidence Package owns the normalized
  envelope representation.
- **Responsibilities:** resolve the exact source, serialize without
  interpretation, bind the source digest, and obtain the required signature.
- **Inputs:** controlled decision locator/revision, repository identity,
  transaction protocol version, and requested transaction identity.
- **Outputs:** canonical signed envelope or a no-effect rejection.
- **Invariants:** semantic equality to the source; complete required fields; no
  added effect or authority.
- **Trust boundary:** untrusted preparer input becomes admissible only after
  canonicalization and IdentityVerifier/AuthorityResolver proof.
- **Version expectations:** emit one declared envelope schema version supported
  by the transaction; no implicit conversion across major versions.
- **Error categories:** `SourceMissing`, `SourceConflict`, `AmbiguousDecision`,
  `CanonicalizationFailure`, `UnsupportedVersion`, `SignatureUnavailable`.
- **Transaction effects:** success permits `Received -> Authenticated` checks;
  error enters `Rejected` with no authoritative effect.

### IdentityVerifier Contract

- **Purpose:** prove that the envelope is attributable to current Governance
  identity authority.
- **Authoritative owner:** Engineering Governance Governance Identity Trust Root.
- **Responsibilities:** verify signature, role at decision time, trust-root
  revision, validity, scope, revocation, nonce, and replay status.
- **Inputs:** canonical envelope, trust-root revision, revocation evidence, and
  replay ledger baseline.
- **Outputs:** content-addressed verification proof or rejection evidence.
- **Invariants:** fail closed; private credentials never cross the interface;
  proof is bound to the exact envelope digest.
- **Trust boundary:** crosses from externally supplied signed content into the
  trusted transaction domain.
- **Version expectations:** verifier must support the envelope signature suite
  and trust schema declared by the envelope.
- **Error categories:** `InvalidSignature`, `UnknownSigner`, `RoleUnauthorized`,
  `ExpiredIdentity`, `RevokedIdentity`, `ScopeMismatch`, `Replay`,
  `UnsupportedTrustVersion`.
- **Transaction effects:** proof permits authentication; error enters
  `Rejected` or `Expired` and consumes no nonce as a successful transaction.

### AuthorityResolver Contract

- **Purpose:** prove the exact controlled authority for every proposed effect.
- **Authoritative owner:** the applicable controlled Governance decision and
  Active EWO; the resolver owns only its derived proof.
- **Responsibilities:** traverse controlled relationships, compare revisions,
  enforce prohibitions, and reject projections as authority sources.
- **Inputs:** verified envelope, controlled sources, EWO, manifest candidate,
  and repository baseline.
- **Outputs:** clause-to-effect authority proof or conflict report.
- **Invariants:** authority not explicit remains ungranted; controlled sources
  prevail; one authority chain per effect.
- **Trust boundary:** converts repository and envelope claims into verified
  authority facts; registry/EOS/context inputs remain untrusted projections.
- **Version expectations:** support the controlled relationship and lifecycle
  model versions named by the source records.
- **Error categories:** `MissingAuthority`, `ScopeExceeded`, `SourceConflict`,
  `StaleAuthority`, `LifecycleConflict`, `UnsupportedAuthorityModel`.
- **Transaction effects:** success permits preflight; error enters
  `BlockedNoChange`, `Rejected`, or `Expired` according to cause.

### IdentifierAllocator Contract

- **Purpose:** reserve a unique controlled identifier as an operational effect.
- **Authoritative owner:** DOC-0001 owns namespace facts; the durable reservation
  ledger owns current reservation facts.
- **Responsibilities:** enumerate all occupied identities, apply the class rule,
  lease and compare-and-swap the ledger, and emit release/allocation receipts.
- **Inputs:** authorized class/quantity, candidate path, mission/transaction,
  repository history/current tree, namespace catalog, and ledger baseline.
- **Outputs:** reservation receipt, release receipt, or collision evidence.
- **Invariants:** uniqueness, no silent reuse, no lifecycle effect, and no
  allocation beyond authorized class/quantity.
- **Trust boundary:** agent requests are untrusted until AuthorityResolver proof;
  repository and ledger observations must be freshly verified.
- **Version expectations:** class adapter and namespace-rule versions are bound
  into every receipt; incompatible major versions stop.
- **Error categories:** `UnauthorizedClass`, `NamespaceUnknown`, `Collision`,
  `LeaseUnavailable`, `StaleLedger`, `ReservationExpired`, `UnsupportedRule`.
- **Transaction effects:** success records a manifested reservation; stale or
  conflicting state enters `BlockedNoChange`; release is journaled on restart.

### TransactionCoordinator Contract

- **Purpose:** enforce the GAT state machine and order manifested effects.
- **Authoritative owner:** GAT Evidence Package owns the transaction definition;
  EOS GAT journal owns in-flight execution state.
- **Responsibilities:** enforce transitions, lease, compare-and-swap,
  idempotency, retry/restart distinction, stops, and recovery ordering.
- **Inputs:** verified envelope, authority proof, manifest, owner baselines,
  adapter capabilities, and journal state.
- **Outputs:** journaled transition, adapter request, status, or terminal receipt.
- **Invariants:** only table-permitted transitions; one transaction writer;
  effect identity is single-use; postpublication recovery is forward-only.
- **Trust boundary:** sole orchestration boundary between validated intent and
  mutating adapters; it cannot originate authority.
- **Version expectations:** all adapter major versions must match the selected
  GAT protocol; capabilities are pinned before preflight exit.
- **Error categories:** `InvalidTransition`, `LeaseLost`, `StaleBaseline`,
  `AdapterIncompatible`, `EffectConflict`, `RecoveryRequired`,
  `GovernanceDispositionRequired`.
- **Transaction effects:** success advances exactly one state/effect; errors
  map to the defined no-change terminal or postpublication recovery states.

### PublicationAdapter Contract

- **Purpose:** persist the exact controlled authority publication set in Git.
- **Authoritative owner:** repository Git history owns persisted tree/commit
  facts; controlled records retain their assigned information ownership.
- **Responsibilities:** verify manifest-to-diff equality and update the expected
  Git ref atomically.
- **Inputs:** manifested tree, excluded paths, expected ref/object identity,
  commit attribution, and transaction/effect identity.
- **Outputs:** publication commit receipt or no-change conflict evidence.
- **Invariants:** byte-exact manifested paths, no excluded effect, expected-ref
  compare-and-swap, and idempotent receipt on replay.
- **Trust boundary:** only this adapter crosses from prepared workspace into
  persistent repository history.
- **Version expectations:** repository format and adapter version are pinned in
  the manifest and receipt.
- **Error categories:** `DiffMismatch`, `ExcludedPathChanged`, `StaleGitRef`,
  `ObjectIntegrityFailure`, `PersistenceFailure`, `ReplayConflict`.
- **Transaction effects:** success enters `AuthorityPublished`; every
  precommit error enters `BlockedNoChange`; uncertain postcommit result enters
  `RecoveryRequired` for Git-object reconciliation.

### ProjectionAdapter Contract

- **Purpose:** reconcile one named operational owner from published authority.
- **Authoritative owner:** the manifest-named Work Registry, Project State, EOS,
  checkpoint, context, or resume owner for that effect.
- **Responsibilities:** transform authoritative inputs, compare-and-swap the
  owner revision, preserve attribution, and return an effect receipt.
- **Inputs:** publication commit, controlled source digests, target owner and
  expected revision/generation, projection schema, transaction/effect identity.
- **Outputs:** owner-specific effect receipt, prior idempotent receipt, or
  convergence conflict.
- **Invariants:** one owner per target fact; projections cannot change decision
  meaning; repeated effect identity cannot duplicate mutation.
- **Trust boundary:** crosses from controlled publication into a named
  operational owner; derived consumers receive no authority.
- **Version expectations:** one adapter per owner/schema major version;
  compatibility must be declared before publication.
- **Error categories:** `UnknownOwner`, `StaleOwnerRevision`, `TransformFailure`,
  `ProjectionConflict`, `WriteFailure`, `UnsupportedProjectionVersion`.
- **Transaction effects:** success advances reconciliation; transient or stale
  postpublication errors enter `RecoveryRequired`; irreconcilable conflict
  enters `GovernanceDispositionRequired`.

### AuditSink Contract

- **Purpose:** durably preserve ordered, attributable transaction evidence.
- **Authoritative owner:** EOS owns in-flight journal facts; the GAT Evidence
  Package owns finalized historical audit facts after closeout.
- **Responsibilities:** append intent/result events, hash-chain them, reject
  secret-bearing or out-of-order content, and acknowledge durability.
- **Inputs:** sequenced event, prior event hash, identities, source/effect
  digests, timestamp, and evidence classification.
- **Outputs:** durable acknowledgement/event hash or audit failure evidence.
- **Invariants:** append-only order, hash continuity, attribution, no silent
  overwrite, and no secrets/unrelated content.
- **Trust boundary:** all executor assertions remain untrusted until persisted
  and later independently recomputed.
- **Version expectations:** event and evidence schema versions are recorded per
  event; closeout requires one supported chain version.
- **Error categories:** `SequenceGap`, `HashMismatch`, `SecretDetected`,
  `DurabilityFailure`, `OwnerUnavailable`, `UnsupportedAuditVersion`.
- **Transaction effects:** failure before publication blocks with no change;
  failure after publication enters `RecoveryRequired` and blocks qualification.

### ValidationAndQualification Contract

- **Purpose:** independently recompute conformance and transaction completion.
- **Authoritative owner:** the approved Validation and Qualification function
  owns its report; it owns no Governance disposition.
- **Responsibilities:** recompute signatures, sources, hashes, Git objects,
  owner revisions, effects, convergence, replay, and initiation blocking.
- **Inputs:** controlled sources, envelope, manifest, finalized journal,
  receipts, repository objects, owner states, and validator versions.
- **Outputs:** signed/content-addressed qualification report with PASS/FAIL and
  complete findings.
- **Invariants:** operational independence from executor; recomputation rather
  than assertion trust; PASS cannot approve or activate.
- **Trust boundary:** converts executor and adapter evidence into independently
  verified qualification evidence.
- **Version expectations:** report declares every validator/schema version and
  fails on an unsupported required evidence version.
- **Error categories:** `EvidenceMissing`, `EvidenceConflict`, `IntegrityFailure`,
  `ConvergenceFailure`, `ValidatorFailure`, `UnsupportedEvidenceVersion`.
- **Transaction effects:** PASS permits `EvidencePersisting -> Qualified`;
  FAIL enters `RecoveryRequired` or `GovernanceDispositionRequired` and blocks
  implementation.

### ClientInterface Contract

- **Purpose:** accept bounded requests and expose transaction status/evidence.
- **Authoritative owner:** the GAT TransactionCoordinator owns accepted request
  and status facts; the client owns no transaction or Governance authority.
- **Responsibilities:** validate request shape, authenticate caller identity,
  expose states/errors/evidence locators, and prevent receipt-as-authority use.
- **Inputs:** authenticated caller, operation, transaction/envelope locator,
  supported versions, and correlation identity.
- **Outputs:** accepted-request receipt, current derived status, structured
  error, or final receipt locator.
- **Invariants:** no client command approves, activates, expands, or implements;
  status resolves to authoritative journal/evidence owners.
- **Trust boundary:** external operators, agents, controllers, and future broker
  clients remain untrusted until identity and authority checks complete.
- **Version expectations:** capability negotiation is mandatory; unsupported
  major client or protocol versions fail without transaction creation.
- **Error categories:** `CallerUnauthenticated`, `CallerUnauthorized`,
  `MalformedRequest`, `TransactionUnknown`, `OperationNotPermitted`,
  `UnsupportedClientVersion`.
- **Transaction effects:** an accepted creation request may create `Received`;
  status reads have no effect; invalid requests create no transaction.

## Audit Requirements

The audit chain must record without secrets or unrelated content:

- transaction, envelope, approval-reference, and decision identifiers;
- Governance identity reference and decision timestamp;
- executor identity and tool/version identity;
- repository root, branch, baseline and publication commits;
- controlled subjects and exact revisions;
- manifest and excluded-path digests;
- registry starting/ending revisions and authority references;
- EOS/checkpoint starting/ending identities;
- every state transition, timestamp, validation result, failure, retry, and
  recovery action;
- final receipt status and unresolved exceptions; and
- evidence locators sufficient for deterministic reconstruction.

The audit record must be append-only or historically immutable after each
durable boundary, independently verifiable against Git and controlled sources,
retained under approved persistence rules, and incapable of silently changing
the Governance decision.

During execution, EOS owns the operational journal. At evidence closeout the
GAT Evidence Package becomes the authoritative historical owner of the
normalized envelope, manifest, finalized journal, independent qualification
report, and Transaction Receipt; EOS retains only a derived status and locator.
The Validation and Qualification component, operationally independent of the
executor, recomputes signatures, hashes, Git objects, owner revisions, effects,
and receipt content. Conflicts are recorded and fail qualification; the
controlled Governance source always wins for decision meaning. Retention,
integrity, discovery, and disposition conform to STD-0002 and the future Audit
and Engineering Evidence Specification.

## Revocation and Supersedence Semantics

| Authority position | Required behavior |
| --- | --- |
| Before AuthorityPublished | An authenticated Governance cancellation/revocation envelope enters `Cancelled`; no authoritative effect occurs |
| Published, resulting EWO not initiated | A new Governance decision and GAT supersedes or cancels it; all projections and receipt must converge |
| Resulting mission initiated or interrupted | New authenticated revocation causes work to stop at a safe boundary, forbids new implementation effects, captures evidence, and requires Governance lifecycle disposition |
| Resulting mission completed | Historical authority and completed evidence remain immutable; a later decision may supersede future effect but cannot retroactively erase execution |

Published controlled authority is never deleted or silently invalidated.
Supersedence preserves lineage and names the prior decision, transaction,
affected work, effective time, and required operational reconciliation.

## Migration and Backward Compatibility

GAT v1 is prospective. Existing EGR/EWO records are classified `Pre-GAT` and
remain valid under their contemporaneous governance; missing envelopes or
receipts must not be fabricated. Migration requires an inventory and
compatibility report, shadow validation with no effects, a separately
authorized pilot, and an explicit cutover baseline. After cutover, new covered
transactions require GAT v1 while legacy readers may consume existing EGR/EWO
outputs but may not execute a GAT transaction.

Interfaces negotiate supported protocol versions and preserve current
controlled-document shapes through adapters. A failed cutover stops new GAT
acceptance. Prepublication transactions end with no change; every transaction
past `AuthorityPublished` is recovered forward. Controlled history is never
rolled back. Production adoption requires complete qualification and an
approved operational baseline.

## Validation Requirements

Prepublication validation must prove:

- envelope completeness, attribution, validity, and no reuse;
- EWO/transaction authority and exact repository scope;
- identifier uniqueness and canonical placement;
- controlled-document lifecycle and approval/persistence separation;
- relationship resolution and absence of circular/conflicting authority;
- one information owner per affected fact;
- exact manifest-to-diff equality and excluded-path preservation;
- expected registry mutations, dependency integrity, and authority boundary;
- no active conflicting Git or lifecycle operation;
- deterministic recovery state and no secret exposure; and
- implementation paths and effects remain excluded.

Postpublication qualification must prove:

- Git object integrity and exact committed publication set;
- controlled-document and repository-index consistency where registration was
  authorized;
- Work Registry revision, state, attribution, and dependency correctness;
- Project State, EOS state, checkpoint, context, and resume alignment;
- persistence and historical reconstruction;
- idempotent replay returns the existing receipt without duplicate effects;
- negative tests reject missing, expired, ambiguous, overbroad, replayed, or
  conflicting envelopes; and
- the resulting Active EWO, if any, cannot execute without separate initiation.

## Qualification Requirements

Before operational adoption, a future implementation must qualify:

1. schema conformance and canonical serialization;
2. authority-chain resolution and reserved-decision enforcement;
3. complete lifecycle transition coverage, including no-successor outcomes;
4. idempotency, replay prevention, concurrency, interruption, and restart;
5. precommit no-change failures and postcommit forward recovery;
6. manifest completeness and scope isolation;
7. approval-identity and evidence integrity without secret exposure;
8. registry/EOS/checkpoint projection convergence;
9. legacy EGR/EWO compatibility and historical reconstruction;
10. explicit revocation/supersedence handling through a new Governance
    decision, never silent mutation;
11. implementation-boundary enforcement across persistent agent processes; and
12. multiple live, independently attributable authorization transactions with
    operator-confirmed expected outcomes.

No production use, autonomous use, or Governance reliance is permitted until
the complete qualification evidence is accepted under separate authority.

## Repository Ownership

The selected architecture intentionally distributes ownership by existing
document responsibility:

- CHAR-0001: foundational Governance authority; no amendment is proposed by
  this EDR.
- POL-0001: policy boundary prohibiting silent correction and preserving
  Governance responsibility.
- STD-0001/0002/0003/0004: lifecycle, persistence, EWO, and Engineering State
  requirements.
- SPEC-0001: identity, metadata, relationship, lineage, approval, and
  persistence representation.
- PROC-0001/0002: operational EWO and Governance-resolution workflows.
- TPL-0001/0002/0004 and a separately approved transaction structure if later
  justified: reusable record representation.
- SPEC-0005 and SERVICE-0001 only after appropriate lifecycle approval:
  controller routing and authoritative operational service responsibilities.
- EMP-0001/SPEC-0006/SERVICE-0002: non-governing Work Registry projection.
- EOS state/checkpoint/context owners: operational continuity projections.

This Draft does not assign implementation to SPEC-0007. SPEC-0007 remains
relevant high-level evidence for the future broker evolution, not the owner of
the minimal-change transaction protocol.

Mandatory future controlled revisions for adoption are: POL-0001; STD-0000
through STD-0005; SPEC-0001 and SPEC-0005; PROC-0001 and PROC-0002; DOC-0001;
TPL-0001 through TPL-0004; HW-0001; FIN-0002; and SERVICE-0001. New controlled
specifications are required for GAT, Controlled Identifier Allocation,
Governance Identity and Trust, and Audit and Engineering Evidence. EDR-0003
must itself be approved and registered. The Repository Impact Analysis is the
definitive owner-by-owner inventory.

CHAR-0001 and EDR-0002 require no revision because Alternative A preserves
their authority and information-authority models. SPEC-0007, EMP-0001,
SPEC-0006, SERVICE-0002, broker/EGAS services, dashboards, and analytics are
future enhancements unless a later approved interface change makes them
mandatory.

## Governance Process Persistence

The EWO-000023 process is the initial qualification case for a permanent,
controlled architecture-governance process. Adoption planning must preserve:

1. Architecture Investigation;
2. materially distinct Alternative Architecture Evaluation before selection;
3. Architecture Recommendation and attributable Governance selection;
4. Stage 1 Discovery Formal Architecture Review to find and classify
   deficiencies and required revisions;
5. bounded Architecture Revision without reopening settled direction;
6. Stage 2 Verification Formal Architecture Review to verify every blocking
   finding, detect regressions, and assess approval readiness;
7. exclusive Engineering Governance approval and controlled publication;
8. Architecture Adoption only after approval; and
9. separate Implementation Authorization through an Active EWO.

The permanent process must standardize deliverables, evidence traceability,
finding classifications, severity, required versus optional corrections,
approval-readiness criteria, and Governance gate sequencing. Governance
decisions must become controlled repository records rather than remain only in
conversation. Cross-repository improvements discovered during project work
must become separately authorized follow-on governance work rather than ad hoc
project changes.

The Implementation Roadmap and Repository Impact Analysis assign the future
controlled owners for this process and for a controlled EWO-000023 Lessons
Learned Report. This section records architectural integration requirements; it
does not create, approve, or activate those records.

## Resolution of Phase 1 Discontinuities

| Gap | Resolution in selected architecture | Residual Governance boundary |
| --- | --- | --- |
| AG-01 successor discontinuity | Every envelope must contain successor, no-successor, or unresolved/escalation disposition; closure cannot silently omit it | GAT cannot choose a successor; missing disposition stops |
| AG-02 decision-to-publication | Canonical envelope and manifest translate an already-made decision into deterministic effects | Governance must still make and authenticate the decision |
| AG-03 transitional/execution separation | Explicit transaction states, expiry, receipt, and separate Active-EWO initiation prevent authority leakage | Receipt is not implementation authority |
| AG-04 multi-projection exposure | Durable journal, pinned baseline, manifest, forward recovery, convergence checks, and receipt make partial state visible and blocking | Cross-store projections may be sequential; controlled records remain authoritative |
| AG-05 mission/process mismatch | Transaction and resulting EWO carry distinct mission identities; implementation requires a fresh wrapped initiation after GAT termination | External host launch remains governed procedurally and by initiation enforcement |
| AG-06 management/governance confusion | Registry/EOS/context are explicitly downstream projections and receipt inputs, never decision sources | Consumers must continue resolving the controlled EWO and approval evidence |

## Alternative C Future Evolution Path

Alternative C is recorded only as a future architectural evolution target. A
future Governance Authority Broker/EGAS could mediate the same GAT contract
without changing the authority model if it remains a non-originating executor
of authenticated Governance decisions.

Stable extension points are:

1. `DecisionEnvelopeProvider`: accepts a human-governed envelope today and a
   future authenticated broker-issued envelope without changing semantics.
2. `AuthorityResolver`: resolves current controlled authority through existing
   repository services and may later consume a qualified knowledge-resolution
   interface.
3. `TransactionCoordinator`: local deterministic orchestration today; a future
   broker may coordinate the same state model and invariants.
4. `PublicationAdapter`: current Git/repository publication with stable
   manifest and receipt contracts.
5. `ProjectionAdapter`: registry, EOS, checkpoint, and context reconciliation
   behind bounded interfaces.
6. `AuditSink`: repository evidence today; future independently qualified
   audit service while preserving controlled source traceability.
7. `IdentityVerifier`: explicit approval reference validation today; future
   authentication/authorization service without transferring decision power.
8. `ClientInterface`: current operator/controller workflow; future API or agent
   clients consuming identical preconditions, stops, and receipts.

The extension points are logical contracts, not implementation designs. Phase
3 does not define EGAS APIs, storage, deployment, delegation, service topology,
or security mechanisms. Any evolution requires a new approved EDR/specification
set and separate implementation authority.

## Consequences

### Advantages

- Preserves current Governance authority and lifecycle semantics.
- Converts repeated ad hoc publication transactions into one deterministic,
  auditable architecture.
- Makes incomplete and partially reconciled authority state visible and
  blocking.
- Improves autonomous-agent compatibility without delegation.
- Retains backward-compatible EGR/EWO, Git, registry, EOS, and checkpoint
  outputs.
- Provides broker-compatible seams without making a broker a prerequisite.

### Disadvantages

- Engineering Governance remains required for every decision.
- Multi-store reconciliation is coordinated and journaled rather than assumed
  atomically committed.
- The transaction model adds manifests, journals, receipts, negative tests,
  and operating discipline.
- Immediate revocation remains a new Governance decision and transaction.
- Legacy publications will not contain complete envelopes or receipts and need
  compatibility treatment rather than retrospective fabrication.

### Risks

- An insufficiently authenticated envelope could propagate an invalid decision.
- An incomplete manifest could omit a required owner or projection.
- A postcommit failure could block new work until forward reconciliation.
- Operators could mistake a receipt for execution authority.
- Extension points could be prematurely treated as approval for EGAS.
- Overloading one future standard or specification could duplicate existing
  lifecycle and ownership responsibilities.

## Rejected Alternatives

Alternative B is not selected because it changes the current transition
authority boundary and depends on a missing reserved/delegable decision
taxonomy, grant lifecycle, identity, replay protection, revocation, and
qualification architecture.

Alternative C is not selected for current adoption because its identity,
authorization, audit, consistency, recovery, availability, security, service,
and qualification contracts are incomplete. It remains the future evolution
target described above.

Registry-as-authority, implementation-agent self-authorization, Git/metadata
activation, and unconstrained autonomous governance remain ineligible because
they conflict with existing authority and lifecycle boundaries.

## Remaining Review Items

No approval-blocking architectural question from the first Formal Architecture
Review remains unresolved. Future implementation work must assign concrete
schema identifiers, source paths, technologies, cryptographic algorithms,
retention periods, timeout values, and service operators within the owners and
invariants fixed here. DOC-0001 registration and every governing-record change
remain separate controlled actions; neither is performed by this revision.

## Evidence Traceability

- Phase 1 characterization: EWO-000023-PHASE-1-INVESTIGATION,
  EWO-000023-PHASE-1-AUTHORITY-BOUNDARY, and
  EWO-000023-PHASE-1-EVIDENCE.
- Phase 2 evaluation: EWO-000023-PHASE-2-ALTERNATIVES,
  EWO-000023-PHASE-2-COMPARATIVE-ANALYSIS,
  EWO-000023-PHASE-2-OWNERSHIP, and EWO-000023-PHASE-2-EVIDENCE.
- Phase 3 refinement and evidence: EWO-000023-PHASE-3-RECOMMENDATION,
  EWO-000023-PHASE-3-ROADMAP, EWO-000023-PHASE-3-REPOSITORY-IMPACT,
  EWO-000023-PHASE-3-EVIDENCE, and EWO-000023-PHASE-3-VALIDATION.

## Review and Adoption Boundary

Engineering Governance review may accept, reject, defer, or require revision
of this Draft. Approval, activation, governing-record revision, implementation,
qualification, publication commit, and operational adoption each require
separate explicit authority. No part of this Draft is self-executing.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 0.1 | 2026-07-18 | Prepared complete Draft EDR-0003 under EWO-000023 Phase 3 after Governance selected Alternative A and reserved Alternative C as a future evolution target. |
| 0.2 | 2026-07-18 | Resolved first-review approval blockers; incorporated Governance dispositions for alternatives and operational controlled-identifier allocation; completed trust, ownership, state, concurrency, recovery, audit, migration, interfaces, impact, and revocation architecture. |
| 0.3 | 2026-07-18 | Completed all logical interface contracts, assigned singular operational projection owners, defined terminal-transaction restart semantics, and recorded requirements for permanent architecture-governance process and lessons-learned persistence. |
