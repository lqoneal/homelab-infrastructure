# Operational Alpha Lifecycle Dependency Analysis

Proposal: `OA-ROADMAP-HF-005`
Status: `PROPOSED — NON-AUTHORITATIVE`

## 1. Scope and method

This is an independent reconstruction of the lifecycle, not a restatement of
the execution narrative. It models (a) ordered OA gate acceptance and (b) the
bounded mission instance proved by those gates. A gate receipt is a roadmap
qualification fact; it is not mission authority. A mission retry or corrective
successor has a new subject identity and is therefore not a backwards edge in
the same lifecycle instance.

The one valid initial condition is `S00`: a resolved, attributable Governance
decision for a bounded subject. It is an input to OA-02 rather than an OA gate.
The sole normal terminal condition is `S22`: closed mission outcome. `S23` is
a separate roadmap-qualification terminal after OA-30 and is not a declaration,
baseline, publication, or activation state.

## 2. Deterministic model

```text
S00 decision -> S01 repository -> S02 effective authority -> S03 contract
 -> S04 context -> S05 staged -> S06 eligible snapshot -> S07 selection
 -> S08 qualified WOP -> S09 admitted candidate -> S10 EWI decision
 -> S11 running attempt -> S12 observed/protected boundary -> S13 evidence
 -> S14 qualification -> S15 completion -> S16 acceptance -> S17 reconciliation
 -> S22 closeout

S11 -- interruption --> S18 interrupted -> S19 recovery-validated -> S11
S14 -- failed qualification --> S20 corrective disposition -> successor S00/S02
S22 -> S21 representative-lifecycle proof -> S23 execution candidate
```

`S18 -> S19 -> S11` is a controlled re-entry to the same attempt only after a
higher fence and a proven-safe checkpoint. `S20` ends the current subject; a
successor starts a distinct instance. Neither path is an admission, authority,
or ownership cycle.

## 3. Lifecycle State Model

| State | Description | Produced by | Consumed by | Authoritative owner | Entry / exit | Persistence |
|---|---|---|---|---|---|---|
| S00 | bounded Governance decision | Governance | authority issuance | Governance | attributable decision / sealed decision | immutable record |
| S01 | identified repository and baseline | repository/baseline owner | authority, context | repository owner | identity resolves / integrity-valid observation | immutable observation |
| S02 | one effective Authority Record | Governance + resolver predicate | contract, WOP, EWI | Governance | S00 + valid lineage / effectiveness receipt | immutable record/receipt |
| S03 | deterministic Mission Contract | EMP | context, WOP, EWI | EMP | S02 + fixed mapping / byte-reproducible contract | immutable artifact |
| S04 | owner-resolved execution context | source owners; resolver composes | planning and admission | each source owner | S01–S03 resolve / one REAC | frozen observation |
| S05 | stable staged mission inventory | EMP | eligibility | EMP | owner planning inputs / stable identities | versioned inventory |
| S06 | eligible candidate snapshot | EMP | selection | EMP | S05 + dependency/policy pass / sealed snapshot | immutable snapshot |
| S07 | selected mission | Zeus selector | WOP resolution | Zeus | S06 + deterministic tie-break / selection receipt | immutable receipt |
| S08 | qualified immutable WOP | WOP publisher + qualifier | admission | WOP publisher; qualifier owns binding | S02,S03,S07 / one applicable package | immutable package |
| S09 | typed admitted dispatch candidate | admission owners; Zeus composes | EWI | each admission owner | S04,S08 + all receipts / candidate digest | immutable receipts |
| S10 | terminal EWI result | Zeus EWI | reservation only when ALLOW | Zeus EWI | S02,S03,S09 current / ALLOW,DENY,or STOP receipt | immutable receipt |
| S11 | fenced running attempt | Zeus | observation, pause, evidence | Zeus | S10=ALLOW + reservation / terminal attempt result | durable attempt ledger |
| S12 | durable observation or protected pause | EENS / decision owner; Zeus enforces | evidence or resumed operation | EENS for events; decision owner for decision | S11 / event persisted or decision applied | append-only events/checkpoint |
| S13 | sealed, bound evidence | originator + evidence sealer | qualification | evidence store/sealer | S11/S12 / integrity-valid manifest | append-only immutable evidence |
| S14 | independent qualification result | independent qualifier | completion/acceptance or correction | qualifier | S13 + independence / attributable disposition | immutable result |
| S15 | calculated completion | Zeus | acceptance | Zeus | S14 applicable + criteria / completion record | durable record |
| S16 | acceptance or rejection | acceptance decision owner | reconciliation/closeout | decision owner | S15 + exact qualified subject / sealed receipt | immutable receipt |
| S17 | reconciled owner/projection facts | each source owner; EOS only for authorized projection | closeout | each fact's owner | terminal result + exact sync scope / reconciliation result | owner records/checkpoints |
| S18 | interrupted attempt | Zeus | recovery | Zeus | interruption detected / old fence retained | durable interruption record |
| S19 | recovery-validated attempt | Zeus recovery coordinator | safe re-entry to S11 | Zeus; source owners retain facts | S18 + owner reconstruction / new fence + safe checkpoint | durable receipt |
| S20 | corrective disposition | EMP/Governance/WOP owners | successor subject | relevant owner | failed qualification / no-work or successor lineage | immutable disposition |
| S21 | representative lifecycle qualified | independent qualifier | OA-30 | qualifier | S22 + scenario evidence / end-to-end report | immutable evidence |
| S22 | mission closed | Zeus; EMP projection owner | representative qualification | Zeus for attempt; EMP for outcome projection | S16,S17 / resources safe and record retained | terminal ledger/records |
| S23 | OA execution candidate | OA-30 evaluator | separately authorized interface only | roadmap qualification owner | S21 + OA-01..29 evidence / candidate manifest | immutable candidate |

