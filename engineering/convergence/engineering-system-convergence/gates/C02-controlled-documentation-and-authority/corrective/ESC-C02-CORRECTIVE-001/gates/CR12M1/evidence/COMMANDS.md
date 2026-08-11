# CR12M1 Command Record

Corrective: ESC-C02-CORRECTIVE-001
Maturity gate: CR12M1
Finding: C02-F-028
Captured: 2026-08-10T08:57:38Z

## Historical defect

CR12 frozen contract required:

REPLAY-RECOVERY-SPEC.yaml

CR12 historical execution actually created:

INTERRUPTION-REPLAY-SPEC.yaml

CR12 RESULT.yaml binds the historical actual artifact.

## Evaluation

The historical CR12 artifact was evaluated against each frozen CR12 acceptance
criterion.

Semantic result: PASS

Filename conformance: FAIL historically, preserved as historical fact.

## Disposition

CR12 was not modified.

CR13 was not modified.

A maturity-owned canonical reconciliation artifact was created:

gates/CR12M1/REPLAY-RECOVERY-RECONCILIATION.yaml

CR13 consumers must use that reconciliation locator and must not falsely claim
that CR12 produced the originally required filename.
