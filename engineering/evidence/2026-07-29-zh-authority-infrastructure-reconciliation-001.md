# ZH-AUTHORITY-INFRASTRUCTURE-RECONCILIATION-001

Status: engineering reconciliation findings; not an authorization artifact,
Mission Contract, admission decision, publication, lifecycle transition, or
Operational Alpha implementation.

Date: 2026-07-29

## 1. Disposition

Engineering Work Initiation (EWI) authority is not resolvable from the current
repository without additional, legitimately produced authority publications
and an explicit integration decision. OA-06 remains blocked.

No authority was fabricated, no publication or receipt was created, no
validation was weakened, and no OA-06 implementation or later-gate activity
was performed.

The remaining blockers are:

1. EWI has no selected Authorization Bundle and no populated legacy locator
   inputs. Its resolver therefore correctly returns an empty
   `ResolvedZeusAuthorizationBundle`.
2. The Authorization Bundle contract defines consumers and resolution
   semantics but does not define an authorized producer, publication timing,
   canonical repository/runtime locator, discovery index, replacement
   lifecycle, or retention contract.
3. No complete, non-fixture compatibility artifact set was found for the
   current Progressive OA WOP. The admission record and immutable WOP exist,
   but a compatible authority graph publication, evaluation state, and WOP
   publication receipt for this WOP were not found.
4. The operational Authority Resolution Service (ARS), EWI compatibility
   evaluator, Mission Contract resolver, Progressive Mission Authority, and
   execution-mission store are separate authority paths. No implemented,
   documented bridge turns the current Mission Contract/Progressive authority
   chain into EWI's five required locator inputs.
5. Progressive Mission Authority resolves every OA-06 prerequisite through
   the OA-05 receipt, then rejects the repository as `STALE` because local
   `HEAD` is two commits ahead of `origin/main`.
6. The active operational authority publication is integrity-discoverable but
   is scoped to `EMP-WORK-ZEUS-P2-014-COMMISSIONING` and binds repository
   baseline `966bba87c10a3cb9edbf1a771c9e53ce17fb289e`, not current HEAD or the
   Progressive OA work item. It is historical/current for its own publication
   contract, not sufficient authority for OA-06.
7. Four authority regressions depend on the live repository being at OA-02.
   At OA-06 they fail at the active-gate check and no longer test their stated
   conditions deterministically.

## 2. Observed repository state

| Item | Observation |
|---|---|
| Repository | `/data/engineering/repositories/homelab` |
| Branch | `main` |
| HEAD | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| `origin/main` | `f79462bd837df51f12a103f2ebc69a071c27f45d` |
| Divergence | ahead 2, behind 0 |
| Progressive active gate | `OA-06`, `IMPLEMENTATION_REQUIRED` |
| Prior gates | OA-01 through OA-05 `ACCEPTED`, receipts verified by Mission Authority |
| Selected EWI bundle | none |
| Legacy EWI locator variables | none populated |
| Active Mission Contract store | one valid active contract in `engineering/mission-contracts/contracts` |
| Runtime authority pointer | `.zeus/runtime/authority/active-publication.json` |
| Runtime authority status | integrity-resolved; P2-014 work item and stale repository baseline |

The working tree contained extensive pre-existing modified and untracked work.
This investigation preserved it.

## 3. Authority architecture analysis

The repository contains multiple similarly named but non-interchangeable
objects.

### 3.1 Authorization Bundle (EWI locator contract)

`ZeusAuthorizationBundle` is a manifest whose required locators are:

- `admission_record`
- `authority_graph`
- `wop`
- `state`
- `receipt`

Optional locators are `lease` and `revocation`; `expected_authority` is an
optional value. The resolver validates shape, resolves relative paths against
the bundle directory, requires regular files, derives `wop_id`, and rejects
canonical/legacy conflicts. It does not evaluate or grant authority.

Producer: not established.

Owner: EWI owns resolution and the transient resolved object; each referenced
artifact retains its existing owner. Ownership of the source bundle itself is
explicitly unresolved.

Publication timing and lifecycle: not established. Architecture documentation
states that creation, replacement, retention, and controlled-document status
require separate authority.

