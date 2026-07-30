# Zeus Authority Pipeline Resolution Specification

Mission: `ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001`

Date: 2026-07-29

Status: planning proposal for operator review; not an authority artifact,
Mission Contract, admission, receipt, activation, execution decision, or OA
gate decision.

## 1. Decisions

The final pipeline shall be:

```text
operator-approved mission intent
  -> exactly one repository Mission Contract
  -> immutable WOP + WOP publication receipt + Admission Record
  -> owner publications + observed execution state
  -> ARS canonical Resolved Execution Authority Context (REAC)
  -> Progressive Mission Authority gate-eligibility result (when applicable)
  -> EWI one terminal initiation decision
  -> execution bound to the REAC digest
  -> typed evidence, effect, and reconciliation receipts
```

The canonical repository is
`/data/engineering/repositories/homelab`. It is the only maintained Homelab
working tree.

The authoritative Mission Contract store shall be
`engineering/mission-contracts/contracts/`, using
`engineering/mission-contracts/mission-contract.schema.yaml` and exactly-one,
fail-closed resolution. `engineering/execution/missions/` shall be migrated to
a derived execution projection or retired; it shall not remain a second
Mission Contract store.

The Authority Resolution Service (ARS) shall become the sole producer of the
canonical resolved authority object. The proposed name `Resolved Execution
Authority Context` distinguishes it from the current locator-only
`ResolvedZeusAuthorizationBundle`; its initial schema should evolve
`engineering/authority/authority-resolution-bundle.schema.yaml` rather than
create a third model.

The Authorization Bundle shall remain temporarily as a compatibility input
manifest. It may locate a Mission Contract, WOP, WOP publication receipt,
Admission Record, owner publications, and observed state for ARS. It may not
contain an independent allow decision or substitute fixture compatibility
artifacts. EWI legacy environment locators shall be deprecated, instrumented,
and removed after all callers select the canonical ARS input path. The
locator-only resolved object is then retired.

The offline Authority Graph and compatibility evaluator shall remain as
test/migration libraries. Production authority-chain resolution moves to ARS.
They shall not make a parallel production decision.

Progressive Mission Authority shall receive a verified REAC and add only
Progressive-specific eligibility checks: current gate, prior accepted gate
receipts, package/runtime integrity, gate capability constraints, and
Progressive repository policy. It may verify upstream bindings already in the
REAC but may not independently resolve Mission Contracts, authority owners,
or generic WOP/admission authority after migration.

EWI shall orchestrate repository observation, Mission Contract resolution,
WOP publication/admission verification, ARS resolution, optional
mission-profile validation, runtime dependency checks, and one terminal
decision. It shall neither reconstruct authority nor choose between competing
allow results.

## 2. Layer contracts and precedence

| Layer | Authoritative input | Owner / producer | Output | May block? | May authorize protected effects? |
|---|---|---|---|---|---|
| 1. Intent | operator handoff, approved roadmap, prohibitions | operator / named record owner | scoped mission intent | yes | no |
| 2. Mission Contract | repository contract store | Mission Contract lifecycle owner via activation transaction | exactly one active applicable contract and digest | yes | no, by itself |
| 3. WOP/admission | immutable WOP, WOP publication receipt, Admission Record | WOP Service; Admission Controller | verified package identity/integrity/admission | yes | no |
| 4. Resolution | signed owner publications, observations, layers 2–3 | ARS resolves; source owners retain fact ownership | sealed, expiring REAC | yes | yes, only as an input to EWI |
| 5. Mission profile | REAC plus Progressive package/gate state | Progressive Mission Authority | eligibility result bound to REAC digest | yes | no independent authority |
| 6. EWI | results from layers 2–5 and runtime preflight | EWI | exactly one Initiation Decision Record | yes | yes, when `ALLOW` |
| 7. Execution | EWI decision and exact REAC digest | executor and evidence services | effects/checkpoints/typed receipts | yes | only within bound capabilities |