## 4. Lifecycle Transition Matrix

Where a source contains a comma-separated tuple, it is one conjunctive source
vector: every listed state is required. It is not a choice among predecessor
paths.

| From → To | Trigger | Responsible subsystem | Preconditions | Output/evidence |
|---|---|---|---|---|
| S00,S01→S02 | issue and resolve authority | Governance / resolver | exact decision, lineage | Authority Record, effectiveness receipt |
| S01,S02,S03→S04 | reconstruct context | source owners / resolver | integrity-valid repository | observation, source manifest, REAC |
| S02→S03 | derive contract | EMP | one effective authority | contract digest, reproduction proof |
| S03,S04→S05 | stage inventory | EMP | owner facts and policy | stable mission records |
| S05→S06 | classify and seal | EMP | dependencies and eligibility pass | snapshot, reason codes |
| S06→S07 | select | Zeus | one frozen eligible set | selection receipt |
| S02,S03,S07→S08 | resolve WOP | WOP publisher / qualifier | exact tuple | WOP digest, qualification binding |
| S04,S08→S09 | admit | typed admission owners | current compatible inputs | receipt set, candidate digest |
| S02,S03,S09→S10 | terminal initiation | Zeus EWI | all inputs current/unambiguous | ALLOW/DENY/STOP receipt |
| S10→S11 | reserve and dispatch | Zeus | ALLOW and available claims | reservation, fence, start record |
| S11→S12 | event or protected action | EENS / decision owner / Zeus | bound event or pre-effect pause | event/checkpoint or decision receipt |
| S11,S12→S13 | seal evidence | producer / sealer | bound schema and identity | manifest, checksums, seal receipt |
| S13→S14 | qualify | independent qualifier | immutable subject/evidence | criterion matrix, determination |
| S14→S15 | calculate completion | Zeus | applicable result and criteria | completion calculation |
| S15→S16 | accept/reject | acceptance owner | exact qualified result | decision receipt |
| S16→S17 | reconcile | source owners / EOS | exact owner and authorized direction | comparison, checkpoints |
| S17→S22 | close | Zeus / EMP | no unclassified effect | closeout report, release receipt |
| S11→S18→S19→S11 | recover | Zeus | interruption, owner revalidation, safe effect classification | interruption, fence, resume receipt |
| S14→S20 | correct | EMP/Governance/WOP owners | failed criterion and bounded scope | disposition, successor lineage |
| S22→S21→S23 | qualify representative lifecycle | qualifier / OA-30 evaluator | exact closed scenario and cumulative evidence | end-to-end report, candidate manifest |

