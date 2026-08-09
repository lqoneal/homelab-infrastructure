# Zeus Submission Call Path

## Authoritative current paths

```text
zeus submit SOURCE [options]
        |
        v
argparse / resolve_wop_source()
        |
        +-- current implementation condition: a.command == submit AND NOT a.repository
        |       |
        |       +-- adjacent SOURCE.traceability.json exists
        |       |       |
        |       |       v
        |       |   submit_wop_boundary()
        |       |       |
        |       |       +-- verify_artifact()
        |       |       +-- Operation Beta / readiness / WOP / Mission checks
        |       |       +-- repository identity and source/output digest checks
        |       |       +-- deterministic submission receipt
        |       |       +-- one ADMISSION_REQUESTED request projection
        |       |       `-- stop: no Mission Admission or execution
        |       |
        |       `-- no traceability sidecar
        |               |
        |               +-- canonical package/source classification
        |               +-- source validation and package_wop() when needed
        |               +-- initialize runtime after package validation
        |               +-- Stage1Runtime.submit_development()
        |               +-- package validation / repository and baseline checks
        |               +-- deterministic Stage-1 mission instance identity
        |               +-- registration and authority snapshot
        |               +-- receipt-backed admission/authorization projections
        |               `-- Development resume/dispatch boundary as configured
        |
        `-- a.repository is supplied
                |
                v
            skip both branches above
                |
                v
            MissionOrchestrator legacy fallback
                |
                +-- require --baseline
                +-- require --approval
                +-- require --impact
                +-- require --affected-repository
                +-- load wop_package as an accepted admission-record path
                +-- create legacy queue mission
                +-- evaluate required_approvals
                +-- select creates legacy approval request
                `-- approve creates legacy authorization state
```

## Why the observed error occurs

The lifecycle invocation supplied `--repository` and other legacy-shaped
arguments. The `if a.command == "submit" and not a.repository` guard is false,
so the source is never tested for an authored traceability sidecar and never
reaches `submit_wop_boundary`. The fallback checks `a.approval` before it can
parse or validate the WOP, producing:

```text
legacy admission-record submission requires --approval
```

This error identifies the legacy CLI contract, not an approval gate declared
by `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`.

## Component ownership

| Stage | Current implementation | Authoritative fact |
|---|---|---|
| CLI resolution | `scripts/zeus::resolve_wop_source` | Input locator only; no authority invented |
| Phase-1 authoring | `scripts/lib/emp/wop_authoring.py` | Generates Markdown plus immutable traceability sidecar |
| Source validation | `scripts/lib/emp/wop_validation.py` | Development schema and required semantic fields |
| Package construction | `scripts/lib/emp/wop_packaging.py` | Deterministic Stage-1 package; preserves source digest |
| P2 submission | `scripts/lib/emp/submission_boundary.py` | Validates provenance and requests admission exactly once |
| Stage 1 | `scripts/lib/emp/stage1_runtime.py` | Package intake, registration, authority snapshot, receipts, and Development lifecycle |
| Legacy queue | `scripts/lib/emp/orchestration.py` | Admission-record queue, selection, and legacy approval metadata |
| P3 admission | `scripts/lib/emp/mission_admission_boundary.py` | Consumes P2 receipt; provisions admission artifacts; no execution |
| Authority projection | Stage-1 authority snapshot and downstream controllers | `operator-submitted WOP`; approvals only when explicitly declared |

## Target path

The target must classify before option-dependent routing:

```text
resolve source
  -> complete classifier and provenance normalization
  -> current authored/promotable Development source
  -> existing P2 boundary
  -> ADMISSION_REQUESTED
  -> explicit later admission

actual legacy admission record + explicit compatibility selector
  -> legacy adapter
  -> legacy queue semantics, including its own selection controls
```

The two paths must never be selected by the incidental presence of
`--repository`, and a current source must never be made to satisfy a legacy
`required_approvals` field merely to cross P2.
