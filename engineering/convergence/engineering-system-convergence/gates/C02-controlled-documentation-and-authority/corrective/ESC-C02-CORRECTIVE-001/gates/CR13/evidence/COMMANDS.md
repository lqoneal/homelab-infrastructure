# CR13 Command Record

Corrective: ESC-C02-CORRECTIVE-001
Item: CR13 — Define CLI Contract
Captured: 2026-08-10T09:00:44Z

## Starting state

CR00-CR12 = COMPLETE
CR12M1 = COMPLETE
current_item = CR13
corrective roadmap version = 1.0.4

## Historical reconciliation

C02-F-028 was resolved by CR12M1.

CR13 consumed:

- historical semantic source:
  gates/CR12/INTERRUPTION-REPLAY-SPEC.yaml

- canonical reconciliation:
  gates/CR12M1/REPLAY-RECOVERY-RECONCILIATION.yaml

CR13 did not claim that historical CR12 produced
REPLAY-RECOVERY-SPEC.yaml.

## Zeus

ZO-001 remains CR13 scope.

ZO-002 through ZO-004 remain assigned to CR14.

Zeus-first pre-create verification was attempted.

Zeus repository projection remains unavailable under ZO-001.

Repository fallback was explicit.

## Work

Defined read-only and mutating CLI surfaces for lifecycle inspection,
operator review, advancement, replay inspection, repository projection,
and pre-create verification.

No implementation changed.

CR14 was not executed.