Precedence is conjunctive and fail-closed, not “last writer wins.” A downstream
layer may narrow an upstream capability but never expand it. Any missing,
malformed, ambiguous, stale, mismatched, conflicted, revoked, superseded,
expired, or ineligible input produces a non-allow terminal result. Revocation
and supersedence override prior activation; exact identity/digest mismatch
overrides all positive states. No compatibility path may override ARS.

The terminal EWI states shall be:
`ALLOW`, `BLOCK`, `STALE`, `CONFLICTED`, or `INELIGIBLE`. The decision records
the first precedence-ranked terminal class plus all diagnostics, so reporting
does not depend on check order.

## 3. REAC integration contract

The REAC must be immutable, canonical-JSON digest bound, signed or sealed by
the ARS production mechanism, short-lived, and contain:

- resolution ID, schema/resolver version, issue/expiry time, and digest;
- mission contract ID/revision/digest/lifecycle;
- mission, phase, work item, WOP ID/digest, WOP publication receipt ID/digest,
  and Admission Record ID/digest;
- repository ID, canonical root, remote, branch, baseline, observed HEAD,
  working-tree policy/result, upstream observation and freshness evidence when
  the selected phase policy requires it;
- principal, approval, authority chain, effective capabilities, requested
  effects, prohibitions, revocations, supersedence, and provenance;
- current mission profile and gate, where applicable;
- reservations/lease bindings when required.

ARS must validate legitimate-owner publications, signatures, provenance,
freshness, scope, lifecycle, revocation, supersedence, and all cross-object
bindings. It must not originate any upstream fact. REAC selection is by
explicit mission/work/principal request plus exactly-one matching active
publication generation. Active publication pointers remain integrity-bound,
but a pointer alone is not authority.

Every consumer verifies the REAC schema, digest, seal, expiry, repository,
mission/WOP/admission, principal, capability, and requested-effect bindings.
Execution persists the REAC digest in every protected-effect receipt and
revalidates expiry/revocation at durable boundaries.

## 4. Component responsibility matrix