Discovery: only explicit `EOS_AUTHORIZATION_INPUT_MANIFEST`; otherwise explicit
legacy environment variables. There is no filesystem scan, repository default,
active pointer, Mission Contract lookup, or precedence search.

Consumers: admission verification and `work-initiation-shadow`.

### 3.2 Authority Graph

The compatibility Authority Graph is an offline, explicitly supplied graph
validated by `scripts/lib/authority/engine.py`. It requires exactly one root,
one parent per non-root node, decreasing rank, a single domain, and
non-expanding capability subsets.

Producer/owner: described as Governance Authority Graph Registrar in the ARS
architecture; no current EWI production publisher is identified.

Publication timing/lifecycle: not established for EWI. The design explicitly
limits the engine to fixtures and explicit offline inputs until a separately
approved migration/integration exists.

Discovery: none; its locator must arrive through the Authorization Bundle or
legacy environment.

Consumer: compatibility evaluator through `work-initiation-shadow`.

The `authority_node` envelopes and resolved chain in operational authority
state are not the same file contract as the offline graph and are not
automatically adapted to it.

### 3.3 Evaluation State

`EvaluationState` is runtime observation input for prerequisites,
dependencies, requested effects, principal, repository, baseline, and branch.

Producer/owner: no production producer or owner was found for the EWI path.

Publication timing/lifecycle: no contract found.

Discovery: none; explicit bundle/environment locator only.

Consumer: compatibility evaluator.

This is the clearest missing lifecycle contract. Repository search found
fixtures used by tests but no current Progressive OA evaluation-state
publication.

### 3.4 Admission Record

The Admission Controller owns an immutable `ACCEPTED` or
`RESUBMISSION_REQUIRED` validation outcome. It validates a submitted WOP,
persists a create-only record, and cannot originate upstream authority.

Producer: `wop-admissionctl` / Admission Controller.

Owner: Admission Controller.

Publication timing: after WOP submission validation and before EWI.

Discovery:

- EWI: explicit Authorization Bundle/environment locator;
- Progressive Mission Authority: fixed package path
  `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/admission/`
  with a hard-coded admission filename.

Consumer: EWI admission verifier and Progressive Mission Authority.

The current Progressive admission record exists and validates, but EWI does
not discover it automatically.

### 3.5 Publication Receipt

The compatibility receipt binds `receipt_id`, `wop_id`, `payload_digest`,
`published_at`, and `publisher_id` to an immutable WOP.

Producer/owner: WOP Service according to the ARS architecture.

Publication timing: after exact-payload authorization and create-only WOP
publication; before admission/EWI evaluation.

Discovery: none; explicit bundle/environment locator only.

Consumer: compatibility evaluator.

The authority-publication framework's readiness and activation receipts and
the Progressive gate acceptance receipts are different contracts. Repository
evidence explicitly says authority activation does not define a separate
WOP `publication-receipt`. None may be substituted for it.

### 3.6 Resolved Authorization Bundle

`ResolvedZeusAuthorizationBundle` is transient normalized JSON produced on
each EWI call. EWI owns it. It is neither sealed nor published, and contains
locators rather than resolved authority facts. Its lifecycle ends with the
invocation.

This object must not be confused with the proposed ARS
`AuthorityResolutionBundle` (`ARB-...`), which is a sealed, expiring authority
snapshot with provenance and reservations.

### 3.7 Operational Authority Resolution Bundle

ARS reads owner-specific authority publications, validates their bindings, and
can seal an ARB. The Authority Publication Framework constructs signed
envelopes, verifies readiness, explicitly activates an append-only runtime
publication, writes an integrity-bound active pointer, and records activation
receipts.

Producer: `AuthorityResolutionRuntime` after owner publications have been
explicitly activated.

Owner: ARS owns resolution only; source facts retain their recorded owners.

Publication timing: after signed-envelope readiness and explicit activation;
ARB issuance occurs on a mission/work/principal request and expires after 15
minutes.

Discovery: `.zeus/runtime/authority/active-publication.json`, then its
digest-bound state and artifact manifest; tracked
`engineering/authority/operational-authority-state.yaml` is a migration
fallback only when no runtime pointer exists.

