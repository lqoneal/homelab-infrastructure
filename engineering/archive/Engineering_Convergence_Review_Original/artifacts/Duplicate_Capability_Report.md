# Duplicate Capability Report

Review ID: `ENGINEERING-CONVERGENCE-REVIEW-001`  
Assessment date: 2026-07-30

## Summary

Most duplication is traceable to successive architecture generations:
foundation EMP/EOS services, pre-Progressive PMCT and gate approval,
Progressive OA, and the newer authority-pipeline convergence work. Historical
implementations were preserved correctly, but several remain callable or
independently editable. The remedy is ownership and routing convergence, not
another adapter layer.

## Duplicate and overlapping capabilities

| Capability | Implementations | Why both exist | Authoritative/canonical direction | Transitional disposition |
|---|---|---|---|---|
| OA gate lifecycle and approval | `progressive_gate.py` and Progressive runtime records; `gate_approval.py`, `gate_decision.py`, `gate_carry_forward.py`, external WOP receipts | Progressive OA superseded the original PMCT/external-WOP lifecycle while preserving historical acceptance | Progressive gate service and canonical package runtime | Remove production routing to legacy service after dependent agent/PMCT behavior consumes Progressive receipts |
| OA-02 lifecycle | `oa02_gate_verification.py` plus Progressive state; `oa02_lifecycle.py` plus external record | Earlier pre-execution OA-02 record model predates canonical Progressive OA | Progressive OA-02 verifier, marker, receipt, and state | Dead code: retire module, import, branches, and legacy-only tests; preserve evidence |
| PMCT execution | Standalone `engineering/tests/.../lib/pmct.py`; current `zeus verify/approve` Progressive path | The standalone PMCT harness established the original capability test before the Progressive package became executable | Progressive gate verification is current acceptance path | Narrow PMCT to reusable observation/regression functions; remove legacy approval projection and reassess installed wrapper |
| Mission Contract storage | `engineering/mission-contracts/contracts/`; `engineering/execution/missions/` | Engineering Execution Interface introduced a separate mission description before canonical store integration | Mission Contract store and schema | Convert execution missions to generated read-only projections or retire after field mapping |
| Authority resolution | `authority/engine.py`; `wop/contract.py` compatibility decision; `authority_resolution.py`; `controlled_mission_authority.py`; `authorization_bundle.py`; PMA reconstruction; EWI composition | Independent missions implemented valid local decisions before end-to-end topology was fixed | ARS produces one resolved execution context; PMA narrows; EWI emits terminal decision | Keep graph/compatibility evaluators offline; migrate callers; remove independent production allow decisions |
| Mission admission | `wop_admission.py`; `mission_admission_runtime.py`; Stage 1 package admission behavior | Different abstraction levels and historical phases | WOP admission owns package acceptance; mission runtime consumes its typed record | Clarify layering; remove duplicate validation only after contract tests prove same semantics |
| Execution lifecycle state | `wop_lifecycle.py`; `mission_execution_runtime.py`; `execution_oversight.py`; `stage1_runtime.py`; Progressive runtime state | Reservation, mission execution, oversight, Stage 1, and gate progression were built separately | Retain separate typed states with a single ownership map; do not collapse distinct concerns | Eliminate duplicated status projection and transition authority, not the distinct records |
| Operator next action/status | `next_action.py` legacy logic; `progressive_lifecycle.py`; `progressive_runtime_support.py`; `scripts/zeus` routing | Legacy operator UX predates current WOP | Progressive lifecycle projection for active package | Remove legacy OA routing once compatibility obligations end |
| Repository/EOS state | PROJ-0001, Work Registry, WOP state, `.zeus` runtime, EOS state, progress document | Each domain needs a view, but state ownership was not always explicit | Repository owners are authoritative; EOS/runtime/status are typed projections | Add owner/projection matrix and validation; never reverse-sync projections |
| Notification | EENS service; shell `notifications/ntfy.sh`; execution sink adapters | Shell notification preceded and complements the service | EENS for durable event/notification lifecycle | Keep shell adapter only as a thin transport client; no independent event store |
| CLI/control surface | `engctl`, `zeus`, EMP management CLI, PMCT wrapper | Different operator domains and historical entry points | `engctl` for engineering control; `zeus` for Zeus operations; internal CLIs as subordinate tools | Remove installed PMCT if no canonical operational caller remains; document command ownership |
| Architecture documentation | controlled `docs/`; `engineering/operations`; `engineering/docs/architecture`; `engineering/architecture`; planning records | Different lifecycle and audiences, plus rapid architecture evolution | Controlled docs own norms; engineering architecture owns implementation contracts; operations owns procedures/status | Mark planning/historical artifacts clearly and reconcile duplicate normative prose at publication |
| Evidence storage | `engineering/evidence/`; WOP-local `EVIDENCE`; WOP runtime evidence; `.zeus/evidence` | Project evidence, package evidence, and runtime evidence have different producers | Retain typed domains, add one catalogue and discovery contract | Do not merge files; remove only duplicate current-state assertions |

