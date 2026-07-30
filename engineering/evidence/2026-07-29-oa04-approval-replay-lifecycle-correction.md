# OA-04 Approval Replay Lifecycle Correction

Date: 2026-07-29  
Handoff: OA-04 Approval Replay Lifecycle Correction  
Disposition: IMPLEMENTED AND FOCUSED VALIDATION PASSED

## 1. Engineering Work Initiation

This is non-EWO corrective engineering work. No Engineering Work Order or ETP
authority is asserted by this report.

| Check | Observed result |
|---|---|
| Repository identity | `homelab-infrastructure` |
| Repository root | `/data/engineering/repositories/homelab` |
| Remote | `origin`, `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch | `main` |
| HEAD | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Upstream | `origin/main`; ahead 2, behind 0 |
| Repository health | PASS; modified working tree reported |
| Registry validation | PASS; 85 objects |
| Index | Empty |
| Project phase | Zeus Operational Alpha |
| Runtime gate | OA-06 |

The working tree was not clean at initiation. It contained an existing,
unstaged corrective candidate spanning the exact implementation, regression
test, and operator documentation paths required by this handoff, together
with unrelated pre-existing work. Repository health nevertheless passed and
the index was empty. The existing candidate was treated as the work-in-
progress baseline: unrelated changes were preserved, no staging or history
operation occurred, and the final report distinguishes the focused validation
from unrelated baseline failures.

## 2. Current Lifecycle Analysis

The Progressive OA runtime state owns the current lifecycle binding:

1. `runtime/state.json` identifies the gate state.
2. An `ACCEPTED` gate contains `acceptance_receipt`, the sole current-receipt
   locator.
3. The located receipt binds package, gate, operator, package manifest,
   VERIFIED marker bytes, marker digest, and verification-evidence digest.
4. Supersedence records identify receipts that remain historical evidence but
   have no current authority.
5. Replay is an observational return of the already-current receipt; it does
   not create a decision or advance a gate.

The defective historical behavior consulted an `accepted.json` pathname as
independent authorization. The corrected path begins with runtime lifecycle
state and never scans a flat historical receipt to establish replay authority.

Lifecycle trace:

```text
runtime gate state
  -> require ACCEPTED
  -> validate active/intervening lifecycle state
  -> resolve runtime acceptance_receipt pointer
  -> require the referenced file
  -> validate receipt integrity and identity
  -> reject any matching supersedence record
  -> validate current VERIFIED marker and verification evidence
  -> validate operator
  -> return current receipt as idempotent replay
```

Any failure stops closed. A historical receipt is consulted only as immutable
evidence or as the subject of a supersedence check.

## 3. Receipt Resolution Contract

Replay authorization now follows this deterministic order:

1. Resolve the current gate lifecycle from runtime state.
2. Require a coherent lifecycle: a later active gate, accepted and bound
   intervening gates, or the valid post-OA-30 terminal state.
3. Resolve only the receipt locator held by the accepted gate.
4. Require receipt existence and self-integrity.
5. Require package, gate, decision, operator, and package-manifest bindings.
6. Reject a receipt named by path or digest in a supersedence record.
7. Reconstruct and validate the current VERIFIED marker and its underlying
   verification evidence.
8. Require receipt-to-marker file, marker digest, and evidence digest matches.
9. Authorize replay only after all checks pass.

Missing pointers, missing files, path escape, wrong-gate binding, malformed
runtime state, regressed or skipped gates, supersedence, receipt corruption,
operator mismatch, marker mismatch, and evidence mismatch are blocking.

## 4. Replay Correction Summary

`scripts/lib/emp/progressive_oa.py` now:

- derives replay exclusively from an `ACCEPTED` runtime gate;
- resolves the exact `acceptance_receipt` lifecycle pointer;
- validates lifecycle ordering before consulting receipt evidence;
- validates receipt, manifest, marker, and evidence bindings;
- detects supersedence by immutable receipt path or digest;
- preserves content-addressed acceptance receipts;
- permits interruption recovery only for one unambiguous current binding;
- applies the same lifecycle and receipt validation to `verify_receipt`.

No historical receipt or supersedence record was edited. Their SHA-256 digests
before and after implementation remained:

| Historical artifact | SHA-256 |
|---|---|
| `accepted.json` | `a2a84dce4a2741b8570169a9507565e119fc7d4f81cabbfa23a71abb94105ef4` |
| `superseded-by-contract-correction.json` | `3e0c5187281d2984774b7ca184b47f6ab710ba0e2289ef8d76cabd538b4b42c7` |
| Current content-addressed receipt | `ddfbc4b110c988dd4687837ecac46879d20c850d9f05c6b3ada7243b343a09cf` |

## 5. Regression and State-Machine Validation

`python3 scripts/tests/test-zeus-progressive-oa.py`:

```text
Ran 21 tests in 0.297s
OK
```

Covered positive cases:

- current accepted lifecycle replays successfully;
- repeated replay is idempotent;
- the current pointer resolves consistently;
- interruption recovery reuses exactly one valid current receipt.

Covered negative cases:

- superseded current receipt;
- historical flat receipt alone;
- missing current receipt pointer;
- receipt integrity mismatch;
- verification-evidence digest mismatch;
- marker digest mismatch;
- operator mismatch;
- wrong-gate lifecycle binding;
- active-gate regression;
- skipped/intervening-gate lifecycle gap.

The demonstrated lifecycle is:

```text
VERIFIED_AWAITING_OPERATOR_ACCEPTANCE
  -> ACCEPTED
  -> current receipt replay authorized
  -> acceptance superseded
  -> replay forbidden
  -> new operator acceptance required
```

## 6. Controlled Documentation Reconciliation

`engineering/operations/zeus-operator-interface.md` now distinguishes:

- immutable historical audit evidence;
- runtime `acceptance_receipt` as current lifecycle authority;
- replay as a fully bound, observational operation;
- supersedence as an unconditional replay blocker;
- lifecycle ordering and terminal-state consistency requirements;
- new acceptance as the required path after supersedence.

Controlled-document relationship tests passed (3 tests). Controlled-document
synchronization tests passed (7 tests). Scoped `git diff --check` passed.

## 7. Additional Validation and Known Baseline Findings

- Python compilation of `scripts/lib/emp/progressive_oa.py`: PASS.
- Repository health: PASS.
- Registry validation: PASS.
- Historical receipt digest preservation: PASS.
- Empty index: PASS.
- History rewrite, amendment, rebase, reset, push, publication, and
  synchronization: NOT PERFORMED.

The legacy OA-04 context-reconstruction and mission-resolution suites were
also invoked with repository import resolution enabled. They fail before
testing this correction because they assume OA-04 is the sole active gate,
while authoritative runtime state has advanced to OA-06. The focused replay
suite uses an isolated 30-gate fixture and passes. These baseline fixture
failures are not attributed to replay logic, but should be reconciled by
future test-maintenance work so those suites construct their required OA-04
state rather than depending on mutable repository runtime.

## 8. Completion

Replay authority is now bound solely to the active lifecycle and its exact
current acceptance receipt. Superseded and flat historical receipts remain
immutable evidence and cannot independently authorize replay. Invalid or
ambiguous lifecycle and evidence bindings fail closed. The focused
implementation, tests, and operator documentation are ready for the next
Operational Alpha verification cycle.