Consumers: ARS/WOP generation architecture. EWI does not consume this ARB.

### 3.8 Mission Contract and Progressive Mission Authority

The operational Mission Contract resolver scans exactly
`engineering/mission-contracts/contracts/*.yaml`, sorts paths, validates every
candidate, and permits exactly one valid active applicable contract. It checks
repository root/identity, branch, qualified baseline ancestry, dirty-tree
policy, WOP locator/digest, roles, approval, and lifecycle.

Progressive Mission Authority then validates fixed/current package sources:
the resolved Mission Contract, fixed immutable WOP, fixed admission record,
runtime state, prior gate receipts derived from state, Work Registry, Project
State, EOS source, repository identity/remote/branch, exact HEAD/upstream
equality, and baseline ancestry.

Producer: Mission Contract activation transaction plus the independent
producers of WOP, admission, gate state, and acceptance receipts.

Consumers: protected Progressive OA operations.

`engineering/execution/missions/*.yaml` is a separate store with a different
schema (`status` and nested lifecycle rather than top-level `lifecycle`).
Neither the operational Mission Contract resolver nor EWI scans it. The
OA-06-specific record in that store therefore does not participate in either
authority decision. Whether it should is contractually ambiguous; treating it
as current authority without an integration contract would manufacture
authority.

## 4. Execution authority dependency graph

```text
Explicit bundle path ─┐
Legacy env locators ──┴─> EWI Authorization Bundle resolver
                              │
                              ├─> admission record + derived WOP ID
                              │      └─> Admission Controller verification
                              └─> graph + WOP + state + WOP receipt
                                     └─> compatibility evaluator
                                            └─> ADR + EWI allow/deny

Mission Contract store ─> exactly-one resolver ─┐
Progressive WOP + admission + runtime state ────┤
OA-01..OA-05 acceptance receipts ───────────────┤
Work Registry + repository Git observations ───┴─> Progressive Mission Authority
                                                       └─> protected OA boundary

Signed authority envelopes ─> readiness ─> explicit activation
    └─> runtime active pointer ─> authority state ─> ARS ─> sealed ARB
                                                        └─> proposed WOP finalization

engineering/execution/missions/*.yaml ─> separate execution-interface discovery

There is no implemented edge from Mission Authority, execution missions, or
the ARS ARB to the EWI Authorization Bundle.
```

## 5. Discovery analysis

| Resolver | Search location / selector | Identifier and filename rules | Precedence |
|---|---|---|---|
| EWI bundle | `EOS_AUTHORIZATION_INPUT_MANIFEST` | Any JSON/YAML mapping at the explicit path; type/version and five locators required | Selected canonical bundle is exclusive; conflicting legacy values fail |
| EWI legacy | eight `EOS_*` variables | Explicit file paths; WOP must contain `WOP-` ID when present | Used only when no canonical bundle is selected |
| Mission Contract | `engineering/mission-contracts/contracts/*.yaml` | Any filename; content identity; sorted; exactly one active applicable contract | No silent precedence; ambiguity fails |
| Execution mission | `engineering/execution/missions/*.yaml` through separate discovery implementation | Content identity and schema | Not visible to Mission Contract/EWI resolvers |
| Progressive WOP/admission | fixed package path and hard-coded admission filename | Package-specific IDs and digests | No search or fallback |
| Prior OA receipts | locator in runtime state; basename maps under `runtime/decisions/<gate>` | current receipt plus digest/marker binding | Runtime state's current locator governs |
| Operational authority state | runtime `active-publication.json` | bounded relative paths and SHA-256 artifact manifest | Runtime pointer first; tracked state only if pointer absent |
| Authority envelopes | `engineering/authority/publications/*.json` plus `.sig` | record type/ID/revision, owner, signer, payload digest | explicit activation; no unsigned fallback |

Findings:

- EWI behavior is deterministic but not discoverable: absence of configuration
  deterministically yields empty values.
- Mission Contract discovery is deterministic and currently resolves one valid
  active contract, but that contract is publication/bootstrap scoped and is
  not an EWI artifact bundle.
- Progressive source discovery is deterministic but contains package-specific
  constants and a hard-coded admission identity.