## Obsolete and superseded work

### Obsolete code or runtime paths

1. **`scripts/lib/emp/oa02_lifecycle.py`**

   Current `scripts/zeus` selects Progressive routing when the canonical
   runtime state exists. The module is only reachable through disabled legacy
   branches and tests. Its external record schema is incompatible with the
   Progressive OA-02 record. It is dead code, not a migration source.

2. **External Progressive OA WOP executable compatibility tree**

   `/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP` contains a semantically
   different legacy package, stale OA status projections, and historical
   receipts. It is not a mirror of
   `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001`. Preserve hashes and
   historical evidence; retire executable use after consumer removal.

3. **Legacy non-Progressive Zeus branches**

   Status, verify, approval, next-action, and carry-forward branches that
   depend on the external package are superseded for current OA execution.
   Some remain reachable through explicit configuration and therefore must be
   deliberately removed, not merely ignored.

4. **Independent production compatibility allow decisions**

   Authority Graph and WOP compatibility evaluation are useful libraries, but
   allowing them to independently authorize production after ARS integration
   would be obsolete architecture.

### Transitional code

- `scripts/lib/emp/gate_approval.py`
- `scripts/lib/emp/gate_decision.py`
- `scripts/lib/emp/gate_carry_forward.py`
- `scripts/lib/emp/next_action.py` legacy path
- `engineering/tests/zeus-operational-alpha/lib/pmct.py`
- `scripts/lib/work_initiation/authorization_bundle.py` legacy environment inputs
- `engineering/execution/missions/`

These are not all dead today. They must be narrowed or migrated before
retirement.

### Historical and superseded documentation

- Completed EWO records and milestone records are historical evidence, not
  current execution instructions.
- ZEUS-P2-005 blocked commissioning assessment is explicitly superseded by
  ZEUS-P2-014 commissioning.
- P2-038 original self-certified completion is superseded by P2-038-CORRECTIVE.
- Legacy PMCT approval descriptions are superseded for current gate acceptance
  by canonical Progressive receipt semantics.
- The external WOP's OA-02–OA-30 status projections are stale historical
  snapshots.
- Planning documents under
  `ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001` are proposals and must not be
  read as current execution authority.

### Generated and organizational artifacts

`__pycache__` files under source trees are generated artifacts, not canonical
implementation. They should be excluded from future inventories and removed
under a separate hygiene change if tracked or operationally unnecessary.

## Retirement sequence

1. Approve the canonical authority topology and ownership map.
2. Inventory every caller of legacy gate, PMCT, Mission Contract, and
   authorization-bundle paths.
3. Build the canonical ARS resolved-context interface.
4. Migrate PMA and EWI in shadow comparison mode with no second allow path.
5. Convert tests to repository-local temporary fixtures.
6. Remove production callers of the external WOP and verify zero consumers.
7. Freeze/archive the external package without importing stale state.
8. Remove dead OA-02 and legacy routing.
9. Convert or retire execution-mission projections.
10. Preserve historical evidence and compatibility fixtures in explicitly
    non-authoritative namespaces.

## Work that can be eliminated

- A compatibility adapter that emulates the external WOP lifecycle.
- A third authority-resolution data model.
- Reimplementation of admission, dispatch, evidence, qualification,
  reconciliation, or EENS for later OA gates.
- Independent edits to `engineering/execution/missions/`.
- A second gate approval or next-action service.
- Broad repository reorganization before Operational Alpha.

