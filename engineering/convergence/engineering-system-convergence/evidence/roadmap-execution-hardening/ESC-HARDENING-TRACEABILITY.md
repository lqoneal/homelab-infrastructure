# ESC Hardening Traceability

## Roadmap invariants preserved

- Gate order remains C00-C20.
- C00 and C01 retain their historical result meaning.
- C02 remains current, unexecuted, and assessment-only.
- C00/C01 use frozen historical provenance; C02 uses frozen activation-era
  provenance; STD-0006 applicability begins at C03.
- Assessment precedes implementation.
- C17 remains the target-architecture boundary.
- C18 remains the implementation-roadmap boundary.
- C19 remains cold-resume qualification.
- C20 remains bounded implementation entry and is explicitly terminal to this
  roadmap, with continuation governed by C18 and separate first-gate authority.

## Gate contract mapping

Every gate resolves `ESC-CXX` in `execution-playbooks.yaml`. C02-C19 define
gate-specific discovery surfaces, inventory method, safety/prohibition,
coverage, vocabulary, artifact records, cross-checks, completeness, and result
rules. All gates resolve shared review, state-transition, persistence, and
cold-resume contracts. C20 alone sets `next_gate: null`, declares terminal
semantics, and names external continuation authority and action.

The previously thin C05, C07, C09, C12, C15, and C18 evidence contracts now
have gate-specific artifact schemas and objective coverage/completeness tests.

## Queue, history, and maturity controls

- `ESC-ROADMAP-001` is the active temporary canonical engineering queue.
- Zeus staging is not yet the queue authority; transfer requires a separately
  reviewed equivalent staging contract and operator acceptance.
- Only pending prospective contracts may be revised by this hardening work.
- Complete and current contracts remain immutable; historical records are
  append-only and standards are prospective only.
- Gate identity is immutable and distinct from `roadmap_order`; future
  maturity gates can use new identities and unused order values without
  renumbering existing gates.
- Pending dependencies may evolve by identity under a new roadmap revision.
  An active-contract defect is recorded as a finding/corrective input and is
  not repaired by editing the active contract in place.