- The authority publication pointer and integrity chain are deterministic and
  valid, but their contents are stale/inapplicable to OA-06.
- Two Mission Contract stores with incompatible schemas and consumers make the
  repository authority topology ambiguous.

## 6. Why the resolver fields are empty

The output

```text
ResolvedZeusAuthorizationBundle
admission_record=""
authority_graph=""
receipt=""
state=""
wop=""
```

is produced by design in `resolve(None)`:

1. no `EOS_AUTHORIZATION_INPUT_MANIFEST` is set;
2. the resolver reads only the documented legacy environment map;
3. none of the required legacy variables is set;
4. it inserts empty defaults for every required field;
5. it performs no repository or publication discovery.

Therefore the immediate cause is absent input selection, not bad filesystem
locator logic. The larger defect is an incomplete production contract: no
component is responsible for selecting/publishing a current canonical bundle.

Even if the current admission and WOP paths were manually supplied, the
repository lacks a proven current production evaluation state and compatible
WOP publication receipt for the Progressive WOP. A fixture graph or receipt
must not be promoted merely to complete the form.

## 7. HEAD versus `origin/main`

### Source

The exact invariant is implemented in
`ControlledMissionAuthority.resolve()` and independently in OA-01 gate
verification. Progressive OA's gate contract requires one synchronized,
integrity-valid repository and records exact HEAD/upstream evidence.

The general Mission Contract resolver is less strict: its baseline need only
be an ancestor of HEAD, subject to dirty-tree policy. The ARS runtime requires
its published repository baseline to equal observed HEAD, but does not compare
HEAD with upstream. EWI compatibility enforcement binds evaluation state to
observed HEAD, also without an upstream comparison.

No repository-wide controlled contract was found that states
`HEAD == origin/main` for every EWI or every phase.

### Rationale and phase assessment

| Phase | Evidence-backed assessment |
|---|---|
| Development | Exact upstream equality is not generally suitable: legitimate unpublished commits are expected. Use repository identity, branch, baseline ancestry, and scoped dirty-tree controls. |
| Engineering qualification | Equality is appropriate only when the qualification subject claims a published/current production baseline. Candidate qualification can bind an exact local commit without asserting remote publication. |
| Operator approval/acceptance | Equality is appropriate when the approval binds the remotely published candidate. Otherwise require an exact immutable candidate fingerprint and make publication state explicit. |
| Production execution | Equality is a defensible fail-closed requirement when `origin/main` is the declared deployment authority, but remote-ref freshness must also be established; equality to a stale local tracking ref is insufficient. |

For current Progressive protected operations the code and OA-01 contract make
the check intentional. It should not be changed during this reconciliation.
Its cross-phase applicability remains insufficiently documented.

Current observed result: all OA-06 Mission Authority checks through OA-05
acceptance pass, followed by `STALE / head_binding` because
`d0861dc... != f79462b...`.

## 8. Validation evidence

Read-only/temporary validation performed:

- Authorization Bundle resolver with the current environment: reproduced the
  empty legacy-environment result.
- Mission Contract discovery: two candidates, one valid active contract,
  result `DISCOVERED`.
- Mission Contract resolver: result `AUTHORIZED` for
  `MC-MISSION-CONTRACT-PUBLICATION-001`.
- Progressive Mission Authority at expected gate OA-06: contract, WOP,
  admission, active gate, and OA-01 through OA-05 acceptance checks pass;
  HEAD/upstream check fails `STALE`.
- Authority publication status: `READY`, ten prepared signed envelopes, no
  commissioning blockers.
- Active authority pointer: integrity-valid and resolves to an append-only
  runtime publication.
- Focused unit suite: 67 tests run, 63 passed, 4 failed. All four failures are
  in `test-zeus-oa02-controlled-authority.py` and result from coupling the test
  defaults to the live repository's current gate.

No full EWI qualification was invoked because, after admission, it persists an
ADR; the read-only resolver result already proves the pre-admission blocker.

## 9. Issue classification