Every row has a named producer, a fixed source state, declared evidence, and a
single authoritative owner for the fact it creates. A denial, rejection,
blocked recovery, or no-work correction is a terminal disposition for its
subject, not an unmodelled forward transition.

## 5. Lifecycle Dependency Matrix

The OA acceptance dependency is deliberately strict: `OA-01` has no OA-gate
predecessor; each later gate requires the immediately preceding accepted gate.
The additional state prerequisites below prevent a serial receipt chain from
concealing invalid operational inputs.

| Gate(s) | Required gate | Required state(s) | Produced state(s) | Produced artifacts | Enables |
|---|---|---|---|---|---|
| OA-01 | — | S00 | S01 | repository/baseline observation | OA-02 |
| OA-02 | OA-01 | S00,S01 | S02 | Authority Record, effectiveness receipt | OA-03 |
| OA-03 | OA-02 | S02 | S03 | Mission Contract, provenance | OA-04 |
| OA-04 | OA-03 | S01,S02,S03 | S04 | REAC, source manifest | OA-05 |
| OA-05 | OA-04 | S04 | S05 | mission inventory | OA-06 |
| OA-06 | OA-05 | S05 | S06 | eligibility reasons, snapshot | OA-07 |
| OA-07 | OA-06 | S06 | S07 | selection receipt | OA-08 |
| OA-08 | OA-07 | S02,S03,S07 | S08 | WOP, qualification binding | OA-09 |
| OA-09 | OA-08 | S04,S08 | S09 | WOP admission receipt | OA-10 |
| OA-10 | OA-09 | S02,S04,S09 | S09 | authority/context/lease receipt | OA-11 |
| OA-11 | OA-10 | S04,S09 | S09 | agent registration/qualification | OA-12 |
| OA-12 | OA-11 | S09 | S09 | agent-selection receipt | OA-13 |
| OA-13 | OA-12 | S02,S03,S04,S09 | S09 | dispatch-candidate digest | OA-14 |
| OA-14 | OA-13 | S02,S03,S09 | S10 | terminal EWI receipt | OA-15 |
| OA-15 | OA-14 | S10=ALLOW | S11 | reservation, fence, assignment | OA-16 |
| OA-16 | OA-15 | S11 | S11,S12 | durable start, EENS event | OA-17 |
| OA-17 | OA-16 | S11 | S12 | events, checkpoints | OA-18 |
| OA-18 | OA-17 | S11,S12 | S12 | protected-action decision/enforcement | OA-19 |
| OA-19 | OA-18 | S11,S12 | S13 | evidence artifacts | OA-20 |
| OA-20 | OA-19 | S13 | S13 | bound evidence manifest | OA-21 |
| OA-21 | OA-20 | S13 | S14 | qualification result | OA-22 |
| OA-22 | OA-21 | S14 | S20 or successor S02 | correction disposition/lineage | OA-23 |
| OA-23 | OA-22 | S11 or S18 | S18 | pause/checkpoint/fence evidence | OA-24 |
| OA-24 | OA-23 | S18 | S19 then S11 or terminal | recovery receipt | OA-25 |
| OA-25 | OA-24 | S16 or terminal attempt facts | S17 | reconciliation matrix/EOS result | OA-26 |
| OA-26 | OA-25 | S13,S14 | S15 | completion calculation | OA-27 |
| OA-27 | OA-26 | S15 | S16 | acceptance/rejection receipt | OA-28 |
| OA-28 | OA-27 | S16,S17 | S22 | closeout report/outcome projection | OA-29 |
| OA-29 | OA-28 | S22 | S21 | representative-lifecycle evidence | OA-30 |
| OA-30 | OA-29 | S21 | S23 | OA execution candidate manifest | separately authorized interface |

## 6. Cycle Analysis

