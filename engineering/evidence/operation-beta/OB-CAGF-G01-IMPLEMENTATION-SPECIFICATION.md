# OB-CAGF-G01 Implementation Specification

**Status:** Analysis candidate; pending operator review and separate WOP authoring
**Operation:** OPERATION-BETA
**Gate:** OB-CAGF-G01
**Repository baseline:** c0ca86279d4257a6248e620752bfc40247cf4d4e
**Authority:** None. This specification does not create a WOP, mission authority,
or implementation authorization.

## 1. Final bounded objective

Prove the CAGF architecture by defining and qualifying exactly one bounded
source-contract/projection family end-to-end. The reference implementation
shall make the existing Operation Beta mission/readiness projection
source-bound, deterministic, provenance-bearing, replay-safe, and fail-closed
without replacing canonical source owners or turning a generated projection
into authority.

This gate does not implement the broader CAGF-01 through CAGF-05 roadmap. Those
remain future, separately scoped development. CAGF-01 is a preferred producer
of the qualified capability, not an authority source for EPE or any other
mission.

## 2. Reference projection family

**Family:** Operation Beta mission/readiness projection manifest.

This is the smallest useful reference family because the repository already
has qualified Operation Beta and Zeus-native mission/readiness projections,
canonical owner records, repository/baseline resolution, drift detection, and
read-only verification surfaces. It exercises the complete CAGF contract while
limiting the generated result to one bounded projection. It is reusable by
Zeus, EPE, CM, EMP, and roadmap/architecture validation without creating a
second mission or source registry.

The family consists of a normalized projection plus an immutable manifest
containing the source-owner references, source revisions/digests, generator
identity/version, projection digest, qualification status, and publication
boundary. The projection is disposable derived state; the manifest is
provenance evidence, not authority.

## 3. Existing capabilities to reuse

| Existing owner/capability | Reuse boundary |
| --- | --- |
| Mission Knowledge Model | Mission identity, lifecycle, readiness, and dependency facts |
| Capability Registry | Capability identity and state |
| EMM | Source bindings and drift/divergence detection |
| PMCT/gate authority | Qualification and gate evidence |
| Engineering Governance | Applicable owner and approval records; no new approval is created here |
| EOS | Synchronized platform projection and consistency validation |
| Repository identity/baseline resolution | Canonical repository identity, branch, HEAD, origin, and baseline |
| Mission Contract/WOP resolution | Existing scoped execution-authority resolution; no synthetic contract or WOP |
| Receipt-backed lifecycle projections | Existing immutable receipt and provenance patterns |
| Zeus-native verification | Operation/mission/readiness/dependency/evidence/snapshot/next-action visibility |
| Drift detection | Existing stale/divergent source detection and fail-closed diagnostics |
| Replay/idempotency controls | Existing deterministic transaction and duplicate-prevention patterns |

No replacement source registry, lifecycle engine, authority resolver, or broad
projection generator is in scope.

## 4. Requirement-level implementation specification

| ID | Objective | Canonical source(s) | Reused capability | Missing capability | Boundary / output | Verification / evidence | Replay and failure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAGF-G01-R01 | Declare ownership for every input | MKM, Capability Registry, EMM, PMCT, Governance, repository identity, EOS | Existing owner map and resolvers | One bounded owner/source contract | Owner inventory and contract | Owner resolution test and owner manifest | Ambiguous or missing owner fails closed; replay preserves identity |
| CAGF-G01-R02 | Normalize source-bound inputs | Declared owners plus qualified Beta baseline | Existing canonical resolvers and baseline checks | Stable normalized input model | Canonical normalized input set | Schema, locator, baseline, and source-binding tests | Missing/malformed input fails closed; no fallback source |
| CAGF-G01-R03 | Establish stable digests | All normalized inputs and generator identity | Repository/EOS digest and provenance utilities | CAGF input digest material and digest schema | Per-source and aggregate digest | Digest reproducibility and provenance evidence | Changed input yields a new identity; unchanged input replays identically |
| CAGF-G01-R04 | Validate relationships | MKM, Registry, EMM, gate/authority records | Existing identity/dependency validators | Unified bounded identity/dependency/cycle/stale/conflict check | Validation result and diagnostics | Positive and malformed/contradictory fixtures | Any invalid relationship blocks generation and publication |
| CAGF-G01-R05 | Generate one deterministic projection | Qualified normalized input set | Existing Beta/Zeus projection shape | One bounded generator for mission/readiness family | Byte-stable projection artifact | Same-input byte comparison and golden fixture | No partial publication; repeated generation is deterministic |
| CAGF-G01-R06 | Preserve source/projection separation | Canonical owners and generated artifact | Existing projection-purity invariants | Explicit non-authoritative projection metadata | Projection marked derived with source bindings | Attempted authority consumption is rejected or diagnosed | Projection cannot become source or authority on replay |
| CAGF-G01-R07 | Emit provenance/publication manifest | Inputs, digests, generator, projection | Evidence provenance and receipt patterns | CAGF manifest schema and bounded publication record | Immutable manifest with projection locator/digest | Manifest completeness, digest binding, and receipt tests | Existing manifest is reused; altered manifest fails closed |
| CAGF-G01-R08 | Qualify byte stability | Qualified source contract and generator | Existing qualification procedures | Generator-level byte-stability qualification | Qualification result and immutable evidence | Two independent runs with identical bytes | Nondeterminism blocks qualification and publication |
| CAGF-G01-R09 | Qualify replay/idempotency | Same qualified source contract | Existing replay/idempotency controls | CAGF replay identity and duplicate guard | IDEMPOTENT replay result | First/replay comparison and artifact cardinality check | No duplicate authority, WOP, Mission Contract, or unintended artifact |
| CAGF-G01-R10 | Enforce bounded publication | Qualified projection and manifest | Governance/publication and EOS validation boundaries | Explicit CAGF publication boundary | Published candidate only after qualification | Publication eligibility, receipt, and repository/EOS checks | Missing qualification or stale baseline fails closed; no mutation on failure |
| CAGF-G01-R11 | Expose the capability through Zeus | Manifest and projection locator | Native operation/mission verification | CAGF-specific source/provenance fields in native verification if absent | Native status, blockers, snapshot, and next action | Zeus-native verification independently reconstructs result | Read-only verification never creates authority or execution |
| CAGF-G01-R12 | Preserve downstream technical usability | Qualified projection interface | Existing consumers and dependency projections | Stable consumer contract and compatibility fixture | `QUALIFIED_CANONICAL_SOURCE_PROJECTION`, digest, manifest | Consumer contract tests for EPE/CM/EMP/ARCH | Consumers depend on capability, never CAGF mission authority |

