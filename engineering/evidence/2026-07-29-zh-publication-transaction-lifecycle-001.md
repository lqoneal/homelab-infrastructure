# ZH Publication Transaction Lifecycle 001

Date: 2026-07-29
Handoff: `ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001`
Disposition: `TRANSACTION LIFECYCLE DESIGNED — PUBLICATION REMAINS PAUSED`

## 1. Engineering Work Initiation

| Check | Result |
| --- | --- |
| Repository identity and root | `/data/engineering/repositories/homelab` |
| Repository authority | Repository content remains authoritative; EOS is derived |
| Branch / HEAD | `main`; `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Repository health | PASS: discovery, integrity, and active branch |
| Registry validity | PASS: 85 objects and authority boundary |
| Publication status | Paused after PU-01A |
| Publication framework baseline | PROC-0005 1.6 candidate baseline; SPEC-0001 1.6 representation baseline |
| Qualification baseline | PROC-0006 1.4 candidate |
| Execution baseline | PROC-0001 1.18 candidate |
| Inventory baseline | Publication Plan 002 and its 128-path manifest |
| Publication dependencies | PU-01 and PU-01A complete; PU-01B proposed before PU-02; synchronization after PU-08 |
| Index | Empty |

No publication execution, staging, commit, synchronization, push, plan
execution, history rewrite, or Operational Alpha declaration occurred.

## 2. Publication Transaction Model

The repository already defines publication as a bounded authorized transaction.
It uses commits as immutable locators and publication units as ordered atomic
persistence boundaries. Neither representation accounts for the full
initiation-through-close lifecycle.

The single governing model is therefore:

**a transaction-oriented, lifecycle-aware publication model.**

The transaction owns one immutable input manifest, one append-only output
ledger, explicit exclusions, ordered persistence results, and one final
transaction manifest. Publication units remain atomic boundaries inside the
transaction. Commits remain immutable results of those boundaries.

This model preserves exact staging and digest controls while distinguishing
facts knowable before execution from evidence that can exist only after
execution.

## 3. Artifact Classification

Every artifact receives exactly one class:

| Class | Classification test |
| --- | --- |
| Publication content | The artifact is subject, implementation, document, evidence, or state intentionally persisted for its engineering meaning |
| Execution evidence | It records execution activity or outcome |
| Recovery evidence | It records a failure, stop, incident, or recovery decision |
| Qualification evidence | It records qualification criteria, findings, or disposition |
| Reconciliation evidence | It reconciles inventories, dependencies, conflicts, or authoritative representations |
| Transaction metadata | It represents ledger, boundary, locator, manifest, or completion state |
| Planning artifact | It defines intended units, order, dependencies, or execution strategy |
| Generated artifact | It is a deterministic derivative whose publication is controlled by the initiating contract |
| Operational state | It is owned repository or runtime state changed only through its operational authority |
| Non-publication artifact | It is temporary, local, diagnostic, secret-bearing, cached, or explicitly excluded |

Classification follows purpose, not extension or filename. A report cannot be
both recovery and reconciliation evidence; its primary governed decision
selects one. Transaction role—input, output, or exclusion—is recorded
separately and is not a second lifecycle class.

The current artifact population is completely classified in the companion
change matrix, including the execution, qualification, recovery, inventory,
plan, manifest, generated, state, and non-publication categories.

## 4. Intrinsic Transaction Outputs

The following are intrinsic outputs when produced before immutable
finalization:

- execution and completion reports;
- recovery and incident reports;
- qualification reports and finding/change matrices;
- reconciliation reports and inventory/dependency matrices;
- output-ledger and boundary records;
- replacement manifests and final transaction manifests;
- replacement plans generated during authorized correction; and
- explicitly authorized corrective controlled-document revisions.

They automatically belong to the active transaction output ledger. Automatic
belonging means deterministic ownership and routing, not automatic approval,
staging, lifecycle transition, or persistence.

Generated artifacts belong only when the initiating output schema declares
them required. Operational state remains governed by its assigned publication
unit or separate synchronization authority. Temporary and secret-bearing
artifacts remain permanently excluded.

An intrinsic output produced after immutable finalization belongs to a linked
corrective successor transaction. It can never reopen a completed commit or
manifest.

## 5. Publication Inventory Model

A publication inventory represents complete transaction state:

```text
immutable input manifest
  + append-only governed output ledger
  + explicit exclusions
  + ordered persistence locators
  = final transaction manifest
```

The input manifest represents planned publication content and stays immutable.
The output ledger represents artifacts that execution necessarily creates but
could not fingerprint at initiation. The final manifest represents the whole
transaction after output freeze.

Regenerating the input plan after every corrective action is not desirable. It
conflates inputs with outputs, invalidates otherwise sound freezes, and creates
the recursive planning chain observed in this recovery. The corrected model
appends outputs, freezes exact ledger intervals at declared output boundaries,
and produces one final transaction manifest.

## 6. Dependency Architecture

Dependencies are separated by role:

| Dependency | Meaning |
| --- | --- |
| Execution dependency | An input unit requires an earlier persisted unit |
| Evidence dependency | An output records or validates an earlier event |
| Reconciliation dependency | An output resolves a conflict among transaction records |
| Recovery dependency | Resumption requires preserved failure and recovery evidence |
| Finalization dependency | Completion requires all input, output, exclusion, locator, and validation obligations |

The recursive chain is removed:

```text
Input Plan -> Execution
                |
                v
         append-only Output Ledger
          / execution evidence
         /  recovery evidence
        /   qualification evidence
       /    reconciliation evidence
      v
