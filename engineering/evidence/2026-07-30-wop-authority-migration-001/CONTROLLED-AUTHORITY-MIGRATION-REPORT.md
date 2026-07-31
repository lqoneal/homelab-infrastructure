# Controlled Authority Migration Report

## Scope

WOP-AUTHORITY-MIGRATION-001 migrated the HF-005–HF-012 convergence baseline
into the controlled Operational Alpha authority boundary. It made no software,
deployment, runtime, gate-order, mission-semantic, or operational execution
change.

## Authority resolution migration

The effective Operational Alpha chain is now:

```text
Governance Decision → Authority Record → EMM → Implementation WOP
→ resolution receipt → qualified capability → action
```

`SPEC-0014@1.0` is the controlled owner of that chain. `STD-0003@2.0`,
`PROC-0001@2.0`, and `SPEC-0005@2.0` consume it. A legacy Work Registry or
Active Engineering Work Order can be retained as historical traceability but
cannot resolve a new Operational Alpha action. `READY` remains explicitly
non-executing.

## Controlled-document revisions

| Controlled record | Revision | Migration effect |
| --- | --- | --- |
| SPEC-0014 | 1.0 Active | New controlled authority, resolver, lifecycle, interfaces, synchronization, generation, qualification, and completion binding |
| STD-0003 | 2.0 Active | Replaces Operational Alpha EWO-only authority with Authority Record plus active WOP resolution |
| PROC-0001 | 2.0 Active | Replaces initiation and lifecycle resolver input; preserves historical path only as provenance |
| SPEC-0005 | 2.0 Active | Requires Zeus/engctl to consume the canonical resolution receipt |
| PROC-0006 | existing Active | Adds the convergence invocation condition for Operational Alpha qualification |
| TPL-0001 | 2.0 Active | Adds baseline, Authority Record, and EMM receipt fields for implementation WOPs |
| TPL-0002 | 2.0 Active | Adds baseline, Authority Record, and resolution-receipt completion binding |
| DOC-0001 | 2.76 Active | Registers the revised controlled authority set |

## Migration outcomes

* The single authority owner for a requested Operational Alpha action is the
  resolved Authority Record, not a command, runtime view, generated artifact,
  WOP state alone, or historical record.
* Resolver behavior is exact-version first, unique-compatible revision second,
  otherwise fail-closed. It emits a durable, derived receipt.
* Synchronization is source-to-derived-consumer only, topologically ordered,
  idempotent, receipt-verified, and recoverable without derived state writing
  back to source metadata.
* Qualification is an executable, sealed assessment of exact manifests and
  criteria. It may block publication or execution but cannot create approval.
* Completion reporting is bound to the same baseline, authority, receipt,
  qualification, synchronization, and evidence chain.

## Controlled-document revision matrix

| Affected document | Why affected | Reconciled outcome |
| --- | --- | --- |
| STD-0001 / STD-0002 | lifecycle and persistence cross-cutting rules | No semantic duplication; SPEC-0014 supplies Operational Alpha runtime precedence |
| STD-0004 | freshness gate | Continues as evidence/freshness support; it cannot substitute for resolver authority |
| PROC-0005 | controlled publication | Continues to govern publication transaction mechanics; publication remains a separate Authority Record action |
| PROC-0006 | qualification | Updated invocation constraint |
| PROC-0007 | stabilization | No direct authority ownership; consumes receipts when stabilization is requested |
| SPEC-0006 | legacy registry | Historical traceability input only for Operational Alpha authority resolution |
| SPEC-0010 | knowledge repository | Retention and archival consumer; no duplicate EMM authority |
| SPEC-0013 | assurance language | Requirement evaluation consumer; cannot create lifecycle or authority facts |

## Baseline-to-controlled traceability

| Baseline architecture | Controlled representation |
| --- | --- |
| HF-005 lifecycle dependency / verification | SPEC-0014 lifecycle, transition receipt, and verification rules |
| HF-006 automatic synchronization / generated artifacts | SPEC-0014 synchronization and projection rules |
| HF-007 EMM / entity / relationship / generator | SPEC-0014 EMM resolution, ownership, and generator contracts |
| HF-008 metadata lifecycle / compatibility / capabilities | SPEC-0014 WOP lifecycle, version resolution, qualification contracts |
| HF-009 integration | SPEC-0014 runtime interfaces and owners |
| HF-010 findings | HF-011 remediation incorporated as resolver, owner, execution, synchronization, and qualification requirements |
| HF-011 remediation | SPEC-0014 sections on resolver, runtime contracts, synchronization, and qualification |
| HF-012 approval / HF-013A baseline record | exact baseline binding in SPEC-0014 and WOP template |

## Boundary confirmation

No Operational Alpha WOP was activated. No capability was executed. No runtime
state was deployed or synchronized. The existing OA-01 WOP remains a separate,
non-executing planning record until an Authority Record resolves for its exact
activation action.
