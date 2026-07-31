# Operational Alpha Gate Catalog

Proposal: `OA-ROADMAP-HF-005`
Status: `PROPOSED — NON-AUTHORITATIVE`

This catalog supplements, rather than changes, the controlled gate packages in
`engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/`. “Consumed” means
read/validated; it never transfers ownership. Verification dependencies are
the gate package's objective, implementation, evidence template, and
verification guide, plus the predecessor receipt.

## Documentation Architecture

This is a transitional mixed document under the HF-006 generated-document
architecture. The following separation prevents a manually maintained view
from becoming a second source of truth.

| Content | Classification | Source / maintenance rule |
|---|---|---|
| gate purpose, objective, rationale, and lifecycle responsibilities | Authored | controlled gate package and declared documentation owner |
| operator guidance | Authored | controlled verification guidance |
| lifecycle positions, state/transition/dependency matrices, ownership, reachability, cycles, cross-references, command index, and qualification status | Generated-designated | regenerate from authoritative metadata, receipts, and contracts when the qualified generator exists; current manual content is transitional |

Generated-designated sections must eventually carry source-manifest and output
digests. Until then, changes belong in their declared source material and are
reviewed as manual transitional synchronization, not independent authority.

## Gate-Level Lifecycle Position

| Gate | Required predecessor state(s) | Produced state(s) | Consumed artifacts | Produced artifacts | Enabled successor | Lifecycle responsibilities |
|---|---|---|---|---|---|---|
| OA-01 | S00 | S01 | decision scope, repository identity | baseline observation | OA-02 | identify the execution boundary |
| OA-02 | S00,S01 | S02 | decision, lineage, repository observation | Authority Record/effectiveness receipt | OA-03 | establish authority only |
| OA-03 | S02 | S03 | Authority Record, derivation policy | Mission Contract/provenance | OA-04 | derive non-authoritative contract |
| OA-04 | S01,S02,S03 | S04 | owner facts, contract, repository | REAC/source manifest | OA-05 | compose context without changing owners |
| OA-05 | S04 | S05 | planning facts/policy | mission inventory | OA-06 | stage stable mission identities |
| OA-06 | S05 | S06 | inventory, dependency graph | eligibility snapshot | OA-07 | classify without selecting |
| OA-07 | S06 | S07 | frozen snapshot/policy | selection receipt | OA-08 | select one mission deterministically |
| OA-08 | S02,S03,S07 | S08 | selection, authority, contract | WOP/qualification binding | OA-09 | resolve one immutable package |
| OA-09 | S04,S08 | S09 | WOP, REAC, schema policy | WOP admission receipt | OA-10 | prove package admission |
| OA-10 | S02,S04,S09 | S09 | authority, context, lease facts | authority/context receipt | OA-11 | bound validity and revocation |
| OA-11 | S04,S09 | S09 | agent profile/repository | agent qualification | OA-12 | register qualified agents only |
| OA-12 | S09 | S09 | qualified agents, claims | agent-selection receipt | OA-13 | choose compatible agent |
| OA-13 | S02,S03,S04,S09 | S09 | receipts, claims, selection | candidate digest | OA-14 | compose without dispatch |
| OA-14 | S02,S03,S09 | S10 | candidate and current predicates | EWI receipt | OA-15 | sole terminal initiation decision |
| OA-15 | S10=ALLOW | S11 | EWI receipt/claims | reservation, fence, assignment | OA-16 | prevent duplicate effects |
| OA-16 | S11 | S11,S12 | attempt/reservation | start record/EENS event | OA-17 | persist start before observation |
| OA-17 | S11 | S12 | typed events/checkpoints | event stream/delivery receipt | OA-18 | observe without deciding |
| OA-18 | S11,S12 | S12 | protected-action request | decision/enforcement evidence | OA-19 | pause before protected effect |
| OA-19 | S11,S12 | S13 | execution facts/events | sealed evidence artifacts | OA-20 | capture append-only proof |
| OA-20 | S13 | S13 | evidence, subject identities | bound evidence manifest | OA-21 | bind proof to exact subject |
| OA-21 | S13 | S14 | frozen evidence/contract | qualification result | OA-22 | qualify independently |
| OA-22 | S14 | S20 or successor S02 | finding/scope | correction disposition/lineage | OA-23 | route bounded correction |
| OA-23 | S11 or S18 | S18 | attempt/checkpoint | pause/fence evidence | OA-24 | persist safe interruption |
| OA-24 | S18 | S19 then S11/terminal | owner facts/effect status | recovery receipt | OA-25 | resume only proven-safe work |
| OA-25 | terminal attempt facts | S17 | owner records/projections | reconciliation result | OA-26 | reconcile at source owners |
| OA-26 | S13,S14 | S15 | criteria/evidence/qualification | completion calculation | OA-27 | calculate, do not accept |
| OA-27 | S15 | S16 | qualified result | acceptance/rejection receipt | OA-28 | explicit decision only |
| OA-28 | S16,S17 | S22 | terminal records | closeout/outcome projection | OA-29 | close safely and retain |
| OA-29 | S22 | S21 | representative mission evidence | end-to-end report | OA-30 | qualify full lifecycle |
| OA-30 | S21 | S23 | OA-01..29 evidence | candidate manifest | separate interface | prepare no-authority candidate |

