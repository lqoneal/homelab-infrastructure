# CR09 — Define Operator Authority

## Result

**COMPLETE**

## Objective and Outcome

CR09 defined the explicit authority required to accept or reject a reviewable
roadmap-gate result.

## What Was Completed

Two operator decisions are authorized:

- ACCEPT
- REJECT

Neither decision can be inferred from result existence, result validity,
result finality, CLI execution, resume state, or process identity.

Every operator decision must bind to the exact roadmap, roadmap version, gate,
frozen gate definition digest, result path, result digest, operator identity,
decision timestamp, and transaction identity.

## Key Decisions and Findings

- ACCEPTED and REJECTED require explicit operator action.
- Only VALID_FINAL results may be decided.
- Decisions against stale or mismatched results fail closed.
- Read-only validate/evaluate/status/resume interfaces cannot create operator
  decisions.
- Exact replay may be idempotent.
- Conflicting replay fails closed.
- Historical operator decisions are append-only.
- Incorrect historical decisions are corrected through new explicit
  transactions, not silent rewrite.
- Acceptance does not itself complete the gate or activate the successor.

## Zeus Development

ZO-001 remains queued to CR13.

Future Zeus/EMP authority infrastructure may strengthen operator identity
resolution, but it must preserve the explicit authority and digest-binding
semantics established here.

## Implementation

Controller modified: NO

engctl modified: NO

Implementation authorized by CR09: NO

## Validation

Explicit ACCEPT authority: PASS

Explicit REJECT authority: PASS

Result digest binding: PASS

Frozen gate digest binding: PASS

Read-only decision boundary: PASS

Replay conflict semantics: PASS

Append-only history: PASS

## Authoritative Artifacts

- `GATE.yaml`
- `OPERATOR-AUTHORITY.yaml`
- `RESULT.yaml`
- `evidence/COMMANDS.md`
- `evidence/VALIDATION.yaml`

## Mutation Boundary

CR00-CR09 gate definitions remained unchanged.

No controller or CLI implementation changed.

CR10 was not executed.

## Next Authorized Item

**CR10**