| Mechanism | Current producer / owner | Current store, schema, discovery, lifecycle | Current consumers / overlap | Target disposition |
|---|---|---|---|---|
| Authorization Bundle resolver | caller config; EWI owns normalization; source producer absent | `engineering/authorization/authorization-bundle.schema.yaml`; explicit `EOS_AUTHORIZATION_INPUT_MANIFEST`, then legacy env; invocation-lived | admission verifier and shadow evaluator; overlaps ARS input selection | **Adapt**, then retire locator-only resolved model. Temporary ARS input manifest with one active selector and lifecycle owner. |
| Compatibility evaluator | EWI/shadow code; compatibility library | `scripts/lib/authority_wop/compatibility.py`; explicit files; stateless | produces compatibility decision/ADR; overlaps ARS and Progressive checks | **Retain for fixtures/migration**, remove from production allow path after parity qualification. |
| Authority Graph | graph registrar is architectural owner; no production EWI publisher | `engineering/authority/authority-graph.schema.yaml`; explicit input; no production lifecycle | compatibility evaluator; overlaps operational authority chain | **Merge semantics into ARS**; retain offline validator/fixtures. |
| Evaluation State | no production owner found | WOP contract object; explicit input; no production store/lifecycle | compatibility evaluator; overlaps repository observation and PMA state | **Replace** with EWI observation snapshot plus profile-owned state references in REAC. |
| WOP publication receipt | WOP Service | compatibility receipt schema in WOP contract; explicit locator; create-only | compatibility evaluator | **Retain and productionize** with one schema/index/discovery rule. Never substitute activation or gate receipts. |
| Mission Contract resolver | Mission Contract lifecycle subsystem | `engineering/mission-contracts/contracts/*.yaml`; repository schema; sorted exactly-one resolution; activation/suspend/revoke/complete | Stage 1 and PMA | **Retain as sole contract resolver**; add mission/applicability selector without precedence shortcuts. |
| Progressive Mission Authority | Progressive OA implementation | `controlled_mission_authority.py`; hard-coded WOP/admission plus runtime receipt locators; re-evaluated at boundaries | protected Progressive operations; overlaps MC, admission, repo, compatibility | **Adapt** to consume REAC and own only profile eligibility. |
| ARS | AuthorityResolutionRuntime; source fact owners remain owners | runtime active pointer then append-only state; tracked migration fallback; ARB schema; 15-minute lifetime | proposed WOP generation, not EWI | **Retain and promote** as sole resolved-authority producer; emit REAC and integrate with EWI. |
| Authority publication framework | enrolled owner/signers; publication runtime | signed envelopes, append-only `.zeus/authority-publications`, `.zeus/runtime/authority/active-publication.json`; explicit activation | ARS | **Retain**; add mission-scoped generation index and freshness/supersedence checks. Historical P2-014 publication stays immutable. |
| Execution mission store | execution-interface tooling | `engineering/execution/missions/*.yaml`; separate schema/discovery | execution snapshot/interface only | **Convert to generated projection or retire** after field migration to authoritative contracts. |
| EWI | EOS/engctl orchestration | shell orchestration plus bundle resolver, admission, repository qualification, shadow/enforcement ADR | protected initiation | **Refactor** to orchestration only and one Initiation Decision Record. |
| Work Registry authority refs | EMP/registry owner | `engineering/registry/work-registry.yaml`; repository validation | Mission Contract/PMA/operations | **Retain as intent/status reference**, never substitute for active contract or REAC. Bind IDs/digests. |
| EOS authority projection | synchronization service | `engineering/eos/repository-eos-authority.yaml` -> `/data/engineering/eos`; repository-to-EOS | operator/runtime status | **Retain as derived projection**; regenerate only from canonical records. |
| Runtime authority pointer | publication activation runtime | `.zeus/runtime/authority/active-publication.json`; digest-bound atomic pointer | ARS | **Retain as derived active selector**, generated only by explicit activation and never hand-edited. |
| Admission Record | Admission Controller | `engineering/admission/admission-record.schema.yaml`; create-only runtime/package record | EWI, PMA, Stage 1 | **Retain**, index by WOP ID/digest and select exactly one accepted nonsuperseded record. |
| Gate acceptance receipt | operator acceptance path | package `runtime/decisions/<gate>` plus runtime locator/digest | PMA | **Retain**, profile-scoped and non-substitutable. |

The matrix's combined lifecycle column describes storage, schema, discovery,
and lifecycle; the following register makes authority level, precedence,
conflict, and missing integration explicit.

| Mechanism | Current purpose and authority level | Precedence | Conflict / missing integration |
|---|---|---|---|
| Authorization Bundle | locator manifest; non-authoritative | explicit bundle excludes conflicting legacy values | no producer, active selector, replacement, expiry, or ARS bridge |
| compatibility evaluator | generic compatibility decision; currently enforcement-capable in EWI | internal deterministic error order | duplicates production resolution without current production inputs |
| Authority Graph | authority delegation model; authoritative only for an explicitly selected evaluation | structural failure precedes resolution | not the operational signed-chain contract |
| Evaluation State | observed prerequisites/context; observational | mismatches deny | no production producer, freshness, or lifecycle |
| WOP publication receipt | authoritative proof of WOP publication only | exact ID/digest/type required | current Progressive receipt is missing from EWI discovery |
| Mission Contract resolver | authoritative mission selection | zero/many/invalid fail; exactly one only | execution mission store is invisible and schema-incompatible |
| Progressive Mission Authority | authoritative current Progressive boundary | narrows all upstream results | reconstructs generic authority and hard-codes package discovery |
| Authority Resolution Service | operational generic authority resolver | revocation/scope/freshness failures deny | canonical ARB is not consumed by EWI or PMA |
| authority publication framework | authoritative publication/activation lifecycle for owner facts | explicit activated generation; fallback only when no pointer | current generation is applicable to P2-014, not OA-06 |
| execution mission store | execution-interface mission description; authority level ambiguous | separate discovery only | duplicates Mission Contract concepts and has no bridge |
| Engineering Work Initiation | terminal initiation authority | all required layer results are conjunctive | currently composes locator/compatibility authority independently |
| Work Registry references | authoritative registry intent/status; not execution authority | must agree with Mission Contract/REAC | references are not uniformly digest-bound |
| EOS projections | derived operational view; non-authoritative | canonical repository always prevails | drift and reverse-edit prevention need enforcement |
| runtime authority pointer | authoritative current selector only, not source authority | runtime pointer before tracked migration fallback | global “active” selection lacks mission applicability |
| Admission Record | authoritative admission outcome only | exact accepted record and WOP digest required | discovery differs between EWI and PMA |
| gate acceptance receipt | authoritative gate acceptance only | earlier gates must be accepted; supersedence wins | separate schema/discovery must reject receipt substitution |

