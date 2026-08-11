# CR08 — Define Result Semantics

## Result

**COMPLETE**

## Objective and Outcome

CR08 defined result validity and finality independently from operator review,
operator acceptance, gate completion, and successor activation.

## What Was Completed

Result handling now distinguishes:

- no result;
- invalid result;
- nonfinal result;
- stale result;
- conflicting result; and
- valid final result.

Only a VALID_FINAL result is eligible to enter operator review.

A valid or final result does not imply operator acceptance.

A result may be terminal for an execution attempt while the roadmap gate
remains current and awaiting review.

## Key Decisions and Findings

- RESULT existence is only a fact about artifact presence.
- Result finality is only a fact about the execution attempt.
- Operator acceptance is a separate authorized lifecycle decision.
- Gate completion is a separate advancement operation.
- Stale or conflicting results fail closed.
- Review must bind to the exact result identity and digest.
- Execution result values such as PASS or COMPLETE_WITH_FINDINGS remain
  distinct from lifecycle state.
- Historical results may not be silently rewritten.

## Zeus Development

ZO-001 remains queued to CR13.

Zeus-first verification was attempted; repository-native verification remains
the temporary fallback while ZO-001 is unresolved.

## Implementation

Controller modified: NO

engctl modified: NO

Implementation authorized by CR08: NO

## Validation

Result validity classes: PASS

VALID_FINAL review boundary: PASS

Result/acceptance separation: PASS

Stale-result semantics: PASS

Conflict semantics: PASS

## Authoritative Artifacts

- `GATE.yaml`
- `RESULT-SEMANTICS.yaml`
- `RESULT.yaml`
- `evidence/COMMANDS.md`
- `evidence/VALIDATION.yaml`

## Mutation Boundary

CR00-CR08 gate definitions remained unchanged.

No controller or CLI implementation changed.

CR09 was not executed.

## Next Authorized Item

**CR09 — Define Operator Authority**