The predecessor gate for OA-01 is none; for OA-02 through OA-30 it is the
numerically previous gate. The state prerequisites in the table are in
addition to that acceptance dependency and are authoritative for lifecycle
position. The detailed cycle, reachability, ownership, and verification
dependencies are in the companion analysis and guide.

## Per-Gate Lifecycle Position

Each section below is the independently reviewable lifecycle position for its
gate. “Verification” means the predecessor receipt plus that gate's controlled
objective, implementation, evidence template, and verification guide.

### OA-01 — Lifecycle Position

Predecessor: `S00`; produces: `S01`; consumes: decision scope/repository identity; produces artifact: baseline observation; enables: `OA-02`; responsibility: identify the integrity-valid execution boundary; verification: S01 observation and no active later gate.

### OA-02 — Lifecycle Position

Predecessors: `S00,S01`; produces: `S02`; consumes: decision, lineage, observation; produces artifact: Authority Record/effectiveness receipt; enables: `OA-03`; responsibility: authority issuance and resolution only; verification: one effective record and OA-01 receipt.

### OA-03 — Lifecycle Position

Predecessor: `S02`; produces: `S03`; consumes: Authority Record and derivation policy; produces artifact: Mission Contract/provenance; enables: `OA-04`; responsibility: deterministic non-authoritative derivation; verification: reproduction proof and OA-02 receipt.

### OA-04 — Lifecycle Position

Predecessors: `S01,S02,S03`; produces: `S04`; consumes: owner facts and contract; produces artifact: REAC/source manifest; enables: `OA-05`; responsibility: compose, never overwrite, owner facts; verification: every input names one owner.

### OA-05 — Lifecycle Position

Predecessor: `S04`; produces: `S05`; consumes: planning facts/policy; produces artifact: mission inventory; enables: `OA-06`; responsibility: stage stable identities; verification: stable inventory and OA-04 receipt.

### OA-06 — Lifecycle Position

Predecessor: `S05`; produces: `S06`; consumes: inventory/dependencies; produces artifact: eligibility snapshot; enables: `OA-07`; responsibility: classify without selecting; verification: explicit reason code and OA-05 receipt.

### OA-07 — Lifecycle Position

Predecessor: `S06`; produces: `S07`; consumes: frozen snapshot/policy; produces artifact: selection receipt; enables: `OA-08`; responsibility: deterministic selection; verification: tie-break binding and OA-06 receipt.

### OA-08 — Lifecycle Position

Predecessors: `S02,S03,S07`; produces: `S08`; consumes: selection, authority, contract; produces artifact: immutable qualified WOP; enables: `OA-09`; responsibility: package resolution; verification: one WOP/qualification binding.

### OA-09 — Lifecycle Position

Predecessors: `S04,S08`; produces: `S09`; consumes: WOP, REAC, schema policy; produces artifact: WOP-admission receipt; enables: `OA-10`; responsibility: package admission; verification: typed current receipt.

### OA-10 — Lifecycle Position

Predecessors: `S02,S04,S09`; produces: `S09`; consumes: authority/context/lease facts; produces artifact: validity receipt; enables: `OA-11`; responsibility: bound lease, expiry, and revocation; verification: current predicate without authority substitution.

### OA-11 — Lifecycle Position

Predecessors: `S04,S09`; produces: `S09`; consumes: agent profile/repository; produces artifact: agent qualification; enables: `OA-12`; responsibility: integrity-bound registration; verification: repository/profile binding.

### OA-12 — Lifecycle Position

Predecessor: `S09`; produces: `S09`; consumes: qualified agents/claims; produces artifact: agent-selection receipt; enables: `OA-13`; responsibility: compatibility selection; verification: all constraints match.

### OA-13 — Lifecycle Position