| Issue | Long-term classification |
|---|---|
| No bundle producer/selector/lifecycle | contract clarification plus engineering enhancement |
| Empty resolver with no inputs | correct implementation behavior; missing publication/configuration |
| Missing current compatibility graph/state/receipt set | publication correction, if compatibility EWI remains authoritative |
| No bridge among ARS, Mission Authority, and EWI | implementation correction following contract decision |
| Two Mission Contract stores | repository/contract clarification; then repository correction |
| Active authority publication scoped to P2-014 and old baseline | publication correction; do not rewrite historical publication |
| HEAD/upstream equality at Progressive boundary | intentional implementation; phase applicability needs contract clarification |
| OA-02 tests coupled to live OA state | implementation correction |
| Hard-coded Progressive admission filename | engineering enhancement, unless the receipt is replaced |

## 10. Immediate corrections required before OA-06

These are prerequisites, not authorization to perform them.

1. Decide and record which authority pipeline EWI must consume:
   the compatibility artifact bundle, an adapter from the operational ARB, or
   an explicitly unified Mission Authority contract. Do not allow parallel
   authoritative decisions.
2. Assign an authorized producer and owner for the source Authorization
   Bundle, including creation trigger, canonical active locator, replacement,
   revocation/supersedence, retention, and consumer handoff.
3. Produce through existing legitimate owners—not by reconstruction or
   fixtures—the complete current authority set for the Progressive OA WOP:
   admission record, graph/chain representation required by the selected
   evaluator, immutable WOP, evaluation state, and WOP publication receipt.
4. Implement and qualify deterministic selection of the active bundle or
   selected replacement contract. Absence, ambiguity, stale binding, or
   partial publication must fail before EWI with field-specific diagnostics.
5. Reconcile the operational authority publication through its append-only
   publication lifecycle so the selected authority source is bound to the
   current Progressive OA work item and an applicable repository baseline.
   Preserve P2-014 history.
6. Resolve the two Mission Contract stores: designate which is authoritative
   for EWI/Progressive operations and either integrate or explicitly classify
   the other as non-authoritative input.
7. Establish a legitimately published/synchronized execution baseline before
   retrying the current Progressive protected boundary. Do not bypass or relax
   the current `HEAD == upstream` check.
8. Make the Controlled Mission Authority tests use isolated repository state
   and explicit gate fixtures so authority qualification is deterministic at
   any live OA gate.
9. Run a preflight completeness check, focused authority suites, and EWI in a
   non-dispatching qualification context. Require exact current bindings and
   preserve the resulting evidence before OA-06 is allowed to resume.

Until all nine are completed and independently validated, the precise
remaining EWI decision is `BLOCKED_AUTHORITY_INFRASTRUCTURE`.

## 11. Deferred improvements

- Add `engctl`/Zeus authority preflight that reports the selected pipeline,
  producer, active locator, source digests, WOP identity, completeness,
  freshness, repository binding, and exact next corrective owner before EWI.
- Add automatic publication validation across bundle, ARS state, Mission
  Contract, WOP, admission, receipt, and gate-receipt identities.
- Add one machine-readable authority topology/index so every authority store
  declares schema, owner, consumer, precedence, lifecycle, and whether it is
  authoritative or evidentiary.
- Replace hard-coded admission filenames with digest-bound discovery from an
  immutable package index while retaining exactly-one semantics.
- Distinguish repository development, candidate qualification, published
  approval, and production-execution synchronization policies.
- Verify remote-ref freshness before treating tracking-ref equality as
  production synchronization.
- Add structured failure output listing every missing bundle field and the
  expected producer rather than allowing empty normalization to defer the
  first failure to admission.
- Add expiry, supersedence, and revocation checks to active bundle selection.
- Add negative tests for cross-store Mission Contract ambiguity and for
  accidental substitution among WOP publication, authority activation, and
  OA gate acceptance receipts.
- Add a read-only self-validation mode that creates no ADR, admission record,
  activation receipt, state transition, or dispatch.

## 12. Completion boundary

This report explains every observed authority blocker and validates every
implemented discovery path in scope. It does not claim that authority has been
restored. Restoration requires legitimate owner publications and an explicit
integration contract, neither of which may be inferred by this engineering
reconciliation.

OA-06 shall not advance on the basis of this report.
