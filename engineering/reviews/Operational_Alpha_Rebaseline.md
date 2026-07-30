# Zeus Operational Alpha Rebaseline

Review ID: `ENGINEERING-CONVERGENCE-REVIEW-001`  
Baseline assessment date: 2026-07-30  
Current Progressive state: OA-01–OA-05 accepted; OA-06 implementation required

## Rebaseline objective

Reach a reproducible Zeus Operational Alpha declaration through the shortest
dependency-ordered path, reusing implemented capabilities and eliminating
parallel authority paths.

## Rebaseline principles

1. Acceptance is cumulative and must follow OA order.
2. Existing implementation is reused unless a verified gap exists.
3. No compatibility adapter is built for obsolete external WOP semantics.
4. No production dispatch occurs until authority, admission, agent,
   repository, and evidence bindings all resolve through one path.
5. Publication and clean-checkout qualification are engineering milestones,
   not end-of-project paperwork.

## Milestone 0 — Preserve and characterize the candidate

**Outcome:** a declared candidate inventory without changing runtime.

- Record the exact dirty-tree boundary and classify tracked, modified,
  untracked, generated, runtime, evidence, and publication artifacts.
- Preserve the reviewed HEAD and existing working-tree baseline evidence.
- Identify which current implementations are absent from Git history.
- Exclude review artifacts and generated caches from runtime qualification.

**Exit:** every candidate path has an owner and intended publication unit.

## Milestone 1 — Decide the canonical authority topology

**Outcome:** one approved component ownership and decision model.

- Confirm Mission Contract store ownership.
- Confirm ARS resolved execution context as the sole generic authority output.
- Confirm PMA as Progressive-only narrowing.
- Confirm EWI as the terminal initiation decision.
- Assign owners to receipt types and state facts.
- Preserve current fail-closed repository policy until replacement is
  qualified.

**Eliminates:** debate over adapters, third authority models, and parallel
allow decisions.

## Milestone 2 — Reconcile contracts and schemas

**Outcome:** type-safe interfaces for the complete authority chain.

- Evolve the existing authority-resolution bundle into the resolved context.
- Define Mission Contract, WOP publication, admission, activation, gate
  acceptance, execution, qualification, and reconciliation bindings.
- Define expiry, freshness, revocation, supersedence, and ambiguity behavior.
- Map execution mission YAML to a projection or retirement plan.
- Add cross-receipt substitution rejection.

**Exit:** every required field has one owner and deterministic error precedence.

## Milestone 3 — Remove duplicate live dependencies

**Outcome:** one canonical repository/runtime path.

- Migrate current callers from legacy gate approval and external WOP records.
- Remove dead `oa02_lifecycle.py` routing.
- Narrow standalone PMCT to current observation/regression duties.
- Convert tests to temporary repository-local fixtures.
- Verify zero runtime/test consumers and zero active users of the external WOP.
- Preserve external evidence as historical; freeze/archive under separate
  authorization.

**Exit:** compatibility paths cannot authorize and the external tree is not a
runtime dependency.

## Milestone 4 — Integrate and qualify OA-06

**Outcome:** deterministic Mission Eligibility Evaluation without dispatch.

- ARS resolves exactly one current context.
- PMA validates current gate, predecessor receipts, package integrity, and
  Progressive policy from that context.
- Mission eligibility classifies staged missions deterministically.
- EWI produces a non-dispatching qualification decision.
- Exercise zero/one/many contracts, stale authority, wrong receipt type,
  revoked publication, repository mismatch, replay, and interruption cases.

**Exit:** OA-06 verification evidence is reproducible and operator acceptance
can occur under its existing lifecycle.

## Milestone 5 — Publish the converged candidate

**Outcome:** clean, reproducible baseline.

- Complete publication units strictly in dependency order.
- Publish PU-01B before PU-01C; then publish the frozen PU-01C boundary.
- Include only declared paths and reproduce accepted qualification
  fingerprints.