## 5. Receipt contracts

| Receipt | Sole owner | Purpose / creation | Discovery and lifecycle | Cannot substitute for |
|---|---|---|---|---|
| WOP publication | WOP Service | proves exact immutable WOP payload was published | WOP index by ID+digest; create-only; supersedence is separate record | admission, activation, gate acceptance |
| Authority activation | Authority publication runtime | proves a prepared signed publication generation was explicitly activated | active pointer + append-only generation; preserved after supersedence | WOP publication, execution allow |
| Admission Record | Admission Controller | proves package validation/admission result | index by WOP ID+digest; immutable; resubmission creates new record | upstream authority, gate acceptance |
| OA gate acceptance | operator gate acceptance owner | proves a verified gate was accepted | state locator + digest; append-only, with explicit supersedence | admission, authority activation |
| Execution receipt | execution/effect owner | proves a protected effect under EWI decision + REAC | append-only by execution/effect ID; interruption-safe | authority creation, reconciliation |
| Reconciliation receipt | reconciliation owner/operator acceptance | proves named records were compared and reconciled | append-only by reconciliation ID; links source/result digests | execution or upstream approval |

Each schema must require type, version, receipt ID, producer/owner, timestamp,
subject identities and digests, repository binding where relevant, provenance,
and supersedence link. Type mismatch is a hard failure.

## 6. Repository synchronization policy

`HEAD == origin/main` is not universal:

| Phase | Required repository policy |
|---|---|
| Development | canonical root/remote/branch, approved baseline ancestor, scoped dirty-tree policy; local commits allowed |
| Candidate qualification | exact candidate commit and tree digest; clean or declared controlled baseline; remote publication optional and explicit |
| Operator acceptance | exact immutable candidate digest; if accepting a published candidate, require fresh remote observation and equality |
| Published execution | exact published commit, clean tree, branch policy, fresh remote observation, `HEAD == verified origin/main` |
| Production execution | published-execution rules plus environment/deployment binding and periodic revocation/freshness recheck |

The present Progressive boundary remains fail-closed with
`HEAD == origin/main` until a separately approved policy replaces it.
Freshness proof shall record remote URL, refspec, fetch/query method, observed
remote object ID, timestamp, maximum age, and authenticated transport result.
A local tracking ref without that proof is stale. Development/qualification
must never silently fetch or mutate refs; an explicit non-authorizing
observation step produces the freshness evidence.

## 7. Dependency graph

```text
Intent
  |
  +--> Mission Contract --------+
  +--> WOP publication ---------+--> ARS --> REAC --+
       +--> Admission Record ---+                  |
  +--> owner publications ------+                  +--> profile validator
  +--> repository observation --+                  |       |
                                                     +-------+--> EWI decision
Runtime dependency preflight ----------------------------------+
                                                                  |
                                                                  v
                                                     execution/checkpoints
                                                                  |
                                                    typed evidence/effect receipts
                                                                  |
                                      repository records <--- controlled reconciliation
```

## 8. Duplicate-path retirement

Retire production use of: direct EWI compatibility allow decisions; legacy
`EOS_*` artifact locator composition; compatibility `EvaluationState` as an
independently published authority object; PMA reconstruction of Mission
Contract/generic authority; and `engineering/execution/missions/` as an
independently edited contract store. Preserve fixtures and historical records
under explicitly non-authoritative namespaces.
