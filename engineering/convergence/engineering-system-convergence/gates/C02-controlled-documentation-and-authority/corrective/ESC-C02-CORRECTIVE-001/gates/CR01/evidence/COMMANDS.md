# CR01 Command Record

Corrective: ESC-C02-CORRECTIVE-001
Item: CR01 — Capture Full Starting State
Captured: 2026-08-10T03:57:59Z

## Repository

HEAD=f2e85d857dc73210c428d42ef9530ce9ffc4933b
ORIGIN_MAIN=f2e85d857dc73210c428d42ef9530ce9ffc4933b

## Dependency

CR00=COMPLETE

## Parent state

current_gate=C02
finding=C02-F-027

## Observed commands

scripts/engctl roadmap validate
return_code=1

scripts/engctl roadmap evaluate
return_code=1

scripts/engctl roadmap status
return_code=1

scripts/engctl resume
return_code=1

## Required defect reproduction

C02_F027_REPRODUCED=YES

## Mutation policy

CONTROLLER_MODIFIED=NO
PARENT_C02_MODIFIED=NO
C03_EXECUTED=NO
EOS_SYNCHRONIZED=NO
EOS_REFRESHED=NO