**Requirement count:** 12.

## 5. Contracts

### Canonical source contract

The contract must enumerate each input owner, locator, revision/baseline,
schema, freshness rule, identity key, dependency references, and digest
material. It must identify the repository and EOS baseline and explicitly mark
authority-bearing records as external inputs. No generated field may be
reinterpreted as authority.

### Projection contract

The generator accepts only the normalized, validated input set and emits one
bounded Operation Beta mission/readiness projection. The output ordering,
serialization, schema, generator version, and derived-state marker are stable.
It contains source references and digests but does not contain authority,
selection, admission, WOP, execution, or publication powers.

### Provenance contract

The immutable manifest records the gate, projection family, input locators and
digests, aggregate input digest, generator identity/version, output digest,
repository identity/baseline, qualification result, publication result, and
receipt locator. Manifest identity is derived from immutable content and is
not a mission or authority identity.

### Publication contract

Only a qualified projection and complete manifest may cross the bounded
publication boundary. Publication is scoped to the reference family and
current baseline. It must preserve prior immutable evidence and must not create
a Mission Contract, WOP, execution, selection, or new operator decision.

### Fail-closed contract

Missing, stale, malformed, conflicting, ambiguous, identity-invalid,
dependency-invalid, cycle-forming, nondeterministic, or baseline-incompatible
inputs fail closed with the exact diagnostic. No partial projection or
manifest is published, and existing authoritative records remain untouched.

### Replay/idempotency contract

An identical qualified input set and generator version resolves to the same
projection and manifest identity, reports `REPLAY=IDEMPOTENT`, and creates no
duplicate authority, execution, WOP, Mission Contract, receipt, or unintended
artifact. Changed inputs produce a new derived identity and require fresh
qualification.

### Zeus-native verification contract

Zeus must independently expose the projection family, source/manifest
identity, qualification state, blockers, derived/non-authoritative status,
repository/baseline binding, and next action through supported read-only
operation/mission/gate/snapshot or equivalent commands. Inspecting generator
internals must not be required.

## 6. Downstream technical inputs

The qualified output enables:

* EPE: `QUALIFIED_CANONICAL_SOURCE_PROJECTION` for executable mission
  contract/task-state foundation; it does not require CAGF authority or the
  CAGF mission identifier.
* CM: canonical package/resolver integration without a competing source.
* EMP: management and roadmap projections over canonical source bindings.
* OB-ARCH-G01: roadmap/source provenance and consistency projection.
* Integrated qualification: source-bound lifecycle and repository/EOS
  reconciliation evidence.

These are technical capability dependencies only. Mission authority remains
independent and recommendation, selection, roadmap order, and completion of a
different mission create no authority.

## 7. WOP-package architecture assessment

The existing WOP contract already provides immutable semantic/package identity,
integrity and digest binding, authority separation, normalized resolution,
verification ordering, gate/evidence/recovery/closeout contract slots,
interruption/resume semantics, fail-closed ambiguity behavior, and immutable
publication receipts. It also explicitly keeps WOP content separate from
authority.

It does not, unchanged, provide the CAGF-specific source-contract manifest,
canonical-input digest set, deterministic projection-output contract, or
generator-level byte-stability/replay evidence. The WOP architecture should
therefore be **extended**, not replaced, before authoring the implementation
WOP. The extension should add a bounded CAGF gate profile/package section that
references the existing WOP identity, integrity, authority, recovery,
closeout, and publication contracts rather than duplicating them.

The future package must contain: immutable package identity and integrity;
authoritative bootstrap/execution document; gate objective/requirements;
verification-first order; detection/adoption of satisfied requirements;
technical prerequisite resolution; explicit execution order; idempotent
execution; evidence contracts; qualification; interruption recovery; failure
handling; publication boundaries; repository/EOS reconciliation;
Zeus-native lifecycle/status/blocker/next-action/snapshot verification; and
closeout. No package field may create mission-to-mission authority.

## 8. Acceptance model

OB-CAGF-G01 is accepted only when all twelve requirements pass, the same
qualified inputs produce byte-identical output, ownership and provenance are
complete, missing/stale/conflicting/invalid inputs fail closed, the generated
projection is proven non-authoritative, the manifest and bounded publication
receipt are immutable and complete, replay is idempotent, repository/EOS
consistency remains valid, and Zeus independently verifies the result. The
gate remains `NEW_UNSATISFIED` until a separately authorized implementation,
qualification, and publication process produces that evidence.

## 9. Current disposition

No CAGF implementation, WOP, mission selection, authority, execution, staging,
publication, commit, push, or EOS synchronization was performed for this
analysis. The catalog requires clarification: its prior `CAGF_01_through_05`
traceability is too broad for this gate and is corrected to one bounded
reference projection family; CAGF-01..05 remain future staged development.