| Inspection | Result | Demonstration |
|---|---|---|
| Direct gate cycles | none | 30 nodes, edges only `OA-n → OA-(n+1)`; no self-edge |
| Indirect gate cycles | none | a monotonically increasing gate number is a topological ordering |
| Hidden lifecycle cycles | none | recovery returns only to S11 with a new fence; correction terminates the old subject and creates a successor identity |
| Ownership cycles | none | producer/consumer handoffs never grant consumers write authority over the producer's fact |
| Admission cycles | none | admission consumes S04/S08 and produces S09; EWI consumes but does not produce admission receipts |
| Authority cycles | none | Governance originates S02; Mission Contract, WOP, receipts, evidence, and projections only consume it |
| Publication cycles | none | S23 is consumed only by a separately authorized interface and cannot publish/activate OA |
| Synchronization cycles | none | EOS is directional from source owner to projection and cannot feed a source fact back into admission |

The apparent recovery loop is not a dependency cycle: it is an execution-state
transition guarded by a fresh fence, source reconstruction, and a proven-safe
checkpoint. The corrective route is likewise not a cycle because the failed
subject cannot re-enter; only a separately identified successor can begin.

## 7. Reachability and Dead-End Report

All states S01–S23 are reachable from S00 under their documented predicates.
Each OA gate is reachable in the topological order in §5. OA-30 is the only
roadmap terminal; S22 is the mission terminal. Exactly one starting condition
exists: S00. A repository observation is not an alternate start because OA-02
still requires S00.

Normal terminal states are S22 (closed), S23 (candidate), EWI `DENY/STOP`,
acceptance rejection, blocked recovery, and no-work corrective disposition.
The latter four are explicit safe terminal dispositions, not dead ends: their
owner, evidence, and re-entry route (new inputs or successor subject) are
defined. No produced state lacks a consumer: S20 is consumed by successor
planning/authority; S23 by the separately authorized interface; all other
states have a transition in §4. Conditional stoppage is fail-closed and is
therefore intentional rather than an execution dead end.

## 8. Lifecycle Ownership Matrix

| Transition family | Authoritative owner | Producer | Consumer | Qualification owner | Reconciliation owner |
|---|---|---|---|---|---|
| decision/authority | Governance | Governance | EMP, Zeus, WOP | independent qualifier where required | Governance |
| contract/context/planning | EMP for contract/planning; source owners for facts | EMP/source owners | Zeus/admission | qualifier for applicable artifacts | each source owner |
| WOP/admission/agent | WOP publisher and typed admission owners | WOP/admission owners | Zeus EWI | independent WOP/agent qualifier | producing owner |
| initiation/execution | Zeus EWI / Zeus attempt ledger | Zeus and agent | EENS, evidence, qualifier | independent qualifier | Zeus for attempt |
| protected action | applicable operator/Governance owner | decision owner | Zeus enforcer | decision owner under policy | decision owner |
| evidence/qualification | evidence sealer / independent qualifier | originator/sealer | qualifier/acceptance owner | independent qualifier | evidence owner |
| acceptance/closeout | acceptance owner; Zeus for closure; EMP outcome projection | owners named | reconciliation/qualification | independent qualifier | each fact owner; EOS for authorized projection |

No row assigns the same authoritative fact to two owners. Zeus composes and
enforces but cannot issue authority, qualify itself, accept its own result, or
overwrite a source owner. EENS observes; EOS synchronizes; neither decides.

## 9. Deterministic Lifecycle Validation

For one exact subject, the valid progression is S00 → S01 → S02 → S03 → S04
→ S05 → S06 → S07 → S08 → S09 → S10 → S11 → S12 → S13 → S14 → S15 → S16
→ S17 → S22 → S21 → S23. Multi-input transitions name their additional source
states in §4; thus each transition has one valid predecessor *transition*, not
an ambiguous choice of producers. Recovery and correction are explicitly
typed exceptional routes. Consequently, the lifecycle can proceed from
Governance authorization to mission closeout without circular dependencies,
unreachable states, or an implicit transfer of authority.