- Validate from a clean checkout.
- Reconcile only publication-owned metadata and projections.

**Exit:** current architecture and implementation exist in an authoritative
commit/tag baseline; no runtime behavior changes during publication.

## Milestone 6 — Qualify existing execution foundation, OA-07–OA-15

**Outcome:** integrated production foundation proven before protected work.

| Gates | Focus | Expected work |
|---|---|---|
| OA-07–OA-10 | agent invocation, admission-driven dispatch, CLI execution, EENS lifecycle | Integrate and qualify existing components |
| OA-11–OA-13 | signed evidence, independent qualification, live reconciliation | Bind identities/digests and qualify existing engines |
| OA-14 | authority restoration | Implement the missing coordinator; reuse resolver and reconciliation |
| OA-15 | integrated production foundation | Cumulative non-destructive qualification and commissioning readiness |

Do not implement a new dispatcher, event service, qualification engine, or
reconciliation engine.

## Milestone 7 — Controlled publication and commissioning, OA-16–OA-23

**Outcome:** published execution baseline with a qualified production agent and
admitted operational mission.

- OA-16 reconcile controlled documents.
- OA-17 create the production implementation commit.
- OA-18 republish the signed repository baseline.
- OA-19 commission dispatcher.
- OA-20 activate a qualified production execution agent.
- OA-21 authorize one bounded operational qualification mission.
- OA-22 construct its complete WOP.
- OA-23 admit it with dispatch explicitly permitted.

Reuse the existing owner publication, dispatcher, agent, admission, and WOP
implementations.

## Milestone 8 — First real mission and Alpha declaration, OA-24–OA-30

**Outcome:** Zeus completes one real bounded operational mission and is
independently qualified.

- Dispatch one low-risk, reversible WOP.
- Execute through checkpoints with revalidation.
- Produce signed evidence.
- Independently qualify it.
- Reconcile authoritative project state.
- Close the mission.
- Perform cumulative Operational Alpha qualification.
- Obtain separate declaration/freeze authority.

## Critical path

```text
candidate inventory
  -> topology decision
  -> contract/schema convergence
  -> duplicate-path retirement
  -> OA-06 qualification/acceptance
  -> ordered baseline publication
  -> OA-07–OA-15 integration qualification
  -> OA-16–OA-23 commissioning
  -> OA-24–OA-28 first real mission
  -> OA-29 qualification
  -> OA-30 declaration
```

## Work to merge

- Merge generic authority resolution into one ARS resolved-context path.
- Merge gate lifecycle routing onto Progressive Gate Service.
- Merge mission discovery onto the controlled Mission Contract store.
- Merge status/next-action projection onto Progressive lifecycle for current OA.
- Merge evidence discovery through a catalogue, while retaining distinct
  evidence owners.

## Work to eliminate

- External WOP compatibility adapter
- New dispatcher/executor/qualification/reconciliation implementations
- Independent execution Mission Contract authoring
- Legacy OA-02 lifecycle
- Parallel production compatibility decisions
- Broad pre-alpha repository reorganization

## Work to defer

- HNS expansion for EENS
- Generalized multi-project topology registry
- Rich UI and notification enhancements
- Historical document relocation
- Automated organization cleanup beyond qualification needs
- Nonessential telemetry and reporting enhancements

## Immediate next mission

**OA-06 Authority Path Convergence and Qualification**

Bound it to architecture decision, schema reconciliation, consumer migration,
test isolation, non-dispatching integration, and OA-06 evidence. Publication
should be a following controlled transaction once the candidate passes.

## Rebaselined readiness statement

Zeus is past foundational prototype stage but before Operational Alpha. The
verified baseline is five accepted Progressive gates plus substantial
downstream reusable implementation. The remaining program is primarily
authority convergence, publication, integration qualification, and one real
operational demonstration—not 25 greenfield capability builds.