Output Freeze -> Output Persistence -> Final Manifest -> Completion
```

A correction may append another output or supersede not-yet-persisted seed
bytes at the same output boundary. It does not create a new input plan.
Post-finalization correction creates a successor transaction, not a recursive
extension.

## 7. Lifecycle Integration

| Phase | Authoritative state and permitted transition |
| --- | --- |
| Transaction initiation | Authority, identity, roles, output schema, boundaries, and successor route become the governing transaction contract |
| Input freeze | Exact approved publication inputs and exclusions become immutable |
| Execution | Units persist in dependency order; generated controls append to the output ledger |
| Correction | Authorized corrections append outputs or successor bytes without changing completed units |
| Reconciliation | Classification and dependency conflicts resolve in the ledger, not by regenerating input |
| Output collection | Every intrinsic output and exclusion is accounted for |
| Output freeze | Exact paths, bytes, digests, owners, dependencies, and destination boundary become immutable |
| Output persistence | Frozen output interval obtains an immutable repository locator |
| Inventory finalization | One complete manifest binds inputs, outputs, exclusions, and locators |
| Publication completion | Final validation, synchronization disposition, push, and remote verification close the transaction when authorized |

Publication content becomes authoritative according to its approved lifecycle
and persistence boundary. Evidence becomes authoritative for observed facts
when attributable, finalized, and persisted. The open ledger is authoritative
for responsibility and routing but does not claim persistence. Operational
state becomes authoritative only through its existing owner.

## 8. Current-Transaction Adoption

Publication Plan 002 and its manifest remain the legacy input and provenance
baseline. They are not regenerated.

PU-01B is the first eligible transaction output boundary. Its existing 11
paths are seed outputs. This handoff appends six ledger entries:

- SPEC-0001 Version 1.7 candidate;
- PROC-0001 Version 1.19 candidate;
- PROC-0005 Version 1.7 candidate;
- PROC-0006 Version 1.5 candidate;
- this lifecycle report; and
- its change matrix.

The later procedure bytes supersede only the unpersisted PU-01B seed bytes for
the same paths. A future execution handoff must explicitly adopt the migration,
freeze the exact combined PU-01B ledger interval, validate its paths and
digests, and declare a final transaction-output/finalization boundary after the
last planned input unit. This is output-ledger finalization, not Publication
Plan 003 regeneration.

## 9. Backward Compatibility

| Baseline | Impact |
| --- | --- |
| PU-01 | Valid and immutable |
| PU-01A | Valid and immutable |
| PU-01B | Remains the proposed first recovery/output boundary; its final exact set is frozen from the adopted ledger before execution |
| Publication Plan 002 | Preserved as input/provenance baseline; no rewrite or regeneration |
| PROC-0001 | Version 1.19 adds output routing without invalidating prior execution evidence |
| PROC-0005 | Version 1.7 adds lifecycle structure while preserving exact-boundary, authority, validation, incident, and successor controls |
| PROC-0006 | Version 1.5 routes qualification outputs without changing qualification ownership |
| SPEC-0001 | Version 1.7 represents transaction records without changing controlled-document authority |
| Synchronization procedure | Unchanged; synchronization remains separate and occurs only at its declared boundary |

Existing repository history remains valid under the procedures in effect when
each commit was created. No historical record needs amendment, reinterpretive
metadata, or fabricated output ledger.

## 10. Validation

Validation covers:

- all ten lifecycle classifications and their exclusivity;
- all transaction phases from initiation through completion;
- exact input immutability and output-freeze rules;
- complete evidence, reconciliation, recovery, and finalization dependencies;
- non-recursive planning behavior;
- repository and EOS authority separation;
- pre- and post-finalization correction routing;
- current-transaction migration;
- immutable-history preservation; and
- controlled-document and cross-reference integrity.

## 11. Risks

- Automatic output belonging could be mistaken for publication authority; the
  model expressly withholds approval, staging, and lifecycle authority.
- An unbounded output schema could become implicit glob authorization; exact
  paths and digests remain mandatory at every output freeze.
- Same-path corrective bytes could obscure provenance; the ledger must retain
  the seed digest, successor event, and final frozen digest.
- Finalization performed too early would strand later evidence; required
  completion and successor-routing checks precede the one-way close.
- Legacy adoption without an explicit migration record would be ambiguous and
  remains prohibited.

## 12. Final Recommendation

Adopt the transaction-oriented lifecycle defined by SPEC-0001 Version 1.7 and
PROC-0005 Version 1.7, with PROC-0001 Version 1.19 and PROC-0006 Version 1.5 as
the execution and qualification integrations.

Keep publication paused after PU-01A. A future execution handoff should adopt
the current output ledger, freeze PU-01B at its output boundary, preserve Plan
002 as the input/provenance baseline, and finish through a declared transaction
finalization boundary without recursively regenerating the publication plan.
