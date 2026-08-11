# ESC-C02-CORRECTIVE-001 Manual Execution Procedure

## Purpose

This procedure governs manual execution of the C02 lifecycle corrective.

The roadmap is intentionally decomposed into individually executable CR items.
Only one item may execute at a time.

## Mandatory Resume Sequence

Before every CR item:

1. `cd /data/engineering/repositories/homelab`
2. verify branch `main`
3. inspect `git status --short`
4. read this file
5. read `ROADMAP.yaml`
6. read `STATE.yaml`
7. identify `current_item`
8. read that item's `GATE.yaml`
9. verify all dependencies are complete
10. verify all frozen artifacts required by the item
11. execute only that item
12. record evidence
13. validate acceptance criteria
14. create that item's `RESULT.yaml`
15. update `STATE.yaml`
16. stop

Do not execute the next item in the same manual transaction.

## Frozen Inputs

The following are historical/current frozen inputs and may not be rewritten by
this corrective:

- ESC C00 GATE.yaml
- ESC C01 GATE.yaml
- ESC C02 GATE.yaml
- C02 RESULT.yaml
- existing C02 assessment evidence

## Mutation Policy

CR items may modify only the paths explicitly authorized in their own GATE.yaml.

Any unexpected modification is a fail-closed condition.

## Result Rule

Each CR item must produce:

- `RESULT.yaml`
- evidence sufficient to reproduce or validate the item
- updated corrective `STATE.yaml`

A result does not authorize the next item unless the current item's acceptance
criteria pass.

## Failure Rule

On failure:

- do not advance STATE.yaml;
- do not execute later items;
- preserve evidence;
- record the blocker;
- stop.

## Publication Boundary

Only CR43/CR45 and CR53/CR54 may authorize commit/push respectively.

## Final Corrective Condition

The corrective is complete only after CR55 proves from a fresh shell that:

- C00/C01/C02 are complete;
- C03 is current;
- C02 acceptance is durable;
- C02-F-027 is resolved;
- roadmap validation passes;
- `engctl resume` derives C03 read-only.

## Mandatory Human-Readable Gate Record

Every executed CR item MUST create a human-readable `SUMMARY.md` before the
gate may be considered complete.

The summary is a required historical projection of the machine-readable result
and evidence. It MUST contain, at minimum:

1. gate identifier and title;
2. result;
3. objective and outcome;
4. what was completed;
5. material findings and decisions;
6. validation result;
7. authoritative artifacts produced;
8. mutation/non-mutation boundary;
9. blockers or unresolved issues;
10. next authorized item.

The summary MUST NOT introduce authority that is absent from the corresponding
`RESULT.yaml` or evidence. When the human-readable summary and machine-readable
records disagree, the machine-readable records fail closed as the source for
verification and the discrepancy must be corrected before advancement.

After a gate completes, the corrective-level `HISTORY.md` MUST also be appended
with a concise entry identifying the gate, result, principal outcome, and link
to the gate `SUMMARY.md`.

A gate is not eligible for state advancement unless all of the following exist:

- `RESULT.yaml`
- `SUMMARY.md`
- required evidence
- validation PASS
- updated `HISTORY.md`

This rule applies prospectively beginning with CR06. CR00-CR05 summaries were
backfilled from their already-persisted authoritative results and evidence as
part of the recordkeeping-hardening corrective.

## Current-Gate Zeus Capability Opportunity Registration

A gate that is the authoritative current execution item MAY append a Zeus
capability opportunity to the canonical Zeus capability-opportunity register
without a separate roadmap-maintenance transaction when, and only when, the
opportunity is directly derived from a blocker, defect, insufficiency, missing
capability, failed qualification, or recovery requirement encountered while
executing that current gate.

This authority is additive and evidence-bound. Before registration, the current
gate MUST:

1. prove that it remains the authoritative current item;
2. persist durable evidence describing the current-gate condition that produced
   the capability opportunity;
3. prove the opportunity is semantically distinct from existing registered
   opportunities or explicitly deduplicate it to an existing opportunity;
4. assign the opportunity to the earliest semantically appropriate future mutable CR gate, preserving the ZO-* opportunity identifier and classifying its implementation as a secondary CR mission;
5. record that opportunity registration does not itself authorize implementation,
   repair, publication, successor execution, or current-gate completion; and
6. preserve all otherwise applicable mutation and stop boundaries.

Under this rule the current gate MAY mutate only the canonical Zeus
capability-opportunity register and current-gate evidence necessary to record
the opportunity. If the opportunity also requires prospective modification of
the corrective roadmap or an existing future gate contract, that separate
roadmap or future-gate mutation still requires the applicable roadmap-maintenance
authority.


### Zeus Opportunity Execution-Gate Binding

The canonical identifier of a Zeus capability opportunity remains `ZO-*`.
Opportunity identity MUST NOT be replaced by a separate implementation-gate
identifier namespace.

Every QUEUED Zeus capability opportunity MUST be assigned to a specific future
mutable `CR*` gate. The assigned CR gate is the execution location for that
opportunity and MUST execute the opportunity as a secondary CR mission alongside
the gate's primary corrective objective.

Assignment MUST be based on semantic lifecycle fit. A completed or frozen CR gate
MUST NOT be reopened solely to absorb later-discovered Zeus capability work. In
that case the opportunity MUST be assigned to the earliest semantically
appropriate future mutable CR gate.

A generic `DEFERRED`, `FUTURE_DEVELOPMENT`, unnamed future gate, or standalone
`ZG-*` implementation-gate assignment does not satisfy this requirement.

Prospective modification of the assigned future CR gate contract is permitted
only to bind the queued ZO-* opportunity as a secondary mission, define its
bounded implementation/verification obligations, and preserve the primary CR
gate objective and stop boundary.

Recording or assigning a Zeus opportunity does not by itself authorize execution
of that secondary mission before its assigned CR gate becomes current.

An opportunity discovered for general improvement, convenience, optimization,
or future maturity that is not directly derived from a condition affecting the
current gate remains subject to the normal prospective roadmap-maintenance
procedure.

A registered opportunity MUST NOT be treated as repair authority. The current
gate may continue only under independently established authority for the
underlying blocker or corrective mutation.