Predecessors: `S02,S03,S04,S09`; produces: `S09`; consumes: receipts, claims, selection; produces artifact: candidate digest; enables: `OA-14`; responsibility: compose non-executing candidate; verification: no attempt exists.

### OA-14 — Lifecycle Position

Predecessors: `S02,S03,S09`; produces: `S10`; consumes: candidate/current predicates; produces artifact: EWI receipt; enables: `OA-15` only for `ALLOW`; responsibility: terminal initiation decision; verification: exact ALLOW/DENY/STOP.

### OA-15 — Lifecycle Position

Predecessor: `S10=ALLOW`; produces: `S11`; consumes: EWI receipt/claims; produces artifact: reservation, fence, assignment; enables: `OA-16`; responsibility: exactly one effect boundary; verification: no duplicate reservation.

### OA-16 — Lifecycle Position

Predecessor: `S11`; produces: `S11,S12`; consumes: attempt/reservation; produces artifact: durable start/EENS event; enables: `OA-17`; responsibility: persist start; verification: start precedes notification.

### OA-17 — Lifecycle Position

Predecessor: `S11`; produces: `S12`; consumes: typed events/checkpoints; produces artifact: event stream/receipt; enables: `OA-18`; responsibility: observation only; verification: EENS has no decision role.

### OA-18 — Lifecycle Position

Predecessors: `S11,S12`; produces: `S12`; consumes: protected-action request; produces artifact: decision/enforcement evidence; enables: `OA-19`; responsibility: pause before effect; verification: decision scope and fence match.

### OA-19 — Lifecycle Position

Predecessors: `S11,S12`; produces: `S13`; consumes: execution facts/events; produces artifact: sealed evidence; enables: `OA-20`; responsibility: append-only capture; verification: seal/checksum integrity.

### OA-20 — Lifecycle Position

Predecessor: `S13`; produces: `S13`; consumes: evidence and subject identities; produces artifact: bound manifest; enables: `OA-21`; responsibility: exact-subject binding; verification: authority/contract/WOP/attempt all bind.

### OA-21 — Lifecycle Position

Predecessor: `S13`; produces: `S14`; consumes: frozen evidence/contract; produces artifact: qualification result; enables: `OA-22`; responsibility: independent qualification; verification: reviewer independence and attributable result.

### OA-22 — Lifecycle Position

Predecessor: `S14`; produces: `S20` or successor `S02`; consumes: finding/scope; produces artifact: correction disposition/lineage; enables: `OA-23`; responsibility: bounded correction routing; verification: old subject cannot re-enter.

### OA-23 — Lifecycle Position

Predecessor: `S11` or `S18`; produces: `S18`; consumes: attempt/checkpoint; produces artifact: pause/fence evidence; enables: `OA-24`; responsibility: durable interruption; verification: no inferred completion.

### OA-24 — Lifecycle Position

Predecessor: `S18`; produces: `S19` then `S11` or terminal; consumes: owner facts/effect status; produces artifact: recovery receipt; enables: `OA-25`; responsibility: safe revalidation; verification: uncertain non-idempotent effect is not repeated.

### OA-25 — Lifecycle Position

Predecessor: terminal attempt facts; produces: `S17`; consumes: owner records/projections; produces artifact: reconciliation result; enables: `OA-26`; responsibility: source-owner reconciliation; verification: EOS is directional only.

### OA-26 — Lifecycle Position

Predecessors: `S13,S14`; produces: `S15`; consumes: criteria/evidence/qualification; produces artifact: completion calculation; enables: `OA-27`; responsibility: calculate completion; verification: no acceptance inference.

### OA-27 — Lifecycle Position

Predecessor: `S15`; produces: `S16`; consumes: qualified result; produces artifact: acceptance/rejection receipt; enables: `OA-28`; responsibility: explicit decision; verification: receipt binds exact subject.

### OA-28 — Lifecycle Position

Predecessors: `S16,S17`; produces: `S22`; consumes: terminal records; produces artifact: closeout/outcome projection; enables: `OA-29`; responsibility: safe closure and retention; verification: resources safe and no residue.

### OA-29 — Lifecycle Position

Predecessor: `S22`; produces: `S21`; consumes: representative mission evidence; produces artifact: end-to-end report; enables: `OA-30`; responsibility: full-lifecycle qualification; verification: negative and recovery paths included.

### OA-30 — Lifecycle Position

Predecessor: `S21`; produces: `S23`; consumes: OA-01 through OA-29 evidence; produces artifact: candidate manifest; enables: separately authorized interface only; responsibility: cumulative qualification; verification: no declaration, publication, synchronization, or activation is claimed.
