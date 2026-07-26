# WOP Submission Admission Control Design

## Boundary

Mission N0 adds a validation-only front door before Engineering Work
Initiation. It does not select, plan, authorize, dispatch, execute, repair, or
reconcile engineering work.

## Authoritative validation basis

The deterministic rules are derived from the active repository records:

- `PROC-0001@1.11`, Engineering Work Order Execution Procedure;
- `TPL-0001@1.7`, Engineering Work Order Template;
- `STD-0000` through `STD-0004`, including the required elements and Active
  lifecycle rule in `STD-0003`.

The machine-readable submission contract requires transaction identity,
approval, execution-package bindings, all transaction sections represented by
TPL-0001, authoritative references, repository identity, and a canonical
content digest. The controller never alters the submitted mapping.

## Decision and record model

Validation produces exactly `ACCEPTED` or `RESUBMISSION_REQUIRED`. Every
failure is sorted by field and reason code. Rejections include exact
corrections, authoritative references, the full required format, and the five
required no-work status statements.

Admission identity is UUIDv5 over canonical decision material excluding the
observation timestamp. The immutable record checksum covers the entire record
except the checksum itself. The ledger uses one create-only JSON file per
Admission ID; an identical replay is idempotent and different bytes at an
existing identity fail closed.

## Platform enforcement

`eos_platform_qualify` calls `eos_wop_admission_require` before legacy
qualification or Zeus authorization. The gate requires a checksum-valid
`ACCEPTED` record bound to the observed repository and, when supplied, the
expected WOP ID. Missing, rejected, corrupt, or mismatched records return 78.

Consequently the admission failure path performs neither repository inventory
nor either authorization evaluation. The admission CLI itself reads only the
submitted document and writes only its admission record.

## Interfaces

```text
scripts/wop-admissionctl admit \
  --submission WOP.yaml \
  --repository /absolute/repository/path \
  --ledger /evidence/admission-ledger

export EOS_WOP_ADMISSION_RECORD=/evidence/admission-ledger/ADMISSION-....json
export EOS_WOP_ADMISSION_WOP_ID=WOP-....
scripts/engctl platform qualify homelab
```

`verify-record` is the narrow downstream interface. It grants admission only;
authorization and execution remain independent and fail closed.
