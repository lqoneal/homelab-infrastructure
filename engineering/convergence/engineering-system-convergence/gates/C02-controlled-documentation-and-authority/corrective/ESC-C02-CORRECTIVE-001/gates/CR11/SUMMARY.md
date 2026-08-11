# CR11 — Define Atomic Advancement

## Result

**COMPLETE**

## Objective and Outcome

CR11 defined the atomic transaction that converts an explicitly accepted gate
into immutable completion and establishes the next authoritative roadmap
position.

## What Was Completed

The advancement transaction now requires an ACCEPTED starting state plus exact
roadmap, gate, frozen-definition, result, receipt, and transaction identities.

A successful transaction establishes completion and either:

- exactly one deterministic successor; or
- explicit terminal roadmap completion.

## Key Decisions

- Only ACCEPTED may become COMPLETED.
- A completed gate cannot remain current.
- Completion and successor-or-terminal selection form one logical transaction.
- Nonterminal advancement requires exactly one eligible successor.
- Terminal advancement never fabricates a successor.
- Partial transactions must be detectable and reconcilable.
- Exact replay is idempotent or already-applied.
- Conflicting replay fails closed.
- Read-only interfaces cannot advance lifecycle state.
- Advancement does not implicitly synchronize EOS, publish, commit, or push.

## Interruption Recovery

The first CR11 execution attempt stopped before CR11 artifacts were created
because a YAML design input was accidentally invoked as Python source.

The resume transaction corrected only that invocation error and completed the
same frozen CR11 contract.

## Implementation

Controller modified: NO

engctl modified: NO

Implementation authorized: NO

## Validation

Atomic advancement design: PASS

Interruption recovery: PASS

Replay semantics: PASS

Terminal semantics: PASS

Read-only boundary: PASS

## Next Authorized Item

**CR12**
